"""
Fleet report formatting for North Sea Financial Bot
Handles comprehensive fleet report generation with proper HTML formatting
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, date
from decimal import Decimal
from utils import fix_html_tags

logger = logging.getLogger(__name__)

class FleetReportFormatter:
    """Comprehensive fleet report formatter"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def safe_float(self, value):
        """Safely convert any numeric value to float"""
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
    
    async def format_comprehensive_fleet_report(self, month: int = None, year: int = None) -> str:
        """Format comprehensive fleet report with daily breakdowns and group details"""
        try:
            if not month or not year:
                now = datetime.now()
                month = now.month
                year = now.year
            
            # Get all transactions from all groups
            all_transactions = await self.db.get_all_groups_transactions(month, year)
            
            if not all_transactions:
                return "<b>North™Sea 北金國際 2025年6月車隊報表</b>\n\n❌ 暫無數據"
            
            # Calculate overall totals
            overall_totals = {'TW': 0.0, 'CN': 0.0}
            daily_transactions = {}
            group_data = {}
            
            for t in all_transactions:
                try:
                    if t.get('transaction_type') == 'income':
                        currency = str(t.get('currency', ''))
                        amount = self.safe_float(t.get('amount', 0))
                        
                        if currency in overall_totals:
                            overall_totals[currency] += amount
                        
                        # Group by date
                        trans_date = t.get('transaction_date') or t.get('date')
                        if isinstance(trans_date, str):
                            date_obj = datetime.strptime(trans_date, '%Y-%m-%d').date()
                        else:
                            date_obj = trans_date
                        
                        day_key = date_obj.strftime('%m/%d')
                        
                        if day_key not in daily_transactions:
                            daily_transactions[day_key] = []
                        
                        # Get user display name
                        user_id = t.get('user_id')
                        display_name = await self.db.get_user_display_name(user_id) if user_id else "未知用戶"
                        if not display_name:
                            display_name = t.get('username', f"User {user_id}")
                        
                        # Get group name
                        group_id = t.get('group_id')
                        group_name = await self.db.get_group_name(group_id) if group_id else "未知群組"
                        
                        daily_transactions[day_key].append({
                            'currency': currency,
                            'amount': amount,
                            'user': display_name,
                            'group': group_name,
                            'type': 'income'
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing transaction for fleet report: {e}")
                    continue
            
            # Calculate USDT equivalents
            tw_rate = 33.33  # Default rate for 06/01
            cn_rate = 7.5    # Default rate for 06/01
            
            tw_usdt_total = overall_totals['TW'] / tw_rate if overall_totals['TW'] > 0 else 0
            cn_usdt_total = overall_totals['CN'] / cn_rate if overall_totals['CN'] > 0 else 0
            
            # Build report header
            report_lines = [
                "<b>North™Sea 北金國際 2025年6月車隊報表</b>",
                "<b>◉ 台幣業績</b>",
                f"<code>NT${overall_totals['TW']:,.0f}</code> → <code>USDT${tw_usdt_total:,.2f}</code>",
                "<b>◉ 人民幣業績</b>",
                f"<code>CN¥{overall_totals['CN']:,.0f}</code> → <code>USDT${cn_usdt_total:,.2f}</code>",
                "_____________________________"
            ]
            
            # Add daily summaries
            for day_key in sorted(daily_transactions.keys()):
                try:
                    day_trans = daily_transactions[day_key]
                    
                    # Calculate daily totals by currency
                    tw_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'TW')
                    cn_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'CN')
                    
                    # Get daily exchange rates (simplified for now)
                    day_tw_rate = 33.33 if day_key == '06/01' else 30.0
                    day_cn_rate = 7.5 if day_key == '06/01' else 7.0
                    
                    # Calculate USDT equivalents
                    tw_daily_usdt = tw_daily / day_tw_rate if tw_daily > 0 else 0
                    cn_daily_usdt = cn_daily / day_cn_rate if cn_daily > 0 else 0
                    
                    # Add date header
                    report_lines.append(f"<b>{day_key} 台幣匯率{day_tw_rate} 人民幣匯率{day_cn_rate}</b>")
                    
                    # Add daily totals line
                    daily_line_parts = []
                    if tw_daily > 0:
                        daily_line_parts.append(f"<code>NT${tw_daily:,.0f}({tw_daily_usdt:,.2f})</code>")
                    if cn_daily > 0:
                        daily_line_parts.append(f"<code>CN¥{cn_daily:,.0f}({cn_daily_usdt:,.2f})</code>")
                    
                    if daily_line_parts:
                        report_lines.append(" ".join(daily_line_parts))
                    
                    # Group transactions by user for this day
                    user_daily_totals = {}
                    for trans in day_trans:
                        user = trans['user']
                        group = trans['group']
                        user_key = f"{user} {group}" if group != "未知群組" else user
                        
                        if user_key not in user_daily_totals:
                            user_daily_totals[user_key] = {'TW': 0, 'CN': 0}
                        user_daily_totals[user_key][trans['currency']] += trans['amount']
                    
                    # Add user transaction lines
                    for user_key, amounts in user_daily_totals.items():
                        user_line_parts = []
                        if amounts['TW'] > 0:
                            user_line_parts.append(f"<code>NT${amounts['TW']:,.0f}</code>")
                        if amounts['CN'] > 0:
                            user_line_parts.append(f"<code>CN¥{amounts['CN']:,.0f}</code>")
                        
                        if user_line_parts:
                            # Extract group name for display
                            if '👀' in user_key:
                                display_name = user_key.split(' ')[-1]  # Get the group name part
                            else:
                                display_name = user_key
                            
                            user_amounts = " ".join(user_line_parts)
                            report_lines.append(f"    • {user_amounts} {display_name}")
                    
                    report_lines.append("")  # Add blank line between days
                    
                except Exception as e:
                    logger.warning(f"Error formatting daily fleet summary: {e}")
                    continue
            
            # Join and fix HTML tags
            final_report = "\n".join(report_lines)
            return fix_html_tags(final_report)
            
        except Exception as e:
            logger.error(f"Error formatting comprehensive fleet report: {e}")
            return f"❌ 車隊報表格式化失敗: {str(e)}"