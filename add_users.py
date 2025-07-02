
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
            'username': 'M8-N3',
            'display_name': '@M8-N3',
            'first_name': 'M8-N3'
        },
        {
            'user_id': 1002,
            'username': 'M8-NIKE', 
            'display_name': '@M8-NIKE',
            'first_name': 'M8-NIKE'
        },
        {
            'user_id': 1003,
            'username': 'M8-J',
            'display_name': '@M8-J', 
            'first_name': 'M8-J'
        },
        {
            'user_id': 1004,
            'username': 'M8-Z8',
            'display_name': '@M8-Z8',
            'first_name': 'M8-Z8'
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
