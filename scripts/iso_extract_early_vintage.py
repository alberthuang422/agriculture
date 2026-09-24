# -*- coding: utf-8 -*-
"""
从 historical/ 早期官方 World Sugar Balance PDF 提取 2015/16 与 2016/17 的当年发布值
（全球汇总表第2页起, surplus/deficit 等指标 × vintage 修订链）
输出: data/fundamentals/sugar/iso/early_vintage_2015_16_2016_17.json + CSV
"""
import os
import re
import csv
import json
from pypdf import PdfReader

BASE = r"C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso"
HIST = os.path.join(BASE, "balance_pdfs", "historical")

METRICS = ["Production", "Consumption", "Surplus/deficit", "Import demand", "End stocks"]

def clean_num(s):
    """去掉千分位逗号与乱码点, 保留负号, 转 int"""
    s = s.strip().replace(",", "").replace(" ", "")
    try:
        return int(float(s))
    except ValueError:
        return None

def extract_global_table(text):
    """找到 WORLD SUGAR BALANCES 段, 返回 (year_list, metric->values dict)"""
    m = re.search(r"WORLD SUGAR BALANCES \(October/September\)(.*?)(?:INTERNATIONAL|International|STATISTICAL)", text, re.S)
    if not m:
        m = re.search(r"WORLD SUGAR BALANCES \(October/September\)(.*)", text, re.S)
    if not m:
        return None, None
    seg = m.group(1)
    # 年份: 形如 2016/17 的 token 序列（后一年为两位数）
    years = re.findall(r"(20\d\d/\d\d)", seg)
    # 指标行: 名称 后跟数字序列
    rows = {}
    for metric in METRICS:
        # 匹配 "Metric" 后到下一指标名前的数字段
        mm = re.search(re.escape(metric) + r"\s*((?:[-\d]+\s*,?\s*)+)", seg)
        if mm:
            nums = re.findall(r"-?\d{1,3}(?:,\d{3})*", mm.group(1).replace(".", ","))
            rows[metric] = nums
    return years, rows

def pdf_global_text(path, max_pages=3):
    r = PdfReader(path)
    out = []
    for i in range(min(max_pages, len(r.pages))):
        out.append(r.pages[i].extract_text() or "")
    return "\n".join(out)

results = []
files = sorted(f for f in os.listdir(HIST) if f.endswith(".pdf"))
for fn in files:
    path = os.path.join(HIST, fn)
    try:
        text = pdf_global_text(path)
        years, rows = extract_global_table(text)
        if years and "2015/16" in years and "surplus_deficit" not in rows and "Surplus/deficit" in rows:
            pass
        # 取 surplus/deficit 值
        entry = {"file": fn}
        if rows:
            sd = rows.get("Surplus/deficit", [])
            prod = rows.get("Production", [])
            cons = rows.get("Consumption", [])
            # 年份与数值按位置对齐
            for i, y in enumerate(years):
                if y in ("2015/16", "2016/17"):
                    entry[y] = {
                        "surplus_deficit_kt": clean_num(sd[i]) if i < len(sd) else None,
                        "production_kt": clean_num(prod[i]) if i < len(prod) else None,
                        "consumption_kt": clean_num(cons[i]) if i < len(cons) else None,
                    }
        results.append(entry)
    except Exception as e:
        results.append({"file": fn, "error": f"{type(e).__name__}: {e}"})

# 输出
out_json = os.path.join(BASE, "early_vintage_2015_16_2016_17.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

# 精简CSV: 期次, 2015/16 sd, 2016/17 sd
out_csv = os.path.join(BASE, "early_vintage_2015_16_2016_17.csv")
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["vintage_file", "2015/16_surplus_kt", "2016/17_surplus_kt"])
    for r in results:
        s15 = r.get("2015/16", {}).get("surplus_deficit_kt") if "2015/16" in r else ""
        s16 = r.get("2016/17", {}).get("surplus_deficit_kt") if "2016/17" in r else ""
        w.writerow([r.get("file", "?"), s15, s16])

print("parsed", len(results), "files ->", out_json)
for r in results:
    s = r.get("2015/16", {}).get("surplus_deficit_kt")
    s6 = r.get("2016/17", {}).get("surplus_deficit_kt")
    if s is not None or s6 is not None:
        print(f"  {r['file']:50s} 2015/16={s}  2016/17={s6}")