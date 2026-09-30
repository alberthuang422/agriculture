#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用「月度季节性」深色 HTML 报告生成器（横轴月份 / 纵轴年份）
   表 1.1 逐月收盘价（绝对价格）  表 一 逐月涨跌幅  表 二 分组平均
"""
import json, argparse
from collections import defaultdict

MH = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']


def build(d, title, unit, source, extra=''):
    years, M, PX, YR, YRPX, PXAVG, G = (d['years'], d['matrix'], d['px'], d['yr_ret'],
                                        d['yr_px'], d['px_avg'], d['groups'])
    GN = d['group_order']
    yb, ye = years[0], years[-1]

    def pct_cell(v, scale=20.0, bold=False):
        if v is None:
            return '<td class="na">—</td>'
        a = min(abs(v) / scale, 1.0)
        if v > 0:
            bg, fg = f'rgba(220,60,50,{0.06 + a * 0.62:.3f})', ('#ffb3ad' if a < 0.5 else '#fff')
        elif v < 0:
            bg, fg = f'rgba(30,170,110,{0.06 + a * 0.62:.3f})', ('#9de3c4' if a < 0.5 else '#fff')
        else:
            bg, fg = 'rgba(255,255,255,.03)', '#8b949e'
        return f'<td class="num{" fw7" if bold else ""}" style="background:{bg};color:{fg}">{v:+.2f}</td>'

    # ---- 表 1.1 逐月收盘价 ----
    def px_cell(y, m):
        v, mom = PX[f'{y}-{m:02d}'], M[f'{y}-{m:02d}']
        if v is None:
            return '<td class="na">—</td>'
        ya = YRPX.get(str(y)) or v
        dev = (v / ya - 1) if ya else 0
        a = min(abs(dev) / 0.20, 1.0)
        if dev > 0:
            bg, fg = f'rgba(220,60,50,{0.04 + a * 0.46:.3f})', ('#ffc0ba' if a < 0.5 else '#fff')
        else:
            bg, fg = f'rgba(30,170,110,{0.04 + a * 0.46:.3f})', ('#a8e8cc' if a < 0.5 else '#fff')
        s = '<i class="mo fl">n/a</i>' if mom is None else \
            f'<i class="mo {"up" if mom > 0 else ("dn" if mom < 0 else "fl")}">{mom:+.2f}%</i>'
        return f'<td class="num2" style="background:{bg};color:{fg}"><b>{v:.2f}</b>{s}</td>'

    r11 = []
    for y in years:
        t = [f'<th class="rowh">{y}</th>'] + [px_cell(y, m) for m in range(1, 13)]
        t.append(f'<td class="num sum2">{YRPX[str(y)]:.2f}</td>' if YRPX.get(str(y)) else '<td class="na">—</td>')
        r11.append('<tr>' + ''.join(t) + '</tr>')
    yravg = [v for v in YRPX.values() if v]
    t = ['<th class="rowh avgrow">多年均价</th>'] + \
        [f'<td class="num sum2">{PXAVG[str(m)]:.2f}</td>' for m in range(1, 13)] + \
        [f'<td class="num sum2">{sum(yravg)/len(yravg):.2f}</td>']
    r11.append('<tr class="avgrow">' + ''.join(t) + '</tr>')
    table11 = ('<table class="mx"><thead><tr><th class="rowh">年份</th>'
               + ''.join(f'<th>{h}</th>' for h in MH) + '<th class="sumh">年均价</th></tr></thead><tbody>'
               + ''.join(r11) + '</tbody></table>')

    # ---- 表 一 逐月涨跌幅 ----
    r1 = []
    for y in years:
        t = [f'<th class="rowh">{y}</th>'] + [pct_cell(M[f'{y}-{m:02d}']) for m in range(1, 13)]
        t.append(pct_cell(YR.get(str(y)), scale=40, bold=True))
        r1.append('<tr>' + ''.join(t) + '</tr>')
    t = ['<th class="rowh avgrow">多年均值</th>']
    for m in range(1, 13):
        vals = [M[f'{y}-{m:02d}'] for y in years if M[f'{y}-{m:02d}'] is not None]
        a = sum(vals) / len(vals)
        bg = 'rgba(220,60,50,.7)' if a > 0 else 'rgba(30,170,110,.7)'
        t.append(f'<td class="num fw7" style="background:{bg};color:#fff">{a:+.2f}</td>')
    t.append('<td class="num sum2">—</td>')
    r1.append('<tr class="avgrow">' + ''.join(t) + '</tr>')
    t = ['<th class="rowh avgrow">上涨年数</th>']
    for m in range(1, 13):
        vals = [M[f'{y}-{m:02d}'] for y in years if M[f'{y}-{m:02d}'] is not None]
        w, n = sum(1 for v in vals if v > 0), len(vals)
        t.append(f'<td class="num2 {"wg" if w/n >= .6 else ("wr" if w/n <= .4 else "wm")}">{w}/{n}</td>')
    t.append('<td class="num2">—</td>')
    r1.append('<tr class="avgrow">' + ''.join(t) + '</tr>')
    table1 = ('<table class="mx"><thead><tr><th class="rowh">年份</th>'
              + ''.join(f'<th>{h}</th>' for h in MH) + '<th class="sumh">年度涨跌</th></tr></thead><tbody>'
              + ''.join(r1) + '</tbody></table>')

    # ---- 表 二 分组 ----
    r2 = []
    for lab in GN:
        y0 = int(lab[:4]) if lab[0].isdigit() else yb
        y1 = int(lab[5:9]) if lab[0].isdigit() else ye
        t = [f'<th class="rowh grpname">{lab}</th>']
        for m in range(1, 13):
            s = G[lab].get(str(m)) or G[lab].get(m)
            if not s:
                t.append('<td class="na">—</td>')
                continue
            av, win, n = s['avg'], s['win'], s['n']
            a = min(abs(av) / 8, 1.0)
            bg = (f'rgba(220,60,50,{0.05 + a * 0.55:.3f})' if av > 0 else
                  (f'rgba(30,170,110,{0.05 + a * 0.55:.3f})' if av < 0 else 'rgba(255,255,255,.03)'))
            wc = 'wg' if win >= 60 else ('wr' if win <= 40 else 'wm')
            t.append(f'<td class="grpc" style="background:{bg}"><b class="{"up" if av > 0 else "dn"}">{av:+.2f}%</b>'
                     f'<i class="{wc}">{win:.0f}% · n={n}</i></td>')
        yrr = [YR[str(y)] for y in years if y0 <= y <= y1 and YR.get(str(y)) is not None]
        t.append(f'<td class="num sum2 grpc">{sum(yrr)/len(yrr):+.2f}%</td>' if yrr else '<td class="na">—</td>')
        r2.append('<tr>' + ''.join(t) + '</tr>')
    table2 = ('<table class="mx"><thead><tr><th class="rowh">分组</th>'
              + ''.join(f'<th>{h}</th>' for h in MH) + '<th class="sumh">组内年均</th></tr></thead><tbody>'
              + ''.join(r2) + '</tbody></table>')

    # ---- 结论 ----
    def st(m):
        return G[GN[-1]][str(m)]
    best = sorted(range(1, 13), key=lambda m: -st(m)['avg'])[:4]
    worst = sorted(range(1, 13), key=lambda m: st(m)['avg'])[:4]
    shape = sorted(range(1, 13), key=lambda m: -(PXAVG[str(m)] or 0))
    lo = sorted(range(1, 13), key=lambda m: (PXAVG[str(m)] or 0))
    amp = (PXAVG[str(shape[0])] / PXAVG[str(lo[0])] - 1) * 100
    # 结构转折：全为正/全为负的月份
    mono = []
    for m in range(1, 13):
        signs = [(G[l][str(m)] or G[l].get(m)) for l in GN[:-1]]
        signs = [s['avg'] for s in signs if s]
        if signs and all(v > 0 for v in signs):
            mono.append(f'{MH[m-1]}（全 {len(signs)} 组为正）')
        if signs and all(v < 0 for v in signs):
            mono.append(f'{MH[m-1]}（全 {len(signs)} 组为负）')
    # 各组最强/最弱月
    grp_note = []
    for l in GN[:-1]:
        avgs = [(m, G[l][str(m)]['avg']) for m in range(1, 13) if G[l].get(str(m))]
        if not avgs:
            continue
        gb = max(avgs, key=lambda x: x[1])
        gw = min(avgs, key=lambda x: x[1])
        grp_note.append(f'{l}：最强 {MH[gb[0]-1]} {gb[1]:+.2f}% / 最弱 {MH[gw[0]-1]} {gw[1]:+.2f}%')
    concl = f'''<ul>
<li><b>最强月份</b>：{'、'.join(f"{MH[m-1]} {st(m)['avg']:+.2f}%（胜率 {st(m)['win']:.0f}%）" for m in best)}。</li>
<li><b>最弱月份</b>：{'、'.join(f"{MH[m-1]} {st(m)['avg']:+.2f}%（胜率 {st(m)['win']:.0f}%）" for m in worst)}。</li>
<li><b>跨周期结构一致的月份</b>：{'；'.join(mono) if mono else '无（各分组方向不一致）'}。</li>
<li><b>价格水平的季节形状（见表 1.1）</b>：{yb}-{ye} 平均月价最高 {MH[shape[0]-1]} {PXAVG[str(shape[0])]:.2f}、{MH[shape[1]-1]} {PXAVG[str(shape[1])]:.2f}；最低 {MH[lo[0]-1]} {PXAVG[str(lo[0])]:.2f}、{MH[lo[1]-1]} {PXAVG[str(lo[1])]:.2f}；极差 <b>{amp:.1f}%</b>。</li>
<li><b>分组对照</b>：{'；'.join(grp_note)}。</li>
<li><b>样本量提醒</b>：{ye} 年数据仅到 {d.get("last_month", 12)} 月，相关月份的分组 n 值小于其他组。</li>
</ul>{extra}'''

    unit_note = unit
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#0d1117;--bg2:#151b23;--bg3:#1c232d;--line:#2a323d;--tx:#e6edf3;--tx2:#9aa7b4;--tx3:#6b7684;--up:#ff5f52;--dn:#2fbf7a;--acc:#e8b04b;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;padding:34px 22px 60px;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1620px;margin:0 auto}}
h1{{font-size:23px;margin:0 0 6px;letter-spacing:.3px}}
.sub{{color:var(--tx2);font-size:13px;margin-bottom:24px}}
.sub b{{color:var(--acc);font-weight:600}}
h2{{font-size:16px;margin:32px 0 6px;padding-left:11px;border-left:3px solid var(--acc)}}
.note{{color:var(--tx3);font-size:12.5px;margin:0 0 12px;padding-left:14px}}
.card{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto}}
table{{border-collapse:separate;border-spacing:3px;width:100%;font-size:12px}}
th{{background:var(--bg3);color:var(--tx2);font-weight:600;padding:6px;border-radius:4px;white-space:nowrap;font-size:12px;text-align:center}}
.rowh{{position:sticky;left:0;z-index:3;background:var(--bg3);color:var(--tx);min-width:76px;text-align:left;padding-left:10px;font-weight:700}}
.grpname{{min-width:112px}}
.sumh{{color:var(--acc)}}
td{{text-align:center;padding:5px 6px;border-radius:4px;background:rgba(255,255,255,.025);font-variant-numeric:tabular-nums;white-space:nowrap}}
.num{{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:-.2px}}
.fw7{{font-weight:700}}
.sum2{{background:var(--bg3);color:var(--tx2);font-family:"SF Mono",monospace;font-size:12px}}
.avgrow th{{background:#222a35;color:var(--acc)}}
.up,.pos{{color:var(--up)}} .dn,.neg{{color:var(--dn)}} .fl,.flat{{color:var(--tx3)}}
.wg{{color:#ff9a91}} .wr{{color:#6fd8a8}} .wm{{color:var(--tx2)}}
.na{{color:#3a424d}}
.num2{{font-family:"SF Mono",ui-monospace,Menlo,monospace;padding:4px 6px}}
.num2 b{{display:block;font-size:13px;font-weight:700;letter-spacing:-.3px}}
.num2 i.mo{{display:block;font-style:normal;font-size:9.5px;opacity:.62;margin-top:1px}}
.grpc{{padding:7px 6px}}
.grpc b{{display:block;font-family:"SF Mono",monospace;font-size:13.5px;font-weight:700;letter-spacing:-.3px}}
.grpc i{{display:block;font-style:normal;font-size:10px;margin-top:2px}}
.legend{{display:flex;gap:18px;flex-wrap:wrap;color:var(--tx3);font-size:12px;margin-top:12px;padding-left:14px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}}
ul{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:16px 20px 16px 36px;margin:12px 0 0}}
li{{margin:7px 0;color:var(--tx2)}} li b{{color:var(--tx)}}
.foot{{color:var(--tx3);font-size:12px;margin-top:28px;padding-top:14px;border-top:1px solid var(--line)}}
</style></head><body><div class="wrap">

<h1>{title}</h1>
<div class="sub">样本区间 <b>{yb}-01 ~ {ye}-{d.get("last_month", 12):02d}</b>（{len(years)} 个年份）　·　表格方向：<b>行为年份、列为月份</b>　·　口径：月环比涨跌幅 = 本月收盘 / 上月收盘 − 1　·　颜色：<span style="color:var(--up)">红=上涨/高于年均</span> / <span style="color:var(--dn)">绿=下跌/低于年均</span></div>

<h2>表 1.1　逐月月末收盘价（绝对价格，{unit_note}）</h2>
<p class="note">格内大字为该月月末收盘价；下方小字为当月环比涨跌幅。底色按「该月价格相对<u>当年均价</u>的偏离」着色——红=高于年内均价、绿=低于。末列为 12 个月均价。</p>
<div class="card">{table11}</div>
<div class="legend"><span><i style="background:rgba(220,60,50,.5)"></i>高于年内均价</span>
<span><i style="background:rgba(30,170,110,.5)"></i>低于年内均价</span><span style="margin-left:8px">小字：当月环比涨跌幅</span></div>

<h2>表 一　逐月涨跌幅矩阵（%）</h2>
<p class="note">格内为当月环比涨跌幅。末列「年度涨跌」= 当年 12 月末收盘 / 上年 12 月末收盘 − 1。倒数两行为多年均值与上涨年数。</p>
<div class="card">{table1}</div>
<div class="legend"><span><i style="background:rgba(220,60,50,.68)"></i>涨 ≥ +10%</span>
<span><i style="background:rgba(220,60,50,.3)"></i>温和上涨</span>
<span><i style="background:rgba(30,170,110,.3)"></i>温和下跌</span>
<span><i style="background:rgba(30,170,110,.68)"></i>跌 ≥ −10%</span></div>

<h2>表 二　5 年分组平均表现（行=分组，列=月份）</h2>
<p class="note">每组内同月份取算术平均。大字为平均涨跌幅，小字为上涨年份占比（胜率）与样本数 n。末列为该组内各年「年度涨跌」的平均。</p>
<div class="card">{table2}</div>

<h2>主要结论</h2>
<div class="card">{concl}</div>

<div class="foot">{source}<br>红色=上涨、绿色=下跌（国内市场习惯口径）</div>

</div></body></html>'''


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--unit', default='美分/磅')
    ap.add_argument('--source', default='')
    ap.add_argument('--last-month', type=int, default=12)
    ap.add_argument('--extra', default='')
    a = ap.parse_args()
    d = json.load(open(a.json))
    d['last_month'] = a.last_month
    open(a.out, 'w').write(build(d, a.title, a.unit, a.source, a.extra))
    print('written', a.out)
