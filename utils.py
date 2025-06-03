"""
Utility functions for the North Sea Financial Bot
Handles formatting, validation, and common operations
"""

import re
import logging
from datetime import datetime, date
from typing import Optional, Tuple, Dict, List
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class TransactionParser:
    """Parse transaction commands and extract relevant information"""
    
    # Currency patterns
    CURRENCY_PATTERNS = {
        'TW': r'(?:TW|台幣|臺幣)',
        'CN': r'(?:CN|人民幣|RMB)'
    }
    
    # Transaction type patterns
    TRANSACTION_PATTERNS = {
        'income': r'[\+＋]',
        'expense': r'[\-－]'
    }
    
    # Date patterns
    DATE_PATTERNS = [
        r'(\d{1,2})/(\d{1,2})',  # MM/DD
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})-(\d{1,2})',  # MM-DD
        r'(\d{1,2})月(\d{1,2})日',  # MM月DD日
    ]
    
    @classmethod
    def parse_transaction(cls, text: str, user_id: int = None) -> Optional[Dict]:
        """Parse transaction command and return transaction details"""
        try:
            text = text.strip()
            
            # Check for user mention
            mentioned_user = None
            if text.startswith('@'):
                parts = text.split(' ', 1)
                if len(parts) > 1:
                    mentioned_user = parts[0][1:]  # Remove @
                    text = parts[1]
            
            # Parse date
            transaction_date = None
            for pattern in cls.DATE_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    try:
                        if len(match.groups()) == 2:  # MM/DD or MM-DD
                            month, day = match.groups()
                            current_year = datetime.now().year
                            transaction_date = date(current_year, int(month), int(day))
                        elif len(match.groups()) == 3:  # YYYY-MM-DD
                            year, month, day = match.groups()
                            transaction_date = date(int(year), int(month), int(day))
                        
                        # Remove date from text
                        text = re.sub(pattern, '', text).strip()
                        break
                    except ValueError:
                        continue
            
            if not transaction_date:
                transaction_date = date.today()
            
            # Parse currency and amount
            currency = None
            amount = None
            transaction_type = None
            
            for curr_key, curr_pattern in cls.CURRENCY_PATTERNS.items():
                for trans_key, trans_pattern in cls.TRANSACTION_PATTERNS.items():
                    # Pattern: Currency + TransactionType + Amount
                    pattern = f'{curr_pattern}\\s*{trans_pattern}\\s*(\\d+(?:\\.\\d+)?)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    
                    if match:
                        currency = curr_key
                        transaction_type = trans_key
                        amount = float(match.group(1))
                        break
                
                if currency:
                    break
            
            if not currency or amount is None:
                return None
            
            return {
                'user_id': user_id,
                'mentioned_user': mentioned_user,
                'date': transaction_date,
                'currency': currency,
                'amount': amount,
                'transaction_type': transaction_type,
                'original_text': text
            }
            
        except Exception as e:
            logger.error(f"Error parsing transaction: {e}")
            return None
    
    @classmethod
    def parse_fund_command(cls, text: str) -> Optional[Dict]:
        """Parse fund management command"""
        try:
            text = text.strip()
            
            # Fund type patterns
            fund_patterns = {
                'public': r'(?:公桶|公共)',
                'private': r'(?:私人|個人)'
            }
            
            fund_type = None
            amount = None
            operation = None
            
            for fund_key, fund_pattern in fund_patterns.items():
                for op_key, op_pattern in cls.TRANSACTION_PATTERNS.items():
                    pattern = f'{fund_pattern}\\s*{op_pattern}\\s*(\\d+(?:\\.\\d+)?)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    
                    if match:
                        fund_type = fund_key
                        operation = op_key
                        amount = float(match.group(1))
                        break
                
                if fund_type:
                    break
            
            if not fund_type or amount is None:
                return None
            
            return {
                'fund_type': fund_type,
                'operation': operation,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error parsing fund command: {e}")
            return None

class ReportFormatter:
    """Format financial reports for display"""
    
    @staticmethod
    def format_personal_report(transactions: List[Dict], user_name: str, 
                             group_name: str = "個人", month: int = None, year: int = None) -> str:
        """Format personal financial report"""
        try:
            if not transactions:
                return f"📊 <b>{group_name} - 個人報表</b>\n\n❌ 本月暫無交易記錄"
            
            # Calculate totals
            tw_income = sum(t['amount'] for t in transactions 
                           if t['currency'] == 'TW' and t['transaction_type'] == 'income')
            tw_expense = sum(t['amount'] for t in transactions 
                            if t['currency'] == 'TW' and t['transaction_type'] == 'expense')
            cn_income = sum(t['amount'] for t in transactions 
                           if t['currency'] == 'CN' and t['transaction_type'] == 'income')
            cn_expense = sum(t['amount'] for t in transactions 
                            if t['currency'] == 'CN' and t['transaction_type'] == 'expense')
            
            tw_total = tw_income - tw_expense
            cn_total = cn_income - cn_expense
            
            # USDT conversion rates (example rates - should be real rates)
            tw_to_usdt_rate = 0.032  # 1 TWD = 0.032 USDT
            cn_to_usdt_rate = 0.14   # 1 CNY = 0.14 USDT
            
            tw_usdt = tw_total * tw_to_usdt_rate * 0.01
            cn_usdt = cn_total * cn_to_usdt_rate * 0.01
            
            # Format displays
            tw_total_display = f"{tw_total:,.0f}"
            cn_total_display = f"{cn_total:,.0f}"
            tw_usdt_display = f"{tw_usdt:,.2f}"
            cn_usdt_display = f"{cn_usdt:,.2f}"
            
            # Sample fund data (should come from database)
            public_funds_display = "0.00"
            private_funds_display = "0.00"
            
            # Format report
            current_date = datetime.now()
            if month and year:
                report_name = f"📊 <b>{group_name} - {user_name} - {year}年{month}月個人報表</b>"
            else:
                year = current_date.year
                month = current_date.month
                report_name = f"📊 <b>{group_name} - {user_name} - {year}年{month}月個人報表</b>"
            
            report_lines = [
                f"<b>【{report_name}】</b>",
                f"<b>◉ 台幣業績</b>",
                f"<code> NT${tw_total_display} </code> → <code> USDT${tw_usdt_display} </code>",
                f"<b>◉ 人民幣業績</b>",
                f"<code> CN¥{cn_total_display} </code> → <code> USDT${cn_usdt_display} </code>",
                f"<b>◉ 資金狀態</b>",
                f"公桶：<code> USDT${public_funds_display} </code>",
                f"私人：<code> USDT${private_funds_display} </code>",
                "－－－－－－－－－－",
                f"<b>{year}年{month}月收支明細</b>"
            ]
            
            # Group transactions by date and add daily breakdown
            from collections import defaultdict
            import calendar
            
            # Group transactions by date
            daily_transactions = defaultdict(lambda: {'TW': 0, 'CN': 0})
            
            for t in transactions:
                date_obj = datetime.strptime(str(t['date']), '%Y-%m-%d').date() if isinstance(t['date'], str) else t['date']
                currency = t['currency']
                amount = t['amount'] if t['transaction_type'] == 'income' else -t['amount']
                daily_transactions[date_obj][currency] += amount
            
            # Sort dates and add to report
            sorted_dates = sorted(daily_transactions.keys())
            current_group = []
            
            for date_obj in sorted_dates:
                day_data = daily_transactions[date_obj]
                weekday = calendar.day_name[date_obj.weekday()]
                weekday_chinese = {
                    'Monday': '一', 'Tuesday': '二', 'Wednesday': '三',
                    'Thursday': '四', 'Friday': '五', 'Saturday': '六', 'Sunday': '日'
                }[weekday]
                
                date_str = f"{date_obj.month:02d}/{date_obj.day:02d}({weekday_chinese})"
                
                # Add transactions for this date
                if day_data['TW'] != 0:
                    amount_str = f"NT${day_data['TW']:,.0f}"
                    if day_data['TW'] > 0:
                        current_group.append(f"<code>{date_str} {amount_str}</code>")
                    else:
                        current_group.append(f"{date_str} {amount_str}")
                
                if day_data['CN'] != 0:
                    amount_str = f"CN¥{day_data['CN']:,.0f}"
                    if day_data['CN'] > 0:
                        current_group.append(f"<code>{date_str} {amount_str}</code>")
                    else:
                        current_group.append(f"{date_str} {amount_str}")
                
                # Add separator every few entries to match your format
                if len(current_group) >= 3:
                    report_lines.extend(current_group)
                    report_lines.append("－－－－－－－－－－")
                    current_group = []
            
            # Add remaining transactions
            if current_group:
                report_lines.extend(current_group)
                report_lines.append("－－－－－－－－－－")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error formatting personal report: {e}")
            return "❌ 報表格式化失敗"
    
    @staticmethod
    async def format_group_report(transactions: List[Dict], group_name: str = "群組", db_manager=None) -> str:
        """Format group financial report with new layout"""
        try:
            if not transactions:
                return f"📊 <b>{group_name}報表</b>\n\n❌ 本月暫無交易記錄"
            
            # Calculate overall totals
            overall_totals = {'TW': 0, 'CN': 0}
            for t in transactions:
                if t['transaction_type'] == 'income':
                    overall_totals[t['currency']] += t['amount']
            
            # Get exchange rates from database or use defaults
            if db_manager:
                import timezone_utils
                today = timezone_utils.get_taiwan_today()
                tw_rate = await db_manager.get_exchange_rate(today)
                tw_rate = tw_rate if tw_rate else 30.2  # Fallback to default
            else:
                tw_rate = 30.2  # Default TWD to USD rate
            
            cn_rate = 7.2   # CNY to USD rate (can be enhanced later)
            
            tw_usdt = overall_totals['TW'] / tw_rate if overall_totals['TW'] > 0 else 0
            cn_usdt = overall_totals['CN'] / cn_rate if overall_totals['CN'] > 0 else 0
            
            # Format report header
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            report_name = f"{group_name} - {year}年{month}月群組報表"
            
            report_lines = [
                f"<b>【👀 {report_name}】</b>",
                f"<b>◉ 台幣業績</b>",
                f"<code>NT${overall_totals['TW']:,.0f}</code> → <code>USDT${tw_usdt:,.2f}</code>",
                f"<b>◉ 人民幣業績</b>",
                f"<code>CN¥{overall_totals['CN']:,.0f}</code> → <code>USDT${cn_usdt:,.2f}</code>",
                "－－－－－－－－－－"
            ]
            
            # Group transactions by date
            daily_transactions = {}
            for t in transactions:
                date_str = t['date']
                if isinstance(date_str, str):
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue
                else:
                    date_obj = date_str
                
                day_key = date_obj.strftime('%m/%d')
                
                if day_key not in daily_transactions:
                    daily_transactions[day_key] = []
                
                # Get user display name
                user_name = t.get('display_name') or t.get('username') or f"User{t['user_id']}"
                
                transaction_entry = {
                    'amount': t['amount'],
                    'currency': t['currency'],
                    'user': user_name,
                    'type': t['transaction_type']
                }
                
                daily_transactions[day_key].append(transaction_entry)
            
            # Add daily transaction details with new format
            for day_key in sorted(daily_transactions.keys()):
                day_trans = daily_transactions[day_key]
                
                # Calculate daily totals by currency
                tw_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'TW' and t['type'] == 'income')
                cn_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'CN' and t['type'] == 'income')
                
                # Skip days with no income
                if tw_daily == 0 and cn_daily == 0:
                    continue
                
                # Calculate USDT equivalents for the day
                tw_daily_usdt = tw_daily / tw_rate if tw_daily > 0 else 0
                cn_daily_usdt = cn_daily / cn_rate if cn_daily > 0 else 0
                
                # Add daily header
                report_lines.append(f"<b>{day_key} 台幣匯率{tw_rate}    人民幣匯率{cn_rate}</b>")
                report_lines.append(f"<code>NT${tw_daily:,.0f}({tw_daily_usdt:.2f})  CN¥{cn_daily:,.0f}({cn_daily_usdt:.2f})</code>")
                
                # Group transactions by user for this day
                user_transactions = {}
                for t in day_trans:
                    if t['type'] == 'income' and t['amount'] > 0:
                        user = t['user']
                        if user not in user_transactions:
                            user_transactions[user] = {'TW': 0, 'CN': 0}
                        user_transactions[user][t['currency']] += t['amount']
                
                # Add user transaction details
                for user, amounts in user_transactions.items():
                    report_lines.append(f"   • <code>NT${amounts['TW']:,.0f} CN¥{amounts['CN']:,.0f} {user}</code>")
                
                report_lines.append("")  # Empty line between days
                
            
            report_lines.append("－－－－－－－－－－")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error formatting group report: {e}")
            return "❌ 群組報表格式化失敗"
    
    @staticmethod
    def format_transaction_list(transactions: List[Dict], limit: int = 10) -> str:
        """Format recent transactions list"""
        try:
            if not transactions:
                return "📝 暫無交易記錄"
            
            report = "📝 <b>最近交易記錄:</b>\n\n"
            
            for t in transactions[:limit]:
                date_str = t['date']
                currency = t['currency']
                amount = t['amount']
                trans_type = "+" if t['transaction_type'] == 'income' else "-"
                
                report += f"<code>{date_str} {currency}{trans_type}{amount:,.0f}</code>\n"
            
            if len(transactions) > limit:
                report += f"\n... 另有 {len(transactions) - limit} 筆記錄"
            
            return report
            
        except Exception as e:
            logger.error(f"Error formatting transaction list: {e}")
            return "❌ 交易列表格式化失敗"

class ValidationUtils:
    """Validation utilities for user input"""
    
    @staticmethod
    def validate_amount(amount_str: str) -> Optional[float]:
        """Validate and parse amount"""
        try:
            amount = float(amount_str.replace(',', ''))
            if amount <= 0:
                return None
            if amount > 1000000:  # Max amount check
                return None
            return amount
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_date(date_str: str) -> Optional[date]:
        """Validate and parse date string"""
        try:
            # Try different date formats
            formats = ['%m/%d', '%Y-%m-%d', '%m-%d', '%m月%d日']
            
            for fmt in formats:
                try:
                    if fmt in ['%m/%d', '%m-%d']:
                        # Add current year
                        parsed_date = datetime.strptime(date_str, fmt)
                        return date(datetime.now().year, parsed_date.month, parsed_date.day)
                    else:
                        parsed_date = datetime.strptime(date_str, fmt)
                        return parsed_date.date()
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def validate_exchange_rate(rate_str: str) -> Optional[float]:
        """Validate exchange rate"""
        try:
            rate = float(rate_str)
            if 0.1 <= rate <= 100:  # Reasonable range for CNY to TWD
                return rate
            return None
        except (ValueError, TypeError):
            return None
