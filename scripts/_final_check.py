# -*- coding: utf-8 -*-
"""最终核查：data 结构、无 py 残留、脚本引用一致性"""
import os, re

data = r'C:\Users\Administrator\Desktop\农业\data'
scr = r'C:\Users\Administrator\Desktop\农业\scripts'

print('=== 1) data/ 顶层 ===')
for f in sorted(os.listdir(data)):
    p = os.path.join(data, f)
    tag = 'DIR' if os.path.isdir(p) else 'FILE'
    n = sum(len(fs) for _,_,fs in os.walk(p)) if os.path.isdir(p) else 1
    print(f'  [{tag}] {f}/  ({n})' if tag == 'DIR' else f'  [{tag}] {f}')

print()
print('=== 2) data/ 下是否还有 .py ===')
pys = [os.path.relpath(os.path.join(r,f), data) for r,_,fs in os.walk(data) for f in fs if f.endswith('.py')]
print(pys if pys else '  NONE ✓')

print()
print('=== 3) fundamentals/ 结构 ===')
fund = os.path.join(data, 'fundamentals')
for r, dirs, files in os.walk(fund):
    rel = os.path.relpath(r, fund)
    mark = '.' if rel == '.' else rel
    if rel == '.':
        print(f'  [fundamentals/] dirs={sorted(dirs)}')
    else:
        print(f'  [{mark}/] files={len(files)}')

print()
print('=== 4) scripts 中仍引用旧路径的残留 ===')
# 已不存在的旧路径模式
bad_patterns = [
    r'data[\\/]sugar[\\/]iso', r'data[\\/]sugar[\\/]raw', r'data[\\/]sugar[\\/]psd',
    r'data[\\/]cotton[\\/]raw', r'data[\\/]cotton[\\/]wasde', r'data[\\/]cotton[\\/]CMO',
    r'data[\\/](sugar|cotton)[\\/]sugarcane',
    r'data[\\/](sugar|cotton)[\\/](sugar|cotton)_',
    r'data[\\/]cotton[\\/]oni', r'data[\\/]cotton[\\/]cotton_wb',
]
issues = 0
for f in sorted(os.listdir(scr)):
    if not f.endswith('.py'): continue
    lines = open(os.path.join(scr,f), encoding='utf-8', errors='replace').read().splitlines()
    for i, l in enumerate(lines, 1):
        for pat in bad_patterns:
            if re.search(pat, l) and not l.strip().startswith('#'):
                print(f'  {f}:{i}: {l.strip()[:120]}')
                issues += 1
                break
print('  issues:', issues)

print()
print('=== 5) 关键新路径存在性 ===')
checks = [
    'data/fundamentals/sugar/iso/iso_qmo_vintage.json',
    'data/fundamentals/sugar/raw/psd_sugar_all.csv',
    'data/fundamentals/sugar/sugarcane_area_yield_2005_2024.csv',
    'data/fundamentals/cotton/raw/oni_latest.txt',
    'data/fundamentals/cotton/wasde_2026/oce-wasde-report-data-2026-09.csv',
    'data/fundamentals/cotton/cotton_survey_20260920.json',
    'data/price/sugar/sb_price_daily.csv',
    'data/price/cotton/cotton_wb_monthly.csv',
    'data/price/cotton/CMO-Historical-Data-Monthly.xlsx',
    'data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv',
]
for c in checks:
    ok = os.path.exists(os.path.join(data, c.replace('data/','')))
    print(f'  {"OK" if ok else "MISSING"}  {c}')