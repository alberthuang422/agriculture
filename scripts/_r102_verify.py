# -*- coding: utf-8 -*-
"""独立复核 102 号报告正文中的关键论断数字（不复用构建脚本逻辑）。"""
import csv, io, json, os, bisect
from datetime import date

BASE = r"C:\Users\Administrator\Desktop\农业"
out = []
rows = list(csv.DictReader(io.open(os.path.join(BASE, "data/price/sugar/sb_price_daily.csv"),
                                   encoding="utf-8-sig")))
d = [r["time"] for r in rows]
C = {r["time"]: float(r["close"]) for r in rows}
cot = list(csv.DictReader(io.open(os.path.join(BASE, "data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"),
                                  encoding="utf-8-sig")))

def pon(dt):
    i = bisect.bisect_right(d, dt) - 1
    return C[d[i]] if i >= 0 else None

W = [{"d": r["date"], "net": int(r["nc_net"]), "l": int(r["nc_l"]), "s": int(r["nc_s"])}
     for r in cot if pon(r["date"]) is not None]
wmap = {r["d"]: r for r in W}

def line(s):
    out.append(s)

line("=" * 74)
line("A. 2023 双顶背离：净多峰 vs 价峰")
line("=" * 74)
net_peak = max([r for r in W if "2023-01-01" <= r["d"] <= "2023-12-31"], key=lambda r: r["net"])
line("2023 年内净多峰: %s  net=%d" % (net_peak["d"], net_peak["net"]))
# price peak by close in 2023
pp = max([(t, C[t]) for t in d if "2023-01-01" <= t <= "2023-12-31"], key=lambda x: x[1])
line("2023 年内收盘峰: %s  close=%.2f" % pp)
# weekly row at/after price peak
cand = [r for r in W if r["d"] <= pp[0]]
wp = cand[-1]
line("价峰周持仓(%s): net=%d  long=%d  short=%d" % (wp["d"], wp["net"], wp["l"], wp["s"]))
line("净多/峰值 = %.1f%%   -> 低于峰值 %.1f%%  (正文称 79.5%% / -17.0%%)"
     % (wp["net"] / net_peak["net"] * 100, (1 - wp["net"] / net_peak["net"]) * 100))
# short change: April peak week vs Nov peak week
wa = wmap["2023-04-25"]; wn = wmap["2023-11-07"]
line("空头 2023-04-25=%d -> 2023-11-07=%d  = %+.1f%%  (正文称 +27.8%%)"
     % (wa["s"], wn["s"], (wn["s"] / wa["s"] - 1) * 100))
line("多头 2023-04-25=%d -> 2023-11-07=%d  = %+.1f%%" % (wa["l"], wn["l"], (wn["l"] / wa["l"] - 1) * 100))
line("净多 2023-04-25=%d -> 2023-11-07=%d  = %+.1f%%" % (wa["net"], wn["net"], (wn["net"] / wa["net"] - 1) * 100))
line("领先天数(净多峰->价峰): %d 天  (正文称 210 天)"
     % (date.fromisoformat(pp[0]) - date.fromisoformat(net_peak["d"])).days)

line("")
line("=" * 74)
line("B. 2015/16 趋势顶：净多峰 vs 价峰")
line("=" * 74)
np15 = max([r for r in W if "2016-01-01" <= r["d"] <= "2016-12-31"], key=lambda r: r["net"])
line("2016 年内净多峰: %s  net=%d" % (np15["d"], np15["net"]))
pp15 = max([(t, C[t]) for t in d if "2016-01-01" <= t <= "2016-12-31"], key=lambda x: x[1])
line("2016 年内收盘峰: %s  close=%.2f" % pp15)
w15 = [r for r in W if r["d"] <= pp15[0]][-1]
line("价峰周持仓(%s): net=%d" % (w15["d"], w15["net"]))
line("净多/峰值 = %.1f%%  (正文称 95.4%%)" % (w15["net"] / np15["net"] * 100))
line("领先天数: %d 天  (正文称 14 天)"
     % (date.fromisoformat(pp15[0]) - date.fromisoformat(np15["d"])).days)
