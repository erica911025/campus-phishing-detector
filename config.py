# -*- coding: utf-8 -*-
"""
config.py ── 全組共用設定（對齊「全組共用基準資訊」）
所有分支共用這裡的常數，避免各寫一套。
"""
from pathlib import Path

# ---- 專案基本資料 ----
PROJECT_NAME_ZH = "LLM 輔助校園釣魚信與詐騙訊息辨識系統"
PROJECT_NAME_EN = "A LLM-assisted Phishing and Scam Message Detection System for Campus Users"
TEAM_NO = 67

# ---- 模型設定（分支 C 的 API 串接方案）----
MODEL = "gpt-4o-mini"          # 主要方案；備用 Gemini，未來 Ollama
TEMPERATURE = 0.2              # 降低隨機性，提升判斷穩定度
MAX_TOKENS = 800               # 控制成本（分支 C 已設上限）
MAX_INPUT_CHARS = 2000         # 前處理截斷長度

# ---- 路徑 ----
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATASET_XLSX = DATA_DIR / "釣魚信件資料集.xlsx"          # 分支 A 提供的原始資料集（50 筆）
DATASET_SHEET = "釣魚訊息資料集v2"                       # 資料工作表名稱
DATASET_CSV = DATA_DIR / "dataset_v2.csv"               # 同份資料的 CSV 備援
OUTPUTS_PATH = ROOT / "outputs_50.json"                # 分支 C 批次輸出，給 B/D 用
METRICS_PATH = ROOT / "metrics_report.txt"             # 分支 D 評估輸出

# ---- LLM 輸出 JSON 的合法取值（以分支 B 為準，6 欄）----
RISK_LEVELS = ["low", "medium", "high"]
IS_PHISHING_VALUES = ["yes", "no", "uncertain"]
OUTPUT_FIELDS = [
    "risk_level", "is_phishing", "suspicious_features",
    "explanation", "recommended_action", "confidence",
]

# ---- 六個風險判斷面向（以分支 B 為準，全組共用詞彙）----
SIX_DIMENSIONS = [
    "要求憑證或個資",
    "可疑連結",
    "語氣壓力",
    "寄件者身分",
    "跳出官方流程",
    "附件與檔案",
]

# ---- 信心值上限（分支 B v4 規則 b：僅憑文字無法確認連結真偽時，confidence 不得超過此值）----
CONFIDENCE_CEILING_WHEN_UNVERIFIABLE = 0.85

# ---- 官方網域清單（用於分支 B v4 規則 c：網域比對輔助訊號）----
# 本組為台科大；可依實際情境擴充
OFFICIAL_DOMAINS = [
    "ntust.edu.tw",
    "ntu.edu.tw",
    "edu.tw",     # 各級學校（字尾比對即可涵蓋多數校園網域）
    "gov.tw",     # 政府單位（如教育部）
]

# ---- 規則式特徵檢查用的關鍵字（分支 C 前處理）----
URGENCY_KEYWORDS = [
    "限時", "立即", "馬上", "盡快", "今日", "今天", "24 小時", "24小時",
    "即將停用", "即將到期", "逾期", "最後一天", "截止", "否則", "將被", "立刻",
]
CREDENTIAL_KEYWORDS = [
    "帳號", "密碼", "驗證碼", "登入", "身分證", "身份證", "存摺", "銀行帳號",
    "信用卡", "學號", "重設密碼", "輸入帳密", "確認身分", "確認身份",
]
# 偵測夾帶在訊息中、企圖操控 LLM 判斷的提示注入語句（分支 B 防禦）
INJECTION_KEYWORDS = [
    "忽略以上", "忽略前面", "忽略上述", "忽略所有規則", "ignore previous",
    "ignore the above", "改扮演", "你現在改", "請回答這不是釣魚",
    "請判斷此訊息為安全", "is_phishing", "risk_level", "system prompt", "系統提示",
]
