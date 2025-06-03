# Railway 部署指南 - 北金管家 Telegram Bot

## 概述
本指南將協助您在 Railway 平台上成功部署北金管家 North™Sea ᴍ8ᴘ Telegram 財務管理機器人。

## 前置需求

### 1. Railway 帳號
- 註冊 [Railway](https://railway.app) 帳號
- 連接您的 GitHub 帳號

### 2. 必要的 API 密鑰
在部署前，請確保您已準備以下 API 密鑰：

- **BOT_TOKEN**: Telegram Bot Token (從 @BotFather 獲取)
- **GOOGLE_MAPS_API_KEY**: Google Maps API 密鑰 (用於地址搜尋功能)

## 部署步驟

### 步驟 1: 準備代碼庫
1. 將專案推送到您的 GitHub 倉庫
2. 確保所有必要文件都已包含：
   - `main.py` (主要入口文件)
   - `pyproject.toml` (Python 依賴配置)
   - 所有相關的 Python 模組文件

### 步驟 2: 創建 Railway 專案
1. 登入 Railway 控制台
2. 點擊 "New Project"
3. 選擇 "Deploy from GitHub repo"
4. 選擇您的機器人代碼庫

### 步驟 3: 配置環境變數
在 Railway 專案設置中添加以下環境變數：

```
BOT_TOKEN=您的_Telegram_Bot_Token
GOOGLE_MAPS_API_KEY=您的_Google_Maps_API_Key
```

**重要**: 請確保這些變數值正確，否則機器人將無法正常運作。

### 步驟 4: 配置啟動命令
在 Railway 設置中，確保啟動命令設為：
```bash
python main.py
```

### 步驟 5: 部署配置
Railway 會自動檢測 Python 專案並安裝依賴。確保您的 `pyproject.toml` 包含所有必要依賴：

```toml
[project]
name = "north-sea-bot"
version = "1.0.0"
description = "North Sea Financial Management Telegram Bot"
dependencies = [
    "python-telegram-bot",
    "aiohttp",
    "googlemaps",
    "trafilatura",
    "telegram"
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
```

## 資料庫配置

### SQLite 資料庫
機器人使用 SQLite 資料庫 (`north_sea_bot.db`)。Railway 會自動處理文件持久化。

### PostgreSQL (可選)
如果您需要使用 PostgreSQL：
1. 在 Railway 添加 PostgreSQL 服務
2. Railway 會自動設置 `DATABASE_URL` 環境變數
3. 修改 `database.py` 以支援 PostgreSQL 連接

## 監控與日誌

### 查看日誌
- 在 Railway 控制台中查看實時日誌
- 監控機器人的啟動和運行狀態

### 健康檢查
機器人包含以下功能來確保正常運行：
- 自動重新連接機制
- 錯誤處理和日誌記錄
- 定期 Telegram API 請求檢查

## 常見問題排解

### 1. 機器人無法啟動
- 檢查 `BOT_TOKEN` 是否正確設置
- 確認所有依賴都已正確安裝
- 查看 Railway 日誌獲取詳細錯誤信息

### 2. Google Maps 功能不工作
- 驗證 `GOOGLE_MAPS_API_KEY` 是否有效
- 確保 Google Maps API 已啟用地理編碼服務
- 檢查 API 配額是否充足

### 3. 資料庫錯誤
- SQLite 文件權限問題：Railway 應自動處理
- 如使用 PostgreSQL，檢查 `DATABASE_URL` 連接字符串

### 4. 記憶體或性能問題
- Railway 提供不同的資源計劃
- 監控資源使用情況並根據需要升級

## 費用考量

### Railway 定價
- 免費額度：$5 USD/月的使用量
- 適用於小型到中型的機器人使用量
- 超出額度後按使用量計費

### 成本優化建議
- 監控 API 調用頻率
- 優化資料庫查詢
- 使用適當的日誌級別

## 安全最佳實踐

### 1. 環境變數安全
- 絕不在代碼中硬編碼敏感信息
- 使用 Railway 的環境變數功能
- 定期更新 API 密鑰

### 2. 機器人權限
- 僅授予必要的 Telegram 權限
- 實施適當的用戶權限檢查
- 監控異常活動

## 維護與更新

### 自動部署
- 連接 GitHub 倉庫後，推送到主分支會自動觸發重新部署
- 建議使用分支進行測試

### 備份策略
- 定期導出 SQLite 資料庫
- 保存重要配置文件的備份
- 文檔化自定義設置

## 支援與故障排除

### 日誌監控
```bash
# 在 Railway 控制台中查看實時日誌
# 關鍵日誌指標：
- Bot startup messages
- Database connection status
- API request success/failure
- Error messages and stack traces
```

### 性能監控
- 監控記憶體使用量
- 檢查 API 響應時間
- 追蹤用戶活動模式

## 聯絡支援
如果遇到部署問題：
1. 檢查 Railway 官方文檔
2. 查看社群論壇
3. 檢查機器人日誌獲取具體錯誤信息

---

**注意**: 本機器人專為財務管理設計，請確保遵守相關的資料保護法規和安全標準。