」 "
#co #co
」 "
從 約。 。 。。
從 打字 進口 列表。。
。 1月。。

。 = 。.。(_____)

。 _new_group_report(。: 。[。], _ 。: str = "你", db__thery=。) -> str:
    “ 」。
 :
 “ “ “ “ ” “ “ “ “:
 ± f"📊 <b>{}<>_/b\n\n❌ honhy caphy"
        
 ##
 *__ = {'TW': 0, 'CN': 0}
 #t 2000:
 | t ["capin+_+"] == "」 :
 *_#[t['+']] += t['+']
        
 # USDT # 中
 tw_rate = 30。. 。. 。. 。. 。. 。0 # * TWD ± ± ±
 cn_rate = 7。. 。. 。. 。. 。. 。2###############################################################################################################################################################################################################################################################
        
 tw_usdt = ± __±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±± ['TW'] /tw_rate ± *_±±±±±±±± ['TW'] > 0 ± 0
 cn_usdt = ± __±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±± ['CN'] /cn_rate ± *_±±±±±±±± ['CN'] > 0 ± 0
        
 ##
 _  = *。. 。. 。. 。Ø））））））））
 * 。 = *_INU。。。。。。* 。
 = _INU。。。。。。
 ± = f"{}}}}}}}_}_}_}_}_}_{- } { }}“}“ }“ }“ }“ }“ }“ }“ }“ }“ }“ }“ }“ }“ }“ }“ 
        
 “ = “
 f"<b>【{}}}}}}}】<>/b"}】<>/b"}】<><>bb",
 f"<b>◉ <>/b",
 f"<code>nt${}}}}}}}<__['TW']:,.0f>/code→ <> code$}<__['TW']:,.0f>/code→ <> code$}<__['TW']:,.0f>/code→ <> code$}<__['TW']:,.0f>/code→ <> code$}<__['TW']:,.0f>/code→ <> code$}<__['TW']:,.0f>/code→ <> code${。}<tw_usdt:,.2f>/",
 f"<b>◉"|f"<b>◉"適* <>/b",/b>,<>/b",/b>",
 f"<code>cn¥{}}}}}}}<__['CN']:,.0f>/code→ <> code$}<__['CN']:,.0f>/code→ <> code$}<__['CN']:,.0f>/code→ <> code$}<__['CN']:,.0f>/code→ <> code$}<__['CN']:,.0f>/code→ <> code$}<__['CN']:,.0f>/code→ <> code${。}<cn_usdt:,.2f>/",
 "－－－－－－－－－－"
        ]
        
 # ichiuceling µcaphice
 “IU_ cccce_ = {}”
 #t 2000:
 IUNIC_str = t['#']
 [0070]（IUNE_str,str）:
 :
 IUNE_obj = * [。0070]（IUNE_str,「%Y-%m-%d」)。()
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
            
            # Get exchange rates for this specific date from database
            day_tw_rate = tw_rate  # Default rate
            day_cn_rate = cn_rate  # Default rate
            
            # For now, use default rates - async rate lookup will be implemented later
            # TODO: Implement proper async rate lookup in calling function
            
            # Calculate daily totals by currency (income only)
            tw_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'TW' and t['type'] == 'income')
            cn_daily = sum(t['amount'] for t in day_trans if t['currency'] == 'CN' and t['type'] == 'income')
            
            # Calculate USDT equivalents for the day
            tw_daily_usdt = tw_daily / day_tw_rate if tw_daily > 0 else 0
            cn_daily_usdt = cn_daily / day_cn_rate if cn_daily > 0 else 0
            
            # Add daily header
            report_lines.append(f"<b>{day_key} 台幣匯率{day_tw_rate}    人民幣匯率{day_cn_rate}</b>")
            report_lines.append(f"<code>NT${tw_daily:,.0f}({tw_daily_usdt:.2f})  CN¥{cn_daily:,.0f}({cn_daily_usdt:.2f})</code>")
            
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
            
            # Add user transaction details (only show users with transactions)
            for user, amounts in user_transactions.items():
                if amounts['TW'] != 0 or amounts['CN'] != 0:
                    report_lines.append(f"   • <code>NT${amounts['TW']:,.0f} CN¥{amounts['CN']:,.0f} {user}</code>")
            
            report_lines.append("")  # Empty line between days
        
        report_lines.append("－－－－－－－－－－")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"Error formatting group report: {e}")
        return "❌ 群組報表格式化失敗"