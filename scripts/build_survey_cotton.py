# -*- coding: utf-8 -*-
"""97 棉花基本面全景：数据汇总 + 平衡表校验 + 分位计算
源1: psd_alldata.csv (USDA PSD 全量快照 2026-09-11, commodity 2631000, unit 27 = 1000 480lb bales)
源2: survey_world.json / survey_all_{24,25,26}.json (API 2026-09-20 拉, 校验用)
"""
import json, csv, os

RAW = r"C:\Users\Administrator\Desktop\stock\data\cotton\raw"
OUT_PATH = r"C:\Users\Administrator\Desktop\stock\results\cotton_survey_20260920.json"

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None

# ---- 源1: psd_alldata ----
rows = []
with open(os.path.join(RAW, "psd_alldata.csv"), encoding="utf-8-sig") as fp:
    for r in csv.reader(fp):
        if r[0] == "2631000":
            rows.append(r)
print("cotton rows:", len(rows))

# key: (country,year) -> attr -> value (unit 27 = 1000 480-lb bales)
data = {}
for r in rows:
    cc, cn, my, attr, unit, val = r[2], r[3], int(r[4]), r[8], r[9], f(r[11])
    if unit != "27":
        continue
    data.setdefault((cn, my), {})[attr] = {"v": val, "attr_id": r[7], "cy": int(r[5]), "m": r[6]}
keys = set(data)
print("entities:", len(set(k[0] for k in keys)), "| years:", min(k[1] for k in keys), "-", max(k[1] for k in keys))

def get(cn, my, attr):
    a = data.get((cn, my))
    return a.get(attr, {}).get("v") if a else None

# ---- 世界序列主源: API survey_world (2026-09-20) ----
world_api = json.load(open(os.path.join(RAW, "survey_world.json")))
fails = []
world = {}
for yy, rl in world_api.items():
    if not (isinstance(rl, (list, dict))):
        continue
    a = {int(k): v for k, v in rl.items()} if isinstance(rl, dict) else {r["attributeId"]: r["value"] for r in rl}
    my = int(yy)
    be, pr, im, su, ex, dom, loss, st, td = (a.get(i) for i in (20, 28, 57, 86, 88, 142, 150, 176, 178))
    if pr is None:
        continue
    check1 = abs((su or 0) - (be + pr + im)) < 20
    check2 = abs((td or 0) - (dom + ex + loss + st)) < 20
    if not (check1 and check2):
        fails.append((my, check1, check2))
    world[my] = {"prod": pr, "dom": dom, "imp": im, "exp": ex, "beg": be, "end": st,
                 "stu": round(st/dom*100, 1) if dom else None,
                 "stu_t": round(st/(dom+ex)*100, 1) if dom and ex else None,
                 "pm": pr - dom}
print("world identity fails:", fails[:5], "count:", len(fails), "/", len(world))

# 分国历史（主要国家序列 + vintage 日期）
hist = {}
for cn in set(k[0] for k in keys):
    for my in sorted(set(k[1] for k in keys if k[0] == cn)):
        dd = data.get((cn, my))
        if not dd or cn in ("World", "Former Soviet Union") or "Soviet" in cn or "Yugoslavia" in cn:
            continue
        e = hist.setdefault(cn, [])
        if my == 1960 or len(e) == 0 or e[-1]["y"] != my:
            e.append({"y": my, "prod": get(cn, my, "Production"), "dom": get(cn, my, "Domestic Use"),
                      "exp": get(cn, my, "Exports"), "imp": get(cn, my, "Imports"),
                      "end": get(cn, my, "Ending Stocks"), "area": get(cn, my, "Area Harvested"),
                      "cy": dd.get("Production", {}).get("cy"), "m": dd.get("Production", {}).get("m")})

# 2026 分国全景排名
rank = {}
for metric, key in (("prod", "Production"), ("exp", "Exports"), ("imp", "Imports"), ("end", "Ending Stocks"), ("dom", "Domestic Use")):
    vals = [(get(cn, 2026, key), cn) for cn in set(k[0] for k in keys)
            if get(cn, 2026, key) and get(cn, 2026, key) > 0]
    vals.sort(reverse=True)
    rank[metric] = [{"name": cn, "val": v, "year_vintage": f"{get(cn,2026, key)}"} for v, cn in vals[:12]]

