#!/usr/bin/env python3
"""
Watcher API MCP Server
Exposes Watcher database and API as callable tools for Kiro
"""
import os
import sys
import json
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Any

# Add MCP SDK (will be installed via uvx)
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    print("Installing mcp package...", file=sys.stderr)
    os.system("pip install mcp")
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'watcher'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    except Exception as e:
        return None

# Create MCP server
app = Server("watcher-api")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Watcher API tools"""
    return [
        Tool(
            name="get_haunts",
            description="Get all haunts from the database with their status",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_email": {
                        "type": "string",
                        "description": "Filter by user email (optional)"
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Filter by active status (optional)"
                    }
                }
            }
        ),
        Tool(
            name="get_haunt_details",
            description="Get detailed information about a specific haunt",
            inputSchema={
                "type": "object",
                "properties": {
                    "haunt_id": {
                        "type": "string",
                        "description": "UUID of the haunt"
                    }
                },
                "required": ["haunt_id"]
            }
        ),
        Tool(
            name="get_rss_items",
            description="Get RSS items (detected changes) for a haunt",
            inputSchema={
                "type": "object",
                "properties": {
                    "haunt_id": {
                        "type": "string",
                        "description": "UUID of the haunt"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of items to return (default 10)",
                        "default": 10
                    }
                },
                "required": ["haunt_id"]
            }
        ),
        Tool(
            name="get_users",
            description="Get list of users in the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of users to return (default 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_database_stats",
            description="Get statistics about the Watcher database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    conn = get_db_connection()
    if not conn:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Could not connect to database. Make sure Docker services are running.",
                "hint": "Run: docker-compose up -d"
            }, indent=2)
        )]
    
    try:
        cursor = conn.cursor()
        
        if name == "get_haunts":
            query = """
                SELECT h.id, h.name, h.url, h.is_active, h.is_public, 
                       h.scrape_interval, h.last_scraped_at, h.error_count,
                       u.email as owner_email, u.username as owner_username
                FROM haunts_haunt h
                JOIN authentication_user u ON h.owner_id = u.id
                WHERE 1=1
            """
            params = []
            
            if arguments.get('user_email'):
                query += " AND u.email = %s"
                params.append(arguments['user_email'])
            
            if arguments.get('is_active') is not None:
                query += " AND h.is_active = %s"
                params.append(arguments['is_active'])
            
            query += " ORDER BY h.created_at DESC LIMIT 20"
            
            cursor.execute(query, params)
            haunts = cursor.fetchall()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(haunts),
                    "haunts": [dict(h) for h in haunts]
                }, indent=2, default=str)
            )]
        
        elif name == "get_haunt_details":
            haunt_id = arguments['haunt_id']
            
            cursor.execute("""
                SELECT h.*, u.email as owner_email, u.username as owner_username,
                       COUNT(r.id) as rss_item_count
                FROM haunts_haunt h
                JOIN authentication_user u ON h.owner_id = u.id
                LEFT JOIN rss_rssitem r ON r.haunt_id = h.id
                WHERE h.id = %s
                GROUP BY h.id, u.email, u.username
            """, (haunt_id,))
            
            haunt = cursor.fetchone()
            
            if not haunt:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Haunt {haunt_id} not found"}, indent=2)
                )]
            
            return [TextContent(
                type="text",
                text=json.dumps(dict(haunt), indent=2, default=str)
            )]
        
        elif name == "get_rss_items":
            haunt_id = arguments['haunt_id']
            limit = arguments.get('limit', 10)
            
            cursor.execute("""
                SELECT id, title, summary, link, pub_date, created_at
                FROM rss_rssitem
                WHERE haunt_id = %s
                ORDER BY pub_date DESC
                LIMIT %s
            """, (haunt_id, limit))
            
            items = cursor.fetchall()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(items),
                    "items": [dict(i) for i in items]
                }, indent=2, default=str)
            )]
        
        elif name == "get_users":
            limit = arguments.get('limit', 10)
            
            cursor.execute("""
                SELECT id, email, username, created_at, 
                       email_notifications_enabled,
                       (SELECT COUNT(*) FROM haunts_haunt WHERE owner_id = u.id) as haunt_count
                FROM authentication_user u
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            users = cursor.fetchall()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "count": len(users),
                    "users": [dict(u) for u in users]
                }, indent=2, default=str)
            )]
        
        elif name == "get_database_stats":
            stats = {}
            
            # Count tables
            cursor.execute("SELECT COUNT(*) FROM authentication_user")
            stats['total_users'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) FROM haunts_haunt")
            stats['total_haunts'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) FROM haunts_haunt WHERE is_active = true")
            stats['active_haunts'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) FROM rss_rssitem")
            stats['total_rss_items'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) FROM haunts_folder")
            stats['total_folders'] = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT scrape_interval, COUNT(*) as count
                FROM haunts_haunt
                GROUP BY scrape_interval
                ORDER BY scrape_interval
            """)
            stats['haunts_by_interval'] = [dict(r) for r in cursor.fetchall()]
            
            return [TextContent(
                type="text",
                text=json.dumps(stats, indent=2)
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
                "type": type(e).__name__
            }, indent=2)
        )]
    
    finally:
        conn.close()

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
