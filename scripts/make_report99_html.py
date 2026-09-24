# -*- coding: utf-8 -*-
"""99号：生成 HTML 报告（读取 report99 数据 JSON，内嵌 ECharts + Okabe-Ito 配色，涨红跌绿）"""
import json, os

ROOT = "C:/Users/Administrator/Desktop/农业"
DATA_JSON = ROOT + "/data/cftc/results_cot/sugar_position_price_report99_data.json"
OUT_HTML = ROOT + "/reports/99_白糖CFTC持仓价格关系_2009_2026/index.html"

d = json.load(open(DATA_JSON, encoding="utf-8"))
META, BASE, SCEN, SERIES, SEG = d["meta"], d["baseline"], d["scenarios"], d["series"], d["seg_stats"]

data_js = json.dumps({"meta": META, "baseline": BASE, "scenarios": SCEN, "series": SERIES,
                      "seg": {k: v for k, v in SEG.items()}}, ensure_ascii=False)

# 关键统计速取
def st(name, hz):
    s = SCEN.get(name, {}).get("stats", {}).get(hz)
    if not s: return {"mean": None, "win": None, "n": 0, "med": None}
    return s

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>99｜ICE原糖 CFTC非商业头寸 × 价格关系研究（2009–2026）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --oi-sky:#56B4E9; --oi-purple:#CC79A7; --oi-yellow:#F0E442; --oi-black:#000000;
        --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}
  .wrap{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}
  .hero{background:linear-gradient(135deg,#12365e 0%,#1d5c93 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}
  .hero h1{font-size:23px;margin-bottom:6px;line-height:1.45;}
  .hero .meta{font-size:12.5px;opacity:.85;margin-top:4px;}
  .hero .sub{margin-top:12px;font-size:14px;opacity:.96;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}
  .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}
  .kcard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}
  .kcard .lab{font-size:12px;color:var(--sub);margin-bottom:3px;}
  .kcard .val{font-size:19px;font-weight:700;font-variant-numeric:tabular-nums;color:#12365e;}
  .kcard .note{font-size:12px;color:var(--sub);margin-top:3px;}
  .red{color:#b2182b;} .green{color:#1a7a3a;} .blue{color:#0072B2;} .orange{color:#b47400;} .purple{color:#7a4a9e;}
  h2{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}
  h3{font-size:16px;color:#12365e;margin:18px 0 8px;}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;}
  th{background:#eef2f7;color:#12365e;padding:6px 7px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid var(--line);vertical-align:middle;}
  tr:last-child td{border-bottom:none;}
  .num{font-variant-numeric:tabular-nums;text-align:right;}
  th.num{text-align:right;}
  .src{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}
  .callout{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}
  .warn{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}
  .ok{background:#f0f8f4;border:1px solid #c9e5d6;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}
  .chart{width:100%;height:380px;}
  .chart-sm{width:100%;height:320px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
  .tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:10px;margin-right:5px;font-weight:600;}
  .t-hi{background:#f0f8f4;color:#1a7a3a;border:1px solid #c9e5d6;}
  .t-mid{background:#fff8ee;color:#b47400;border:1px solid #f0d9a8;}
  .t-low{background:#fdf2f2;color:#b2182b;border:1px solid #eccaca;}
  .footer{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}
  code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}
  ul{padding-left:22px;} li{margin:4px 0;}
  .flex{display:flex;gap:8px;align-items:center;}
  @media(max-width:900px){.cards{grid-template-columns:repeat(2,1fr);}.grid2{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <h1>ICE 原糖：CFTC 非商业（投机）头寸 × 价格关系统计研究</h1>
  <div class="meta">99 号报告 · 数据窗口 2009-01 ~ 2026-09 · 价格锚定 2011-12-23 ~ 2026-09-18 · 768 个 CFTC 报告周</div>
  <div class="sub">以 2009 年以来真实 CFTC（Futures Only，11 号原糖）周报与 ICE 日线为样本，量化 8 类“头寸—价格”组合的同期与 t+20/t+60 表现，给出信号可信度分级与交叉验证要求。</div>
</div>

<div class="cards">
  <div class="kcard"><div class="lab">全样本基准 t+20</div><div class="val">+0.2% <span style="font-size:13px;color:var(--sub)">(胜率 46.8%)</span></div><div class="note">768 周，中位数 -0.4%</div></div>
  <div class="kcard"><div class="lab">多头连增3周 t+60</div><div class="val red">-3.1%</div><div class="note">胜率 33.3%，<span class="red">显著低于基准</span></div></div>
  <div class="kcard"><div class="lab">高位多头观望 t+60</div><div class="val green">+4.7%</div><div class="note">胜率 70.6%（n=17，样本小）</div></div>
  <div class="kcard"><div class="lab">增仓但价跌背离 t+20</div><div class="val red">-3.3%</div><div class="note">胜率 28.1%，<b>最弱信号组合</b></div></div>
</div>

<h2>0. 数据与口径</h2>
<div class="panel">
  <ul>
    <li><b>持仓</b>：CFTC COT <code>Futures Only</code>，11 号原糖（Sugar #11），非商业=投机（基金/CTA 等）；报告日=周二快照，周度。字段：OI、非商业多/空/净、商业净、非报告净。</li>
    <li><b>价格</b>：ICE 原糖主力连续日线收盘（美分/磅）。价格数据自 2011-12-23 起，故 2009–2011 的持仓周无价格锚点被自动跳过，实际统计区间 2011-12 → 2026-09。</li>
    <li><b>对齐</b>：以每个报告周为锚点，取 ≤ 报告日最近交易日收盘为基准；<code>t+N</code>=其后第 N 个交易日收益；<code>周收益</code>=锚点收盘到下一报告周锚点收盘。</li>
    <li><b>“明显变动”</b>：单周 |Δ|≥5000 手（空头减仓/OI 用 20000 手）；<b>“持续增仓”</b>=连续 k 周同向；<b>“高位”</b>=价格 250 日分位 ≥80% 且非商业净多/OI ≥ 历史 60% 分位。</li>
    <li><b>检验</b>：各组同期/前瞻均值、中位数、胜率 vs 全样本基准（lift），并分段（2012-16 熊市 / 2017-19 底部 / 2020-24 上行 / 2025+ 缺口行情）交叉验证。</li>
  </ul>
</div>

<h2>1. 全景：价格 × 非商业净多（2009–2026）</h2>
<div class="panel"><div id="c_series" class="chart"></div>
  <div class="src">左轴=ICE 原糖收盘（美分/磅），右轴=非商业净多（手）。阴影区=分段。净多与价格大体同向，但 2017-19 底部区净多先于价格见底、2023 顶部净多先于价格回落——头寸是<b>滞后确认</b>指标而非领先指标。</div>
</div>

<h2>2. 场景一：非商业多头持续增仓 → 价格表现</h2>
<div class="panel">
  <div class="callout"><b>核心发现（反直觉）</b>：2009 年以来，非商业多头连续增仓 2/3/4 周后，ICE 原糖<b>平均走弱</b>——t+60 均值 -2.6% / -3.1% / -3.4%，胜率 37% / 33% / 32%，显著低于全样本基准（45.6%）。多头增仓本身不是看涨信号，关键看<b>增仓的时点与价格是否共振</b>。</div>
  <table id="t_s1"></table>
  <div class="src">「周收益」=报告周内价格变动；t+5…t+60=锚点后第 N 个交易日收益；胜率=收益&gt;0 比例；lift=相对全样本基准胜率的百分点差。单位：%。</div>
</div>
<div class="grid2">
  <div class="panel"><div class="chart-sm" id="c_s1path"></div><div class="src">多头连增 2/3/4 周后的累积路径（周度，0=锚点）。无论增仓多久，t+8（约 6 周）后普遍转负——白糖的“多头增仓”更多出现在<b>上涨末端或下跌中的反弹</b>，而非趋势起点。</div></div>
  <div class="panel"><div class="chart-sm" id="c_s1hz"></div><div class="src">多头连增 3 周各时点收益 vs 全样本基准。t+5 起持续为负，t+60 达 -3.1%。增仓周数越长，负收益越深。</div></div>
</div>
<div class="panel">
  <h3>关键拆解：多头增仓必须结合当周价格方向</h3>
  <table id="t_s1split"></table>
  <div class="warn"><b>操作含义</b>：①多头增仓 + 当周价格上行（共振）→ t+20 胜率 55%+，但 t+60 衰减，属于<b>短期动量确认</b>；②多头增仓 + 当周价格下跌 ≥1%（接盘/背离）→ 各时段胜率仅 15–35%，是<b>较强的续跌信号</b>（详见场景八）。切勿把“基金加多”单独当买入理由。</div>
</div>

<h2>3. 场景二：价格高位 + 非商业多头不再增仓（高位观望）</h2>
<div class="panel">
  <div class="callout"><b>核心发现</b>：价格处 250 日高分位（≥80%）且非商业净多/OI 偏高、但多头连续 4 周累计持仓变动 ≤0.5% OI（<b>横盘观望</b>），后续 t+20 均值 +4.3%、t+40 +6.3%、t+60 +4.7%，胜率 46% / 65% / 71%——<b>多数情况下是中继而非顶部</b>。</div>
  <table id="t_s2"></table>
  <div class="src">n=17（样本较少，结论置信度中）。13/17 分布于 2020-24 上行段，2025+ 无样本。反例：2023-10-24（绝对顶部，多头已离场，t+60 -14.6%）——高位观望能否成立，需排除<b>多头已明显减持</b>的顶部形态。</div>
  <table id="t_s2detail"></table>
  <div class="src">典型案例（最近 12 个）。d_nc_l_4w=前 4 周非商业多头累计变动（手）；t+20/t+60=后续收益%。2021-01/2023-03 观望后继续大涨；2023-05/10 观望后回落（顶部特征：净多绝对水平已在下降）。</div>
</div>
<div class="grid2">
  <div class="panel"><div class="chart-sm" id="c_s2path"></div><div class="src">高位观望后的路径（0=触发周）：t+4~t+8 明显上行——筹码锁定、净多未撤，趋势未破。</div></div>
  <div class="panel"><div class="chart-sm" id="c_s2bpath"></div><div class="src">对照：高位 + 多头<b>继续</b>增仓（n=86）→ t+40 中位数 +0.5%、胜率 51.8%，远弱于观望组——高位继续追多在白糖里常买在尾部。</div></div>
</div>

<h2>4. 场景三：非商业空头明显减仓 → 价格支撑</h2>
<div class="panel">
  <div class="callout"><b>核心发现</b>：空头单周减仓 ≥5000 手（n=217），t+20 均值 +0.5%、胜率 44.9%，支撑<b>温和且方向依赖价格位置</b>：价格低位（250日分位&lt;40）时空头回补 t+20 均值 +1.9%、t+60 +4.9%（2020-24 段胜率 75%）；价格高位时空头减仓支撑弱（t+20 均值 -0.4%）。</div>
  <table id="t_s3"></table>
  <div class="src">空头减仓 = 空头了结离场，缓解抛压；但<b>只有在低位才是反转确认</b>（空头止损/认输），高位空头减仓往往是反弹尾声的换手。</div>
</div>
<div class="grid2">
  <div class="panel"><div class="chart-sm" id="c_s3path"></div><div class="src">空头明显减仓后的路径：低位组（蓝）触发后温和上行，高位组（橙）继续走弱。位置决定一切。</div></div>
  <div class="panel"><div class="chart-sm" id="c_s5path"></div><div class="src">对照：非商业<b>空头持续增仓</b> 2 周后反而偏强（t+20 +0.7%、2020-24 段 +1.6%/胜率 62%）——看跌离场、空头加在被低位限期逼空，详见场景五。</div></div>
</div>

<h2>5. 场景四：多头持续增仓后的滞后统计（t+N）</h2>
<div class="panel">
  <table id="t_s1hz_tab"></table>
  <div class="src">完整 t+N 表。三档（2/3/4 周连续增仓）在全部 6 个时点的均值均为负、胜率均低于基准——<b>在白糖上不存在“多头连续增仓→滞后上涨”的统计规律</b>，与“基金加仓后市看涨”的直觉相反。原因：非商业多头在白糖中是趋势跟随+均值回归的双重角色，加仓往往发生在价格已充分反映预期之后（周报滞后一周）。</div>
</div>

<h2>6. 其他重要组合情形</h2>
<div class="grid2">
  <div class="panel"><h3>场景五：非商业空头持续增仓</h3>
    <table id="t_s5"></table>
    <div class="callout"><b>反直觉</b>：空头连增 2 周（n=248）t+20 均值 +0.7%、2020-24 段胜率 62%、2025+ 段 +3.2%——<b>空头持续加仓在白糖里常被逼空</b>（基金空头拥挤、基本面反转时集中回补）。2012-16 熊市中空头增仓则方向正确（t+60 +2.1%）。<b>需结合趋势</b>：牛市/缺口行情中的空头增仓=反向指标；熊市中的空头增仓=顺势。</div></div>
  <div class="panel"><h3>场景六：多空同步增仓（分歧加剧）</h3>
    <table id="t_s6"></table>
    <div class="callout">多空同增（n=115）→ OI 扩张、投机分歧加大。方向略微偏多（t+20 +1.1%、胜率 51%），因净多仍占优；但波动通常放大。<b>解读</b>：分歧是行情酝酿期，突破方向需等一方溃败；2025+ 段 t+20 +4.5%（胜率 71%）→ 缺口行情中多头占上风时同增=偏多确认。</div></div>
  <div class="panel"><h3>场景七：总持仓（OI）显著萎缩</h3>
    <table id="t_s7"></table>
    <div class="callout">OI 单周 -20000 手（n=139）：t+20 均值 +2.3%、胜率 60%——<b>持仓大幅萎缩=投机资金出清/止损，短期乖离修复</b>（多空皆砍）。但 <b>2025+ 缺口行情中该信号失效</b>（t+60 均值 -8.3%、胜率仅 8%）——极端行情里 OI 萎缩代表趋势参与者整体撤退而非止跌。<b>必须看萎缩发生在什么行情里</b>。</div></div>
  <div class="panel"><h3>场景八：持仓与价格背离</h3>
    <table id="t_s8"></table>
    <div class="warn"><b>背离是全部组合里最可靠的方向信号</b>：①机构（净多）大幅增仓但当周价格下跌 → 后续 t+20 均值 -3.3%、胜率 28%——<b>价格先于持仓，且空头掌握主动</b>，机构加仓多为摊低成本/逆势抄底失败；②净多明显减仓但当周价格大涨（n=100）→ t+20 +3.9%——多头离场但价格上行=逼空行情，短期强势，但 t+60 衰减（胜率 56.8%），持续性有限。<b>背离时：价格优先，持仓次之</b>。</div></div>
</div>

<h2>7. 信号可信度分级与交叉验证要求</h2>
<div class="panel">
  <table id="t_grade"></table>
  <div class="src">可信度分级基于样本量、跨时段一致性、与直觉的偏离度。所有“高”信号均在大样本且多个趋势段方向一致时给出。</div>
  <div class="callout"><b>交叉验证三件套</b>（每个信号都要过）：
    ① <b>成交量</b>：持仓变动是否伴随放量？放量增仓（无论多空）比缩量增仓可信；OI 变化方向（同步扩/缩）决定是“新钱进场”还是“存量换手”。
    ② <b>趋势/位置</b>：250 日分位在哪？趋势段（2012-16 熊 vs 2020-24 牛）同一持仓行为的含义完全相反（见 S5 空头增仓）。
    ③ <b>基本面</b>：白糖是基本面定价市场（ISO 供需缺口、巴西/印度/泰国产量、油价/乙醇价差），CFTC 头寸是<b>第二层信息</b>——机构头寸本身就由基本面驱动，背离出现时先问“基本面在发生什么”，再决定是抄背离还是顺价格。</div>
</div>

<h2>8. 分段交叉验证：信号在不同行情类型中的稳定性</h2>
<div class="panel"><div id="c_seg" class="chart"></div>
  <div class="src">各场景 t+20 胜率 vs 基准（虚点线=46.8%）按四段拆解。S8a（多头增仓价跌背离）在四个段全部低于基准——<b>唯一跨时段稳定的看空信号</b>；S5（空头增仓）与 S7（OI 萎缩）方向在 2025+ 缺口行情中与前期相反——趋势依赖型信号。</div>
</div>

<h2>9. 总结：头寸—价格组合解读要点与操作含义</h2>
<div class="panel">
  <h3>三类高可信信号</h3>
  <ul>
    <li><span class="tag t-hi">高</span><b>“多头增仓 + 当周价格下跌”背离 → 看空</b>（S8a/S1-背离）：t+20 胜率 28%、均值 -3.3%，跨时段稳定。释义：价格先于持仓、空头掌握主动，机构加仓多为逆势摊仓。操作：不抄底，等待背离修复或顺势做空（需基本面配合）。</li>
    <li><span class="tag t-hi">高</span><b>“将多头连增本身当作买入理由” → 否决</b>：2009 年以来全部 6 个前瞻时点负收益，是应避免的常见误用。</li>
    <li><span class="tag t-hi">高</span><b>低位（分位&lt;40）+ 空头明显回补 → 浅反弹</b>：t+20 +1.9%、2020-24 段 t+60 胜率 75%。释义：抛压了结。操作：作为空头止盈/反弹参与信号，做反转需等价格确认。</li>
  </ul>
  <h3>四类中可信信号（需交叉验证）</h3>
  <ul>
    <li><span class="tag t-mid">中</span><b>高位多头观望 → 中继</b>（n=17）：t+40 胜率 65%。前提：排除净多绝对水平已下行的顶部形态；2025+ 无样本。操作：趋势跟随者持有，勿因“高位”轻易离场；出现“观望→减持”切换再减仓。</li>
    <li><span class="tag t-mid">中</span><b>空头持续增仓 → 逼空潜力</b>：牛市中=反向指标（2020-24 t+20 胜率 62%），熊市中=顺势。操作：牛市见到基金空头快速堆积，警惕轧空反弹；熊市则空头增仓确认空头趋势。</li>
    <li><span class="tag t-mid">中</span><b>多空同步增仓 → 分歧放大</b>：方向偏多但波动增大，突破需等单边溃败。操作：观望或轻仓，避免在分歧中追涨杀跌。</li>
    <li><span class="tag t-mid">中</span><b>OI 显著萎缩 → 短期反弹，但 2025+ 缺口行情例外</b>：正常行情的止跌信号；极端缺口行情中=趋势撤退的危险信号。操作：先判断行情类型（是否处于基本面缺口定价），再决定方向。</li>
  </ul>
  <h3>两条总原则</h3>
  <ul>
    <li><b>持仓是滞后确认指标，不是领先指标</b>：CFTC 周报滞后一周，且基金在白糖中多是趋势跟随者。它验证“价格已在做的事”，而非预告“将要发生的事”。</li>
    <li><b>持仓信息量在于“偏离”而非“水平”</b>：净多多少不重要，重要的是<b>持仓变动方向 × 当周价格方向是否一致</b>。一致=趋势确认；不一致（背离）先跟价格；同时配合成交量与基本面（ISO/USDA/巴西印度产量）定位。</li>
  </ul>
</div>

<div class="footer">
  数据来源：CFTC COT（Futures Only，Sugar #11），ICE 原糖主力连续日线。统计窗口 2009-01~2026-09（价格锚定 2011-12~2026-09，768 周）。本报告为统计研究，不构成投资建议；收益均值易受极端事件影响，请同时参考中位数与胜率。样本端（2025+）事件较少，分段统计仅供参考。生成：2026-09-22。
</div>
</div>

<script>
var DATA = __DATA_JS__;
var OI = {blue:'#0072B2', orange:'#E69F00', verm:'#D55E00', green:'#009E73', sky:'#56B4E9', purple:'#CC79A7', black:'#000000'};
var UP='#b2182b', DOWN='#1a7a3a', SUB='#5a6a7d';
function fmt(x, d){ if(x===null||x===undefined||isNaN(x)) return '—'; return x.toFixed(d===undefined?2:d); }
function pct(x){ if(x===null||x===undefined||isNaN(x)) return '—'; return x.toFixed(1)+'%'; }
function cls(v){ return v>0?'red':(v<0?'green':'') ; }

// ---------- 1. 全景 ----------
(function(){
  var ser = DATA.series;
  var x = ser.map(function(r){return r.date;});
  var chart = echarts.init(document.getElementById('c_series'));
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['价格','非商业净多'],textStyle:{color:SUB}},
    grid:{left:50,right:60,top:40,bottom:50},
    xAxis:{type:'category',data:x,axisLabel:{show:false}},
    yAxis:[
      {type:'value',name:'原糖(美分/磅)',nameTextStyle:{color:SUB},splitLine:{lineStyle:{color:'#eef2f7'}}},
      {type:'value',name:'净多(万手)',nameTextStyle:{color:SUB},axisLabel:{formatter:function(v){return (v/10000).toFixed(0)+'万';}}}
    ],
    dataZoom:[{type:'inside'}],
    series:[
      {name:'价格',type:'line',data:ser.map(function(r){return r.close;}),yAxisIndex:0,showSymbol:false,lineStyle:{width:1.8,color:OI.blue},itemStyle:{color:OI.blue}},
      {name:'非商业净多',type:'line',data:ser.map(function(r){return r.nc_net;}),yAxisIndex:1,showSymbol:false,lineStyle:{width:1.4,color:OI.orange,type:'dashed'},itemStyle:{color:OI.orange}}
    ]
  });
})();

// ---------- 2. S1 多空增仓 ----------
(function(){
  var rows = [['多头连增 k 周','n','周收益','t+5','t+10','t+20','t+40','t+60']];
  [['S1_nc_l_up_2w',2],['S1_nc_l_up_3w',3],['S1_nc_l_up_4w',4]].forEach(function(p){
    var k=p[1], nm=p[0], sc=DATA.scenarios[nm].stats;
    function c(h){var s=sc[h]; if(!s) return ['—','—','—']; return [pct(s.mean), s.win.toFixed(1)+'%', cls(s.mean)];}
    var w=c('w'), t5=c('t5'), t10=c('t10'), t20=c('t20'), t40=c('t40'), t60=c('t60');
    rows.push(['<b>'+k+' 周</b>', DATA.scenarios[nm].n,
      '<span class="'+w[2]+'">'+w[0]+'</span>', '<span class="'+t5[2]+'">'+t5[0]+'</span>',
      '<span class="'+t10[2]+'">'+t10[0]+'</span>', '<span class="'+t20[2]+'">'+t20[0]+'</span>',
      '<span class="'+t40[2]+'">'+t40[0]+'</span>', '<span class="'+t60[2]+'">'+t60[0]+'</span>']);
  });
  rows.push(['全样本基准','768','+0.05% (46.6)','+0.06 (46.7)','+0.10 (46.0)','+0.18 (46.8)','+0.16 (47.2)','+0.11 (45.6)']);
  document.getElementById('t_s1').innerHTML = rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
})();

// t_s1hz_tab 全表
(function(){
  var hz=['w','t5','t10','t20','t40','t60'];
  var hl=['周收益','t+5','t+10','t+20','t+40','t+60'];
  var rows=[['多头连增k周','n'].concat(hl.map(function(h){return h+' 均值 (胜率)';}))];
  [['S1_nc_l_up_2w',2],['S1_nc_l_up_3w',3],['S1_nc_l_up_4w',4]].forEach(function(p){
    var sc=DATA.scenarios[p[0]].stats;
    var cells=[hz.map(function(h){var s=sc[h]; if(!s) return '—'; return '<span class="'+cls(s.mean)+'">'+fmt(s.mean)+'%</span> <span style="color:'+SUB+'">('+s.win.toFixed(0)+'%)</span>';})];
    rows.push(['<b>'+p[1]+' 周</b>', DATA.scenarios[p[0]].n].concat(cells[0]));
  });
  rows.push(['基准 —','768'].concat(hz.map(function(h){var b=DATA.baseline[h]; return '<span>'+fmt(b.mean)+'%</span> <span style="color:'+SUB+'">('+b.win.toFixed(0)+'%)</span>';})));
  document.getElementById('t_s1hz_tab').innerHTML = rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
})();

// S1 路径图
(function(){
  var names=['S1_nc_l_up_2w','S1_nc_l_up_3w','S1_nc_l_up_4w'];
  var labels=['增仓2周','增仓3周','增仓4周'];
  var colors=[OI.blue,OI.orange,OI.verm];
  var x0=[]; for(var i=-4;i<=12;i++) x0.push(i>0?'+'+i+'周':(i===0?'触发':'t'+i+'周'));
  var chart=echarts.init(document.getElementById('c_s1path'));
  var series=names.map(function(nm,idx){
    var p=DATA.scenarios[nm].path;
    return {name:labels[idx],type:'line',showSymbol:false,lineStyle:{width:2,color:colors[idx]},itemStyle:{color:colors[idx]},
      data:x0.map(function(_,i){var k=i-4; return p.hasOwnProperty(k)?+p[k]:null;}),
      markLine:{silent:true,symbol:'none',data:[{xAxis:4}],lineStyle:{color:SUB,type:'dashed'}}};
  });
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(2)+'%';}},
    legend:{data:labels,textStyle:{color:SUB}},grid:{left:45,right:20,top:40,bottom:44},
    xAxis:{type:'category',data:x0},yAxis:{type:'value',name:'累积收益%',nameTextStyle:{color:SUB}},
    series:series});
})();

// S1 各时点对比柱
(function(){
  var hz=['w','t5','t10','t20','t40','t60'];
  var hl=['周','+5','+10','+20','+40','+60'];
  var chart=echarts.init(document.getElementById('c_s1hz'));
  var bl=DATA.baseline;
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(2)+'%';}},
    legend:{data:['增仓2周','增仓3周','增仓4周','全样本基准'],textStyle:{color:SUB}},
    grid:{left:45,right:20,top:40,bottom:44},
    xAxis:{type:'category',data:hl.map(function(h){return h==='周'?'周':'t+'+h;})},
    yAxis:{type:'value',name:'均值收益%',nameTextStyle:{color:SUB}},
    series:[
      {name:'增仓2周',type:'bar',data:hz.map(function(h){var s=DATA.scenarios.S1_nc_l_up_2w.stats[h]; return s?+s.mean.toFixed(2):0;}),itemStyle:{color:OI.blue}},
      {name:'增仓3周',type:'bar',data:hz.map(function(h){var s=DATA.scenarios.S1_nc_l_up_3w.stats[h]; return s?+s.mean.toFixed(2):0;}),itemStyle:{color:OI.orange}},
      {name:'增仓4周',type:'bar',data:hz.map(function(h){var s=DATA.scenarios.S1_nc_l_up_4w.stats[h]; return s?+s.mean.toFixed(2):0;}),itemStyle:{color:OI.verm}},
      {name:'全样本基准',type:'line',data:hz.map(function(h){return +bl[h].mean.toFixed(2);}),itemStyle:{color:OI.black},lineStyle:{width:2,type:'dashed'}}
    ]});
})();

