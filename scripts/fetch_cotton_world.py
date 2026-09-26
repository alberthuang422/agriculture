#!/usr/bin/env python3
"""PSD 棉花 World 加总：全部 135 个互斥实体直接求和（无欧盟聚合行，历史实体与后继国不重叠）。"""
import zipfile, csv, io, os

BASE = "/Users/alberthuang/agriculture/data"
TMP = f"{BASE}/_tmp"
OUT = f"{BASE}/cotton"

ATTRS = ["Beginning Stocks", "Production", "Imports", "Total Supply",
         "Exports", "Domestic Use", "Ending Stocks"]

best = {}  # (country, my, attr) -> (month, value)
with zipfile.ZipFile(f"{TMP}/psd_alldata_csv.zip") as z:
    name = [n for n in z.namelist() if n.endswith(".csv")][0]
    with z.open(name) as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace")):
            if r["Commodity_Code"] != "2631000":
                continue
            key = (r["Country_Name"], int(r["Market_Year"]), r["Attribute_Description"])
            m = int(r["Month"])
            if key not in best or m > best[key][0]:
                best[key] = (m, r["Value"])

world = {}  # (my, attr) -> sum
for (c, y, a), (m, v) in best.items():
    if a not in ATTRS or v in (None, ""):
        continue
    world[(y, a)] = world.get((y, a), 0.0) + float(v)

out_rows = []
years = sorted({y for (y, a) in world})
for y in years:
    row = {"Country": "World", "Market_Year": y, "Unit": "1000 480-lb bales"}
    for a in ATTRS:
        if (y, a) in world:
            row[a] = round(world[(y, a)], 1)
    use = world.get((y, "Domestic Use"), 0)
    stocks = world.get((y, "Ending Stocks"), 0)
    if use > 0:
        row["Stocks_to_Use_Pct"] = round(stocks / use * 100, 2)
        # 剥离中国口径（中国国储是全球最大封闭库存，必须双口径）
        cn_stocks = None
        out_rows.append(row)

# 剥离中国口径
cn = {}
for (c, y, a), (m, v) in best.items():
    if c == "China" and a in ATTRS and v not in (None, ""):
        cn[(y, a)] = cn.get((y, a), 0.0) + float(v)

out2 = []
for y in years:
    use = world.get((y, "Domestic Use"), 0) - cn.get((y, "Domestic Use"), 0)
    stocks = world.get((y, "Ending Stocks"), 0) - cn.get((y, "Ending Stocks"), 0)
    if use > 0:
        out2.append({"Market_Year": y,
                     "World_ExChina_Stocks_kBales": round(stocks, 1),
                     "World_ExChina_DomUse_kBales": round(use, 1),
                     "Stocks_to_Use_Pct_ExChina": round(stocks / use * 100, 2)})

os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/usda_psd_cotton_world.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["Country", "Market_Year", "Unit"] + ATTRS + ["Stocks_to_Use_Pct"])
    w.writeheader()
    w.writerows(out_rows)

with open(f"{OUT}/usda_psd_cotton_world_exchina.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["Market_Year", "World_ExChina_Stocks_kBales",
                                      "World_ExChina_DomUse_kBales", "Stocks_to_Use_Pct_ExChina"])
    w.writeheader()
    w.writerows(out2)

# 自检锚
for y, anchor in [(1960, 46000), (1980, 64000), (2000, 88000), (2010, 115000), (2026, 118000)]:
    v = world.get((y, "Production"), 0)
    print(f"World MY{y} Production = {v:,.0f} (anchor ~{anchor:,}, dev {v/anchor*100-100:+.1f}%)")
# 库消比对照（skill 实测：2026 全球 ≈56.8%、剥离中国 ≈28.5%）
r26 = [r for r in out_rows if r["Market_Year"] == 2026]
r26x = [r for r in out2 if r["Market_Year"] == 2026]
if r26: print(f"World MY2026 Stocks/Use = {r26[0]['Stocks_to_Use_Pct']}% (skill anchor ~56.8%)")
if r26x: print(f"ExChina MY2026 Stocks/Use = {r26x[0]['Stocks_to_Use_Pct_ExChina']}% (skill anchor ~28.5%)")
