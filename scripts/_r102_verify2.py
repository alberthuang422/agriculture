# -*- coding: utf-8 -*-
"""102 号报告：争议数字的权威口径重算（供正文对齐用）。全部从原始 CSV 直接计算。"""
import csv, io, json, os, bisect
from datetime import date, timedelta

BASE = r"C:\Users\Administrator\Desktop\农业"
rows = list(csv.DictReader(io.open(os.path.join(BASE, "data/price/sugar/sb_price_daily.csv"),
                                   encoding="utf-8-sig")))
d = [r["time"] for r in rows]
C = {r["time"]: float(r["close"]) for r in rows}
H = {r["time"]: float(r["high"]) for r in rows}
L = {r["time"]: float(r["low"]) for r in rows}
cot = list(csv.DictReader(io.open(os.path.join(BASE, "data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"),
                                  encoding="utf-8-sig")))
W = []
for r in cot:
    i = bisect.bisect_right(d, r["date"]) - 1
    if i < 0:
        continue
    W.append({"d": r["date"], "net": int(r["nc_net"]), "l": int(r["nc_l"]), "s": int(r["nc_s"]),
              "oi": int(r["oi"]), "c": C[d[i]]})
wmap = {r["d"]: r for r in W}

out = []
def p(s=""): out.append(str(s))

def weekrow(dt):
    """CFTC report row on-or-before dt."""
    c = [r for r in W if r["d"] <= dt]
    return c[-1] if c else None

p("=" * 78)
p("1. 2016 年 10 月顶部：周度持仓明细 + 对应收盘")
p("=" * 78)
for r in W:
    if "2016-09-13" <= r["d"] <= "2016-11-15":
        p("  %s  net=%+7d  L=%6d  S=%6d  OI=%7d  close(报表日)=%.2f" % (r["d"], r["net"], r["l"], r["s"], r["oi"], r["c"]))
p()
p("  2016-10 每日收盘:")
for t in d:
    if "2016-10-03" <= t <= "2016-10-14":
        p("     %s  close=%.2f  high=%.2f  low=%.2f" % (t, C[t], H[t], L[t]))
p()
pk16 = max([(t, C[t]) for t in d if "2016-01-01" <= t <= "2016-12-31"], key=lambda x: x[1])
p("  2016 收盘峰 = %s %.2f" % pk16)
pk16i = max([(t, H[t]) for t in d if "2016-01-01" <= t <= "2016-12-31"], key=lambda x: x[1])
p("  2016 盘中峰 = %s %.2f" % pk16i)
netpk16 = max([r for r in W if "2016-01-01" <= r["d"] <= "2016-12-31"], key=lambda r: r["net"])
p("  净多峰 = %s %+d" % (netpk16["d"], netpk16["net"]))
for lbl, dt in [("收盘峰日", pk16[0]), ("盘中峰日", pk16i[0])]:
    r = weekrow(dt)
    p("  %s(%s) 对应周 %s: net=%+d  = 峰值 %.1f%%  | 净多峰领先 %d 天"
      % (lbl, dt, r["d"], r["net"], r["net"] / netpk16["net"] * 100,
         (date.fromisoformat(dt) - date.fromisoformat(netpk16["d"])).days))
    r2 = [x for x in W if x["d"] >= dt][0]
    p("     价峰之后第一个周度 %s: net=%+d = 峰值 %.1f%%" % (r2["d"], r2["net"], r2["net"] / netpk16["net"] * 100))

p()
p("=" * 78)
p("2. 2023 年 11 月顶部：周度持仓明细 + 对应收盘")
p("=" * 78)
for r in W:
    if "2023-10-10" <= r["d"] <= "2023-12-19":
        p("  %s  net=%+7d  L=%6d  S=%6d  OI=%7d  close(报表日)=%.2f" % (r["d"], r["net"], r["l"], r["s"], r["oi"], r["c"]))
p()
p("  2023-11 每日收盘:")
for t in d:
    if "2023-11-01" <= t <= "2023-11-15":
        p("     %s  close=%.2f  high=%.2f  low=%.2f" % (t, C[t], H[t], L[t]))
p()
pk23 = max([(t, C[t]) for t in d if "2023-01-01" <= t <= "2023-12-31"], key=lambda x: x[1])
pk23i = max([(t, H[t]) for t in d if "2023-01-01" <= t <= "2023-12-31"], key=lambda x: x[1])
netpk23 = max([r for r in W if "2023-01-01" <= r["d"] <= "2023-12-31"], key=lambda r: r["net"])
p("  2023 收盘峰 = %s %.2f | 盘中峰 = %s %.2f | 净多峰 = %s %+d" % (pk23[0], pk23[1], pk23i[0], pk23i[1], netpk23["d"], netpk23["net"]))
for lbl, dt in [("收盘峰日", pk23[0]), ("盘中峰日", pk23i[0])]:
    r = weekrow(dt)
    p("  %s(%s) 对应周 %s: net=%+d = 峰值 %.1f%%  | 净多峰领先 %d 天"
      % (lbl, dt, r["d"], r["net"], r["net"] / netpk23["net"] * 100,
         (date.fromisoformat(dt) - date.fromisoformat(netpk23["d"])).days))
    r2 = [x for x in W if x["d"] >= dt][0]
    p("     价峰之后第一个周度 %s: net=%+d = 峰值 %.1f%%" % (r2["d"], r2["net"], r2["net"] / netpk23["net"] * 100))
