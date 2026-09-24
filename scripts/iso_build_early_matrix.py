# -*- coding: utf-8 -*-
"""
从 historical/ 早期官方 World Sugar Balance PDF 提取 2015/16~2023/24 各市场年 surplus/deficit
按发布期次(月/年)排成 vintage 修订矩阵, 并入核心库 iso_qmo_vintage.json
- 早期期次(2017-02 ~ 2024-08) = "当年发布视角"（每次修订都保留）
- 与已有 2024-11 ~ 2026-08 8期矩阵衔接
输出:
  early_vintage_matrix_2015_16_2023_24.csv / .json   (发布期次 × 年份 修订矩阵)
"""
import os
import re
import csv
import json
from pypdf import PdfReader

BASE = r"C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso"
HIST = os.path.join(BASE, "balance_pdfs", "historical")

YEAR_ORDER = ["2015/16","2016/17","2017/18","2018/19","2019/20",
              "2020/21","2021/22","2022/23","2023/24"]

def clean_num(s):
    s = s.strip().replace(",", "").replace(" ", "")
    try:
        return int(float(s))
    except ValueError:
        return None

def extract_surplus(text):
    """返回该期文本中 年份列表 + surplus/deficit 数值列表（按顺序对齐）"""
    m = re.search(r"WORLD SUGAR BALANCES \(October/September\)(.*)", text, re.S)
    if not m:
        return [], []
    seg = m.group(1)
    years = re.findall(r"(20\d\d/\d\d)", seg)
    mm = re.search(re.escape("Surplus/deficit") + r"\s*((?:[-\d,]+\s*,?\s*)+)", seg)
    if not mm:
        return years, []
    nums = re.findall(r"-?\d{1,3}(?:,\d{3})*", mm.group(1).replace(".", ","))
    return years, nums

def release_key(fn):
    """world_sugar_balance_<month>_<year>.pdf -> 'YYYY-MM'"""
    mo = {"february":"02","may":"05","august":"08","november":"11"}
    parts = fn.replace(".pdf", "").split("_")  # ['world','sugar','balance','february','2017']
    return parts[4] + "-" + mo.get(parts[3], "00")

# 收集每个发布期次的 surplus 向量
vintages = {}   # release -> {year: sd_value}
for fn in sorted(f for f in os.listdir(HIST) if f.endswith(".pdf")):
    path = os.path.join(HIST, fn)
    try:
        r = PdfReader(path)
        text = "".join((r.pages[i].extract_text() or "") for i in range(min(3, len(r.pages))))
        years, nums = extract_surplus(text)
        rel = release_key(fn)
        mp = {}
        for i, y in enumerate(years):
            if y in YEAR_ORDER and i < len(nums):
                v = clean_num(nums[i])
                if v is not None:
                    mp[y] = v
        if mp:
            vintages[rel] = mp
    except Exception as e:
        print("ERR", fn, type(e).__name__, e)

release_order = sorted(vintages.keys())
print("releases:", release_order)

# CSV 矩阵
csv_path = os.path.join(BASE, "early_vintage_matrix_2015_16_2023_24.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["market_year"] + release_order + ["unit"])
    chain = {}
    for y in YEAR_ORDER:
        row = [y] + [vintages[rel].get(y, "") for rel in release_order] + ["kt (tel quel)"]
        w.writerow(row)
        chain[y] = [vintages[rel].get(y) for rel in release_order]

# JSON
jdata = {
    "scope": "早期官方 World Sugar Balance memo（当年发布视角）中 2015/16~2023/24 的 surplus/deficit 修订轨迹",
    "source_files": "balance_pdfs/historical/world_sugar_balance_<month>_<year>.pdf (2017-02 ~ 2024-08, 28期)",
    "unit": "千吨 tel quel",
    "release_order": release_order,
    "revision_chain_kt": chain,
}
json_path = os.path.join(BASE, "early_vintage_matrix_2015_16_2023_24.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(jdata, f, ensure_ascii=False, indent=1)

# 并入核心库
core_path = os.path.join(BASE, "iso_qmo_vintage.json")
with open(core_path, encoding="utf-8") as f:
    core = json.load(f)
core["early_vintage_matrix_2015_16_2023_24"] = jdata
# 把 2015/16、2016/17 修订链写成更直白的 timeline
for y in ("2015/16", "2016/17"):
    core[f"revision_timeline_{y.replace('/', '_')}_kt"] = [
        {"vintage": rel, "balance_kt": vintages[rel].get(y)}
        for rel in release_order if vintages[rel].get(y) is not None
    ]
with open(core_path, "w", encoding="utf-8") as f:
    json.dump(core, f, ensure_ascii=False, indent=2)

print("\n--- 2015/16 revision chain (kt) ---")
for rel in release_order:
    v = vintages[rel].get("2015/16")
    if v is not None:
        print(f"  {rel}: {v}")
print("\n--- 2016/17 revision chain (kt) ---")
for rel in release_order:
    v = vintages[rel].get("2016/17")
    if v is not None:
        print(f"  {rel}: {v}")
print("\nwritten:", csv_path, json_path)