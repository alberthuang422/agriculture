# -*- coding: utf-8 -*-
"""最终口径裁定：以"盘中价峰日"为全文统一价峰，持仓取该日或之前最近报表。
   并算出顶后 N 周路径（基准=价峰日最近报表的收盘），供正文一次性对齐。"""
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

CASES = [("2015/16", "2015-08-24", "2017-06-30", "2016-01-01", "2016-12-31"),
         ("2023",    "2022-10-03", "2024-05-31", "2023-01-01", "2023-12-31")]

for lbl, wa, wb, pa, pb in CASES:
    p("=" * 78); p(lbl); p("=" * 78)
    # 全文口径价峰 = 窗口内盘中最高
    pk = max([t for t in d if wa <= t <= wb], key=lambda t: H[t])
    p("盘中价峰: %s  high=%.2f  close=%.2f" % (pk, H[pk], C[pk]))
    # 收盘峰（对照）
    ck = max([t for t in d if wa <= t <= wb], key=lambda t: C[t])
    p("收盘价峰(对照): %s close=%.2f" % (ck, C[ck]))
    # 报表日采样峰（旧口径，对照）
    rs = [r for r in W if pa <= r["d"] <= pb]
    i = bisect.bisect_right(d, "2000-01-01")
    def rclose(rd):
        j = bisect.bisect_right(d, rd) - 1
        return C[d[j]]
    rk = max(rs, key=lambda r: rclose(r["d"]))
    p("报表日采样峰(旧口径,对照): %s close=%.2f net=%+d" % (rk["d"], rclose(rk["d"]), rk["net"]))
    # 净多峰
    np_ = max(rs, key=lambda r: r["net"])
    p("净多峰: %s %+d" % (np_["d"], np_["net"]))
    # 价峰日 or 之前最近报表
    align = [r for r in W if r["d"] <= pk][-1]
    p(">> 价峰(%s)对齐报表: %s  net=%+d  = 峰值 %.1f%%" % (pk, align["d"], align["net"], align["net"]/np_["net"]*100))
    p(">> 净多峰领先价峰: %d 天" % (date.fromisoformat(pk) - date.fromisoformat(np_["d"])).days)
    p(">> 净多峰日报表价 %.2f -> 价峰日对齐报表收盘 %.2f = %+.1f%%"
      % (rclose(np_["d"]), rclose(align["d"]),
         (rclose(align["d"])/rclose(np_["d"])-1)*100))
    p(">> 明细: L=%d S=%d OI=%d" % (align["l"], align["s"], align["oi"]))
    # 顶后路径，基准=对齐报表收盘
    base = rclose(align["d"])
    p(">> 顶后路径（基准 = 对齐报表收盘 %.2f @ %s）" % (base, align["d"]))
    for wk in (4, 8, 13, 26, 52):
        tgt = date.fromisoformat(align["d"]) + timedelta(days=wk*7)
        c = [t for t in d if date.fromisoformat(t) <= tgt]
        if c:
            t2 = c[-1]
            p("     %+3d 周 -> %s close=%6.2f = %+6.1f%%" % (wk, t2, C[t2], (C[t2]/base-1)*100))
    # 顶后 4 周净多
    t4 = date.fromisoformat(align["d"]) + timedelta(days=28)
    n4 = [r for r in W if date.fromisoformat(r["d"]) <= t4][-1]
    p(">> 顶后4周净多: %s %+d = %+.1f%%" % (n4["d"], n4["net"], (n4["net"]/align["net"]-1)*100))
    p()

p("=" * 78); p("月度环比（供 '单月跌幅' 标注）"); p("=" * 78)
def me(y, m):
    c = [t for t in d if t.startswith("%04d-%02d" % (y, m))]
    return (c[-1], C[c[-1]])
def mavg(y, m):
    v = [C[t] for t in d if t.startswith("%04d-%02d" % (y, m))]
    return sum(v)/len(v)
for (y1,m1),(y2,m2) in [((2023,11),(2023,12)),((2023,10),(2023,12)),((2016,10),(2016,11)),((2016,11),(2016,12))]:
    a=me(y1,m1); b=me(y2,m2)
    p("  %04d-%02d -> %04d-%02d 月末收盘: %.2f -> %.2f = %+.2f%% | 月均价 %.2f -> %.2f = %+.2f%%"
      % (y1,m1,y2,m2,a[1],b[1],(b[1]/a[1]-1)*100, mavg(y1,m1), mavg(y2,m2), (mavg(y2,m2)/mavg(y1,m1)-1)*100))

p(); p("=" * 78); p("反弹/谷值 具体日期"); p("=" * 78)
for t in ["2017-01-03","2017-01-04","2017-02-06","2024-01-24","2024-01-25","2017-06-20","2017-08-22"]:
    if t in C: p("  %s close=%.2f high=%.2f" % (t, C[t], H[t]))
w = [r for r in W if r["d"] in ("2017-06-20","2017-08-22")]
for r in w: p("  报表 %s net=%+d" % (r["d"], r["net"]))
p("  2016顶后首次转净空: %s" % [ (r["d"],r["net"]) for r in W if r["d"]>"2016-10-06" and r["net"]<0 ][:3])
p("  2017-01~02 收盘最高: %s" % (max([(t,C[t]) for t in d if "2017-01-01"<=t<="2017-02-28"], key=lambda x:x[1]),))
p("  2017-01~02 盘中最高: %s" % (max([(t,H[t]) for t in d if "2017-01-01"<=t<="2017-02-28"], key=lambda x:x[1]),))
p("  2024-01 收盘最高: %s" % (max([(t,C[t]) for t in d if t.startswith("2024-01")], key=lambda x:x[1]),))
p("  2024-01 盘中最高: %s" % (max([(t,H[t]) for t in d if t.startswith("2024-01")], key=lambda x:x[1]),))

io.open(os.path.join(BASE, "scripts", "_r102_verify6.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
