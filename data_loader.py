# -*- coding: utf-8 -*-
"""
data_loader.py ── 載入分支 A 的資料集（優先讀 xlsx，找不到則讀 csv）
回傳 list[dict]，每筆含 9 個標準欄位 + scenario。
"""
import csv
import config


def load_dataset():
    """回傳資料集 list[dict]。"""
    # 優先讀 xlsx（分支 A 原始檔）
    if config.DATASET_XLSX.exists():
        try:
            import pandas as pd
            df = pd.read_excel(config.DATASET_XLSX,
                               sheet_name=config.DATASET_SHEET, engine="openpyxl")
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"[data_loader] 讀取 xlsx 失敗（{e}），改用 CSV。")

    # 備援：讀 CSV
    if config.DATASET_CSV.exists():
        with open(config.DATASET_CSV, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    raise FileNotFoundError("找不到資料集，請確認 data/ 內有 xlsx 或 csv。")


if __name__ == "__main__":
    rows = load_dataset()
    print(f"共載入 {len(rows)} 筆")
    print("欄位:", list(rows[0].keys()))
    print("第 1 筆 id:", rows[0]["id"], "| 標籤:", rows[0]["ground_truth_label"])
