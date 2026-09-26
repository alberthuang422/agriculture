#!/usr/bin/env python3
"""Build US cotton export same-period comparison report (report 106).

Inputs:
- data/fundamentals/cotton/us_cotton_esr_20260925/esr_5y_by_country.json (ESRQS Comparison5YearReport)
- data/cotton/usda_psd_cotton_major_countries.csv (PSD annual, US exports)
- national same-week numbers extracted from archived weekly report PDFs (hardcoded below with source dates)

Output: reports/106_美国棉花出口同期对比_20260925/index.html
"""
import json, csv, os, math

ROOT = "/Users/alberthuang/agriculture"
ESR = f"{ROOT}/data/fundamentals/cotton/us_cotton_esr_20260925/esr_5y_by_country.json"
OUT_DIR = f"{ROOT}/reports/106_美国棉花出口同期对比_20260925"
os.makedirs(OUT_DIR, exist_ok=True)

raw = json.load(open(ESR))
countries = list(raw["countries"].keys())  # ordered: China, Vietnam, Pakistan, Bangladesh, Turkey, Mexico, India, Korea, Japan, Indonesia, Thailand, Honduras

ch = raw["countries"]["China"]["accumulated_exports"]
L = next(i for i, r in enumerate(ch) if r["weekendingDate"][:10] >= r["reportWeekEndingDate"][:10])  # = 6, week ending 2026-09-17
NWEEK = 40  # show 40 weeks of prior-year trajectories

weeks = [r["weekendingDate"][:10] for r in ch]

def s(c, rname, f):
    return [r[f] or 0 for r in raw["countries"][c][rname]]

# ---- top-12 aggregate weekly series ----
agg = {}
for rname in ["accumulated_exports", "accumulated_net_sales", "outstanding_sales"]:
    agg[rname] = []
    for i in range(53):
        agg[rname].append({
            "cur": round(sum(s(c, rname, "currentMarketingYear")[i] for c in countries)),
            "y1": round(sum(s(c, rname, "yearAgo1")[i] for c in countries)),
            "y2": round(sum(s(c, rname, "yearAgo2")[i] for c in countries)),
            "y3": round(sum(s(c, rname, "yearAgo3")[i] for c in countries)),
            "y4": round(sum(s(c, rname, "yearAgo4")[i] for c in countries)),
            "y5": round(sum(s(c, rname, "yearAgo5")[i] for c in countries)),
            "avg5": round(sum(s(c, rname, "yearsAverage5")[i] for c in countries)),
        })

# ---- per-country YTD at latest week ----
rows = []
tot_cur = tot_y1 = tot_avg5 = 0
tot_ns_cur = tot_ns_y1 = tot_ns_avg5 = 0
for c in countries:
    e = raw["countries"][c]["accumulated_exports"][L]
    n = raw["countries"][c]["accumulated_net_sales"][L]
    o = raw["countries"][c]["outstanding_sales"][L]
    cur, y1, a5 = e["currentMarketingYear"], e["yearAgo1"], e["yearsAverage5"]
    ncur, ny1, na5 = n["currentMarketingYear"], n["yearAgo1"], n["yearsAverage5"]
    tot_cur += cur; tot_y1 += y1; tot_avg5 += a5
    tot_ns_cur += ncur; tot_ns_y1 += ny1; tot_ns_avg5 += na5
    rows.append({
        "name": c, "exp_cur": cur, "exp_y1": y1, "exp_avg5": round(a5),
        "exp_yoy": round((cur / y1 - 1) * 100, 1) if y1 > 0 else None,
        "exp_vs_avg": round((cur / a5 - 1) * 100, 1) if a5 > 0 else None,
        "ns_cur": ncur, "ns_y1": ny1, "ns_avg5": round(na5),
        "ns_vs_avg": round((ncur / na5 - 1) * 100, 1) if na5 > 0 else None,
        "out_cur": o["currentMarketingYear"], "out_avg5": round(o["yearsAverage5"]),
    })

# ---- national same-week (week 7 of MY) from archived weekly report PDFs ----
national = [
    # MY, as-of date, outstanding, accumulated exports, total commitment, export projection (all 1000 RB)
    {"my": "2021/22", "asof": "2021-09-23", "out": 5708.3, "exp": 1515.5, "com": 7223.8, "proj": 14640},
    {"my": "2022/23", "asof": "2022-09-22", "out": 6193.5, "exp": 1825.9, "com": 8019.4, "proj": 11810},
    {"my": "2023/24", "asof": "2023-09-21", "out": 4187.3, "exp": 1353.2, "com": 5540.4, "proj": 11570},
    {"my": "2024/25", "asof": "2024-09-19", "out": 4000.2, "exp": 958.8,  "com": 4959.0, "proj": 11070},
    {"my": "2025/26", "asof": "2025-09-18", "out": 3137.8, "exp": 921.1,  "com": 4058.9, "proj": 11120},
    {"my": "2026/27", "asof": "2026-09-17", "out": 3517.0, "exp": 1217.6, "com": 4734.6, "proj": 11550},
]
cur_nat = national[-1]
prior5 = national[:-1]
avg_exp5 = sum(x["exp"] for x in prior5) / 5
avg_com5 = sum(x["com"] for x in prior5) / 5
avg_out5 = sum(x["out"] for x in prior5) / 5

# ---- PSD annual US exports ----
psd = []
with open(f"{ROOT}/data/cotton/usda_psd_cotton_major_countries.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["Country"] == "United States":
            psd.append([int(r["Market_Year"]), float(r["Exports"])])
psd.sort()

RB2T = 0.217724 * 1.03  # 1 running bale -> metric tons (480-lb bale * 1.03)
data = {
    "asof": "2026-09-17", "fetched": "2026-09-25",
    "weeks": weeks, "L": L, "NWEEK": NWEEK,
    "agg": agg,
    "rows": rows,
    "national": national,
    "kpi": {
        "exp_cur": cur_nat["exp"], "exp_yoy": round((cur_nat["exp"] / 921.1 - 1) * 100, 1),
        "exp_vs_avg": round((cur_nat["exp"] / avg_exp5 - 1) * 100, 1), "exp_t": round(cur_nat["exp"] * 1000 * RB2T / 10000, 1),  # 万吨
        "com_cur": cur_nat["com"], "com_yoy": round((cur_nat["com"] / 4058.9 - 1) * 100, 1),
        "com_vs_avg": round((cur_nat["com"] / avg_com5 - 1) * 100, 1), "com_t": round(cur_nat["com"] * 1000 * RB2T / 10000, 1),
        "out_cur": cur_nat["out"], "out_vs_avg": round((cur_nat["out"] / avg_out5 - 1) * 100, 1),
        "avg_exp5": round(avg_exp5), "avg_com5": round(avg_com5),
        "t12": round(tot_cur * RB2T / 10000, 1),
    },
    "psd": psd,
}
json.dump(data, open(f"{OUT_DIR}/data.json", "w"), ensure_ascii=False)
print("top12 exp cur/y1/avg5:", tot_cur, tot_y1, round(tot_avg5))
print("kpi:", data["kpi"])
print("written", f"{OUT_DIR}/data.json")
