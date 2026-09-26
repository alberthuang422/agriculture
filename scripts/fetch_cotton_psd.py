#!/usr/bin/env python3
"""提取 USDA PSD 棉花数据（Cotton=2631000），生成主产国/出口国供需长表。"""
import zipfile, csv, io, os

BASE = "/Users/alberthuang/agriculture/data"
TMP = f"{BASE}/_tmp"
OUT = f"{BASE}/cotton"

KEEP_COUNTRIES = [
    "China", "India", "United States", "Brazil", "Pakistan",
    "Australia", "Turkey", "Uzbekistan",
    "Benin", "Burkina Faso", "Mali", "Cote d`Ivoire", "Cote d'Ivoire",  # 西非 C4
    "Vietnam", "Bangladesh", "Indonesia",          # 主要进口国
    "World",
]

# 读取 psd_alldata.csv，筛选 Cotton
rows = []
with zipfile.ZipFile(f"{TMP}/psd_alldata_csv.zip") as z:
    name = [n for n in z.namelist() if n.endswith(".csv")][0]
    with z.open(name) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"))
        for r in reader:
            if r["Commodity_Code"] == "2631000":
                rows.append(r)

print(f"Total cotton rows: {len(rows)}")

# 每个 (country, market_year, attribute) 取 month 最大 = 最新修订
best = {}
countries_seen = set()
attrs_seen = {}
for r in rows:
    c = r["Country_Name"]
    countries_seen.add(c)
    attrs_seen[r["Attribute_Description"]] = r["Attribute_ID"]
    if c not in KEEP_COUNTRIES:
        continue
    key = (c, int(r["Market_Year"]), r["Attribute_Description"])
    m = int(r["Month"])
    if key not in best or m > best[key][0]:
        best[key] = (m, r["Value"])

print(f"Attributes: {attrs_seen}")
print(f"Available countries sample: {sorted(countries_seen)[:30]}")

# 组织为宽表：每行 (Country, Market_Year)，列为各属性
ATTRS = ["Area Harvested", "Beginning Stocks", "Production", "Imports",
         "Total Supply", "Exports", "Domestic Use", "Ending Stocks", "Stocks-to-Use"]
out_rows = []
by_ckpt = {}
for (c, y, a), (m, v) in best.items():
    by_ckpt.setdefault((c, y), {})[a] = v

for (c, y), d in sorted(by_ckpt.items()):
    prod = float(d.get("Production", 0) or 0)
    use = float(d.get("Domestic Use", 0) or 0)
    row = {"Country": c, "Market_Year": y, "Unit": "1000 480-lb bales"}
    for a in ATTRS:
        if a in d and d[a] not in (None, ""):
            row[a] = d[a]
    # 补算库消比（分母 = Domestic Use，PSD 棉花口径）
    if use > 0 and "Ending Stocks" in row:
        row["Stocks_to_Use_Pct"] = round(float(row["Ending Stocks"]) / use * 100, 2)
    out_rows.append(row)

os.makedirs(OUT, exist_ok=True)
out_csv = f"{OUT}/usda_psd_cotton_major_countries.csv"
fields = ["Country", "Market_Year", "Unit"] + [a for a in ATTRS if a != "Stocks-to-Use"] + ["Stocks_to_Use_Pct"]
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in out_rows:
        w.writerow(r)

print(f"Wrote {len(out_rows)} rows -> {out_csv}")

# 自检锚（全球产量，千 bales）
for y in (1960, 1980, 2000, 2010, 2026):
    v = best.get(("World", y, "Production"))
    print(f"Check World MY{y} Production = {v[1] if v else 'N/A'} (anchor: 46000/64000/88000/115000/118000)")
for c in ("China", "India", "United States"):
    v = best.get((c, 2026, "Production"))
    print(f"Check {c} MY2026 Production = {v[1] if v else 'N/A'} (anchor: CN~6000 IN~5500 US~14000)")
