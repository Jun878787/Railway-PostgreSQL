#!/usr/bin/env python3
"""
測試匯率設定功能
"""

import asyncio
import os
from datetime import date, datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_exchange_rates():
    """測試匯率設定和讀取功能"""
    
    # 檢查是否有 PostgreSQL 連接
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql'):
        logger.info("🐘 Testing PostgreSQL database...")
        from railway_database import RailwayDatabaseManager
        db = RailwayDatabaseManager()
    else:
        logger.info("📁 Testing SQLite database...")
        from database import DatabaseManager
        db = DatabaseManager()
    
    try:
        # 測試設定台幣匯率
        today = date.today()
        test_user_id = 123456789
        
        logger.info("測試設定台幣匯率...")
        result1 = await db.set_exchange_rate(today, 33.33, test_user_id, 'TW')
        logger.info(f"台幣匯率設定結果: {result1}")
        
        # 測試設定人民幣匯率
        logger.info("測試設定人民幣匯率...")
        result2 = await db.set_exchange_rate(today, 6.9, test_user_id, 'CN')
        logger.info(f"人民幣匯率設定結果: {result2}")
        
        # 測試讀取匯率
        logger.info("測試讀取台幣匯率...")
        tw_rate = await db.get_exchange_rate(today, 'TW')
        logger.info(f"台幣匯率讀取結果: {tw_rate}")
        
        logger.info("測試讀取人民幣匯率...")
        cn_rate = await db.get_exchange_rate(today, 'CN')
        logger.info(f"人民幣匯率讀取結果: {cn_rate}")
        
        # 驗證結果
        if result1 and result2 and tw_rate == 33.33 and cn_rate == 6.9:
            logger.info("✅ 匯率功能測試成功！")
            return True
        else:
            logger.error("❌ 匯率功能測試失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試過程出錯: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_exchange_rates())
    if result:
        print("匯率功能正常運作")
    else:
        print("匯率功能需要修正")