"""
Main bot application for North Sea Financial Management Bot
Configures and initializes the Telegram bot with all handlers
"""

import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from database import DatabaseManager
from handlers import BotHandlers
import config

logger = logging.getLogger(__name__)

def create_bot():
    """Create and configure the bot application"""
    try:
        # Initialize database
        db_manager = DatabaseManager()
        
        # Initialize handlers
        bot_handlers = BotHandlers(db_manager)
        
        # Create application
        application = Application.builder().token(config.get_bot_token()).build()
        
        # Command handlers
        application.add_handler(CommandHandler("start", bot_handlers.start_command))
        application.add_handler(CommandHandler("help", bot_handlers.help_command))
        application.add_handler(CommandHandler("restart", bot_handlers.restart_command))
        
        # Callback query handler for inline keyboards
        application.add_handler(CallbackQueryHandler(bot_handlers.callback_query_handler))
        
        # Message handlers for transactions and commands
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            bot_handlers.handle_transaction_message
        ))
        
        # Error handler
        async def error_handler(update, context):
            """Handle errors"""
            try:
                logger.error(f"Update {update} caused error {context.error}")
                
                # Try to send error message to user
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ 系統發生錯誤，請稍後再試\n"
                        "如問題持續，請聯繫管理員"
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ Bot application created successfully")
        return application
        
    except Exception as e:
        logger.error(f"❌ Error creating bot application: {e}")
        raise

# Additional bot configuration
async def post_init(application):
    """Post initialization setup"""
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot initialized: @{bot_info.username} ({bot_info.first_name})")
        
        # Set bot commands
        from telegram import BotCommand
        commands = [
            BotCommand("start", "啟動機器人"),
            BotCommand("help", "顯示幫助信息"),
            BotCommand("restart", "重新啟動機器人（管理員）"),
        ]
        
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands set successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in post initialization: {e}")

def run_bot():
    """Run the bot (alternative entry point)"""
    try:
        import asyncio
        
        async def main():
            application = create_bot()
            await application.initialize()
            await post_init(application)
            await application.start()
            await application.updater.start_polling()
            
            # Keep running
            await asyncio.Event().wait()
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    run_bot()
