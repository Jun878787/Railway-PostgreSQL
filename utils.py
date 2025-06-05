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

def fix_html_tags(text: str) -> str:
    """Fix corrupted HTML tags that may have been converted to uppercase or missing closing tags"""
    if not text:
        return text
    
    # First, fix uppercase corrupted tags
    tag_fixes = [
        (r'<CODE>', '<code>'),
        (r'</CODE>', '</code>'),
        (r'<Code>', '<code>'),
        (r'</Code>', '</code>'),
        (r'<B>', '<b>'),
        (r'</B>', '</b>'),
        (r'<STRONG>', '<strong>'),
        (r'</STRONG>', '</strong>'),
        (r'<I>', '<i>'),
        (r'</I>', '</i>'),
        (r'<U>', '<u>'),
        (r'</U>', '</u>'),
        (r'<EM>', '<em>'),
        (r'</EM>', '</em>'),
    ]
    
    for pattern, replacement in tag_fixes:
        text = re.sub(pattern, replacement, text)
    
    # Fix missing closing tags (e.g., <code> without </code>)
    missing_closing_fixes = [
        # Fix <b>text<b> -> <b>text</b>
        (r'<b>([^<]*)<b>', r'<b>\1</b>'),
        # Fix <code>text<code> -> <code>text</code>
        (r'<code>([^<]*)<code>', r'<code>\1</code>'),
        # Fix <strong>text<strong> -> <strong>text</strong>
        (r'<strong>([^<]*)<strong>', r'<strong>\1</strong>'),
        # Fix <i>text<i> -> <i>text</i>
        (r'<i>([^<]*)<i>', r'<i>\1</i>'),
    ]
    
    for pattern, replacement in missing_closing_fixes:
        text = re.sub(pattern, replacement, text)
    
    return text

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
            
            # First try with explicit + or - signs
            for curr_key, curr_pattern in cls.CURRENCY_PATTERNS.items():
                for trans_key, trans_pattern in cls.TRANSACTION_PATTERNS.items():
                    # Pattern: Currency + TransactionType + Amount
                    # Allow negative sign directly before amount for expense
                    pattern = f'{curr_pattern}\s*(?:{trans_pattern}\s*)?(-?\d+(?:\.\d+)?)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    
                    if match:
                        amount_str = match.group(1)
                        try:
                            amount_val = float(amount_str)
                        except ValueError:
                            continue # Invalid amount

                        currency = curr_key
                        # Determine transaction type based on sign of amount if not explicitly given by +/- symbols
                        if trans_pattern in text or amount_val < 0:
                            transaction_type = 'expense' if amount_val < 0 else trans_key
                            if transaction_type == 'expense' and amount_val > 0:
                                amount_val = -amount_val # Ensure amount is negative for expense if not already
                        else:
                            transaction_type = 'income'
                        
                        amount = abs(amount_val) # Store absolute amount, type indicates sign
                        if transaction_type == 'expense' and match.group(0).count('-') + match.group(0).count('－') == 0 and not amount_str.startswith('-'):
                            # If it's an expense but no explicit minus sign was found with the currency token, and amount is positive, it's likely a parsing error or ambiguous input.
                            # For example "CN500" could be income, but if context implies expense, this logic needs refinement.
                            # For now, if no explicit sign, and it's not negative, assume income unless context changes this.
                            # This part might need more sophisticated logic if "CN500" can mean expense in some contexts.
                            pass # Keep as is, or add specific logic if needed

                        break
                
                if currency:
                    break
            
            # If no explicit sign found, try default format: Currency + Amount (assume expense for CN, income for TW)
            if not currency:
                for curr_key, curr_pattern in cls.CURRENCY_PATTERNS.items():
                    # Pattern: Currency + Amount (without explicit + or -)
                    pattern = f'{curr_pattern}\s*([\d]+(?:\.\d+)?)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    
                    if match:
                        amount_str = match.group(1)
                        try:
                            amount_val = float(amount_str)
                        except ValueError:
                            continue

                        currency = curr_key
                        if curr_key == 'CN':
                            transaction_type = 'expense'
                            amount = amount_val
                        else:
                            transaction_type = 'income'
                            amount = amount_val
                        break
            
            if not currency or amount is None:
                 # Try parsing format like -500 or -CN500
                # Regex for optional currency, mandatory minus, then amount
                # Adjusted to be more specific for negative amounts without explicit currency type before them
                pattern_neg_amount = r'(-)(?:(TW|台幣|臺幣|CN|人民幣|RMB)\s*)?(\d+(?:\.\d+)?)'
                match_neg_amount = re.search(pattern_neg_amount, text, re.IGNORECASE)
                if match_neg_amount:
                    sign = match_neg_amount.group(1)
                    curr_text = match_neg_amount.group(2)
                    amount_val_str = match_neg_amount.group(3)
                    try:
                        amount_val = float(amount_val_str)
                        if sign == '-':
                            transaction_type = 'expense'
                            amount = -amount_val # 寫入負數，確保資料庫正確
                            if curr_text:
                                if curr_text.upper() in ['TW', '台幣', '臺幣']:
                                    currency = 'TW'
                                elif curr_text.upper() in ['CN', '人民幣', 'RMB']:
                                    currency = 'CN'
                            else:
                                # Default currency if not specified, e.g., TWD
                                # 依預設行為，沒指定幣別時為 TW
                                currency = 'TW'
                        # else: # This case should not happen with the current regex for negative amounts
                            # transaction_type = 'income'
                            # amount = amount_val

                    except ValueError:
                        pass # Amount not a valid float

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
                    # Allow negative sign directly before amount for expense
                    pattern = f'{fund_pattern}\s*(?:{op_pattern}\s*)?(-?\d+(?:\.\d+)?)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    
                    if match:
                        amount_str = match.group(1)
                        try:
                            amount_val = float(amount_str)
                        except ValueError:
                            continue

                        fund_type = fund_key
                        if op_pattern in text or amount_val < 0:
                            operation = 'expense' if amount_val < 0 else op_key
                            if operation == 'expense' and amount_val > 0:
                                amount_val = -amount_val
                        else:
                            operation = 'income'
                        
                        amount = abs(amount_val)
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
            
            final_report = "\n".join(report_lines)
            return fix_html_tags(final_report)
            
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
            
            final_report = "\n".join(report_lines)
            return fix_html_tags(final_report)
            
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


