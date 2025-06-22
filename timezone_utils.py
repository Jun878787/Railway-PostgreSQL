"""
台灣時區工具模組
處理所有時間相關的操作，確保使用台灣時區
"""
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import config

# 台灣時區
TAIWAN_TZ = ZoneInfo("Asia/Taipei")

def get_taiwan_now():
    """獲取台灣當前時間"""
    return datetime.now(TAIWAN_TZ)

def get_taiwan_today():
    """獲取台灣當前日期"""
    return get_taiwan_now().date()

def convert_to_taiwan_time(dt):
    """將datetime轉換為台灣時區"""
    if dt.tzinfo is None:
        # 如果沒有時區信息，假設為UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TAIWAN_TZ)

def format_taiwan_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """格式化台灣時間"""
    if isinstance(dt, str):
        # 如果是字符串，先轉換為datetime
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    taiwan_dt = convert_to_taiwan_time(dt)
    return taiwan_dt.strftime(format_str)

def get_taiwan_weekday_chinese(date_obj=None):
    """獲取中文星期幾"""
    if date_obj is None:
        date_obj = get_taiwan_today()
    
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    return weekdays[date_obj.weekday()]

def setup_timezone():
    """設置系統時區為台灣時區"""
    timezone_str = config.get_timezone()
    os.environ['TZ'] = timezone_str
    
    try:
        import time
        time.tzset()
        print(f"✅ 時區設定為: {timezone_str}")
    except AttributeError:
        # Windows 系統可能沒有 tzset
        print(f"✅ 時區環境變數設定為: {timezone_str}")