# -*- coding: utf-8 -*-
"""
102号报告构建器：2015/16 与 2023 两次白糖牛市全周期复盘
读取项目既有数据（日线价 / CFTC / ISO vintage / USDA PSD 聚合），产出 HTML。
"""
import csv, io, os, json, bisect
from collections import defaultdict

BASE = r"C:\Users\Administrator\Desktop\农业"
OUT  = os.path.join(BASE, "reports", "102_白糖两轮牛市全周期复盘_2015_2023")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- load daily px
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

# ---------------------------------------------------------------- load COT
cot = []
with io.open(os.path.join(BASE, "data", "cftc", "sugar", "sugar_cftc_futonly_1986_2026.csv"),
             encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        q = pon(r["date"])
        cot.append({"d": r["date"], "net": int(r["nc_net"]), "l": int(r["nc_l"]),
                    "s": int(r["nc_s"]), "oi": int(r["oi"]),
                    "c": q[1] if q else None})

def weekly(a, b):
    return [{"d": r["d"], "c": r["c"], "net": r["net"], "l": r["l"], "s": r["s"], "oi": r["oi"]}
            for r in cot if a <= r["d"] <= b and r["c"] is not None]

W15 = weekly("2015-05-01", "2017-12-31")
W23 = weekly("2022-08-01", "2024-06-30")

# ---------------------------------------------------------------- normalized overlay
def norm(lo_date, lo_px, a, b):
    """以 lo_date 收盘价为 100 的归一化序列，x = 距起点的交易日数（每 3 日采样）。"""
    seg = [(t, c) for t, c, h, l in px if a <= t <= b]
    i0 = next(i for i, (t, c) in enumerate(seg) if t >= lo_date)
    out = []
    for k in range(0, len(seg) - i0, 3):
        t, c = seg[i0 + k]
        out.append([k, round(c / lo_px * 100, 2)])
    return out

N15 = norm("2015-08-24", 10.39, "2015-08-24", "2017-06-30")
N23 = norm("2022-10-03", 17.42, "2022-10-03", "2024-05-31")

# ---------------------------------------------------------------- USDA PSD aggregates
with io.open(os.path.join(BASE, "data", "fundamentals", "sugar",
                          "sugar_stock_layers_2014_2025.json"), encoding="utf-8") as f:
    SL = json.load(f)
YEARS = SL["years"]

# ---------------------------------------------------------------- ISO balance + vintage
iso_bal = {}
with io.open(os.path.join(BASE, "data", "fundamentals", "sugar", "iso",
                          "iso_world_balance_2010_2026.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        iso_bal[r["market_year"]] = {
            "prod": float(r["production_mt"]), "cons": float(r["consumption_mt"]),
            "bal": float(r["balance_mt"]), "end": float(r["end_stocks_mt"]) if r["end_stocks_mt"] else None,
            "su": float(r["stock_to_use_pct"]) if r["stock_to_use_pct"] else None}

VINT = {}
with io.open(os.path.join(BASE, "data", "fundamentals", "sugar", "iso",
                          "vintage_path_key_years.json"), encoding="utf-8") as f:
    VINT = json.load(f)

def vpath(my):
    return sorted([[v, x] for v, x in VINT.get(my, {}).items()])

VINTAGE = {my: vpath(my) for my in ["2015/16", "2016/17", "2017/18", "2021/22", "2022/23", "2023/24"]}

# ---------------------------------------------------------------- assemble payload
payload = {
    "W15": W15, "W23": W23, "N15": N15, "N23": N23,
    "years": YEARS,
    "world": SL["world"],
    "locked": SL["locked"],
    "world_end": SL["world_end"],
    "stocks": {c: SL["end"][c] for c in ["BR", "TH", "IN", "CH"]},
    "countries": SL["countries"],
    "iso_bal": iso_bal,
    "vintage": VINTAGE,
    "locked_list": SL["locked_list"],
}

with io.open(os.path.join(BASE, "scripts", "_r102_data.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

# ---------------------------------------------------------------- quick sanity print
chk = []
chk.append("W15 n=%d  W23 n=%d  N15 n=%d  N23 n=%d" % (len(W15), len(W23), len(N15), len(N23)))
chk.append("N15 peak %.1f at day %d" % (max(x[1] for x in N15), max(N15, key=lambda x: x[1])[0]))
chk.append("N23 peak %.1f at day %d" % (max(x[1] for x in N23), max(N23, key=lambda x: x[1])[0]))
for my in VINTAGE:
    p = VINTAGE[my]
    if len(p) >= 2:
        chk.append("%s: %s %+.0f -> %s %+.0f (delta %+.0f)" % (
            my, p[0][0], p[0][1], p[-1][0], p[-1][1], p[-1][1] - p[0][1]))
with io.open(os.path.join(BASE, "scripts", "_r102_chk.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(chk))
print("payload built")
