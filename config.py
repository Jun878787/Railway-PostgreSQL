"""
Configuration file for North Sea Financial Bot
Contains environment variables and constants
"""

import os
from typing import List

# Bot configuration
def get_bot_token() -> str:
    """Get bot token from environment"""
    return os.getenv('BOT_TOKEN', '')

def get_group_id() -> int:
    """Get group ID from environment"""
    return int(os.getenv('GROUP_ID', '0'))

def get_group_ids() -> list:
    """Get group IDs from environment, support multiple IDs separated by comma"""
    group_ids_str = os.getenv('GROUP_ID', '')
    if group_ids_str:
        return [int(x.strip()) for x in group_ids_str.split(',') if x.strip()]
    return []

def get_admin_ids() -> List[int]:
    """Get admin IDs from environment"""
    admin_ids_str = os.getenv('ADMIN_IDS', '')
    if admin_ids_str:
        return [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
    return []

def get_google_maps_api_key() -> str:
    """Get Google Maps API key from environment"""
    return os.getenv('GOOGLE_MAPS_API_KEY', '')

def get_timezone() -> str:
    """Get timezone from environment"""
    return os.getenv('TZ', 'Asia/Taipei')

# Default constants
DEFAULT_EXCHANGE_RATE = 0.22  # Default CNY to USD rate

# Database configuration
DATABASE_PATH = "north_sea_bot.db"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'