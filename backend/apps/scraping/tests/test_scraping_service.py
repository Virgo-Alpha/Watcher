"""
Unit tests for scraping service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.scraping.services import (
    ScrapingService,
    ChangeDetectionService,
    ScrapingError,
    PageLoader,
    BrowserPool
)


class TestScrapingService:
    """Test cases for ScrapingService"""

    def test_scrape_url_requires_url(self):
        """Test that scrape_url requires a URL"""
        service = ScrapingService(use_pool=False)
        
        with pytest.raises(ScrapingError, match="URL is required"):
            service.scrape_url("", {"selectors": {}})

    def test_scrape_url_requires_config(self):
        """Test that scrape_url requires configuration"""
        service = ScrapingService(use_pool=False)
        
        with pytest.raises(ScrapingError, match="Configuration with selectors is required"):
            service.scrape_url("https://example.com", {})

    def test_scrape_url_requires_selectors(self):
        """Test that scrape_url requires selectors in config"""
        service = ScrapingService(use_pool=False)
        
        with pytest.raises(ScrapingError, match="At least one selector must be provided"):
            service.scrape_url("https://example.com", {"selectors": {}})

    @patch('apps.scraping.services.sync_playwright')
    def test_scrape_url_success(self, mock_playwright):
        """Test successful scraping"""
        # Mock Playwright components
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Test Status"
        mock_page.query_selector.return_value = mock_element
        
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_pw
        
        # Create service and scrape
        service = ScrapingService(use_pool=False)
        config = {
            "selectors": {
                "status": "css:.status"
            },
            "normalization": {}
        }
        
        result = service.scrape_url("https://example.com", config)
        
        # Verify result
        assert result == {"status": "Test Status"}
        assert mock_page.goto.called
        assert mock_page.query_selector.called

    def test_extract_value_css_selector(self):
        """Test extracting value with CSS selector"""
        service = ScrapingService(use_pool=False)
        
        # Mock page and element
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Test Value"
        mock_page = MagicMock()
        mock_page.query_selector.return_value = mock_element
        
        # Extract value
        value = service._extract_value(mock_page, "css:.test")
        
        assert value == "Test Value"
        mock_page.query_selector.assert_called_once_with(".test")

    def test_extract_value_xpath_selector(self):
        """Test extracting value with XPath selector"""
        service = ScrapingService(use_pool=False)
        
        # Mock page and element
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "XPath Value"
        mock_page = MagicMock()
        mock_page.query_selector.return_value = mock_element
        
        # Extract value
        value = service._extract_value(mock_page, "xpath://div[@class='test']")
        
        assert value == "XPath Value"
        mock_page.query_selector.assert_called_once_with("xpath=//div[@class='test']")

    def test_extract_value_with_attribute(self):
        """Test extracting attribute value"""
        service = ScrapingService(use_pool=False)
        
        # Mock page and element
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "https://example.com"
        mock_page = MagicMock()
        mock_page.query_selector.return_value = mock_element
        
        # Extract value
        selector_config = {
            "selector": "css:a.link",
            "attribute": "href"
        }
        value = service._extract_value(mock_page, selector_config)
        
        assert value == "https://example.com"
        mock_element.get_attribute.assert_called_once_with("href")

    def test_normalize_value_text(self):
        """Test text normalization"""
        service = ScrapingService(use_pool=False)
        
        # Test lowercase transform
        result = service._normalize_value(
            "  HELLO WORLD  ",
            {"type": "text", "transform": "lowercase", "strip": True}
        )
        assert result == "hello world"
        
        # Test uppercase transform
        result = service._normalize_value(
            "hello",
            {"type": "text", "transform": "uppercase", "strip": True}
        )
        assert result == "HELLO"

    def test_normalize_value_number(self):
        """Test number normalization"""
        service = ScrapingService(use_pool=False)
        
        # Test integer extraction
        result = service._normalize_value(
            "Price: $123",
            {"type": "number"}
        )
        assert result == 123
        
        # Test float extraction
        result = service._normalize_value(
            "Score: 98.5%",
            {"type": "number"}
        )
        assert result == 98.5


class TestChangeDetectionService:
    """Test cases for ChangeDetectionService"""

    def test_detect_changes_first_scrape(self):
        """Test change detection on first scrape"""
        service = ChangeDetectionService()
        
        old_state = {}
        new_state = {"status": "open", "count": 5}
        
        has_changes, changes = service.detect_changes(old_state, new_state)
        
        assert has_changes is True
        assert len(changes) == 2
        assert changes["status"]["old"] is None
        assert changes["status"]["new"] == "open"

    def test_detect_changes_no_changes(self):
        """Test change detection when nothing changed"""
        service = ChangeDetectionService()
        
        old_state = {"status": "open", "count": 5}
        new_state = {"status": "open", "count": 5}
        
        has_changes, changes = service.detect_changes(old_state, new_state)
        
        assert has_changes is False
        assert len(changes) == 0

    def test_detect_changes_value_changed(self):
        """Test change detection when value changed"""
        service = ChangeDetectionService()
        
        old_state = {"status": "pending", "count": 5}
        new_state = {"status": "approved", "count": 5}
        
        has_changes, changes = service.detect_changes(old_state, new_state)
        
        assert has_changes is True
        assert len(changes) == 1
        assert changes["status"]["old"] == "pending"
        assert changes["status"]["new"] == "approved"

    def test_should_alert_on_change_mode(self):
        """Test alert logic in on_change mode"""
        service = ChangeDetectionService()
        
        # Should alert when changes detected
        should_alert = service.should_alert(
            has_changes=True,
            changes={"status": {"old": "pending", "new": "approved"}},
            alert_mode="on_change",
            last_alert_state=None,
            current_state={"status": "approved"}
        )
        assert should_alert is True
        
        # Should not alert when no changes
        should_alert = service.should_alert(
            has_changes=False,
            changes={},
            alert_mode="on_change",
            last_alert_state=None,
            current_state={"status": "pending"}
        )
        assert should_alert is False

    def test_should_alert_once_mode_first_time(self):
        """Test alert logic in once mode on first alert"""
        service = ChangeDetectionService()
        
        # Should alert when value becomes truthy for first time
        should_alert = service.should_alert(
            has_changes=True,
            changes={"status": {"old": None, "new": "approved"}},
            alert_mode="once",
            last_alert_state=None,
            current_state={"status": "approved"},
            truthy_values={"status": ["approved", "accepted"]}
        )
        assert should_alert is True

    def test_should_alert_once_mode_already_alerted(self):
        """Test alert logic in once mode when already alerted"""
        service = ChangeDetectionService()
        
        # Should not alert again if already in truthy state
        should_alert = service.should_alert(
            has_changes=True,
            changes={"status": {"old": "approved", "new": "approved"}},
            alert_mode="once",
            last_alert_state={"status": "approved"},
            current_state={"status": "approved"},
            truthy_values={"status": ["approved"]}
        )
        assert should_alert is False

    def test_is_truthy(self):
        """Test truthy value checking"""
        service = ChangeDetectionService()
        
        # Test case-insensitive matching
        assert service._is_truthy("APPROVED", ["approved", "accepted"]) is True
        assert service._is_truthy("approved", ["approved", "accepted"]) is True
        assert service._is_truthy("pending", ["approved", "accepted"]) is False
        assert service._is_truthy(None, ["approved"]) is False

    def test_get_change_summary(self):
        """Test change summary generation"""
        service = ChangeDetectionService()
        
        # Single change
        changes = {
            "status": {"old": "pending", "new": "approved"}
        }
        summary = service.get_change_summary(changes)
        assert "status" in summary
        assert "pending" in summary
        assert "approved" in summary
        
        # Multiple changes
        changes = {
            "status": {"old": "pending", "new": "approved"},
            "count": {"old": 5, "new": 10},
            "priority": {"old": "low", "new": "high"},
            "extra": {"old": "a", "new": "b"}
        }
        summary = service.get_change_summary(changes)
        assert "and 1 more" in summary  # Should show first 3 + count


class TestPageLoader:
    """Test cases for PageLoader"""

    def test_validate_url_invalid_scheme(self):
        """Test URL validation rejects invalid schemes"""
        loader = PageLoader()
        
        with pytest.raises(ScrapingError, match="Unsupported URL scheme"):
            loader._validate_url("ftp://example.com")

    def test_validate_url_localhost(self):
        """Test URL validation rejects localhost"""
        loader = PageLoader()
        
        with pytest.raises(ScrapingError, match="Cannot scrape localhost"):
            loader._validate_url("http://localhost:8000")
        
        with pytest.raises(ScrapingError, match="Cannot scrape localhost"):
            loader._validate_url("http://127.0.0.1")

    def test_validate_url_valid(self):
        """Test URL validation accepts valid URLs"""
        loader = PageLoader()
        
        # Should not raise exception
        try:
            loader._validate_url("https://example.com")
            loader._validate_url("http://www.google.com")
        except ScrapingError:
            pytest.fail("Valid URLs should not raise ScrapingError")


class TestBrowserPool:
    """Test cases for BrowserPool"""

    def test_browser_pool_initialization(self):
        """Test browser pool initializes correctly"""
        pool = BrowserPool(max_browsers=3)
        
        assert pool.max_browsers == 3
        assert len(pool._browsers) == 0
        assert len(pool._in_use) == 0

    @patch('apps.scraping.services.sync_playwright')
    def test_browser_pool_acquire_creates_browser(self, mock_playwright):
        """Test browser pool creates browser on first acquire"""
        mock_browser = MagicMock()
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw
        
        pool = BrowserPool(max_browsers=2)
        browser = pool.acquire()
        
        assert browser == mock_browser
        assert len(pool._browsers) == 1
        assert browser in pool._in_use

    @patch('apps.scraping.services.sync_playwright')
    def test_browser_pool_reuses_browser(self, mock_playwright):
        """Test browser pool reuses released browsers"""
        mock_browser = MagicMock()
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw
        
        pool = BrowserPool(max_browsers=2)
        
        # Acquire and release
        browser1 = pool.acquire()
        pool.release(browser1)
        
        # Acquire again - should reuse
        browser2 = pool.acquire()
        
        assert browser1 == browser2
        assert len(pool._browsers) == 1

    @patch('apps.scraping.services.sync_playwright')
    def test_browser_pool_max_limit(self, mock_playwright):
        """Test browser pool respects max limit"""
        mock_browser = MagicMock()
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_pw
        
        pool = BrowserPool(max_browsers=1)
        
        # Acquire first browser
        browser1 = pool.acquire()
        
        # Try to acquire second - should raise error
        with pytest.raises(ScrapingError, match="Browser pool exhausted"):
            pool.acquire()
