"""
Unit tests for AI-powered alert evaluation
"""
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from apps.ai.services import AIConfigService, AIConfigurationError


class AIAlertEvaluationTestCase(TestCase):
    """Test AI-powered alert decision making"""

    def setUp(self):
        """Set up test fixtures"""
        self.ai_service = AIConfigService()

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_should_alert(self, mock_genai):
        """Test AI correctly decides to alert when changes match intent"""
        # Mock AI response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Status changed to indicate applications are now open",
            "confidence": 0.95,
            "summary": "Applications are now open for the fellowship program."
        })
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data
        user_description = "Alert me when fellowship applications are open"
        old_state = {"status": "Applications closed"}
        new_state = {"status": "Now accepting applications"}
        changes = {
            "status": {
                "old": "Applications closed",
                "new": "Now accepting applications"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify
        self.assertTrue(result['should_alert'])
        self.assertGreater(result['confidence'], 0.9)
        self.assertIn('open', result['reason'].lower())
        self.assertIn('summary', result)
        self.assertIsInstance(result['summary'], str)

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_should_not_alert(self, mock_genai):
        """Test AI correctly decides NOT to alert when changes don't match intent"""
        # Mock AI response - wrong context
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": False,
            "reason": "Change is about review process, not application availability",
            "confidence": 0.88,
            "summary": "The review process status changed, but applications remain closed."
        })
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data - user wants to know about applications, but change is about reviews
        user_description = "Alert me when fellowship applications are open"
        old_state = {"status": "Applications closed", "review": "Not started"}
        new_state = {"status": "Applications closed", "review": "Open for review"}
        changes = {
            "review": {
                "old": "Not started",
                "new": "Open for review"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify
        self.assertFalse(result['should_alert'])
        self.assertGreater(result['confidence'], 0.8)
        self.assertIn('review', result['reason'].lower())

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_with_markdown_json(self, mock_genai):
        """Test AI response parsing when JSON is wrapped in markdown code blocks"""
        # Mock AI response with markdown formatting
        mock_response = Mock()
        mock_response.text = """```json
{
    "should_alert": true,
    "reason": "Deadline has been extended",
    "confidence": 0.92,
    "summary": "Application deadline extended to March 15, 2026."
}
```"""
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data
        user_description = "Alert me about deadline changes"
        old_state = {"deadline": "March 1, 2026"}
        new_state = {"deadline": "March 15, 2026"}
        changes = {
            "deadline": {
                "old": "March 1, 2026",
                "new": "March 15, 2026"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify - should successfully parse despite markdown
        self.assertTrue(result['should_alert'])
        self.assertIn('deadline', result['reason'].lower())
        self.assertGreater(result['confidence'], 0.9)

    def test_evaluate_alert_decision_ai_unavailable(self):
        """Test fallback behavior when AI service is unavailable"""
        # Set model to None to simulate unavailable AI
        self.ai_service.model = None

        # Test data
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        changes = {
            "status": {
                "old": "closed",
                "new": "open"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify fallback behavior
        self.assertTrue(result['should_alert'])  # Fallback alerts on any change
        self.assertEqual(result['confidence'], 0.5)
        self.assertIn('unavailable', result['reason'].lower())
        self.assertIn('summary', result)

    def test_evaluate_alert_decision_no_changes(self):
        """Test behavior when there are no changes"""
        # Set model to None to test fallback
        self.ai_service.model = None

        # Test data - no changes
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed"}
        new_state = {"status": "closed"}
        changes = {}

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify - should not alert when no changes
        self.assertFalse(result['should_alert'])

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_low_confidence(self, mock_genai):
        """Test AI response with low confidence score"""
        # Mock AI response with low confidence
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Possible change but unclear context",
            "confidence": 0.45,
            "summary": "Status may have changed."
        })
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data
        user_description = "Alert me when applications are open"
        old_state = {"status": "unknown"}
        new_state = {"status": "pending"}
        changes = {
            "status": {
                "old": "unknown",
                "new": "pending"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify - should still return the result even with low confidence
        self.assertTrue(result['should_alert'])
        self.assertLess(result['confidence'], 0.5)

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_multiple_changes(self, mock_genai):
        """Test AI evaluation with multiple field changes"""
        # Mock AI response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Both status and deadline changed indicating applications are now open",
            "confidence": 0.97,
            "summary": "Applications opened with deadline of March 15, 2026."
        })
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data - multiple changes
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed", "deadline": None}
        new_state = {"status": "open", "deadline": "March 15, 2026"}
        changes = {
            "status": {
                "old": "closed",
                "new": "open"
            },
            "deadline": {
                "old": None,
                "new": "March 15, 2026"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify
        self.assertTrue(result['should_alert'])
        self.assertGreater(result['confidence'], 0.95)
        self.assertIn('deadline', result['summary'].lower())

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_api_error(self, mock_genai):
        """Test fallback when AI API returns an error"""
        # Mock API error
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API rate limit exceeded")
        self.ai_service.model = mock_model

        # Test data
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        changes = {
            "status": {
                "old": "closed",
                "new": "open"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify fallback behavior
        self.assertTrue(result['should_alert'])  # Fallback alerts on any change
        self.assertEqual(result['confidence'], 0.5)
        self.assertIn('failed', result['reason'].lower())

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_invalid_json(self, mock_genai):
        """Test fallback when AI returns invalid JSON"""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.text = "This is not valid JSON at all"
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        changes = {
            "status": {
                "old": "closed",
                "new": "open"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify fallback behavior
        self.assertTrue(result['should_alert'])
        self.assertEqual(result['confidence'], 0.5)
        self.assertIn('failed', result['reason'].lower())

    @patch('apps.ai.services.genai')
    def test_evaluate_alert_decision_missing_fields(self, mock_genai):
        """Test fallback when AI response is missing required fields"""
        # Mock incomplete response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "should_alert": True,
            "reason": "Applications are open"
            # Missing confidence and summary
        })
        mock_response.candidates = [Mock(content=Mock(parts=[Mock()]))]
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        self.ai_service.model = mock_model

        # Test data
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        changes = {
            "status": {
                "old": "closed",
                "new": "open"
            }
        }

        # Execute
        result = self.ai_service.evaluate_alert_decision(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify fallback behavior due to missing fields
        self.assertTrue(result['should_alert'])
        self.assertEqual(result['confidence'], 0.5)
        self.assertIn('failed', result['reason'].lower())


class AIPromptBuildingTestCase(TestCase):
    """Test AI prompt construction"""

    def setUp(self):
        """Set up test fixtures"""
        self.ai_service = AIConfigService()

    def test_build_alert_evaluation_prompt(self):
        """Test alert evaluation prompt construction"""
        user_description = "Alert me when applications are open"
        old_state = {"status": "closed"}
        new_state = {"status": "open"}
        changes = {
            "status": {
                "old": "closed",
                "new": "open"
            }
        }

        prompt = self.ai_service._build_alert_evaluation_prompt(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify prompt contains all necessary information
        self.assertIn(user_description, prompt)
        self.assertIn("closed", prompt)
        self.assertIn("open", prompt)
        self.assertIn("should_alert", prompt)
        self.assertIn("confidence", prompt)
        self.assertIn("summary", prompt)
        self.assertIn("reason", prompt)

    def test_build_alert_evaluation_prompt_complex_state(self):
        """Test prompt building with complex state objects"""
        user_description = "Monitor fellowship application status"
        old_state = {
            "status": "closed",
            "deadline": None,
            "batch": "Fall 2025"
        }
        new_state = {
            "status": "open",
            "deadline": "March 15, 2026",
            "batch": "Spring 2026"
        }
        changes = {
            "status": {"old": "closed", "new": "open"},
            "deadline": {"old": None, "new": "March 15, 2026"},
            "batch": {"old": "Fall 2025", "new": "Spring 2026"}
        }

        prompt = self.ai_service._build_alert_evaluation_prompt(
            user_description=user_description,
            old_state=old_state,
            new_state=new_state,
            changes=changes
        )

        # Verify all fields are in prompt
        self.assertIn("status", prompt)
        self.assertIn("deadline", prompt)
        self.assertIn("batch", prompt)
        self.assertIn("March 15, 2026", prompt)
        self.assertIn("Spring 2026", prompt)
