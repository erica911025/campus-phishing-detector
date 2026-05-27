# -*- coding: utf-8 -*-
"""
batch_run.py ── 分支 C：批次測試模式
讀入分支 A 的資料集，對每筆呼叫分析，輸出 outputs_50.json（id + 6 欄），
作為分支 B 全量觀察與分支 D 指標計算的資料來源。

用法：
    python batch_run.py            # 自動判斷線上/離線
    python batch_run.py --mock     # 強制離線啟發式（不花 API 費用）
"""
import json
import sys
import time

import config
from data_loader import load_dataset
from llm_analyzer import analyze


def main():
    use_mock = "--mock" in sys.argv
    rows = load_dataset()
    print(f"載入 {len(rows)} 筆，模式：{'離線啟發式' if use_mock else '自動（有金鑰則線上）'}")

    results = []
    t0 = time.time()
    for i, r in enumerate(rows, 1):
        msg = str(r.get("message_content", ""))
        a = analyze(msg, use_mock=True if use_mock else None)
        results.append({
            "id": r.get("id"),
            "scenario": r.get("scenario"),
            "message_type": r.get("message_type"),
            "ground_truth_label": r.get("ground_truth_label"),
            "risk_level": a["risk_level"],
            "is_phishing": a["is_phishing"],
            "suspicious_features": a["suspicious_features"],
            "explanation": a["explanation"],
            "recommended_action": a["recommended_action"],
            "confidence": a["confidence"],
        })
        print(f"  [{i:>2}/{len(rows)}] id={r.get('id')} → {a['risk_level']}/{a['is_phishing']} (conf={a['confidence']})")

    with open(config.OUTPUTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n完成，耗時 {time.time()-t0:.1f}s，已輸出：{config.OUTPUTS_PATH}")


if __name__ == "__main__":
    main()
