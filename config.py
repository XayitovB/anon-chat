import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file. Get token from @BotFather")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "chat_bot.db")

# Admin Configuration
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", 0))
if SUPER_ADMIN_ID == 0:
    raise ValueError("SUPER_ADMIN_ID must be set in .env file")

# Note: Regular admin IDs are now stored in database, not in .env file
# Only SUPER_ADMIN_ID comes from .env file for security

# Backward compatibility: ADMIN_IDS (includes super admin)
# Regular admins are loaded from database at runtime
ADMIN_IDS = [SUPER_ADMIN_ID] if SUPER_ADMIN_ID != 0 else []

# Note: Mandatory channels are now stored in database, not in .env file
# This will be populated from database when needed

# Bot settings
MAX_WAITING_TIME = 300  # 5 minutes waiting for a partner
RATING_REQUIRED = True  # Require rating after chat ends

# Security Settings (optional)
MAX_MESSAGES_PER_MINUTE = int(os.getenv("MAX_MESSAGES_PER_MINUTE", 20))
MAX_ACTIONS_PER_MINUTE = int(os.getenv("MAX_ACTIONS_PER_MINUTE", 30))
COMMAND_COOLDOWN = int(os.getenv("COMMAND_COOLDOWN", 1))

# Bot Info
BOT_NAME = os.getenv("BOT_NAME", "Anonymous Chat Bot")
BOT_DESCRIPTION = os.getenv("BOT_DESCRIPTION", "Secure anonymous chat bot for Telegram")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")
if BOT_USERNAME == "your_bot_username" or not BOT_USERNAME:
    raise ValueError("BOT_USERNAME must be set in .env file. Get username from @BotFather")

def reload_config():
    """Reload configuration from .env file"""
    # Reload .env file
    load_dotenv(override=True)
    
    # Note: Admin IDs and mandatory channels are now managed via database, not .env file
