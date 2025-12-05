#!/usr/bin/env python3
"""
Google Gemini AI Studio Test Server
Test your Gemini API key and generate content
"""
import os
import sys
import json
import asyncio
from typing import Any

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    os.system("pip install mcp")
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio

try:
    import google.generativeai as genai
except ImportError:
    os.system("pip install google-generativeai")
    import google.generativeai as genai

app = Server("gemini-test")

# Get API key from environment
API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('LLM_API_KEY')

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Gemini test tools"""
    return [
        Tool(
            name="test_api_key",
            description="Test if your Gemini API key is valid and working",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "Gemini API key (optional, uses env var if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="generate_text",
            description="Generate text using Gemini AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to send to Gemini"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: gemini-1.5-flash)",
                        "default": "gemini-1.5-flash"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key (optional)"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_haunt_config",
            description="Use Gemini to generate a haunt configuration from natural language",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to monitor"
                    },
                    "description": {
                        "type": "string",
                        "description": "Natural language description of what to monitor"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key (optional)"
                    }
                },
                "required": ["url", "description"]
            }
        ),
        Tool(
            name="list_models",
            description="List available Gemini models",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "API key (optional)"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    # Get API key
    api_key = arguments.get('api_key') or API_KEY
    
    if not api_key:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "No API key provided",
                "hint": "Set GEMINI_API_KEY or LLM_API_KEY environment variable, or pass api_key parameter",
                "get_key_at": "https://aistudio.google.com/app/apikey"
            }, indent=2)
        )]
    
    try:
        genai.configure(api_key=api_key)
        
        if name == "test_api_key":
            # Try to list models to test the key
            try:
                models = list(genai.list_models())
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "✅ API key is valid!",
                        "models_available": len(models),
                        "sample_models": [m.name for m in models[:5]],
                        "message": "Your Gemini API key is working correctly!"
                    }, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "❌ API key is invalid",
                        "error": str(e),
                        "hint": "Get a valid key at https://aistudio.google.com/app/apikey"
                    }, indent=2)
                )]
        
        elif name == "generate_text":
            prompt = arguments['prompt']
            model_name = arguments.get('model', 'gemini-1.5-flash')
            
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "prompt": prompt,
                    "model": model_name,
                    "response": response.text,
                    "status": "success"
                }, indent=2)
            )]
        
        elif name == "generate_haunt_config":
            url = arguments['url']
            description = arguments['description']
            
            prompt = f"""Generate a JSON configuration for monitoring a website.

URL: {url}
User wants to: {description}

Generate a JSON object with these fields:
- selectors: CSS selectors for the elements to monitor (object with descriptive keys)
- normalization: Rules for normalizing the extracted text (object)
- truthy_values: Values that indicate a positive/true state (object)

Example format:
{{
  "selectors": {{
    "price": ".product-price",
    "status": ".availability-status"
  }},
  "normalization": {{
    "price": "remove_currency",
    "status": "lowercase"
  }},
  "truthy_values": {{
    "status": ["in stock", "available"]
  }}
}}

Return ONLY the JSON, no explanation."""

            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            # Try to parse the JSON
            try:
                config = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "url": url,
                        "description": description,
                        "config": config,
                        "status": "success",
                        "message": "Configuration generated successfully!"
                    }, indent=2)
                )]
            except json.JSONDecodeError:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "url": url,
                        "description": description,
                        "raw_response": response.text,
                        "status": "partial_success",
                        "message": "Generated response but couldn't parse as JSON"
                    }, indent=2)
                )]
        
        elif name == "list_models":
            models = list(genai.list_models())
            model_list = []
            
            for model in models:
                model_list.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description[:100] if model.description else "",
                    "supported_methods": model.supported_generation_methods
                })
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "total_models": len(model_list),
                    "models": model_list
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "hint": "Make sure your API key is valid and you have internet connection"
            }, indent=2)
        )]

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
