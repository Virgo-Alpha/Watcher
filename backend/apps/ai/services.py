"""
AI service business logic for configuration generation and summaries using Google Gemini API.

This service uses Google AI Studio API (Gemini) for:
- Converting natural language descriptions to CSS selectors and monitoring configurations
- Generating human-readable summaries of detected changes

Configuration:
- LLM_API_KEY: Google AI Studio API key (get from https://aistudio.google.com/app/apikey)
- Model: gemini-2.5-flash (fast, cost-effective model for structured outputs)
"""
import json
import logging
from typing import Dict, Any
from django.conf import settings
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .config_schema import ConfigurationValidator, ConfigurationStorage, HauntConfig

logger = logging.getLogger(__name__)


class AIConfigurationError(Exception):
    """Raised when AI configuration generation fails"""
    pass


class AIConfigService:
    """
    Service for AI-powered configuration generation and change summaries using Google Gemini.
    
    Requires LLM_API_KEY environment variable set to a Google AI Studio API key.
    Get your API key from: https://aistudio.google.com/app/apikey
    """
    
    def __init__(self):
        if not settings.LLM_API_KEY:
            logger.warning("LLM_API_KEY not configured - AI features will be disabled")
            self.model = None
        else:
            try:
                genai.configure(api_key=settings.LLM_API_KEY)
                # Use Gemini 2.0 Flash - latest stable model
                self.model = genai.GenerativeModel('models/gemini-2.0-flash')
                logger.info("Google Gemini AI service initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Google Gemini: %s", str(e))
                self.model = None
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.model is not None
    
    def generate_config(self, url: str, description: str) -> Dict[str, Any]:
        """
        Generate monitoring configuration from natural language description
        
        Args:
            url: The URL to monitor
            description: Natural language description of what to monitor
            
        Returns:
            Dictionary containing selectors, normalization rules, and truthy values
            
        Raises:
            AIConfigurationError: If configuration generation fails
        """
        if not self.is_available():
            raise AIConfigurationError("AI service is not available - LLM_API_KEY not configured")
        
        try:
            # Build the full prompt combining system and user prompts for Gemini
            full_prompt = f"{self._get_system_prompt()}\n\n{self._build_config_prompt(url, description)}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Slightly higher to avoid recitation
                    max_output_tokens=1000,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                raise AIConfigurationError(
                    f"AI response was blocked or empty (finish_reason: {finish_reason}). "
                    "Try rephrasing your description."
                )
            
            config_text = response.text.strip()
            
            # Extract JSON from response (handle potential markdown formatting)
            if "```json" in config_text:
                config_text = config_text.split("```json")[1].split("```")[0].strip()
            elif "```" in config_text:
                config_text = config_text.split("```")[1].split("```")[0].strip()
            
            config = json.loads(config_text)
            
            # Validate the generated configuration using the schema validator
            errors = ConfigurationValidator.validate_raw_config(config)
            if errors:
                raise AIConfigurationError(f"Generated configuration is invalid: {'; '.join(errors)}")
            
            logger.info(f"Successfully generated AI configuration for URL: {url}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI-generated configuration: {e}")
            raise AIConfigurationError(f"Invalid JSON in AI response: {e}")
        except Exception as e:
            logger.error(f"AI configuration generation failed: {e}")
            raise AIConfigurationError(f"Configuration generation failed: {e}")
    
    def generate_summary(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """
        Generate human-friendly summary of state changes
        
        Args:
            old_state: Previous state values
            new_state: Current state values
            
        Returns:
            Human-readable summary of changes
            
        Raises:
            AIConfigurationError: If summary generation fails
        """
        if not self.is_available():
            # Fallback to simple change description
            return self._generate_fallback_summary(old_state, new_state)
        
        try:
            system_prompt = "You are a helpful assistant that creates concise, human-readable summaries of website changes. Keep summaries to 1-2 sentences maximum."
            full_prompt = f"{system_prompt}\n\n{self._build_summary_prompt(old_state, new_state)}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=150,
                )
            )
            
            summary = response.text.strip()
            logger.info("Successfully generated AI summary for state change")
            return summary
            
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            # Fallback to simple change description
            return self._generate_fallback_summary(old_state, new_state)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for configuration generation"""
        return """Create a monitoring config as JSON."""
    
    def _build_config_prompt(self, url: str, description: str) -> str:
        """Build the prompt for configuration generation"""
        # Use a very simple, direct prompt to avoid recitation filter
        return f"""Task: Monitor "{description}" on {url}

Output JSON with:
- selectors: CSS selectors for elements (format: "css:.selector" or just ".selector")
- normalization: text cleaning rules
- truthy_values: positive state values

IMPORTANT RULES:
1. normalization "type" must be one of: "text", "number", "date", "boolean"
2. normalization "transform" (optional) must be one of: "lowercase", "uppercase", "strip"
3. Do NOT use types like "attribute" or "list"
4. Do NOT use transforms like "remove_non_numeric", "replace", "int"
5. For extracting attributes, use regex_pattern in normalization instead

