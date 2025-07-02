
"""
批量添加用戶到資料庫的腳本
"""
import asyncio
import sys
import os

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

async def add_multiple_users():
    """批量添加用戶"""
    db = DatabaseManager()
    
    # 用戶列表  
    users_to_add = [
        {
            'user_id': 1001,  # 這裡需要實際的 Telegram user_id
            'username': 'N3',
            'display_name': '@N3',
            'first_name': 'N3'
        },
        {
            'user_id': 1002,
            'username': 'J', 
            'display_name': '@J',
            'first_name': 'J'
        },
        {
            'user_id': 1003,
            'username': 'NIKE',
            'display_name': '@NIKE', 
            'first_name': 'NIKE'
        },
        {
            'user_id': 1004,
            'username': 'Z8',
            'display_name': '@Z8',
            'first_name': 'Z8'
        }
    ]
    
    print("🚀 開始批量添加用戶...")
    
    for user in users_to_add:
        success = await db.add_user(
            user_id=user['user_id'],
            username=user['username'],
            display_name=user['display_name'],
            first_name=user['first_name']
        )
        
        if success:
            print(f"✅ 成功添加用戶: {user['username']}")
        else:
            print(f"❌ 添加用戶失敗: {user['username']}")
    
    print("📊 批量添加完成！")

if __name__ == "__main__":
    asyncio.run(add_multiple_users())
