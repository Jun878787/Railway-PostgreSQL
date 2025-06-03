"""
New report formatting functions with updated layout
"""
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def format_new_group_report(transactions: List[Dict], group_name: str = "群組") -> str:
    """Format group financial report with new layout as requested"""
    try:
        if not transactions:
            return f"📊 <b>{group_name}報表</b>\n\n❌ 本月暫無交易記錄"
        
        # Calculate overall totals
        overall_totals = {'TW': 0, 'CN': 0}
        for t in transactions:
            if t['transaction_type'] == 'income':
                overall_totals[t['currency']] += t['amount']
        
        # USDT conversion rates (default rates)
        tw_rate = 30.2  # TWD to USD rate
        cn_rate = 7.2   # CNY to USD rate
        
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