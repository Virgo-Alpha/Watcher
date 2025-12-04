"""
Unit tests for browser pool and page loader functionality
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from apps.scraping.services import (
    BrowserPool,
    PageLoader,
    ScrapingError,
    get_browser_pool
)


class BrowserPoolTest(TestCase):
    """Test cases for BrowserPool"""

    def setUp(self):
        """Set up test fixtures"""
        self.pool = BrowserPool(max_browsers=2)

    def tearDown(self):
        """Clean up after tests"""
        self.pool.cleanup()

    @patch('apps.scraping.services.sync_playwright')
    def test_acquire_creates_new_browser(self, mock_playwright):
        """Test that acquire creates a new browser when pool is empty"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw

        browser = self.pool.acquire()

        self.assertEqual(browser, mock_browser)
        self.assertEqual(len(self.pool._browsers), 1)
        self.assertIn(browser, self.pool._in_use)
        mock_pw.chromium.launch.assert_called_once()

    @patch('apps.scraping.services.sync_playwright')
    def test_acquire_reuses_available_browser(self, mock_playwright):
        """Test that acquire reuses an available browser"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw

        # Acquire and release a browser
        browser1 = self.pool.acquire()
        self.pool.release(browser1)

        # Acquire again - should reuse
        browser2 = self.pool.acquire()

        self.assertEqual(browser1, browser2)
        self.assertEqual(len(self.pool._browsers), 1)
        # Should only call launch once
        self.assertEqual(mock_pw.chromium.launch.call_count, 1)

    @patch('apps.scraping.services.sync_playwright')
    def test_acquire_respects_max_browsers(self, mock_playwright):
        """Test that acquire respects max_browsers limit"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser1 = Mock()
        mock_browser2 = Mock()
        mock_pw.chromium.launch.side_effect = [mock_browser1, mock_browser2]
        mock_playwright.return_value.start.return_value = mock_pw

        # Acquire max browsers
        browser1 = self.pool.acquire()
        browser2 = self.pool.acquire()

        # Try to acquire one more - should raise error
        with self.assertRaises(ScrapingError) as context:
            self.pool.acquire()

        self.assertIn("Browser pool exhausted", str(context.exception))
        self.assertEqual(len(self.pool._browsers), 2)

    @patch('apps.scraping.services.sync_playwright')
    def test_release_marks_browser_available(self, mock_playwright):
        """Test that release marks browser as available"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw

        browser = self.pool.acquire()
        self.assertIn(browser, self.pool._in_use)

        self.pool.release(browser)
        self.assertNotIn(browser, self.pool._in_use)

    @patch('apps.scraping.services.sync_playwright')
    def test_cleanup_closes_all_browsers(self, mock_playwright):
        """Test that cleanup closes all browsers"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser1 = Mock()
        mock_browser2 = Mock()
        mock_pw.chromium.launch.side_effect = [mock_browser1, mock_browser2]
        mock_playwright.return_value.start.return_value = mock_pw

        # Acquire browsers
        self.pool.acquire()
        self.pool.acquire()

        # Cleanup
        self.pool.cleanup()

        # Verify browsers were closed
        mock_browser1.close.assert_called_once()
        mock_browser2.close.assert_called_once()
        self.assertEqual(len(self.pool._browsers), 0)
        self.assertEqual(len(self.pool._in_use), 0)

    @patch('apps.scraping.services.sync_playwright')
    def test_get_browser_context_manager(self, mock_playwright):
        """Test get_browser context manager"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser = Mock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw

        # Use context manager
        with self.pool.get_browser() as browser:
            self.assertEqual(browser, mock_browser)
            self.assertIn(browser, self.pool._in_use)

        # After context, browser should be released
        self.assertNotIn(mock_browser, self.pool._in_use)


class PageLoaderTest(TestCase):
    """Test cases for PageLoader"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = PageLoader(timeout=30000, wait_after_load=1000)

    def test_validate_url_rejects_empty_url(self):
        """Test that empty URL is rejected"""
        mock_context = Mock()

        with self.assertRaises(ScrapingError) as context:
            self.loader.load_page(mock_context, "")

        self.assertIn("URL is required", str(context.exception))

    def test_validate_url_rejects_localhost(self):
        """Test that localhost URLs are rejected"""
        mock_context = Mock()

        with self.assertRaises(ScrapingError) as context:
            self.loader._validate_url("http://localhost:8000")

        self.assertIn("Cannot scrape localhost", str(context.exception))

    def test_validate_url_rejects_127_0_0_1(self):
        """Test that 127.0.0.1 URLs are rejected"""
        mock_context = Mock()

        with self.assertRaises(ScrapingError) as context:
            self.loader._validate_url("http://127.0.0.1:8000")

        self.assertIn("Cannot scrape localhost", str(context.exception))

    @patch('apps.scraping.services.socket.getaddrinfo')
    def test_validate_url_rejects_private_ip(self, mock_getaddrinfo):
        """Test that private IP addresses are rejected"""
        # Mock DNS resolution to return private IP
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('192.168.1.1', 80))
        ]

        with self.assertRaises(ScrapingError) as context:
            self.loader._validate_url("http://example.com")

        self.assertIn("Cannot scrape private IP", str(context.exception))

    @patch('apps.scraping.services.socket.getaddrinfo')
    def test_validate_url_accepts_public_ip(self, mock_getaddrinfo):
        """Test that public IP addresses are accepted"""
        # Mock DNS resolution to return public IP
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('8.8.8.8', 80))
        ]

        # Should not raise exception
        self.loader._validate_url("http://example.com")

    def test_validate_url_rejects_invalid_scheme(self):
        """Test that invalid URL schemes are rejected"""
        with self.assertRaises(ScrapingError) as context:
            self.loader._validate_url("ftp://example.com")

        self.assertIn("Unsupported URL scheme", str(context.exception))

    @patch('apps.scraping.services.socket.getaddrinfo')
    def test_load_page_success(self, mock_getaddrinfo):
        """Test successful page loading"""
        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('8.8.8.8', 80))
        ]

        # Mock context and page
        mock_context = Mock()
        mock_page = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_page.goto.return_value = mock_response
        mock_context.new_page.return_value = mock_page

        page = self.loader.load_page(mock_context, "http://example.com")

        self.assertEqual(page, mock_page)
        mock_page.goto.assert_called_once()
        mock_page.wait_for_timeout.assert_called_once_with(1000)

    @patch('apps.scraping.services.socket.getaddrinfo')
    def test_load_page_timeout(self, mock_getaddrinfo):
        """Test page load timeout handling"""
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('8.8.8.8', 80))
        ]

        # Mock context and page
        mock_context = Mock()
        mock_page = Mock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")
        mock_context.new_page.return_value = mock_page

        with self.assertRaises(ScrapingError) as context:
            self.loader.load_page(mock_context, "http://example.com")

        self.assertIn("Page load timeout", str(context.exception))
        mock_page.close.assert_called_once()

    @patch('apps.scraping.services.socket.getaddrinfo')
    def test_load_page_sets_up_ssrf_protection(self, mock_getaddrinfo):
        """Test that SSRF protection is set up"""
        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('8.8.8.8', 80))
        ]

        # Mock context and page
        mock_context = Mock()
        mock_page = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_page.goto.return_value = mock_response
        mock_context.new_page.return_value = mock_page

        self.loader.load_page(mock_context, "http://example.com")

        # Verify route handler was set up
        mock_page.route.assert_called_once()
        call_args = mock_page.route.call_args
        self.assertEqual(call_args[0][0], '**/*')


class GetBrowserPoolTest(TestCase):
    """Test cases for get_browser_pool function"""

    def test_get_browser_pool_returns_singleton(self):
        """Test that get_browser_pool returns the same instance"""
        pool1 = get_browser_pool()
        pool2 = get_browser_pool()

        self.assertIs(pool1, pool2)

    def tearDown(self):
        """Clean up global pool"""
        import apps.scraping.services as services
        if services._browser_pool:
            services._browser_pool.cleanup()
            services._browser_pool = None
