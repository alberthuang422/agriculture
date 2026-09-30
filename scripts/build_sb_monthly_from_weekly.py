#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ICE 白糖（SB1!）周线导出文件重采样为月线 CSV。
   月末收盘 = 该月最后一根周线的收盘；月开/高/低同理取首/极值。
"""
import csv, sys
from collections import OrderedDict

SRC = '/Users/alberthuang/Downloads/ICEUS_DLY_SB1!, 1W.csv'
OUT = '/Users/alberthuang/agriculture/data/price/sugar/sb_price_monthly_tv.csv'

mon = OrderedDict()
with open(SRC) as f:
    for r in csv.DictReader(f):
        if not r['close'] or r['close'].strip() == '':
            continue
        y, m = int(r['time'][:4]), int(r['time'][5:7])
        k = f'{y:04d}-{m:02d}'
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        if k not in mon:
            mon[k] = {'time': r['time'], 'open': o, 'high': h, 'low': l, 'close': c, 'n': 1}
        else:
            d = mon[k]
            d['time'] = r['time']
            d['high'] = max(d['high'], h)
            d['low'] = min(d['low'], l)
            d['close'] = c
            d['n'] += 1

ks = list(mon)
print('months:', ks[0], '->', ks[-1], 'n =', len(ks))

# 完整性：1989-12 ~ 2026-09
exp, y, m = [], 1989, 12
while (y, m) <= (2026, 9):
    exp.append(f'{y:04d}-{m:02d}')
    m += 1
    if m == 13:
        m, y = 1, y + 1
miss = [x for x in exp if x not in mon]
print('missing months:', miss if miss else '无')
thin = [(k, mon[k]['n']) for k in ks if k >= '2008-01' and mon[k]['n'] < 3]
print('周数<3 的月份（2008+）:', thin if thin else '无')

with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['time', 'open', 'high', 'low', 'close', 'weeks'])
    for k in ks:
        d = mon[k]
        w.writerow([d['time'], round(d['open'], 2), round(d['high'], 2),
                    round(d['low'], 2), round(d['close'], 2), d['n']])
print('written', OUT)

print('\n12 月末收盘（2007-2025）:')
for yy in range(2007, 2026):
    print(yy, mon.get(f'{yy}-12', {}).get('close'))
