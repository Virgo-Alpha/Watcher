"""
Unit tests for content extraction functionality
"""
from unittest.mock import Mock, patch
from django.test import TestCase
from apps.scraping.services import ScrapingService, ScrapingError


class ContentExtractionTest(TestCase):
    """Test cases for content extraction engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = ScrapingService(use_pool=False)

    def test_extract_value_with_css_selector(self):
        """Test extracting value using CSS selector"""
        # Mock page with element
        mock_page = Mock()
        mock_element = Mock()
        mock_element.inner_text.return_value = "Test Value"
        mock_page.query_selector.return_value = mock_element

        value = self.service._extract_value(mock_page, "css:.test-class")

        self.assertEqual(value, "Test Value")
        mock_page.query_selector.assert_called_once_with(".test-class")

    def test_extract_value_with_xpath_selector(self):
        """Test extracting value using XPath selector"""
        # Mock page with element
        mock_page = Mock()
        mock_element = Mock()
        mock_element.inner_text.return_value = "XPath Value"
        mock_page.query_selector.return_value = mock_element

        value = self.service._extract_value(mock_page, "xpath://div[@class='test']")

        self.assertEqual(value, "XPath Value")
        mock_page.query_selector.assert_called_once_with("xpath=//div[@class='test']")

    def test_extract_value_with_default_css_selector(self):
        """Test extracting value with selector without prefix (defaults to CSS)"""
        # Mock page with element
        mock_page = Mock()
        mock_element = Mock()
        mock_element.inner_text.return_value = "Default Value"
        mock_page.query_selector.return_value = mock_element

        value = self.service._extract_value(mock_page, ".test-class")

        self.assertEqual(value, "Default Value")
        mock_page.query_selector.assert_called_once_with(".test-class")

    def test_extract_value_with_attribute(self):
        """Test extracting attribute value instead of text"""
        # Mock page with element
        mock_page = Mock()
        mock_element = Mock()
        mock_element.get_attribute.return_value = "https://example.com"
        mock_page.query_selector.return_value = mock_element

        selector_config = {
            "selector": "css:a.link",
            "attribute": "href"
        }

        value = self.service._extract_value(mock_page, selector_config)

        self.assertEqual(value, "https://example.com")
        mock_element.get_attribute.assert_called_once_with("href")

    def test_extract_value_element_not_found(self):
        """Test extracting value when element is not found"""
        # Mock page with no element
        mock_page = Mock()
        mock_page.query_selector.return_value = None

        value = self.service._extract_value(mock_page, "css:.nonexistent")

        self.assertIsNone(value)

    def test_normalize_value_text_lowercase(self):
        """Test normalizing text value to lowercase"""
        normalization_config = {
            "type": "text",
            "transform": "lowercase"
        }

        value = self.service._normalize_value("HELLO WORLD", normalization_config)

        self.assertEqual(value, "hello world")

    def test_normalize_value_text_uppercase(self):
        """Test normalizing text value to uppercase"""
        normalization_config = {
            "type": "text",
            "transform": "uppercase"
        }

        value = self.service._normalize_value("hello world", normalization_config)

        self.assertEqual(value, "HELLO WORLD")

    def test_normalize_value_text_strip(self):
        """Test normalizing text value with strip"""
        normalization_config = {
            "type": "text",
            "strip": True
        }

        value = self.service._normalize_value("  hello world  ", normalization_config)

        self.assertEqual(value, "hello world")

    def test_normalize_value_text_no_strip(self):
        """Test normalizing text value without strip"""
        normalization_config = {
            "type": "text",
            "strip": False
        }

        value = self.service._normalize_value("  hello world  ", normalization_config)

        self.assertEqual(value, "  hello world  ")

    def test_normalize_value_number_integer(self):
        """Test normalizing value to integer"""
        normalization_config = {
            "type": "number"
        }

        value = self.service._normalize_value("Price: $42", normalization_config)

        self.assertEqual(value, 42)
        self.assertIsInstance(value, int)

    def test_normalize_value_number_float(self):
        """Test normalizing value to float"""
        normalization_config = {
            "type": "number"
        }

        value = self.service._normalize_value("Price: $42.99", normalization_config)

        self.assertEqual(value, 42.99)
        self.assertIsInstance(value, float)

    def test_normalize_value_number_negative(self):
        """Test normalizing negative number"""
        normalization_config = {
            "type": "number"
        }

        value = self.service._normalize_value("Temperature: -15.5°C", normalization_config)

        self.assertEqual(value, -15.5)

    def test_normalize_value_number_invalid(self):
        """Test normalizing invalid number returns None"""
        normalization_config = {
            "type": "number"
        }

        value = self.service._normalize_value("No numbers here", normalization_config)

        self.assertIsNone(value)

    def test_normalize_value_none_input(self):
        """Test normalizing None value returns None"""
        normalization_config = {
            "type": "text"
        }

        value = self.service._normalize_value(None, normalization_config)

        self.assertIsNone(value)

    def test_extract_all_fields_success(self):
        """Test extracting all fields successfully"""
        # Mock page
        mock_page = Mock()

        # Mock elements for different fields
        mock_status = Mock()
        mock_status.inner_text.return_value = "  OPEN  "
        mock_deadline = Mock()
        mock_deadline.inner_text.return_value = "2024-12-31"

        def query_selector_side_effect(selector):
            if ".status" in selector:
                return mock_status
            elif ".deadline" in selector:
                return mock_deadline
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect

        selectors = {
            "status": "css:.status",
            "deadline": "css:.deadline"
        }

        normalization = {
            "status": {
                "type": "text",
                "transform": "lowercase",
                "strip": True
            }
        }

        extracted_data = self.service._extract_all_fields(mock_page, selectors, normalization)

        self.assertEqual(extracted_data["status"], "open")
        self.assertEqual(extracted_data["deadline"], "2024-12-31")

    def test_extract_all_fields_with_missing_element(self):
        """Test extracting fields when some elements are missing"""
        # Mock page
        mock_page = Mock()

        # Mock only one element
        mock_status = Mock()
        mock_status.inner_text.return_value = "OPEN"

        def query_selector_side_effect(selector):
            if ".status" in selector:
                return mock_status
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect

        selectors = {
            "status": "css:.status",
            "deadline": "css:.deadline"
        }

        normalization = {}

        extracted_data = self.service._extract_all_fields(mock_page, selectors, normalization)

        self.assertEqual(extracted_data["status"], "OPEN")
        self.assertIsNone(extracted_data["deadline"])

    def test_extract_all_fields_with_extraction_error(self):
        """Test extracting fields when extraction raises error"""
        # Mock page that raises error
        mock_page = Mock()
        mock_page.query_selector.side_effect = Exception("Extraction error")

        selectors = {
            "status": "css:.status"
        }

        normalization = {}

        extracted_data = self.service._extract_all_fields(mock_page, selectors, normalization)

        # Should handle error gracefully and return None
        self.assertIsNone(extracted_data["status"])

    def test_scrape_url_requires_url(self):
        """Test that scrape_url requires URL"""
        config = {
            "selectors": {"status": "css:.status"},
            "normalization": {},
            "truthy_values": {}
        }

        with self.assertRaises(ScrapingError) as context:
            self.service.scrape_url("", config)

        self.assertIn("URL is required", str(context.exception))

    def test_scrape_url_requires_config(self):
        """Test that scrape_url requires config"""
        with self.assertRaises(ScrapingError) as context:
            self.service.scrape_url("http://example.com", None)

        self.assertIn("Configuration with selectors is required", str(context.exception))

    def test_scrape_url_requires_selectors(self):
        """Test that scrape_url requires selectors in config"""
        config = {
            "normalization": {},
            "truthy_values": {}
        }

        with self.assertRaises(ScrapingError) as context:
            self.service.scrape_url("http://example.com", config)

        self.assertIn("Configuration with selectors is required", str(context.exception))

    def test_scrape_url_requires_non_empty_selectors(self):
        """Test that scrape_url requires non-empty selectors"""
        config = {
            "selectors": {},
            "normalization": {},
            "truthy_values": {}
        }

        with self.assertRaises(ScrapingError) as context:
            self.service.scrape_url("http://example.com", config)

        self.assertIn("At least one selector must be provided", str(context.exception))


class ScrapingServiceIntegrationTest(TestCase):
    """Integration tests for ScrapingService with mock HTML"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = ScrapingService(use_pool=False)

    @patch('apps.scraping.services.PageLoader.load_page')
    @patch('apps.scraping.services.sync_playwright')
    def test_scrape_url_with_mock_html(self, mock_playwright, mock_load_page):
        """Test scraping URL with mock HTML content"""
        # Mock Playwright
        mock_pw = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_playwright.return_value.__enter__.return_value = mock_pw

        # Mock page loader
        mock_load_page.return_value = mock_page

        # Mock elements
        mock_status_element = Mock()
        mock_status_element.inner_text.return_value = "OPEN"

        mock_deadline_element = Mock()
        mock_deadline_element.inner_text.return_value = "2024-12-31"

        def query_selector_side_effect(selector):
            if ".status" in selector or "status" in selector:
                return mock_status_element
            elif ".deadline" in selector or "deadline" in selector:
                return mock_deadline_element
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect

        # Configuration
        config = {
            "selectors": {
                "status": "css:.status",
                "deadline": "css:.deadline"
            },
            "normalization": {
                "status": {
                    "type": "text",
                    "transform": "lowercase"
                }
            },
            "truthy_values": {
                "status": ["open", "available"]
            }
        }

        # Scrape
        result = self.service.scrape_url("http://example.com", config)

        # Verify results
        self.assertEqual(result["status"], "open")
        self.assertEqual(result["deadline"], "2024-12-31")

        # Verify cleanup
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
