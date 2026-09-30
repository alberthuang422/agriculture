#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把多品种「月度季节性」合并成一个 Tab 版深色报告，并内置「横纵坐标翻转」开关。

用法：
  python3 gen_seasonality_tabs_html.py --out reports/xxx.html \
      --set 'key=ct08|tab=棉花（ICE 2号）|json=/tmp/ct_2008.json|unit=美分/磅|last=9|source=...' \
      --set 'key=sb08|tab=白糖（ICE 11号）|json=/tmp/sb_2008.json|unit=美分/磅|last=9|source=...'
"""
import json, argparse, html

MH = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']


def conclusions(d):
    G = d['groups']
    GN = d['group_order']
    years, PXAVG = d['years'], d['px_avg']
    allg = G[GN[-1]]

    def st(m):
        return allg[str(m)]

    best = sorted(range(1, 13), key=lambda m: -st(m)['avg'])[:4]
    worst = sorted(range(1, 13), key=lambda m: st(m)['avg'])[:4]
    shape = sorted(range(1, 13), key=lambda m: -(PXAVG[str(m)] or 0))
    lo = sorted(range(1, 13), key=lambda m: (PXAVG[str(m)] or 0))
    amp = (PXAVG[str(shape[0])] / PXAVG[str(lo[0])] - 1) * 100
    mono = []
    for m in range(1, 13):
        signs = [G[l][str(m)]['avg'] for l in GN[:-1] if G[l].get(str(m))]
        if signs and all(v > 0 for v in signs):
            mono.append(f'{MH[m-1]}（{len(signs)} 组全为正）')
        if signs and all(v < 0 for v in signs):
            mono.append(f'{MH[m-1]}（{len(signs)} 组全为负）')
    grp = []
    for l in GN[:-1]:
        av = [(m, G[l][str(m)]['avg']) for m in range(1, 13) if G[l].get(str(m))]
        if av:
            b, w = max(av, key=lambda x: x[1]), min(av, key=lambda x: x[1])
            grp.append(f'{l}：最强 {MH[b[0]-1]} {b[1]:+.2f}% / 最弱 {MH[w[0]-1]} {w[1]:+.2f}%')
    return f'''<ul>
<li><b>最强月份</b>：{'、'.join(f"{MH[m-1]} {st(m)['avg']:+.2f}%（胜率 {st(m)['win']:.0f}%）" for m in best)}。</li>
<li><b>最弱月份</b>：{'、'.join(f"{MH[m-1]} {st(m)['avg']:+.2f}%（胜率 {st(m)['win']:.0f}%）" for m in worst)}。</li>
<li><b>跨分组方向一致的月份</b>：{'；'.join(mono) if mono else '无（各分组方向不一致）'}。</li>
<li><b>价格水平的季节形状</b>：{years[0]}-{years[-1]} 平均月价最高 {MH[shape[0]-1]} {PXAVG[str(shape[0])]:.2f}、{MH[shape[1]-1]} {PXAVG[str(shape[1])]:.2f}；最低 {MH[lo[0]-1]} {PXAVG[str(lo[0])]:.2f}、{MH[lo[1]-1]} {PXAVG[str(lo[1])]:.2f}；极差 <b>{amp:.1f}%</b>。</li>
<li><b>分组对照</b>：{'；'.join(grp)}。</li>
</ul>'''


def build_set(spec):
    kv = dict(p.split('=', 1) for p in spec.split('|'))
    d = json.load(open(kv['json']))
    return {
        'key': kv['key'],
        'tab': kv.get('tab', kv['key']),
        'unit': kv.get('unit', '美分/磅'),
        'last': int(kv.get('last', 12)),
        'source': kv.get('source', ''),
        'extra': open(kv['extra']).read() if kv.get('extra') else '',
        'data': d,
        'concl': conclusions(d),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--set', action='append', required=True, dest='sets')
    a = ap.parse_args()

    sets = [build_set(s) for s in a.sets]
    payload = []
    for s in sets:
        d = s['data']
        payload.append({
            'key': s['key'], 'tab': s['tab'], 'unit': s['unit'], 'last': s['last'],
            'source': s['source'], 'concl': s['concl'], 'extra': s['extra'],
            'years': d['years'], 'px': d['px'], 'matrix': d['matrix'],
            'yr_ret': d['yr_ret'], 'yr_px': d['yr_px'], 'px_avg': d['px_avg'],
            'groups': d['groups'], 'groupOrder': d['group_order'],
        })
    DATA = json.dumps(payload, ensure_ascii=False)

    tabs = ''.join(
        f'<button class="tab{" on" if i == 0 else ""}" data-k="{s["key"]}">{html.escape(s["tab"])}</button>'
        for i, s in enumerate(sets))

    htmldoc = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(a.title)}</title>
<style>
:root{{--bg:#0d1117;--bg2:#151b23;--bg3:#1c232d;--bg4:#222a35;--line:#2a323d;--tx:#e6edf3;--tx2:#9aa7b4;--tx3:#6b7684;--up:#ff5f52;--dn:#2fbf7a;--acc:#e8b04b;--blue:#56B4E9;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;padding:30px 22px 60px;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1660px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 4px;letter-spacing:.3px}}
.sub{{color:var(--tx2);font-size:13px;margin-bottom:16px}}
.bar{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0 4px;padding:10px 12px;background:var(--bg2);border:1px solid var(--line);border-radius:10px}}
.tabs{{display:flex;gap:8px;flex-wrap:wrap}}
.tab{{padding:6px 22px;font-size:13.5px;font-weight:600;border:1px solid var(--line);background:var(--bg3);color:var(--tx2);border-radius:8px;cursor:pointer;font-family:inherit}}
.tab:hover{{background:#1f2833;color:var(--tx)}}
.tab.on{{background:var(--acc);color:#1a1200;border-color:var(--acc)}}
.sp{{flex:1}}
.flip{{padding:6px 16px;font-size:13px;font-weight:600;border:1px solid var(--blue);background:var(--bg3);color:var(--blue);border-radius:8px;cursor:pointer;font-family:inherit;white-space:nowrap}}
.flip:hover{{background:#16222c}}
.flip.on{{background:var(--blue);color:#04161f;border-color:var(--blue)}}
.metaline{{color:var(--tx3);font-size:12.5px;margin:10px 0 2px;padding-left:2px}}
.metaline b{{color:var(--acc)}}
h2{{font-size:16px;margin:28px 0 6px;padding-left:11px;border-left:3px solid var(--acc)}}
.note{{color:var(--tx3);font-size:12.5px;margin:0 0 12px;padding-left:14px}}
.card{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto}}
table{{border-collapse:separate;border-spacing:3px;width:100%;font-size:12px}}
th{{background:var(--bg3);color:var(--tx2);font-weight:600;padding:6px;border-radius:4px;white-space:nowrap;font-size:12px;text-align:center}}
.rowh{{position:sticky;left:0;z-index:3;background:var(--bg3);color:var(--tx);min-width:76px;text-align:left;padding-left:10px;font-weight:700}}
.grpname{{min-width:118px}}
.acc{{color:var(--acc)}}
td{{text-align:center;padding:5px 6px;border-radius:4px;background:rgba(255,255,255,.025);font-variant-numeric:tabular-nums;white-space:nowrap}}
.num{{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:-.2px}}
.fw7{{font-weight:700}}
.sum2{{background:var(--bg3);color:var(--tx2);font-family:"SF Mono",monospace;font-size:12px}}
.avgrow th{{background:var(--bg4);color:var(--acc)}}
.up{{color:var(--up)}} .dn{{color:var(--dn)}} .fl{{color:var(--tx3)}}
.wg{{color:#ff9a91}} .wr{{color:#6fd8a8}} .wm{{color:var(--tx2)}}
.na{{color:#3a424d}}
.num2{{font-family:"SF Mono",ui-monospace,Menlo,monospace;padding:4px 6px}}
.num2 b{{display:block;font-size:13px;font-weight:700;letter-spacing:-.3px}}
.num2 i.mo{{display:block;font-style:normal;font-size:9.5px;opacity:.62;margin-top:1px}}
.grpc{{padding:7px 6px}}
.grpc b{{display:block;font-family:"SF Mono",monospace;font-size:13.5px;font-weight:700;letter-spacing:-.3px}}
.grpc i{{display:block;font-style:normal;font-size:10px;margin-top:2px}}
.legend{{display:flex;gap:18px;flex-wrap:wrap;color:var(--tx3);font-size:12px;margin-top:10px;padding-left:14px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}}
ul{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:16px 20px 16px 36px;margin:12px 0 0}}
li{{margin:7px 0;color:var(--tx2)}} li b{{color:var(--tx)}}
.foot{{color:var(--tx3);font-size:12px;margin-top:28px;padding-top:14px;border-top:1px solid var(--line);line-height:1.8}}
</style></head><body><div class="wrap">

<h1>{html.escape(a.title)}</h1>
<div class="sub">表格方向 <b>行 = 年份 / 分组，列 = 1–12 月</b>　·　口径：月环比涨跌幅 = 本月收盘 / 上月收盘 − 1　·　颜色：<span class="up">红=上涨/高于年均</span> / <span class="dn">绿=下跌/低于年均</span></div>

<div class="bar">
  <div class="tabs" id="tabs">{tabs}</div>
  <div class="sp"></div>
  <button class="flip" id="btnFlip" type="button" title="把三张表的横纵坐标对调（行↔列）">⇄ 翻转横纵坐标</button>
</div>
<div class="metaline" id="meta"></div>

<h2>表 1.1　逐月月末收盘价（绝对价格）</h2>
<p class="note">格内大字为该月月末收盘价；下方小字为当月环比涨跌幅。底色按「该月价格相对<u>当年均价</u>的偏离」着色——红=高于年内均价、绿=低于。末列/末行为均价汇总。</p>
<div class="card" id="t11"></div>

<h2>表 一　逐月涨跌幅矩阵（%）</h2>
<p class="note">格内为当月环比涨跌幅。汇总列为「年度涨跌」= 当年 12 月末收盘 / 上年 12 月末收盘 − 1；汇总行为多年均值与上涨年数。</p>
<div class="card" id="t1"></div>
<div class="legend"><span><i style="background:rgba(220,60,50,.68)"></i>涨 ≥ +10%</span>
<span><i style="background:rgba(220,60,50,.3)"></i>温和上涨</span>
<span><i style="background:rgba(30,170,110,.3)"></i>温和下跌</span>
<span><i style="background:rgba(30,170,110,.68)"></i>跌 ≥ −10%</span></div>

<h2>表 二　分组平均表现</h2>
<p class="note">每组内同月份取算术平均。大字为平均涨跌幅，小字为上涨年份占比（胜率）与样本数 n。汇总列为该组内各年「年度涨跌」的平均。</p>
<div class="card" id="t2"></div>

<h2>主要结论</h2>
<div class="card" id="concl"></div>
<div id="extra"></div>

<div class="foot" id="foot"></div>
</div>

<script>
const DATA = {DATA};
const MH = {json.dumps(MH, ensure_ascii=False)};
let cur = 0, trans = false;
const pad = m => String(m).padStart(2, '0');
const sgn = v => (v > 0 ? '+' : '') + v.toFixed(2);
const num = v => (v == null ? '—' : v.toFixed(2));

function heat(v, scale, strong) {{
  if (v == null) return {{h: '—', cls: 'na', style: ''}};
  const a = Math.min(Math.abs(v) / scale, 1);
  let bg, fg;
  if (v > 0) {{ bg = `rgba(220,60,50,${{(0.06 + a * 0.62).toFixed(3)}})`; fg = a < 0.5 ? '#ffb3ad' : '#fff'; }}
  else if (v < 0) {{ bg = `rgba(30,170,110,${{(0.06 + a * 0.62).toFixed(3)}})`; fg = a < 0.5 ? '#9de3c4' : '#fff'; }}
  else {{ bg = 'rgba(255,255,255,.03)'; fg = '#8b949e'; }}
  return {{h: sgn(v), cls: 'num' + (strong ? ' fw7' : ''), style: `background:${{bg}};color:${{fg}}`}};
}}

function pxCell(d, y, m) {{
  const k = y + '-' + pad(m), v = d.px[k];
  if (v == null) return {{h: '—', cls: 'na', style: ''}};
  const ya = d.yr_px[y] != null ? d.yr_px[y] : v;
  const dev = ya ? v / ya - 1 : 0, a = Math.min(Math.abs(dev) / 0.20, 1);
  let bg, fg;
  if (dev > 0) {{ bg = `rgba(220,60,50,${{(0.04 + a * 0.46).toFixed(3)}})`; fg = a < 0.5 ? '#ffc0ba' : '#fff'; }}
  else {{ bg = `rgba(30,170,110,${{(0.04 + a * 0.46).toFixed(3)}})`; fg = a < 0.5 ? '#a8e8cc' : '#fff'; }}
  const mom = d.matrix[k];
  const momHtml = mom == null ? '<i class="mo fl">n/a</i>'
    : `<i class="mo ${{mom > 0 ? 'up' : (mom < 0 ? 'dn' : 'fl')}}">${{sgn(mom)}}%</i>`;
  return {{h: `<b>${{v.toFixed(2)}}</b>${{momHtml}}`, cls: 'num2', style: `background:${{bg}};color:${{fg}}`}};
}}

function spec11(d) {{
  const cols = MH.map(h => ({{label: h, cls: ''}})).concat([{{label: '年均价', cls: 'acc'}}]);
  const rows = d.years.map(y => ({{
    label: y, cls: 'rowh',
    cells: MH.map((_, i) => pxCell(d, y, i + 1))
      .concat([{{h: num(d.yr_px[y]), cls: 'num sum2', style: ''}}])
  }}));
  const all = d.years.map(y => d.yr_px[y]).filter(v => v != null);
  const gm = all.reduce((s, v) => s + v, 0) / all.length;
  const tails = [{{
    label: '多年均价', cls: 'rowh avgrow',
    cells: MH.map((_, i) => ({{h: num(d.px_avg[String(i + 1)]), cls: 'num sum2', style: ''}}))
      .concat([{{h: gm.toFixed(2), cls: 'num sum2', style: ''}}])
  }}];
  return {{corner: '年份', cornerT: '月份', cols, rows, tails}};
}}

function spec1(d) {{
  const cols = MH.map(h => ({{label: h, cls: ''}})).concat([{{label: '年度涨跌', cls: 'acc'}}]);
  const rows = d.years.map(y => ({{
    label: y, cls: 'rowh',
    cells: MH.map((_, i) => heat(d.matrix[y + '-' + pad(i + 1)], 20, false))
      .concat([heat(d.yr_ret[y], 40, true)])
  }}));
  const avgCells = MH.map((_, i) => {{
    const v = d.years.map(y => d.matrix[y + '-' + pad(i + 1)]).filter(x => x != null);
    const a = v.reduce((s, x) => s + x, 0) / v.length;
    return {{h: sgn(a), cls: 'num fw7', style: `background:${{a > 0 ? 'rgba(220,60,50,.7)' : 'rgba(30,170,110,.7)'}};color:#fff`}};
  }}).concat([{{h: '—', cls: 'num sum2', style: ''}}]);
  const winCells = MH.map((_, i) => {{
    const v = d.years.map(y => d.matrix[y + '-' + pad(i + 1)]).filter(x => x != null);
    const w = v.filter(x => x > 0).length, r = w / v.length;
    return {{h: w + '/' + v.length, cls: 'num2 ' + (r >= .6 ? 'wg' : (r <= .4 ? 'wr' : 'wm')), style: ''}};
  }}).concat([{{h: '—', cls: 'num2', style: ''}}]);
  return {{corner: '年份', cornerT: '月份', cols, rows, tails: [
    {{label: '多年均值', cls: 'rowh avgrow', cells: avgCells}},
    {{label: '上涨年数', cls: 'rowh avgrow', cells: winCells}}
  ]}};
}}

function spec2(d) {{
  const cols = MH.map(h => ({{label: h, cls: ''}})).concat([{{label: '组内年均', cls: 'acc'}}]);
  const rows = d.groupOrder.map(lab => {{
    const g = d.groups[lab];
    const cells = MH.map((_, i) => {{
      const s = g[String(i + 1)];
      if (!s) return {{h: '—', cls: 'na', style: ''}};
      const a = Math.min(Math.abs(s.avg) / 8, 1);
      const bg = s.avg > 0 ? `rgba(220,60,50,${{(0.05 + a * 0.55).toFixed(3)}})`
        : (s.avg < 0 ? `rgba(30,170,110,${{(0.05 + a * 0.55).toFixed(3)}})` : 'rgba(255,255,255,.03)');
      const wc = s.win >= 60 ? 'wg' : (s.win <= 40 ? 'wr' : 'wm');
      return {{h: `<b class="${{s.avg > 0 ? 'up' : 'dn'}}">${{sgn(s.avg)}}%</b><i class="${{wc}}">${{Math.round(s.win)}}% · n=${{s.n}}</i>`,
        cls: 'grpc', style: `background:${{bg}}`}};
    }});
    const y0 = parseInt(lab.slice(0, 4)), y1 = parseInt(lab.slice(5, 9));
    const yr = d.years.filter(y => y >= y0 && y <= y1).map(y => d.yr_ret[y]).filter(v => v != null);
    const av = yr.length ? yr.reduce((s, v) => s + v, 0) / yr.length : null;
    cells.push(av == null ? {{h: '—', cls: 'na', style: ''}} : {{h: sgn(av) + '%', cls: 'num sum2 grpc', style: ''}});
    return {{label: lab, cls: 'rowh grpname', cells}};
  }});
  return {{corner: '分组', cornerT: '月份', cols, rows, tails: []}};
}}

function renderTable(spec, tr) {{
  const rowList = spec.rows.concat(spec.tails || []);
  const cellHtml = c => (c ? `<td class="${{c.cls || ''}}" style="${{c.style || ''}}">${{c.h}}</td>` : '<td class="na">—</td>');
  let thead, tbody;
  if (!tr) {{
    thead = `<tr><th class="rowh">${{spec.corner}}</th>` + spec.cols.map(c => `<th class="${{c.cls || ''}}">${{c.label}}</th>`).join('') + '</tr>';
    tbody = rowList.map(r => `<tr><th class="${{r.cls}}">${{r.label}}</th>` + r.cells.map(cellHtml).join('') + '</tr>').join('');
  }} else {{
    thead = `<tr><th class="rowh">${{spec.cornerT}}</th>` + rowList.map(r => `<th class="${{r.cls === 'rowh avgrow' ? 'acc' : ''}}">${{r.label}}</th>`).join('') + '</tr>';
    tbody = spec.cols.map((c, j) => `<tr><th class="rowh ${{c.cls === 'acc' ? 'avgrow' : ''}}">${{c.label}}</th>`
      + rowList.map(r => cellHtml(r.cells[j])).join('') + '</tr>').join('');
  }}
  return `<table><thead>${{thead}}</thead><tbody>${{tbody}}</tbody></table>`;
}}

function render() {{
  const d = DATA[cur];
  document.getElementById('t11').innerHTML = renderTable(spec11(d), trans);
  document.getElementById('t1').innerHTML = renderTable(spec1(d), trans);
  document.getElementById('t2').innerHTML = renderTable(spec2(d), trans);
  document.getElementById('concl').innerHTML = d.concl;
  document.getElementById('extra').innerHTML = d.extra || '';
  document.getElementById('meta').innerHTML =
    `样本区间 <b>${{d.years[0]}}-01 ~ ${{d.years[d.years.length - 1]}}-${{String(d.last).padStart(2, '0')}}</b>　·　${{d.years.length}} 个年份　·　单位 <b>${{d.unit}}</b>　·　当前方向：<b>${{trans ? '行 = 月份，列 = 年份/分组' : '行 = 年份/分组，列 = 月份'}}</b>`;
  document.getElementById('foot').innerHTML = d.source;
  document.querySelectorAll('#tabs .tab').forEach((b, i) => b.classList.toggle('on', i === cur));
}}

document.querySelectorAll('#tabs .tab').forEach((b, i) => b.addEventListener('click', () => {{ cur = i; render(); }}));
document.getElementById('btnFlip').addEventListener('click', e => {{
  trans = !trans; e.currentTarget.classList.toggle('on', trans);
  e.currentTarget.textContent = trans ? '⇄ 已翻转（点击还原）' : '⇄ 翻转横纵坐标';
  render();
}});
render();
</script>
</body></html>'''
    open(a.out, 'w').write(htmldoc)
    print('written', a.out, len(htmldoc))


if __name__ == '__main__':
    main()
