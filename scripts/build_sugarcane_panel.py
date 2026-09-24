# -*- coding: utf-8 -*-
"""下载 OWID(FAO 源) 甘蔗产量/单产 CSV，构建 2005-2024 主产国面板
面积 = 产量 / 单产 (FAO 三者定义自洽)
输出: data/fundamentals/sugarcane_area_yield_2005_2024.csv
      data/fundamentals/sugarcane_area_yield_2005_2024.json
原始下载: data/sugar/raw/owid_*.csv
"""
import urllib.request, ssl, csv, json, os, io

ctx = ssl.create_default_context()
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BASE = "C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar"
FUND = "C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar"

def fetch(slug):
    url = (f"https://ourworldindata.org/grapher/{slug}.csv"
           f"?v=1&csvType=full&useColumnShortNames=true")
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")

print("downloading production...", flush=True)
prod_csv = fetch("sugar-cane-production")
print("downloading yields...", flush=True)
yield_csv = fetch("sugar-cane-yields")

os.makedirs(BASE + "/raw", exist_ok=True)
open(BASE + "/raw/owid_sugarcane_production.csv", "w", encoding="utf-8", newline="").write(prod_csv)
open(BASE + "/raw/owid_sugarcane_yields.csv", "w", encoding="utf-8", newline="").write(yield_csv)

def load(csv_text):
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    # 列名如 sugar_cane__00000156__production__005510__tonnes
    valcol = [k for k in rows[0].keys() if k.startswith("sugar_cane")][0]
    d = {}
    for r in rows:
        ent, code, year = r["entity"], r.get("code") or "", int(r["year"])
        v = r[valcol]
        d.setdefault(ent, {})[year] = float(v) if v not in ("", "nan") else None
    return d, valcol

prod, pcol = load(prod_csv)
yld, ycol = load(yield_csv)
print("prod entities:", len(prod), "yield entities:", len(yld))

# 目标国家（OWID entity 名）
TARGETS = {
    "World": "全球",
    "China": "中国",
    "Brazil": "巴西",
    "India": "印度",
    "Thailand": "泰国",
    "United States": "美国",
    "Mexico": "墨西哥",
    "Pakistan": "巴基斯坦",
    "Indonesia": "印尼",
    "Australia": "澳大利亚",
    "Guatemala": "危地马拉",
    "Colombia": "哥伦比亚",
}

YEARS = list(range(2005, 2025))  # 2005-2024 (OWID 最新为2024)

missing = []
panel = {}
for ent, cn in TARGETS.items():
    if ent not in prod:
        print("MISSING ENTITY in prod:", ent); missing.append(ent); continue
    if ent not in yld:
        print("MISSING ENTITY in yield:", ent); missing.append(ent); continue
    rows = []
    ok = 0
    for y in YEARS:
        p = prod[ent].get(y)
        yv = yld[ent].get(y)
        if p is None or yv is None or yv == 0:
            rows.append({"year": y, "prod_t": None, "yield_t_ha": None, "area_ha": None,
                         "area_1000ha": None})
            continue
        area = p / yv  # 公顷
        rows.append({
            "year": y,
            "prod_t": round(p, 1),
            "yield_t_ha": round(yv, 2),
            "area_ha": round(area, 0),
            "area_1000ha": round(area / 1000, 1),
        })
        ok += 1
    panel[cn] = {"entity_owid": ent, "rows": rows, "years_present": ok}
    print(f"{cn:6s} {ent:15s} years_present={ok}/{len(YEARS)}", flush=True)

# 导出 CSV
with open(FUND + "/sugarcane_area_yield_2005_2024.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["country_cn", "entity_owid", "year", "production_tonnes",
                "yield_t_per_ha", "area_ha", "area_1000ha"])
    for cn in panel:
        for row in panel[cn]["rows"]:
            w.writerow([cn, panel[cn]["entity_owid"], row["year"],
                        row["prod_t"], row["yield_t_ha"], row["area_ha"], row["area_1000ha"]])

# 导出 JSON
json.dump({"meta": {
            "source": "Our World in Data (FAOSTAT Production: Crops and livestock products, FAO 2025 release)",
            "og_url_prod": "https://ourworldindata.org/grapher/sugar-cane-production",
            "og_url_yield": "https://ourworldindata.org/grapher/sugar-cane-yields",
            "item": "Sugar cane (FAOSTAT item 156)",
            "defs": "production=tonnes; yield=t/ha(=FAOSTAT 5412); area_ha=production/yield",
            "years": [YEARS[0], YEARS[-1]],
            "latest_year_note": "FAO(OWID) 最新发布至 2024；2025 需 FAO 2026 年批次发布",
           },
           "countries": panel,
           "missing_entities": missing},
          open(FUND + "/sugarcane_area_yield_2005_2024.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("saved:", FUND + "/sugarcane_area_yield_2005_2024.csv")
print("missing:", missing)