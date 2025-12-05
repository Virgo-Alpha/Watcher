#!/usr/bin/env python3
"""
Kiroween Scoring Engine MCP Server
Halloween-themed scoring and gamification for Watcher
"""
import os
import sys
import json
import asyncio
from datetime import datetime
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

app = Server("kiroween-scoring")

# Halloween-themed scoring rules
SCORING_RULES = {
    "haunt_created": {
        "points": 10,
        "emoji": "👻",
        "message": "Summoned a new haunt!"
    },
    "haunt_active_24h": {
        "points": 5,
        "emoji": "🕐",
        "message": "Haunt survived 24 hours!"
    },
    "change_detected": {
        "points": 15,
        "emoji": "🎃",
        "message": "Caught a change in the wild!"
    },
    "email_sent": {
        "points": 3,
        "emoji": "📧",
        "message": "Delivered a spooky notification!"
    },
    "folder_organized": {
        "points": 5,
        "emoji": "📁",
        "message": "Organized the haunted mansion!"
    },
    "public_haunt_shared": {
        "points": 20,
        "emoji": "🌐",
        "message": "Shared your haunting with the world!"
    },
    "ai_summary_generated": {
        "points": 8,
        "emoji": "🤖",
        "message": "AI conjured a summary!"
    },
    "keyboard_shortcut_used": {
        "points": 2,
        "emoji": "⌨️",
        "message": "Power user move!"
    },
    "streak_7_days": {
        "points": 50,
        "emoji": "🔥",
        "message": "7-day haunting streak!"
    },
    "first_haunt": {
        "points": 25,
        "emoji": "🎉",
        "message": "Welcome to the haunted web!"
    }
}

