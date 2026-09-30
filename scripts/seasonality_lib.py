#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月度季节性统计通用库 —— 输入任意「连续合约月线 OHLC CSV」，产出季节性统计 JSON。
   口径：月环比涨跌幅 = 本月收盘 / 上月收盘 − 1（相邻月份不连续则跳过）。
"""
import csv, json
from collections import defaultdict


def load_months(src):
    """读取月线 CSV（列：time,open,high,low,close[,trading_days]），返回按时间排序的列表"""
    rows = []
    with open(src) as f:
        for r in csv.DictReader(f):
            rows.append({
                'y': int(r['time'][:4]), 'm': int(r['time'][5:7]),
                'close': float(r['close']), 'time': r['time']
            })
    rows.sort(key=lambda x: (x['y'], x['m']))
    return rows


def seasonality(src, start_year, groups=None, group_len=5):
    rows = load_months(src)

    # 月环比涨跌幅 %
    ret = {}
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        if (b['y'] - a['y']) * 12 + (b['m'] - a['m']) != 1:
            continue
        ret[(b['y'], b['m'])] = (b['close'] / a['close'] - 1) * 100

    years = sorted({y for (y, m) in ret if y >= start_year})
    pxmap = {(r['y'], r['m']): r['close'] for r in rows}

    out = {'years': years, 'matrix': {}, 'px': {}, 'close': {}, 'yr_ret': {}, 'yr_px': {}, 'px_avg': {}}
    for y in years:
        for m in range(1, 13):
            k = f'{y}-{m:02d}'
            out['matrix'][k] = round(ret[(y, m)], 2) if (y, m) in ret else None
            out['px'][k] = round(pxmap[(y, m)], 2) if (y, m) in pxmap else None
        out['close'][str(y)] = pxmap.get((y, 12))
        # 年度涨跌 = 本年12月末 / 上年12月末 − 1
        c, p = pxmap.get((y, 12)), pxmap.get((y - 1, 12))
        out['yr_ret'][str(y)] = round((c / p - 1) * 100, 2) if (c and p) else None
        vals = [out['px'][f'{y}-{m:02d}'] for m in range(1, 13) if out['px'][f'{y}-{m:02d}'] is not None]
        out['yr_px'][str(y)] = round(sum(vals) / len(vals), 2) if vals else None

    for m in range(1, 13):
        vals = [out['px'][f'{y}-{m:02d}'] for y in years if out['px'][f'{y}-{m:02d}'] is not None]
        out['px_avg'][str(m)] = round(sum(vals) / len(vals), 2) if vals else None

    # 分组（默认按 5 年切）
    if groups is None:
        groups, y0 = [], start_year
        while y0 <= years[-1]:
            groups.append((y0, min(y0 + group_len - 1, years[-1])))
            y0 += group_len
    gstat = {}
    for g0, g1 in groups:
        lab = f'{g0}-{g1}'
        d = {}
        for m in range(1, 13):
            vals = [ret[(y, m)] for y in years if g0 <= y <= g1 and (y, m) in ret]
            if vals:
                d[m] = {
                    'avg': round(sum(vals) / len(vals), 2),
                    'win': round(sum(1 for v in vals if v > 0) / len(vals) * 100),
                    'n': len(vals),
                    'max': round(max(vals), 2), 'min': round(min(vals), 2),
                }
            else:
                d[m] = None
        gstat[lab] = d

    allg = {}
    for m in range(1, 13):
        vals = [ret[(y, m)] for y in years if (y, m) in ret]
        allg[m] = {
            'avg': round(sum(vals) / len(vals), 2),
            'win': round(sum(1 for v in vals if v > 0) / len(vals) * 100),
            'n': len(vals),
            'max': round(max(vals), 2), 'min': round(min(vals), 2),
            'maxY': max([y for y in years if (y, m) in ret], key=lambda y: ret[(y, m)]),
            'minY': min([y for y in years if (y, m) in ret], key=lambda y: ret[(y, m)]),
            'med': round(sorted(vals)[len(vals) // 2], 2),
        }
    gstat[f'全样本 {start_year}-{years[-1]}'] = allg

    out['groups'] = gstat
    out['group_order'] = [f'{a}-{b}' for a, b in groups] + [f'全样本 {start_year}-{years[-1]}']
    out['start_year'] = start_year
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--start-year', type=int, required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    d = seasonality(a.src, a.start_year)
    json.dump(d, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('written', a.out, '| years', d['years'][0], '-', d['years'][-1])