class PersonalReportFormatter:
    """Personal report formatting functions"""
    
    def __init__(self):
        self.formatter = ReportFormatter()
    
    def safe_decimal_to_float(self, value):
        """Safely convert Decimal or any numeric value to float"""
        try:
            if isinstance(value, Decimal):
                return float(value)
            elif isinstance(value, (int, float)):
                return float(value)
            elif hasattr(value, '__float__'):
                return float(value)
            return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def format_personal_report(self, transactions: List[Dict], user_name: str, group_name: str = "個人") -> str:
        """Format personal financial report"""
        try:
            if not transactions:
                return f"📊 <b>{user_name}個人報表</b>\n\n❌ 本月暫無交易記錄"
            
            # Calculate totals by currency
            totals = {'TW': 0.0, 'CN': 0.0}
            for t in transactions:
                try:
                    if t.get('transaction_type') == 'income':
                        currency = str(t.get('currency', ''))
                        amount = self.safe_decimal_to_float(t.get('amount', 0))
                        if currency in totals:
                            totals[currency] += amount
                except Exception as e:
                    logger.warning(f"Error processing personal transaction: {e}")
                    continue
            
            # Calculate USDT equivalents
            tw_rate = 30.0
            cn_rate = 7.0
            tw_usdt = totals['TW'] / tw_rate if totals['TW'] > 0 else 0
            cn_usdt = totals['CN'] / cn_rate if totals['CN'] > 0 else 0
            
            # Build report
            report_lines = [
                f"📊 <b>{user_name}個人報表 ({group_name})</b>",
                "－－－－－－－－－－",
                "◉ 台幣業績",
                f"<code>NT${totals['TW']:,.0f}</code> → <code>USDT${tw_usdt:,.2f}</code>",
                "◉ 人民幣業績",
                f"<code>CN¥{totals['CN']:,.0f}</code> → <code>USDT${cn_usdt:,.2f}</code>",
                "－－－－－－－－－－"
            ]
            
            # Add transaction details by date
            daily_transactions = {}
            for t in transactions:
                try:
                    date_str = t.get('date')
                    if isinstance(date_str, str):
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                date_obj = datetime.fromisoformat(str(date_str)).date()
                            except ValueError:
                                continue
                    else:
                        date_obj = date_str
                    
                    day_key = date_obj.strftime('%m/%d')
                    
                    if day_key not in daily_transactions:
                        daily_transactions[day_key] = {'TW': 0, 'CN': 0}
                    
                    if t.get('transaction_type') == 'income':
                        currency = str(t.get('currency', ''))
                        amount = self.safe_decimal_to_float(t.get('amount', 0))
                        if currency in daily_transactions[day_key]:
                            daily_transactions[day_key][currency] += amount
                            
                except Exception as e:
                    logger.warning(f"Error processing daily personal transaction: {e}")
                    continue
            
            # Add daily summaries without USDT conversion for individual dates
            for day_key in sorted(daily_transactions.keys()):
                try:
                    amounts = daily_transactions[day_key]
                    if amounts['TW'] > 0 or amounts['CN'] > 0:
                        # Format date entry with amounts only (no USDT conversion)
                        daily_line = f"<b>{day_key} (日)</b> • "
                        amount_parts = []
                        if amounts['TW'] > 0:
                            amount_parts.append(f"<code>NT${amounts['TW']:,.0f}</code>")
                        if amounts['CN'] > 0:
                            amount_parts.append(f"<code>CN¥{amounts['CN']:,.0f}</code>")
                        daily_line += " ".join(amount_parts)
                        report_lines.append(daily_line)
                except Exception as e:
                    logger.warning(f"Error formatting daily personal summary: {e}")
                    continue
            
            final_report = "\n".join(report_lines)
            return fix_html_tags(final_report)
            
        except Exception as e:
            logger.error(f"Error formatting personal report: {e}")
            return f"❌ 個人報表格式化失敗: {str(e)}"


