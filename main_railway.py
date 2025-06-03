#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
北金管家 North™Sea ᴍ8ᴘ - Telegram Financial Management Bot
Railway deployment version with PostgreSQL support
"""

import os
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Set timezone
import timezone_utils
timezone_utils.setup_timezone()

from telegram.ext import Application
from handlers import BotHandlers
from keyboards import BotKeyboards
import config

# Import PostgreSQL database manager directly
from railway_database import RailwayDatabaseManager as DatabaseManager

async def post_init(application):
    """Post initialization setup"""
    try:
        logger.info("🔧 Running post-initialization setup...")
        # Any additional setup can go here
        logger.info("✅ Post-initialization completed")
    except Exception as e:
        logger.error(f"❌ Post-initialization failed: {e}")

def main():
    """Main function to start the bot"""
    try:
        logger.info("🚀 Starting 北金管家 North™Sea ᴍ8ᴘ for Railway deployment...")
        
        # Initialize PostgreSQL database
        logger.info("🔗 Connecting to PostgreSQL database...")
        db_manager = DatabaseManager()
        logger.info("✅ PostgreSQL database connected successfully")
        
        # Create application
        bot_token = config.get_bot_token()
        if not bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables")
        
        application = Application.builder().token(bot_token).post_init(post_init).build()
        
        # Initialize handlers
        handlers = BotHandlers(db_manager)
        
        # Add handlers
        application.add_handler(handlers.get_start_handler())
        application.add_handler(handlers.get_help_handler())
        application.add_handler(handlers.get_restart_handler())
        application.add_handler(handlers.get_message_handler())
        application.add_handler(handlers.get_callback_handler())
        application.add_error_handler(handlers.get_error_handler())
        
        logger.info("✅ All handlers registered successfully")
        
        # Check for Railway environment
        port = int(os.getenv('PORT', 5000))
        railway_environment = os.getenv('RAILWAY_ENVIRONMENT')
        
        if railway_environment:
            logger.info(f"🚂 Railway environment detected: {railway_environment}")
            logger.info(f"🔗 Starting webhook server on port {port}")
            
            # Railway webhook mode
            webhook_url = os.getenv('RAILWAY_STATIC_URL', os.getenv('RAILWAY_PUBLIC_DOMAIN'))
            if webhook_url:
                webhook_url = f"https://{webhook_url}/webhook"
                application.run_webhook(
                    listen="0.0.0.0",
                    port=port,
                    webhook_url=webhook_url,
                    url_path="/webhook"
                )
            else:
                logger.warning("No webhook URL found, falling back to polling")
                application.run_polling(
                    timeout=30,
                    drop_pending_updates=True
                )
        else:
            logger.info("💻 Local development mode - using polling")
            application.run_polling(
                timeout=30,
                drop_pending_updates=True
            )
            
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()