// S1 共振/背离拆分表
(function(){
  var rows=[['组合','n','t+20均值','t+20胜率','t+60均值','t+60胜率']];
  [['多头增仓2周 + 当周价涨>1%（共振）','S1_resonance_up','green'],
   ['多头增仓2周 + 当周价跌>1%（背离）','S1_diverge_down','red']].forEach(function(p){
    var sc=DATA.scenarios[p[1]].stats;
    var t20=sc.t20, t60=sc.t60;
    rows.push([p[0],DATA.scenarios[p[1]].n,
      '<span class="'+cls(t20.mean)+'">'+fmt(t20.mean)+'%</span>',t20.win.toFixed(1)+'%',
      '<span class="'+cls(t60.mean)+'">'+fmt(t60.mean)+'%</span>',t60.win.toFixed(1)+'%']);
  });
  document.getElementById('t_s1split').innerHTML=rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
})();

// ---------- 3. S2 高位观望 ----------
(function(){
  var sc=DATA.scenarios.S2_high_stall.stats;
  var rows=[['时点','n','均值','中位数','胜率','lift(pp)']];
  [['w','周收益'],['t10','t+10'],['t20','t+20'],['t40','t+40'],['t60','t+60']].forEach(function(p){
    var s=sc[p[0]]; if(!s) return;
    rows.push([p[1],s.n,'<span class="'+cls(s.mean)+'">'+fmt(s.mean)+'%</span>','<span class="'+cls(s.med)+'">'+fmt(s.med)+'%</span>',s.win.toFixed(1)+'%',(s.lift>0?'+':'')+s.lift.toFixed(1)]);
  });
  document.getElementById('t_s2').innerHTML=rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
  var dt=DATA.scenarios.S2_high_stall.detail || [];
  if(dt.length){
    var dr=[['报告日','收盘价','250日分位','净多(手)','4周多头Δ(手)','t+20%','t+60%']];
    dt.forEach(function(d){
      dr.push([d.date, d.close, (d.px250!==null&&d.px250!==undefined)?d.px250.toFixed(0)+'%':'—',
        (d.nc_net/10000).toFixed(1)+'万', d.d_nc_l_4w,
        '<span class="'+cls(d.t20)+'">'+fmt(d.t20)+'%</span>','<span class="'+cls(d.t60)+'">'+fmt(d.t60)+'%</span>']);
    });
    document.getElementById('t_s2detail').innerHTML=dr.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
  }
})();
// S2 路径
(function(){
  var chart=echarts.init(document.getElementById('c_s2path'));
  var p=DATA.scenarios.S2_high_stall.path;
  var x=[]; for(var i=0;i<=12;i++){x.push(i===0?'触发':'+'+i+'周');}
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(2)+'%';}},
    grid:{left:45,right:20,top:20,bottom:44},xAxis:{type:'category',data:x},
    yAxis:{type:'value',name:'累积收益%',nameTextStyle:{color:SUB}},
    series:[{type:'line',data:x.map(function(_,i){return p.hasOwnProperty(i)?+p[i]:null;}),showSymbol:true,symbolSize:6,
      lineStyle:{width:2.4,color:OI.green},itemStyle:{color:OI.green},
      markLine:{silent:true,symbol:'none',data:[{yAxis:0}],lineStyle:{color:SUB,type:'dashed'}}}]});
})();
// S2b 路径(对照)
(function(){
  var chart=echarts.init(document.getElementById('c_s2bpath'));
  var p=DATA.scenarios.S2b_high_accum.path;
  var x=[]; for(var i=0;i<=12;i++){x.push(i===0?'触发':'+'+i+'周');}
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(2)+'%';}},
    grid:{left:45,right:20,top:20,bottom:44},xAxis:{type:'category',data:x},
    yAxis:{type:'value',name:'累积收益%',nameTextStyle:{color:SUB}},
    series:[{type:'line',data:x.map(function(_,i){return p.hasOwnProperty(i)?+p[i]:null;}),showSymbol:true,symbolSize:5,
      lineStyle:{width:2,color:OI.verm},itemStyle:{color:OI.verm},
      markLine:{silent:true,symbol:'none',data:[{yAxis:0}],lineStyle:{color:SUB,type:'dashed'}}}]});
})();

