"""
AI service business logic for configuration generation and summaries
"""
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from openai import OpenAI
from rest_framework import serializers
from .config_schema import ConfigurationValidator, ConfigurationStorage, HauntConfig

logger = logging.getLogger(__name__)


class AIConfigurationError(Exception):
    """Raised when AI configuration generation fails"""
    pass


class AIConfigService:
    """Service for AI-powered configuration generation and change summaries"""
    
    def __init__(self):
        if not settings.LLM_API_KEY:
            logger.warning("LLM_API_KEY not configured - AI features will be disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.LLM_API_KEY)
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
    
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
            prompt = self._build_config_prompt(url, description)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=1000
            )
            
            config_text = response.choices[0].message.content.strip()
            
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
            prompt = self._build_summary_prompt(old_state, new_state)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise, human-readable summaries of website changes. Keep summaries to 1-2 sentences maximum."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info("Successfully generated AI summary for state change")
            return summary
            
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            # Fallback to simple change description
            return self._generate_fallback_summary(old_state, new_state)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for configuration generation"""
        return """You are an expert web scraping assistant. Your job is to analyze a website URL and natural language description to generate a JSON configuration for monitoring specific elements.

The configuration should include:
1. "selectors": CSS selectors or XPath expressions to extract data
2. "normalization": Rules for cleaning/normalizing extracted values
3. "truthy_values": Values that indicate "interesting" or "open" states

Return ONLY valid JSON with no additional text or markdown formatting.

Example output:
{
  "selectors": {
    "status": "css:.status-indicator",
    "deadline": "css:.deadline-date"
  },
  "normalization": {
    "status": {
      "type": "text",
      "transform": "lowercase",
      "strip": true
    },
    "deadline": {
      "type": "date",
      "format": "%Y-%m-%d"
    }
  },
  "truthy_values": {
    "status": ["open", "accepting", "available", "active"]
  }
}"""
    
    def _build_config_prompt(self, url: str, description: str) -> str:
        """Build the prompt for configuration generation"""
        return f"""URL: {url}

Description: {description}

Please generate a monitoring configuration that will track the elements described. Focus on:
- Selecting the most reliable CSS selectors for the described elements
- Normalizing text values to be consistent (lowercase, trimmed)
- Identifying which values indicate "open", "available", or "interesting" states
- Keeping the configuration simple and focused on the key elements mentioned

Generate the JSON configuration now:"""
    
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
            return f"{len(changes)} fields changed: {', '.join(changes[:2])}{'...' if len(changes) > 2 else ''}"
    
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