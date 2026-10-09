# -*- coding: utf-8 -*-
"""临时分析：白糖月度季节性（均值 vs 去极值截尾均值 vs 中位数），不产出报告"""
import csv, statistics as st

def load(src):
    rows = []
    with open(src) as f:
        for r in csv.DictReader(f):
            rows.append((int(r['time'][:4]), int(r['time'][5:7]), float(r['close'])))
    rows.sort()
    return rows

def monthly_ret(rows):
    ret = {}
    for i in range(1, len(rows)):
        y0, m0, c0 = rows[i-1]; y1, m1, c1 = rows[i]
        if (y1 - y0) * 12 + (m1 - m0) == 1:
            ret[(y1, m1)] = (c1 / c0 - 1) * 100
    return ret

rows = load(r"C:/Users/Administrator/Desktop/农业/data/price/sugar/sb_price_monthly_tv.csv")
ret = monthly_ret(rows)

def stat(years, trim):
    out = {}
    for m in range(1, 13):
        vals = sorted(ret[(y, m)] for y in years if (y, m) in ret)
        if not vals: continue
        n = len(vals)
        t = vals[trim:n-trim] if trim else vals
        out[m] = dict(n=n,
                      mean=sum(vals)/n,
                      trim=sum(t)/len(t) if t else float('nan'),
                      med=st.median(vals),
                      win=sum(1 for v in vals if v > 0)/n*100,
                      mx=max(vals), mn=min(vals))
    return out

for label, y0, trim in [("1990-2026 全样本", 1990, 0), ("1990-2026 截尾(去最高最低)", 1990, 1),
                        ("2008-2026 全样本", 2008, 0), ("2008-2026 截尾(去最高最低)", 2008, 1),
                        ("2016-2026 截尾", 2016, 1)]:
    s = stat(range(y0, 2027), trim)
    print("=" * 72)
    print(label)
    print(f"{'月':>3} {'n':>3} {'均值%':>7} {'截尾均值%':>9} {'中位数%':>8} {'胜率%':>6} {'最大%':>7} {'最小%':>7}")
    for m in range(1, 13):
        d = s.get(m)
        if d:
            print(f"{m:>3} {d['n']:>3} {d['mean']:>7.2f} {d['trim']:>9.2f} {d['med']:>8.2f} {d['win']:>6.0f} {d['mx']:>7.1f} {d['mn']:>7.1f}")

# 极值来源：截尾前后差异最大的月份，列出异常年份
print("=" * 72)
print("各月 1990-2026 的最大/最小涨跌来自哪些年份（识别离群值来源）：")
s = stat(range(1990, 2027), 0)
for m in range(1, 13):
    per = sorted(((ret[(y, m)], y) for y in range(1990, 2027) if (y, m) in ret), reverse=True)
    if per:
        print(f"{m:>2}月  max {per[0][1]} {per[0][0]:+.1f}% | min {per[-1][1]} {per[-1][0]:+.1f}%")
