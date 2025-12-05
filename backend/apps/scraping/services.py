"""
Scraping service business logic for extracting data from websites
"""
import logging
import ipaddress
import socket
import threading
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from contextlib import contextmanager
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Raised when scraping fails"""
    pass


class BrowserPool:
    """
    Manages a pool of Playwright browser instances for concurrent scraping.
    Implements thread-safe browser instance management with automatic cleanup.
    """

    def __init__(self, max_browsers: int = 5):
        """
        Initialize browser pool

        Args:
            max_browsers: Maximum number of concurrent browser instances
        """
        self.max_browsers = max_browsers
        self._lock = threading.Lock()
        self._browsers = []
        self._in_use = set()
        self._playwright = None

    def _ensure_playwright(self):
        """Ensure Playwright is initialized"""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
        return self._playwright

    def acquire(self) -> Browser:
        """
        Acquire a browser instance from the pool

        Returns:
            Browser instance ready for use
        """
        with self._lock:
            playwright = self._ensure_playwright()

            # Try to reuse an existing browser
            for browser in self._browsers:
                if browser not in self._in_use:
                    self._in_use.add(browser)
                    logger.debug(f"Reusing browser from pool. In use: {len(self._in_use)}/{len(self._browsers)}")
                    return browser

            # Create new browser if under limit
            if len(self._browsers) < self.max_browsers:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                self._browsers.append(browser)
                self._in_use.add(browser)
                logger.info(f"Created new browser. Pool size: {len(self._browsers)}/{self.max_browsers}")
                return browser

            # Pool is full, wait and retry (simplified - in production use proper queue)
            logger.warning("Browser pool exhausted, waiting for available browser")
            raise ScrapingError("Browser pool exhausted. Too many concurrent scraping operations.")

    def release(self, browser: Browser):
        """
        Release a browser instance back to the pool

        Args:
            browser: Browser instance to release
        """
        with self._lock:
            if browser in self._in_use:
                self._in_use.remove(browser)
                logger.debug(f"Released browser to pool. In use: {len(self._in_use)}/{len(self._browsers)}")

    def cleanup(self):
        """Close all browser instances and cleanup resources"""
        with self._lock:
            for browser in self._browsers:
                try:
                    browser.close()
                except Exception as e:
                    logger.error(f"Error closing browser: {e}")

            self._browsers.clear()
            self._in_use.clear()

            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception as e:
                    logger.error(f"Error stopping Playwright: {e}")
                self._playwright = None

            logger.info("Browser pool cleaned up")

    @contextmanager
    def get_browser(self):
        """
        Context manager for acquiring and releasing browsers

        Usage:
            with pool.get_browser() as browser:
                # Use browser
                pass
        """
        browser = self.acquire()
        try:
            yield browser
        finally:
            self.release(browser)


# Global browser pool instance
_browser_pool = None
_pool_lock = threading.Lock()


def get_browser_pool() -> BrowserPool:
    """Get or create the global browser pool instance"""
    global _browser_pool
    with _pool_lock:
        if _browser_pool is None:
            _browser_pool = BrowserPool(max_browsers=5)
        return _browser_pool


class PageLoader:
    """
    Utility class for loading pages with proper timeout and ready state handling.
    Implements SSRF protection and error handling for page loads.
    """

    def __init__(self, timeout: int = 30000, wait_after_load: int = 2000):
        """
        Initialize page loader

        Args:
            timeout: Page load timeout in milliseconds (default: 30000)
            wait_after_load: Additional wait time after load for dynamic content (default: 2000)
        """
        self.timeout = timeout
        self.wait_after_load = wait_after_load

    def load_page(self, context: BrowserContext, url: str) -> Page:
        """
        Load a page with proper timeout and ready state handling

        Args:
            context: Browser context to use
            url: URL to load

        Returns:
            Loaded page object

        Raises:
            ScrapingError: If page load fails
        """
        if not url:
            raise ScrapingError("URL is required")

        # Validate URL is not targeting private/internal resources
        self._validate_url(url)

        page = context.new_page()

        # Set up SSRF protection route handler
        self._setup_ssrf_protection(page)

        try:
            logger.info(f"Loading page: {url}")

            # Navigate to URL with timeout
            try:
                response = page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')

                if response is None:
                    raise ScrapingError(f"Failed to load page: {url}")

                if not response.ok:
                    logger.warning(f"Page loaded with non-OK status: {response.status}")

            except PlaywrightTimeoutError:
                raise ScrapingError(f"Page load timeout after {self.timeout}ms for URL: {url}")

            # Wait for dynamic content to load
            if self.wait_after_load > 0:
                page.wait_for_timeout(self.wait_after_load)

            logger.info(f"Successfully loaded page: {url}")
            return page

        except ScrapingError:
            page.close()
            raise
        except Exception as e:
            page.close()
            logger.error(f"Error loading page {url}: {e}")
            raise ScrapingError(f"Failed to load page: {str(e)}")

    def _validate_url(self, url: str):
        """
        Validate URL is not targeting private/internal resources

        Args:
            url: URL to validate

        Raises:
            ScrapingError: If URL is invalid or targets private resources
        """
        try:
            parsed = urlparse(url)

            if not parsed.scheme or not parsed.hostname:
                raise ScrapingError("Invalid URL format")

            if parsed.scheme not in ['http', 'https']:
                raise ScrapingError(f"Unsupported URL scheme: {parsed.scheme}")

            hostname = parsed.hostname.lower()

            # Block localhost
            localhost_names = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '::']
            if hostname in localhost_names:
                raise ScrapingError("Cannot scrape localhost URLs")

            # Resolve and check IP
            try:
                addr_info = socket.getaddrinfo(hostname, None)
                for info in addr_info:
                    ip_str = info[4][0]
                    try:
                        ip = ipaddress.ip_address(ip_str)
                        if (ip.is_private or ip.is_loopback or ip.is_link_local or
                            ip.is_reserved or ip.is_multicast or ip_str.startswith('169.254.')):
                            raise ScrapingError(f"Cannot scrape private IP addresses: {ip_str}")
                    except ValueError:
                        continue
            except socket.gaierror as e:
                raise ScrapingError(f"Cannot resolve hostname: {hostname}")

        except ScrapingError:
            raise
        except Exception as e:
            raise ScrapingError(f"URL validation failed: {str(e)}")

    def _setup_ssrf_protection(self, page: Page):
        """
        Set up route handler for SSRF protection

        Args:
            page: Page to protect
        """
        def handle_route(route):
            """Block requests to private/internal resources"""
            request_url = route.request.url
            try:
                parsed = urlparse(request_url)
                hostname = parsed.hostname

                if hostname:
                    # Block localhost
                    localhost_names = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '::']
                    if hostname.lower() in localhost_names:
                        logger.warning(f"Blocked redirect to localhost: {request_url}")
                        route.abort()
                        return

                    # Resolve and check IP
                    try:
                        addr_info = socket.getaddrinfo(hostname, None)
                        for info in addr_info:
                            ip_str = info[4][0]
                            try:
                                ip = ipaddress.ip_address(ip_str)
                                if (ip.is_private or ip.is_loopback or ip.is_link_local or
                                    ip.is_reserved or ip.is_multicast or ip_str.startswith('169.254.')):
                                    logger.warning(f"Blocked redirect to private IP: {request_url} ({ip_str})")
                                    route.abort()
                                    return
                            except ValueError:
                                continue
                    except socket.gaierror:
                        pass
            except Exception as e:
                logger.error(f"Error checking redirect URL: {e}")

            route.continue_()

        # Apply route handler to all requests
        page.route('**/*', handle_route)


class ScrapingService:
    """Service for scraping websites using Playwright with browser pool management"""

    def __init__(self, timeout: int = 30000, use_pool: bool = True):
        """
        Initialize scraping service

        Args:
            timeout: Page load timeout in milliseconds (default: 30000)
            use_pool: Whether to use browser pool (default: True)
        """
        self.timeout = timeout
        self.use_pool = use_pool
        self.page_loader = PageLoader(timeout=timeout)

    def scrape_url(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape a URL and extract data based on configuration

        Args:
            url: URL to scrape
            config: Configuration with selectors, normalization, and truthy_values

        Returns:
            Dictionary of extracted key-value pairs

        Raises:
            ScrapingError: If scraping fails
        """
        if not url:
            raise ScrapingError("URL is required")

        if not config or 'selectors' not in config:
            raise ScrapingError("Configuration with selectors is required")

        selectors = config.get('selectors', {})
        normalization = config.get('normalization', {})

        if not selectors:
            raise ScrapingError("At least one selector must be provided")

        try:
            logger.info(f"Starting scrape for URL: {url}")

            if self.use_pool:
                # Use browser pool for better performance
                return self._scrape_with_pool(url, selectors, normalization)
            else:
                # Use standalone browser (for testing or single operations)
                return self._scrape_standalone(url, selectors, normalization)

        except ScrapingError:
            raise
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            raise ScrapingError(f"Scraping failed: {str(e)}")

    def _scrape_with_pool(self, url: str, selectors: Dict[str, Any], normalization: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape using browser pool

        Args:
            url: URL to scrape
            selectors: Selector configuration
            normalization: Normalization configuration

        Returns:
            Extracted data
        """
        pool = get_browser_pool()

        with pool.get_browser() as browser:
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            try:
                page = self.page_loader.load_page(context, url)

                try:
                    # Extract data based on selectors
                    extracted_data = self._extract_all_fields(page, selectors, normalization)

                    logger.info(f"Successfully scraped {len(extracted_data)} fields from {url}")
                    return extracted_data

                finally:
                    page.close()

            finally:
                context.close()

    def _scrape_standalone(self, url: str, selectors: Dict[str, Any], normalization: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape using standalone browser (for testing)

        Args:
            url: URL to scrape
            selectors: Selector configuration
            normalization: Normalization configuration

        Returns:
            Extracted data
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            try:
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                try:
                    page = self.page_loader.load_page(context, url)

                    try:
                        # Extract data based on selectors
                        extracted_data = self._extract_all_fields(page, selectors, normalization)

                        logger.info(f"Successfully scraped {len(extracted_data)} fields from {url}")
                        return extracted_data

                    finally:
                        page.close()

                finally:
                    context.close()

            finally:
                browser.close()

    def _extract_all_fields(self, page: Page, selectors: Dict[str, Any], normalization: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all configured fields from page

        Args:
            page: Playwright page object
            selectors: Selector configuration
            normalization: Normalization configuration

        Returns:
            Dictionary of extracted key-value pairs
        """
        extracted_data = {}

        for key, selector_config in selectors.items():
            try:
                value = self._extract_value(page, selector_config)

                # Apply normalization if configured
                if key in normalization:
                    value = self._normalize_value(value, normalization[key])

                extracted_data[key] = value

            except Exception as e:
                logger.warning(f"Failed to extract '{key}': {e}")
                extracted_data[key] = None

        return extracted_data

    def _extract_value(self, page, selector_config: str) -> str:
        """
        Extract value from page using selector

        Args:
            page: Playwright page object
            selector_config: Selector string (e.g., "css:.status" or "xpath://div[@class='status']")

        Returns:
            Extracted text value
        """
        if isinstance(selector_config, dict):
            # Handle complex selector config
            selector = selector_config.get('selector', '')
            attribute = selector_config.get('attribute')
        else:
            selector = selector_config
            attribute = None

        # Parse selector type
        if selector.startswith('css:'):
            css_selector = selector[4:]
            element = page.query_selector(css_selector)
        elif selector.startswith('xpath:'):
            xpath_selector = selector[6:]
            element = page.query_selector(f'xpath={xpath_selector}')
        else:
            # Default to CSS selector
            element = page.query_selector(selector)

        if not element:
            return None

        # Extract value
        if attribute:
            return element.get_attribute(attribute)
        else:
            return element.inner_text()

    def _normalize_value(self, value: Any, normalization_config: Dict[str, Any]) -> Any:
        """
        Normalize extracted value based on configuration

        Args:
            value: Raw extracted value
            normalization_config: Normalization rules

        Returns:
            Normalized value
        """
        if value is None:
            return None

        value_type = normalization_config.get('type', 'text')
        transform = normalization_config.get('transform')
        strip = normalization_config.get('strip', True)

        # Convert to string for text processing
        if value_type == 'text':
            value = str(value)

            if strip:
                value = value.strip()

            if transform == 'lowercase':
                value = value.lower()
            elif transform == 'uppercase':
                value = value.upper()

        elif value_type == 'number':
            # Extract numeric value
            import re
            numeric_str = re.sub(r'[^\d.-]', '', str(value))
            try:
                if '.' in numeric_str:
                    value = float(numeric_str)
                else:
                    value = int(numeric_str)
            except ValueError:
                value = None

        return value



class ChangeDetectionService:
    """
    Simplified service for detecting changes in scraped state.
    Alert decisions are now handled by AI in AIConfigService.
    """

    def detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare old and new state to detect changes

        Args:
            old_state: Previous state dictionary
            new_state: Current state dictionary

        Returns:
            Tuple of (has_changes, changes_dict) where changes_dict contains
            keys that changed with their old and new values
        """
        if not old_state:
            # First scrape - everything is new
            changes = {
                key: {"old": None, "new": value}
                for key, value in new_state.items()
            }
            return bool(changes), changes

        changes = {}

        # Check for changed values
        all_keys = set(old_state.keys()) | set(new_state.keys())

        for key in all_keys:
            old_value = old_state.get(key)
            new_value = new_state.get(key)

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value
                }

        has_changes = len(changes) > 0
        return has_changes, changes
