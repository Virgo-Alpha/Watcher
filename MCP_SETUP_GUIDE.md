# MCP Servers Setup Guide for Watcher

## Overview

You now have **5 MCP servers** configured for Kiro:

1. **Watcher API Server** - Access your database and live data
2. **Kiroween Scoring Engine** - Halloween-themed gamification
3. **Gemini Test Server** - Test your AI Studio API key
4. **GitHub Server** - Fetch issues, wiki, and repository data
5. **Fetch Server** - Make HTTP requests to any URL

## Quick Start

### 1. Restart Kiro
The MCP servers will auto-connect when you restart Kiro or reload the window.

### 2. Test Your Setup
Try these commands in Kiro chat:

```
Test my Gemini API key
```

```
Get database stats from Watcher
```

```
Calculate my haunting power
```

## Server Details

### 🎃 Watcher API Server

**Purpose:** Access your Watcher database directly from Kiro

**Available Tools:**
- `get_haunts` - List all haunts with filters
- `get_haunt_details` - Get detailed info about a specific haunt
- `get_rss_items` - Get detected changes for a haunt
- `get_users` - List users in the system
- `get_database_stats` - Get overall database statistics

**Example Usage:**
```
Show me all active haunts
Get database stats
Show me the last 5 RSS items for haunt [id]
List all users
```

**Configuration:**
- Database: localhost:5432
- Requires Docker services running: `docker-compose up -d`

### 👻 Kiroween Scoring Engine

**Purpose:** Halloween-themed scoring and gamification

**Available Tools:**
- `calculate_score` - Calculate points for actions
- `check_achievements` - Check earned achievements
- `get_leaderboard` - Generate spooky leaderboard
- `get_halloween_message` - Get motivational messages
- `calculate_haunting_power` - Calculate power level

**Scoring Rules:**
- Haunt created: 10 points 👻
- Change detected: 15 points 🎃
- 7-day streak: 50 points 🔥
- Public haunt shared: 20 points 🌐
- And more...

**Achievements:**
- Ghost Whisperer (10 haunts)
- Night Owl (3 AM check)
- Change Hunter (50 changes)
- Marathon Haunter (30-day streak)
- And more...

**Example Usage:**
```
Calculate score for haunt_created
Check my achievements with 15 haunts created
Get a spooky Halloween message
Calculate my haunting power with 250 points
```

### 🤖 Gemini Test Server

**Purpose:** Test your Google AI Studio API key and generate content

**Available Tools:**
- `test_api_key` - Verify your API key works
- `generate_text` - Generate text with Gemini
- `generate_haunt_config` - Generate haunt config from natural language
- `list_models` - List available Gemini models

**Setup:**
1. Get API key: https://aistudio.google.com/app/apikey
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   # OR
   export LLM_API_KEY="your-key-here"
   ```
3. Or add to `.env` file

**Example Usage:**
```
Test my Gemini API key
Generate a haunt config for monitoring price on amazon.com
List available Gemini models
Generate text: Write a spooky haiku about web monitoring
```

### 🐙 GitHub Server

**Purpose:** Access GitHub repositories, issues, and wikis

**Available Tools:**
- Search repositories
- Get file contents
- List issues
- Get pull requests
- And more...

**Setup:**
1. Create GitHub Personal Access Token: https://github.com/settings/tokens
2. Set environment variable:
   ```bash
   export GITHUB_TOKEN="your-token-here"
   ```

**Example Usage:**
```
Search for Python web scraping repositories
Get the README from my Watcher repository
List open issues in my project
```

### 🌐 Fetch Server

**Purpose:** Make HTTP requests to any URL

**Available Tools:**
- `fetch` - Fetch content from any URL

**Example Usage:**
```
Fetch https://api.github.com/repos/torvalds/linux
Fetch the HTML from example.com
```

## Configuration Files

### Workspace Config
Location: `.kiro/settings/mcp.json`

This is your project-specific MCP configuration. It includes:
- Custom servers (Watcher API, Kiroween, Gemini)
- GitHub server
- Fetch server

### User Config
Location: `~/.kiro/settings/mcp.json`

Your global MCP configuration (already has fetch server).

**Priority:** Workspace config overrides user config.

## Environment Variables

Add these to your `.env` file or shell profile:

```bash
# Gemini AI Studio
export GEMINI_API_KEY="AIzaSy..."  # Get from https://aistudio.google.com/app/apikey

