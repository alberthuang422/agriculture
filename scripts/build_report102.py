# -*- coding: utf-8 -*-
"""
102号报告：2015/16 与 2023 两次白糖牛市全周期复盘
一次性构建：数据聚合 -> HTML 生成
"""
import csv, io, os, json, bisect
from collections import defaultdict

BASE = r"C:\Users\Administrator\Desktop\农业"
OUTD = os.path.join(BASE, "reports", "102_白糖两轮牛市全周期复盘_2015_2023")
os.makedirs(OUTD, exist_ok=True)

# ================================================================ 1. 数据加载
px = []
with io.open(os.path.join(BASE, "data", "price", "sugar", "sb_price_daily.csv"),
             encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        px.append((r["time"], float(r["close"]), float(r["high"]), float(r["low"])))
pdates = [x[0] for x in px]
pmap = {x[0]: x for x in px}

def pon(dt):
    i = bisect.bisect_right(pdates, dt) - 1
    return pmap[pdates[i]] if i >= 0 else None

cot = []
with io.open(os.path.join(BASE, "data", "cftc", "sugar", "sugar_cftc_futonly_1986_2026.csv"),
             encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        q = pon(r["date"])
        cot.append({"d": r["date"], "net": int(r["nc_net"]), "l": int(r["nc_l"]),
                    "s": int(r["nc_s"]), "oi": int(r["oi"]), "c": q[1] if q else None})

def weekly(a, b):
    return [{"d": r["d"], "c": r["c"], "net": r["net"], "l": r["l"], "s": r["s"], "oi": r["oi"]}
            for r in cot if a <= r["d"] <= b and r["c"] is not None]

W15 = weekly("2015-05-01", "2017-12-31")
W23 = weekly("2022-08-01", "2024-06-30")

def norm(lo_date, lo_px, a, b):
    seg = [(t, c) for t, c, h, l in px if a <= t <= b]
    i0 = next(i for i, (t, c) in enumerate(seg) if t >= lo_date)
    return [[k, round(seg[i0 + k][1] / lo_px * 100, 2)] for k in range(len(seg) - i0)]

N15 = norm("2015-08-24", 10.39, "2015-08-24", "2017-06-30")
N23 = norm("2022-10-03", 17.42, "2022-10-03", "2024-05-31")

# 榨季均价（10月-次年9月）
season_avg = {}
for y in range(2014, 2026):
    a, b = "%d-10-01" % y, "%d-09-30" % (y + 1)
    v = [c for t, c, h, l in px if a <= t <= b]
    season_avg[y] = round(sum(v) / len(v), 2) if v else None

with io.open(os.path.join(BASE, "data", "fundamentals", "sugar",
                          "sugar_stock_layers_2014_2025.json"), encoding="utf-8") as f:
    SL = json.load(f)

iso_bal = {}
with io.open(os.path.join(BASE, "data", "fundamentals", "sugar", "iso",
                          "iso_world_balance_2010_2026.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        iso_bal[r["market_year"]] = {
            "prod": float(r["production_mt"]), "cons": float(r["consumption_mt"]),
            "bal": float(r["balance_mt"]),
            "end": float(r["end_stocks_mt"]) if r["end_stocks_mt"] else None,
            "su": float(r["stock_to_use_pct"]) if r["stock_to_use_pct"] else None}

with io.open(os.path.join(BASE, "data", "fundamentals", "sugar", "iso",
                          "vintage_path_key_years.json"), encoding="utf-8") as f:
    VRAW = json.load(f)
VINTAGE = {my: sorted([[v, x] for v, x in VRAW.get(my, {}).items()])
           for my in ["2015/16", "2016/17", "2017/18", "2021/22", "2022/23", "2023/24"]}

P = {"W15": W15, "W23": W23, "N15": N15, "N23": N23,
     "years": SL["years"], "world": SL["world"], "locked": SL["locked"],
     "world_end": SL["world_end"], "stocks": {c: SL["end"][c] for c in ["BR", "TH", "IN", "CH"]},
     "iso_bal": iso_bal, "vintage": VINTAGE, "savg": season_avg}

# ================================================================ 2. HTML 部件
J = lambda o: json.dumps(o, ensure_ascii=False)

with io.open(os.path.join(BASE, "scripts", "_r102_css.txt"), encoding="utf-8") as f:
    CSS = f.read()
with io.open(os.path.join(BASE, "scripts", "_r102_body.txt"), encoding="utf-8") as f:
    BODY = f.read()
with io.open(os.path.join(BASE, "scripts", "_r102_js.txt"), encoding="utf-8") as f:
    JS = f.read()

HTML = ("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>102号 · 白糖两轮牛市全周期复盘（2015/16 与 2023）</title>\n"
        "<script src=\"https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js\"></script>\n"
        "<style>" + CSS + "</style>\n</head>\n<body>\n<div class=\"wrap\">\n"
        + BODY +
        "\n</div>\n<script>\nvar P = " + J(P) + ";\n" + JS + "\n</script>\n</body>\n</html>\n")

with io.open(os.path.join(OUTD, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("HTML written: %d bytes" % len(HTML))
