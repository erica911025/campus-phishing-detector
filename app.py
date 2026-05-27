# -*- coding: utf-8 -*-
"""
app.py ── 分支 C：使用者介面（Streamlit）
七個區塊：標題、輸入、分析進度、風險等級、可疑特徵、防範建議(行動卡)、JSON 原始輸出。
另含應用面亮點：一鍵「通報草稿」、批次測試頁。

執行：streamlit run app.py
"""
import json

import streamlit as st

import config
from llm_analyzer import analyze, has_api_key
from incident_response import get_incident_advice, generate_report_draft

st.set_page_config(page_title="校園釣魚訊息辨識系統", page_icon="🛡️", layout="centered")

RISK_META = {
    "high":   {"label": "高風險", "color": "#B42318", "emoji": "🔴"},
    "medium": {"label": "中風險", "color": "#B5610B", "emoji": "🟠"},
    "low":    {"label": "低風險", "color": "#1E7A46", "emoji": "🟢"},
}
SOP_COLOR = {"red": "#B42318", "orange": "#B5610B", "green": "#1E7A46"}


# ===== 區塊一：標題 =====
st.title("🛡️ 校園釣魚訊息辨識系統")
st.caption(f"{config.PROJECT_NAME_ZH}　|　組別 {config.TEAM_NO}　|　LLM 輔助・僅供參考")

with st.sidebar:
    st.header("關於本系統")
    st.write("貼上你收到的可疑訊息，系統會用 LLM 分析風險、列出可疑特徵，"
             "並給你白話、可照做的處理建議。")
    mode = "🟢 線上（GPT-4o-mini）" if has_api_key() else "🟡 離線啟發式（未設定 API 金鑰）"
    st.info(f"目前模式：{mode}")
    st.divider()
    page = st.radio("功能", ["單筆分析", "批次測試（展示用）"])
    st.divider()
    st.caption("⚠️ 系統判斷僅供參考，最終處置請向學校資訊中心等專責單位確認。")


def render_result(message: str, result: dict):
    meta = RISK_META.get(result["risk_level"], RISK_META["medium"])
    conf_pct = int(round(result["confidence"] * 100))

    # ===== 區塊四：風險等級 =====
    st.markdown(
        f"""<div style="background:{meta['color']}15;border-left:8px solid {meta['color']};
        padding:14px 18px;border-radius:8px;margin:8px 0;">
        <span style="font-size:24px;font-weight:700;color:{meta['color']};">
        {meta['emoji']} {meta['label']}</span>
        <span style="font-size:15px;color:#555;margin-left:12px;">信心度 {conf_pct}%　|　
        is_phishing：{result['is_phishing']}</span></div>""",
        unsafe_allow_html=True,
    )

    # 判斷說明
    st.markdown(f"**為什麼這樣判斷：** {result['explanation']}")

    # ===== 區塊五：可疑特徵 =====
    st.subheader("🔍 可疑特徵")
    if result["suspicious_features"]:
        for feat in result["suspicious_features"]:
            st.markdown(f"- {feat}")
    else:
        st.markdown("- （未發現明顯可疑特徵）")

    # ===== 區塊六：防範建議（行動卡，對接分支 D 應變 SOP）=====
    st.subheader("✅ 下一步該怎麼做")
    st.success(result["recommended_action"])

    sop = get_incident_advice(result["risk_level"])
    sop_color = SOP_COLOR.get(sop["color"], "#555")
    with st.container(border=True):
        st.markdown(f"**📋 {sop['title']}**")
        for s in sop["steps"]:
            st.markdown(f"- {s}")
        if sop["channels"]:
            st.markdown("**建議通報管道：** " + "、".join(sop["channels"]))

    # 應用面亮點：一鍵通報草稿
    st.subheader("📨 一鍵產生通報草稿")
    st.caption("可直接複製寄給學校資訊中心或轉知 165 反詐騙專線。")
    draft = generate_report_draft(message, result)
    st.code(draft, language="text")
    st.download_button("下載通報草稿 (.txt)", draft,
                       file_name="phishing_report_draft.txt", mime="text/plain")

    # ===== 區塊七：JSON 原始輸出 =====
    with st.expander("🧩 查看完整 JSON 原始輸出（除錯/評估用）"):
        show = {k: result[k] for k in config.OUTPUT_FIELDS}
        st.json(show)
        st.caption("規則式特徵旗標：")
        st.json(result.get("_feature_flags", {}))


# ===================== 單筆分析 =====================
if page == "單筆分析":
    # ===== 區塊二：輸入 =====
    msg = st.text_area("請貼上你收到的可疑電子郵件、LINE 訊息或簡訊內容：",
                       height=180, placeholder="例如：【計算機中心】您的帳號即將停用，請點連結驗證…")
    if st.button("開始分析", type="primary"):
        if not msg.strip():
            st.warning("請先貼上訊息內容。")
        else:
            # ===== 區塊三：分析進度 =====
            with st.spinner("分析中，請稍候…"):
                result = analyze(msg)
            render_result(msg, result)

# ===================== 批次測試 =====================
else:
    st.subheader("批次測試（讀取分支 A 的 50 筆資料集）")
    st.caption("此頁用離線啟發式模式快速展示整批結果，不消耗 API 費用。")
    if st.button("執行批次分析", type="primary"):
        from data_loader import load_dataset
        rows = load_dataset()
        prog = st.progress(0.0)
        table = []
        for i, r in enumerate(rows, 1):
            a = analyze(str(r.get("message_content", "")), use_mock=True)
            ok = "✅" if (a["risk_level"] in ("high", "medium")) == \
                 (str(r.get("ground_truth_label")) == "高風險") else "❌"
            table.append({"id": r.get("id"), "情境": r.get("scenario"),
                          "標準答案": r.get("ground_truth_label"),
                          "系統判定": a["risk_level"], "is_phishing": a["is_phishing"],
                          "信心": a["confidence"], "對照": ok})
            prog.progress(i / len(rows))
        st.dataframe(table, use_container_width=True)
        correct = sum(1 for t in table if t["對照"] == "✅")
        st.metric("離線啟發式整體正確率", f"{correct}/{len(table)} = {correct/len(table):.0%}")
        st.caption("正式指標請以線上 GPT-4o-mini 跑 batch_run.py 後，用 evaluate.py 計算。")