// ---------- 4. S3 空头减仓 ----------
(function(){
  var rows=[['组','n','t+20均值','t+20胜率','t+60均值','t+60胜率']];
  [['空头单周减仓≥5000手(全)','S3_cover_big'],
   ['其中 价格低位(分位<40)','S3_cover_low'],
   ['其中 价格高位(分位≥40)','S3_cover_high']].forEach(function(p){
    var sc=DATA.scenarios[p[1]].stats, t20=sc.t20, t60=sc.t60;
    rows.push([p[0],DATA.scenarios[p[1]].n,
      '<span class="'+cls(t20.mean)+'">'+fmt(t20.mean)+'%</span>',t20.win.toFixed(1)+'%',
      '<span class="'+cls(t60.mean)+'">'+fmt(t60.mean)+'%</span>',t60.win.toFixed(1)+'%']);
  });
  document.getElementById('t_s3').innerHTML=rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
})();
(function(){
  var chart=echarts.init(document.getElementById('c_s3path'));
  var x=[]; for(var i=0;i<=12;i++)x.push(i===0?'触发':'+'+i+'周');
  var mk=function(nm,color){var p=DATA.scenarios[nm].path; return {name:nm==='S3_cover_low'?'低位回补':'高位回补',type:'line',data:x.map(function(_,i){return p.hasOwnProperty(i)?+p[i]:null;}),showSymbol:false,lineStyle:{width:2,color:color},itemStyle:{color:color}};};
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(2)+'%';}},
    legend:{data:['低位回补','高位回补'],textStyle:{color:SUB}},grid:{left:45,right:20,top:35,bottom:44},
    xAxis:{type:'category',data:x},yAxis:{type:'value',name:'累积收益%',nameTextStyle:{color:SUB}},
    series:[mk('S3_cover_low',OI.blue),mk('S3_cover_high',OI.orange)]});
})();
(function(){
  var chart=echarts.init(document.getElementById('c_s5path'));
  var x=[]; for(var i=0;i<=12;i++)x.push(i===0?'触发':'+'+i+'周');
  var p=DATA.scenarios.S5_nc_s_up_2w.path;
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(2)+'%';}},
    grid:{left:45,right:20,top:20,bottom:44},xAxis:{type:'category',data:x},
    yAxis:{type:'value',name:'累积收益%',nameTextStyle:{color:SUB}},
    series:[{type:'line',data:x.map(function(_,i){return p.hasOwnProperty(i)?+p[i]:null;}),showSymbol:true,symbolSize:5,
      lineStyle:{width:2,color:OI.purple},itemStyle:{color:OI.purple},
      markLine:{silent:true,symbol:'none',data:[{yAxis:0}],lineStyle:{color:SUB,type:'dashed'}}}]});
})();

