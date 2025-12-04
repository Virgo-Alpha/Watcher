"""
Unit tests for AI service functionality
"""
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from apps.ai.services import AIConfigService, AIConfigurationError


class AIConfigServiceTest(TestCase):
    """Test cases for AIConfigService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = AIConfigService()
    
    @override_settings(LLM_API_KEY='')
    def test_is_available_without_api_key(self):
        """Test service availability when API key is not configured"""
        service = AIConfigService()
        self.assertFalse(service.is_available())
    
    @override_settings(LLM_API_KEY='test-api-key')
    def test_is_available_with_api_key(self):
        """Test service availability when API key is configured"""
        with patch('apps.ai.services.OpenAI'):
            service = AIConfigService()
            self.assertTrue(service.is_available())
    
    @override_settings(LLM_API_KEY='')
    def test_generate_config_without_api_key(self):
        """Test configuration generation fails without API key"""
        service = AIConfigService()
        
        with self.assertRaises(AIConfigurationError) as context:
            service.generate_config("https://example.com", "Monitor status")
        
        self.assertIn("AI service is not available", str(context.exception))
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_config_success(self, mock_openai):
        """Test successful configuration generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "selectors": {
                "status": "css:.status-indicator"
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
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        config = service.generate_config("https://example.com", "Monitor status")
        
        # Verify the configuration structure
        self.assertIn('selectors', config)
        self.assertIn('normalization', config)
        self.assertIn('truthy_values', config)
        self.assertEqual(config['selectors']['status'], 'css:.status-indicator')
        self.assertEqual(config['truthy_values']['status'], ['open', 'available'])
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_config_with_markdown_formatting(self, mock_openai):
        """Test configuration generation with markdown-formatted response"""
        # Mock OpenAI response with markdown formatting
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''```json
{
    "selectors": {
        "status": "css:.status"
    },
    "normalization": {
        "status": {"type": "text"}
    },
    "truthy_values": {
        "status": ["open"]
    }
}
```'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        config = service.generate_config("https://example.com", "Monitor status")
        
        self.assertIn('selectors', config)
        self.assertEqual(config['selectors']['status'], 'css:.status')
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_config_invalid_json(self, mock_openai):
        """Test configuration generation with invalid JSON response"""
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        
        with self.assertRaises(AIConfigurationError) as context:
            service.generate_config("https://example.com", "Monitor status")
        
        self.assertIn("Invalid JSON in AI response", str(context.exception))
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_config_missing_required_keys(self, mock_openai):
        """Test configuration generation with missing required keys"""
        # Mock OpenAI response missing required keys
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "selectors": {"status": "css:.status"}
            # Missing normalization and truthy_values
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        
        with self.assertRaises(AIConfigurationError) as context:
            service.generate_config("https://example.com", "Monitor status")
        
        self.assertIn("Missing required key", str(context.exception))
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_config_auto_prefix_selectors(self, mock_openai):
        """Test that selectors without prefixes get css: prefix added"""
        # Mock OpenAI response without css: prefix
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "selectors": {
                "status": ".status-indicator"  # No css: prefix
            },
            "normalization": {
                "status": {"type": "text"}
            },
            "truthy_values": {
                "status": ["open"]
            }
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        config = service.generate_config("https://example.com", "Monitor status")
        
        # The raw config should not be modified, but parsing should handle the prefix
        self.assertEqual(config['selectors']['status'], '.status-indicator')
        
        # But when parsed, it should have the css: prefix
        haunt_config = service.parse_config(config)
        self.assertEqual(haunt_config.get_selector_string('status'), 'css:.status-indicator')
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_summary_success(self, mock_openai):
        """Test successful summary generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Status changed from closed to open"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        
        summary = service.generate_summary(old_state, new_state)
        
        self.assertEqual(summary, "Status changed from closed to open")
        
        # Verify the API was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'gpt-3.5-turbo')
        self.assertEqual(call_args[1]['temperature'], 0.3)
        self.assertEqual(call_args[1]['max_tokens'], 150)
    
    @override_settings(LLM_API_KEY='')
    def test_generate_summary_fallback_without_api_key(self):
        """Test summary generation fallback when API key is not available"""
        service = AIConfigService()
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        
        summary = service.generate_summary(old_state, new_state)
        
        self.assertEqual(summary, "status changed from 'closed' to 'open'")
    
    @override_settings(LLM_API_KEY='test-api-key')
    @patch('apps.ai.services.OpenAI')
    def test_generate_summary_fallback_on_error(self, mock_openai):
        """Test summary generation fallback when AI call fails"""
        # Mock OpenAI to raise an exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        service = AIConfigService()
        old_state = {"status": "closed", "deadline": "2024-01-01"}
        new_state = {"status": "open", "deadline": "2024-01-01"}
        
        summary = service.generate_summary(old_state, new_state)
        
        # Should fallback to simple summary
        self.assertEqual(summary, "status changed from 'closed' to 'open'")
    
    def test_generate_fallback_summary_no_changes(self):
        """Test fallback summary generation with no changes"""
        service = AIConfigService()
        old_state = {"status": "open"}
        new_state = {"status": "open"}
        
        summary = service._generate_fallback_summary(old_state, new_state)
        
        self.assertEqual(summary, "No changes detected")
    
    def test_generate_fallback_summary_single_change(self):
        """Test fallback summary generation with single change"""
        service = AIConfigService()
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        
        summary = service._generate_fallback_summary(old_state, new_state)
        
        self.assertEqual(summary, "status changed from 'closed' to 'open'")
    
    def test_generate_fallback_summary_multiple_changes(self):
        """Test fallback summary generation with multiple changes"""
        service = AIConfigService()
        old_state = {"status": "closed", "deadline": "2024-01-01", "priority": "low"}
        new_state = {"status": "open", "deadline": "2024-02-01", "priority": "high"}
        
        summary = service._generate_fallback_summary(old_state, new_state)
        
        # Should show first 2 changes and indicate more
        self.assertIn("3 fields changed", summary)
        self.assertIn("...", summary)
    
    def test_parse_config_success(self):
        """Test successful configuration parsing"""
        service = AIConfigService()
        config = {
            "selectors": {"status": "css:.status"},
            "normalization": {"status": {"type": "text"}},
            "truthy_values": {"status": ["open"]}
        }
        
        # Should not raise any exception
        haunt_config = service.parse_config(config)
        self.assertIsNotNone(haunt_config)
    
    def test_parse_config_missing_keys(self):
        """Test configuration parsing with missing keys"""
        service = AIConfigService()
        config = {"selectors": {"status": "css:.status"}}
        
        with self.assertRaises(AIConfigurationError) as context:
            service.parse_config(config)
        
        self.assertIn("Missing required key", str(context.exception))
    
    def test_parse_config_invalid_types(self):
        """Test configuration parsing with invalid types"""
        service = AIConfigService()
        config = {
            "selectors": "not a dict",  # Should be dict
            "normalization": {},
            "truthy_values": {}
        }
        
        with self.assertRaises(AIConfigurationError) as context:
            service.parse_config(config)
        
        self.assertIn("'selectors' must be a dictionary", str(context.exception))
    
    def test_parse_config_invalid_selector_type(self):
        """Test configuration parsing with invalid selector type"""
        service = AIConfigService()
        config = {
            "selectors": {"status": 123},  # Should be string
            "normalization": {},
            "truthy_values": {}
        }
        
        with self.assertRaises(AIConfigurationError) as context:
            service.parse_config(config)
        
        self.assertIn("Selector 'status' must be a string", str(context.exception))
    
    def test_parse_config_invalid_normalization_type(self):
        """Test configuration parsing with invalid normalization type"""
        service = AIConfigService()
        config = {
            "selectors": {"status": "css:.status"},
            "normalization": {"status": "not a dict"},  # Should be dict
            "truthy_values": {}
        }
        
        with self.assertRaises(AIConfigurationError) as context:
            service.parse_config(config)
        
        self.assertIn("Normalization rules for 'status' must be a dictionary", str(context.exception))
    
    def test_parse_config_invalid_truthy_values_type(self):
        """Test configuration parsing with invalid truthy values type"""
        service = AIConfigService()
        config = {
            "selectors": {"status": "css:.status"},
            "normalization": {"status": {"type": "text"}},
            "truthy_values": {"status": "not a list"}  # Should be list
        }
        
        with self.assertRaises(AIConfigurationError) as context:
            service.parse_config(config)
        
        self.assertIn("Truthy values for 'status' must be a list", str(context.exception))