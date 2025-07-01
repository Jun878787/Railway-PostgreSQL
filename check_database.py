
#!/usr/bin/env python3
"""
資料庫檢查工具
檢查資料庫連接狀態和數據
"""

import asyncio
import os
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_database():
    """檢查資料庫狀態"""
    
    # 檢查資料庫類型
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql'):
        logger.info("🐘 檢測到 PostgreSQL 資料庫 (Railway)")
        try:
            from railway_database import RailwayDatabaseManager
            db = RailwayDatabaseManager()
            db_type = "PostgreSQL (Railway)"
        except ImportError as e:
            logger.error(f"❌ 無法導入 PostgreSQL 資料庫管理器: {e}")
            return
    else:
        logger.info("📁 使用 SQLite 資料庫 (本地)")
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db_type = "SQLite (本地)"
        except ImportError as e:
            logger.error(f"❌ 無法導入 SQLite 資料庫管理器: {e}")
            return
    
    print(f"\n{'='*50}")
    print(f"📊 資料庫狀態檢查")
    print(f"{'='*50}")
    print(f"資料庫類型: {db_type}")
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    try:
        # 檢查資料庫連接
        logger.info("🔍 檢查資料庫連接...")
        
        # 檢查 users 表
        if hasattr(db, 'get_connection'):
            if database_url and database_url.startswith('postgresql'):
                # PostgreSQL
                async with db._lock:
                    conn = db.get_connection()
                    try:
                        cursor = conn.cursor()
                        
                        # 檢查用戶數量
                        cursor.execute("SELECT COUNT(*) FROM users")
                        user_count = cursor.fetchone()[0]
                        print(f"👥 用戶數量: {user_count}")
                        
                        # 檢查交易數量
                        cursor.execute("SELECT COUNT(*) FROM transactions")
                        transaction_count = cursor.fetchone()[0]
                        print(f"💰 交易記錄數量: {transaction_count}")
                        
                        # 檢查群組數量
                        cursor.execute("SELECT COUNT(*) FROM groups")
                        group_count = cursor.fetchone()[0]
                        print(f"👥 群組數量: {group_count}")
                        
                        # 檢查匯率記錄
                        cursor.execute("SELECT COUNT(*) FROM exchange_rates")
                        rate_count = cursor.fetchone()[0]
                        print(f"💱 匯率記錄數量: {rate_count}")
                        
                        # 最近的交易
                        cursor.execute("""
                        SELECT t.date, t.currency, t.amount, t.transaction_type, u.first_name 
                        FROM transactions t 
                        LEFT JOIN users u ON t.user_id = u.user_id 
                        ORDER BY t.created_at DESC 
                        LIMIT 5
                        """)
                        recent_transactions = cursor.fetchall()
                        
                        print(f"\n📋 最近 5 筆交易:")
                        if recent_transactions:
                            for i, tx in enumerate(recent_transactions, 1):
                                date_str = tx[0].strftime('%m/%d') if tx[0] else "N/A"
                                currency = tx[1] or "N/A"
                                amount = tx[2] or 0
                                tx_type = "收入" if tx[3] == 'income' else "支出"
                                user_name = tx[4] or "未知用戶"
                                print(f"  {i}. {date_str} - {currency}{amount:,.0f} ({tx_type}) - {user_name}")
                        else:
                            print("  📝 暫無交易記錄")
                        
                    finally:
                        conn.close()
            else:
                # SQLite
                async with db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 檢查用戶數量
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    print(f"👥 用戶數量: {user_count}")
                    
                    # 檢查交易數量
                    cursor.execute("SELECT COUNT(*) FROM transactions")
                    transaction_count = cursor.fetchone()[0]
                    print(f"💰 交易記錄數量: {transaction_count}")
                    
                    # 檢查群組數量
                    cursor.execute("SELECT COUNT(*) FROM groups")
                    group_count = cursor.fetchone()[0]
                    print(f"👥 群組數量: {group_count}")
                    
                    # 檢查匯率記錄
                    cursor.execute("SELECT COUNT(*) FROM exchange_rates")
                    rate_count = cursor.fetchone()[0]
                    print(f"💱 匯率記錄數量: {rate_count}")
                    
                    # 最近的交易
                    cursor.execute("""
                    SELECT t.date, t.currency, t.amount, t.transaction_type, u.first_name 
                    FROM transactions t 
                    LEFT JOIN users u ON t.user_id = u.user_id 
                    ORDER BY t.created_at DESC 
                    LIMIT 5
                    """)
                    recent_transactions = cursor.fetchall()
                    
                    print(f"\n📋 最近 5 筆交易:")
                    if recent_transactions:
                        for i, tx in enumerate(recent_transactions, 1):
                            date_str = tx[0] if tx[0] else "N/A"
                            currency = tx[1] or "N/A"
                            amount = tx[2] or 0
                            tx_type = "收入" if tx[3] == 'income' else "支出"
                            user_name = tx[4] or "未知用戶"
                            print(f"  {i}. {date_str} - {currency}{amount:,.0f} ({tx_type}) - {user_name}")
                    else:
                        print("  📝 暫無交易記錄")
        
        print(f"\n✅ 資料庫檢查完成！")
        
    except Exception as e:
        logger.error(f"❌ 資料庫檢查失敗: {e}")
        print(f"❌ 錯誤: {e}")

async def main():
    """主程序"""
    await check_database()

if __name__ == "__main__":
    asyncio.run(main())
