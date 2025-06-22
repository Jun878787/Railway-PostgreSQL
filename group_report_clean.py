"""
Clean group report formatting with exact specification format
"""
from typing import List, Dict
from datetime import datetime, date
import logging

def safe_float(value):
    """Safely convert any numeric value to float"""
    try:
        if value is None:
            return 0.0
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return float(value)
        return 0.0
    except (ValueError, TypeError):
        return 0.0

async def format_group_report_exact(transactions: List[Dict], group_name: str = "群組", db_manager=None) -> str:
    """Format group financial report with exact specification format"""
    try:
        if not transactions:
            return f"<b>{group_name} 2025年6月群組報表</b>\n\n❌ 暫無數據"
        
        logger = logging.getLogger(__name__)
        logger.info(f"Processing {len(transactions)} transactions for group report")
        
        # Initialize daily data structure
        daily_transactions = {}
        daily_rates = {}
        
        # Process transactions and group by date
        for t in transactions:
            try:
                if t.get('transaction_type') == 'income':
                    currency = str(t.get('currency', ''))
                    amount = safe_float(t.get('amount', 0))
                    
                    logger.info(f"Processing transaction: currency={currency}, amount={amount}, type={t.get('transaction_type')}")
                    
                    # Group by date
                    trans_date = t.get('date')
                    if isinstance(trans_date, str):
                        try:
                            date_obj = datetime.strptime(trans_date, '%Y-%m-%d').date()
                        except ValueError:
                            logger.warning(f"Invalid date format: {trans_date}")
                            continue
                    else:
                        date_obj = trans_date
                    
                    if not date_obj:
                        logger.warning(f"No valid date found for transaction: {t}")
                        continue
                        
                    day_key = date_obj.strftime('%m/%d')
                    logger.info(f"Processing date {day_key} for currency {currency} amount {amount}")
                    
                    if day_key not in daily_transactions:
                        daily_transactions[day_key] = {'TW': [], 'CN': []}
                    
                    # Get user display name
                    user_id = t.get('user_id')
                    if db_manager and user_id:
                        display_name = await db_manager.get_user_display_name(user_id)
                        if not display_name:
                            display_name = t.get('display_name') or t.get('username', f"User {user_id}")
                    else:
                        display_name = t.get('display_name') or t.get('username', f"User {user_id}")
                    
                    # Only add if currency is valid
                    if currency in ['TW', 'CN']:
                        daily_transactions[day_key][currency].append({
                            'amount': amount,
                            'user': display_name
                        })
                        logger.info(f"Added transaction: {day_key} {currency} {amount} {display_name}")
                    else:
                        logger.warning(f"Invalid currency {currency}, skipping transaction")
                    
                    # Store date object for rate lookup
                    daily_rates[day_key] = date_obj
                    
            except Exception as e:
                logger.error(f"Error processing transaction: {e}")
                continue
        
        logger.info(f"Daily transactions processed: {daily_transactions}")
        
        # Check if we have any data
        if not daily_transactions:
            logger.warning("No daily transactions found, returning empty data message")
            return f"<b>{group_name} 2025年6月群組報表</b>\n\n❌ 暫無數據"
        
        # Calculate overall totals by summing daily USDT equivalents
        overall_tw_usdt = 0.0
        overall_cn_usdt = 0.0
        overall_tw_amount = 0.0
        overall_cn_amount = 0.0
        
        # Calculate daily totals and accumulate USDT using daily rates
        for day_key, day_data in daily_transactions.items():
            date_obj = daily_rates[day_key]
            
            # Get daily exchange rates
            if db_manager:
                day_rates_result = await db_manager.get_latest_exchange_rates(date_obj)
                day_tw_rate = day_rates_result.get('TWD', 30.0)
                day_cn_rate = day_rates_result.get('CNY', 7.0)
            else:
                day_tw_rate = 30.0
                day_cn_rate = 7.0
            
            # Calculate daily totals
            tw_daily = sum(trans['amount'] for trans in day_data['TW'])
            cn_daily = sum(trans['amount'] for trans in day_data['CN'])
            
            # Add to overall amounts
            overall_tw_amount += tw_daily
            overall_cn_amount += cn_daily
            
            # Convert to USDT using daily rates and accumulate
            if tw_daily > 0:
                overall_tw_usdt += tw_daily / day_tw_rate
            if cn_daily > 0:
                overall_cn_usdt += cn_daily / day_cn_rate
        
        # Build report
        report_lines = [
            f"<b>{group_name} 2025年6月群組報表</b>",
            ""
        ]
        
        # Overall totals section
        if overall_tw_amount > 0:
            report_lines.append(f"◉ 台幣業績")
            report_lines.append(f"NT${overall_tw_amount:,.0f} → USDT${overall_tw_usdt:,.2f}")
        
        if overall_cn_amount > 0:
            report_lines.append(f"◉ 人民幣業績")
            report_lines.append(f"CN¥{overall_cn_amount:,.0f} → USDT${overall_cn_usdt:,.2f}")
        
        report_lines.append("_____________________________")
        
        # Daily breakdowns
        for day_key in sorted(daily_transactions.keys()):
            try:
                day_data = daily_transactions[day_key]
                date_obj = daily_rates[day_key]
                
                # Get daily exchange rates
                if db_manager:
                    day_rates_result = await db_manager.get_latest_exchange_rates(date_obj)
                    day_tw_rate = day_rates_result.get('TWD', 30.0)
                    day_cn_rate = day_rates_result.get('CNY', 7.0)
                else:
                    day_tw_rate = 30.0
                    day_cn_rate = 7.0
                
                # Calculate daily totals
                tw_daily = sum(trans['amount'] for trans in day_data['TW'])
                cn_daily = sum(trans['amount'] for trans in day_data['CN'])
                
                if tw_daily > 0 or cn_daily > 0:
                    # Date header with rates
                    report_lines.append(f"{day_key} 台幣匯率{day_tw_rate} 人民幣匯率{day_cn_rate}")
                    
                    # Daily totals line with USDT conversion
                    daily_line_parts = []
                    if tw_daily > 0:
                        tw_daily_usdt = tw_daily / day_tw_rate
                        daily_line_parts.append(f"NT${tw_daily:,.0f}({tw_daily_usdt:,.2f})")
                    if cn_daily > 0:
                        cn_daily_usdt = cn_daily / day_cn_rate
                        daily_line_parts.append(f"CN¥{cn_daily:,.0f}({cn_daily_usdt:,.2f})")
                    
                    if daily_line_parts:
                        report_lines.append("  ".join(daily_line_parts))
                    
                    # Group user totals for this day
                    user_totals = {}
                    
                    # Process TW transactions
                    for trans in day_data['TW']:
                        user = trans['user']
                        if user not in user_totals:
                            user_totals[user] = {'TW': 0, 'CN': 0}
                        user_totals[user]['TW'] += trans['amount']
                    
                    # Process CN transactions
                    for trans in day_data['CN']:
                        user = trans['user']
                        if user not in user_totals:
                            user_totals[user] = {'TW': 0, 'CN': 0}
                        user_totals[user]['CN'] += trans['amount']
                    
                    # Add user detail lines
                    for user, amounts in user_totals.items():
                        user_line_parts = []
                        if amounts['TW'] > 0:
                            user_line_parts.append(f"NT${amounts['TW']:,.0f}")
                        if amounts['CN'] > 0:
                            user_line_parts.append(f"CN¥{amounts['CN']:,.0f}")
                        
                        if user_line_parts:
                            user_amounts = "  ".join(user_line_parts)
                            report_lines.append(f"   • {user_amounts} <code>{user}</code>")
                    
                    report_lines.append("")  # Blank line between days
                    
            except Exception as e:
                logger.error(f"Error formatting daily group summary: {e}")
                continue
        
        return "\n".join(report_lines)
        
    except Exception as e:
        return f"❌ 群組報表格式化失敗: {str(e)}"