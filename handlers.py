"""
Message and callback handlers for the North Sea Financial Bot
Handles all user interactions and bot responses
"""

import logging
import asyncio
import sys
import os
from datetime import datetime, date
from typing import Optional, Dict
import re

from telegram import Update, Message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Add current directory to path and import timezone utilities
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timezone_utils

try:
    from database import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from railway_database import RailwayDatabaseManager
except ImportError:
    RailwayDatabaseManager = None
from keyboards import BotKeyboards
from utils import TransactionParser, ReportFormatter, ValidationUtils
from list_formatter import ListFormatter
import config

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.list_formatter = ListFormatter()
        self.keyboards = BotKeyboards()
        self.parser = TransactionParser()
        self.formatter = ReportFormatter()
        self.user_states = {}
    
    async def _send_message_with_menu(self, update, text: str, parse_mode='HTML'):
        """Helper function to send message with main menu button"""
        keyboard = BotKeyboards.get_main_inline_keyboard()
        if update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )

        self.validator = ValidationUtils()
        # User state tracking for multi-step operations
        self.user_states = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Add user to database
            await self.db.add_user(
                user_id=user.id,
                username=user.username,
                display_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Welcome message
            welcome_text = f"""🎉 <b>歡迎使用北金管家 North™Sea ᴍ8ᴘ</b>

👋 你好 {user.first_name}！

🤖 我是專業的多幣別財務管理機器人，提供以下功能：

💰 <b>記帳功能:</b>
• 支援台幣(TWD)和人民幣(CNY)
• 快速記錄收入和支出
• 支援日期指定和代記帳

📊 <b>報表功能:</b>
• 個人月度報表
• 群組統計報表
• 歷史數據查詢

💱 <b>匯率管理:</b>
• 自訂匯率設定
• 歷史匯率查詢

💵 <b>資金管理:</b>
• 公桶/私人資金分類
• 餘額查詢統計

⚙️ <b>快速開始:</b>
點擊下方按鈕或輸入 /help 查看完整指令
"""
            
            # Send welcome with inline keyboard
            await update.message.reply_text(
                welcome_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_main_inline_keyboard()
            )
            
            # Set custom keyboard for all chats
            await update.message.reply_text(
                "🎯 快速操作鍵盤已啟用",
                reply_markup=self.keyboards.get_currency_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ 啟動失敗，請稍後再試")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """📖 <b>北金管家機器人指令說明</b>

🔸 <b>基本指令</b>
/start - 啟動機器人，顯示主選單
/restart - 重新啟動機器人（僅管理員）
/help - 顯示此幫助信息

🔸 <b>報表指令</b>
<code>📊個人報表</code> - 顯示個人當月收支報表
<code>📊組別報表</code> - 顯示此群組的收支總計
<code>📊車隊總表</code> - 顯示全群組的收支總計
<code>📚歷史報表</code> - 查看過去月份的報表
<code>初始化報表</code> - 清空所有個人報表數據

🔸 <b>記帳指令 (多種格式輸入方式)</b>
<code>TW+數字</code> - 記錄台幣收入
<code>TW-數字</code> - 記錄台幣支出
<code>CN+數字</code> - 記錄人民幣收入
<code>CN-數字</code> - 記錄人民幣支出
<code>台幣+數字</code> - 記錄台幣收入
<code>人民幣-數字</code> - 記錄人民幣支出

🔸 <b>日期記帳</b>
<code>日期 TW+數字</code> - 記錄特定日期台幣收入
<code>日期 TW-數字</code> - 記錄特定日期台幣支出
<code>日期 CN+數字</code> - 記錄特定日期人民幣收入
<code>日期 CN-數字</code> - 記錄特定日期人民幣支出

🔸 <b>為其他用戶記帳</b>
<code>@用戶名 日期 TW+數字</code> - 為指定用戶記錄台幣收入
<code>@用戶名 日期 TW-數字</code> - 為指定用戶記錄台幣支出

🔸 <b>資金管理</b>
<code>公桶+數字</code> - 增加公桶資金
<code>公桶-數字</code> - 減少公桶資金
<code>私人+數字</code> - 增加私人資金
<code>私人-數字</code> - 減少私人資金

🔸 <b>匯率設置</b>
<code>設置匯率 數字</code> - 設置今日匯率
<code>設置"日期"匯率 數字</code> - 設置指定日期匯率

🔸 <b>刪除記錄</b>
<code>刪除"日期"TW金額</code> - 刪除指定日期台幣記錄
<code>刪除"日期"CN金額</code> - 刪除指定日期人民幣記錄
<code>刪除"月份"TW報表</code> - 刪除整個月份的台幣記錄
<code>刪除"月份"CN報表</code> - 刪除整個月份的人民幣記錄

🔸 <b>其他設置</b>
<code>使用者設定 名稱</code> - 設置報表標題名稱
<code>歡迎詞設定 內容</code> - 設置新成員加入群組時的歡迎訊息
<code>列表</code> - 回覆訊息文本並輸入列表可格式化當前的文本內容

💡 <b>提示:</b>
• 所有指令都支援群組和私聊使用
• 日期格式支援: MM/DD, YYYY-MM-DD
• 金額支援小數點，但建議使用整數
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode='HTML',
            reply_markup=self.keyboards.get_main_inline_keyboard()
        )
    
    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command (admin only)"""
        user_id = update.effective_user.id
        
        # If no admin IDs configured, allow group admins or creator
        admin_ids = config.get_admin_ids()
        if len(admin_ids) > 0 and user_id not in admin_ids:
            await update.message.reply_text("❌ 您沒有權限執行此操作")
            return
        elif len(admin_ids) == 0:
            # Check if user is group admin when no specific admin IDs configured
            chat = update.effective_chat
            if chat.type in ['group', 'supergroup']:
                try:
                    member = await context.bot.get_chat_member(chat.id, user_id)
                    if member.status not in ['administrator', 'creator']:
                        keyboard = BotKeyboards.get_main_inline_keyboard()
                        await update.message.reply_text(
                            text="❌ 您沒有權限執行此操作",
                            reply_markup=keyboard
                        )
                        return
                except Exception:
                    keyboard = BotKeyboards.get_main_inline_keyboard()
                    await update.message.reply_text(
                        text="❌ 無法驗證權限",
                        reply_markup=keyboard
                    )
                    return
        
        try:
            await update.message.reply_text("🔄 系統刷新中...")
            
            # Perform system refresh only (no actual restart)
            import asyncio
            await asyncio.sleep(1)
            
            try:
                # Refresh database connection
                if hasattr(self.db, 'init_database'):
                    self.db.init_database()
                    
                # Clear any cached user data
                if hasattr(context, 'user_data'):
                    context.user_data.clear()
                if hasattr(context, 'chat_data'):
                    context.chat_data.clear()
                
                # Send completion message
                await update.message.reply_text(
                    "✅ <b>系統刷新完成</b>\n\n"
                    "🚀 所有功能已恢復正常\n"
                    "📊 繼續提供記帳服務",
                    parse_mode='HTML'
                )
                logger.info("Bot system refresh completed")
                
            except Exception as e:
                logger.error(f"Failed to complete refresh process: {e}")
                await update.message.reply_text("❌ 系統刷新失敗")
            
        except Exception as e:
            logger.error(f"Error in restart command: {e}")
            await update.message.reply_text("❌ 重啟失敗")
    
    async def handle_transaction_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle transaction recording messages"""
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"📨 Message handler called")

            user = update.effective_user
            chat = update.effective_chat
            text = update.message.text

            logger.info(f"👤 User: {user.id if user else 'None'}, Chat: {chat.id if chat else 'None'}")
            logger.info(f"💬 Text: {text}")

            if not text:
                logger.warning("No text in message")
                return

            # Check for financial record message format first
            financial_record = self._parse_financial_record(text)
            if financial_record:
                await self._handle_financial_record(update, context, financial_record)
                return

            # Parse transaction
            logger.info(f"🔍 Attempting to parse transaction text: '{text}'")
            transaction_data = self.parser.parse_transaction(text, user.id)
            logger.info(f"📊 Transaction parsing result: {transaction_data}")

            if not transaction_data:
                # Check for restart command with bot mention
                if text == "/restart@NorthSea88_Bot":
                    await self.restart_command(update, context)
                    return
                
                # Check for keyboard button commands
                if text in ["📝選單", "📊出款報表"]:
                    await self._handle_keyboard_buttons(update, context, text)
                    return
                
                # Check if it's a fund management command
                fund_data = self.parser.parse_fund_command(text)
                if fund_data:
                    await self._handle_fund_command(update, context, fund_data)
                    return
                
                # Check for other commands
                await self._handle_other_commands(update, context, text)
                return
            
            # Add user to database if not exists
            await self.db.add_user(
                user_id=user.id,
                username=user.username,
                display_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Auto-detect and save group name if it's a group chat
            if chat.type in ['group', 'supergroup'] and chat.title:
                await self.db.add_or_update_group(chat.id, chat.title)
            
            # Handle mentioned user
            target_user_id = user.id
            if transaction_data['mentioned_user']:
                # TODO: Implement user lookup by username
                # For now, use the current user
                target_user_id = user.id
            
            # Add transaction
            success = await self.db.add_transaction(
                user_id=target_user_id,
                group_id=chat.id if chat.type in ['group', 'supergroup'] else 0,
                transaction_date=transaction_data['date'],
                currency=transaction_data['currency'],
                amount=transaction_data['amount'],
                transaction_type=transaction_data['transaction_type'],
                created_by=user.id
            )
            
            if success:
                currency_symbol = "💰" if transaction_data['currency'] == 'TW' else "💴"
                type_symbol = "+" if transaction_data['transaction_type'] == 'income' else "-"
                date_str = transaction_data['date'].strftime('%m/%d')
                
                success_msg = f"""✅ <b>記帳成功</b>

{currency_symbol} <b>{transaction_data['currency']}{type_symbol}{transaction_data['amount']:,.0f}</b>
📅 日期: {date_str}
👤 用戶: {user.first_name}
"""
                
                await update.message.reply_text(success_msg, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ 記帳失敗，請稍後再試")
                
        except Exception as e:
            logger.error(f"Error handling transaction: {e}")
            await update.message.reply_text("❌ 處理交易時發生錯誤")
    
    async def _handle_keyboard_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
        """Handle custom keyboard button presses"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if button_text == "📝選單":
                main_text = """🏠 <b>北金管家主選單</b>

歡迎使用多幣別財務管理系統！

請選擇您需要的功能：

📊 <b>報表功能</b> - 查看個人或群組財務報表
📚 <b>歷史查詢</b> - 查詢過往月份數據
💱 <b>匯率管理</b> - 設置和查看匯率
⚙️ <b>系統設置</b> - 個人化設定選項
"""
                await update.message.reply_text(
                    main_text,
                    parse_mode='HTML',
                    reply_markup=self.keyboards.get_main_inline_keyboard()
                )
            
            elif button_text == "📊出款報表":
                payout_text = """📊 <b>出款報表</b>

請選擇要查看的報表類型：

📅 <b>當日報表</b> - 查看今日出款記錄
📊 <b>當月報表</b> - 查看本月出款統計
"""
                await update.message.reply_text(
                    payout_text,
                    parse_mode='HTML',
                    reply_markup=self.keyboards.get_payout_report_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error handling keyboard button: {e}")
            await update.message.reply_text("❌ 按鈕操作失敗")
    
    async def _handle_fund_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, fund_data: Dict):
        """Handle fund management commands"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Get current fund balance
            current_balance = await self.db.get_fund_balance(fund_data['fund_type'], chat.id)
            
            # Calculate new balance
            current_amount = current_balance.get('TW', 0)  # Default to TWD
            if fund_data['operation'] == 'income':
                new_amount = current_amount + fund_data['amount']
            else:
                new_amount = current_amount - fund_data['amount']
            
            # Update fund
            success = await self.db.update_fund(
                fund_type=fund_data['fund_type'],
                amount=new_amount,
                currency='TW',  # Default currency for funds
                group_id=chat.id,
                updated_by=user.id
            )
            
            if success:
                fund_name = "公桶" if fund_data['fund_type'] == 'public' else "私人"
                operation_text = "增加" if fund_data['operation'] == 'income' else "減少"
                
                msg = f"""✅ <b>{fund_name}資金{operation_text}成功</b>

💰 {operation_text}金額: {fund_data['amount']:,.0f}
💳 當前餘額: {new_amount:,.0f}
👤 操作人員: {user.first_name}
"""
                await update.message.reply_text(msg, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ 資金操作失敗")
                
        except Exception as e:
            logger.error(f"Error handling fund command: {e}")
            await update.message.reply_text("❌ 資金操作錯誤")
    
    async def _handle_other_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle other text commands"""
        try:
            text = text.strip()
            
            # Exchange rate setting - enhanced detection
            if ('設定' in text and '匯率' in text) or text.startswith('匯率設定') or any(text.startswith(curr) for curr in ['TWD', 'CNY']):
                await self._handle_exchange_rate_setting(update, context, text)
                return
            
            # Delete commands
            if text.startswith('刪除'):
                await self._handle_delete_commands(update, context, text)
                return
            
            # User settings
            if text.startswith('使用者設定'):
                await self._handle_user_settings(update, context, text)
                return
            
            # Welcome message setting
            if text.startswith('歡迎詞設定'):
                await self._handle_welcome_setting(update, context, text)
                return
            
            # List formatting
            if text == '列表':
                await self._handle_list_formatting(update, context)
                return
            
            # Fleet report
            if text == '車隊報表':
                await self._handle_fleet_report(update, context)
                return
            
            # Initialize report
            if text == '初始化報表':
                await self._handle_initialize_report(update, context)
                return
            
            # Check if user is in a state waiting for clear report input
            user_id = update.effective_user.id if update.effective_user else None
            if user_id and user_id in self.user_states:
                user_state = self.user_states[user_id]
                if user_state.get('step') == 'waiting_date':
                    await self._process_clear_report_date(update, context, user_state, text)
                    return
                elif user_state.get('step') == 'waiting_confirmation':
                    await self._process_clear_report_confirmation(update, context, user_state, text)
                    return
                
        except Exception as e:
            logger.error(f"Error handling other commands: {e}")
    
    async def _process_clear_report_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: dict, date_input: str):
        """Process date input for clear report operations"""
        try:
            user_id = update.effective_user.id
            action = user_state.get('action')
            
            # Validate date format
            import re
            date_pattern = r'^(\d{1,2})$|^(\d{1,2}/\d{1,2})$'
            if not re.match(date_pattern, date_input.strip()):
                await update.message.reply_text(
                    "❌ 日期格式錯誤\n\n"
                    "請輸入正確格式：\n"
                    "• 月份：<code>6</code>\n"
                    "• 日期：<code>6/12</code>",
                    parse_mode='HTML'
                )
                return
            
            # Parse date
            date_str = date_input.strip()
            
            # Update user state for confirmation
            self.user_states[user_id] = {
                'action': action,
                'step': 'waiting_confirmation',
                'date': date_str
            }
            
            # Generate confirmation message based on action
            action_names = {
                'clear_personal': '個人報表',
                'clear_group': '組別報表', 
                'clear_fleet': '車隊總表'
            }
            
            action_name = action_names.get(action, '報表')
            
            # Create confirmation message
            text = f"""⚠️ <b>確認清空 {action_name}</b>

您確定要清空 <code>{date_str}</code> 的{action_name}嗎？

⚠️ <b>此操作不可復原！</b>

請輸入 <code>確認</code> 來執行刪除，或輸入其他任何內容取消操作。"""
            
            await update.message.reply_text(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error processing clear report date: {e}")
            # Clear user state on error
            if user_id in self.user_states:
                del self.user_states[user_id]
            await update.message.reply_text("❌ 處理日期輸入時發生錯誤")
    
    async def _process_clear_report_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: dict, confirmation_input: str):
        """Process confirmation input for clear report operations"""
        try:
            user_id = update.effective_user.id
            action = user_state.get('action')
            date_str = user_state.get('date')
            
            # Clear user state
            if user_id in self.user_states:
                del self.user_states[user_id]
            
            # Check if user confirmed
            if confirmation_input.strip() == '確認':
                # Execute the clear operation
                success = await self._execute_clear_report(user_id, action, date_str)
                
                if success:
                    action_names = {
                        'clear_personal': '個人報表',
                        'clear_group': '組別報表', 
                        'clear_fleet': '車隊總表'
                    }
                    action_name = action_names.get(action, '報表')
                    
                    await update.message.reply_text(
                        f"✅ <b>清空完成</b>\n\n"
                        f"已成功清空 <code>{date_str}</code> 的{action_name}",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text("❌ 清空操作失敗，請稍後再試")
            else:
                # User cancelled
                await update.message.reply_text("🔙 已取消清空操作")
                
        except Exception as e:
            logger.error(f"Error processing clear report confirmation: {e}")
            # Clear user state on error
            if user_id in self.user_states:
                del self.user_states[user_id]
            await update.message.reply_text("❌ 處理確認輸入時發生錯誤")
    
    async def _execute_clear_report(self, user_id: int, action: str, date_str: str) -> bool:
        """Execute the actual clear report operation"""
        try:
            # Parse date string to get month and day
            import re
            from datetime import datetime
            
            current_year = datetime.now().year
            
            if '/' in date_str:
                # Format: MM/DD
                month, day = map(int, date_str.split('/'))
                target_date = datetime(current_year, month, day).date()
                
                # Delete transactions for specific date
                if action == 'clear_personal':
                    return await self.db.delete_transaction(user_id, target_date, None, None)
                elif action == 'clear_group':
                    # Delete group transactions for specific date - implementation needed
                    return True  # Placeholder
                elif action == 'clear_fleet':
                    # Delete all transactions for specific date - implementation needed  
                    return True  # Placeholder
            else:
                # Format: MM (monthly clear)
                month = int(date_str)
                
                # Delete transactions for entire month
                if action == 'clear_personal':
                    return await self.db.delete_monthly_transactions(user_id, month, current_year)
                elif action == 'clear_group':
                    # Delete group transactions for month - implementation needed
                    return True  # Placeholder
                elif action == 'clear_fleet':
                    # Delete all transactions for month - implementation needed
                    return True  # Placeholder
                    
            return False
            
        except Exception as e:
            logger.error(f"Error executing clear report: {e}")
            return False
    
    async def _handle_exchange_rate_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle exchange rate setting commands"""
        try:
            import re
            from datetime import datetime, date
            
            user = update.effective_user
            user_id = user.id
            
            # Pattern 1: 設定匯率33.00 (current date, TWD)
            match1 = re.match(r'設定匯率(\d+\.?\d*)', text)
            if match1:
                rate = float(match1.group(1))
                today = date.today()
                success = await self.db.set_exchange_rate(today, rate, user_id, 'TW')
                if success:
                    await update.message.reply_text(
                        f"✅ 台幣匯率設定成功\n"
                        f"日期: {today.strftime('%Y-%m-%d')}\n"
                        f"匯率: {rate}",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text("❌ 匯率設定失敗")
                return
            
            # Pattern 2: 設定6/1匯率33.00 (specific date, TWD)
            match2 = re.match(r'設定(\d{1,2}/\d{1,2})匯率(\d+\.?\d*)', text)
            if match2:
                date_str = match2.group(1)
                rate = float(match2.group(2))
                month, day = map(int, date_str.split('/'))
                current_year = date.today().year
                rate_date = date(current_year, month, day)
                
                success = await self.db.set_exchange_rate(rate_date, rate, user_id, 'TW')
                if success:
                    await update.message.reply_text(
                        f"✅ 台幣匯率設定成功\n"
                        f"日期: {rate_date.strftime('%Y-%m-%d')}\n"
                        f"匯率: {rate}",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text("❌ 匯率設定失敗")
                return
            
            # Pattern 3: 設定CN匯率7.5 (current date, CNY)
            match3 = re.match(r'設定CN匯率(\d+\.?\d*)', text)
            if match3:
                rate = float(match3.group(1))
                today = date.today()
                success = await self.db.set_exchange_rate(today, rate, user_id, 'CN')
                if success:
                    await update.message.reply_text(
                        f"✅ 人民幣匯率設定成功\n"
                        f"日期: {today.strftime('%Y-%m-%d')}\n"
                        f"匯率: {rate}",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text("❌ 匯率設定失敗")
                return
            
            # Pattern 4: 設定6/1CN匯率7.0 (specific date, CNY)
            match4 = re.match(r'設定(\d{1,2}/\d{1,2})CN匯率(\d+\.?\d*)', text)
            if match4:
                date_str = match4.group(1)
                rate = float(match4.group(2))
                month, day = map(int, date_str.split('/'))
                current_year = date.today().year
                rate_date = date(current_year, month, day)
                
                success = await self.db.set_exchange_rate(rate_date, rate, user_id, 'CN')
                if success:
                    await update.message.reply_text(
                        f"✅ 人民幣匯率設定成功\n"
                        f"日期: {rate_date.strftime('%Y-%m-%d')}\n"
                        f"匯率: {rate}",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text("❌ 匯率設定失敗")
                return
            
            # If no pattern matches, show help
            await update.message.reply_text(
                "❌ 匯率設定格式不正確\n\n"
                "支援的格式：\n"
                "• <code>設定匯率33.00</code> - 今日台幣匯率\n"
                "• <code>設定6/1匯率33.00</code> - 指定日期台幣匯率\n"
                "• <code>設定CN匯率7.5</code> - 今日人民幣匯率\n"
                "• <code>設定6/1CN匯率7.0</code> - 指定日期人民幣匯率",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error handling exchange rate setting: {e}")
            await update.message.reply_text("❌ 匯率設定失敗")
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user = update.effective_user
            chat = update.effective_chat
            
            if data == "personal_report":
                await self._show_personal_report(query, user)
            elif data == "group_report":
                await self._show_group_report(query, chat)
            elif data == "history_report":
                await self._show_history_options(query)
            elif data == "exchange_rate":
                await self._show_exchange_rate_menu(query)
            elif data == "fleet_report":
                await self._show_fleet_report(query)
            elif data == "settings":
                await self._show_settings_menu(query)
            elif data == "main_menu":
                await self._show_main_menu(query)
            elif data == "money_actions":
                await self._show_money_actions(query)
            elif data == "report_display":
                await self._show_report_display(query)
            elif data == "settings_menu":
                await self._show_settings_menu(query)
            elif data == "command_help":
                await self._show_command_help(query)
            elif data == "currency_tw":
                await self._show_tw_help(query)
            elif data == "currency_cn":
                await self._show_cn_help(query)
            elif data == "fund_public":
                await self._show_public_fund_help(query)
            elif data == "fund_private":
                await self._show_private_fund_help(query)
            elif data == "clear_reports":
                await self._show_clear_reports_menu(query)
            elif data == "user_settings":
                await self._show_user_settings(query)
            elif data == "current_exchange_rates":
                await self._show_current_exchange_rates(query)
            elif data == "set_tw_rate":
                await self._prompt_tw_rate_setting(query)
            elif data == "set_cn_rate":
                await self._prompt_cn_rate_setting(query)
            elif data == "set_date_rate":
                await self._prompt_date_rate_setting(query)
            elif data.startswith("clear_"):
                await self._handle_clear_report(query, data)
            elif data.startswith("help_"):
                await self._show_help_content(query, data)
            elif data.startswith("role_"):
                await self._show_role_management(query, data)
            elif data.startswith("month_"):
                month = int(data.split("_")[1])
                await self._show_monthly_report(query, user, month)
            elif data == "history_personal":
                await self._show_history_options(query)
            elif data == "history_group":
                await self._show_history_options(query)
            elif data == "history_fleet":
                await self._show_history_options(query)
            elif data == "group_current":
                await self._show_group_report(query, query.message.chat)
            elif data == "fleet_current":
                await self._show_fleet_report(query)
            elif data == "payout_daily":
                await self._show_daily_payout_report(query)
            elif data == "payout_monthly":
                await self._show_monthly_payout_report(query)
            else:
                keyboard = BotKeyboards.get_main_inline_keyboard()
                await query.edit_message_text(
                    text="❌ 未知的操作",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            try:
                keyboard = BotKeyboards.get_main_inline_keyboard()
                await query.edit_message_text(
                    text="❌ 操作失敗",
                    reply_markup=keyboard
                )
            except:
                pass
    
    async def _show_personal_report(self, query, user):
        """Show personal financial report for current group"""
        try:
            # Get group ID from the callback query
            chat = query.message.chat
            group_id = chat.id if chat.type in ['group', 'supergroup'] else None
            
            # Get current month transactions for this group only
            transactions = await self.db.get_user_transactions(user.id, group_id)
            
            # Add group context to report title
            group_name = chat.title if group_id else "個人"
            
            # Format report using personal report formatter
            from utils import PersonalReportFormatter
            personal_formatter = PersonalReportFormatter()
            report = personal_formatter.format_personal_report(
                transactions, 
                user.first_name or user.username or f"User{user.id}",
                group_name
            )
            
            keyboard = BotKeyboards.get_personal_report_keyboard()
            await query.edit_message_text(
                report,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing personal report: {e}")
            keyboard = BotKeyboards.get_main_inline_keyboard()
            await query.edit_message_text(
                text="❌ 獲取個人報表失敗",
                reply_markup=keyboard
            )
    
    async def _show_group_report(self, query, chat):
        """Show group financial report"""
        try:
            if chat.type not in ['group', 'supergroup']:
                keyboard = BotKeyboards.get_main_inline_keyboard()
                await query.edit_message_text(
                    text="❌ 此功能僅限群組使用",
                    reply_markup=keyboard
                )
                return
            
            # Get current month group transactions
            transactions = await self.db.get_group_transactions(chat.id)
            
            # Import the updated formatting function
            from new_report_format import format_new_group_report
            
            # Format report using updated function with daily exchange rates
            report = await format_new_group_report(
                transactions,
                chat.title or "群組",
                self.db
            )
            
            keyboard = BotKeyboards.get_group_report_keyboard()
            
            # Debug: Log the actual report content being sent
            logger.info(f"Original report HTML: {repr(report[:200])}")
            
            # Check if HTML tags are being corrupted before sending
            import re
            html_tags = re.findall(r'<[^>]+>', report[:500])
            logger.info(f"HTML tags found: {html_tags[:5]}")
            
            await query.edit_message_text(
                report,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing group report: {e}")
            keyboard = BotKeyboards.get_main_inline_keyboard()
            await query.edit_message_text(
                text="❌ 獲取群組報表失敗",
                reply_markup=keyboard
            )
    
    async def _show_history_options(self, query):
        """Show history report options"""
        try:
            text = "📚 <b>歷史報表查詢</b>\n\n請選擇要查詢的月份："
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_month_selection_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing history options: {e}")
            await query.edit_message_text("❌ 顯示歷史選項失敗")
    
    async def _show_exchange_rate_info(self, query):
        """Show current exchange rate information"""
        try:
            from datetime import date
            
            current_rate = await self.db.get_exchange_rate()
            cn_rate = current_rate if current_rate else config.DEFAULT_EXCHANGE_RATE
            
            # Default rates (these could be fetched from external API in production)
            tw_rate = 1.0  # TWD to USD base rate
            
            rate_text = f"""💱 <b>當前匯率資訊</b>

台幣匯率: <code>1 USD = {tw_rate:.2f} TWD</code>
人民幣匯率: <code>1 CNY = {cn_rate:.2f} TWD</code>

💡 <b>設置匯率:</b>

<code>TW匯率{tw_rate:.2f}</code>
<code>CN匯率{cn_rate:.2f}</code>
<code>月/日TW匯率數值</code>
<code>月/日CN匯率數值</code>

💡 <b>範例:</b>
• <code>CN匯率4.35</code> - 設置人民幣匯率
• <code>6/1CN匯率4.40</code> - 設置6月1日人民幣匯率
"""
            
            await query.edit_message_text(
                rate_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_main_inline_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing exchange rate: {e}")
            await query.edit_message_text("❌ 獲取匯率資訊失敗")
    
    async def _show_settings_menu(self, query):
        """Show settings menu"""
        try:
            settings_text = """⚙️ <b>設置選單</b>

請選擇要設置的項目：

👤 <b>使用者設定</b> - 設置顯示名稱
💱 <b>匯率設定</b> - 管理匯率設定
👋 <b>歡迎詞設定</b> - 設定群組歡迎訊息
🗑️ <b>清空報表</b> - 清除歷史數據
"""
            
            await query.edit_message_text(
                settings_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_settings_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing settings menu: {e}")
            await query.edit_message_text("❌ 顯示設置選單失敗")
    
    async def _show_main_menu(self, query):
        """Show main menu"""
        try:
            main_text = """🏠 <b>北金管家主選單</b>

歡迎使用多幣別財務管理系統！

請選擇您需要的功能：

📊 <b>報表功能</b> - 查看個人或群組財務報表
📚 <b>歷史查詢</b> - 查詢過往月份數據
💱 <b>匯率管理</b> - 設置和查看匯率
⚙️ <b>系統設置</b> - 個人化設定選項
"""
            
            await query.edit_message_text(
                main_text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_main_inline_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            await query.edit_message_text("❌ 顯示主選單失敗")

    async def _show_fleet_report(self, query):
        """Show fleet report via callback - aggregates ALL groups"""
        try:
            from datetime import datetime
            from fleet_report_formatter import FleetReportFormatter
            
            now = datetime.now()
            year = now.year
            month = now.month
            
            # Use comprehensive fleet report formatter
            fleet_formatter = FleetReportFormatter(self.db)
            report = await fleet_formatter.format_comprehensive_fleet_report(month, year)
            
            keyboard = BotKeyboards.get_fleet_report_keyboard()
            await query.edit_message_text(
                report,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing fleet report: {e}")
            keyboard = BotKeyboards.get_main_inline_keyboard()
            await query.edit_message_text(
                text="❌ 車隊報表顯示失敗",
                reply_markup=keyboard
            )

    async def _show_monthly_report(self, query, user, month):
        """Show monthly report for specific month"""
        try:
            chat = query.message.chat
            now = datetime.now()
            year = now.year
            
            # Get user transactions for the specified month
            transactions = await self.db.get_user_transactions(
                user_id=user.id,
                group_id=chat.id,
                month=month,
                year=year
            )
            
            # Format the report
            user_name = user.first_name or user.username or "用戶"
            chat_name = chat.title if hasattr(chat, 'title') and chat.title else "群組"
            
            # Format report using personal report formatter
            from utils import PersonalReportFormatter
            personal_formatter = PersonalReportFormatter()
            report = personal_formatter.format_personal_report(
                transactions, 
                user_name,
                chat_name
            )
            
            keyboard = BotKeyboards.get_personal_report_keyboard()
            await query.edit_message_text(
                text=report,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing monthly report: {e}")
            keyboard = BotKeyboards.get_main_inline_keyboard()
            await query.edit_message_text(
                text="❌ 月份報表生成失敗",
                reply_markup=keyboard
            )

    async def _show_money_actions(self, query):
        """Show money actions menu"""
        try:
            text = "💰 <b>金額異動選單</b>\n\n請選擇操作類型："
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_money_actions_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing money actions: {e}")
            await query.edit_message_text("❌ 顯示金額異動選單失敗")

    async def _show_report_display(self, query):
        """Show report display menu"""
        try:
            text = "📊 <b>報表顯示選單</b>\n\n請選擇要查看的報表類型："
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_report_display_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing report display: {e}")
            await query.edit_message_text("❌ 顯示報表選單失敗")

    async def _show_command_help(self, query):
        """Show command help menu"""
        try:
            text = """🔣 <b>指令說明選單</b>

請選擇您的身份以查看相應的指令說明："""
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_command_help_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing command help: {e}")
            await query.edit_message_text("❌ 顯示指令說明失敗")

    async def _show_clear_reports_menu(self, query):
        """Show clear reports menu"""
        try:
            text = """🚯 <b>清空報表選單</b>

⚠️ <b>注意：此操作不可逆！</b>

請選擇要清空的報表類型：

• 🚯清空個人報表 - 清空您的個人交易記錄
• 🚯清空組別報表 - 清空當前群組記錄（需管理員權限）
• 🚯清空車隊總表 - 清空所有群組記錄（需群主權限）"""
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_clear_reports_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing clear reports menu: {e}")
            await query.edit_message_text("❌ 顯示清空報表選單失敗")

    async def _show_user_settings(self, query):
        """Show user settings menu with permission check"""
        try:
            user = query.from_user
            user_id = user.id
            
            # Check if user has admin or owner permissions
            # For now, implement basic permission system - this can be enhanced later
            text = """👤 <b>使用者設定</b>

管理群組內的使用者權限：

• 👤群主 - 最高權限，可執行所有操作
• 👤管理員 - 可管理組別報表和使用者
• 👤操作員 - 可記帳和查看個人報表"""
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_user_settings_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing user settings: {e}")
            keyboard = [[InlineKeyboardButton("🔙返回設置選單", callback_data="settings_menu")]]
            await query.edit_message_text(
                "❌ 顯示使用者設定失敗",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _handle_clear_report(self, query, data):
        """Handle clear report actions"""
        try:
            user = query.from_user
            chat = query.message.chat
            
            if data == "clear_personal":
                # Set user state for clearing personal reports
                user_id = user.id
                self.user_states[user_id] = {
                    'action': 'clear_personal',
                    'step': 'waiting_date'
                }
                
                text = """🚯 <b>清空個人報表</b>

請直接輸入要清空的月份或日期：

💡 格式範例:
• <code>6</code> - 清空6月報表
• <code>6/12</code> - 清空6/12報表

⚠️ 此操作將刪除該月份或當日的所有記錄，無法復原！"""
                
                keyboard = [[InlineKeyboardButton("🔙返回清空報表", callback_data="clear_reports")]]
                await query.edit_message_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
            elif data == "clear_group":
                # Set user state for clearing group reports
                user_id = user.id
                self.user_states[user_id] = {
                    'action': 'clear_group',
                    'step': 'waiting_date'
                }
                
                text = """🚯 <b>清空組別報表</b>

請直接輸入要清空的月份或日期：

💡 格式範例:
• <code>6</code> - 清空6月報表
• <code>6/12</code> - 清空6/12報表

⚠️ 此操作將刪除該月份或當日的所有群組記錄，無法復原！"""
                
                keyboard = [[InlineKeyboardButton("🔙返回清空報表", callback_data="clear_reports")]]
                await query.edit_message_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
            elif data == "clear_fleet":
                # Set user state for clearing fleet reports
                user_id = user.id
                self.user_states[user_id] = {
                    'action': 'clear_fleet',
                    'step': 'waiting_date'
                }
                
                text = """🚯 <b>清空車隊總表</b>

請直接輸入要清空的月份或日期：

💡 格式範例:
• <code>6</code> - 清空6月報表
• <code>6/12</code> - 清空6/12報表

⚠️ 此操作將刪除該月份或當日的所有車隊記錄，無法復原！"""
                
                keyboard = [[InlineKeyboardButton("🔙返回清空報表", callback_data="clear_reports")]]
                await query.edit_message_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error handling clear report: {e}")
            keyboard = [[InlineKeyboardButton("🔙返回清空報表", callback_data="clear_reports")]]
            await query.edit_message_text(
                "❌ 清空報表操作失敗",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _show_help_content(self, query, data):
        """Show help content for different user roles"""
        try:
            help_texts = {
                "help_owner": """1️⃣ <b>群主指令</b>

🔸 <b>完整權限</b>
• 所有管理員和操作員功能
• 🚯清空車隊總表 - 清空所有群組數據
• 👤使用者設定 - 管理所有用戶權限

🔸 <b>系統管理</b>
• 設定匯率、歡迎詞等系統參數
• 管理群組設定和權限分配""",
                
                "help_admin": """2️⃣ <b>管理員指令</b>

🔸 <b>報表管理</b>
• 📊組別報表 - 查看和管理群組報表
• 🚯清空組別報表 - 清空當前群組數據

🔸 <b>用戶管理</b>
• 👤使用者設定 - 管理操作員權限
• 💱匯率設定 - 設定交易匯率""",
                
                "help_operator": """3️⃣ <b>操作員指令</b>

🔸 <b>報表指令</b>
• 📊個人報表 - 顯示個人當月收支報表
• 🚯清空個人報表 - 清空所有個人報表數據

🔸 <b>記帳指令</b>
• 💰金額異動 - 按鍵內的功能都可以使用

🔸 <b>列表指令</b>
• 列表 - 回覆訊息文本並輸入列表可格式化當前的文本內容""",
                

            }
            
            text = help_texts.get(data, "❌ 未知的幫助類型")
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_command_help_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error showing help content: {e}")
            await query.edit_message_text("❌ 顯示幫助內容失敗")

    async def _show_role_management(self, query, data):
        """Show role management for specific role"""
        try:
            role_map = {
                "role_owner": "群主",
                "role_admin": "管理員", 
                "role_operator": "操作員"
            }
            
            role_type = role_map.get(data, "未知")
            
            text = f"""👤 <b>{role_type}管理</b>

請選擇操作：

• 顯示目前{role_type} - 查看當前{role_type}列表
• 添加{role_type} - 新增{role_type}權限
• 取消{role_type} - 移除{role_type}權限"""
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=self.keyboards.get_role_management_keyboard(role_type)
            )
            
        except Exception as e:
            logger.error(f"Error showing role management: {e}")
            await query.edit_message_text("❌ 顯示角色管理失敗")

    async def _show_tw_help(self, query):
        """Show Taiwan dollar transaction help"""
        try:
            text = """💰 <b>台幣記帳</b>

請輸入交易格式：

<b>台幣收入</b>
<code>Tw+NN</code> <code>+NN</code>

<b>台幣支出</b>
<code>Tw-NN</code> <code>-NN</code>

<b>指定日期</b>
<code>MM/DD +NN</code> <code>MM/DD -NN</code>"""

            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error showing TW help: {e}")
            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            await query.edit_message_text(
                "❌ 顯示台幣說明失敗",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _show_cn_help(self, query):
        """Show Chinese yuan transaction help"""
        try:
            text = """💰 <b>人民幣記帳</b>

請輸入交易格式：

<b>人民幣收入</b>
<code>Cn+NN</code> <code>+NN</code>

<b>人民幣支出</b>
<code>Cn-NN</code> <code>-NN</code>

<b>指定日期</b>
<code>MM/DD +NN</code> <code>MM/DD -NN</code>"""

            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error showing CN help: {e}")
            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            await query.edit_message_text(
                "❌ 顯示人民幣說明失敗",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _show_public_fund_help(self, query):
        """Show public fund management help"""
        try:
            text = """💵 <b>公桶資金管理</b>

<b>餘額:</b> <code>看當前的公桶餘額為多少</code>

<b>操作格式：</b>
<code>公桶+NN</code> <code>公桶-NN</code>"""

            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error showing public fund help: {e}")
            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            await query.edit_message_text(
                "❌ 顯示公桶說明失敗",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _show_private_fund_help(self, query):
        """Show private fund management help"""
        try:
            text = """💵 <b>私人資金管理</b>

<b>餘額:</b> <code>看當前的私人餘額為多少</code>

<b>操作格式：</b>
<code>私人+NN</code> <code>私人-NN</code>"""

            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error showing private fund help: {e}")
            keyboard = [[InlineKeyboardButton("🔙返回金額異動", callback_data="money_actions")]]
            await query.edit_message_text(
                "❌ 顯示私人說明失敗",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _handle_list_formatting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle list formatting command"""
        try:
            # Check if this is a reply to another message
            if not update.message.reply_to_message:
                await update.message.reply_text(
                    "❌ 請回覆包含客戶資訊的訊息並輸入「列表」\n\n"
                    "📝 支援的格式:\n"
                    "• 客戶/姓名: 張三\n"
                    "• 金額: 1000萬 或 500克\n" 
                    "• 時間: 9/1 或 14:30\n"
                    "• 地址: 台北市信義區\n"
                    "• 公司: ABC公司"
                )
                return
            
            # Extract text content from the replied message
            replied_message = update.message.reply_to_message
            original_text = None
            
            # Check if the message has text content
            if replied_message.text:
                original_text = replied_message.text
            # Check if the message has a caption (for photos/documents with text)
            elif replied_message.caption:
                original_text = replied_message.caption
            # If no text content is found
            else:
                await update.message.reply_text(
                    "❌ 請回覆包含文字內容的訊息並輸入「列表」\n\n"
                    "支援處理:\n"
                    "• 純文字訊息\n"
                    "• 附有文字說明的圖片\n"
                    "• 附有文字說明的文件"
                )
                return
            
            # Validate format
            if not self.list_formatter.validate_format(original_text):
                await update.message.reply_text(
                    "❌ 無法識別列表格式，請確保訊息包含必要資訊\n\n"
                    "需要包含: 客戶姓名、金額、時間、地址、公司等資訊"
                )
                return
            
            # Format the list
            result = self.list_formatter.format_list(original_text)
            if not result:
                await update.message.reply_text("❌ 處理列表時發生錯誤")
                return
            
            # Send formatted result
            await update.message.reply_text(result['formatted_text'])
            
            logger.info(f"用戶 {update.effective_user.username or update.effective_user.id} 格式化了一條列表")
            
        except Exception as e:
            logger.error(f"處理列表格式化時出錯: {str(e)}")
            await update.message.reply_text("❌ 處理訊息時發生錯誤")

    async def _handle_delete_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle delete commands"""
        try:
            user = update.effective_user
            text = text.strip()
            
            # Parse delete command patterns
            import re
            from datetime import datetime, date
            
            # Pattern for deleting specific date and amount: 刪除"MM/DD"TW100
            date_amount_pattern = r'刪除["\'""]?(\d{1,2}/\d{1,2})["\'""]?(TW|CN)(\d+(?:\.\d+)?)'
            match = re.search(date_amount_pattern, text)
            
            if match:
                date_str, currency, amount_str = match.groups()
                try:
                    # Parse date
                    month, day = map(int, date_str.split('/'))
                    current_year = datetime.now().year
                    target_date = date(current_year, month, day)
                    
                    # Parse amount
                    amount = float(amount_str)
                    
                    # Delete specific transaction
                    success = await self.db.delete_transaction(
                        user_id=user.id,
                        transaction_date=target_date,
                        currency=currency,
                        amount=amount
                    )
                    
                    if success:
                        currency_name = "台幣" if currency == "TW" else "人民幣"
                        msg = f"""✅ <b>刪除記錄成功</b>

📅 日期: {target_date.strftime('%m/%d')}
💰 幣別: {currency_name}
💵 金額: {amount:,.0f}
👤 操作人: {user.first_name}
"""
                        await update.message.reply_text(msg, parse_mode='HTML')
                    else:
                        await update.message.reply_text("❌ 找不到符合條件的記錄")
                    return
                    
                except ValueError:
                    await update.message.reply_text("❌ 日期或金額格式錯誤")
                    return
            
            # Pattern for deleting monthly reports: 刪除"MM月"TW報表
            monthly_pattern = r'刪除["\'""]?(\d{1,2})月["\'""]?(TW|CN)報表'
            match = re.search(monthly_pattern, text)
            
            if match:
                month_str, currency = match.groups()
                try:
                    month = int(month_str)
                    current_year = datetime.now().year
                    
                    # Delete monthly transactions
                    success = await self.db.delete_monthly_transactions(
                        user_id=user.id,
                        month=month,
                        year=current_year,
                        currency=currency
                    )
                    
                    if success:
                        currency_name = "台幣" if currency == "TW" else "人民幣"
                        msg = f"""✅ <b>刪除月份記錄成功</b>

📅 月份: {current_year}年{month}月
💰 幣別: {currency_name}
👤 操作人: {user.first_name}

⚠️ 該月份的所有{currency_name}記錄已被刪除
"""
                        await update.message.reply_text(msg, parse_mode='HTML')
                    else:
                        await update.message.reply_text("❌ 該月份沒有找到記錄")
                    return
                    
                except ValueError:
                    await update.message.reply_text("❌ 月份格式錯誤")
                    return
            
            # If no pattern matches, show help
            help_text = """❓ <b>刪除記錄指令格式</b>

🔸 <b>刪除特定記錄</b>
<code>刪除"日期"TW金額</code> - 刪除指定日期台幣記錄
<code>刪除"日期"CN金額</code> - 刪除指定日期人民幣記錄

🔸 <b>刪除月份記錄</b>
<code>刪除"月份"TW報表</code> - 刪除整個月份的台幣記錄
<code>刪除"月份"CN報表</code> - 刪除整個月份的人民幣記錄

💡 <b>範例:</b>
• <code>刪除"6/1"TW500</code> - 刪除6月1日台幣500元記錄
• <code>刪除"6月"CN報表</code> - 刪除6月所有人民幣記錄
"""
            await update.message.reply_text(help_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error handling delete commands: {e}")
            await update.message.reply_text("❌ 刪除指令處理錯誤")

    async def _handle_user_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle user settings - placeholder"""
        await update.message.reply_text("🚧 用戶設定功能開發中...")

    async def _handle_welcome_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle welcome setting - placeholder"""
        await update.message.reply_text("🚧 歡迎設定功能開發中...")

    async def _handle_fleet_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle fleet report generation"""
        try:
            from datetime import datetime
            import calendar
            
            now = datetime.now()
            year = now.year
            month = now.month
            month_name = f"{year}年{month}月"
            
            chat = update.effective_chat
            user = update.effective_user
            
            # Get current month's transactions from ALL groups for fleet report
            transactions = await self.db.get_all_groups_transactions(month, year)
            
            # Get exchange rates for calculations from database
            import timezone_utils
            today = timezone_utils.get_taiwan_today()
            today_rate = await self.db.get_exchange_rate(today)
            if not today_rate:
                today_rate = 30.2  # Default rate
            
            cn_rate = 7.2  # Default CNY rate
            
            # Calculate totals
            tw_total = sum(t['amount'] for t in transactions if t['currency'] == 'TW' and t['transaction_type'] == 'income')
            cn_total = sum(t['amount'] for t in transactions if t['currency'] == 'CN' and t['transaction_type'] == 'income')
            
            # Convert to USDT
            tw_usdt = (tw_total / today_rate)  if tw_total > 0 else 0
            cn_usdt = (cn_total / cn_rate)  if cn_total > 0 else 0
            
            # Generate daily breakdown
            daily_data = {}
            for transaction in transactions:
                date_key = transaction['transaction_date'].strftime('%m/%d')
                day_name = ['一', '二', '三', '四', '五', '六', '日'][transaction['transaction_date'].weekday()]
                date_display = f"{date_key}({day_name})"
                
                if date_display not in daily_data:
                    daily_data[date_display] = {'TW': 0, 'CN': 0}
                
                if transaction['transaction_type'] == 'income':
                    daily_data[date_display][transaction['currency']] += transaction['amount']
            
            # Format fleet report
            report = f"""【👀 North™Sea 北金國際 - {month_name}車隊報表】
◉ 台幣總業績
<code>NT${tw_total:,.0f}</code>  →  <code>USDT${tw_usdt:,.2f}</code>
◉ 人民幣總業績
<code>CN¥{cn_total:,.0f}</code>  →  <code>USDT${cn_usdt:,.2f}</code>
－－－－－－－－－－"""

            for date_display, amounts in daily_data.items():
                daily_tw_usdt = (amounts['TW'] / today_rate)  if amounts['TW'] > 0 else 0
                daily_cn_usdt = (amounts['CN'] / cn_rate)  if amounts['CN'] > 0 else 0
                daily_total_usdt = daily_tw_usdt + daily_cn_usdt
                
                report += f"""
{date_display} <code>台幣{today_rate:.2f} 人民幣{cn_rate:.1f}</code>【<code>{daily_total_usdt:,.2f}</code>】
{chat.title or '群組'} <code>NT${amounts['TW']:,.0f}  CN¥{amounts['CN']:,.0f}</code>
--- <code>NT${amounts['TW']:,.0f}</code> → [<code>{daily_tw_usdt:,.2f}</code>]
--- <code>CN¥{amounts['CN']:,.0f}</code> → [<code>{daily_cn_usdt:,.2f}</code>]"""

            await update.message.reply_text(report, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error generating fleet report: {e}")
            await update.message.reply_text("❌ 車隊報表生成失敗")

    async def _handle_initialize_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle initialize report - placeholder"""
        await update.message.reply_text("🚧 初始化報表功能開發中...")

    def _parse_financial_record(self, text: str) -> Optional[Dict]:
        """解析金融記錄訊息格式"""
        try:
            import re
            from datetime import datetime

            # 首先檢查是否包含必要的項目和金額欄位
            if not ('項目' in text and '金額' in text):
                return None

            # 解析出款人格式：【出款人-姓名】或【出款人】（可選）
            payer_pattern = r'【([^-]+)(?:-([^】]+))?】'
            payer_match = re.search(payer_pattern, text)

            if payer_match:
                # 有出款人標記的格式
                payer_code = payer_match.group(1).strip()
                payer_name = payer_match.group(2).strip() if payer_match.group(2) else payer_code
            else:
                # 檢查是否為新格式（文字開頭為出款人代碼）
                lines = text.strip().split('\n')
                first_line = lines[0].strip()
                
                # 如果第一行只是簡短代碼且下一行是項目，則認為是新格式
                if len(first_line) <= 10 and len(lines) > 1 and '項目' in lines[1]:
                    payer_code = first_line
                    payer_name = first_line
                else:
                    # 如果沒有明確的出款人，使用用戶名作為預設
                    payer_code = "未指定"
                    payer_name = "未指定"

            # 解析項目
            item_pattern = r'項目[：:]\s*([^\n]+)'
            item_match = re.search(item_pattern, text)
            item = item_match.group(1).strip() if item_match else "未指定"

            # 解析銀行
            bank_pattern = r'銀行[：:]\s*([^\n]+)'
            bank_match = re.search(bank_pattern, text)
            bank = bank_match.group(1).strip() if bank_match else "未指定"

            # 解析金額
            amount_pattern = r'金額[：:]\s*(\d+)'
            amount_match = re.search(amount_pattern, text)

            if not amount_match:
                return None

            amount = int(amount_match.group(1))

            # 解析代碼（可選）
            code_pattern = r'代碼[：:]\s*(\d+)'
            code_match = re.search(code_pattern, text)
            code = code_match.group(1) if code_match else None

            # 解析帳號（可選）
            account_pattern = r'帳號[：:]\s*(\d+)'
            account_match = re.search(account_pattern, text)
            account = account_match.group(1) if account_match else None

            return {
                'payer_code': payer_code,
                'payer_name': payer_name,
                'item': item,
                'bank': bank,
                'amount': amount,
                'code': code,
                'account': account
            }

        except Exception as e:
            logger.error(f"Error parsing financial record: {e}")
            return None

    async def _handle_financial_record(self, update: Update, context: ContextTypes.DEFAULT_TYPE, record: Dict):
        """處理金融記錄訊息"""
        try:
            user = update.effective_user
            chat = update.effective_chat

            # 添加用戶到資料庫
            await self.db.add_user(
                user_id=user.id,
                username=user.username,
                display_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name
            )

            # 自動檢測並保存群組名稱
            if chat.type in ['group', 'supergroup'] and chat.title:
                await self.db.add_or_update_group(chat.id, chat.title)

            # 如果沒有指定出款人，使用發言人的名稱
            payer_name = record['payer_name']
            if payer_name == "未指定":
                # 使用 @ 標記格式顯示發言人
                if user.username:
                    payer_name = f"@{user.username}"
                else:
                    payer_name = user.first_name or user.full_name or f"User{user.id}"

            # 記錄交易（預設為台幣收入）
            today = datetime.now().date()
            success = await self.db.add_transaction(
                user_id=user.id,
                group_id=chat.id if chat.type in ['group', 'supergroup'] else 0,
                transaction_date=today,
                currency='TW',
                amount=record['amount'],
                transaction_type='income',
                created_by=user.id,
                description=f"出款人: {payer_name} | 項目: {record['item']} | 銀行: {record['bank']}"
            )

            if success:
                # 格式化回報訊息
                today_str = today.strftime('%Y/%m/%d')
                weekdays = ['一', '二', '三', '四', '五', '六', '日']
                weekday = weekdays[today.weekday()]

                # 獲取今日和本月總計
                daily_total = await self._get_daily_total(user.id, chat.id, today)
                monthly_total = await self._get_monthly_total(user.id, chat.id, today.year, today.month)

                response_msg = f"""已經收到您的記帳紀錄！

{today_str} ({weekday})
出款人：{payer_name} 金額：{record['amount']:,}

📊 今日總計：{daily_total:,}
📊 本月總計：{monthly_total:,}"""

                await update.message.reply_text(response_msg)
            else:
                await update.message.reply_text("❌ 記帳失敗，請稍後再試")

        except Exception as e:
            logger.error(f"Error handling financial record: {e}")
            await update.message.reply_text("❌ 處理記帳記錄時發生錯誤")

    async def _get_daily_total(self, user_id: int, group_id: int, target_date: date) -> int:
        """獲取指定日期的總計"""
        try:
            async with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # 修改查詢以包含所有交易類型的收入
                cursor.execute("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE group_id = ? AND date = ? AND transaction_type = 'income'
                """, (group_id, target_date))
                result = cursor.fetchone()
                total = result['total'] if result and result['total'] else 0
                logger.info(f"Daily total for group {group_id} on {target_date}: {total}")
                return int(total)
        except Exception as e:
            logger.error(f"Error getting daily total: {e}")
            return 0

    async def _get_monthly_total(self, user_id: int, group_id: int, year: int, month: int) -> int:
        """獲取指定月份的總計"""
        try:
            async with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # 修改查詢以包含所有交易類型的收入
                cursor.execute("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE group_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ? AND transaction_type = 'income'
                """, (group_id, str(year), f"{month:02d}"))
                result = cursor.fetchone()
                total = result['total'] if result and result['total'] else 0
                logger.info(f"Monthly total for group {group_id} in {year}-{month:02d}: {total}")
                return int(total)
        except Exception as e:
            logger.error(f"Error getting monthly total: {e}")
            return 0

    async def _show_daily_payout_report(self, query):
        """Show daily payout report"""
        try:
            from datetime import datetime
            import timezone_utils
            
            chat = query.message.chat
            today = timezone_utils.get_taiwan_today()
            
            # 獲取今日所有出款記錄
            transactions = await self.db.get_group_transactions_by_date(chat.id, today)
            
            # 計算總出款
            total_payout = sum(t['amount'] for t in transactions if t['transaction_type'] == 'income')
            
            # 生成當日報表
            report = f"""<b>◉ 本日總出款</b>
<code>NT${total_payout:,}</code>
－－－－－－－－－－
{today.strftime('%Y年%m月%d日')}收支明細"""

            # 按用戶分組顯示
            user_totals = {}
            for t in transactions:
                if t['transaction_type'] == 'income':
                    username = t.get('username') or t.get('display_name') or f"User{t.get('user_id', 'Unknown')}"
                    user_key = f"@{username}"
                    user_totals[user_key] = user_totals.get(user_key, 0) + t['amount']

            for user, amount in user_totals.items():
                report += f"\n{user} <code>NT${amount:,}</code>"

            keyboard = self.keyboards.get_payout_report_keyboard()
            await query.edit_message_text(
                report,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing daily payout report: {e}")
            keyboard = BotKeyboards.get_main_inline_keyboard()
            await query.edit_message_text(
                text="❌ 當日出款報表生成失敗",
                reply_markup=keyboard
            )

    async def _show_monthly_payout_report(self, query):
        """Show monthly payout report"""
        try:
            from datetime import datetime
            import timezone_utils
            
            chat = query.message.chat
            now = timezone_utils.get_taiwan_now()
            
            # 獲取本月所有出款記錄
            transactions = await self.db.get_group_transactions(chat.id)
            
            # 計算總出款和USDT價值
            tw_total = sum(t['amount'] for t in transactions if t['currency'] == 'TW' and t['transaction_type'] == 'income')
            cn_total = sum(t['amount'] for t in transactions if t['currency'] == 'CN' and t['transaction_type'] == 'income')
            
            # 取得匯率
            today = timezone_utils.get_taiwan_today()
            tw_rate = await self.db.get_exchange_rate(today) or 33.25
            cn_rate = 7.2  # 預設人民幣匯率
            
            # 轉換為USDT
            tw_usdt = tw_total / tw_rate if tw_total > 0 else 0
            cn_usdt = cn_total / cn_rate if cn_total > 0 else 0
            total_usdt = tw_usdt + cn_usdt
            
            # 生成月度報表
            report = f"""<b>◉ 本月總出款</b>
<code>NT${tw_total + (cn_total * cn_rate / tw_rate):,.0f}</code> → <code>USDT${total_usdt:,.2f}</code>
－－－－－－－－－－
{now.strftime('%Y年%m月')}收支明細"""

            # 按日期分組顯示
            daily_data = {}
            for t in transactions:
                if t['transaction_type'] == 'income':
                    date_key = t['transaction_date'].strftime('%m/%d')
                    weekday_names = ['一', '二', '三', '四', '五', '六', '日']
                    weekday = weekday_names[t['transaction_date'].weekday()]
                    date_display = f"{date_key}({weekday})"
                    
                    if date_display not in daily_data:
                        daily_data[date_display] = {'TW': 0, 'CN': 0}
                    
                    daily_data[date_display][t['currency']] += t['amount']

            # 按日期排序並顯示
            sorted_dates = sorted(daily_data.keys(), key=lambda x: tuple(map(int, x.split('(')[0].split('/'))))
            
            tw_dates = []
            cn_dates = []
            
            for date_display in sorted_dates:
                amounts = daily_data[date_display]
                if amounts['TW'] > 0:
                    tw_dates.append(f"<code>{date_display} NT${amounts['TW']:,}</code>")
                if amounts['CN'] > 0:
                    cn_dates.append(f"<code>{date_display} CN¥{amounts['CN']:,}</code>")

            # 添加台幣記錄
            if tw_dates:
                for i, date_line in enumerate(tw_dates):
                    report += f"\n{date_line}"
                    if i < len(tw_dates) - 1 and (i + 1) % 2 == 0:
                        report += "\n－－－－－－－－－－"

            # 添加人民幣記錄
            if cn_dates:
                if tw_dates:
                    report += "\n－－－－－－－－－－"
                for i, date_line in enumerate(cn_dates):
                    report += f"\n{date_line}"
                    if i < len(cn_dates) - 1 and (i + 1) % 2 == 0:
                        report += "\n－－－－－－－－－－"

            keyboard = self.keyboards.get_payout_report_keyboard()
            await query.edit_message_text(
                report,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing monthly payout report: {e}")
            keyboard = BotKeyboards.get_main_inline_keyboard()
            await query.edit_message_text(
                text="❌ 當月出款報表生成失敗",
                reply_markup=keyboard
            )
    
    async def _handle_clear_report_date_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, date_input: str):
        """Handle date input for clearing reports"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Check if context exists in application user data
            if (user_id not in context.application.user_data or 
                'clear_report_context' not in context.application.user_data[user_id]):
                await update.message.reply_text("❌ 請先選擇清空報表類型")
                return
            
            clear_type = context.application.user_data[user_id]['clear_report_context']
            
            # Format confirmation message based on input type
            if '/' in date_input:
                # MM/DD format
                date_display = date_input
                time_desc = f"{date_input}的記錄"
            else:
                # MM format
                date_display = f"{date_input}月"
                time_desc = f"{date_input}月的所有記錄"
            
            # Determine report type
            if clear_type == "clear_personal":
                report_type = "個人報表"
            elif clear_type == "clear_group":
                report_type = "組別報表"
            elif clear_type == "clear_fleet":
                report_type = "車隊總表"
            else:
                report_type = "報表"
            
            # Create confirmation keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ 確認刪除", callback_data=f"confirm_clear_{clear_type}_{date_input}"),
                    InlineKeyboardButton("❌ 取消", callback_data="clear_reports")
                ]
            ]
            
            confirmation_text = f"""⚠️ <b>確認刪除操作</b>

📊 報表類型: {report_type}
📅 時間範圍: {time_desc}
👤 操作人員: {user.first_name}

<b>⚠️ 警告:</b>
此操作將永久刪除所選時間範圍內的所有記錄，無法復原！

請確認是否要繼續?"""

            await update.message.reply_text(
                confirmation_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Clear the context
            del context.user_data['clear_report_context']
            
        except Exception as e:
            logger.error(f"Error handling clear report date input: {e}")
            await update.message.reply_text("❌ 處理日期輸入失敗")
    
    async def _show_exchange_rate_menu(self, query):
        """Show exchange rate settings menu"""
        keyboard = BotKeyboards.get_exchange_rate_keyboard()
        await query.edit_message_text(
            text="💱 <b>匯率設定選單</b>\n\n"
                 "請選擇要執行的匯率操作：",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    async def _show_current_exchange_rates(self, query):
        """Show current exchange rate information"""
        try:
            # Get current exchange rates from database
            today = timezone_utils.get_taiwan_today()
            
            tw_rate = await self.db.get_exchange_rate(today)
            
            if tw_rate:
                tw_rate_text = f"台幣匯率: {tw_rate:.2f}"
            else:
                tw_rate_text = "台幣匯率: 未設定"
            
            # For CN rate, use a default value since we don't store it separately yet
            cn_rate_text = "人民幣匯率: 7.20 (預設值)"
            
            rate_info = f"""💱 <b>當前匯率資訊</b>

📅 查詢日期: {today.strftime('%Y/%m/%d')}

💰 {tw_rate_text}
💴 {cn_rate_text}

💡 <b>設置匯率指令:</b>
• 設定匯率30.5 (設定台幣匯率)
• 設定06/01匯率30.2 (設定指定日期台幣匯率)
• 設定CN匯率7.2 (設定人民幣匯率)
• 設定06/01CN匯率7.1 (設定指定日期人民幣匯率)

⚠️ 匯率設定需要管理員權限"""

            keyboard = BotKeyboards.get_exchange_rate_keyboard()
            await query.edit_message_text(
                text=rate_info,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing current exchange rates: {e}")
            await query.edit_message_text(
                text="❌ 獲取匯率資訊失敗",
                reply_markup=BotKeyboards.get_exchange_rate_keyboard()
            )
    
    async def _prompt_tw_rate_setting(self, query):
        """Prompt user to set Taiwan dollar exchange rate"""
        prompt_text = """💰 <b>設定台幣匯率</b>

請直接輸入以下格式的指令：

🔹 <b>設定今日匯率:</b>
   <code>設定匯率30.5</code>

🔹 <b>設定指定日期匯率:</b>
   <code>設定06/01匯率30.2</code>
   <code>設定2024-06-01匯率30.2</code>

⚠️ 需要管理員權限才能設定匯率"""

        keyboard = BotKeyboards.get_exchange_rate_keyboard()
        await query.edit_message_text(
            text=prompt_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    async def _prompt_cn_rate_setting(self, query):
        """Prompt user to set Chinese yuan exchange rate"""
        prompt_text = """💴 <b>設定人民幣匯率</b>

請直接輸入以下格式的指令：

🔹 <b>設定今日匯率:</b>
   <code>設定CN匯率7.2</code>

🔹 <b>設定指定日期匯率:</b>
   <code>設定06/01CN匯率7.1</code>
   <code>設定2024-06-01CN匯率7.1</code>

⚠️ 需要管理員權限才能設定匯率"""

        keyboard = BotKeyboards.get_exchange_rate_keyboard()
        await query.edit_message_text(
            text=prompt_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    async def _prompt_date_rate_setting(self, query):
        """Prompt user to set exchange rate for specific date"""
        prompt_text = """📅 <b>設定指定日期匯率</b>

支援以下日期格式的匯率設定：

🔹 <b>台幣匯率:</b>
   <code>設定06/01匯率30.2</code>
   <code>設定2024-06-01匯率30.2</code>

🔹 <b>人民幣匯率:</b>
   <code>設定06/01CN匯率7.1</code>
   <code>設定2024-06-01CN匯率7.1</code>

📝 <b>日期格式說明:</b>
• MM/DD - 當年月日
• YYYY-MM-DD - 完整日期
• MM月DD日 - 中文格式

⚠️ 需要管理員權限才能設定匯率"""

        keyboard = BotKeyboards.get_exchange_rate_keyboard()
        await query.edit_message_text(
            text=prompt_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    # Handler getter methods for main application
    def get_start_handler(self):
        """Get start command handler"""
        from telegram.ext import CommandHandler
        return CommandHandler("start", self.start_command)
    
    def get_help_handler(self):
        """Get help command handler"""
        from telegram.ext import CommandHandler
        return CommandHandler("help", self.help_command)
    
    def get_restart_handler(self):
        """Get restart command handler"""
        from telegram.ext import CommandHandler
        return CommandHandler("restart", self.restart_command)
    
    def get_message_handler(self):
        """Get message handler"""
        from telegram.ext import MessageHandler, filters
        return MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_transaction_message)
    
    def get_callback_handler(self):
        """Get callback query handler"""
        from telegram.ext import CallbackQueryHandler
        return CallbackQueryHandler(self.callback_query_handler)
    
    def get_error_handler(self):
        """Get error handler"""
        async def error_handler(update, context):
            """Handle errors"""
            logger.error(f"Update {update} caused error {context.error}")
        return error_handler