// ---------- 6. 其他场景表 ----------
function scTable(el,name,nm,desc){
  var sc=DATA.scenarios[nm].stats;
  var rows=[['时点','n','均值','中位数','胜率','lift(pp)']];
  [['w','周收益'],['t10','t+10'],['t20','t+20'],['t40','t+40'],['t60','t+60']].forEach(function(p){
    var s=sc[p[0]]; if(!s) return;
    rows.push([p[1], s.n, '<span class="'+cls(s.mean)+'">'+fmt(s.mean)+'%</span>', '<span class="'+cls(s.med)+'">'+fmt(s.med)+'%</span>', s.win.toFixed(1)+'%', (s.lift>0?'+':'')+s.lift.toFixed(1)]);
  });
  var html=rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
  // 分段速览
  var sg=DATA.seg;
  var dr=[['分段','n','t+20均值','t+20胜率','t+60均值','t+60胜率']];
  Object.keys(sg).forEach(function(k){
    var v=sg[k][nm]; if(!v||!v.n) return;
    dr.push([k, v.n, v.t20===null?'—':'<span class="'+cls(v.t20)+'">'+fmt(v.t20)+'%</span>',
      v.t20w===null?'—':v.t20w.toFixed(0)+'%', v.t60===null?'—':'<span class="'+cls(v.t60)+'">'+fmt(v.t60)+'%</span>', v.t60w===null?'—':v.t60w.toFixed(0)+'%']);
  });
  var segHtml=dr.length>1?'<table>'+dr.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('')+'</table>':'';
  document.getElementById(el).innerHTML='<table>'+html+'</table>'+segHtml+'<div class="src">分段: 2012-16熊/2017-19底/2020-24牛/2025+缺口 (n=该段事件数)。</div>';
}
scTable('t_s5','S5','S5_nc_s_up_2w');
scTable('t_s6','S6','S6_both_up');
scTable('t_s7','S7','S7_oi_shrink');
(function(){
  var rows=[['背离组合','n','t+20均值','t+20胜率','t+60均值','t+60胜率']];
  [['净多增仓≥1万手 但当周价格跌>1%','S8a_up_price_down'],
   ['净多减仓≥1万手 但当周价格涨>1%','S8b_down_price_up']].forEach(function(p){
    var sc=DATA.scenarios[p[1]].stats, t20=sc.t20, t60=sc.t60;
    rows.push([p[0],DATA.scenarios[p[1]].n,
      '<span class="'+cls(t20.mean)+'">'+fmt(t20.mean)+'%</span>',t20.win.toFixed(1)+'%',
      '<span class="'+cls(t60.mean)+'">'+fmt(t60.mean)+'%</span>',t60.win.toFixed(1)+'%']);
  });
  document.getElementById('t_s8').innerHTML=rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return (j===0||i===0)?'<td>'+c+'</td>':'<td class="num">'+c+'</td>';}).join('')+'</tr>';}).join('');
})();

