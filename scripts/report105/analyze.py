"""报告105 · 棉花历史牛市全周期复盘 —— 核心量化分析
产出 /tmp/cotton105_analysis.json，供 HTML 报告直接引用。
口径：ICE Cotton No.2 连续周线（1988-10~2026-09）；CFTC Legacy Futures-Only 非商业（1995-03~2026-09）；
USDA PSD 棉花（1000 480lb bales，Aug-Jul MY；cotton_global_sd.csv 1960-2026）；
vintage 矩阵（WASDE 2010-04~2022-09，世界产量/期末库存/库消比）。
"""
import csv, json
from datetime import datetime
from bisect import bisect_right

OUT = {}
B = '/Users/alberthuang/agriculture/data/'

# ---------- 1. 价格 ----------
wk = []
with open(B+'price/cotton/ct1_weekly_1988_2026.csv') as f:
    for r in csv.DictReader(f):
        wk.append((r['time'], float(r['high']), float(r['low']), float(r['close'])))
wk.sort()
dates = [w[0] for w in wk]

def idx_of(d):  # first index with date >= d
    return bisect_right(dates, d) - 1

# 定义的牛市（ZigZag 22% 阈值识别 + 人工合并 2008-11~2011-03 为一轮）
BULLS = [
    ('1992-94 复苏牛',    '1992-02-03', '1994-05-16'),
    ('1994-95 缺口牛',    '1994-08-15', '1995-06-05'),
    ('1995 逼空脉冲',     '1995-07-31', '1995-09-18'),
    ('2001-03 复苏牛',    '2001-10-22', '2003-10-27'),
    ('2004-08 商品牛',    '2004-12-06', '2008-03-03'),
    ('2008-11 超级牛',    '2008-11-10', '2011-03-07'),
    ('2012-14 干旱牛',    '2012-06-04', '2014-03-24'),
    ('2016-18 去库存牛',  '2016-02-29', '2018-06-11'),
    ('2020-22 疫情牛',    '2020-03-30', '2022-05-02'),
    ('2022 干旱脉冲',     '2022-07-11', '2022-08-15'),
    ('2025-26 本轮',      '2025-03-31', '2026-08-31'),
]

def path_after(peak_date, weeks=(4,8,13,26,52)):
    i = idx_of(peak_date)
    p = wk[i][3]
    res = {}
    for w in weeks:
        j = min(i + w, len(wk)-1)
        res[f'{w}w'] = round((wk[j][3]/p - 1)*100, 1)
        res[f'{w}w_d'] = wk[j][0]
    return res

bull_stats = []
for name, d0, d1 in BULLS:
    i0, i1 = idx_of(d0), idx_of(d1)
    # 用极值修正底/顶（在给定窗口内取真实极值）
    lo = min(wk[i0][2] for i0 in [i0])  # bottom week low
    hi = wk[i1][1]
    p0, p1 = wk[i0][3], wk[i1][3]
    days = (datetime.strptime(dates[i1],'%Y-%m-%d')-datetime.strptime(dates[i0],'%Y-%m-%d')).days
    bull_stats.append({
        'name': name, 'low_d': dates[i0], 'low': wk[i0][2], 'low_c': p0,
        'high_d': dates[i1], 'high': hi, 'high_c': p1,
        'gain_intra': round((hi/wk[i0][2]-1)*100,1), 'gain_close': round((p1/p0-1)*100,1),
        'days': days, 'weeks': i1-i0,
        'post': path_after(d1),
    })
OUT['bulls'] = bull_stats
for b in bull_stats:
    print(f"{b['name']:16s} {b['low_d']} {b['low']:>7.2f} -> {b['high_d']} {b['high']:>7.2f} +{b['gain_intra']:>6.1f}% {b['days']:>4d}d | post4w {b['post']['4w']}% 8w {b['post']['8w']}% 26w {b['post']['26w']}%")

# ---------- 2. CFTC ----------
cot = []
with open(B+'cftc/cotton/cotton_cftc_futonly_1995_2026.csv') as f:
    for r in csv.DictReader(f):
        cot.append({'d': list(r.values())[0].lstrip('\ufeff'), 'oi': int(r['oi']), 'nc_l': int(r['nc_l']),
                    'nc_s': int(r['nc_s']), 'nc_net': int(r['nc_net']), 'c_s': int(r['c_s'])})
cot_dates = [c['d'] for c in cot]
def cot_at(d):
    i = bisect_right(cot_dates, d) - 1
    return cot[i] if i>=0 else None

