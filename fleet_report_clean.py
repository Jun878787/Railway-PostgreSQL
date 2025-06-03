"""
Clean fleet report formatting with exact specification format for multi-group reports
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

async def format_fleet_report_exact(all_transactions: List[Dict], month: int, year: int, db_manager=None) -> str:
    """Format fleet report with exact specification format for multi-group data"""
    try:
        if not all_transactions:
            return f"<b>North™Sea 北金國際 {year}年{month}月車隊報表</b>\n\n❌ 暫無數據"
        
        logger = logging.getLogger(__name__)
        logger.info(f"Processing {len(all_transactions)} transactions for fleet report")
        
        # Initialize daily data structure
        daily_transactions = {}
        daily_rates = {}
        
        # Process transactions and group by date
        for t in all_transactions:
            try:
                if t.get('transaction_type') == 'income':
                    currency = str(t.get('currency', ''))
                    amount = safe_float(t.get('amount', 0))
                    
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
                        continue
                        
                    day_key = date_obj.strftime('%m/%d')
                    
                    if day_key not in daily_transactions:
                        daily_transactions[day_key] = {'TW': 0.0, 'CN': 0.0, 'groups': {}}
                    
                    # Only process if currency is valid
                    if currency in ['TW', 'CN']:
                        # Add to daily totals (all groups combined)
                        daily_transactions[day_key][currency] += amount
                        
                        # Group breakdown within each day
                        group_id = t.get('group_id')
                        if group_id and db_manager:
                            group_name = await db_manager.get_group_name(group_id) or f"群組{group_id}"
                            
                            if group_name not in daily_transactions[day_key]['groups']:
                                daily_transactions[day_key]['groups'][group_name] = {'TW': 0.0, 'CN': 0.0}
                            
                            daily_transactions[day_key]['groups'][group_name][currency] += amount
                    
                    # Store date object for rate lookup
                    daily_rates[day_key] = date_obj
                    
            except Exception as e:
                logger.error(f"Error processing transaction: {e}")
                continue
        
        logger.info(f"Daily transactions processed: {daily_transactions}")
        
        # Check if we have any data
        if not daily_transactions:
            logger.warning("No daily transactions found, returning empty data message")
            return f"<b>North™Sea 北金國際 {year}年{month}月車隊報表</b>\n\n❌ 暫無數據"
        
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
            
            # Add to overall amounts
            overall_tw_amount += day_data['TW']
            overall_cn_amount += day_data['CN']
            
            # Convert to USDT using daily rates and accumulate
            if day_data['TW'] > 0:
                overall_tw_usdt += day_data['TW'] / day_tw_rate
            if day_data['CN'] > 0:
                overall_cn_usdt += day_data['CN'] / day_cn_rate
        
        # Build report
        report_lines = [
            f"<b>North™Sea 北金國際 {year}年{month}月車隊報表</b>",
            ""
        ]
        
        # Overall totals section
        if overall_tw_amount > 0:
            report_lines.append("◉ 台幣業績")
            report_lines.append(f"NT${overall_tw_amount:,.0f} → USDT${overall_tw_usdt:,.2f}")
        
        if overall_cn_amount > 0:
            report_lines.append("◉ 人民幣業績")
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
                
                if day_data['TW'] > 0 or day_data['CN'] > 0:
                    # Date header with rates
                    report_lines.append(f"{day_key} 台幣匯率{day_tw_rate} 人民幣匯率{day_cn_rate}")
                    
                    # Daily totals line with USDT conversion (all groups combined)
                    daily_line_parts = []
                    if day_data['TW'] > 0:
                        tw_daily_usdt = day_data['TW'] / day_tw_rate
                        daily_line_parts.append(f"NT${day_data['TW']:,.0f}({tw_daily_usdt:,.2f})")
                    if day_data['CN'] > 0:
                        cn_daily_usdt = day_data['CN'] / day_cn_rate
                        daily_line_parts.append(f"CN¥{day_data['CN']:,.0f}({cn_daily_usdt:,.2f})")
                    
                    if daily_line_parts:
                        report_lines.append("  ".join(daily_line_parts))
                    
                    # Group breakdown for this day
                    for group_name, group_amounts in day_data['groups'].items():
                        group_line_parts = []
                        if group_amounts['TW'] > 0:
                            group_line_parts.append(f"NT${group_amounts['TW']:,.0f}")
                        if group_amounts['CN'] > 0:
                            group_line_parts.append(f"CN¥{group_amounts['CN']:,.0f}")
                        
                        if group_line_parts:
                            group_amounts_text = "  ".join(group_line_parts)
                            report_lines.append(f"   • {group_amounts_text} {group_name}")
                    
                    report_lines.append("")  # Blank line between days
                    
            except Exception as e:
                logger.error(f"Error formatting daily fleet summary: {e}")
                continue
        
        return "\n".join(report_lines)
        
    except Exception as e:
        return f"❌ 車隊報表格式化失敗: {str(e)}"