// ---------- 7. 可信度分级表 ----------
(function(){
  var rows=[['信号','可信度','依据（样本/时点）','交叉验证要求']];
  var g=[['多头增仓但当周价跌 → 偏空','t-hi','S8a n=105；t+20 胜率28% 跨4段一致','成交量/基本面确认下跌原因'],['多头连增后追多 → 否决','t-hi','S1 n=240/148/83；6时点全负胜率<40%','——'],['低位空头回补 → 浅反弹','t-hi','S3-low n=101；2020-24 t+60 胜率75%','位置确认+反弹量能验证'],
    ['高位多头观望 → 中继','t-mid','S2 n=17；t+40 胜率65%','排除多头减持的顶部形态+基本面缺口'],['空头持续增仓 → 逼空潜力','t-mid','S5 n=248；2020-24 t+20 胜率62%','确认趋势方向（牛/熊）'],['多空同步增仓 → 分歧放大','t-mid','S6 n=115；t+20 +1.1%','看突破方向，避免在分歧中下单'],['OI显著萎缩 → 短反弹(缺口行情除外)','t-mid','S7 n=139；t+20 胜率60%；2025+失效','判断行情类型(是否基本面缺口定价)'],
    ['减仓但当周价涨 → 逼空但持续性弱','t-low','S8b n=100；t+60 衰减至56.8%','出现快速回补失效即离场']];
  g.forEach(function(r){rows.push(['<b>'+r[0]+'</b>','<span class="tag '+r[1]+'">'+(r[1]==='t-hi'?'高':r[1]==='t-mid'?'中':'低')+'</span>',r[2],r[3]]);});
  document.getElementById('t_grade').innerHTML=rows.map(function(r,i){return '<tr>'+r.map(function(c,j){return '<td>'+c+'</td>';}).join('')+'</tr>';}).join('');
})();

