# Railway 部署指南

## 必要檔案清單

請確保以下檔案都上傳到 Railway：

### 核心程式檔案
- `main_railway.py` - 主程式（Railway 版本）
- `handlers.py` - 訊息處理器
- `database.py` - SQLite 資料庫管理器
- `railway_database.py` - PostgreSQL 資料庫管理器
- `config.py` - 配置檔案
- `keyboards.py` - 鍵盤布局
- `utils.py` - 工具函數
- `timezone_utils.py` - 時區工具
- `list_formatter.py` - 列表格式化
- `new_report_format.py` - 報告格式

### 配置檔案
- `Procfile` - 啟動配置
- `runtime.txt` - Python 版本
- `pyproject.toml` - 依賴包配置
- `railway.toml` - Railway 配置

## 環境變數設定

在 Railway 專案中設定：
- `BOT_TOKEN` = 你的機器人令牌
- `GOOGLE_MAPS_API_KEY` = 你的 Google Maps API 金鑰
- `DATABASE_URL` = 由 PostgreSQL 服務自動提供

## 部署步驟

1. 添加 PostgreSQL 服務到 Railway 專案
2. 上傳所有必要檔案
3. 設定環境變數
4. 部署並測試

部署完成後測試匯率設定功能：`設定06/01匯率33.33`