# 净多峰 & 价峰对齐（牛市窗口内）
align = []
for b in bull_stats:
    if b['low_d'] < '1995-03-21': 
        align.append({'name': b['name'], 'note': 'CFTC 数据始于 1995-03，无法对齐'}); continue
    w = [c for c in cot if b['low_d'] <= c['d'] <= b['high_d']]
    if not w: 
        align.append({'name': b['name'], 'note': '窗口内无持仓数据'}); continue
    peak = max(w, key=lambda c: c['nc_net'])
    cp = cot_at(b['high_d'])
    lag = (datetime.strptime(b['high_d'],'%Y-%m-%d') - datetime.strptime(peak['d'],'%Y-%m-%d')).days
    align.append({'name': b['name'], 'peak_d': peak['d'], 'nc_net_peak': peak['nc_net'],
                  'nc_l_peak': peak['nc_l'], 'nc_s_peak': peak['nc_s'], 'oi_peak': peak['oi'],
                  'lag_days': lag,
                  'nc_net_at_pricepeak': cp['nc_net'], 'oi_at_pricepeak': cp['oi'],
                  'ratio_at_peak': round(cp['nc_net']/peak['nc_net']*100,1) if peak['nc_net'] else None,
                  'netOI_peak_pct': round(peak['nc_net']/peak['oi']*100,1),
                  'netOI_pricepeak_pct': round(cp['nc_net']/cp['oi']*100,1),
                  })
OUT['cftc_align'] = align
for a in align: print(a.get('name'), {k:v for k,v in a.items() if k not in ('name',)})

# 空头拥挤度：每轮牛市起点前 12 个月的非商业空头最大值 & 起点净持仓
crowd = []
for b in bull_stats:
    if b['low_d'] < '1995-06-01': continue
    d0 = datetime.strptime(b['low_d'],'%Y-%m-%d')
    w = [c for c in cot if 0 <= (d0 - datetime.strptime(c['d'],'%Y-%m-%d')).days <= 365]
    if w:
        smax = max(w, key=lambda c: c['nc_s'])
        crowd.append({'name': b['name'], 'short_max': smax['nc_s'], 'short_max_d': smax['d'],
                      'net_at_start': cot_at(b['low_d'])['nc_net']})
OUT['cftc_crowd'] = crowd

# 净多/OI 全样本百分位（时代中性拥挤度）
import statistics
noi = sorted(c['nc_net']/c['oi'] for c in cot)
def pct(x): return round(bisect_right(noi, x)/len(noi)*100,1)
OUT['netoi_percentile'] = {
    'current': pct(cot[-1]['nc_net']/cot[-1]['oi']),
    'current_val': round(cot[-1]['nc_net']/cot[-1]['oi']*100,1),
    'current_d': cot[-1]['d'], 'current_net': cot[-1]['nc_net'], 'current_oi': cot[-1]['oi'],
}
for a in align:
    if 'netOI_peak_pct' in a: a['peak_pctile'] = pct(a['netOI_peak_pct']/100)
# 历史顶：2008-11~2011-03 与 2020-22 顶部时的 net/OI 百分位
for nm, dd in [('2011-03 顶部','2011-03-08'), ('2022-05 顶部','2022-05-03'), ('2008-03 顶部','2008-03-04')]:
    c = cot_at(dd)
    if c: OUT.setdefault('hist_tops', []).append({'name': nm, 'd': c['d'], 'nc_net': c['nc_net'], 'oi': c['oi'],
        'netOI': round(c['nc_net']/c['oi']*100,1), 'pctile': pct(c['nc_net']/c['oi'])})
print('netOI:', OUT['netoi_percentile'], OUT.get('hist_tops'))

# ---------- 3. PSD 全球平衡表（牛市对应 MY） ----------
sd = {}
with open(B+'fundamentals/cotton/cotton_global_sd.csv') as f:
    for r in csv.DictReader(f):
        if r['Production']:
            sd[int(r['Market_Year'])] = {k: float(v) for k,v in r.items() if k!='Market_Year' and v}
OUT['sd_years'] = sorted(sd.keys())

# 牛市对应市场年（Aug-Jul）：底部所在 MY 与顶部所在 MY
def my_of(d):
    y = int(d[:4]); m = int(d[5:7])
    return y if m >= 8 else y-1
for b in bull_stats:
    b['my_low'] = my_of(b['low_d']); b['my_high'] = my_of(b['high_d'])