# Achievement badges
ACHIEVEMENTS = {
    "ghost_whisperer": {
        "name": "Ghost Whisperer",
        "description": "Created 10 haunts",
        "emoji": "👻",
        "requirement": {"haunts_created": 10}
    },
    "night_owl": {
        "name": "Night Owl",
        "description": "Checked haunts at 3 AM",
        "emoji": "🦉",
        "requirement": {"late_night_check": True}
    },
    "change_hunter": {
        "name": "Change Hunter",
        "description": "Detected 50 changes",
        "emoji": "🎯",
        "requirement": {"changes_detected": 50}
    },
    "organizer": {
        "name": "Haunted Librarian",
        "description": "Created 5 folders",
        "emoji": "📚",
        "requirement": {"folders_created": 5}
    },
    "community_spirit": {
        "name": "Community Spirit",
        "description": "Made 3 haunts public",
        "emoji": "🌟",
        "requirement": {"public_haunts": 3}
    },
    "speed_demon": {
        "name": "Speed Demon",
        "description": "Used keyboard shortcuts 100 times",
        "emoji": "⚡",
        "requirement": {"keyboard_shortcuts": 100}
    },
    "marathon_haunter": {
        "name": "Marathon Haunter",
        "description": "30-day streak",
        "emoji": "🏆",
        "requirement": {"streak_days": 30}
    }
}

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Kiroween scoring tools"""
    return [
        Tool(
            name="calculate_score",
            description="Calculate Halloween-themed score for an action",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": list(SCORING_RULES.keys()),
                        "description": "The action to score"
                    },
                    "multiplier": {
                        "type": "number",
                        "description": "Score multiplier (default 1.0)",
                        "default": 1.0
                    }
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="check_achievements",
            description="Check which achievements a user has earned",
            inputSchema={
                "type": "object",
                "properties": {
                    "stats": {
                        "type": "object",
                        "description": "User statistics",
                        "properties": {
                            "haunts_created": {"type": "integer"},
                            "changes_detected": {"type": "integer"},
                            "folders_created": {"type": "integer"},
                            "public_haunts": {"type": "integer"},
                            "keyboard_shortcuts": {"type": "integer"},
                            "streak_days": {"type": "integer"},
                            "late_night_check": {"type": "boolean"}
                        }
                    }
                },
                "required": ["stats"]
            }
        ),
        Tool(
            name="get_leaderboard",
            description="Generate a spooky leaderboard",
            inputSchema={
                "type": "object",
                "properties": {
                    "users": {
                        "type": "array",
                        "description": "List of users with their scores",
                        "items": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "score": {"type": "integer"}
                            }
                        }
                    }
                },
                "required": ["users"]
            }
        ),
        Tool(
            name="get_halloween_message",
            description="Get a random Halloween-themed motivational message",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": ["spooky", "encouraging", "funny", "mysterious"],
                        "description": "The mood of the message",
                        "default": "encouraging"
                    }
                }
            }
        ),
        Tool(
            name="calculate_haunting_power",
            description="Calculate a user's overall 'haunting power' level",
            inputSchema={
                "type": "object",
                "properties": {
                    "total_score": {"type": "integer"},
                    "achievements_count": {"type": "integer"},
                    "active_haunts": {"type": "integer"}
                },
                "required": ["total_score"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "calculate_score":
        action = arguments['action']
        multiplier = arguments.get('multiplier', 1.0)
        
        if action not in SCORING_RULES:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown action: {action}"}, indent=2)
            )]
        
        rule = SCORING_RULES[action]
        points = int(rule['points'] * multiplier)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "action": action,
                "points": points,
                "emoji": rule['emoji'],
                "message": rule['message'],
                "multiplier": multiplier
            }, indent=2)
        )]
    
    elif name == "check_achievements":
        stats = arguments['stats']
        earned = []
        
        for achievement_id, achievement in ACHIEVEMENTS.items():
            requirements = achievement['requirement']
            earned_achievement = True
            
            for req_key, req_value in requirements.items():
                user_value = stats.get(req_key, 0)
                if isinstance(req_value, bool):
                    if user_value != req_value:
                        earned_achievement = False
                        break
                elif user_value < req_value:
                    earned_achievement = False
                    break
            
            if earned_achievement:
                earned.append({
                    "id": achievement_id,
                    "name": achievement['name'],
                    "description": achievement['description'],
                    "emoji": achievement['emoji']
                })
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "total_achievements": len(ACHIEVEMENTS),
                "earned_count": len(earned),
                "earned": earned,
                "completion_percentage": round(len(earned) / len(ACHIEVEMENTS) * 100, 1)
            }, indent=2)
        )]
    
    elif name == "get_leaderboard":
        users = arguments['users']
        sorted_users = sorted(users, key=lambda x: x['score'], reverse=True)
        
        leaderboard = []
        for i, user in enumerate(sorted_users[:10], 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👻"
            leaderboard.append({
                "rank": i,
                "emoji": rank_emoji,
                "username": user['username'],
                "score": user['score']
            })
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "title": "🎃 Kiroween Leaderboard 🎃",
                "leaderboard": leaderboard
            }, indent=2)
        )]
    
    elif name == "get_halloween_message":
        mood = arguments.get('mood', 'encouraging')
        
        messages = {
            "spooky": [
                "👻 Your haunts are watching... always watching...",
                "🕷️ Something wicked this way comes... it's a website change!",
                "🦇 The night is dark and full of changes...",
                "💀 Death to missed updates! Your haunts never sleep!"
            ],
            "encouraging": [
                "🎃 Keep haunting! You're doing great!",
                "⭐ Every haunt brings you closer to mastery!",
                "🌟 Your vigilance is legendary!",
                "✨ The web trembles before your watchful eye!"
            ],
            "funny": [
                "👻 Boo! Did I scare you? No? Well, your haunts will scare those websites!",
                "🎭 Why did the ghost haunt the website? To catch the BOO-gs!",
                "🤡 Your haunts are so good, they're scary good!",
                "🎪 Step right up to the greatest show on web: Your haunts!"
            ],
            "mysterious": [
                "🔮 The spirits whisper of changes yet to come...",
                "🌙 In the moonlight, your haunts reveal hidden truths...",
                "🗝️ You hold the key to the web's secrets...",
                "📜 Ancient scrolls foretold your haunting prowess..."
            ]
        }
        
        import random
        message = random.choice(messages.get(mood, messages['encouraging']))
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "mood": mood,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    elif name == "calculate_haunting_power":
        total_score = arguments['total_score']
        achievements_count = arguments.get('achievements_count', 0)
        active_haunts = arguments.get('active_haunts', 0)
        
        # Calculate power level (0-100)
        score_component = min(total_score / 10, 50)  # Max 50 from score
        achievement_component = min(achievements_count * 5, 30)  # Max 30 from achievements
        haunt_component = min(active_haunts * 2, 20)  # Max 20 from active haunts
        
        power_level = int(score_component + achievement_component + haunt_component)
        
        # Determine rank
        if power_level >= 90:
            rank = "👑 Legendary Haunter"
        elif power_level >= 75:
            rank = "🎃 Master Haunter"
        elif power_level >= 60:
            rank = "👻 Expert Haunter"
        elif power_level >= 40:
            rank = "🕷️ Skilled Haunter"
        elif power_level >= 20:
            rank = "🦇 Apprentice Haunter"
        else:
            rank = "🌱 Novice Haunter"
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "power_level": power_level,
                "rank": rank,
                "breakdown": {
                    "from_score": int(score_component),
                    "from_achievements": int(achievement_component),
                    "from_active_haunts": int(haunt_component)
                },
                "next_rank_at": min(power_level + 15, 100)
            }, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
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
