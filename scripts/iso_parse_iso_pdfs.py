# -*- coding: utf-8 -*-
"""解析 ISO 官方 World Sugar Balance memo PDF 第2页全球汇总表，生成 vintage 矩阵。
8 期: Nov-2024, Feb-2025, May-2025, Aug-2025, Nov-2025, Feb-2026, May-2026, Aug-2026
输出:
  iso_balance_vintage_matrix.csv  - vintage × market_year 的 surplus/deficit 矩阵(千吨)
  iso_balance_raw_matrix.json     - 完整原始数据(所有指标)
"""
import pypdf, os, re, csv, json

BASE = r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'
PDFDIR = os.path.join(BASE, 'balance_pdfs')

PDFS = [
    'world_sugar_balance_november_2024.pdf',
    'world_sugar_balance_february_2025.pdf',
    'world_sugar_balance_may_2025.pdf',
    'world_sugar_balance_august_2025.pdf',
    'world_sugar_balance_november_2025.pdf',
    'world_sugar_balance_february_2026.pdf',
    'world_sugar_balance_may_2026.pdf',
    'world_sugar_balance_august_2026.pdf',
]
VINTAGE_LABEL = {
    'world_sugar_balance_november_2024.pdf': '2024-11',
    'world_sugar_balance_february_2025.pdf': '2025-02',
    'world_sugar_balance_may_2025.pdf': '2025-05',
    'world_sugar_balance_august_2025.pdf': '2025-08',
    'world_sugar_balance_november_2025.pdf': '2025-11',
    'world_sugar_balance_february_2026.pdf': '2026-02',
    'world_sugar_balance_may_2026.pdf': '2026-05',
    'world_sugar_balance_august_2026.pdf': '2026-08',
}
ROWS = ['production', 'consumption', 'surplus_deficit', 'import_demand',
        'export_availability', 'end_stocks', 'stock_to_use']

def parse_block(txt):
    """解析汇总文本块, 返回 {market_year: {metric: value_kte}}"""
    lines = txt.split('\n')
    # 1) 找年份行: 形如 "  2026/27 2025/26 2024/25 2023/24 2022/23 2021/22 2020/21"
    years_list = None
    for ln in lines:
        toks = re.findall(r'\b(20\d{2}/20\d{2})\b', ln)
        if len(toks) >= 6:
            years_list = toks
            break
    if not years_list:
        return None, None

    # 2) 指标行: 名称关键 + 跟在后面的数字
    metric_defs = [
        ('production', 'Production'),
        ('consumption', 'Consumption'),
        ('surplus_deficit', 'Surplus/deficit'),
        ('import_demand', 'Import demand'),
        ('export_availability', 'Export availability'),
        ('end_stocks', 'End stocks'),
        ('stock_to_use', 'ratio in %'),
    ]
    metrics = {}
    for mname, key in metric_defs:
        for i, ln in enumerate(lines):
            if key in ln:
                # 找本行及后续行中的数字
                nums = None
                # 本行
                vals = re.findall(r'-?[\d,]+\.?\d*', ln.replace('%', ''))
                # 数字数量需 >= 6 才有效, 否则看下一行(可能是 stock ratio 折行)
                if len(vals) >= 6:
                    nums = vals
                else:
                    nxt = lines[i+1] if i+1 < len(lines) else ''
                    vals2 = re.findall(r'-?[\d,]+\.?\d*', (ln + ' ' + nxt).replace('%', ''))
                    if len(vals2) >= 6:
                        nums = vals2
                if nums:
                    metrics[mname] = [int(v.replace(',', '').strip()) if '.' not in v or mname != 'stock_to_use'
                                      else float(v.replace(',', '').strip()) for v in nums[:len(years_list)]]
                break
    # stock_to_use 是浮点
    if 'stock_to_use' in metrics:
        metrics['stock_to_use'] = [float(str(v).replace(',', '')) if isinstance(v, str) else float(v) for v in metrics['stock_to_use']]

    n = len(years_list)
    out = {}
    for i, yr in enumerate(years_list):
        row = {}
        for mname in ROWS:
            arr = metrics.get(mname)
            if arr and i < len(arr):
                row[mname] = arr[i]
        out[yr] = row
    return years_list, out

all_data = {}   # vintage -> {my: {...}}
for fn in PDFS:
    p = os.path.join(PDFDIR, fn)
    r = pypdf.PdfReader(p)
    txt = ''
    for pg in r.pages[1:3]:
        txt += pg.extract_text() + '\n'
    years_list, out = parse_block(txt)
    label = VINTAGE_LABEL[fn]
    if out is None:
        print(label, 'PARSE FAIL')
        continue
    all_data[label] = out
    print(label, 'years:', years_list)

# 汇总 surplus/deficit 矩阵
all_years = []
for v in all_data.values():
    for y in v:
        if y not in all_years:
            all_years.append(y)
all_years.sort(key=lambda s: int(s.split('/')[0]))
vintages = list(all_data.keys())
print('market years:', all_years)
print('vintages:', vintages)

# 写 CSV: 行=market_year, 列=vintage 的 surplus_deficit (kt)
csv_path = os.path.join(BASE, 'iso_balance_vintage_matrix.csv')
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['market_year'] + vintages + ['unit'])
    for y in all_years:
        row = [y]
        for v in vintages:
            sd = all_data[v].get(y, {}).get('surplus_deficit')
            row.append('' if sd is None else sd)
        row.append('kt (tel quel)')
        w.writerow(row)

# 写完整 JSON
json_path = os.path.join(BASE, 'iso_balance_raw_matrix.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=1)
print('wrote', csv_path)
print('wrote', json_path)

# 打印核对用: 2021/22, 2022/23, 2023/24, 2025/26 的 SD 演进
print('\n--- 核对: surplus/deficit 演进 (kt) ---')
for y in ['2021/22', '2022/23', '2023/24', '2024/25', '2025/26', '2026/27']:
    line = [y]
    for v in vintages:
        sd = all_data[v].get(y, {}).get('surplus_deficit')
        line.append('' if sd is None else sd)
    print(line)