class FleetReportFormatter:
    """Fleet report formatting functions"""
    
    def safe_decimal_to_float(self, value):
        """Safely convert Decimal or any numeric value to float"""
        try:
            if isinstance(value, Decimal):
                return float(value)
            elif isinstance(value, (int, float)):
                return float(value)
            elif hasattr(value, '__float__'):
                return float(value)
            return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def format_fleet_report(self, all_groups_data: List[Dict]) -> str:
        """Format fleet report aggregating all groups"""
        try:
            if not all_groups_data:
                return "📊 <b>車隊報表</b>\n\n❌ 暫無數據"
            
            # Calculate total across all groups
            fleet_totals = {'TW': 0.0, 'CN': 0.0}
            group_summaries = {}
            
            for group_data in all_groups_data:
                try:
                    group_name = group_data.get('group_name', '未知群組')
                    transactions = group_data.get('transactions', [])
                    
                    group_totals = {'TW': 0.0, 'CN': 0.0}
                    
                    for t in transactions:
                        if t.get('transaction_type') == 'income':
                            currency = str(t.get('currency', ''))
                            amount = self.safe_decimal_to_float(t.get('amount', 0))
                            if currency in group_totals:
                                group_totals[currency] += amount
                                fleet_totals[currency] += amount
                    
                    if group_totals['TW'] > 0 or group_totals['CN'] > 0:
                        group_summaries[group_name] = group_totals
                        
                except Exception as e:
                    logger.warning(f"Error processing group data for fleet report: {e}")
                    continue
            
            # Calculate USDT equivalents
            tw_rate = 30.0
            cn_rate = 7.0
            fleet_tw_usdt = fleet_totals['TW'] / tw_rate if fleet_totals['TW'] > 0 else 0
            fleet_cn_usdt = fleet_totals['CN'] / cn_rate if fleet_totals['CN'] > 0 else 0
            
            # Build fleet report
            report_lines = [
                "📊 <b>車隊總報表</b>",
                "－－－－－－－－－－",
                "◉ 車隊台幣總業績",
                f"<code>NT${fleet_totals['TW']:,.0f}</code> → <code>USDT${fleet_tw_usdt:,.2f}</code>",
                "◉ 車隊人民幣總業績",
                f"<code>CN¥{fleet_totals['CN']:,.0f}</code> → <code>USDT${fleet_cn_usdt:,.2f}</code>",
                "－－－－－－－－－－"
            ]
            
            # Add group breakdowns
            for group_name, totals in group_summaries.items():
                try:
                    group_tw_usdt = totals['TW'] / tw_rate if totals['TW'] > 0 else 0
                    group_cn_usdt = totals['CN'] / cn_rate if totals['CN'] > 0 else 0
                    
                    report_lines.append(f"📍 <b>{group_name}</b>")
                    if totals['TW'] > 0:
                        report_lines.append(f"台幣: <code>NT${totals['TW']:,.0f}</code> → <code>USDT${group_tw_usdt:,.2f}</code>")
                    if totals['CN'] > 0:
                        report_lines.append(f"人民幣: <code>CN¥{totals['CN']:,.0f}</code> → <code>USDT${group_cn_usdt:,.2f}</code>")
                    report_lines.append("")
                except Exception as e:
                    logger.warning(f"Error formatting group summary: {e}")
                    continue
            
            final_report = "\n".join(report_lines)
            return fix_html_tags(final_report)
            
        except Exception as e:
            logger.error(f"Error formatting fleet report: {e}")
            return f"❌ 車隊報表格式化失敗: {str(e)}"
