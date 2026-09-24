# -*- coding: utf-8 -*-
"""102 号报告：崩塌路径 / 锁定层区间 / 周度净持仓明细 的权威重算。"""
import csv, io, json, os, bisect
from datetime import date, timedelta

BASE = r"C:\Users\Administrator\Desktop\农业"
rows = list(csv.DictReader(io.open(os.path.join(BASE, "data/price/sugar/sb_price_daily.csv"), encoding="utf-8-sig")))
d = [r["time"] for r in rows]
C = {r["time"]: float(r["close"]) for r in rows}
H = {r["time"]: float(r["high"]) for r in rows}
cot = list(csv.DictReader(io.open(os.path.join(BASE, "data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"), encoding="utf-8-sig")))
W = []
for r in cot:
    i = bisect.bisect_right(d, r["date"]) - 1
    if i >= 0:
        W.append({"d": r["date"], "net": int(r["nc_net"]), "l": int(r["nc_l"]), "s": int(r["nc_s"]), "oi": int(r["oi"])})

out = []
def p(s=""): out.append(str(s))

p("=" * 78); p("1. 2023-11 ~ 2024-02 周度净持仓与收盘（核对 '-67.8%' 与 '16.5万->7.5万'）"); p("=" * 78)
for r in W:
    if "2023-11-07" <= r["d"] <= "2024-02-20":
        p("  %s  net=%+7d (%.1f万)  L=%6d  S=%6d  OI=%7d" % (r["d"], r["net"], r["net"]/10000.0, r["l"], r["s"], r["oi"]))
base = 232083
p()
for r in W:
    if "2023-11-07" < r["d"] <= "2024-01-31":
        p("  %s: net 相对 11-07 峰值 %+.1f%%" % (r["d"], (r["net"]/base - 1)*100))

p(); p("=" * 78); p("2. 2016-09 ~ 2017-01 周度净持仓"); p("=" * 78)
for r in W:
    if "2016-09-27" <= r["d"] <= "2017-01-31":
        p("  %s  net=%+7d (%.1f万)  L=%6d  S=%6d  OI=%7d" % (r["d"], r["net"], r["net"]/10000.0, r["l"], r["s"], r["oi"]))

p(); p("=" * 78); p("3. 见顶后路径（基准=收盘峰；+N周=该自然日或之前最后交易日）"); p("=" * 78)
def path(pk, weeks):
    b = C[pk]; res = []
    for wk in weeks:
        tgt = date.fromisoformat(pk) + timedelta(days=wk*7)
        c = [t for t in d if date.fromisoformat(t) <= tgt]
        if c: res.append((wk, c[-1], C[c[-1]], (C[c[-1]]/b - 1)*100))
    return b, res
for lbl, pk in [("2016-10-05", "2016-10-05"), ("2023-11-06", "2023-11-06")]:
    b, res = path(pk, (2, 4, 8, 13, 26, 52))
    p("  %s 收盘峰 base=%.2f" % (lbl, b))
    for wk, t2, v, ch in res:
        p("     %+3d 周 -> %s  %6.2f  = %+6.1f%%" % (wk, t2, v, ch))
p()
p("  盘中峰口径对照:")
for lbl, pk in [("2016-10-06 盘中23.90", "2016-10-06"), ("2023-11-07 盘中28.14", "2023-11-07")]:
    b = H[pk]; _, res = path(pk, (4, 8))
    p("    %s base(high)=%.2f -> 4周 %+.1f%% / 8周 %+.1f%%" % (lbl, b, res[0][3], res[1][3]))

p(); p("=" * 78); p("4. 月度环比（月末收盘）"); p("=" * 78)
def me(y, m):
    c = [t for t in d if t.startswith("%04d-%02d" % (y, m))]
    return (c[-1], C[c[-1]]) if c else (None, None)
seq = [(2016,9),(2016,10),(2016,11),(2016,12),(2017,1),(2017,2),(2017,3),(2017,4),
       (2023,9),(2023,10),(2023,11),(2023,12),(2024,1),(2024,2)]
prev = None
for y, m in seq:
    t, v = me(y, m)
    ch = "" if prev is None else "  环比 %+6.2f%%" % ((v/prev[1]-1)*100)
    p("  %04d-%02d 月末 %s = %6.2f%s" % (y, m, t, v, ch))
    if (y, m) in [(2017,4), (2023,9)]:
        prev = None
        p("  ---")
        continue
    prev = (t, v)
p()
n = me(2023, 11); dc = me(2023, 12)
p("  2023-12 单月环比(月末收盘) = %+.2f%%   [外部引用 Mysteel -16.44%% / FAO -16.6%%]" % ((dc[1]/n[1]-1)*100))
# 月均价口径
def mavg(y, m):
    v = [C[t] for t in d if t.startswith("%04d-%02d" % (y, m))]
    return sum(v)/len(v) if v else None
a11, a12 = mavg(2023,11), mavg(2023,12)
p("  2023 月均价: 11月=%.2f  12月=%.2f  -> 环比 %+.2f%%" % (a11, a12, (a12/a11-1)*100))

p(); p("=" * 78); p("5. 锁定层 / 残差层 全区间（核对 '70-77%%' 与 '11.7-15.7 Mt'）"); p("=" * 78)
SL = json.load(io.open(os.path.join(BASE, "data/fundamentals/sugar/sugar_stock_layers_2014_2025.json"), encoding="utf-8"))
sh, rh = [], []
p("  MY   期末库存   锁定层   锁定占比   残差层   库消比")
for y in SL["years"]:
    k = str(y); we = SL["world_end"][k]; lk = SL["locked"][k]; rs = we - lk
    w = SL["world"][k]; su = w["end"]/w["disp"]*100
    sh.append(lk/we*100); rh.append(rs)
    p("  %s  %8d  %8d   %5.1f%%  %8d   %5.1f%%" % (k, we, lk, lk/we*100, rs, su))
p()
p("  锁定层占比区间: %.1f%% ~ %.1f%%   (正文称 70-77%%)" % (min(sh), max(sh)))
p("  残差层区间: %.0f ~ %.0f kt = %.1f ~ %.1f Mt   (正文称 11.7-15.7 Mt)" % (min(rh), max(rh), min(rh)/1000.0, max(rh)/1000.0))

io.open(os.path.join(BASE, "scripts", "_r102_verify3.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
