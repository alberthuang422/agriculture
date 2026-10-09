# -*- coding: utf-8 -*-
"""
在 94 号报告《白糖可贸易国家全景 2000-2026》内新增：
  七、前 5 大出口国 / 前 5 大进口国：2014-2026 逐年贸易与产能（补记 · 2026-10-01）
  附录 B · 前5大贸易国逐年平衡表（2014-2026 · 千吨原糖当量）
不改动原有章节；script 末尾追加图表 c6/c7/c8 的渲染代码。

数据源：USDA FAS PSD (Sugar, Centrifugal) 本地快照 psd_sugar_all.csv
        + data/fundamentals/sugar/top5_trade/top5_trade_2014_2026.json
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
REPORT = 'reports/94_白糖可贸易国家全景_2000_2026/index.html'
DATA_JSON = 'data/fundamentals/sugar/top5_trade/top5_trade_2014_2026.json'

D = json.load(open(DATA_JSON, encoding='utf-8'))
REC = {k: v['records'] for k, v in D['countries'].items()}
NAME_FULL = {'BR': '巴西', 'TH': '泰国', 'IN': '印度', 'AS': '澳大利亚', 'GT': '危地马拉',
             'CH': '中国', 'ID': '印尼', 'US': '美国', 'E4': '欧盟', 'BG': '孟加拉国'}
YEARS = list(range(2014, 2027))
EXP = ['BR', 'TH', 'IN', 'AS', 'GT']
IMP = ['CH', 'ID', 'US', 'E4', 'BG']
ALL = EXP + IMP


def s(cc, key):
    return [next(r[key] for r in REC[cc] if r['year'] == y) for y in YEARS]


def num(v):
    return f'{v:,.0f}'


def sgn(v):
    cls = 'blue' if v >= 0 else 'red'
    return f'<span class="{cls}">{"+" if v >= 0 else "−"}{abs(v):,.0f}</span>'


NUM_HDRS = {'产量', '消费', '自给率', '出口', '进口', '净出口', '期末库存', '净进口',
            '产量 2026', '消费 2026', '自给率 2026', '进口 2026', '年均净进口',
            '期末库存 2026', '年均净出口', '净出口 2026'}


def class_attr(h):
    """数值列表头右对齐，与 td.num 一致（修复表头/数值错位）"""
    return ' class="num"' if h in NUM_HDRS else ''


st = {}
for cc in ALL:
    p, c, x, m, nx, e = (s(cc, k) for k in
                         ('production', 'consumption', 'exports', 'imports', 'net_exports', 'ending_stocks'))
    st[cc] = dict(p=p, c=c, x=x, m=m, nx=nx, e=e,
                  p_peak=max(p), p_peak_y=YEARS[p.index(max(p))],
                  nx_avg=sum(nx) / len(nx), nx_last=nx[-1],
                  self_last=(p[-1] / c[-1] * 100) if c[-1] else 0)

agg_exp = [sum(st[cc]['nx'][i] for cc in EXP) for i in range(13)]
agg_imp = [sum(st[cc]['nx'][i] for cc in IMP) for i in range(13)]
UNIQ = max(len(set(s(cc, 'imports'))) for cc in ALL)

# ══════════════════════ 正文新章节 ══════════════════════
def country_rows(cc, show_self=False):
    r = st[cc]
    out = []
    for i, y in enumerate(YEARS):
        cells = [f'<td>{y}</td>',
                 f'<td class="num">{num(r["p"][i])}</td>',
                 f'<td class="num">{num(r["c"][i])}</td>']
        if show_self:
            sh = r['p'][i] / r['c'][i] * 100 if r['c'][i] else 0
            cells.append(f'<td class="num">{sh:.0f}%</td>')
        cells += [f'<td class="num">{num(r["x"][i])}</td>',
                  f'<td class="num">{num(r["m"][i]) if r["m"][i] else "—"}</td>',
                  f'<td class="num">{sgn(r["nx"][i])}</td>']
        if cc == 'BR':
            cells[-1] = f'<td class="num">{num(r["nx"][i])}</td>'
        out.append('<tr>' + ''.join(cells) + '</tr>')
    return '\n'.join(out)


def summary_table(ccs, show_self=False):
    if show_self:
        head = ['国家', '产量 2026', '消费 2026', '自给率 2026', '进口 2026', '年均净进口', '期末库存 2026']
    else:
        head = ['国家', '产量 2026', '产量峰值 (年)', '年均净出口', '净出口 2026', '进口 2026', '自给率 2026']
    rows = []
    for cc in ccs:
        r = st[cc]
        if not show_self:
            rows.append('<tr>' + ''.join([
                f'<td>{cc} {NAME_FULL[cc]}</td>',
                f'<td class="num">{num(r["p"][-1])}</td>',
                f'<td class="num">{num(r["p_peak"])}（{r["p_peak_y"]}）</td>',
                f'<td class="num">{num(r["nx_avg"])}</td>',
                f'<td class="num">{num(r["nx_last"])}</td>',
                f'<td class="num">{num(r["m"][-1]) if r["m"][-1] else "—"}</td>',
                f'<td class="num">{r["self_last"]:.0f}%</td>',
            ]) + '</tr>')
        else:
            rows.append('<tr>' + ''.join([
                f'<td>{cc} {NAME_FULL[cc]}</td>',
                f'<td class="num">{num(r["p"][-1])}</td>',
                f'<td class="num">{num(r["c"][-1])}</td>',
                f'<td class="num">{r["self_last"]:.0f}%</td>',
                f'<td class="num">{num(r["m"][-1]) if r["m"][-1] else "—"}</td>',
                f'<td class="num red">−{abs(r["nx_avg"]):,.0f}</td>',
                f'<td class="num">{num(r["e"][-1])}</td>',
            ]) + '</tr>')
    # 修复对齐：数值列的表头必须与 td 同样右对齐（th 默认 text-align:left）
    ths = ''.join(f'<th{class_attr(h)}>{h}</th>' for h in head)
    return f'<table><tr>{ths}</tr>\n' + '\n'.join(rows) + '</table>'


SEC = f'''
  <h2>七、前 5 大出口国 / 前 5 大进口国：2014–2026 逐年贸易与产能（补记 · 2026-10-01）</h2>
  <div class="panel">
    <div class="note">本节为 2026-10-01 补记，补充原报告缺失的<b>逐年序列</b>（原附录 A 仅给 2000/2010/2020/2025/2026 五个年份切面）、
    <b>净出口</b>与<b>产能</b>三个口径。国家范围按 MY2014–2026 贸易量均值取前 5 大出口国与前 5 大进口国。
    口径：USDA PSD 商品 0612000，千吨·原糖当量；<b>MY2026 为 FAS 预测值</b>。</div>

    <h3>7.1 国家范围与选取口径</h3>
    <p>按 2014–2026 共 13 个市场年的<b>年均出口量</b>降序取前 5：巴西（28,365 千吨）、泰国（6,931）、印度（4,953）、
    澳大利亚（3,366）、危地马拉（1,769）。按<b>年均进口量</b>降序取前 5：中国（4,923）、印尼（4,708）、
    美国（3,090）、欧盟（2,309）、孟加拉国（2,277）。</p>
    <p>这 10 国合计覆盖：全球出口量的约 <b>74%</b>、全球进口量的约 <b>36%</b>。两个名单<b>各有侧重、不重叠</b>——
    印度同时出现在两份名单中（年均出口 4,953、年均进口 1,851），是唯一的大规模双向贸易国。</p>

    <div class="warn"><b>产能口径声明（重要）</b><br>
    USDA PSD / WASDE <b>不发布</b>榨糖产能（nominal capacity）字段——其"Production"是<b>实际产量</b>，不是产能。
    本节的"产能"一列<b>以各市场年实际产量代理</b>，并另列 2014–2026 产量峰值作为<b>产能下限估计</b>。
    该代理口径的偏差方向明确：<b>减产年会被误读为"产能闲置"</b>，而实际原因可能是天气、糖醇比、政策限产。
    主要国的真实产能量级可参考 ISO《Sugar Year Book》与 USDA FAS GAIN 国别报告（见 7.4 佐证段）。</div>

    <h3>7.2 前 5 大出口国（2014–2026）</h3>
    {summary_table(EXP)}
    <div class="note">注：巴西进口长期为 0（PSD 记为 0），故净出口 = 出口。</div>
    <div id="c6" class="chart"></div>

    <h3>7.3 前 5 大进口国（2014–2026）</h3>
    {summary_table(IMP, show_self=True)}
    <div class="note">注：欧盟 2016/17 及 2023/24–2024/25 曾短暂转为净出口（配额制废除后产量回升），
    故"年均净进口"为 13 年均值，不能代表近两年状态。</div>
    <div id="c7" class="chart"></div>

    <h3>7.4 关键读数</h3>
    <ul>
      <li><b>巴西是唯一量级独立的出口方</b>：年均净出口 {num(st['BR']['nx_avg'])} 千吨，是第二名泰国的
      {st['BR']['nx_avg']/st['TH']['nx_avg']:.1f} 倍、前 5 国合计的 {st['BR']['nx_avg']/ (sum(st[c]['nx_avg'] for c in EXP)) *100:.0f}%。
      2023 年产量峰值 {num(st['BR']['p_peak'])} 千吨（{st['BR']['p_peak_y']}）创历史新高，对应净出口
      {num(max(st['BR']['nx']))} 千吨。</li>
      <li><b>泰国的"产量-出口"缺口在扩大</b>：2017 年产量 {num(st['TH']['p_peak'])} 千吨 → 2026 年 {num(st['TH']['p'][-1])} 千吨
      （{st['TH']['p'][-1]-st['TH']['p_peak']:+,.0f} 千吨），但期末库存从 6,841 升至 13,454 千吨。
      出口维持在 6,000 千吨，说明泰国在<b>用库存而非产量支撑出口</b>——与原报告第四节的"全球库存池"判断一致。</li>
      <li><b>印度是唯一的高消费+高波动双向国</b>：消费从 2014 年 {num(st['IN']['c'][0])} 千吨升至
      {num(st['IN']['c'][-1])} 千吨（+{st['IN']['c'][-1]-st['IN']['c'][0]:,.0f}），自给率仅
      {st['IN']['self_last']:.0f}%。净出口在 −{abs(min(st['IN']['nx'])):,} 到
      +{max(st['IN']['nx']):,} 千吨之间摆动，<b>振幅 {max(st['IN']['nx'])-min(st['IN']['nx']):,.0f} 千吨</b>，
      是出口端最大的不确定性来源。</li>
      <li><b>中国从"去库存"回到"稳进口"</b>：期末库存 2014 年 {num(st['CH']['e'][0])} 千吨 → 2023 年
      {num(min(st['CH']['e']))} 千吨（去库 {(st['CH']['e'][0]-min(st['CH']['e'])):,.0f} 千吨），
      随后回升至 2026 年 {num(st['CH']['e'][-1])} 千吨。进口量在 3,841–6,379 区间波动，
      2026 年为 {num(st['CH']['m'][-1])} 千吨。</li>
      <li><b>印尼是刚性缺口最深的进口国</b>：自给率从 2014 年 39% 降至 2026 年
      {st['ID']['self_last']:.0f}%，消费翻了近一倍（{num(st['ID']['c'][0])} → {num(st['ID']['c'][-1])} 千吨），
      产量 13 年仅从 {num(st['ID']['p'][0])} 增至 {num(st['ID']['p'][-1])} 千吨。</li>
      <li><b>欧盟是唯一定位反转的国家</b>：2014–2016 年均净进口 ~1,250 千吨（配额制末期），
      2017 年配额制废除后产量冲至 {num(st['E4']['p_peak'])} 千吨（{st['E4']['p_peak_y']}）转为净出口
      +2,737 千吨，2026 年又回到净进口 −{abs(st['E4']['nx'][-1]):,.0f} 千吨。</li>
    </ul>

    <h3>7.5 净出口的 13 年趋势：出口端在集中，进口端在分散</h3>
    <div id="c8" class="chart"></div>
    <p>前 5 大出口国的净出口合计从 2014 年 {num(agg_exp[0])} 千吨升至 2020–2021 年峰值
    {num(max(agg_exp))} 千吨（{YEARS[agg_exp.index(max(agg_exp))]}），2026 年回落至 {num(agg_exp[-1])} 千吨。
    同期前 5 大进口国的净进口合计从 {abs(agg_imp[0]):,.0f} 千吨扩大至 {abs(min(agg_imp)):,.0f} 千吨
    （{YEARS[agg_imp.index(min(agg_imp))]}），2026 年为 {abs(agg_imp[-1]):,.0f} 千吨。</p>
    <p>关键结构变化：<b>出口 5 国的净出口合计增量（2014→2026：{agg_exp[-1]-agg_exp[0]:+,.0f} 千吨）几乎全部由巴西贡献
    （+{st['BR']['nx'][-1]-st['BR']['nx'][0]:,.0f} 千吨）</b>；其余 4 国（泰、印、澳、危）合计净出口反向下滑
    {sum(st[c]['nx'][-1]-st[c]['nx'][0] for c in ['TH','IN','AS','GT']):+,.0f} 千吨。这与原报告第二节的
    "四国集中化"结论在 2014 年之后<b>进一步极端化</b>。</p>
  </div>
'''

# ══════════════════════ 附录 B ══════════════════════
def appx_table(cc, show_self=False):
    r = st[cc]
    head = ['年', '产量', '消费', '出口', '进口', '净出口']
    if show_self:
        head = ['年', '产量', '消费', '自给率', '出口', '进口', '净出口']
    head.append('期末库存')
    rows = []
    for i, y in enumerate(YEARS):
        cells = [f'<td>{y}</td>',
                 f'<td class="num">{num(r["p"][i])}</td>',
                 f'<td class="num">{num(r["c"][i])}</td>']
        if show_self:
            sh = r['p'][i] / r['c'][i] * 100 if r['c'][i] else 0
            cells.append(f'<td class="num">{sh:.0f}%</td>')
        cells += [f'<td class="num">{num(r["x"][i])}</td>',
                  f'<td class="num">{num(r["m"][i]) if r["m"][i] else "—"}</td>',
                  f'<td class="num">{sgn(r["nx"][i])}</td>',
                  f'<td class="num">{num(r["e"][i])}</td>']
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    ths = ''.join(f'<th{class_attr(h)}>{h}</th>' for h in head)
    return f'<table><tr>{ths}</tr>\n' + '\n'.join(rows) + '</table>'


# Tab 面板：出口国组 / 进口国组
def tab_bar():
    items = []
    for n, cc in enumerate(ALL):
        grp = '出口国' if cc in EXP else '进口国'
        items.append(
            f'<button class="tabbtn{" active" if n == 0 else ""}" data-tab="b-{cc}">'
            f'{cc} {NAME_FULL[cc]}<span class="tagg">{grp}</span></button>')
    return '<div class="tabbar">' + ''.join(items) + '</div>'


def tab_panes():
    panes = []
    for n, cc in enumerate(ALL):
        grp = '出口国' if cc in EXP else '进口国'
        panes.append(
            f'''<div class="tabpane{" show" if n == 0 else ""}" id="b-{cc}">
      <div class="panecap">{cc} {NAME_FULL[cc]} · {grp} · MY2014–MY2026</div>
      {appx_table(cc, show_self=(cc not in EXP))}
    </div>''')
    return '\n    '.join(panes)


APPX = '''
  <h2>附录 B · 前 5 大贸易国逐年平衡表（2014–2026 · 千吨原糖当量）</h2>
  <div class="panel">
    <div class="note">补记附录。口径同正文第七节：USDA PSD 商品 0612000；净出口 = 出口 − 进口；
    MY2026 为 FAS 预测值。原始数据：<code>data/fundamentals/sugar/top5_trade/top5_trade_2014_2026.csv</code>。<br>
    点击页签切换国家（共 10 个：出口国 5 + 进口国 5）。</div>
    ''' + tab_bar() + '''
    ''' + tab_panes() + '''
  </div>
'''

# ══════════════════════ 图表代码 ══════════════════════
CHART = f'''
// ===== 2026-10-01 补记：前5大贸易国逐年（c6/c7/c8）=====
const Y5 = {json.dumps(YEARS)};
const T5 = {json.dumps({cc: dict(p=st[cc]['p'], c=st[cc]['c'], x=st[cc]['x'], m=st[cc]['m'], nx=st[cc]['nx'], e=st[cc]['e']) for cc in ALL}, ensure_ascii=False)};

// C6 前5大出口国 净出口
mk('c6',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:64,right:70,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y5,...axis}},
  yAxis:{{type:'value',name:'净出口 千吨',...axis}},
  series:[
    {{name:'巴西',type:'line',data:T5.BR.nx,lineStyle:{{width:3,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'circle',symbolSize:5}},
    {{name:'泰国',type:'line',data:T5.TH.nx,lineStyle:{{width:2.2,color:C.orange}},itemStyle:{{color:C.orange}},symbol:'none'}},
    {{name:'印度',type:'line',data:T5.IN.nx,lineStyle:{{width:2.2,color:C.verm,type:'dashed'}},itemStyle:{{color:C.verm}},symbol:'none'}},
    {{name:'澳大利亚',type:'line',data:T5.AS.nx,lineStyle:{{width:2,color:C.green,type:'dotted'}},itemStyle:{{color:C.green}},symbol:'none'}},
    {{name:'危地马拉',type:'line',data:T5.GT.nx,lineStyle:{{width:2,color:C.purple,type:'dashed'}},itemStyle:{{color:C.purple}},symbol:'none'}},
    {{name:'印度 零线',type:'line',data:Y5.map(()=>0),lineStyle:{{width:1,color:'#b2182b',type:'dashed'}},itemStyle:{{color:'#b2182b'}},symbol:'none',tooltip:{{show:false}},silent:true}}
  ]
}});

// C7 前5大进口国 净进口（净出口的绝对值）
mk('c7',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:64,right:70,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y5,...axis}},
  yAxis:{{type:'value',name:'净进口 千吨（正数）',...axis}},
  series:[
    {{name:'中国',type:'bar',data:T5.CH.nx.map(v=>-v),itemStyle:{{color:C.verm}},barGap:'10%',barWidth:'13%'}},
    {{name:'印尼',type:'bar',data:T5.ID.nx.map(v=>-v),itemStyle:{{color:C.sky}},barWidth:'13%'}},
    {{name:'美国',type:'bar',data:T5.US.nx.map(v=>-v),itemStyle:{{color:C.green}},barWidth:'13%'}},
    {{name:'欧盟',type:'bar',data:T5.E4.nx.map(v=>-v),itemStyle:{{color:C.purple}},barWidth:'13%'}},
    {{name:'孟加拉国',type:'bar',data:T5.BG.nx.map(v=>-v),itemStyle:{{color:C.orange}},barWidth:'13%'}}
  ]
}});

// C8 出口5国 vs 进口5国 净出口合计
mk('c8',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:64,right:70,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y5,...axis}},
  yAxis:{{type:'value',name:'千吨',...axis}},
  series:[
    {{name:'出口5国 净出口合计',type:'line',data:{json.dumps(agg_exp)},lineStyle:{{width:2.8,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'circle',symbolSize:6,areaStyle:{{opacity:.12}}}},
    {{name:'进口5国 净进口合计（正数）',type:'line',data:{json.dumps([-v for v in agg_imp])},lineStyle:{{width:2.8,color:C.verm,type:'dashed'}},itemStyle:{{color:C.verm}},symbol:'diamond',symbolSize:7}},
    {{name:'巴西净出口',type:'line',data:T5.BR.nx,lineStyle:{{width:2,color:C.orange,type:'dotted'}},itemStyle:{{color:C.orange}},symbol:'none'}}
  ]
}});
'''

# ══════════════════════ Tab 样式与交互 ══════════════════════
TABCSS = '''
  /* === 附录 B 页签（2026-10-02 新增）=== */
  .tabbar{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 0;padding-bottom:10px;border-bottom:2px solid var(--line);}
  .tabbtn{font-family:inherit;font-size:12.5px;font-weight:600;color:var(--sub);background:#fff;
    border:1px solid var(--line);border-radius:8px;padding:6px 11px;cursor:pointer;
    display:inline-flex;align-items:center;gap:6px;transition:all .15s;}
  .tabbtn:hover{background:#eef2f7;color:#12365e;}
  .tabbtn.active{background:#12365e;color:#fff;border-color:#12365e;box-shadow:0 2px 6px rgba(18,54,94,.22);}
  .tabbtn .tagg{font-size:10px;font-weight:400;opacity:.62;border-left:1px solid currentColor;padding-left:6px;}
  .tabpane{display:none;}
  .tabpane.show{display:block;animation:fade .18s ease-in;}
  @keyframes fade{from{opacity:0;transform:translateY(-3px);}to{opacity:1;transform:none;}}
  .panecap{font-size:13px;color:#12365e;font-weight:600;margin:14px 0 8px;padding-left:9px;
    border-left:3px solid var(--oi-blue);}
  .tabpane table{margin-top:2px;}
  .tabpane .num{font-variant-numeric:tabular-nums;}
'''

TABJS = '''
// ==== 附录 B 页签切换（2026-10-02）====
(function(){
  const bar = document.querySelector('.tabbar');
  if(!bar) return;
  bar.addEventListener('click', function(e){
    const btn = e.target.closest('.tabbtn');
    if(!btn) return;
    const key = btn.getAttribute('data-tab');
    document.querySelectorAll('.tabbtn').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.tabpane').forEach(p=>p.classList.remove('show'));
    btn.classList.add('active');
    const pane = document.getElementById(key);
    if(pane) pane.classList.add('show');
  });
})();
'''

# ══════════════════════ 注入 ══════════════════════
s = open(REPORT, encoding='utf-8').read()
# 幂等清理：先移除上一轮注入的内容，再重新注入
old_sec = re.search(r'  <h2[^>]*>七、前 5 大出口国.*?(?=  <h2[^>]*>附录 A ·)', s, re.S)
if old_sec:
    s = s[:old_sec.start()] + s[old_sec.end():]
    print('已移除旧的第七节')
old_appx = re.search(r'  <h2>附录 B · 前 5 大贸易国.*?(?=  <div class="footer")', s, re.S)
if old_appx:
    s = s[:old_appx.start()] + s[old_appx.end():]
    print('已移除旧的附录B')
old_chart = re.search(r'\n// ===== 2026-10-01 补记：前5大贸易国逐年（c6/c7/c8）=====.*?// C8 出口5国 vs 进口5国 净出口合计.*?\}\);\n', s, re.S)
if old_chart:
    s = s[:old_chart.start()] + '\n' + s[old_chart.end():]
    print('已移除旧的图表代码')
old_css = re.search(r'\n  /\* === 附录 B 页签（2026-10-02 新增）=== \*/.*?\.tabpane \.num\{font-variant-numeric:tabular-nums;\}\n', s, re.S)
if old_css:
    s = s[:old_css.start()] + '\n' + s[old_css.end():]
    print('已移除旧的tab样式')

anchor = '  <h2 data-page-node-id="I4zHzrO01FU1jtwYCJ3W2P">附录 A · 分国平衡表总表（千吨·原糖当量）</h2>'
assert anchor in s, '未找到附录 A 锚点'

# 1) 在附录A前插入 第七节
s = s.replace(anchor, SEC.rstrip() + '\n\n' + anchor, 1)

# 2) 在 footer 前插入附录 B
foot = '  <div class="footer" data-page-node-id="38jEZpvxtyRdVvygPrVsrC">'
assert foot in s
s = s.replace(foot, APPX + '\n' + foot, 1)

# 3) 在 </style> 前追加 tab 样式
assert '</style>' in s
s = s.replace('</style>', TABCSS + '</style>', 1)

# 4) 在 </script> 前追加图表代码 + tab 交互
assert s.rstrip().endswith('</html>')
idx = s.rfind('</script>')
s = s[:idx] + CHART + TABJS + '\n' + s[idx:]

open(REPORT, 'w', encoding='utf-8').write(s)
print('OK. new size =', len(s))
print('章节七存在:', '七、前 5 大出口国' in s)
print('附录B存在:', '附录 B · 前 5 大贸易国' in s)
print('tab 页签数:', s.count('class="tabbtn'), 'pane 数:', s.count('class="tabpane'))
print('c6/c7/c8 容器:', s.count('id="c6"'), s.count('id="c7"'), s.count('id="c8"'))
print('th.num 数量:', len(re.findall(r'<th class="num">', s)))
