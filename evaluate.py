# -*- coding: utf-8 -*-
"""
evaluate.py ── 分支 D：評估方法實作
讀入 outputs_50.json（分支 C 產出）與資料集 ground truth，計算：
  1. 整體混淆矩陣與 Accuracy / Precision / Recall / F1
  2. 四情境別的 Precision / Recall
  3. Risk Level 與二元標籤的一致率
  4. 信心值校準（依 confidence 分箱比較實際正確率）

三級 ↔ 二元對照規則（共用基準，由分支 D 定義）：
  以 risk_level 為主：high/medium → 高風險側（正類），low → 低風險側（負類）。
  另以 is_phishing 做輔助對照（yes/uncertain → 正類，no → 負類）。

用法：
    python evaluate.py
"""
import json

import config
from data_loader import load_dataset


def risk_to_binary(risk_level: str) -> str:
    """high/medium → 高風險；low → 低風險（共用基準對照規則）。"""
    return "高風險" if risk_level in ("high", "medium") else "低風險"


def is_phishing_to_binary(v: str) -> str:
    return "低風險" if v == "no" else "高風險"   # yes/uncertain 皆視為正類（偏保守）


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def confusion(pairs):
    """pairs: list[(y_true, y_pred)]，正類為「高風險」。回傳 tp,fp,fn,tn。"""
    tp = sum(1 for t, p in pairs if t == "高風險" and p == "高風險")
    fp = sum(1 for t, p in pairs if t == "低風險" and p == "高風險")
    fn = sum(1 for t, p in pairs if t == "高風險" and p == "低風險")
    tn = sum(1 for t, p in pairs if t == "低風險" and p == "低風險")
    return tp, fp, fn, tn


def main():
    if not config.OUTPUTS_PATH.exists():
        raise SystemExit("找不到 outputs_50.json，請先執行 batch_run.py。")

    outputs = {str(o["id"]): o for o in json.load(open(config.OUTPUTS_PATH, encoding="utf-8"))}
    rows = load_dataset()

    lines = []
    def out(s=""):
        print(s); lines.append(s)

    out("=" * 60)
    out(f"評估報告 ── {config.PROJECT_NAME_ZH}（組別 {config.TEAM_NO}）")
    out("=" * 60)

    # ---- 主指標：以 risk_level 對照 ----
    pairs, conf_records, level_match = [], [], 0
    n = 0
    for r in rows:
        o = outputs.get(str(r["id"]))
        if not o:
            continue
        n += 1
        y_true = str(r["ground_truth_label"])
        y_pred = risk_to_binary(o["risk_level"])
        pairs.append((y_true, y_pred))
        conf_records.append((float(o.get("confidence", 0)), y_true == y_pred))
        if y_true == y_pred:
            level_match += 1

    tp, fp, fn, tn = confusion(pairs)
    acc = (tp + tn) / n if n else 0
    p, r, f1 = prf(tp, fp, fn)

    out(f"\n樣本數：{n}")
    out("\n【混淆矩陣】（正類＝高風險，依 risk_level 對照）")
    out(f"                預測高風險   預測低風險")
    out(f"  實際高風險      TP={tp:<6}    FN={fn}")
    out(f"  實際低風險      FP={fp:<6}    TN={tn}")
    out("\n【整體分類指標】")
    out(f"  Accuracy  = {acc:.3f}")
    out(f"  Precision = {p:.3f}   （判為釣魚者中實際為釣魚的比例）")
    out(f"  Recall    = {r:.3f}   （實際釣魚中被成功抓出的比例）")
    out(f"  F1-score  = {f1:.3f}")
    out(f"  Risk Level 一致率（high/med/low 對二元）= {level_match}/{n} = {level_match/n:.3f}")

    # ---- 情境別 ----
    out("\n【四情境別 Precision / Recall】")
    by_scn = {}
    for r in rows:
        o = outputs.get(str(r["id"]))
        if not o:
            continue
        scn = str(r["scenario"])
        by_scn.setdefault(scn, []).append((str(r["ground_truth_label"]),
                                           risk_to_binary(o["risk_level"])))
    for scn in sorted(by_scn):
        t, fpp, fnn, _ = confusion(by_scn[scn])
        pp, rr, ff = prf(t, fpp, fnn)
        out(f"  {scn}：P={pp:.2f}  R={rr:.2f}  F1={ff:.2f}  (n={len(by_scn[scn])})")

    # ---- 信心值校準 ----
    out("\n【信心值校準】（各信心區間的實際正確率）")
    bins = [("conf < 0.6", lambda c: c < 0.6),
            ("0.6 ≤ conf < 0.8", lambda c: 0.6 <= c < 0.8),
            ("conf ≥ 0.8", lambda c: c >= 0.8)]
    for label, cond in bins:
        sub = [ok for c, ok in conf_records if cond(c)]
        if sub:
            out(f"  {label:<18} 筆數={len(sub):<3} 實際正確率={sum(sub)/len(sub):.3f}")
        else:
            out(f"  {label:<18} 筆數=0")

    # ---- is_phishing 輔助對照 ----
    pairs2 = []
    uncertain = 0
    for r in rows:
        o = outputs.get(str(r["id"]))
        if not o:
            continue
        if o["is_phishing"] == "uncertain":
            uncertain += 1
        pairs2.append((str(r["ground_truth_label"]), is_phishing_to_binary(o["is_phishing"])))
    tp2, fp2, fn2, tn2 = confusion(pairs2)
    p2, r2, f2 = prf(tp2, fp2, fn2)
    out("\n【輔助：以 is_phishing 對照】（yes/uncertain 視為正類）")
    out(f"  Precision={p2:.3f}  Recall={r2:.3f}  F1={f2:.3f}  其中 uncertain {uncertain} 筆")

    out("\n" + "=" * 60)
    with open(config.METRICS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n已輸出評估報告：{config.METRICS_PATH}")


if __name__ == "__main__":
    main()
