#!/usr/bin/env python3
"""
北金管家 North™Sea ᴍ8ᴘ - Telegram Financial Management Bot
Simple polling mode version
"""

import logging
import os
from bot import create_bot
from database import DatabaseManager
from config import BOT_TOKEN, GROUP_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def post_init(application):
    """Post initialization setup"""
    try:
        from config import get_group_ids
        group_ids = get_group_ids()
        for group_id in group_ids:
            await application.bot.send_message(
                chat_id=group_id,
                text="🤖 北金管家機器人已啟動\n\n"
                     "✅ 系統正常運行\n"
                     "🔧 所有功能已就緒\n"
                     "📊 準備開始記帳服務",
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")

def main():
    """Main function to start the bot in polling mode"""
    try:
        logger.info("🚀 Starting 北金管家 North™Sea ᴍ8ᴘ in simple polling mode...")
        
        # Initialize database
        db_manager = DatabaseManager()
        
        # Create bot application
        application = create_bot()
        
        # Add post init hook
        application.post_init = post_init
        
        # Start with polling - this will handle the event loop properly
        logger.info("✅ Starting bot with polling mode...")
        application.run_polling(
            poll_interval=1.0,
            timeout=10,
            bootstrap_retries=5,
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=10,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    main()