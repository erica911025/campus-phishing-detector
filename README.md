# 校園釣魚訊息辨識系統（組別 67）

LLM 輔助校園釣魚信與詐騙訊息辨識系統
*A LLM-assisted Phishing and Scam Message Detection System for Campus Users*

使用者貼上可疑訊息，系統用大型語言模型分析風險等級、列出可疑特徵，並給出白話、可照做的處理建議與一鍵通報草稿。本系統定位為**輔助判斷工具**，輸出僅供參考，最終處置應由使用者或學校資訊中心確認。

---

## 檔案結構與分工對應

| 檔案 | 對應分支 | 說明 |
|---|---|---|
| `config.py` | 全組共用 | 模型、常數、六面向、官方網域、關鍵字等共用設定 |
| `data/釣魚信件資料集.xlsx`、`data/dataset_v2.csv` | A 吳宛蓁 | 50 筆資料集（32 高 / 18 低，四情境） |
| `data_loader.py` | A / 共用 | 載入資料集（xlsx 優先，csv 備援） |
| `prompts.py` | B 張芳瑜 | v4 系統 Prompt（v3＋三條新規則）與 few-shot |
| `preprocessing.py` | C 楊云綺 | 文字清洗、URL/附件偵測、關鍵字旗標、網域比對 |
| `llm_analyzer.py` | C＋B | 呼叫 GPT-4o-mini（JSON mode）／離線啟發式備援、解析重試 |
| `incident_response.py` | D 譚婕伶 | 三級應變 SOP 與通報草稿產生器 |
| `app.py` | B 張芳瑜 | Streamlit 介面（七區塊＋行動卡＋通報草稿＋批次頁） |
| `batch_run.py` | C 楊云綺 | 批次跑 50 筆 → `outputs_50.json`（給 B/D 用） |
| `evaluate.py` | D 譚婕伶 | 混淆矩陣、Accuracy/Precision/Recall/F1、情境別、信心值校準 |

資料流：`資料集 → preprocessing → prompts → llm_analyzer → (app 顯示 / batch 輸出) → evaluate`

---

## 安裝與執行

```bash
# 1. 安裝套件
pip install -r requirements.txt

# 2.（可選）設定 API 金鑰啟用線上模式；不設定則用離線啟發式
cp .env.example .env        # 編輯 .env 填入 OPENAI_API_KEY

# 3. 啟動介面
streamlit run app.py

# 4. 批次跑 50 筆，產生 outputs_50.json（--mock 為離線、不花費用）
python batch_run.py            # 線上（需金鑰）
python batch_run.py --mock     # 離線啟發式

# 5. 計算評估指標，產生 metrics_report.txt
python evaluate.py

---

## 兩種執行模式

- **線上模式**：設定 `OPENAI_API_KEY` 後呼叫 GPT-4o-mini（JSON mode），為正式評估使用。
- **離線啟發式模式**：未設金鑰時自動啟用，用規則式特徵產生合理判斷，讓系統可立即端到端展示與測試，**不消耗 API 費用**。正式指標請以線上模式跑 `batch_run.py` 後再用 `evaluate.py` 計算。

---

## 與報告章節對應（Week 16 整合）

- 分支 A → 主題、應用情境與資料設計（資料集 v2）
- 分支 B → Prompt Engineering 與 LLM 判斷流程（`prompts.py` 即 v4 定稿）
- 分支 C → 系統原型與介面實作（`app.py` + 部署連結 + `batch_run.py`）
- 分支 D → 評估結果、安全限制與事件應變（`evaluate.py` 輸出 + `incident_response.py`）
