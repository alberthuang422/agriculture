# -*- coding: utf-8 -*-
"""
厄尔尼诺 → 棕榈油单产/产量 滞后效应量化
方法论：
- 反事实基准 = 前3年均值（不用 YoY，趋势上行期 YoY 会系统性低估减产）——沿用糖项目 skill 纪律
- 滞后扫描 lag = 0..18 月，找 ONI 与单产偏差相关最强的滞后窗
- 事件研究：历次强 EN（峰值≥1.5）后马来西亚/全球单产偏差
- 产出：本轮 2026 EN 对 MY2026/MY2027 的产量冲击区间，与 USDA 预测对比
"""
import json, os, csv
import statistics as st

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fundamentals", "palm"))
PN = os.path.normpath(os.path.join(BASE, "..", "..", "price", "palm"))
IND = json.load(open(os.path.join(BASE, "palm_indicators.json")))

# ---------- ONI 月度化 ----------
SEAS = {"DJF":1,"JFM":2,"FMA":3,"MAM":4,"AMJ":5,"MJJ":6,"JJA":7,"JAS":8,"ASO":9,"SON":10,"OND":11,"NDJ":12}
oni = {}   # "YYYY-MM" -> anom
for line in open(os.path.join(PN, "oni.txt")):
    p = line.split()
    if len(p) == 4 and p[1].isdigit() and p[0] in SEAS:
        # SEAS 标签取季中月为该月代表值（CPC 约定：DJF=12/1/2 季，标签年取起始年）
        yr, mo = int(p[1]), SEAS[p[0]]
        if mo == 12:            # NDJ/OND.. 12 月 → 同年12月
            oni["%d-12" % yr] = float(p[3])
        else:
            oni["%d-%02d" % (yr if mo > 1 else yr, mo)] = float(p[3])
# 补 DJF（跨年：DJF 1950 = 1949-12,1950-01,1950-02）
for line in open(os.path.join(PN, "oni.txt")):
    p = line.split()
    if len(p) == 4 and p[1].isdigit() and p[0] == "DJF":
        yr = int(p[1]); oni["%d-01" % yr] = float(p[3]); oni["%d-02" % yr] = float(p[3])

def oni_at(y, m):
    return oni.get("%d-%02d" % (y, m))

# ---------- 市场年 → 月序列映射 ----------
# 棕榈油 MY = 10月-次年9月。MY2026 = 2026-10 ~ 2027-09
def my_months(my):
    y = int(my)
    return [(y, m) for m in range(10, 13)] + [(y + 1, m) for m in range(1, 10)]