// ---------- 8. 分段 t+20 胜率图 ----------
(function(){
  var chart=echarts.init(document.getElementById('c_seg'));
  var sg=DATA.seg, segKeys=Object.keys(sg);
  var scenKeys=[['S1_3w','多头连增3周',OI.blue],['S5_2w','空头连增2周',OI.purple],['S7_shrink','OI萎缩',OI.orange],['S8a','增仓价跌背离',OI.red]];
  var series=scenKeys.map(function(p){
    return {name:p[1],type:'line',data:segKeys.map(function(k){var v=sg[k][p[0]]; return v&&v.t20w!==null?v.t20w:null;}),showSymbol:true,symbolSize:7,
      lineStyle:{width:2,color:p[2]},itemStyle:{color:p[2]}};
  });
  series.push({name:'基准46.8%',type:'line',data:segKeys.map(function(){return 46.8;}),lineStyle:{type:'dashed',width:1.5,color:OI.black},itemStyle:{color:OI.black},symbol:'none'});
  chart.setOption({tooltip:{trigger:'axis',valueFormatter:function(v){return v===null?'—':v.toFixed(0)+'%';}},
    legend:{data:series.map(function(s){return s.name;}),textStyle:{color:SUB}},grid:{left:45,right:20,top:40,bottom:44},
    xAxis:{type:'category',data:segKeys},yAxis:{type:'value',name:'t+20胜率%',min:0,max:90,nameTextStyle:{color:SUB}},
    series:series});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA_JS__", data_js)

os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
open(OUT_HTML, "w", encoding="utf-8").write(HTML)
print("HTML written:", OUT_HTML, "| size:", len(HTML))