# short squeeze 2015-06-23 -> 2017-02-21
def near(t):
    return min([r for r in W], key=lambda r: abs((date.fromisoformat(r["d"]) - date.fromisoformat(t)).days))
a = near("2015-06-23"); b = near("2017-02-21")
line("空头 %s=%d -> %s=%d  = %+.1f%%  (正文称 -89.7%%)" % (a["d"], a["s"], b["d"], b["s"], (b["s"] / a["s"] - 1) * 100))

line("")
line("=" * 74)
line("C. 崩塌速度")
line("=" * 74)
# 2023: Nov 7 peak -> Dec monthly change
seg = [(t, C[t]) for t in d if "2023-11-01" <= t <= "2024-01-31"]
nov_pk = max([(t, C[t]) for t in d if "2023-11-01" <= t <= "2023-11-30"], key=lambda x: x[1])
dec_end = max([(t, C[t]) for t in d if t <= "2023-12-31"], key=lambda x: x[0])
oct_end = max([(t, C[t]) for t in d if t <= "2023-10-31"], key=lambda x: x[0])
line("2023-10 月末 %s=%.2f | 2023-11 收盘峰 %s=%.2f | 2023-12 月末 %s=%.2f"
     % (oct_end[0], oct_end[1], nov_pk[0], nov_pk[1], dec_end[0], dec_end[1]))
line("12月单月跌幅(月末对月末) = %+.1f%%  (正文称 -16.4%%)" % ((dec_end[1] / oct_end[1] - 1) * 100))
line("11月收盘峰->12月末 = %+.1f%%" % ((dec_end[1] / nov_pk[1] - 1) * 100))
# 2016: Oct peak -> 3 months
p16 = max([(t, C[t]) for t in d if "2016-10-01" <= t <= "2016-10-31"], key=lambda x: x[1])
e16 = max([(t, C[t]) for t in d if t <= "2017-01-31"], key=lambda x: x[0])
line("2016-10 收盘峰 %s=%.2f -> 2017-01 月末 %s=%.2f = %+.1f%%  (正文称 3个月 -27.7%%)"
     % (p16[0], p16[1], e16[0], e16[1], (e16[1] / p16[1] - 1) * 100))

line("")
line("=" * 74)
line("D. 库存分层（sugar_stock_layers_2014_2025.json）")
line("=" * 74)
SL = json.load(io.open(os.path.join(BASE, "data/fundamentals/sugar/sugar_stock_layers_2014_2025.json"),
                       encoding="utf-8"))
line("keys: %s" % sorted(SL.keys()))
for y in ("2015", "2022", "2023"):
    w = SL["world"][y]; lk = SL["locked"][y]; we = SL["world_end"][y]
    res = we - lk
    line("MY%s: 期末=%d  锁定层=%d (%.1f%%)  残差层=%d  库消比=%.1f%%"
         % (y, we, lk, lk / we * 100, res, w["end"] / w["disp"] * 100))
line("正文称: 锁定层占 70-77%%; 残差层 MY2015=12,547 / MY2022=12,803 kt; 库消比 25.8%% vs 25.7%%")
line("锁定层国家: %s" % SL.get("locked_countries", SL.get("locked_list", "?")))

line("")
line("=" * 74)
line("E. ISO vintage 修订路径")
line("=" * 74)
V = json.load(io.open(os.path.join(BASE, "data/fundamentals/sugar/iso/vintage_path_key_years.json"),
                      encoding="utf-8"))
for my in ("2015/16", "2022/23", "2023/24"):
    p = sorted(V.get(my, {}).items())
    line("%s: %s" % (my, " | ".join("%s=%+.0f" % (k, v) for k, v in p)))
p22 = sorted(V["2022/23"].items())
line("2022/23 首版=%+.0f -> 末版=%+.0f  修订幅度=%+.0f kt  (正文称 +5,571->-1,101, 下修 7,442)"
     % (p22[0][1], p22[-1][1], p22[-1][1] - p22[0][1]))
p15 = sorted(V["2015/16"].items())
line("2015/16 首版=%+.0f -> 末版=%+.0f  (正文称 -5,359 -> -6,462, 连续上修缺口)"
     % (p15[0][1], p15[-1][1]))

io.open(os.path.join(BASE, "scripts", "_r102_verify.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