# GitHub
export GITHUB_TOKEN="ghp_..."  # Get from https://github.com/settings/tokens

# Database (already configured in docker-compose)
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="watcher"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
```

## Testing Each Server

### Test Watcher API
```bash
# Make sure Docker is running
docker-compose up -d

# In Kiro chat:
Get database stats
Show me all haunts
```

### Test Kiroween Scoring
```bash
# In Kiro chat:
Calculate score for haunt_created
Get a spooky Halloween message
Calculate my haunting power with 100 points
```

### Test Gemini
```bash
# Set API key first
export GEMINI_API_KEY="your-key"

# In Kiro chat:
Test my Gemini API key
Generate text: Write a haiku about ghosts
```

### Test GitHub
```bash
# Set token first
export GITHUB_TOKEN="your-token"

# In Kiro chat:
Search for MCP server repositories
```

### Test Fetch
```bash
# In Kiro chat:
Fetch https://api.github.com/zen
```

## Troubleshooting

### Server Not Connecting
1. Check Kiro's MCP panel (View → MCP Servers)
2. Look for error messages
3. Restart Kiro
4. Check server logs

### Database Connection Failed
```bash
# Make sure Docker services are running
docker-compose ps

# Start if not running
docker-compose up -d

# Check database is accessible
docker-compose exec db psql -U postgres -d watcher -c "SELECT 1"
```

### API Key Not Working
```bash
# Test Gemini key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_KEY"

# Test GitHub token
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user
```

### Python Dependencies Missing
```bash
pip3 install mcp google-generativeai psycopg2-binary
```

## Auto-Approved Tools

These tools don't require confirmation:

**Watcher API:**
- get_database_stats
- get_haunts
- get_users

**Kiroween:**
- calculate_score
- get_halloween_message
- calculate_haunting_power

**Gemini:**
- test_api_key
- list_models

**GitHub:**
- search_repositories
- get_file_contents

**Fetch:**
- fetch

## Advanced Usage

### Custom Queries
```
Get all active haunts for user test@example.com
Show me haunts with scrape interval of 60 minutes
Calculate leaderboard for top 5 users
```

### Combining Tools
```
Get database stats, then calculate haunting power for the top user
Test my Gemini key, then generate a haunt config for monitoring GitHub stars
```

### Debugging
```
List all available MCP tools
Show me the schema for get_haunts
Test connection to Watcher database
```

## Next Steps

### Add More Servers

**AWS Server:**
```bash
uvx awslabs.aws-documentation-mcp-server@latest
```

**Filesystem Server:**
```bash
uvx mcp-server-filesystem
```

**Brave Search:**
```bash
uvx mcp-server-brave-search
```

### Create Custom Servers

See the examples in `.kiro/mcp-servers/` for templates.

### Modify Existing Servers

Edit the Python files in `.kiro/mcp-servers/` and restart Kiro.

## Security Notes

- API keys are stored in environment variables (not in config files)
- Database credentials are for local development only
- GitHub tokens should have minimal required permissions
- Auto-approve only safe, read-only operations

## Resources

- MCP Documentation: https://modelcontextprotocol.io
- Kiro MCP Guide: https://kiro.dev/docs/mcp
- Gemini API: https://ai.google.dev/
- GitHub API: https://docs.github.com/en/rest

## Support

If you encounter issues:
1. Check the MCP panel in Kiro
2. Look at server logs
3. Verify environment variables
4. Restart Kiro
5. Check this guide for troubleshooting steps

Happy haunting! 👻🎃