def oni_my_avg(my, lag=0):
    """MY 内 ONI 均值，可整体后移 lag 个月"""
    ms = my_months(my)
    vals = []
    for (y, m) in ms:
        tot = y * 12 + (m - 1) + lag
        vals.append(oni.get("%d-%02d" % (tot // 12, tot % 12 + 1)))
    vals = [v for v in vals if v is not None]
    return st.mean(vals) if vals else None

def peak_oni_window(my, back=6, fwd=6):
    """MY 起始前 back 月 ~ MY 结束后 fwd 月 的 ONI 峰值（捕捉滞后冲击）"""
    ms = my_months(my)
    y0, m0 = ms[0]
    t0 = y0 * 12 + (m0 - 1)
    best, bt = None, None
    for i in range(-back, fwd + 1):
        t = t0 + i
        v = oni.get("%d-%02d" % (t // 12, t % 12 + 1))
        if v is not None and (best is None or v > best):
            best, bt = v, i
    return best, bt

# ---------- 单产偏差（反事实=前3年均值）----------
def series_from(rows, key):
    return {r["my"]: r[key] for r in rows if r.get(key)}

world = IND["world"]
y_w = series_from(world, "yield")          # MT/HA
p_w = series_from(world, "prod")
my_y = series_from(IND["countries"]["MY"], "yield")
id_y = series_from(IND["countries"]["ID"], "yield")
my_p = series_from(IND["countries"]["MY"], "prod")
id_p = series_from(IND["countries"]["ID"], "prod")

def deviation(s, k=3):
    """反事实 = 前 k 年均值；返回 {my: (实际, 反事实, 偏差%, 偏差绝对值)}"""
    ys = sorted(s)
    out = {}
    for i, y in enumerate(ys):
        prev = [s[z] for z in ys[max(0, i - k):i] if s[z]]
        if len(prev) < k: continue
        cf = st.mean(prev)
        out[y] = {"actual": s[y], "cf": cf, "dev_pct": round(100.0 * (s[y] - cf) / cf, 2),
                  "dev_abs": round(s[y] - cf, 4)}
    return out

dev_w_y = deviation(y_w); dev_my_y = deviation(my_y); dev_id_y = deviation(id_y)
dev_my_p = deviation(my_p); dev_id_p = deviation(id_p); dev_w_p = deviation(p_w)

# ---------- 滞后扫描：ONI 与单产偏差相关性 ----------
def pearson(xs, ys):
    n = len(xs)
    if n < 3: return None
    mx, my_ = st.mean(xs), st.mean(ys)
    sx = (sum((x - mx) ** 2 for x in xs)) ** .5
    sy = (sum((y - my_) ** 2 for y in ys)) ** .5
    if sx == 0 or sy == 0: return None
    return sum((x - mx) * (y - my_) for x, y in zip(xs, ys)) / (sx * sy)

print("=" * 78)
print("滞后扫描：MY 内平均 ONI（后移 lag 月）vs 单产偏差%  [反事实=前3年均值]")
print("=" * 78)
print("%-6s %10s %10s %10s   %s" % ("lag月", "全球单产", "马来单产", "印尼单产", "n"))
best = {}
for lag in range(0, 19):
    row = []
    for nm, dv, ysrc in [("world", dev_w_y, y_w), ("MY", dev_my_y, my_y), ("ID", dev_id_y, id_y)]:
        xs, ys = [], []
        for my_ in sorted(dv):
            o = oni_my_avg(my_, lag)
            if o is None: continue
            xs.append(o); ys.append(dv[my_]["dev_pct"])
        r = pearson(xs, ys)
        row.append((r, len(xs)))
        best.setdefault(nm, []).append((lag, r, len(xs)))
    print("%-6d %10s %10s %10s   %d" % (
        lag, "%.3f" % row[0][0] if row[0][0] else "n/a",
        "%.3f" % row[1][0] if row[1][0] else "n/a",
        "%.3f" % row[2][0] if row[2][0] else "n/a", row[0][1]))

for nm in best:
    valid = [(l, r, n) for l, r, n in best[nm] if r is not None and n >= 8]
    if valid:
        l, r, n = min(valid, key=lambda x: x[1])   # 最负相关
        print("  → %s 单产：最强负相关 lag=%d 月, r=%.3f (n=%d)" % (nm, l, r, n))

# ---------- 事件研究：强 EN 后单产偏差 ----------
print()
print("=" * 78)
print("事件研究：强厄尔尼诺（MY窗口内 ONI 峰值 ≥ 1.5）后的单产偏差%")
print("=" * 78)
print("%-8s %8s %10s %10s %10s %10s" % ("MY", "峰值ONI", "峰值位", "全球单产", "马来单产", "印尼单产"))
ev = []
for my_ in sorted(set(dev_w_y) & set(dev_my_y)):
    pk, off = peak_oni_window(my_, back=6, fwd=6)
    if pk is not None and pk >= 1.5:
        wv = dev_w_y.get(my_, {}).get("dev_pct")
        mv = dev_my_y.get(my_, {}).get("dev_pct")
        iv = dev_id_y.get(my_, {}).get("dev_pct")
        ev.append({"my": my_, "peak_oni": pk, "peak_offset_my_start": off,
                   "world_yield_dev": wv, "my_yield_dev": mv, "id_yield_dev": iv,
                   "world_prod_dev": dev_w_p.get(my_, {}).get("dev_pct"),
                   "my_prod_dev": dev_my_p.get(my_, {}).get("dev_pct"),
                   "id_prod_dev": dev_id_p.get(my_, {}).get("dev_pct")})
        print("%-8s %8.2f %10s %10s %10s %10s" % (
            my_, pk, "%+d月" % off,
            "%+.1f" % wv if wv is not None else "-",
            "%+.1f" % mv if mv is not None else "-",
            "%+.1f" % iv if iv is not None else "-"))

print()
for lbl, key in [("全球单产", "world_yield_dev"), ("马来单产", "my_yield_dev"),
                 ("印尼单产", "id_yield_dev"), ("马来产量", "my_prod_dev")]:
    vs = [e[key] for e in ev if e[key] is not None]
    if vs:
        print("  %s：n=%d  均值 %+.1f%%  中位 %+.1f%%  区间 [%+.1f, %+.1f]  为负次数 %d/%d" % (
            lbl, len(vs), st.mean(vs), st.median(vs), min(vs), max(vs),
            sum(1 for v in vs if v < 0), len(vs)))

# ---------- 本轮事件定位 ----------
print()
print("=" * 78)
print("本轮厄尔尼诺定位")
print("=" * 78)
cur = [oni.get(k) for k in ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]]
print("  ONI 2026-06..12:", ["%+.2f" % v if v is not None else "n/a" for v in cur])
for my_ in ["2025", "2026", "2027"]:
    pk, off = peak_oni_window(my_, back=8, fwd=14)
    o = oni_my_avg(my_, 0)
    yy = int(my_)
    print("  MY%s (%d-10~%d-09): MY内ONI均值 %s | 窗口峰值ONI %s @ 相对MY起点 %+d月" % (
        my_, yy, yy + 1, "%+.2f" % o if o is not None else "n/a",
        "%+.2f" % pk if pk is not None else "n/a", off if off is not None else 0))
    # 滞后传导窗口：峰值月 + 9~12 个月
    if pk is not None and off is not None:
        t0 = yy * 12 + 9 + off          # MY 起点(10月)的绝对月序 + off
        for lg in (9, 12):
            t = t0 + lg
            print("       └ 峰值 %+d月 → +%d月滞后 = %d年%02d月（落在 MY%d）" % (
                off, lg, t // 12, t % 12 + 1, t // 12 - (1 if t % 12 + 1 < 10 else 0)))

# 历史类比：MY内ONI均值 vs 次年单产偏差
print()
print("  历史 MY内ONI均值 ≥ +1.0 的年份及后续单产偏差：")
for my_ in sorted(dev_w_y):
    o = oni_my_avg(my_, 0)
    if o is not None and o >= 1.0:
        nxt = str(int(my_) + 1)
        print("    MY%s (ONI %+.2f) → 当年全球单产偏差 %s | 次年 MY%s 偏差 %s" % (
            my_, o,
            "%+.1f%%" % dev_w_y[my_]["dev_pct"] if my_ in dev_w_y else "-",
            nxt, "%+.1f%%" % dev_w_y[nxt]["dev_pct"] if nxt in dev_w_y else "-"))

json.dump({"events": ev, "oni_monthly": oni,
           "lag_scan": {nm: [(l, r, n) for l, r, n in v] for nm, v in best.items()},
           "deviation_world_yield": dev_w_y, "deviation_my_yield": dev_my_y,
           "deviation_id_yield": dev_id_y, "deviation_my_prod": dev_my_p,
           "deviation_id_prod": dev_id_p, "deviation_world_prod": dev_w_p},
          open(os.path.join(BASE, "palm_enso_lag.json"), "w"), ensure_ascii=False, indent=1)
print("\nsaved ->", os.path.join(BASE, "palm_enso_lag.json"))

# ---------- 附：P-D 价差口径分段检验 ----------
# 世行 Description 页实测：棕榈油 2021-01~2024-10 = RBD FOB Malaysia Ports；
# 2024-11 起 = 5% Bulk CIF NW Europe；2001-12~2020-12 = RBD CIF Rotterdam
# 豆油 2021-01 起 = Dutch Soyoil Crude Degummed EXW Dutch Mills；1999-01~2020-12 = FOB NW Europe
# ⇒ 价差跨期口径不一致，分位必须分段计算
print()
print("=" * 78)
print("P-D 价差口径分段检验（豆油 − 棕榈油，$/mt）")
print("=" * 78)
pm = {r["ym"]: r for r in IND["price_monthly"] if r.get("pd_spread") is not None}
segs = [("1960-1998 早期(马5%CIF NWE vs FOB NL)", "1960-01", "1998-12"),
        ("1999-2020/12 (RBD CIF Rotterdam vs FOB NWE)", "1999-01", "2020-12"),
        ("2021-01~2024-10 (RBD FOB Malaysia vs EXW Dutch)", "2021-01", "2024-10"),
        ("2024-11~ 现行 (5%Bulk CIF NWE vs EXW Dutch)", "2024-11", "2099-12")]
cur = None
for ym, r in sorted(pm.items()):
    pass
for nm, a, b in segs:
    vs = [r["pd_spread"] for ym, r in pm.items() if a <= ym <= b]
    if len(vs) < 6:
        print("  %-52s n=%d 样本不足" % (nm, len(vs))); continue
    print("  %-52s n=%3d mean %+7.0f median %+7.0f 区间 [%+.0f, %+.0f]" % (
        nm, len(vs), st.mean(vs), st.median(vs), min(vs), max(vs)))
    cur = vs
latest_ym = sorted(pm)[-1]
lat = pm[latest_ym]["pd_spread"]
def pr(s, v):
    return round(100.0 * (sum(1 for x in s if x < v) + .5) / len(s), 1)
print()
print("  最新 %s = %+.0f $/mt" % (latest_ym, lat))
print("    → 全样本分位        %.1f%%  (n=%d)" % (pr([v["pd_spread"] for v in pm.values()], lat), len(pm)))
print("    → 现行口径段分位    %.1f%%  (n=%d) ← 唯一可比口径" % (pr(cur, lat), len(cur)))
print("    → 2021以来分位      %.1f%%" % pr([v["pd_spread"] for ym, v in pm.items() if ym >= "2021-01"], lat))
print()
print("  ⚠ 2024-11 口径切换造成水平跳变：切换前后 3 个月均值")
for ym in sorted(pm):
    if "2024-08" <= ym <= "2025-02":
        print("     %s  palm %s  soy %s  spread %+.0f" % (
            ym, pm[ym].get("palm"), pm[ym].get("soy"), pm[ym]["pd_spread"]))
