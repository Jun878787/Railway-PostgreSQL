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
            
            # Calculate USDT equivalents by summing daily conversions (will be calculated in daily loop)
            tw_usdt_total = 0.0
            cn_usdt_total = 0.0
            
            # Placeholder for report lines - header will be built after calculations
            report_lines = []
            
            # Add daily summaries
            for day_key in sorted(daily_transactions.keys()):
                try:
                    day_trans = daily_transactions[day_key]
                    
                    # Calculate daily totals by currency
                    tw_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'TW')
                    cn_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'CN')
                    
                    # Get daily exchange rates from database using proper date conversion
                    from datetime import datetime
                    date_obj = datetime.strptime(f"2025-{day_key}", "%Y-%m/%d").date()
                    
                    # Get actual exchange rates for this specific date
                    day_tw_rate = await self.db.get_exchange_rate(date_obj, 'TW') or 30.0
                    day_cn_rate = await self.db.get_exchange_rate(date_obj, 'CN') or 7.0
                    
                    # Calculate USDT equivalents
                    tw_daily_usdt = tw_daily / day_tw_rate if tw_daily > 0 else 0
                    cn_daily_usdt = cn_daily / day_cn_rate if cn_daily > 0 else 0
                    
                    # Accumulate total USDT amounts
                    tw_usdt_total += tw_daily_usdt
                    cn_usdt_total += cn_daily_usdt
                    
                    # Add date header with consistent formatting
                    report_lines.append(f"<b>{day_key} 台幣匯率{day_tw_rate:.2f} 人民幣匯率{day_cn_rate:.1f}</b>")
                    
                    # Add daily totals line
                    daily_line_parts = []
                    if tw_daily > 0:
                        daily_line_parts.append(f"<code>NT${tw_daily:,.0f}({tw_daily_usdt:,.2f})</code>")
                    if cn_daily > 0:
                        daily_line_parts.append(f"<code>CN¥{cn_daily:,.0f}({cn_daily_usdt:,.2f})</code>")
                    
                    if daily_line_parts:
                        report_lines.append(" ".join(daily_line_parts))
                    
                    # Group transactions by group for this day
                    group_daily_totals = {}
                    for trans in day_trans:
                        group = trans['group']
                        
                        if group not in group_daily_totals:
                            group_daily_totals[group] = {'TW': 0, 'CN': 0}
                        group_daily_totals[group][trans['currency']] += trans['amount']
                    
                    # Display transactions grouped by group
                    for group, amounts in group_daily_totals.items():
                        group_line_parts = []
                        if amounts['TW'] > 0:
                            group_line_parts.append(f"<code>NT${amounts['TW']:,.0f}</code>")
                        else:
                            group_line_parts.append(f"<code>NT$0</code>")
                        
                        if amounts['CN'] > 0:
                            group_line_parts.append(f"<code>CN¥{amounts['CN']:,.0f}</code>")
                        else:
                            group_line_parts.append(f"<code>CN¥0</code>")
                        
                        group_amounts = " ".join(group_line_parts)
                        report_lines.append(f"    • {group_amounts} {group}")
                    
                    report_lines.append("")  # Add blank line between days
                    
                except Exception as e:
                    logger.warning(f"Error formatting daily fleet summary: {e}")
                    continue
            
            # Build report header with correct USDT totals
            final_report = [
                "<b>North™Sea 北金國際 2025年6月車隊報表</b>",
                "<b>◉ 台幣業績</b>",
                f"<code>NT${overall_totals['TW']:,.0f}</code> → <code>USDT${tw_usdt_total:,.2f}</code>",
                "<b>◉ 人民幣業績</b>",
                f"<code>CN¥{overall_totals['CN']:,.0f}</code> → <code>USDT${cn_usdt_total:,.2f}</code>",
                "_____________________________"
            ]
            
            # Add daily details
            final_report.extend(report_lines)
            
            # Join and fix HTML tags
            final_report_text = "\n".join(final_report)
            return fix_html_tags(final_report_text)
            
        except Exception as e:
            logger.error(f"Error formatting comprehensive fleet report: {e}")
            return f"❌ 車隊報表格式化失敗: {str(e)}"