# ---------- 4. 国别产量分解（PSD gz） ----------
import gzip
PSD = B+'fundamentals/cotton/raw/psd_alldata.csv.gz'
KEY = {'CH':'中国','IN':'印度','US':'美国','BR':'巴西','PK':'巴基斯坦','AS':'澳大利亚','TU':'土耳其','UZ':'乌兹别克斯坦','EG':'埃及','BR':None}
KEY = {'CH':'中国','IN':'印度','US':'美国','BR':'巴西','PK':'巴基斯坦','AS':'澳大利亚','TU':'土耳其','UZ':'乌兹别克斯坦','EG':'埃及'}
prod = {}   # (country, MY) -> bales
use  = {}
es   = {}
exp  = {}
with gzip.open(PSD,'rt') as f:
    for rec in csv.DictReader(f):
        if 'Cotton' not in rec['Commodity_Description']: continue
        if rec['Unit_Description'] != '1000 480 lb. Bales': continue
        c = rec['Country_Code']; my = int(rec['Market_Year']); v = float(rec['Value']) if rec['Value'] else None
        a = rec['Attribute_Description']
        if v is None: continue
        if a=='Production': prod[(c,my)] = prod.get((c,my),0)+v
        elif a=='Domestic Use': use[(c,my)] = use.get((c,my),0)+v
        elif a=='Ending Stocks': es[(c,my)] = es.get((c,my),0)+v
        elif a=='Exports': exp[(c,my)] = exp.get((c,my),0)+v
OUT['psd_countries'] = KEY

# 各轮牛市的产量变化分解（底部MY -> 顶部MY+1，看两年变化）
decomp = []
for b in bull_stats:
    y0, y1 = b['my_low'], b['my_high']
    rows = []
    for cc, nm in KEY.items():
        p0 = prod.get((cc,y0)); p1 = prod.get((cc,y1)); p2 = prod.get((cc,y1+1))
        if p0 is not None and p1 is not None:
            rows.append({'c': nm, 'p0': round(p0), 'p1': round(p1), 'p2': round(p2) if p2 else None,
                         'chg': round(p1-p0), 'chg2': round(p2-p1) if p2 else None})
    w0 = sum(prod.get((c,y0),0) for c in KEY)
    decomp.append({'name': b['name'], 'my': f"{y0}->{y1}", 'rows': rows})
OUT['decomp'] = decomp

# ---------- 5. 库存分层（cotton_tradeable.csv） ----------
tr = {}
with open(B+'fundamentals/cotton/cotton_tradeable.csv') as f:
    for r in csv.DictReader(f):
        tr[int(r['MY'])] = r
OUT['tradeable'] = {y: {k: (float(v) if v not in ('', None) else None) for k,v in r.items() if k!='MY'} for y,r in tr.items()}

# ---------- 6. vintage 修订路径 ----------
vt = {}
with open(B+'fundamentals/cotton/vintage/cotton_world_vintage_summary.csv') as f:
    for r in csv.DictReader(f):
        vt.setdefault(r['market_year'], []).append(r)
OUT['vintage_keys'] = sorted(vt.keys())
# 三轮牛市对应 MY 的首版/行情期/终值
for my in ['2010/11','2020/21','2021/22','2016/17','2017/18']:
    if my in vt:
        sel = vt[my]
        first, last = sel[0], sel[-1]
        OUT.setdefault('vintage_paths', {})[my] = {
            'n': len(sel), 'first': {'d': first['report_date'], 'role': first['role'], 'prod': first['production'], 'es': first['ending_stocks'], 'su': first['stocks_to_use_pct']},
            'last': {'d': last['report_date'], 'role': last['role'], 'prod': last['production'], 'es': last['ending_stocks'], 'su': last['stocks_to_use_pct']},
            'path': [{'d': r['report_date'], 'role': r['role'], 'prod': r['production'], 'use': r['domestic_use'], 'es': r['ending_stocks'], 'su': r['stocks_to_use_pct']} for r in sel],
        }

# ---------- 7. 中国国储 ----------
res = []
with open(B+'fundamentals/cotton/china_reserve_policy.csv') as f:
    for r in csv.DictReader(f): res.append(r)
OUT['reserve'] = res

json.dump(OUT, open('/tmp/cotton105_analysis.json','w'), ensure_ascii=False, indent=1)
print('\nSAVED /tmp/cotton105_analysis.json')
