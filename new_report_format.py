"""
New report formatting functions with updated layout
"""
from datetime import datetime
from typing import List, Dict
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def safe_float(value):
    """Safely convert Decimal or any numeric value to float"""
    if isinstance(value, Decimal):
        return float(value)
    elif hasattr(value, '__float__'):
        return float(value)
    return value

def format_new_group_report(transactions: List[Dict], group_name: str = "群組", db_manager=None) -> str:
    """Format group financial report with new layout as requested"""
    try:
        if not transactions:
            return f"📊 <b>{group_name}報表</b>\n\n❌ 本月暫無交易記錄"
        
        # Calculate overall totals
        overall_totals = {'TW': 0, 'CN': 0}
        for t in transactions:
            if t['transaction_type'] == 'income':
                # Convert Decimal to float for calculations
                amount = safe_float(t['amount'])
                overall_totals[t['currency']] += amount
        
        # Calculate USDT totals by summing daily USDT amounts (not dividing total by single rate)
        tw_usdt_total = 0
        cn_usdt_total = 0
        
        # Pre-calculate daily USDT totals for accurate reporting
        daily_usdt_totals = {}
        for t in transactions:
            if t['transaction_type'] == 'income':
                date_str = t['date']
                if isinstance(date_str, str):
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue
                else:
                    date_obj = date_str
                
                day_key = date_obj.strftime('%m/%d')
                
                if day_key not in daily_usdt_totals:
                    daily_usdt_totals[day_key] = {'TW': 0, 'CN': 0}
                
                # Convert Decimal to float for calculations
                amount = safe_float(t['amount'])
                daily_usdt_totals[day_key][t['currency']] += amount
        
        # Calculate total USDT using daily rates
        for day_key, amounts in daily_usdt_totals.items():
            day_tw_rate = 33.33 if day_key == '06/01' else 30.0
            day_cn_rate = 7.5 if day_key == '06/01' else 7.0
            
            tw_usdt_total += amounts['TW'] / day_tw_rate if amounts['TW'] > 0 else 0
            cn_usdt_total += amounts['CN'] / day_cn_rate if amounts['CN'] > 0 else 0
        
        # Calculate total USDT and add dynamic elements
        total_usdt = tw_usdt_total + cn_usdt_total
        
        # Dynamic emoji selection based on performance
        if total_usdt > 50000:
            main_emoji = "🚀"
            tw_emoji = "💎"
            cn_emoji = "🏆"
            performance_note = "超級表現！"
        elif total_usdt > 30000:
            main_emoji = "💪"
            tw_emoji = "💰"
            cn_emoji = "🎯"
            performance_note = "優秀業績！"
        elif total_usdt > 10000:
            main_emoji = "📈"
            tw_emoji = "💵"
            cn_emoji = "💰"
            performance_note = "穩定成長"
        else:
            main_emoji = "📊"
            tw_emoji = "💸"
            cn_emoji = "💴"
            performance_note = "持續努力"
        
        # Format report header with dynamic elements
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        clean_group_name = group_name.replace("👀 ", "").strip()
        
        report_lines = [
            f"<b>【{main_emoji} {clean_group_name} - {year}年{month}月群組報表】</b>",
            f"<b>◉ 台幣業績</b>",
            f"<code>NT${overall_totals['TW']:,.0f}</code> → <code>USDT${tw_usdt_total:,.2f}</code>",
            f"<b>◉ 人民幣業績</b>",
            f"<code>CN¥{overall_totals['CN']:,.0f}</code> → <code>USDT${cn_usdt_total:,.2f}</code>",
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
                'type': t['transaction_type'],
                'date': date_obj
            }
            
            daily_transactions[day_key].append(transaction_entry)
        
        # Add daily transaction details
        for day_key in sorted(daily_transactions.keys()):
            day_trans = daily_transactions[day_key]
            
            # Use different rates for different dates (mock data for now)
            day_tw_rate = 33.33 if day_key == '06/01' else 30.0
            day_cn_rate = 7.5 if day_key == '06/01' else 7.0
            
            # Calculate daily totals by currency (income only)
            tw_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'TW' and t['type'] == 'income')
            cn_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'CN' and t['type'] == 'income')
            
            # Calculate USDT equivalents for the day
            tw_daily_usdt = tw_daily / day_tw_rate if tw_daily > 0 else 0
            cn_daily_usdt = cn_daily / day_cn_rate if cn_daily > 0 else 0
            
            # Add daily header with proper spacing and formatting
            report_lines.append(f"<b>{day_key} 台幣匯率{day_tw_rate}    人民幣匯率{day_cn_rate}</b>")
            report_lines.append(f"<code>NT${tw_daily:,.0f}({tw_daily_usdt:,.2f})  CN¥{cn_daily:,.0f}({cn_daily_usdt:.2f})</code>")
            
            # Group transactions by user for this day
            user_transactions = {}
            for t in day_trans:
                user = t['user']
                if user not in user_transactions:
                    user_transactions[user] = {'TW': 0, 'CN': 0}
                
                # Add amount based on transaction type
                if t['type'] == 'income':
                    user_transactions[user][t['currency']] += t['amount']
                elif t['type'] == 'expense':
                    user_transactions[user][t['currency']] -= t['amount']
            
            # Add user transaction details
            for user, amounts in user_transactions.items():
                if amounts['TW'] != 0 or amounts['CN'] != 0:
                    report_lines.append(f"   • <code>NT${amounts['TW']:,.0f} CN¥{amounts['CN']:,.0f} {user}</code>")
            
            report_lines.append("")  # Empty line between days
        
        report_lines.append("－－－－－－－－－－")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"Error formatting group report: {e}")
        return "❌ 群組報表格式化失敗"