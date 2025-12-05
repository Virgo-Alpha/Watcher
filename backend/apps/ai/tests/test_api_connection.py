"""
Tests for Google Gemini API connection and basic functionality
"""
import os
from django.test import TestCase
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class GeminiAPIConnectionTest(TestCase):
    """Test Google Gemini API connection"""
    
    def setUp(self):
        """Set up API key"""
        self.api_key = os.environ.get('LLM_API_KEY')
        if not self.api_key:
            self.skipTest("LLM_API_KEY not configured")
    
    def test_api_key_is_configured(self):
        """Test that API key is present"""
        self.assertIsNotNone(self.api_key)
        self.assertTrue(self.api_key.startswith('AIzaSy'))
    
    def test_simple_generation(self):
        """Test simple text generation"""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        response = model.generate_content("Say hello in 3 words")
        
        self.assertIsNotNone(response)
        self.assertTrue(len(response.text) > 0)
        print(f"\n✓ Simple generation works: {response.text}")
    
    def test_json_generation_simple(self):
        """Test JSON generation with simple prompt"""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        prompt = 'Return this JSON: {"status": "open", "count": 5}'
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500,
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        self.assertIsNotNone(response)
        self.assertIn('status', response.text)
        print(f"\n✓ JSON generation works: {response.text[:100]}")
    
    def test_monitoring_config_generation(self):
        """Test generating a monitoring configuration"""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        prompt = """Generate a JSON config for monitoring a website.

Task: Monitor "job applications status" on https://example.com/careers

Return JSON with this structure:
{
  "selectors": {"status": ".job-status"},
  "normalization": {"status": {"type": "text", "transform": "lowercase", "strip": true}},
  "truthy_values": {"status": ["open", "hiring"]}
}

Your JSON:"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        self.assertIsNotNone(response)
        self.assertTrue(len(response.text) > 0)
        
        # Check if response was blocked
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason
            print(f"\n✓ Monitoring config generation - Finish reason: {finish_reason}")
            print(f"Response preview: {response.text[:200]}")
            
            # finish_reason should be 1 (STOP) for success
            self.assertEqual(finish_reason, 1, f"Response was blocked with finish_reason: {finish_reason}")
        else:
            self.fail("No candidates in response")
