# -*- coding: utf-8 -*-
"""102 号报告：第八章表格与第九章节点中其余数值的权威复核。"""
import csv, io, os, bisect
from datetime import date, timedelta

BASE = r"C:\Users\Administrator\Desktop\农业"
rows = list(csv.DictReader(io.open(os.path.join(BASE, "data/price/sugar/sb_price_daily.csv"), encoding="utf-8-sig")))
d = [r["time"] for r in rows]
C = {r["time"]: float(r["close"]) for r in rows}
H = {r["time"]: float(r["high"]) for r in rows}
L = {r["time"]: float(r["low"]) for r in rows}
cot = list(csv.DictReader(io.open(os.path.join(BASE, "data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"), encoding="utf-8-sig")))
W = [{"d": r["date"], "net": int(r["nc_net"]), "l": int(r["nc_l"]), "s": int(r["nc_s"]), "oi": int(r["oi"])} for r in cot]

out = []
def p(s=""): out.append(str(s))

def seg(a, b): return [r for r in W if a <= r["d"] <= b]

p("=" * 78); p("1. 底部净持仓"); p("=" * 78)
for lbl, a, b in [("2015 底窗 2015-07~2015-09", "2015-07-01", "2015-09-30"),
                  ("2022 底窗 2022-08~2022-10", "2022-08-01", "2022-10-31")]:
    s = seg(a, b)
    mn = min(s, key=lambda r: r["net"])
    p("  %s: 最低净持仓 %s %+d  (正文: -9,651@2015-08-18 / +48,601@2022-09-27)" % (lbl, mn["d"], mn["net"]))
for t in ("2015-08-18", "2022-09-27"):
    r = [x for x in W if x["d"] == t]
    p("    %s -> %s" % (t, ("%+d" % r[0]["net"]) if r else "无此报表日"))

p(); p("=" * 78); p("2. 非商业空头 / 多头峰值"); p("=" * 78)
s = seg("2014-01-01", "2015-12-31"); mx = max(s, key=lambda r: r["s"])
p("  2014-2015 空头峰: %s %d  (正文 271,542@2015-03-31)" % (mx["d"], mx["s"]))
s = seg("2023-01-01", "2024-12-31"); mx = max(s, key=lambda r: r["s"])
p("  2023-2024 空头峰: %s %d  (正文 198,226@2024-05-28)" % (mx["d"], mx["s"]))
s = seg("2016-01-01", "2016-12-31"); mx = max(s, key=lambda r: r["l"])
p("  2016 多头峰: %s %d  (正文 369,812@2016-08-30)" % (mx["d"], mx["l"]))
s = seg("2023-01-01", "2023-12-31"); mx = max(s, key=lambda r: r["l"])
p("  2023 多头峰: %s %d  (正文 354,581@2023-04-25)" % (mx["d"], mx["l"]))
p("  2015-06-23 空头 = %d ; 2017-02-21 空头 = %d" % (
    [x for x in W if x["d"] == "2015-06-23"][0]["s"], [x for x in W if x["d"] == "2017-02-21"][0]["s"]))

p(); p("=" * 78); p("3. 净持仓归零 / 转净空"); p("=" * 78)
after = [r for r in W if r["d"] > "2016-10-05"]
z = next((r for r in after if r["net"] < 0), None)
p("  2016 顶后首次转净空: %s %+d  (正文 2017-08-22 / -68,632)" % (z["d"], z["net"]) if z else "  none")
if z:
    p("     距收盘峰(2016-10-05) %d 天 = %.0f 周" % ((date.fromisoformat(z["d"]) - date(2016, 10, 5)).days,
                                                     (date.fromisoformat(z["d"]) - date(2016, 10, 5)).days / 7))
after = [r for r in W if r["d"] > "2023-11-06"]
z = next((r for r in after if r["net"] < 0), None)
p("  2023 顶后首次转净空: %s %+d  (正文 2024-06-04 / -4,040)" % (z["d"], z["net"]) if z else "  none")
if z:
    p("     距收盘峰(2023-11-06) %d 天 = %.0f 周" % ((date.fromisoformat(z["d"]) - date(2023, 11, 6)).days,
                                                     (date.fromisoformat(z["d"]) - date(2023, 11, 6)).days / 7))
p("  2017-08-22 前后: %s" % [(r["d"], r["net"]) for r in W if "2017-08-08" <= r["d"] <= "2017-09-05"])
p("  2024-06-04 前后: %s" % [(r["d"], r["net"]) for r in W if "2024-05-21" <= r["d"] <= "2024-06-18"])

p(); p("=" * 78); p("4. 中间反弹价位"); p("=" * 78)
for lbl, a, b in [("2016顶后 13 周窗 (至 2017-01-04)", "2016-12-01", "2017-01-10"),
                  ("2017年1-2月反弹窗", "2017-01-01", "2017-02-28"),
                  ("2017-05-22 中国关税落地", "2017-05-15", "2017-05-31"),
                  ("2017-08 (关税后3个月)", "2017-08-15", "2017-08-31"),
                  ("2024年1月反弹窗", "2024-01-01", "2024-02-15")]:
    c = [t for t in d if a <= t <= b]
    if not c: continue
    hi = max(c, key=lambda t: H[t]); hc = max(c, key=lambda t: C[t])
    p("  %s: 盘中高 %s=%.2f | 收盘高 %s=%.2f" % (lbl, hi, H[hi], hc, C[hc]))
p("  正文称: 13周反弹至 20.51 / 2017年1-2月反弹至 20.84 / 关税落地时 16.51、三个月后 13.51 / 2024-01 反弹至 24.13")

p(); p("=" * 78); p("5. 顶后 4 周净多（最近报表周口径）"); p("=" * 78)
for lbl, pk, pkd in [("2015/16", "2016-10-04", "2016-10-05"), ("2023", "2023-11-07", "2023-11-06")]:
    base = [r for r in W if r["d"] == pk][0]
    tgt = date.fromisoformat(pk) + timedelta(days=28)
    nx = [r for r in W if date.fromisoformat(r["d"]) <= tgt][-1]
    p("  %s: 价峰最近报表周 %s net=%+d -> +4周 %s net=%+d = %+.1f%%" % (lbl, pk, base["net"], nx["d"], nx["net"], (nx["net"]/base["net"]-1)*100))
    netpk = max([r for r in W if r["d"] <= pk], key=lambda r: r["net"])
    p("     本轮净多峰 %s %+d -> 价峰最近报表周 = %.1f%% 峰值" % (netpk["d"], netpk["net"], base["net"]/netpk["net"]*100))
    # on-or-before daily peak week
    prevw = [r for r in W if r["d"] <= pkd][-1]
    p("     日线收盘峰 %s 之前最近报表 %s net=%+d = %.1f%% 峰值 (稳健性对照)" % (pkd, prevw["d"], prevw["net"], prevw["net"]/netpk["net"]*100))

p(); p("=" * 78); p("6. 2023-12 净持仓周度崩塌明细"); p("=" * 78)
for r in W:
    if "2023-11-07" <= r["d"] <= "2024-01-16":
        p("  %s net=%+7d (%.1f万)" % (r["d"], r["net"], r["net"]/10000.0))
p("  232,083 -> 74,825 = %+.1f%% (8周)" % ((74825/232083-1)*100))
p("  165,469 -> 74,825 = %+.1f%% (4周)" % ((74825/165469-1)*100))

io.open(os.path.join(BASE, "scripts", "_r102_verify4.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
