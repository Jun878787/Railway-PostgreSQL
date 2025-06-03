#!/usr/bin/env python3
"""
模擬 Telegram 匯率設定測試
"""

import asyncio
import os
from datetime import date
import logging
import re

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockUser:
    def __init__(self):
        self.id = 123456789
        self.first_name = "測試用戶"

class MockUpdate:
    def __init__(self):
        self.effective_user = MockUser()

async def test_exchange_rate_handler():
    """測試匯率設定處理邏輯"""
    
    # 導入資料庫
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        from railway_database import RailwayDatabaseManager
        db = RailwayDatabaseManager()
    else:
        from database import DatabaseManager
        db = DatabaseManager()
    
    # 導入時區工具
    import timezone_utils
    timezone_utils.setup_timezone()
    
    # 模擬匯率設定測試
    test_cases = [
        "設定06/01匯率33.33",
        "設定匯率30.22", 
        "設定CN匯率6.9",
        "設定06/01CN匯率7.2"
    ]
    
    for text in test_cases:
        logger.info(f"測試指令: {text}")
        
        try:
            # 解析台幣匯率
            tw_rate_match = re.search(r'設定(?:(\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}月\d{1,2}日))?匯率([\d.]+)', text)
            cn_rate_match = re.search(r'設定(?:(\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}月\d{1,2}日))?CN匯率([\d.]+)', text)
            
            if tw_rate_match:
                date_str = tw_rate_match.group(1)
                rate_str = tw_rate_match.group(2)
                currency_type = "台幣"
                
                rate = float(rate_str)
                
                # 解析日期
                if date_str:
                    from utils import ValidationUtils
                    rate_date = ValidationUtils.validate_date(date_str)
                    if not rate_date:
                        logger.error("日期格式錯誤")
                        continue
                else:
                    rate_date = timezone_utils.get_taiwan_today()
                
                # 設定匯率（修正版本 - 包含貨幣類型）
                success = await db.set_exchange_rate(rate_date, rate, 123456789, 'TW')
                if success:
                    logger.info(f"✅ {currency_type}匯率設定成功: {rate:.2f} 日期: {rate_date}")
                else:
                    logger.error(f"❌ {currency_type}匯率設定失敗")
                    
            elif cn_rate_match:
                date_str = cn_rate_match.group(1)
                rate_str = cn_rate_match.group(2)
                currency_type = "人民幣"
                
                rate = float(rate_str)
                
                # 解析日期
                if date_str:
                    from utils import ValidationUtils
                    rate_date = ValidationUtils.validate_date(date_str)
                    if not rate_date:
                        logger.error("日期格式錯誤")
                        continue
                else:
                    rate_date = timezone_utils.get_taiwan_today()
                
                # 設定人民幣匯率
                success = await db.set_exchange_rate(rate_date, rate, 123456789, 'CN')
                if success:
                    logger.info(f"✅ {currency_type}匯率設定成功: {rate:.2f} 日期: {rate_date}")
                else:
                    logger.error(f"❌ {currency_type}匯率設定失敗")
                    
        except Exception as e:
            logger.error(f"處理錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_exchange_rate_handler())