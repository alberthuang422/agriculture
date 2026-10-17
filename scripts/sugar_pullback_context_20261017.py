# -*- coding: utf-8 -*-
"""回调前背景条件分析: 前期涨幅/腿长 vs 随后回撤深度; 回调启动月份分布; 与当前对照"""
import csv, datetime as dt, statistics as st

SRC = r"C:\Users\Administrator\Desktop\农业\data\price\sugar\sb_daily_spliced_20261014.csv"
TH = 0.06
rows = []
with open(SRC, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['date']), float(r['sb_close'])))
rows.sort()

BULLS = [
    ("2015-16", dt.date(2015, 8, 24), dt.date(2016, 10, 6)),
    ("2020-21", dt.date(2020, 4, 28), dt.date(2021, 11, 18)),
    ("2022-23", dt.date(2022, 10, 3), dt.date(2023, 11, 7)),
    ("2026",    dt.date(2026, 4, 17), dt.date(2026, 10, 13)),
]

def analyze(seg, th=TH):
    eps = []
    peak_i, peak_p = 0, seg[0][1]
    trough_i, trough_p = None, None
    in_dd = False
    for i in range(1, len(seg)):
        d, p = seg[i]
        if not in_dd:
            if p > peak_p:
                peak_i, peak_p = i, p
            elif p <= peak_p * (1 - th):
                in_dd = True
                trough_i, trough_p = i, p
        else:
            if p < trough_p:
                trough_i, trough_p = i, p
            elif p > peak_p:
                eps.append(dict(hi_i=peak_i, hi_d=seg[peak_i][0], hi_p=peak_p,
                                lo_d=seg[trough_i][0], lo_p=trough_p,
                                nh_d=d, nh_p=p))
                in_dd = False
                peak_i, peak_p = i, p
    return eps, seg

MONTH_CN = {1:'1月',2:'2月',3:'3月',4:'4月',5:'5月',6:'6月',7:'7月',8:'8月',9:'9月',10:'10月',11:'11月',12:'12月'}
legs = []   # (牛市, 前期涨幅%, 腿长天数, 随后回撤%, 回撤天数, 高点月份)
for name, s, e in BULLS:
    seg = [(d, p) for d, p in rows if s <= d <= e]
    eps, seg = analyze(seg)
    prev_trough_i = 0  # 窗口起点
    prev_trough_p = seg[0][1]
    for ep in eps:
        runup = (ep['hi_p'] / prev_trough_p - 1) * 100
        legd  = (ep['hi_d'] - seg[prev_trough_i][0]).days
        dd    = (ep['lo_p'] / ep['hi_p'] - 1) * 100
        ddd   = (ep['lo_d'] - ep['hi_d']).days
        legs.append((name, runup, legd, dd, ddd, ep['hi_d'].month))
        # 下一段腿的起点 = 本轮低点
        prev_trough_i = next(i for i, (d, _) in enumerate(seg) if d == ep['lo_d'])
        prev_trough_p = ep['lo_p']

print("=== 每条腿: 前期涨幅 -> 随后回撤 ===")
print(f"{'牛市':<8}{'前涨幅%':>9}{'腿长天':>7}{'回撤%':>8}{'回调天':>7}  高点月")
for name, runup, legd, dd, ddd, m in legs:
    print(f"{name:<8}{runup:>9.1f}{legd:>7}{dd:>8.1f}{ddd:>7}  {MONTH_CN[m]}")

xs = [l[1] for l in legs]; ys = [l[3] for l in legs]
n = len(xs)
mx, my = sum(xs)/n, sum(ys)/n
cov = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
sx = (sum((a-mx)**2 for a in xs))**0.5; sy = (sum((b-my)**2 for b in ys))**0.5
print(f"\n相关系数 前期涨幅 vs 回撤深度: r={cov/sx/sy:.2f} (n={n})")

deep = [l for l in legs if l[3] <= -12]
shallow = [l for l in legs if l[3] > -12]
print(f"深回调(≤-12%, n={len(deep)}): 前期涨幅中位 {st.median(l[1] for l in deep):.0f}%, 腿长中位 {st.median(l[2] for l in deep):.0f}天")
print(f"浅回调(>-12%, n={len(shallow)}): 前期涨幅中位 {st.median(l[1] for l in shallow):.0f}%, 腿长中位 {st.median(l[2] for l in shallow):.0f}天")

print("\n=== 回调启动月份分布(高点所在月) ===")
from collections import Counter
cnt = Counter(l[5] for l in legs)
for m in range(1, 13):
    if cnt.get(m):
        print(f"{MONTH_CN[m]}: {'■'*cnt[m]} {cnt[m]}次")

legd_all = [l[2] for l in legs]
print(f"\n=== 腿长(低点→下个回调起点) ===")
print(f"中位 {st.median(legd_all):.0f}天, 范围 {min(legd_all)}~{max(legd_all)}天; <20天的比例 {sum(1 for x in legd_all if x<20)}/{len(legd_all)}")

# 当前状态
cur = 20.83  # 2026-10-17 02:00 北京 FOREXCOM:SUGAR
hi = 21.11
lo918 = 17.36
lo622 = 13.35
print("\n=== 当前(2026-10-17)对照 ===")
print(f"现价 {cur}, 距 10-13 高点 {hi}: {(cur/hi-1)*100:.1f}%")
print(f"9-18 低点 17.36 → 高点 21.11: +{(hi/lo918-1)*100:.1f}% / 25天 (腿龄25天, 腿长中位为{st.median(legd_all):.0f}天)")
print(f"6-22 低点 13.35 → 高点 21.11: +{(hi/lo622-1)*100:.1f}% / 113天")
