# -*- coding: utf-8 -*-
"""97 号棉花基本面全景：PSD cotton 分国数据拉取
输出: data/fundamentals/cotton/raw/survey_world.json (world 1975-2026)
      data/fundamentals/cotton/raw/survey_all_2026.json (country=all, MY2024/25/26)
      data/fundamentals/cotton/raw/survey_hist_top.json (关键国家 1980-2026)
"""
import json, ssl, urllib.request, time, os

KEY = "DxRVr66dGKqS1pItPj1sUXl1PLgmu3CmUPZCJsPL"
BASE = "https://api.fas.usda.gov/api/psd"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
os.makedirs(OUT, exist_ok=True)
CT = {"commodityCode": "0612000", "commodityName": "Sugar, Centrifugal"}  # placeholder
COTTON_CC = None

def get(path):
    req = urllib.request.Request(BASE + path, headers={"X-Api-Key": KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

# 1. 找棉花商品码
comms = get("/commodities")
for c in comms:
    nm = c.get("commodityName", "")
    if "otton" in nm:
        print("COTTON:", c)
        if nm == "Cotton":
            COTTON_CC = c["commodityCode"]  # 2631000 棉花(皮棉)
assert COTTON_CC == "2631000", f"cotton code wrong: {COTTON_CC}"
json.dump(comms, open(os.path.join(OUT, "commodities.json"), "w"))

# 2. 找关键国码（按名称断言）
countries = get("/countries")
json.dump(countries, open(os.path.join(OUT, "countries.json"), "w"))
want = ["United States", "China", "China, Mainland", "India", "Brazil", "Pakistan",
        "Turkey", "Australia", "Uzbekistan", "Mexico", "Egypt", "Bangladesh",
        "Vietnam", "European Union", "West Africa", "Argentina", "Indonesia", "Thailand"]
found = {}
for c in countries:
    nm = c.get("countryName", "")
    for w in want:
        if w.lower() == nm.lower() or (w == "China" and nm.startswith("China")):
            found[w] = c["countryCode"]
print("FOUND:", found)
json.dump(found, open(os.path.join(OUT, "key_countries.json"), "w"))

# 3. 世界序列 1975-2026
worlds = {}
for y in range(1975, 2027):
    try:
        d = get(f"/commodity/{COTTON_CC}/world/year/{y}")
        worlds[y] = {a["attributeId"]: a["value"] for a in d} if isinstance(d, list) else d
    except Exception as e:
        print("world", y, "ERR", e)
        worlds[y] = None
    time.sleep(0.15)
json.dump(worlds, open(os.path.join(OUT, "survey_world.json"), "w"), ensure_ascii=False)
print("world done", sum(1 for v in worlds.values() if v))

# 4. 分国全量：近 3 年 + 2026 一年 allcountries
for y in (2024, 2025, 2026):
    d = get(f"/commodity/{COTTON_CC}/country/all/year/{y}")
    json.dump(d, open(os.path.join(OUT, f"survey_all_{y}.json"), "w"), ensure_ascii=False)
    print("all", y, len(d) if d else 0, "records")
    time.sleep(0.5)

# 5. 关键国家历史 1980-2026
keys = {k: v for k, v in found.items() if k not in ("West Africa",)}
hist = {k: {} for k in keys}
for k, cc in keys.items():
    for y in range(1980, 2027):
        try:
            d = get(f"/commodity/{COTTON_CC}/country/{cc}/year/{y}")
            hist[k][y] = {a["attributeId"]: a["value"] for a in d} if isinstance(d, list) else d
        except Exception as e:
            hist[k][y] = None
        time.sleep(0.08)
json.dump(hist, open(os.path.join(OUT, "survey_hist_top.json"), "w"), ensure_ascii=False)
print("hist done", {k: sum(1 for v in hist[k].values() if v) for k in hist})
