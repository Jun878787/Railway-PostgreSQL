#!/usr/bin/env python3
"""
北金管家 North™Sea ᴍ8ᴘ - Telegram Financial Management Bot
Main entry point for the bot application
"""

import asyncio
import logging
import os
from aiohttp import web
from telegram import Update
from bot import create_bot
from database import DatabaseManager
from config import GROUP_ID

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全域應用程式變數
application = None

async def webhook_handler(request):
    """Handle incoming webhook requests"""
    logger.info("📨 Webhook handler called")
    try:
        # Get the application from the request's app
        app = request.app
        application = app.get('bot_application')
        
        if not application:
            logger.error("❌ Bot application not found in request")
            return web.Response(text="Bot not ready", status=503)
        
        logger.info("✅ Bot application found")
        
        # Get request content
        try:
            update_json = await request.json()
            logger.info(f"Received webhook data: {update_json}")
        except Exception as json_error:
            logger.error(f"Failed to parse JSON: {json_error}")
            return web.Response(text="Invalid JSON", status=400)
        
        if not update_json:
            logger.error("Empty update received")
            return web.Response(text="Empty update", status=400)
        
        try:
            update = Update.de_json(update_json, application.bot)
            if update:
                logger.info(f"Processing update ID: {update.update_id}")
                await application.process_update(update)
                logger.info("Update processed successfully")
            else:
                logger.error("Failed to create Update object")
                return web.Response(text="Invalid update format", status=400)
        except Exception as process_error:
            logger.error(f"Error processing update: {process_error}")
            return web.Response(text="Processing error", status=500)
        
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return web.Response(text="Error", status=500)

async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="Bot is running", status=200)

async def main():
    """Main function to start the bot"""
    global application
    
    logger.info("🚀 Starting 北金管家 North™Sea ᴍ8ᴘ...")
    
    try:
        # 初始化資料庫
        db_manager = DatabaseManager()
        
        # 創建機器人應用程式
        application = create_bot()
        
        # 啟動應用程式
        await application.initialize()
        await application.start()
        
        # 設置 webhook
        webhook_url = f"https://{os.getenv('REPL_SLUG')}-{os.getenv('REPL_OWNER')}.replit.app/webhook"
        if os.getenv('REPLIT_DOMAINS'):
            domains = os.getenv('REPLIT_DOMAINS').split(',')
            if domains:
                webhook_url = f"https://{domains[0]}/webhook"
        
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
        
        # 發送啟動通知
        group_id = int(GROUP_ID)
        
        try:
            await application.bot.send_message(
                chat_id=group_id,
                text="🤖 <b>北金管家機器人已啟動</b>\n\n"
                     "✅ 系統正常運行\n"
                     "🔧 所有功能已就緒\n"
                     "📊 準備開始記帳服務",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
        
        # 創建 web 應用程式
        app = web.Application()
        app['bot_application'] = application  # Store bot application for webhook handler
        app.router.add_post('/webhook', webhook_handler)
        app.router.add_get('/health', health_check)
        app.router.add_get('/', health_check)
        
        # 啟動 web 服務器
        port = int(os.getenv('PORT', 5000))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"✅ Webhook server started on port {port}")
        logger.info("✅ Bot started successfully with webhook!")
        
        # 保持服務器運行
        try:
            await asyncio.Future()  # 永久運行
        except asyncio.CancelledError:
            logger.info("🛑 Bot shutdown requested")
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise
    finally:
        # 清理資源
        if application:
            await application.stop()
            await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")