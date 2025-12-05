"""
Tests for AI service functionality
"""
import json
from unittest.mock import Mock, patch
from django.test import TestCase
from django.conf import settings
from apps.ai.services import AIConfigService, AIConfigurationError


class AIConfigServiceTestCase(TestCase):
    """Test cases for AIConfigService"""
    
    def test_service_initialization_with_api_key(self):
        """Test that service initializes correctly with API key"""
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            
            self.assertIsNotNone(service.model)
            self.assertTrue(service.is_available())
            mock_genai.configure.assert_called_once_with(api_key=settings.LLM_API_KEY)
            mock_genai.GenerativeModel.assert_called_once_with('models/gemini-2.0-flash')
    
    def test_service_initialization_without_api_key(self):
        """Test that service handles missing API key gracefully"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            
            self.assertIsNone(service.model)
            self.assertFalse(service.is_available())
    
    def test_generate_config_success(self):
        """Test successful configuration generation"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "selectors": {
                "status": "css:.status-indicator"
            },
            "normalization": {
                "status": {
                    "type": "text",
                    "transform": "lowercase",
                    "strip": True
                }
            },
            "truthy_values": {
                "status": ["open", "available"]
            }
        })
        # Mock the candidates structure
        mock_candidate = Mock()
        mock_candidate.content.parts = [Mock()]
        mock_response.candidates = [mock_candidate]
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            config = service.generate_config(
                url="https://example.com",
                description="Check if status is open"
            )
            
            self.assertIn("selectors", config)
            self.assertIn("status", config["selectors"])
            self.assertEqual(config["selectors"]["status"], "css:.status-indicator")
    
    def test_generate_config_with_markdown_formatting(self):
        """Test that service handles markdown-formatted JSON responses"""
        mock_response = Mock()
        mock_response.text = '''```json
{
    "selectors": {
        "status": "css:.status"
    },
    "normalization": {
        "status": {
            "type": "text",
            "transform": "lowercase",
            "strip": true
        }
    },
    "truthy_values": {
        "status": ["open"]
    }
}
```'''
        # Mock the candidates structure
        mock_candidate = Mock()
        mock_candidate.content.parts = [Mock()]
        mock_response.candidates = [mock_candidate]
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            config = service.generate_config(
                url="https://example.com",
                description="Check status"
            )
            
            self.assertIn("selectors", config)
            self.assertIn("status", config["selectors"])
    
    def test_generate_config_unavailable_service(self):
        """Test that generate_config raises error when service unavailable"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            
            with self.assertRaises(AIConfigurationError) as context:
                service.generate_config(
                    url="https://example.com",
                    description="test"
                )
            
            self.assertIn("not available", str(context.exception))
    
    def test_generate_summary_success(self):
        """Test successful summary generation"""
        mock_response = Mock()
        mock_response.text = "Status changed from closed to open"
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            summary = service.generate_summary(
                old_state={"status": "closed"},
                new_state={"status": "open"}
            )
            
            self.assertEqual(summary, "Status changed from closed to open")
    
    def test_generate_summary_fallback(self):
        """Test fallback summary when AI service unavailable"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            summary = service.generate_summary(
                old_state={"status": "closed"},
                new_state={"status": "open"}
            )
            
            # Should return fallback summary
            self.assertIn("status", summary.lower())
            self.assertIn("closed", summary.lower())
            self.assertIn("open", summary.lower())
    
    def test_evaluate_alert_decision_success(self):
        """Test successful AI alert evaluation"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Applications have opened, matching user's monitoring intent",
            "confidence": 0.95,
            "summary": "Fellowship applications are now open"
        })
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when fellowship applications open",
                old_state={"status": "Applications closed"},
                new_state={"status": "Applications are now open"},
                changes={"status": {"old": "Applications closed", "new": "Applications are now open"}}
            )
            
            self.assertTrue(result["should_alert"])
            self.assertIn("reason", result)
            self.assertIn("confidence", result)
            self.assertIn("summary", result)
            self.assertGreaterEqual(result["confidence"], 0.0)
            self.assertLessEqual(result["confidence"], 1.0)
    
    def test_evaluate_alert_decision_no_alert(self):
        """Test AI evaluation deciding not to alert"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": False,
            "reason": "Change is minor formatting update, not related to application status",
            "confidence": 0.85,
            "summary": "Minor text formatting change detected"
        })
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when fellowship applications open",
                old_state={"status": "Applications  closed"},
                new_state={"status": "Applications closed"},
                changes={"status": {"old": "Applications  closed", "new": "Applications closed"}}
            )
            
            self.assertFalse(result["should_alert"])
            self.assertIn("reason", result)
    
    def test_evaluate_alert_decision_with_markdown_formatting(self):
        """Test AI evaluation with markdown-formatted JSON response"""
        mock_response = Mock()
        mock_response.text = '''```json
{
    "should_alert": true,
    "reason": "Deadline has been announced",
    "confidence": 0.9,
    "summary": "Application deadline set to March 15, 2026"
}
```'''
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me about application deadlines",
                old_state={"deadline": None},
                new_state={"deadline": "March 15, 2026"},
                changes={"deadline": {"old": None, "new": "March 15, 2026"}}
            )
            
            self.assertTrue(result["should_alert"])
            self.assertEqual(result["confidence"], 0.9)
    
    def test_evaluate_alert_decision_fallback_when_unavailable(self):
        """Test fallback behavior when AI service is unavailable"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when status changes",
                old_state={"status": "closed"},
                new_state={"status": "open"},
                changes={"status": {"old": "closed", "new": "open"}}
            )
            
            # Should use fallback logic
            self.assertTrue(result["should_alert"])  # Has changes
            self.assertEqual(result["confidence"], 0.5)
            self.assertIn("AI unavailable", result["reason"])
            self.assertIn("summary", result)
    
    def test_evaluate_alert_decision_fallback_no_changes(self):
        """Test fallback behavior with no changes"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when status changes",
                old_state={"status": "open"},
                new_state={"status": "open"},
                changes={}
            )
            
            # Should not alert when no changes
            self.assertFalse(result["should_alert"])
            self.assertEqual(result["confidence"], 0.5)
    
    def test_evaluate_alert_decision_handles_ai_error(self):
        """Test graceful error handling when AI call fails"""
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.side_effect = Exception("API rate limit exceeded")
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when status changes",
                old_state={"status": "closed"},
                new_state={"status": "open"},
                changes={"status": {"old": "closed", "new": "open"}}
            )
            
            # Should fall back to simple detection
            self.assertTrue(result["should_alert"])  # Has changes
            self.assertEqual(result["confidence"], 0.5)
            self.assertIn("failed", result["reason"].lower())
    
    def test_evaluate_alert_decision_handles_invalid_json(self):
        """Test handling of invalid JSON response from AI"""
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when status changes",
                old_state={"status": "closed"},
                new_state={"status": "open"},
                changes={"status": {"old": "closed", "new": "open"}}
            )
            
            # Should fall back to simple detection
            self.assertTrue(result["should_alert"])
            self.assertEqual(result["confidence"], 0.5)
    
    def test_evaluate_alert_decision_handles_missing_keys(self):
        """Test handling of AI response missing required keys"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Status changed"
            # Missing confidence and summary
        })
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when status changes",
                old_state={"status": "closed"},
                new_state={"status": "open"},
                changes={"status": {"old": "closed", "new": "open"}}
            )
            
            # Should fall back to simple detection
            self.assertTrue(result["should_alert"])
            self.assertEqual(result["confidence"], 0.5)
    
    def test_evaluate_alert_decision_complex_state_changes(self):
        """Test AI evaluation with multiple field changes"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Both application status and deadline changed, matching user intent",
            "confidence": 0.92,
            "summary": "Applications opened with deadline of March 15, 2026"
        })
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me when applications open",
                old_state={"status": "closed", "deadline": None, "batch": "Fall 2025"},
                new_state={"status": "open", "deadline": "March 15, 2026", "batch": "Spring 2026"},
                changes={
                    "status": {"old": "closed", "new": "open"},
                    "deadline": {"old": None, "new": "March 15, 2026"},
                    "batch": {"old": "Fall 2025", "new": "Spring 2026"}
                }
            )
            
            self.assertTrue(result["should_alert"])
            self.assertGreater(result["confidence"], 0.9)
    
    def test_evaluate_alert_decision_low_confidence(self):
        """Test AI evaluation with low confidence score"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Unclear if this change is significant",
            "confidence": 0.4,
            "summary": "Some text changed on the page"
        })
        
        with patch('apps.ai.services.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            service = AIConfigService()
            result = service.evaluate_alert_decision(
                user_description="Alert me about important changes",
                old_state={"text": "Some content"},
                new_state={"text": "Different content"},
                changes={"text": {"old": "Some content", "new": "Different content"}}
            )
            
            self.assertTrue(result["should_alert"])
            self.assertEqual(result["confidence"], 0.4)
    
    def test_fallback_summary_no_changes(self):
        """Test fallback summary generation with no changes"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            summary = service._generate_fallback_summary(
                old_state={"status": "open"},
                new_state={"status": "open"}
            )
            
            self.assertEqual(summary, "No changes detected")
    
    def test_fallback_summary_single_change(self):
        """Test fallback summary generation with single change"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            summary = service._generate_fallback_summary(
                old_state={"status": "closed"},
                new_state={"status": "open"}
            )
            
            self.assertIn("status", summary)
            self.assertIn("closed", summary)
            self.assertIn("open", summary)
    
    def test_fallback_summary_multiple_changes(self):
        """Test fallback summary generation with multiple changes"""
        with patch('apps.ai.services.settings') as mock_settings:
            mock_settings.LLM_API_KEY = None
            
            service = AIConfigService()
            summary = service._generate_fallback_summary(
                old_state={"status": "closed", "deadline": None, "batch": "Fall"},
                new_state={"status": "open", "deadline": "March 15", "batch": "Spring"}
            )
            
            self.assertIn("3 changes detected", summary)
