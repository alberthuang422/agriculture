#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 /tmp/ct_monthly.json 生成 ICE 棉花月度季节性 HTML 报告（深色主题 · 横纵坐标对调版）
   表 1.1 = 逐月收盘价（绝对价格）  表 一 = 逐月涨跌幅  表 二 = 5 年分组平均
"""
import json

d = json.load(open('/tmp/ct_monthly.json'))
years, M, PX, YR, YRPX, PXAVG, G = d['years'], d['matrix'], d['px'], d['yr_ret'], d['yr_px'], d['px_avg'], d['groups']
MH = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']


def pct_cell(v, scale=20.0, bold=False, extra=''):
    if v is None:
        return f'<td class="na">{extra or "—"}</td>'
    a = min(abs(v) / scale, 1.0)
    if v > 0:
        bg, fg = f'rgba(220,60,50,{0.06 + a * 0.62:.3f})', ('#ffb3ad' if a < 0.5 else '#fff')
    elif v < 0:
        bg, fg = f'rgba(30,170,110,{0.06 + a * 0.62:.3f})', ('#9de3c4' if a < 0.5 else '#fff')
    else:
        bg, fg = 'rgba(255,255,255,.03)', '#8b949e'
    b = ' fw7' if bold else ''
    return f'<td class="num{b}" style="background:{bg};color:{fg}">{v:+.2f}</td>'


# ================= 表 1.1：逐月收盘价（绝对价格） =================
def px_cell(y, m):
    v, mom = PX[f'{y}-{m:02d}'], M[f'{y}-{m:02d}']
    if v is None:
        return '<td class="na">—</td>'
    yr_avg = YRPX[str(y)] or v
    dev = (v / yr_avg - 1) if yr_avg else 0
    a = min(abs(dev) / 0.20, 1.0)
    if dev > 0:
        bg, fg = f'rgba(220,60,50,{0.04 + a * 0.46:.3f})', ('#ffc0ba' if a < 0.5 else '#fff')
    else:
        bg, fg = f'rgba(30,170,110,{0.04 + a * 0.46:.3f})', ('#a8e8cc' if a < 0.5 else '#fff')
    if mom is None:
        s = '<i class="mo n">n/a</i>'
    else:
        c = 'up' if mom > 0 else ('dn' if mom < 0 else 'fl')
        s = f'<i class="mo {c}">{mom:+.2f}%</i>'
    return f'<td class="num2" style="background:{bg};color:{fg}"><b>{v:.2f}</b>{s}</td>'


rows11 = []
for y in years:
    tds = [f'<th class="rowh">{y}</th>']
    for m in range(1, 13):
        tds.append(px_cell(y, m))
    tds.append(f'<td class="num sum2">{YRPX[str(y)]:.2f}</td>' if YRPX[str(y)] else '<td class="na">—</td>')
    rows11.append('<tr>' + ''.join(tds) + '</tr>')
# 末行：19 年平均价
avg_tds = ['<th class="rowh avgrow">19年均价</th>']
for m in range(1, 13):
    v = PXAVG[str(m)]
    avg_tds.append(f'<td class="num sum2">{v:.2f}</td>')
avg_tds.append(f'<td class="num sum2">{sum(YRPX.values())/len(YRPX):.2f}</td>')
rows11.append('<tr class="avgrow">' + ''.join(avg_tds) + '</tr>')
table11 = ('<table class="mx"><thead><tr><th class="rowh">年份</th>'
           + ''.join(f'<th>{h}</th>' for h in MH) + '<th class="sumh">年均价</th></tr></thead><tbody>'
           + ''.join(rows11) + '</tbody></table>')

# ================= 表 一：逐月涨跌幅（%） =================
rows1 = []
for y in years:
    tds = [f'<th class="rowh">{y}</th>']
    for m in range(1, 13):
        tds.append(pct_cell(M[f'{y}-{m:02d}']))
    tds.append(pct_cell(YR[str(y)], scale=40, bold=True))
    rows1.append('<tr>' + ''.join(tds) + '</tr>')

avg1 = ['<th class="rowh avgrow">19年均值</th>']
for m in range(1, 13):
    vals = [M[f'{y}-{m:02d}'] for y in years if M[f'{y}-{m:02d}'] is not None]
    a = sum(vals) / len(vals)
    bg = 'rgba(220,60,50,.7)' if a > 0 else 'rgba(30,170,110,.7)'
    avg1.append(f'<td class="num fw7" style="background:{bg};color:#fff">{a:+.2f}</td>')
avg1.append('<td class="num sum2">—</td>')
rows1.append('<tr class="avgrow">' + ''.join(avg1) + '</tr>')

win1 = ['<th class="rowh avgrow">上涨年数</th>']
for m in range(1, 13):
    vals = [M[f'{y}-{m:02d}'] for y in years if M[f'{y}-{m:02d}'] is not None]
    w, n = sum(1 for v in vals if v > 0), len(vals)
    cls = 'wg' if w / n >= .6 else ('wr' if w / n <= .4 else 'wm')
    win1.append(f'<td class="num2 {cls}">{w}/{n}</td>')
win1.append('<td class="num2">—</td>')
rows1.append('<tr class="avgrow">' + ''.join(win1) + '</tr>')

table1 = ('<table class="mx"><thead><tr><th class="rowh">年份</th>'
          + ''.join(f'<th>{h}</th>' for h in MH) + '<th class="sumh">年度涨跌</th></tr></thead><tbody>'
          + ''.join(rows1) + '</tbody></table>')

# ================= 表 二：5 年分组（行=组，列=月份） =================
GN = ['2008-2012', '2013-2017', '2018-2022', '2023-2026', '全样本 2008-2026']
rows2 = []
for lab in GN:
    y0 = int(lab[:4]) if lab[0].isdigit() else 2008
    y1 = int(lab[5:9]) if lab[0].isdigit() else 2026
    tds = [f'<th class="rowh grpname">{lab}</th>']
    for m in range(1, 13):
        s = G[lab][str(m)] or G[lab][m]
        if not s:
            tds.append('<td class="na">—</td>')
            continue
        av, win, n = s['avg'], s['win'], s['n']
        a = min(abs(av) / 8, 1.0)
        if av > 0:
            bg = f'rgba(220,60,50,{0.05 + a * 0.55:.3f})'
        elif av < 0:
            bg = f'rgba(30,170,110,{0.05 + a * 0.55:.3f})'
        else:
            bg = 'rgba(255,255,255,.03)'
        wcls = 'wg' if win >= 60 else ('wr' if win <= 40 else 'wm')
        tds.append(f'<td class="grpc" style="background:{bg}">'
                   f'<b class="{"up" if av > 0 else "dn"}">{av:+.2f}%</b>'
                   f'<i class="{wcls}">{win:.0f}% · n={n}</i></td>')
    yrr = [YR[str(y)] for y in years if y0 <= y <= y1 and YR.get(str(y)) is not None]
    tds.append(f'<td class="num sum2 grpc">{sum(yrr)/len(yrr):+.2f}%</td>' if yrr else '<td class="na">—</td>')
    rows2.append('<tr>' + ''.join(tds) + '</tr>')

body2 = ''.join(rows2)
head2 = ''.join(f'<th>{h}</th>' for h in MH)
table2 = (f'<table class="mx"><thead><tr><th class="rowh">分组</th>{head2}'
          f'<th class="sumh">组内年均</th></tr></thead><tbody>{body2}</tbody></table>')

# ================= 结论 =================
def st(m):
    return G['全样本 2008-2026'][str(m)]
best = sorted(range(1, 13), key=lambda m: -st(m)['avg'])[:4]
worst = sorted(range(1, 13), key=lambda m: st(m)['avg'])[:4]
concl = f'''<ul>
<li><b>最强月份</b>：{'、'.join(f"{MH[m-1]} {st(m)['avg']:+.2f}%（胜率 {st(m)['win']:.0f}%）" for m in best)}。<b>12 月</b>在 2008-2012 组胜率高达 100%，是全样本最稳定的多头月份。</li>
<li><b>最弱月份</b>：{'、'.join(f"{MH[m-1]} {st(m)['avg']:+.2f}%（胜率 {st(m)['win']:.0f}%）" for m in worst)}。<b>5 月</b>是唯一一个「四个分组全部为负」的月份，跨周期结构最一致的空头窗口。</li>
<li><b>结构转折（2018 起季节性重心后移）</b>：4 月由弱转强（2018-2022 组 +6.04%、胜率 80%），10 月由强转弱（2023-2026 组 −4.13%、胜率 <b>0%</b>）。与 2018/19 年度起中国抛储结束、进口需求前置有关。</li>
<li><b>价格水平的季节形状（见表 1.1）</b>：19 年平均月价呈「<b>春季高、夏秋低</b>」——3 月 84.69 / 4 月 84.67 为年内最高，7 月 76.11 / 9 月 75.67 最低，均值振幅约 12%。即价格在 3-4 月见季节性高点、7-9 月见季节性低点。</li>
<li><b>样本量提醒</b>：2026 年数据仅到 9 月，因此「2023-2026」组的 10-12 月只有 n=3，稳定性弱于其他分组；「19年均价」行的 2026 年也只含 1-9 月。</li>
</ul>'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ICE 棉花月线季节性统计（2008–2026）</title>
<style>
:root{{
  --bg:#0d1117; --bg2:#151b23; --bg3:#1c232d; --line:#2a323d;
  --tx:#e6edf3; --tx2:#9aa7b4; --tx3:#6b7684;
  --up:#ff5f52; --dn:#2fbf7a; --acc:#e8b04b;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);
  font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;
  padding:34px 22px 60px;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1620px;margin:0 auto}}
h1{{font-size:23px;margin:0 0 6px;letter-spacing:.3px}}
.sub{{color:var(--tx2);font-size:13px;margin-bottom:24px}}
.sub b{{color:var(--acc);font-weight:600}}
h2{{font-size:16px;margin:32px 0 6px;padding-left:11px;border-left:3px solid var(--acc)}}
.note{{color:var(--tx3);font-size:12.5px;margin:0 0 12px;padding-left:14px}}
.card{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;
  padding:14px;overflow:auto}}
table{{border-collapse:separate;border-spacing:3px;width:100%;font-size:12px}}
th{{background:var(--bg3);color:var(--tx2);font-weight:600;padding:6px 6px;
  border-radius:4px;white-space:nowrap;font-size:12px;text-align:center}}
.rowh{{position:sticky;left:0;z-index:3;background:var(--bg3);color:var(--tx);
  min-width:74px;text-align:left;padding-left:10px;font-weight:700}}
.grpname{{min-width:112px;font-size:12px}}
.sumh{{color:var(--acc)}}
td{{text-align:center;padding:5px 6px;border-radius:4px;background:rgba(255,255,255,.025);
  font-variant-numeric:tabular-nums;white-space:nowrap}}
.num{{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:-.2px}}
.fw7{{font-weight:700}}
.sum{{background:var(--bg3);font-weight:700;color:var(--tx)}}
.sum2{{background:var(--bg3);color:var(--tx2);font-family:"SF Mono",monospace;font-size:12px}}
.avgrow th{{background:#222a35;color:var(--acc)}}
.up,.pos{{color:var(--up)}} .dn,.neg{{color:var(--dn)}} .fl,.flat{{color:var(--tx3)}}
.wg{{color:#ff9a91}} .wr{{color:#6fd8a8}} .wm{{color:var(--tx2)}}
.na{{color:#3a424d}}
.num2{{font-family:"SF Mono",ui-monospace,Menlo,monospace;padding:4px 6px}}
.num2 b{{display:block;font-size:13px;font-weight:700;letter-spacing:-.3px}}
.num2 i.mo{{display:block;font-style:normal;font-size:9.5px;opacity:.62;margin-top:1px;letter-spacing:-.2px}}
.grpc{{padding:7px 6px}}
.grpc b{{display:block;font-family:"SF Mono",monospace;font-size:13.5px;font-weight:700;letter-spacing:-.3px}}
.grpc i{{display:block;font-style:normal;font-size:10px;margin-top:2px}}
.legend{{display:flex;gap:18px;flex-wrap:wrap;color:var(--tx3);font-size:12px;margin-top:12px;padding-left:14px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}}
ul{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;
  padding:16px 20px 16px 36px;margin:12px 0 0}}
li{{margin:7px 0;color:var(--tx2)}}
li b{{color:var(--tx)}}
.foot{{color:var(--tx3);font-size:12px;margin-top:28px;padding-top:14px;border-top:1px solid var(--line)}}
</style></head><body><div class="wrap">

<h1>ICE 棉花 2 号连续合约 · 月度季节性统计</h1>
<div class="sub">样本区间 <b>2008-01 ~ 2026-09</b>（{len(years)} 个年份）　·　表格方向：<b>行为年份、列为月份</b>　·　颜色：<span style="color:var(--up)">红=上涨/高于年均</span> / <span style="color:var(--dn)">绿=下跌/低于年均</span></div>

<h2>表 1.1　逐月月末收盘价（绝对价格，美分/磅）</h2>
<p class="note">格内大字为该月月末收盘价；下方小字为当月环比涨跌幅。底色按「该月价格相对<u>当年均价</u>的偏离」着色——红=高于年内均价、绿=低于。末列为 12 个月均价。</p>
<div class="card">{table11}</div>
<div class="legend"><span><i style="background:rgba(220,60,50,.5)"></i>高于年内均价</span>
<span><i style="background:rgba(30,170,110,.5)"></i>低于年内均价</span>
<span style="margin-left:8px">小字：当月环比涨跌幅</span></div>

<h2>表 一　逐月涨跌幅矩阵（%）</h2>
<p class="note">格内为当月环比涨跌幅（本月收盘 / 上月收盘 − 1）。末列「年度涨跌」= 当年 12 月末收盘 / 上年 12 月末收盘 − 1（2008 年因缺 2007-12 前值无法计算）。倒数两行为 19 年均值与上涨年数。</p>
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

<div class="foot">数据源：ICEUS_DLY_CT1!, 1M.csv（ICE 棉花 2 号连续合约月线，原文件自 1972-08 起）　·　脚本：scripts/ct_monthly_seasonality.py + scripts/gen_ct_seasonality_html.py<br>
红色=上涨、绿色=下跌（国内市场习惯口径）</div>

</div></body></html>'''

out = '/Users/alberthuang/agriculture/reports/ICE棉花月度季节性_2008-2026.html'
open(out, 'w').write(html)
print('written', out, len(html))
