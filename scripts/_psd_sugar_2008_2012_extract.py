# -*- coding: utf-8 -*-
"""提取 PSD 糖（0612000）2007/08-2012/13 主要国家平衡表 -> data/fundamentals/sugar/raw/psd_sugar_2008_2012_balance.csv"""
import csv
from collections import defaultdict

SRC = 'data/fundamentals/sugar/raw/psd_sugar_all.csv'
DST = 'data/fundamentals/sugar/raw/psd_sugar_2008_2012_balance.csv'

ATTR = {'020': 'BS', '028': 'P', '057': 'M', '088': 'X', '126': 'C', '176': 'ES'}
ATTR_CN = {'BS': '期初库存', 'P': '产量', 'M': '进口', 'X': '出口', 'C': '消费', 'ES': '期末库存'}
YEARS = ('2007', '2008', '2009', '2010', '2011', '2012')
WANT = ['Brazil', 'India', 'European Union', 'China', 'Thailand', 'United States',
        'Russia', 'Australia', 'Pakistan', 'Mexico', 'United Arab Emirates',
        'Indonesia', 'Bangladesh', 'Egypt', 'Algeria', 'Malaysia', 'Nigeria']
WL = {w.lower(): w for w in WANT}

data = defaultdict(dict)
dbg = {'yr': 0, 'cc': 0, 'attr': 0, 'val': 0}
for r in csv.reader(open(SRC, encoding='utf-8-sig')):
    yr = r[4]
    if yr not in YEARS:
        continue
    dbg['yr'] += 1
    cl = r[3].lower()
    if cl not in WL:
        continue
    dbg['cc'] += 1
    code = ATTR.get(r[7])
    if not code:
        continue
    dbg['attr'] += 1
    try:
        v = float(r[-1])  # 数值恒为最后一列
    except ValueError:
        continue
    dbg['val'] += 1
    data[(WL[cl], yr)][code] = v
print('DEBUG', dbg, flush=True)

with open(DST, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['country', 'market_year', 'beginning_stocks', 'production', 'imports',
                'exports', 'consumption', 'ending_stocks', 'stock_to_use_pct'])
    for c in WANT:
        for yr in YEARS:
            d = data.get((c, yr))
            if not d:
                continue
            p, m, x, cs, es = d.get('P', 0), d.get('M', 0), d.get('X', 0), d.get('C', 0), d.get('ES', 0)
            sr = es / cs * 100 if cs else 0
            w.writerow([c, '%s/%d' % (yr, int(yr) + 1), d.get('BS', 0), p, m, x, cs, es, round(sr, 1)])
            print('%-20s %s/%d  产%7.0f 消%7.0f 缺口%7.0f 进%6.0f 出%6.0f 末库存%8.0f 库消比%5.1f%%'
                  % (c, yr, int(yr) + 1, p, cs, p - cs, m, x, es, sr))
print('saved ->', DST)
