# -*- coding: utf-8 -*-
"""
llm_analyzer.py ── 分支 C（串接）＋ 分支 B（提示）
- analyze()：核心入口。有 OPENAI_API_KEY 就呼叫 GPT-4o-mini（JSON mode）；
  沒有金鑰則自動切換到「離線啟發式模式」，讓系統仍可端到端展示與測試。
- 內含 JSON 解析失敗重試、輸出欄位驗證與正規化、v4 信心值上限的事後保險。
"""
import json
import os

import config
import prompts
import preprocessing as pre

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _get_api_key():
    """取得 OpenAI 金鑰：本機讀環境變數（.env），雲端讀 Streamlit secrets。"""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    # Streamlit Community Cloud：從 st.secrets 取（本機未裝 streamlit 時略過）
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            key = st.secrets["OPENAI_API_KEY"]
            os.environ["OPENAI_API_KEY"] = key   # 讓 openai SDK 也讀得到
            return key
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# 輸出正規化：確保 6 欄齊全、取值合法、confidence 落在 0~1
# ---------------------------------------------------------------------------
def normalize_output(obj: dict, flags: dict) -> dict:
    out = {
        "risk_level": "uncertain",
        "is_phishing": "uncertain",
        "suspicious_features": [],
        "explanation": "",
        "recommended_action": "",
        "confidence": 0.5,
    }
    if isinstance(obj, dict):
        out.update({k: obj.get(k, out[k]) for k in out})

    if out["risk_level"] not in config.RISK_LEVELS:
        out["risk_level"] = "medium"
    if out["is_phishing"] not in config.IS_PHISHING_VALUES:
        out["is_phishing"] = "uncertain"
    if not isinstance(out["suspicious_features"], list):
        out["suspicious_features"] = [str(out["suspicious_features"])]
    try:
        out["confidence"] = max(0.0, min(1.0, float(out["confidence"])))
    except (TypeError, ValueError):
        out["confidence"] = 0.5

    # v4 規則 7 的事後保險：有外部連結但無法驗證真偽時，信心值不超過上限
    if flags.get("urls") and flags.get("domain_mismatch"):
        out["confidence"] = min(out["confidence"],
                                config.CONFIDENCE_CEILING_WHEN_UNVERIFIABLE)

    # 注入企圖一定列為可疑特徵（防止模型漏列）
    if flags.get("injection_hits"):
        note = "訊息中夾帶試圖操控判斷的指令（提示注入），本身即為高度可疑訊號"
        if note not in out["suspicious_features"]:
            out["suspicious_features"].append(note)
        out["risk_level"] = "high"
        if out["is_phishing"] == "no":
            out["is_phishing"] = "yes"
    return out


def _parse_json(text: str):
    """容錯解析：去除可能的 Markdown 圍欄後解析。"""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


# ---------------------------------------------------------------------------
# 線上模式：呼叫 OpenAI
# ---------------------------------------------------------------------------
def _analyze_openai(message: str, flags: dict, retries: int = 2) -> dict:
    from openai import OpenAI
    client = OpenAI()
    messages = prompts.build_messages(message, pre.feature_hint_text(flags))
    last_err = None
    for _ in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                response_format={"type": "json_object"},   # 強制 JSON 輸出
            )
            return normalize_output(_parse_json(resp.choices[0].message.content), flags)
        except Exception as e:           # JSON 解析失敗或 API 問題 → 重試
            last_err = e
    raise RuntimeError(f"OpenAI 呼叫/解析多次失敗：{last_err}")


# ---------------------------------------------------------------------------
# 離線模式：啟發式判斷（無 API 金鑰時使用，邏輯對齊 v4 規則）
# ---------------------------------------------------------------------------
def _analyze_heuristic(message: str, flags: dict) -> dict:
    feats, score = [], 0
    if flags["asks_for_credentials"]:
        feats.append("要求提供帳號、密碼或個人敏感資料"); score += 2
    if flags["domain_mismatch"]:
        feats.append("連結網域與官方網域不符"); score += 2
    elif flags["urls"]:
        feats.append("訊息含外部連結")
    if pre.has_attachment(message):
        feats.append("要求下載或開啟附件檔"); score += 1
    if flags["urgency_level"] == "高":
        feats.append("使用急迫、限時或威脅語氣"); score += 1

    # v4 規則 6：語氣急但連結與身分皆合理 → 下修
    if flags["urgency_level"] == "高" and not flags["domain_mismatch"] \
            and not flags["asks_for_credentials"]:
        score = max(0, score - 1)

    if score >= 3:
        risk, is_ph, conf = "high", "yes", 0.8
    elif score >= 1:
        risk, is_ph, conf = "medium", "uncertain", 0.6
    else:
        risk, is_ph, conf = "low", "no", 0.8

    if risk == "high":
        action = "不要點擊連結、不要輸入帳密或提供個資。請改從官方網站或官方電話查證，並向學校資訊中心回報這則訊息。"
        expl = "這則訊息同時出現索取個資、可疑連結或限時施壓等強指標，符合常見釣魚/詐騙手法。"
    elif risk == "medium":
        action = "先暫停點擊連結或填表，改用官方管道（系辦、資訊中心、官網）確認訊息真實性後再決定。"
        expl = "這則訊息出現少數可疑特徵，但尚無法只憑文字確認真偽，建議先向官方查證。"
    else:
        action = "目前看起來沒有明顯危險特徵，無需特別處理；若仍有疑慮，可至官方網站確認。"
        expl = "訊息未要求帳密或個資、無可疑連結、語氣正常，與一般校園通知相符。"

    return normalize_output({
        "risk_level": risk, "is_phishing": is_ph,
        "suspicious_features": feats, "explanation": expl,
        "recommended_action": action, "confidence": conf,
    }, flags)


# ---------------------------------------------------------------------------
# 對外入口
# ---------------------------------------------------------------------------
def has_api_key() -> bool:
    return bool(_get_api_key())


def analyze(message: str, use_mock: bool = None) -> dict:
    """分析單一訊息，回傳 6 欄結構化結果。
    use_mock=None 時自動判斷（有金鑰用線上、無金鑰用離線）。
    """
    cleaned = pre.clean_text(message)
    flags = pre.build_feature_flags(cleaned)
    if use_mock is None:
        use_mock = not has_api_key()
    if use_mock:
        result = _analyze_heuristic(cleaned, flags)
    else:
        try:
            result = _analyze_openai(cleaned, flags)
        except Exception as e:
            print(f"[llm_analyzer] 線上模式失敗，改用離線啟發式：{e}")
            result = _analyze_heuristic(cleaned, flags)
    result["_feature_flags"] = flags        # 附帶旗標供介面顯示與除錯
    return result


if __name__ == "__main__":
    msg = ("【計算機中心緊急通知】您的校園帳號偵測到異常登入即將停用，"
           "請於今日23:59前點擊 http://campus-verify-tw.site/login 重新驗證身分。")
    print(json.dumps(analyze(msg, use_mock=True), ensure_ascii=False, indent=2))
