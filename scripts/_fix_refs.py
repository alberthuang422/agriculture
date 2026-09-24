# -*- coding: utf-8 -*-
"""批量修正 scripts/ 中因 data 目录重构而失效的路径引用"""
import os

scr = r'C:\Users\Administrator\Desktop\农业\scripts'

# 文件 -> [(old, new), ...]（精确替换，先长后短）
FIXES = {
    # === iso 系列：data/sugar/iso -> data/fundamentals/sugar/iso ===
    'iso_build_early_matrix.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    'iso_build_iso_series.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    'iso_build_vintage_matrix.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    'iso_extract_early_vintage.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    'iso_finalize_iso.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    'iso_parse_iso_pdfs.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    'iso_download_historical_pdfs.py': [
        ('"data", "sugar", "iso"', '"data", "fundamentals", "sugar", "iso"'),
        ('data/sugar/iso/balance_pdfs/historical', 'data/fundamentals/sugar/iso/balance_pdfs/historical'),
    ],
    'iso_extract_early_vintage.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar\iso',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'),
    ],
    # === 甘蔗系列：data/sugar -> data/fundamentals/sugar ===
    'build_sugarcane_panel.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\sugar',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar'),
    ],
    'calc_sugarcane_stats.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\fundamentals',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar'),
    ],
    'make_report98.py': [
        (r'C:\Users\Administrator\Desktop\农业\data\fundamentals',
         r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar'),
    ],
    'fetch_faostat_cane.py': [
        ('"data", "sugar", "raw"', '"data", "fundamentals", "sugar", "raw"'),
    ],
    'sugar_production_panorama_20260918.py': [
        ("'data', 'sugar', 'raw'", "'data', 'fundamentals', 'sugar', 'raw'"),
        ('data/sugar/psd_sugar_all.csv', 'data/fundamentals/sugar/raw/psd_sugar_all.csv'),
    ],
    # === enso_europe_summer：data/cotton/raw -> data/fundamentals/cotton/raw ===
    'enso_europe_summer.py': [
        ('"data", "cotton", "raw"', '"data", "fundamentals", "cotton", "raw"'),
    ],
    # === make_report97：data/fundamentals/cotton_survey -> data/fundamentals/cotton/ ===
    'make_report97.py': [
        ('"fundamentals", "cotton_survey_20260920.json"',
         '"fundamentals", "cotton", "cotton_survey_20260920.json"'),
    ],
    # === cot_stats_cotton：stock 死路径 -> data/cftc/results_cot ===
    'cot_stats_cotton.py': [
        (r'C:\Users\Administrator\Desktop\stock\results\cot\agri_cot_history_1995_2026.csv',
         r'C:\Users\Administrator\Desktop\农业\data\cftc\results_cot\agri_cot_history_1995_2026.csv'),
        (r'C:\Users\Administrator\Desktop\stock\results\cot\cotton_cot_stats_20260920.json',
         r'C:\Users\Administrator\Desktop\农业\data\cftc\results_cot\cotton_cot_stats_20260920.json'),
    ],
}

changed = []
for fn, pairs in FIXES.items():
    p = os.path.join(scr, fn)
    if not os.path.exists(p):
        print(f'MISS {fn}')
        continue
    src = open(p, encoding='utf-8', errors='replace').read()
    orig = src
    for old, new in pairs:
        src = src.replace(old, new)
    if src != orig:
        open(p, 'w', encoding='utf-8', newline='').write(src)
        changed.append(fn)
        print(f'FIXED {fn}')
    else:
        print(f'NOCHANGE {fn}')

print()
print('changed:', changed)