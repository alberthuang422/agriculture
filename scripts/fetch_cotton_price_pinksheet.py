#!/usr/bin/env python3
"""从 World Bank Pink Sheet 提取 Cotton A Index 月度价格（按表头名定位，不硬编码列号）。"""
import openpyxl, csv, os

BASE = "/Users/alberthuang/agriculture/data"
TMP = f"{BASE}/_tmp"
OUT = f"{BASE}/cotton"

wb = openpyxl.load_workbook(f"{TMP}/cmo_monthly.xlsx", read_only=True, data_only=True)
ws = wb["Monthly Prices"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

# 表头在第 5 行（0-based index 4），单位在第 6 行（index 5），数据从 index 6 起
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
print("Header sample:", [k for k in hdr if "otton" in k])
unit_row = rows[5]

col = hdr.get("Cotton") or next(v for k, v in hdr.items() if "Cotton" in k)
unit = unit_row[col]
print(f"Cotton column index = {col}, unit = {unit}")

out_rows = []
for r in rows[6:]:
    d = r[0]
    if d is None:
        continue
    s = str(d)
    if len(s) < 6 or "M" not in s:
        continue
    try:
        y, m = int(s[:4]), int(s[5:7])
    except ValueError:
        continue
    v = r[col]
    if v is not None:
        out_rows.append({"Year": y, "Month": m, "Cotlook_A_Index_USD_per_kg": v})

os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/worldbank_cotlook_a_monthly.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["Year", "Month", "Cotlook_A_Index_USD_per_kg"])
    w.writeheader()
    w.writerows(out_rows)

print(f"Wrote {len(out_rows)} rows ({out_rows[0]['Year']}-{out_rows[0]['Month']:02d} ~ {out_rows[-1]['Year']}-{out_rows[-1]['Month']:02d})")
print(f"First: {out_rows[0]}, Latest: {out_rows[-1]}")
# 锚点：2022 年 5 月棉价历史峰值约 $2.14/kg（Cotlook A ~176 美分/磅）
peak = max(out_rows, key=lambda x: x["Cotlook_A_Index_USD_per_kg"])
print(f"All-time peak: {peak}")
