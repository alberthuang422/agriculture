# -*- coding: utf-8 -*-
"""短回调后创新高的形态统计: 之后的腿还有多大, 离牛市顶还有多远"""
import csv, datetime as dt, statistics as st

SRC = r"C:\Users\Administrator\Desktop\农业\data\price\sugar\sb_daily_spliced_20261014.csv"
TH = 0.06
rows = []
with open(SRC, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['date']), float(r['sb_close'])))
rows.sort()

BULLS = [
    ("2015-16", dt.date(2015, 8, 24), dt.date(2016, 10, 6), 23.90),
    ("2020-21", dt.date(2020, 4, 28), dt.date(2021, 11, 18), 20.69),
    ("2022-23", dt.date(2022, 10, 3), dt.date(2023, 11, 7), 28.14),
    ("2026",    dt.date(2026, 4, 17), dt.date(2026, 10, 13), None),  # 顶未知
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
                eps.append(dict(hi_d=seg[peak_i][0], hi_p=peak_p,
                                lo_d=seg[trough_i][0], lo_p=trough_p,
                                nh_d=d, nh_p=p))
                in_dd = False
                peak_i, peak_p = i, p
    return eps, seg

print("对每次完成的回调: 回调时长/深度 → 创新高后的腿(低点→下一回调前的峰值) → 新高之后离牛市顶还剩多少")
print(f"{'牛市':<8}{'回调天':>5}{'深度%':>7}{'创新高天':>6} | {'腿涨幅%':>7}{'腿长天':>6} | {'新高→牛顶%':>9}{'新高→牛顶天':>8}")
recs = []
for name, s, e, top_p in BULLS:
    seg = [(d, p) for d, p in rows if s <= d <= e]
    eps, seg = analyze(seg)
    for k, ep in enumerate(eps):
        dd_days = (ep['lo_d'] - ep['hi_d']).days
        dd = (ep['lo_p'] / ep['hi_p'] - 1) * 100
        nh_days = (ep['nh_d'] - ep['lo_d']).days
        # 腿峰值 = 下一个回调的前高
        if k + 1 < len(eps):
            h2d, h2p = eps[k+1]['hi_d'], eps[k+1]['hi_p']
        else:
            cand = [(d, p) for d, p in seg if d >= ep['nh_d']]
            h2d, h2p = max(cand, key=lambda x: x[1])
        legp = (h2p / ep['lo_p'] - 1) * 100
        legd = (h2d - ep['lo_d']).days
        # 新高之后距离牛市顶
        if top_p:
            r_pct = (top_p / ep['nh_p'] - 1) * 100
            r_day = (e - ep['nh_d']).days
        else:
            r_pct, r_day = None, None
        recs.append((name, dd_days, dd, nh_days, legp, legd, r_pct, r_day))
        rp = f"{r_pct:>8.1f}%" if r_pct is not None else "      顶?"
        rd = f"{r_day:>7}天" if r_day is not None else "     ?"
        print(f"{name:<8}{dd_days:>5}{dd:>7.1f}{nh_days:>6} | {legp:>7.1f}{legd:>6} | {rp}{rd}")

# 分组: 短回调(下跌<=14天) vs 长回调(>14天)
short = [r for r in recs if r[1] <= 14]
lng   = [r for r in recs if r[1] > 14]
for label, grp in [("短回调(下跌≤14天)", short), ("长回调(>14天)", lng)]:
    print(f"\n{label} n={len(grp)}:")
    print(f"  创新高后下一腿涨幅: 中位 +{st.median(r[4] for r in grp):.1f}%, 范围 +{min(r[4] for r in grp):.1f}%~+{max(r[4] for r in grp):.1f}%")
    print(f"  腿长中位: {st.median(r[5] for r in grp):.0f}天")
    done = [r for r in grp if r[6] is not None]
    if done:
        print(f"  新高→牛市顶剩余涨幅: 中位 +{st.median(r[6] for r in done):.1f}%, 剩余时间中位 {st.median(r[7] for r in done):.0f}天")

# 用户当前形态匹配: 短回调(<=10天) 且 创新高后腿已涨>=15%
print("\n=== 与当前形态最相似的历史腿(回调下跌≤10天 且 腿已确认涨幅较大) ===")
for r in recs:
    if r[1] <= 10 and r[4] >= 15:
        rp = f", 新高后牛市还剩 +{r[6]:.1f}%/{r[7]}天" if r[6] is not None else ", 牛市顶未知"
        print(f"  {r[0]}: 回调{r[1]}天/{r[2]:.1f}%, 创新高后腿 +{r[4]:.1f}%/{r[5]}天{rp}")
