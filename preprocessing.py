# -*- coding: utf-8 -*-
"""
preprocessing.py ── 分支 C：文字前處理與規則式特徵檢查
產生供 LLM 參考的「特徵旗標」（僅輔助，不直接決定結論）。
"""
import re
import config

URL_RE = re.compile(r"https?://[^\s）)」』\]】，,；;]+", re.IGNORECASE)
# 附件樣式：[惡意附件：xxx.doc] 或常見可疑副檔名
ATTACH_FILE_RE = re.compile(r"\.(docx?|pptm?|xlsm?|exe|zip|rar|js|scr|bat)\b", re.IGNORECASE)
ATTACH_WORD_RE = re.compile(r"附件|夾帶|下載檔案|附上.*檔")


def clean_text(text: str) -> str:
    """去除多餘空白並截斷過長輸入。"""
    text = (text or "").strip()
    text = re.sub(r"[ \t\u3000]+", " ", text)        # 合併空白（含全形空白）
    text = re.sub(r"\n{3,}", "\n\n", text)            # 壓縮過多換行
    if len(text) > config.MAX_INPUT_CHARS:
        text = text[: config.MAX_INPUT_CHARS] + " …（內容過長已截斷）"
    return text


def extract_urls(text: str):
    return URL_RE.findall(text or "")


def _registrable_domain(url: str) -> str:
    """從 URL 取出網域（host），去掉路徑與埠。"""
    host = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    host = host.split("/")[0].split(":")[0].lower()
    return host


def is_official_domain(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in config.OFFICIAL_DOMAINS)


def check_domain_mismatch(urls):
    """只要有任一連結網域不屬於官方網域，視為 domain_mismatch=True。"""
    for u in urls:
        if not is_official_domain(_registrable_domain(u)):
            return True
    return False


def has_attachment(text: str) -> bool:
    return bool(ATTACH_FILE_RE.search(text or "") or ATTACH_WORD_RE.search(text or ""))


def _hit_keywords(text: str, keywords):
    return [k for k in keywords if k in (text or "")]


def detect_injection(text: str):
    """偵測夾帶在訊息中、企圖操控 LLM 判斷的提示注入語句。"""
    return [k for k in config.INJECTION_KEYWORDS if k.lower() in (text or "").lower()]


def build_feature_flags(text: str) -> dict:
    """產生規則式特徵旗標（dict）。"""
    urls = extract_urls(text)
    urgency_hits = _hit_keywords(text, config.URGENCY_KEYWORDS)
    cred_hits = _hit_keywords(text, config.CREDENTIAL_KEYWORDS)
    injection_hits = detect_injection(text)

    if len(urgency_hits) >= 2:
        urgency_level = "高"
    elif len(urgency_hits) == 1:
        urgency_level = "中"
    else:
        urgency_level = "低"

    return {
        "has_link_or_attachment": bool(urls) or has_attachment(text),
        "urls": urls,
        "asks_for_credentials": len(cred_hits) > 0,
        "credential_hits": cred_hits,
        "urgency_level": urgency_level,
        "urgency_hits": urgency_hits,
        "domain_mismatch": check_domain_mismatch(urls),
        "injection_hits": injection_hits,
    }


def feature_hint_text(flags: dict) -> str:
    """把旗標整理成一行字串，附在 prompt 裡給 LLM 當輔助線索。"""
    return (
        f"has_link={str(flags['has_link_or_attachment']).lower()}, "
        f"asks_for_credentials={str(flags['asks_for_credentials']).lower()}, "
        f"urgency={flags['urgency_level']}, "
        f"domain_mismatch={str(flags['domain_mismatch']).lower()}"
    )


if __name__ == "__main__":
    demo = ("【計算機中心緊急通知】您的校園帳號因多次異常登入即將停用，"
            "請於今日23:59前點擊 http://campus-verify-tw.site/login 重新驗證身分。")
    f = build_feature_flags(clean_text(demo))
    print(f)
    print(feature_hint_text(f))
