# -*- coding: utf-8 -*-
"""
incident_response.py ── 分支 D：事件應變建議與通報草稿
- INCIDENT_SOP：三級（low/medium/high）對應的處置步驟與通報管道。
- get_incident_advice()：依風險等級回傳結構化建議（供分支 C 的「行動卡」顯示）。
- generate_report_draft()：依分析結果產生可寄給資訊中心 / 165 的通報草稿
  （供分支 C 的「一鍵通報草稿」功能）。
"""

INCIDENT_SOP = {
    "low": {
        "title": "低風險：留意即可",
        "color": "green",
        "steps": [
            "可自行確認訊息來源是否為官方單位。",
            "若含連結，建議不直接點擊，改從學校官網或系統登入確認。",
            "若仍有疑慮，可截圖轉寄至資訊中心或相關單位確認。",
            "無需進行帳號保護或緊急通報等額外處置。",
        ],
        "channels": [],
    },
    "medium": {
        "title": "中風險：先查證再行動",
        "color": "orange",
        "steps": [
            "暫停點擊連結或下載附件，先從官方管道確認訊息真實性。",
            "比對寄件者信箱網域是否與聲稱單位相符（例如 @ntu.edu.tw 而非 @gmail.com）。",
            "若要求填個資或登入，請直接從官方網站登入，不要用訊息中的連結。",
            "主動向系辦、資訊中心或相關單位查詢確認，勿僅依賴訊息本身判斷。",
            "保留原始訊息截圖，作為後續確認或通報依據。",
        ],
        "channels": ["系辦 / 學務處", "學校資訊中心"],
    },
    "high": {
        "title": "高風險：立即停止互動並通報",
        "color": "red",
        "steps": [
            "立即停止與該訊息互動：不回覆、不點擊、不下載附件。",
            "若涉及帳號或密碼，立即更改相關帳號密碼並啟用雙因素驗證。",
            "將原始訊息（含寄件者、連結、時間）回報至學校資訊中心或安全單位。",
            "告知周遭同學注意相同類型訊息，避免擴散受害。",
            "若已點擊連結但未輸入資料，建議更改密碼並觀察帳號近期活動。",
            "若已提供個資或帳密，立即聯繫資訊中心，並視情況處理個資外洩後續。",
        ],
        "channels": ["學校資訊中心 / 校安中心", "內政部 165 反詐騙專線", "TWCERT/CC（視情況）"],
    },
}


def get_incident_advice(risk_level: str) -> dict:
    """回傳該風險等級的應變建議（含標題、步驟、通報管道）。"""
    return INCIDENT_SOP.get(risk_level, INCIDENT_SOP["medium"])


def generate_report_draft(message: str, analysis: dict) -> str:
    """依分析結果產生通報草稿（純文字，使用者可一鍵複製寄出）。"""
    risk = analysis.get("risk_level", "medium")
    sop = get_incident_advice(risk)
    feats = analysis.get("suspicious_features", []) or ["（未列出明顯特徵）"]
    feats_text = "\n".join(f"  - {f}" for f in feats)
    flags = analysis.get("_feature_flags", {})
    urls = flags.get("urls", [])
    urls_text = "、".join(urls) if urls else "（無）"
    channels = "、".join(sop["channels"]) if sop["channels"] else "（低風險，暫無需通報）"

    snippet = (message or "").strip().replace("\n", " ")
    if len(snippet) > 200:
        snippet = snippet[:200] + " …（後略）"

    return (
        "主旨：可疑釣魚/詐騙訊息通報\n"
        "──────────────────────────────\n"
        "您好，我收到一則疑似釣魚/詐騙的訊息，使用校園釣魚訊息辨識系統初步分析後，"
        f"判定為「{risk.upper()}（{sop['title']}）」，特此通報協助查證。\n\n"
        f"【系統判定風險等級】{risk.upper()}\n"
        f"【可疑特徵】\n{feats_text}\n"
        f"【訊息內含連結】{urls_text}\n\n"
        "【原始訊息內容】\n"
        f"{snippet}\n\n"
        f"【建議通報管道】{channels}\n"
        "──────────────────────────────\n"
        "備註：本判定由 LLM 輔助系統產生，僅供參考，最終請由資訊中心協助確認。\n"
        "通報人：________　學號：________　聯絡方式：________"
    )


if __name__ == "__main__":
    from llm_analyzer import analyze
    msg = "【計算機中心】帳號異常即將停用，請點 http://campus-verify-tw.site/login 驗證。"
    a = analyze(msg, use_mock=True)
    print(generate_report_draft(msg, a))