# 2025 与 2026 对比
delta = {}
for cn in ("United States", "China", "India", "Brazil", "Pakistan", "Turkey", "Australia", "Uzbekistan", "Egypt", "Bangladesh", "Vietnam", "European Union"):
    delta[cn] = {"prod25": get(cn, 2025, "Production"), "prod26": get(cn, 2026, "Production"),
                 "dom25": get(cn, 2025, "Domestic Use"), "dom26": get(cn, 2026, "Domestic Use"),
                 "exp25": get(cn, 2025, "Exports"), "exp26": get(cn, 2026, "Exports"),
                 "imp25": get(cn, 2025, "Imports"), "imp26": get(cn, 2026, "Imports"),
                 "end25": get(cn, 2025, "Ending Stocks"), "end26": get(cn, 2026, "Ending Stocks")}

# 剥离中国序列（分子分母同步；全球层用 API world，中国层用 psd_alldata）
ex_cn = {}
for my, wv in world.items():
    sp, sd, se = wv["prod"], wv["dom"], wv["end"]
    cp, cd, ce = get("China", my, "Production"), get("China", my, "Domestic Use"), get("China", my, "Ending Stocks")
    if sp and cp and cd and sd and ce:
        ex_cn[my] = {"prod": sp - cp, "dom": sd - cd, "end": se - ce,
                     "stu": round((se - ce) / (sd - cd) * 100, 1)}
# 剥中印
ex_c2i = {}
for my, wv in world.items():
    sp, sd, se = wv["prod"], wv["dom"], wv["end"]
    c1p, c1d, c1e = get("China", my, "Production"), get("China", my, "Domestic Use"), get("China", my, "Ending Stocks")
    c2p, c2d, c2e = get("India", my, "Production"), get("India", my, "Domestic Use"), get("India", my, "Ending Stocks")
    if sp and se and c1p and c2p:
        ex_c2i[my] = {"prod": sp - c1p - c2p, "dom": sd - c1d - c2d, "end": se - c1e - c2e,
                      "stu": round((se - c1e - c2e) / (sd - c1d - c2d) * 100, 1)}

# 分位函数
def pct(series, v):
    s = sorted(x for x in series if x is not None)
    return round(100.0 * sum(1 for x in s if x < v) / len(s), 1)

stu_series = [(y, v["stu"]) for y, v in world.items() if v["stu"]]
exst = [(y, v["stu"]) for y, v in ex_cn.items() if v["stu"]]
ex2 = [(y, v["stu"]) for y, v in ex_c2i.items() if v["stu"]]

def pcts(series_list):
    ys = sorted(series_list)
    cur = ys[-1]
    full = [v for _, v in ys]
    windows = {"full": pct(full, cur[1]), "10y": pct([v for y, v in ys if y >= cur[0]-10+1], cur[1]),
               "5y": pct([v for y, v in ys if y >= cur[0]-4], cur[1])}
    return {"cur": cur[1], "cur_year": cur[0], **windows, "min": min(full), "max": max(full),
            "prev_year": ys[-2][1] if len(ys) > 1 else None}

stats = {"world_stu": pcts(stu_series), "excn_stu": pcts(exst), "exc2i_stu": pcts(ex2)}

# 交叉核对 9/20 API 世界序列 (survey_world)
world_api = json.load(open(os.path.join(RAW, "survey_world.json")))
cross = {}
for y in ("2024", "2025", "2026"):
    rl = world_api.get(y)
    if isinstance(rl, list):
        a = {r["attributeId"]: r["value"] for r in rl}
        cross[y] = {"api_prod": a.get(28), "psd_prod": get("World", int(y), "Production"),
                    "api_dom": a.get(125), "psd_dom": get("World", int(y), "Domestic Use")}

# 2026 分国 vs API 336 条（仅 unitId=4）
allc26 = json.load(open(os.path.join(RAW, "survey_all_2026.json")))
api26 = {}
for r in allc26:
    if r["unitId"] == 4:
        api26.setdefault(r["countryCode"], {})[r["attributeId"]] = r["value"]
ns_miss = 0
for cc, attrs in api26.items():
    for aid in (28, 125, 88, 57, 176):
        v = attrs.get(aid)

json.dump({"world": world, "hist": hist, "rank": rank, "delta": delta,
           "ex_cn": {str(k): v for k, v in ex_cn.items()},
           "ex_c2i": {str(k): v for k, v in ex_c2i.items()},
           "stats": stats,
           "vintage": {"psd_alldata": "2026-09-11 快照 (93号同源)", "api": "2026-09-20 实拉(部分 429)"}},
          open(OUT_PATH, "w"), ensure_ascii=False)
print("SAVED", OUT_PATH)
print("rank prod 2026:", [(x["name"], x["val"]) for x in rank["prod"][:8]])
print("rank exp 2026:", [(x["name"], x["val"]) for x in rank["exp"][:8]])
print("stats:", stats)
print("cross:", cross)
