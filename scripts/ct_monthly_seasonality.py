#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ICE 棉花 2 号连续合约月线：月度涨跌幅季节性统计（2008 至今）"""
import csv, json, calendar
from collections import defaultdict

SRC = '/Users/alberthuang/Downloads/ICEUS_DLY_CT1!, 1M.csv'
START_YEAR = 2008

rows = []
with open(SRC) as f:
    for r in csv.DictReader(f):
        y, m = int(r['time'][:4]), int(r['time'][5:7])
        rows.append({'y': y, 'm': m, 'close': float(r['close']), 'time': r['time']})
rows.sort(key=lambda x: (x['y'], x['m']))

# 月环比涨跌幅 %
ret = {}
for i in range(1, len(rows)):
    a, b = rows[i - 1], rows[i]
    # 仅相邻月份才构成环比
    if (b['y'] - a['y']) * 12 + (b['m'] - a['m']) != 1:
        continue
    ret[(b['y'], b['m'])] = (b['close'] / a['close'] - 1) * 100

years = sorted({y for (y, m) in ret if y >= START_YEAR})
# 各年实际有数据的月份（2026 只到 9 月）
avail = defaultdict(set)
for (y, m) in ret:
    if y >= START_YEAR:
        avail[y].add(m)

out = {'years': years, 'matrix': {}, 'close': {}, 'px': {}, 'avail': {y: sorted(avail[y]) for y in years}}
pxmap = {(r['y'], r['m']): r['close'] for r in rows}
for y in years:
    for m in range(1, 13):
        key = f'{y}-{m:02d}'
        out['matrix'][key] = round(ret[(y, m)], 2) if (y, m) in ret else None
        out['px'][key] = round(pxmap[(y, m)], 2) if (y, m) in pxmap else None
    for r in rows:
        if r['y'] == y and r['m'] == 12:
            out['close'][str(y)] = r['close']
    if str(y) not in out['close']:
        out['close'][str(y)] = None

# 年度涨跌幅（12月末收盘 / 上年12月末收盘 − 1），及年均价
out['yr_ret'], out['yr_px'] = {}, {}
for y in years:
    c, p = out['close'].get(str(y)), out['close'].get(str(y - 1))
    out['yr_ret'][str(y)] = round((c / p - 1) * 100, 2) if (c and p) else None
    vals = [out['px'][f'{y}-{m:02d}'] for m in range(1, 13) if out['px'][f'{y}-{m:02d}'] is not None]
    out['yr_px'][str(y)] = round(sum(vals) / len(vals), 2) if vals else None

# 5 年分组平均
groups = [(2008, 2012), (2013, 2017), (2018, 2022), (2023, 2026)]
gstat = {}
for g0, g1 in groups:
    label = f'{g0}-{g1}'
    d = {}
    for m in range(1, 13):
        vals = [ret[(y, m)] for y in years if g0 <= y <= g1 and (y, m) in ret]
        if vals:
            d[m] = {
                'avg': round(sum(vals) / len(vals), 2),
                'win': round(sum(1 for v in vals if v > 0) / len(vals) * 100),
                'n': len(vals),
                'max': round(max(vals), 2),
                'min': round(min(vals), 2),
            }
        else:
            d[m] = None
    gstat[label] = d

# 全样本
allg = {}
for m in range(1, 13):
    vals = [ret[(y, m)] for y in years if (y, m) in ret]
    allg[m] = {
        'avg': round(sum(vals) / len(vals), 2),
        'win': round(sum(1 for v in vals if v > 0) / len(vals) * 100),
        'n': len(vals),
        'max': round(max(vals), 2),
        'min': round(min(vals), 2),
        'maxY': max([y for y in years if (y, m) in ret], key=lambda y: ret[(y, m)]),
        'minY': min([y for y in years if (y, m) in ret], key=lambda y: ret[(y, m)]),
        'med': round(sorted(vals)[len(vals) // 2], 2),
    }
gstat['全样本 2008-2026'] = allg

# 各月 19 年平均收盘价（表 1.1 末行）
out['px_avg'] = {}
for m in range(1, 13):
    vals = [out['px'][f'{y}-{m:02d}'] for y in years if out['px'][f'{y}-{m:02d}'] is not None]
    out['px_avg'][str(m)] = round(sum(vals) / len(vals), 2) if vals else None

out['groups'] = gstat
json.dump(out, open('/tmp/ct_monthly.json', 'w'), ensure_ascii=False, indent=1)

# ---- 控制台预览 ----
print('=== 月度涨跌幅矩阵 (%CHG, 单位 %) ===')
hdr = '月份  ' + ' '.join(f'{y:>7}' for y in years)
print(hdr)
for m in range(1, 13):
    line = f'{m:>3}月 '
    for y in years:
        v = out['matrix'][f'{y}-{m:02d}']
        line += f'{v:>7.2f}' if v is not None else f'{"-":>7}'
    print(line)

print('\n=== 5 年分组平均涨跌幅 (%) / 胜率 (%) ===')
labels = [f'{a}-{b}' for a, b in groups] + ['全样本 2008-2026']
print('月份  ' + ' '.join(f'{l:>16}' for l in labels))
for m in range(1, 13):
    line = f'{m:>3}月 '
    for l in labels:
        s = gstat[l][m]
        if s:
            line += f'{s["avg"]:>8.2f}/{s["win"]:>3.0f}%  '
        else:
            line += f'{"-":>16}'
    print(line)
