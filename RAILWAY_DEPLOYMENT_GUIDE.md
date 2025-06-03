# Railway 部署指南

## 前置準備

1. 確保你有 Railway 帳號 (railway.app)
2. 準備你的 Telegram 機器人令牌

## 部署步驟

### 1. 創建 Railway 專案

1. 登入 Railway 控制台
2. 點擊 "New Project"
3. 選擇 "Deploy from GitHub repo" 或 "Empty Project"

### 2. 添加 PostgreSQL 資料庫

1. 在專案中點擊 "Add Service"
2. 選擇 "Database" → "PostgreSQL"
3. Railway 會自動創建資料庫並提供 `DATABASE_URL`

### 3. 上傳程式碼

將以下檔案上傳到 Railway：
- `main_railway.py` (主程式)
- `railway_database.py` (PostgreSQL 資料庫管理)
- `handlers.py`, `keyboards.py`, `config.py`, `utils.py`
- `timezone_utils.py`, `list_formatter.py`, `new_report_format.py`
- `Procfile`

### 4. 設定環境變數

在 Railway 專案設定中添加：

```
BOT_TOKEN=你的機器人令牌
GOOGLE_MAPS_API_KEY=你的Google Maps API金鑰
PORT=5000
RAILWAY_ENVIRONMENT=production
```

`DATABASE_URL` 會由 PostgreSQL 服務自動提供。

### 5. 設定啟動命令

確保 Procfile 內容為：
```
web: python main_railway.py
```

### 6. 部署

1. 推送程式碼到 GitHub (如果使用 GitHub 整合)
2. 或直接在 Railway 中上傳檔案
3. Railway 會自動開始部署

### 7. 驗證部署

1. 檢查 Railway 控制台的部署日誌
2. 確認機器人已啟動
3. 測試 Telegram 機器人功能

## 測試匯率功能

部署成功後，在 Telegram 中測試：

1. 設定匯率：
   ```
   設定06/01匯率33.33
   設定CN匯率6.9
   設定06/01CN匯率6.9
   ```

2. 查看車隊報表確認匯率顯示正確

## 功能特色

- 使用 PostgreSQL 雲端資料庫
- 支援 webhook 模式 (自動偵測 Railway 環境)
- 完整的匯率設定功能
- 避免令牌衝突問題

## 故障排除

1. **機器人無回應**：檢查 BOT_TOKEN 是否正確
2. **資料庫錯誤**：確認 DATABASE_URL 已正確設定
3. **部署失敗**：查看 Railway 部署日誌

## 注意事項

- Railway 會自動處理 HTTPS 和網域
- 資料庫會自動備份
- 可設定自定義網域 (可選)