Example structure:
{{"selectors": {{"status": ".status-text"}}, "normalization": {{"status": {{"type": "text", "transform": "lowercase", "strip": true}}}}, "truthy_values": {{"status": ["open", "active"]}}}}

Your JSON:"""
    
    def _build_summary_prompt(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """Build the prompt for summary generation"""
        changes = []
        for key in set(old_state.keys()) | set(new_state.keys()):
            old_val = old_state.get(key, "N/A")
            new_val = new_state.get(key, "N/A")
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
        
        changes_text = "\n".join(changes)
        
        return f"""The following changes were detected on a monitored website:

{changes_text}

Please provide a concise, human-readable summary of what changed. Focus on the most important changes and use natural language. Keep it to 1-2 sentences maximum."""
    
    def evaluate_alert_decision(
        self,
        user_description: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to evaluate if changes warrant an alert based on user intent.
        This is the core of AI-powered change detection.
        
        Args:
            user_description: Original natural language description from user
            old_state: Previous scraped state
            new_state: Current scraped state
            changes: Detected changes dictionary
            
        Returns:
            Dictionary with:
                - should_alert (bool): Whether to alert the user
                - reason (str): Explanation of the decision
                - confidence (float): Confidence score 0.0-1.0
                - summary (str): Human-readable summary of changes
        """
        if not self.is_available():
            # Fallback to simple rule-based detection
            return {
                "should_alert": len(changes) > 0,
                "reason": "AI unavailable, alerting on any change",
                "confidence": 0.5,
                "summary": self._generate_fallback_summary(old_state, new_state)
            }
        
        try:
            prompt = self._build_alert_evaluation_prompt(
                user_description,
                old_state,
                new_state,
                changes
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent decisions
                    max_output_tokens=300,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Extract JSON from response
            result_text = response.text.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            # Validate response structure
            required_keys = ["should_alert", "reason", "confidence", "summary"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"AI response missing required keys: {required_keys}")
            
            logger.info(
                f"AI alert decision: should_alert={result['should_alert']}, "
                f"confidence={result['confidence']}, reason={result['reason']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"AI alert evaluation failed: {e}")
            # Fallback to simple detection
            return {
                "should_alert": len(changes) > 0,
                "reason": f"AI evaluation failed: {str(e)}",
                "confidence": 0.5,
                "summary": self._generate_fallback_summary(old_state, new_state)
            }
    
    def _build_alert_evaluation_prompt(
        self,
        user_description: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> str:
        """Build prompt for AI alert evaluation"""
        changes_text = json.dumps(changes, indent=2)
        old_state_text = json.dumps(old_state, indent=2)
        new_state_text = json.dumps(new_state, indent=2)
        
        return f"""You are evaluating whether a user should be alerted about website changes.

USER'S MONITORING INTENT:
"{user_description}"

PREVIOUS STATE:
{old_state_text}

CURRENT STATE:
{new_state_text}

DETECTED CHANGES:
{changes_text}

TASK:
Determine if these changes match what the user wants to monitor. Consider:
1. Does the change align with the user's stated intent?
2. Is this a meaningful change or just noise?
3. Would the user want to be notified about this?

Respond with JSON:
{{
  "should_alert": true or false,
  "reason": "brief explanation of why you made this decision",
  "confidence": 0.0 to 1.0 (how confident you are in this decision),
  "summary": "1-2 sentence human-readable summary of what changed"
}}

Your JSON response:"""
    
    def _generate_fallback_summary(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """Generate a simple fallback summary when AI is not available"""
        changes = []
        for key in set(old_state.keys()) | set(new_state.keys()):
            old_val = old_state.get(key, "N/A")
            new_val = new_state.get(key, "N/A")
            if old_val != new_val:
                changes.append(f"{key} changed from '{old_val}' to '{new_val}'")
        
        if not changes:
            return "No changes detected"
        elif len(changes) == 1:
            return changes[0]
        else:
            return f"{len(changes)} changes detected: " + "; ".join(changes[:3])
    
    def parse_config(self, config_dict: Dict[str, Any]) -> 'HauntConfig':
        """
        Parse and validate a configuration dictionary into a HauntConfig object
        
        Args:
            config_dict: Raw configuration dictionary
            
        Returns:
            HauntConfig object
            
        Raises:
            AIConfigurationError: If configuration is invalid
        """
        try:
            return ConfigurationValidator.parse_config(config_dict)
        except ValueError as e:
            raise AIConfigurationError(str(e))
    
    def config_to_dict(self, config: 'HauntConfig') -> Dict[str, Any]:
        """
        Convert a HauntConfig object to a dictionary for storage
        
        Args:
            config: HauntConfig object
            
        Returns:
            Dictionary representation of the configuration
        """
        return ConfigurationStorage.config_to_dict(config)