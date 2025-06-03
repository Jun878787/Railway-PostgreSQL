# 北金管家 North™Sea ᴍ8ᴘ - Telegram 財務管理機器人

一個功能完整的 Telegram 財務管理機器人，專為多幣種交易追蹤和財務報表管理而設計。

## 功能特色

### 🏦 多幣種交易管理
- **台幣 (TWD)** 和 **人民幣 (CNY)** 雙幣種支援
- 快速記帳格式：`TW+100`、`CN-50`
- 自動匯率轉換和 USDT 計算
- 交易類型自動識別（收入/支出）

### 📊 智能報表系統
- **個人報表**：查看個人財務狀況
- **群組報表**：群組內財務統計
- **車隊報表**：跨群組綜合財務分析
- **歷史報表**：按月份查詢歷史數據
- 即時匯率顯示和 USDT 轉換

### 💰 基金管理
- **公桶基金**：群組共同資金管理
- **私人基金**：個人資金池管理
- 基金餘額查詢和異動記錄
- 支援多幣種基金操作

### 🗺️ 地址智能搜尋
- Google Maps API 整合
- 地標位置自動識別
- 縣市區域資訊提取
- 客戶資訊格式化處理

### 🔐 權限管理系統
- 管理員權限控制
- 群組管理員自動識別
- 操作權限分級管理
- 安全的資料存取控制

## 技術架構

### 核心技術
- **Python 3.11+** - 主要開發語言
- **python-telegram-bot** - Telegram Bot API 框架
- **SQLite** - 本地資料庫存儲
- **Google Maps API** - 地理位置服務
- **aiohttp** - 異步 HTTP 請求處理

### 資料庫設計
- 用戶資訊管理
- 交易記錄存儲
- 群組資料隔離
- 匯率歷史記錄
- 基金異動追蹤

### 部署架構
- **Polling 模式**：穩定的長輪詢連接
- **錯誤恢復**：自動重啟和錯誤處理
- **日誌系統**：完整的運行狀態記錄
- **環境配置**：靈活的配置管理

## 當前環境配置狀態

### ✅ 環境變數配置
```bash
BOT_TOKEN=已配置且正常運作
GOOGLE_MAPS_API_KEY=已配置且正常運作
GROUP_ID=預設群組已設定
```

### 🔧 系統狀態
- **機器人狀態**: 🟢 正常運行中（Polling 模式）
- **資料庫**: 🟢 SQLite 已初始化
- **Google Maps**: 🟢 API 客戶端已就緒
- **Telegram API**: 🟢 連接正常，定期更新中

### 📋 功能模組狀態
- **交易處理器**: ✅ 已載入
- **報表生成器**: ✅ 已載入  
- **鍵盤布局**: ✅ 已載入
- **地址格式化**: ✅ 已載入
- **權限管理**: ✅ 已載入

## 快速開始

### 本地運行
```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設置環境變數
export BOT_TOKEN="your_telegram_bot_token"
export GOOGLE_MAPS_API_KEY="your_google_maps_api_key"

# 3. 啟動機器人
python main.py
```

### Railway 部署
1. 將代碼推送到 GitHub
2. 在 Railway 創建新專案
3. 連接 GitHub 倉庫
4. 設置環境變數：
   - `BOT_TOKEN`
   - `GOOGLE_MAPS_API_KEY`
5. 自動部署完成

詳細部署指南請參考：[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

## 使用指南

### 基本交易記錄
```
TW+1000      # 台幣收入 1000 元
CN-500       # 人民幣支出 500 元
TW+1500 12/25 # 指定日期的台幣收入
```

### 基金操作
```
公桶+5000    # 公共基金增加 5000
私人-2000    # 私人基金減少 2000
```

### 報表查詢
- 使用內建鍵盤選擇報表類型
- 支援當月報表和歷史報表查詢
- 自動計算匯率和 USDT 轉換

### 管理功能
- `/restart` - 重啟機器人（管理員）
- 清空報表功能
- 匯率設定功能

## 檔案結構

```
├── main.py              # 主程式入口
├── config.py            # 配置設定
├── handlers.py          # 訊息處理器
├── database.py          # 資料庫管理
├── keyboards.py         # 鍵盤布局
├── utils.py             # 工具函數
├── list_formatter.py    # 列表格式化
├── bot.py              # 機器人創建
├── pyproject.toml      # 依賴配置
├── railway.toml        # Railway 部署配置
└── README.md           # 專案文檔
```

## API 需求

### Telegram Bot API
1. 前往 [@BotFather](https://t.me/botfather)
2. 創建新機器人：`/newbot`
3. 獲取 Bot Token
4. 設置為環境變數 `BOT_TOKEN`

### Google Maps API
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 啟用 Maps JavaScript API
3. 創建 API 密鑰
4. 設置為環境變數 `GOOGLE_MAPS_API_KEY`

## 安全考量

- 所有敏感資訊通過環境變數管理
- 群組資料完全隔離
- 管理員權限嚴格控制
- 交易記錄加密存儲
- API 請求頻率限制

## 支援與維護

### 日誌監控
機器人提供完整的日誌記錄：
- HTTP 請求狀態
- 資料庫操作記錄
- 錯誤追蹤和診斷
- 用戶操作審計

### 性能優化
- 資料庫查詢優化
- 記憶體使用監控
- API 調用頻率控制
- 自動垃圾回收

### 故障排除
常見問題解決方案：
1. 檢查環境變數設置
2. 驗證 API 密鑰有效性
3. 查看日誌錯誤信息
4. 確認網路連接狀態

## 版本資訊

**當前版本**: v1.0.0
**最後更新**: 2025-06-02
**Python 版本**: 3.11+
**相容性**: Railway, Heroku, VPS

## 授權

本專案為私有專案，僅供授權用戶使用。

---

**注意**: 本機器人處理財務敏感資料，請確保在安全環境中運行，並定期備份重要資料。