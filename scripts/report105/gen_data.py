#!/usr/bin/env python3
"""生成 105 号棉花牛市复盘报告的全部嵌入数据 -> /tmp/r105_data.json"""
import csv, json, gzip
from datetime import date

AG = '/Users/alberthuang/agriculture'

# ---------- 周度价格 ----------
W = []
for r in csv.DictReader(open(f'{AG}/data/price/cotton/ct1_weekly_1988_2026.csv')):
    W.append({'d': r['time'], 'o': float(r['open']), 'h': float(r['high']),
              'l': float(r['low']), 'c': float(r['close'])})
W.sort(key=lambda x: x['d'])

# ---------- CFTC ----------
C = []
for r in csv.DictReader(open(f'{AG}/data/cftc/cotton/cotton_cftc_futonly_1995_2026.csv')):
    d = list(r.values())[0].lstrip('\ufeff')
    C.append({'d': d, 'oi': int(r['oi']), 'l': int(r['nc_l']), 's': int(r['nc_s']),
              'net': int(r['nc_net'])})
C.sort(key=lambda x: x['d'])
cmap = {c['d']: c for c in C}

A = json.load(open('/tmp/cotton105_analysis.json'))

# ---------- 1. 全史价格（周收盘，紧凑） ----------
px_all = [[w['d'], w['c']] for w in W]

# ---------- 2. 牛市归一化路径（底部=100，到顶后52周） ----------
def wi(dstr):
    for i, w in enumerate(W):
        if w['d'] >= dstr:
            return i
    return len(W) - 1

norm = []
for b in A['bulls']:
    i0, i1 = wi(b['low_d']), wi(b['high_d'])
    base = W[i0]['c']
    pts = []
    for j in range(i0, min(i1 + 53, len(W))):
        pts.append([j - i0, round(W[j]['c'] / base * 100, 1), W[j]['d']])
    norm.append({'name': b['name'], 'base': base, 'low_d': b['low_d'], 'high_d': b['high_d'],
                 'pts': pts, 'post': b['post']})

# ---------- 3. dual 图数据（选定轮次：底部前78周 ~ 顶后78周） ----------
DUAL_PICK = ['2001-03 复苏牛', '2008-11 超级牛', '2016-18 去库存牛', '2020-22 疫情牛', '2025-26 本轮']
duals = {}
for b in A['bulls']:
    if b['name'] not in DUAL_PICK:
        continue
    i0, i1 = wi(b['low_d']), wi(b['high_d'])
    lo, hi = max(0, i0 - 78), min(len(W) - 1, i1 + 78)
    rows = []
    for j in range(lo, hi + 1):
        w = W[j]
        cc = cmap.get(w['d'])
        if cc is None:
            # 找最近的 CFTC 周
            k = max([c for c in C if c['d'] <= w['d']], key=lambda x: x['d'], default=None)
            cc = k
        if cc is None:
            continue
        rows.append([w['d'], w['c'], cc['net'], cc['l'], cc['s'], cc['oi']])
    duals[b['name']] = rows

# ---------- 4. 供需平衡（ProdMinusUse + SU，1960-2026） ----------
sd = []
def _f(v):
    try: return float(v)
    except (ValueError, TypeError): return None
for r in csv.DictReader(open(f'{AG}/data/fundamentals/cotton/cotton_global_sd.csv')):
    sd.append([int(r['Market_Year']), _f(r['ProdMinusUse']), _f(r['StockToUse']),
               _f(r['Production']), _f(r['Domestic Use']), _f(r['Ending Stocks'])])

# ---------- 5. 库存分层 SU（正确口径：分子分母同步剥离） ----------
LC = json.load(open('/tmp/r105_layer_correct.json'))
layer = []
for y in sorted(LC.keys(), key=int):
    r = LC[y]
    layer.append([int(y), r['W_su'], r['R1_su'], r['R2_su'], r['b3_cov'],
                  r['cn_es'], r['w_es']])

# ---------- 6. 持仓对齐汇总 ----------
align = [a for a in A['cftc_align'] if 'lag_days' in a]

# ---------- 7. vintage ----------
vint_sum = []
for my, v in A['vintage_paths'].items():
    f, l = v['first'], v['last']
    vint_sum.append([my, float(f['su']), float(l['su']), round(float(l['su']) - float(f['su']), 1)])
vint_sum.sort(key=lambda x: x[0])
vint_intra = {}
for my in ['2016/17', '2020/21', '2010/11']:
    p = A['vintage_paths'][my]['path']
    vint_intra[my] = [[x['d'], _f(x['su']), x['role']] for x in p if _f(x['su']) is not None]

# ---------- 8. 国储 ----------
reserve = []
for r in A['reserve']:
    reserve.append({k.lstrip('\ufeff'): v for k, v in r.items()})

# ---------- 9. 当前持仓定位 ----------
cur = A['netoi_percentile']
# 历史各顶部 netOI 百分位
tops = A['hist_tops']

# ---------- 10. 美棉 26/27 逐月修订 ----------
uswasde = list(csv.DictReader(open(f'{AG}/data/fundamentals/cotton/us_cotton_wasde_2026_timeline.csv')))

# ---------- 11. ONI ----------
oni = []
for ln in open(f'{AG}/data/fundamentals/cotton/raw/oni_latest.txt'):
    p = ln.split()
    if len(p) == 4 and p[0] in ('JFM','FMA','MAM','AMJ','MJJ','JJA','JAS','ASO','SON','OND','NDJ','DJF'):
        try: oni.append([p[0] + ' ' + p[1], float(p[3])])
        except ValueError: pass

# ---------- 12. A 指数月度 ----------
ca = []
for r in csv.DictReader(open(f'{AG}/data/price/cotton/cotton_wb_monthly.csv')):
    ca.append([r['month'], float(r['cotton_a'])])

# ---------- 13. 空头拥挤度（各轮启动前空头峰） ----------
crowd = A['cftc_crowd']

# ---------- 14. 本轮 WASDE 最新（26/27） ----------
w26 = list(csv.DictReader(open(f'{AG}/data/fundamentals/cotton/wasde_2026/oce-wasde-report-data-2026-09.csv')))

# ---------- 15. netOI 时间序列 + 全样本百分位（供 c11 散点） ----------
nets = sorted([c['net'] / c['oi'] * 100 for c in C if c['oi'] > 0])
import bisect
netoi_ts = []
for c in C:
    v = c['net'] / c['oi'] * 100
    p = bisect.bisect_left(nets, v) / len(nets) * 100
    netoi_ts.append([c['d'], round(v, 2), round(p, 1)])

# ---------- 16. decomp 原样 ----------
decomp = A['decomp']

out = {
    'px_all': px_all, 'norm': norm, 'duals': duals, 'sd': sd, 'layer': layer,
    'align': align, 'vint_sum': vint_sum, 'vint_intra': vint_intra, 'reserve': reserve,
    'cur': cur, 'tops': tops, 'uswasde': uswasde, 'oni': oni, 'ca': ca, 'crowd': crowd,
    'bulls': A['bulls'], 'netoi_ts': netoi_ts, 'decomp': decomp,
}
json.dump(out, open('/tmp/r105_data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
import os
print('OK', os.path.getsize('/tmp/r105_data.json') // 1024, 'KB')
print('duals weeks:', {k: len(v) for k, v in duals.items()})
print('align:', len(align), 'sd:', len(sd), 'layer:', len(layer), 'ca:', len(ca), 'oni:', len(oni))
print('uswasde cols:', list(uswasde[0].keys()) if uswasde else None)