p()
wa, wn = wmap["2023-04-25"], wmap["2023-11-07"]
p("  空头 04-25=%d -> 11-07=%d = %+.1f%% | 多头 %+.1f%% | 净多 %+.1f%%"
  % (wa["s"], wn["s"], (wn["s"] / wa["s"] - 1) * 100, (wn["l"] / wa["l"] - 1) * 100, (wn["net"] / wa["net"] - 1) * 100))
p("  OI  04-25=%d -> 11-07=%d = %+.1f%%" % (wa["oi"], wn["oi"], (wn["oi"] / wa["oi"] - 1) * 100))

p()
p("=" * 78)
p("3. 月度环比（月末收盘）——核对 '-16.4% 单月'")
p("=" * 78)
def month_end(y, m):
    c = [t for t in d if t.startswith("%04d-%02d" % (y, m))]
    return (c[-1], C[c[-1]]) if c else (None, None)
for (y, m) in [(2023, 9), (2023, 10), (2023, 11), (2023, 12), (2024, 1),
               (2016, 9), (2016, 10), (2016, 11), (2016, 12), (2017, 1), (2017, 2), (2017, 3)]:
    t, v = month_end(y, m)
    p("  %s 月末 %s = %.2f" % ("%04d-%02d" % (y, m), t, v))
p()
n_end = month_end(2023, 11); dec_end = month_end(2023, 12)
p("  2023-12 单月环比 = %+.2f%%  (Nov %.2f -> Dec %.2f)" % ((dec_end[1] / n_end[1] - 1) * 100, n_end[1], dec_end[1]))
o_end = month_end(2023, 10)
p("  2023-10月末 -> 12月末 = %+.2f%%" % ((dec_end[1] / o_end[1] - 1) * 100))

p()
p("=" * 78)
p("4. 见顶后 N 周路径（以收盘峰为基准）")
p("=" * 78)
def path(peak_date, weeks=(4, 8, 13, 26, 52)):
    base = C[peak_date]
    res = []
    for wk in weeks:
        tgt = date.fromisoformat(peak_date) + timedelta(days=wk * 7)
        c = [t for t in d if date.fromisoformat(t) <= tgt]
        if not c: continue
        t2 = c[-1]
        res.append((wk, t2, C[t2], (C[t2] / base - 1) * 100))
    return base, res
for lbl, pk in [("2016-10-05 收盘峰", pk16[0]), ("2023-11-06 收盘峰", pk23[0])]:
    base, res = path(pk)
    p("  %s (%s, base=%.2f):" % (lbl, pk, base))
    for wk, t2, v, ch in res:
        p("     %+3d 周 -> %s  %.2f  = %+.1f%%" % (wk, t2, v, ch))
p()
p("  注: 2016 收盘峰(2016-10-05) 与 2023 收盘峰(2023-11-06) 为各自年度最高收盘。")

p()
p("=" * 78)
p("5. ISO 2022/23 vintage vs 终值")
p("=" * 78)
V = json.load(io.open(os.path.join(BASE, "data/fundamentals/sugar/iso/vintage_path_key_years.json"), encoding="utf-8"))
iso_bal = {}
with io.open(os.path.join(BASE, "data/fundamentals/sugar/iso/iso_world_balance_2010_2026.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        iso_bal[r["market_year"]] = r
for my in ("2015/16", "2022/23", "2023/24"):
    pp = sorted(V[my].items())
    p("  %s vintage 矩阵: %s" % (my, " ".join("%s=%+.0f" % (k, v) for k, v in pp)))
    r = iso_bal.get(my, {})
    fin = r.get("balance_mt")
    p("     iso_world_balance 终值 = %s Mt (%+.0f kt) | 首版 %+.0f -> 终值 %+.0f = 修订 %+.0f kt"
      % (fin, float(fin) * 1000, pp[0][1], float(fin) * 1000, float(fin) * 1000 - pp[0][1]))
    p("     矩阵末版(%s)=%+.0f -> 终值 %+.0f = 额外 %+.0f kt" % (pp[-1][0], pp[-1][1], float(fin) * 1000, float(fin) * 1000 - pp[-1][1]))
p()
p("  iso_world_balance 列名: %s" % list(iso_bal["2022/23"].keys()))
for my in ("2015/16", "2016/17", "2022/23", "2023/24"):
    r = iso_bal[my]
    p("     %s: prod=%s cons=%s bal=%s end=%s su=%s" % (my, r.get("production_mt"), r.get("consumption_mt"),
                                                        r.get("balance_mt"), r.get("end_stocks_mt"), r.get("stock_to_use_pct")))

io.open(os.path.join(BASE, "scripts", "_r102_verify2.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
