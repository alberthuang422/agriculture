# -*- coding: utf-8 -*-
"""导出 Cotton A Index 月度序列(1960M01-最新)  → cotton_wb_monthly.csv"""
import openpyxl, csv, json

F = r"C:\Users\Administrator\Desktop\stock\data\cotton\CMO-Historical-Data-Monthly.xlsx"
wb = openpyxl.load_workbook(F, data_only=True)
sh = wb["Monthly Prices"]
rows = []
for r in sh.iter_rows(min_row=7):
    m = r[0].value
    v = r[54].value  # col 55 = Cotton
    if isinstance(m, str) and m.endswith("M01") or isinstance(m, str) and "M" in m:
        try:
            rows.append((m, float(v)))
        except (TypeError, ValueError):
            rows.append((m, None))
out = [(m, v) for m, v in rows if v is not None]
print("n =", len(out), "first:", out[0], "last:", out[-1])
lasty = [(m, v) for m, v in out if m.startswith(("2024", "2025", "2026"))]
print(lasty)
with open(r"C:\Users\Administrator\Desktop\stock\data\cotton\cotton_wb_monthly.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "cotton_a"])
    w.writerows(out)
vals = [v for _, v in out]
cur = out[-1][1]
import statistics
def pct(s, x): return 100.0 * sum(1 for a in s if a < x) / len(s)
print("current", cur, "| pct_full", round(pct(vals, cur), 1), "| pct_10y", round(pct(vals[-120:], cur), 1), "| pct_5y", round(pct(vals[-60:], cur), 1))
print("hist max", max(vals), "hist min", min(vals))
