# -*- coding: utf-8 -*-
"""计算甘蔗面积/单产统计量，输出报告用 JSON"""
import json, csv, os

BASE = "C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar"
SRC = os.path.join(BASE, "sugarcane_area_yield_2005_2024.csv")

# 读取面板
rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
by = {}
for r in rows:
    cc, y = r["country_cn"], int(r["year"])
    by.setdefault(cc, {})[y] = {
        "prod": float(r["production_tonnes"]),
        "yield": float(r["yield_t_per_ha"]),
        "area": float(r["area_1000ha"]),
    }

YEARS = list(range(2005, 2025))
OUT = {}

def chg(c, y0, y1):
    d = by.get(c, {})
    if y0 not in d or y1 not in d: return None
    return d[y1], d[y0]

# 1) 各国关键统计
stats = {}
for c, d in by.items():
    y0, y1 = YEARS[0], YEARS[-1]
    a0, a1 = d.get(y0, {}).get("area"), d.get(y1, {}).get("area")
    yld0, yld1 = d.get(y0, {}).get("yield"), d.get(y1, {}).get("yield")
    p0, p1 = d.get(y0, {}).get("prod"), d.get(y1, {}).get("prod")
    areas = [d[y]["area"] for y in YEARS if y in d and d[y]["area"]]
    yields = [d[y]["yield"] for y in YEARS if y in d and d[y]["yield"]]
    stats[c] = {
        "year0": y0, "year1": y1,
        "area_2005": round(a0, 1), "area_2024": round(a1, 1),
        "area_chg_1000ha": round((a1 - a0) if (a0 is not None and a1 is not None) else None, 1),
        "area_pct": round((a1 / a0 - 1) * 100, 1) if (a0 and a1) else None,
        "area_min": round(min(areas), 1), "area_max": round(max(areas), 1),
        "area_min_year": YEARS[areas.index(min(areas))] if areas else None,
        "area_max_year": YEARS[areas.index(max(areas))] if areas else None,
        "yield_2005": round(yld0, 2), "yield_2024": round(yld1, 2),
        "yield_chg_pct": round((yld1 / yld0 - 1) * 100, 1) if (yld0 and yld1) else None,
        "yield_min": round(min(yields), 2), "yield_max": round(max(yields), 2),
        "yield_min_year": YEARS[yields.index(min(yields))] if yields else None,
        "yield_max_year": YEARS[yields.index(max(yields))] if yields else None,
        "prod_2005": round(p0 / 1e6, 1), "prod_2024": round(p1 / 1e6, 1),
    }
OUT["countries"] = stats

# 2) 全球分年序列
OUT["world_series"] = [{"year": y, **by["全球"][y]} for y in YEARS]

# 3) 全球 20 年总览
g0, g1 = by["全球"][2005], by["全球"][2024]
OUT["world_overview"] = {
    "area_2005_1000ha": round(g0["area"], 1),
    "area_2024_1000ha": round(g1["area"], 1),
    "area_chg_1000ha": round(g1["area"] - g0["area"], 1),
    "area_pct": round((g1["area"] / g0["area"] - 1) * 100, 1),
    "yield_2005": round(g0["yield"], 2),
    "yield_2024": round(g1["yield"], 2),
    "yield_chg_pct": round((g1["yield"] / g0["yield"] - 1) * 100, 1),
    "prod_2005_MT": round(g0["prod"] / 1e6, 1),
    "prod_2024_MT": round(g1["prod"] / 1e6, 1),
    "prod_pct": round((g1["prod"] / g0["prod"] - 1) * 100, 1),
}

# 4) 中国细分
cn = by["中国"]
OUT["china"] = {
    "area_2005_1000ha": round(cn[2005]["area"], 1),
    "area_2024_1000ha": round(cn[2024]["area"], 1),
    "area_chg_1000ha": round(cn[2024]["area"] - cn[2005]["area"], 1),
    "area_chg_pct": round((cn[2024]["area"] / cn[2005]["area"] - 1) * 100, 1),
    "area_max_1000ha": round(max(cn[y]["area"] for y in YEARS), 1),
    "area_max_year": max((cn[y]["area"], y) for y in YEARS)[1],
    "yield_2005": round(cn[2005]["yield"], 2),
    "yield_2024": round(cn[2024]["yield"], 2),
    "yield_chg_pct": round((cn[2024]["yield"] / cn[2005]["yield"] - 1) * 100, 1),
    "yield_max": round(max(cn[y]["yield"] for y in YEARS), 2),
    "yield_max_year": max((cn[y]["yield"], y) for y in YEARS)[1],
}

# 5) 全球面积增量分解（2024 vs 2005）
areas_2024 = {c: stats[c]["area_2024"] for c in stats if c != "全球"}
areas_2005 = {c: stats[c]["area_2005"] for c in stats if c != "全球"}
chgs = sorted([(c, areas_2024[c] - areas_2005[c]) for c in areas_2024], key=lambda x: -x[1])
OUT["area_change_breakdown"] = [
    {"country": c, "chg_1000ha": round(v, 1)} for c, v in chgs
]
OUT["world_area_chg"] = round(g1["area"] - g0["area"], 1)

json.dump(OUT, open(os.path.join(BASE, "sugarcane_stats_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("DONE")
print("全球面积:", OUT["world_overview"]["area_2005_1000ha"], "->", OUT["world_overview"]["area_2024_1000ha"],
      "chg", OUT["world_overview"]["area_chg_1000ha"], "pct", OUT["world_overview"]["area_pct"])
print("全球单产:", OUT["world_overview"]["yield_2005"], "->", OUT["world_overview"]["yield_2024"])
print("增量分解:", [(c["country"], c["chg_1000ha"]) for c in OUT["area_change_breakdown"]])