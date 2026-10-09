# -*- coding: utf-8 -*-
"""110 号报告生成器：棕榈油基本面全景"""
import json, os, io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "reports", "110_棕榈油基本面全景_20261007")
D = json.load(open(os.path.join(OUT, "_data.json"), encoding="utf-8"))

W = {w["my"]: w for w in D["world"]}
YRS = sorted(W)
SUP, SCEN, ENSO = D["sup"], D["scen"], D["enso"]

# biodiesel 子块由 D["id"] 派生（印尼工业消费 = 生柴 + 油化，MY2015 vs MY2026）
SUP.setdefault("biodiesel", {
    "id_industrial_2015": D["id"]["2015"]["industrial"],
    "id_industrial_2026": D["id"]["2026"]["industrial"],
})

# ---------- 关键数字 ----------
w26, w25 = W["2026"], W["2025"]
id26, my26 = D["id"]["2026"], D["my"]["2026"]
mpob = {m["ym"]: m for m in D["mpob"]}
lat = [p for p in D["price"] if p.get("palm")][-1]

# 单产 CAGR
def cagr(a, b, n):
    return 100 * ((b / a) ** (1.0 / n) - 1) if a > 0 and b > 0 else 0

yld_cagr_2026 = cagr(W["2020"]["yield"], W["2026"]["yield"], 6)
area_cagr_2026 = cagr(W["2020"]["area_kha"], W["2026"]["area_kha"], 6)
my_yld_peak = max(((y, r["yield"]) for y, r in D["my"].items()), key=lambda x: x[1])

HTML = []
A = HTML.append

A("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>110 棕榈油基本面全景 · 近端极松 vs 远端三重收紧 · 2026-10-07</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;--red:#d9381e;--green:#0b8a5f;
      --blue:#1e66d6;--o1:#0072B2;--o2:#E69F00;--o3:#56B4E9;--o4:#CC79A7;--o5:#D55E00;--o6:#009E73;--o7:#000;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--ink);font:14px/1.78 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:26px 16px 60px;}
.wrap{max-width:1280px;margin:0 auto;}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px 26px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
h1{font-size:23px;line-height:1.42;margin-bottom:6px;color:#111827;}
.meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
h2{font-size:17px;margin:2px 0 13px;padding-left:11px;border-left:4px solid var(--blue);}
h3{font-size:14.2px;margin:17px 0 8px;color:#374151;font-weight:650;}
h4{font-size:13.2px;margin:13px 0 6px;color:#4b5563;}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(196px,1fr));gap:12px;margin-top:15px;}
.kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:13px 15px;}
.kpi .num{font-size:21px;font-weight:720;letter-spacing:-.2px;}
.kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);} .kpi .num.blue{color:var(--blue);}
.kpi .num.warn{color:var(--o2);}
.kpi .lab{color:var(--sub);font-size:11.8px;margin-top:3px;line-height:1.5;}
.chart{width:100%;height:410px;}
.chart.sm{height:305px;} .chart.mid{height:355px;} .chart.tall{height:470px;}
table{width:100%;border-collapse:collapse;font-size:12.4px;}
th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);font-weight:640;white-space:nowrap;}
th.num{text-align:right;}
td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
td.num{text-align:right;font-variant-numeric:tabular-nums;}
td.up{color:var(--red);font-weight:640;} td.dn{color:var(--green);font-weight:640;}
tr.hl-row td{background:#eef6ff;} tr.warn-row td{background:#fff8ec;}
.scroll{overflow-x:auto;}
.note{color:var(--sub);font-size:11.9px;margin-top:9px;line-height:1.7;}
.keypoint{background:#eef7f2;border:1px solid #cde8da;border-left:4px solid var(--o6);border-radius:9px;padding:13px 17px;font-size:12.9px;color:#123f2c;margin:13px 0 5px;}
.warn{background:#fff8ec;border:1px solid #f3dfb6;border-left:4px solid var(--o2);border-radius:9px;padding:13px 17px;font-size:12.9px;color:#75470a;margin:13px 0 5px;}
.contra{background:#fdf1f1;border:1px solid #f2cfcf;border-left:4px solid var(--o5);border-radius:9px;padding:13px 17px;font-size:12.9px;color:#7c1f1f;margin:13px 0 5px;}
.info{background:#eef4fd;border:1px solid #cfe0f7;border-left:4px solid var(--o1);border-radius:9px;padding:13px 17px;font-size:12.9px;color:#12355e;margin:13px 0 5px;}
.keypoint ul,.warn ul,.contra ul,.info ul{margin:7px 0 0 19px;} .keypoint li,.warn li,.contra li,.info li{margin-bottom:5px;}
.dis{color:var(--sub);font-size:11.9px;border-top:1px dashed var(--line);padding-top:13px;margin-top:17px;line-height:1.75;}
.hl{font-weight:720;color:var(--red);} .hlg{font-weight:720;color:var(--green);} .hlb{font-weight:720;color:var(--blue);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;} @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
.tag{display:inline-block;padding:1px 7px;border-radius:5px;font-size:11px;font-weight:640;margin-right:5px;}
.tag.bear{background:#e8f5ef;color:#0b6b4a;} .tag.bull{background:#fdeeeb;color:#b02d17;}
.tag.neu{background:#eef1f5;color:#5a6472;} .tag.pol{background:#f3ecfa;color:#6b3fa0;}
code{background:#f2f4f7;padding:1px 5px;border-radius:4px;font-size:11.8px;font-family:ui-monospace,Consolas,monospace;}
.sig{font-family:ui-monospace,Consolas,monospace;font-size:11.6px;}
.verdict{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px;}
.vbox{flex:1;min-width:250px;border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:#fbfcfe;}
.vbox .vt{font-size:12.5px;color:var(--sub);margin-bottom:6px;font-weight:600;}
.vbox .vv{font-size:15px;font-weight:700;line-height:1.5;}
</style>
</head>
<body>
<div class="wrap">
""")

# ================= 标题 =================
A("""<div class="card">
<h1>110 · 棕榈油基本面全景：近端极度宽松 vs 远端三重收紧</h1>
<div class="meta">数据截至 2026-10-07 ｜ 主口径 USDA FAS PSD（vintage 2026-09）｜ 市场年 = 10月–次年9月 ｜
月度实况 MPOB / GAPKI ｜ 价格 IMF-FRED ｜ ENSO CPC-ONI ｜ 单位：千吨(kt)/百万吨(Mt)/美元每吨</div>
""")

A('<div class="kpis">')
for num, cls, lab in [
    ("%.1f Mt" % (w26["end"] / 1000), "warn", "全球期末库存 MY2026<br>STU %.1f%%（分位 %.0f%% / %.0f%% 双窗口）" % (
        w26["stu"], w26.get("stu_pctile_1989-2025", 0), w26.get("stu_pctile_2010-2025", 0))),
    ("%+.2f Mt" % (w26["surplus"] / 1000), "dn", "全球盈余（产量−消费）<br>较 MY2025 的 %+.2f Mt 收窄 %.2f Mt" % (
        w25["surplus"] / 1000, (w25["surplus"] - w26["surplus"]) / 1000)),
    ("%.0f 万吨" % (mpob["2026-09"]["total_stocks_wt"] or 0), "up", "马来 9月库存（路透调查）<br>8月实绩 %.0f 万吨，历史峰值 %.0f 万吨(2018-12)" % (
        mpob["2026-08"]["total_stocks_wt"], 322)),
    ("%.0f $" % lat["palm"], "up", "棕榈油 IMF 月均（%s）<br>1980以来分位 %.1f%%｜近5年 %.1f%%" % (
        lat["ym"], SUP["price"]["palm_pctile_all"], SUP["price"]["palm_pctile_5y"])),
    ("%.0f $" % (lat["pd_spread"] or 0), "up", "豆油−棕榈油价差<br>历史分位 98.7%（现行口径段 92.9%）"),
    ("+2.16", "warn", "ONI JAS-2026（强厄尔尼诺）<br>历史第 3 强峰值，但统计上无法证实减产"),
    ("82.3%", "blue", "印尼+马来源产量集中度<br>出口集中度更高达 87.1%"),
    ("%.1f%%" % w26["biodiesel_share"], "blue", "工业消费占比（生柴+油化）<br>2000 年 14.6% → 2026 年 35.6%"),
]:
    A('<div class="kpi"><div class="num %s">%s</div><div class="lab">%s</div></div>' % (cls, num, lab))
A('</div>')

# ================= 一、结论 =================
A("""
<h2 style="margin-top:24px">一、结论先行：三个时间尺度上方向相反的信号</h2>
<div class="verdict">
<div class="vbox"><div class="vt">近端（0–3 个月）</div><div class="vv" style="color:var(--green)">▼ 宽松，利空主导</div>
<div class="note" style="margin-top:7px">马来 9月库存预估 %.0f 万吨，将创历史新高（前峰 %.0f 万吨 / 2018-12）；
9月产量预估 %.0f 万吨亦为纪录，出口连续两月环比下滑（ITS 9月 −17.1%%）。MPOB 正式数据 10-12 公布，利空集中兑现。</div></div>
<div class="vbox"><div class="vt">中端（3–12 个月）</div><div class="vv" style="color:var(--o2)">◆ 政策驱动收紧，可核实</div>
<div class="note" style="margin-top:7px">印尼 B50 已于 2026-07-01 落地，GAPKI 测算年增 CPO 内需 300–350 万吨（= 全球消费 3.8%%），
2026 下半年出口减少约 200 万吨。马来 B15 自 2026-06-01 起增需 33 万吨。两国生柴强制掺混直接削减可贸易量。</div></div>
<div class="vbox"><div class="vt">远端（12–24 个月）</div><div class="vv" style="color:var(--red)">▲ 供给引擎熄火 + 天气风险</div>
<div class="note" style="margin-top:7px">全球单产 CAGR 2020–2026 = <b>%+.2f%%/年</b>（首次转负），面积增速降至 %+.2f%%/年；
产量增长 %d%% 靠面积、%d%% 靠单产。叠加 ONI +2.16 强厄尔尼诺，市场共识指向 2027 两国减产约 3%%。</div></div>
</div>
""" % (mpob["2026-09"]["total_stocks_wt"] or 0, 322, 210,
       yld_cagr_2026, area_cagr_2026,
       SUP["attribution_world"]["area_pct"], SUP["attribution_world"]["yield_pct"]))

A("""
<h3>多空因素对照（按可核实性排序，非按权重）</h3>
<div class="scroll"><table>
<tr><th style="width:52px">方向</th><th style="width:210px">因素</th><th style="width:150px">量级 / 数据</th>
<th>可核实性与时效</th></tr>
<tr><td><span class="tag bear">利空</span></td><td>马来西亚库存逼近历史峰值</td><td class="num">9月预估 337 万吨</td>
<td>MPOB 8月实绩 282 万吨已公布；9月为路透调查预估，<b>10-12 官方数据待验证</b></td></tr>
<tr><td><span class="tag bear">利空</span></td><td>马来 9月产量创纪录</td><td class="num">预估 210 万吨（环比 +15.7%%）</td>
<td>路透调查 / SPPOMA 高频数据，非官方实绩</td></tr>
<tr><td><span class="tag bear">利空</span></td><td>出口连续下滑</td><td class="num">ITS 9月 −17.1%%；MPOB 8月 −7.5%%</td>
<td>MPOB 8月为实绩；9月为船运调查机构预估</td></tr>
<tr><td><span class="tag bear">利空</span></td><td>印度采购转向豆油/葵花油</td><td class="num">价差收窄削弱棕榈油性价比</td>
<td>路透引交易商定性表述；印度 9月已下调食用油进口关税，<b>方向存在争议</b></td></tr>
<tr class="hl-row"><td><span class="tag bull">利多</span></td><td>印尼 B50 强制掺混</td><td class="num">年增 CPO 内需 300–350 万吨</td>
<td><b>已落地（2026-07-01）</b>，GAPKI + 印尼能矿部双口径；实际兑现率待跟踪</td></tr>
<tr class="hl-row"><td><span class="tag bull">利多</span></td><td>单产增长引擎熄火</td><td class="num">全球单产 CAGR 2020–26 = −0.17%%/年</td>
<td><b>USDA PSD 实绩序列，可核实</b>；马来单产 2010–14 峰值 %.2f → 2020–26 均值 3.44（树龄老化）</td></tr>
<tr><td><span class="tag bull">利多</span></td><td>P-D 价差极端走阔 → 替代需求</td><td class="num">%.0f $/t，分位 98.7%%</td>
<td>IMF 月度实绩；但需注意<b>口径分段</b>（2024-11 起棕榈油改 CIF NWE）</td></tr>
<tr><td><span class="tag bull">利多</span></td><td>马来 B15 生柴强制</td><td class="num">MY2026/27 增需 33 万吨</td>
<td>USDA FAS GAIN（2026-07-01）；2026-06-01 起分阶段实施</td></tr>
<tr class="warn-row"><td><span class="tag neu">不确定</span></td><td>厄尔尼诺滞后减产</td><td class="num">ONI +2.16（JAS-2026）</td>
<td><b>本报告统计检验未能证实</b>（57 项检验，BH-FDR 拒绝 0 项）；仅产业共识与机构预测支持</td></tr>
<tr><td><span class="tag neu">不确定</span></td><td>原油价格（生柴经济性）</td><td class="num">Brent 2026-09 约 114–120 $/bbl</td>
<td>地缘溢价，波动大；红海/霍尔木兹扰动</td></tr>
<tr><td><span class="tag pol">政策</span></td><td>印尼出口税与 levy</td><td class="num">CPO 出口税 12.5%%（2026-03-01 上调）</td>
<td>政策摇摆风险高：2026-01 曾宣布放弃 B50，后于 7月反转实施</td></tr>
</table></div>
<div class="note">▲ 表中“量级”为已核实数字或其区间；标注“预估/调查”的项目尚未有官方实绩。红色底纹行 = 本报告认为证据最强的两项多头逻辑。</div>
""" % (my_yld_peak[1], lat["pd_spread"] or 0))

A("""
<div class="contra">
<b>本报告的三项方法论警示（先读这段再看图表）</b>
<ul>
<li><b>STU 分位对窗口极度敏感</b>：MY2026 的 STU = %.1f%%，在 1989–2025 窗口是 <b>%.1f 分位（偏宽松）</b>，
在 2010–2025 窗口仅 <b>%.1f 分位（偏紧）</b>。原因是 STU 中枢发生了结构性上移（1990s 约 10–15%% → 2010s 后 15–24%%）。
<b>任何单一分位数都不足以判断松紧</b>，本报告全文并列披露两个窗口。</li>
<li><b>USDA 马来库存数字已被 MPOB 实绩证伪</b>：PSD MY2025（期末 = 2026年9月）马来期末库存 = %.0f 万吨，
vintage 标记为 2026-09；但 MPOB <b>8月已公布实绩 %.0f 万吨</b>，9月路透调查预估 %.0f 万吨。
USDA 低估 34–90 万吨（−12%% ~ −27%%）。<b>涉及马来库存一律以 MPOB 为准</b>，PSD 仅用于跨国平衡表框架。</li>
<li><b>厄尔尼诺减产不是统计结论</b>：市场普遍引用“滞后 9–12 月减产 10–25%%”，但本报告用 1990–2026 数据做去趋势 + 多重比较校正后，
<b>57 项滞后检验无一在 5%% 水平显著</b>（最小原始 p=0.017，Bonferroni 校正后 p=0.99）。
该叙事只能作为情景参照，不可作为独立多头论据。详见第七节。</li>
</ul>
</div>
""" % (w26["stu"], w26.get("stu_pctile_1989-2025", 0), w26.get("stu_pctile_2010-2025", 0),
       w25 and 247.5, mpob["2026-08"]["total_stocks_wt"], mpob["2026-09"]["total_stocks_wt"] or 0))

A("</div>")

# ================= 二、全球平衡表 =================
A("""<div class="card">
<h2>二、全球平衡表 38 年：盈余连续第二年收窄，但仍未转缺口</h2>
<div class="info">
MY2026（= 2026/27，2026-10 ~ 2027-09，<b>进行中，属预测值</b>）：产量 %.1f Mt / 消费 %.1f Mt / 盈余 %+.2f Mt / 期末 %.2f Mt / STU %.1f%%。<br>
与 MY2025 相比：产量 <b>%+.2f Mt</b>、消费 <b>%+.2f Mt</b>、盈余 <b>%+.2f Mt</b>、期末库存 <b>%+.2f Mt</b>、STU <b>%+.1f pct</b>。<br>
→ 收紧的全部来源是<b>需求侧</b>（消费 +%.1f Mt），供给侧实际略降（−%.1f Mt）。这与“厄尔尼诺减产”叙事不同：USDA 的 MY2026 预测中产量只降了 0.3%%，减产尚未被计入。
</div>
<div id="c1" class="chart tall"></div>
<div class="note">▲ 柱 = 产量 / 消费（左轴，千吨）；实线 = 期末库存，虚线 = STU%%（右轴）。
STU 在 MY2021 见顶 %.1f%% 后连续 5 年下行至 %.1f%%。灰色阴影带 = MY2026（进行中，预测值）。
配色为 Okabe–Ito 色弱安全方案，并以线型（实线/虚线）与标记（●/▲）作非颜色区分。</div>
""" % (w26["prod"] / 1000, w26["dom_cons"] / 1000, w26["surplus"] / 1000, w26["end"] / 1000, w26["stu"],
       (w26["prod"] - w25["prod"]) / 1000, (w26["dom_cons"] - w25["dom_cons"]) / 1000,
       (w26["surplus"] - w25["surplus"]) / 1000, (w26["end"] - w25["end"]) / 1000,
       w26["stu"] - w25["stu"], (w26["dom_cons"] - w25["dom_cons"]) / 1000,
       (w25["prod"] - w26["prod"]) / 1000, W["2021"]["stu"], w26["stu"]))

# 平衡表明细
A("""<h3>全球平衡表明细（近 14 个市场年，千吨）</h3><div class="scroll"><table>
<tr><th>市场年</th><th class="num">收获面积<br>(千公顷)</th><th class="num">单产<br>(t/ha)</th>
<th class="num">期初库存</th><th class="num">产量</th><th class="num">进口</th><th class="num">工业消费<br>(生柴+油化)</th>
<th class="num">食用消费</th><th class="num">总消费</th><th class="num">出口</th><th class="num">期末库存</th>
<th class="num">盈余</th><th class="num">STU%</th><th>vintage</th></tr>""")
for y in YRS[-14:]:
    w_ = W[y]
    cls = ' class="hl-row"' if y == "2026" else (' class="warn-row"' if y == "2025" else "")
    A("<tr%s><td><b>%s</b>%s</td><td class='num'>%.0f</td><td class='num'>%.3f</td><td class='num'>%.0f</td>"
      "<td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td>"
      "<td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td>"
      "<td class='num %s'>%+.0f</td><td class='num'>%.1f</td><td class='sig'>%s</td></tr>" % (
          cls, y, "（2026/27·进行中）" if y == "2026" else "",
          w_["area_kha"], w_["yield"], w_["beg"], w_["prod"], w_["imp"], w_["industrial"],
          w_["food"], w_["dom_cons"], w_["exp"], w_["end"],
          "up" if w_["surplus"] > 0 else "dn", w_["surplus"], w_["stu"], w_["vintage"]))
A("""</table></div>
<div class="note">▲ 消费口径 = PSD 属性 125 <code>Domestic Consumption</code> = 140 工业 + 149 食用 + 161 饲料损耗（已跑恒等式校验：38 年供给/分配全部平衡，0 个不平）。
<b>注意与糖不同</b>：糖的消费码是 126 <code>Total Disappearance</code>，棕榈油用 126 会取到空值。STU = 176 期末库存 ÷ 125 总消费（自行计算，PSD 的 195 字段未填充）。</div>
""")

# STU 分位
A("""<h3>STU 历史分位：窗口选择会改变结论方向</h3>
<div id="c2" class="chart mid"></div>
<div class="scroll"><table style="margin-top:12px">
<tr><th>分位窗口</th><th class="num">样本数 n</th><th class="num">区间下限</th><th class="num">区间上限</th>
<th class="num">MY2026 STU</th><th class="num">分位</th><th>解读</th></tr>""")
for win, key in [("1989–2025（全样本）", "stu_pctile_1989-2025"),
                 ("2000–2025", "stu_pctile_2000-2025"),
                 ("2010–2025（近 16 年）", "stu_pctile_2010-2025")]:
    lo = win[:4]
    s = [W[y]["stu"] for y in YRS if lo <= y <= "2025"]
    interp = ("偏宽松：1990s STU 中枢仅 10–15%，当前 18.3% 高于那个时代"
              if "1989" in win else
              "居中：跨越了 STU 中枢上移的过渡期"
              if "2000" in win else
              "偏紧：2010 年后 STU 中枢已升至 15–24%，18.3% 落在下沿附近")
    A("<tr><td><b>%s</b></td><td class='num'>%d</td><td class='num'>%.1f%%</td><td class='num'>%.1f%%</td>"
      "<td class='num'>%.1f%%</td><td class='num'><b>%.1f%%</b></td><td style='white-space:normal'>%s</td></tr>" % (
          win, len(s), min(s), max(s), w26["stu"], w26.get(key, 0), interp))
A("""</table></div>
<div class="warn"><b>为什么中枢上移</b>：1990s 全球产量 24–36 Mt、库存 3–6 Mt；2020s 产量 74–81 Mt、库存 14–17 Mt。
产业规模化后各环节（种植园、压榨厂、精炼厂、贸易商、进口国）持有的绝对周转库存同步放大，STU 中枢随之抬升。
<b>因此“STU 处于历史低位”这类表述必须指明窗口，否则可能同时得出“最紧”和“最松”两种结论。</b></div>
</div>""")

# ================= 三、供给 =================
A("""<div class="card">
<h2>三、供给：两国的绝对垄断，与正在熄火的增长引擎</h2>
<div class="grid2">
<div><div id="c3" class="chart mid"></div>
<div class="note">▲ 产量集中度：印尼 %.1f%% + 马来 %.1f%% = <b>%.1f%%</b>；出口集中度 <b>%.1f%%</b>。
出口集中度高于产量集中度，意味着两国对<b>可贸易量</b>的控制力更强。</div></div>
<div><div id="c4" class="chart mid"></div>
<div class="note">▲ 进口方高度分散：印度 %.1f%% + 中国 %.1f%% + 巴基斯坦 %.1f%% + 欧盟 %.1f%% = %.1f%%，
前 6 大占 %.1f%%。<b>买方分散、卖方集中</b>是棕榈油定价权结构的根本特征。</div></div>
</div>
""" % (100 * id26["prod"] / w26["prod"], 100 * my26["prod"] / w26["prod"],
       100 * (id26["prod"] + my26["prod"]) / w26["prod"],
       100 * (id26["exp"] + my26["exp"]) / w26["exp"],
       8700 / w26["exp"] * 100, 3900 / w26["exp"] * 100, 3700 / w26["exp"] * 100,
       3100 / w26["exp"] * 100, (8700 + 3900 + 3700 + 3100) / w26["exp"] * 100,
       (8700 + 3900 + 3700 + 3100 + 1725 + 1700) / w26["exp"] * 100))

A("""<h3>3.1 增长引擎切换：从“单产提升”到“纯面积扩张”</h3>
<div id="c5" class="chart tall"></div>
<div class="scroll"><table style="margin-top:12px">
<tr><th>期间</th><th class="num">全球面积 CAGR</th><th class="num">全球单产 CAGR</th><th class="num">全球产量 CAGR</th>
<th class="num">印尼面积</th><th class="num">印尼单产</th><th class="num">马来面积</th><th class="num">马来单产</th><th>阶段特征</th></tr>""")
periods = [("1990", "2000", "高速双轮驱动"), ("2000", "2010", "面积主导，单产加速"),
           ("2010", "2020", "面积减速，单产停滞"), ("2020", "2026", "单产转负，仅剩面积")]
for y0, y1, lbl in periods:
    gy = lambda cc, k: (W[y0] if cc is None else D[cc][y0])[k]
    A("<tr%s><td><b>%s–%s</b></td><td class='num'>%+.2f%%</td><td class='num %s'>%+.2f%%</td>"
      "<td class='num'>%+.2f%%</td><td class='num'>%+.2f%%</td><td class='num'>%+.2f%%</td>"
      "<td class='num'>%+.2f%%</td><td class='num %s'>%+.2f%%</td><td>%s</td></tr>" % (
          ' class="hl-row"' if y1 == "2026" else "", y0, y1,
          cagr(gy(None, "area_kha"), W[y1]["area_kha"], int(y1) - int(y0)),
          "dn" if cagr(W[y0]["yield"], W[y1]["yield"], int(y1) - int(y0)) < 0 else "",
          cagr(gy(None, "yield"), W[y1]["yield"], int(y1) - int(y0)),
          cagr(gy(None, "prod"), W[y1]["prod"], int(y1) - int(y0)),
          cagr(D["id"][y0]["area_kha"], D["id"][y1]["area_kha"], int(y1) - int(y0)),
          cagr(D["id"][y0]["yield"], D["id"][y1]["yield"], int(y1) - int(y0)),
          cagr(D["my"][y0]["area_kha"], D["my"][y1]["area_kha"], int(y1) - int(y0)),
          "dn" if cagr(D["my"][y0]["yield"], D["my"][y1]["yield"], int(y1) - int(y0)) < 0 else "",
          cagr(D["my"][y0]["yield"], D["my"][y1]["yield"], int(y1) - int(y0)), lbl))
A("</table></div>")

A("""
<div class="keypoint">
<b>三个可核实的结构性事实</b>
<ul>
<li><b>全球单产 CAGR 2020–2026 = %+.2f%%/年，首次转负</b>（1990–2000 为 +1.21%%，2000–2010 为 +1.88%%）。
同期面积 CAGR 从 +6.93%% 一路降至 +1.79%%。两个引擎同时减速。</li>
<li><b>马来西亚单产呈明确倒 U 型</b>：线性趋势 R²=0.005（无趋势），二次趋势 R²=<b>0.650</b>。
峰值出现在 <b>MY%s（%.2f t/ha）</b>，2020–26 均值已回落至 3.44，2026 年为 %.2f。
这与马来种植园树龄老化 + 翻种（replanting）进度偏慢的产业事实一致。</li>
<li><b>2015→2026 产量增长归因（对数分解）</b>：全球面积贡献 <b>%d%%</b> / 单产贡献 <b>%d%%</b>；
马来更极端 —— 面积贡献 <b>%d%%</b>、单产贡献 <b>%d%%</b>（即单产是<b>拖累项</b>，产量增长全靠面积堆出来）。</li>
</ul>
</div>
<div class="warn"><b>这意味着什么</b>：棕榈油供给已进入“面积约束型”阶段。面积扩张受三重硬约束 ——
①印尼/马来森林与泥炭地开发禁令、EUDR 等可持续认证要求；②GAPKI 明确指出小农翻种计划（PSR）推进缓慢是产能瓶颈；
③油棕从种植到投产需 3–4 年，<b>今日的面积决策要 2030 年才反映到产量</b>。
因此供给端对价格信号的响应弹性显著低于历史水平，任何需求侧冲击（如 B50）都更难被供给消化。</div>
""" % (yld_cagr_2026, my_yld_peak[0], my_yld_peak[1], D["my"]["2026"]["yield"],
       SUP["attribution_world"]["area_pct"], SUP["attribution_world"]["yield_pct"],
       SUP["attribution_MY"]["area_pct"], SUP["attribution_MY"]["yield_pct"]))

# 主产国明细表
A("""<h3>3.2 印尼 vs 马来西亚：两国分国平衡表（MY2015–MY2026，千吨）</h3>
<div class="grid2">
<div><h4>印度尼西亚</h4><div class="scroll"><table>
<tr><th>MY</th><th class="num">面积<br>千ha</th><th class="num">单产</th><th class="num">产量</th>
<th class="num">国内</th><th class="num">其中工业</th><th class="num">出口</th><th class="num">期末</th><th class="num">STU%</th></tr>""")
for y in sorted(D["id"])[-12:]:
    r = D["id"][y]
    A("<tr%s><td><b>%s</b></td><td class='num'>%.0f</td><td class='num'>%.2f</td><td class='num'>%.0f</td>"
      "<td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td>"
      "<td class='num'>%.1f</td></tr>" % (
          ' class="hl-row"' if y == "2026" else "", y, r["area_kha"], r["yield"], r["prod"],
          r["dom"], r["industrial"], r["exp"], r["end"], r["stu"] or 0))
A("""</table></div></div>
<div><h4>马来西亚</h4><div class="scroll"><table>
<tr><th>MY</th><th class="num">面积<br>千ha</th><th class="num">单产</th><th class="num">产量</th>
<th class="num">国内</th><th class="num">其中工业</th><th class="num">出口</th><th class="num">期末</th><th class="num">STU%</th></tr>""")
for y in sorted(D["my"])[-12:]:
    r = D["my"][y]
    A("<tr%s><td><b>%s</b></td><td class='num'>%.0f</td><td class='num'>%.2f</td><td class='num'>%.0f</td>"
      "<td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td><td class='num'>%.0f</td>"
      "<td class='num'>%.1f</td></tr>" % (
          ' class="hl-row"' if y == "2026" else "", y, r["area_kha"], r["yield"], r["prod"],
          r["dom"], r["industrial"], r["exp"], r["end"], r["stu"] or 0))
A("""</table></div></div></div>
<div class="note">▲ 印尼 STU（%.1f%%）远低于马来（%.1f%%），因为印尼国内消费基数大（%.0f kt，其中工业 %.0f kt 被生柴锁定）。
<b>马来 STU 高不代表马来更宽松</b> —— 马来出口/产量 = %.1f%%（印尼仅 %.1f%%），是典型的“高周转出口枢纽”结构，
其库存绝对量（%.0f kt）只有印尼（%.0f kt）的 %.0f%%。分国 STU 横向比较无意义，应看库存绝对量与净贸易方向。</div>
""" % (id26["stu"], my26["stu"], id26["dom"], id26["industrial"],
       100 * my26["exp"] / my26["prod"], 100 * id26["exp"] / id26["prod"],
       my26["end"], id26["end"], 100 * my26["end"] / id26["end"]))
A("</div>")

# ================= 四、需求 =================
A("""<div class="card">
<h2>四、需求：生物柴油已成为增量的主引擎，且被政策强制锁定</h2>
<div id="c6" class="chart tall"></div>
<div class="scroll"><table style="margin-top:12px">
<tr><th>期间</th><th class="num">Δ工业消费<br>(千吨)</th><th class="num">Δ食用消费<br>(千吨)</th>
<th class="num">工业增量占<br>总增量</th><th class="num">期末工业占比</th><th>阶段特征</th></tr>""")
for d_ in SUP["demand_growth"]:
    y0, y1 = d_["period"].split("-")
    lbl = {"2000": "食用主导（人口与收入驱动）", "2010": "生柴与食用并驾齐驱",
           "2020": "生柴主导（印尼 B20→B30→B35）", "2015": "11 年长周期",
           "2025": "单年变化"}.get(y0, "")
    A("<tr%s><td><b>%s</b></td><td class='num up'>%+.0f</td><td class='num'>%+.0f</td>"
      "<td class='num'><b>%s%%</b></td><td class='num'>%.1f%%</td><td>%s</td></tr>" % (
          ' class="hl-row"' if d_["period"] == "2020-2026" else "",
          d_["period"], d_["d_ind"], d_["d_food"],
          ("%.0f" % d_["ind_share_pct"]) if d_["ind_share_pct"] is not None else "—",
          W[y1]["biodiesel_share"], lbl))
A("""</table></div>
<div class="keypoint"><b>结构性转变</b>：2000→2010 工业增量占总增量 32%%（食用主导）；2010→2020 升至 48%%；
<b>2020→2026 已达 70%%</b>。全球棕榈油工业消费从 MY2000 的 %.0f kt 增至 MY2026 的 %.0f kt（+%.0f kt），
而食用消费同期仅增 %.0f kt。其中印尼工业消费从 MY2015 的 %.0f kt 增至 %.0f kt（<b>+%.0f%%</b>），
是这一转变的绝对主力。</div>
""" % (W["2000"]["industrial"], w26["industrial"], w26["industrial"] - W["2000"]["industrial"],
       w26["food"] - W["2000"]["food"],
       SUP["biodiesel"]["id_industrial_2015"], SUP["biodiesel"]["id_industrial_2026"],
       100 * (SUP["biodiesel"]["id_industrial_2026"] - SUP["biodiesel"]["id_industrial_2015"])
       / SUP["biodiesel"]["id_industrial_2015"]))

A("""<h3>4.1 印尼 B50：政策已落地，但兑现率是关键跟踪变量</h3>
<div class="scroll"><table>
<tr><th style="width:150px">项目</th><th style="width:130px">数值 / 时点</th><th>来源与说明</th></tr>
<tr><td>政策实施日</td><td><b>2026-07-01</b></td><td>经 8 个月试用期后启动。
<b>注意政策摇摆</b>：2026年1月印尼政府曾宣布放弃 B50、维持 B40，后于 7月反转实施。</td></tr>
<tr><td>年增 CPO 内需</td><td class="num">300–350 万吨</td><td>GAPKI 主席 Eddy Martono（2026-05-08）：完全运行后年增 300–350 万吨；
2026 年初阶段仅 150–170 万吨，逐年爬坡。</td></tr>
<tr><td>B50 总需求</td><td class="num">1,600 万吨 CPO/年</td><td>GAPKI 测算，vs B40 的 1,300 万吨。
印尼能矿部口径：吸收量从 1,520 万吨提升至 1,630–1,700 万吨。</td></tr>
<tr><td>2026 国家生柴配额</td><td class="num">1,565 万千升</td><td>其中 745 万千升由 BPDPKS（棕榈油种植基金）补贴；1–4月已分配 461 万千升。</td></tr>
<tr><td>出口减少量</td><td class="num">2026H2 约 200 万吨</td><td>GAPKI 测算，按 CIF 鹿特丹 1,356 $/t（2026Q1 均价）折约 27 亿美元出口收入损失。</td></tr>
<tr><td>融资机制</td><td>CPO 出口税 12.5%%</td><td>2026-03-01 起从 10%% 上调至 12.5%%；精炼产品同步 +2.5pct（现 4.75–9.5%%）。
<b>形成正反馈</b>：CPO 价格越高 → 税收越多 → B50 补贴资金越充足。</td></tr>
<tr class="warn-row"><td>产能缺口风险</td><td>PSR 翻种进度慢</td><td>GAPKI：印尼潜在产能可达 6,000 万吨/年，但小农翻种（PSR）推进缓慢使实际产能受限。
ISEAI 指出近 5 年 CPO 产量在 4,800–5,100 万吨区间“走平”。</td></tr>
<tr><td>技术争议</td><td>油耗 +3.12%%</td><td>印尼能矿部（2026-04-07）：重型设备耐受测试逾 900 小时无故障，油耗增 3.12%% “可接受”。
但矿业协会 Aspindo 与重型设备代理协会 PAABI 持保留意见（燃料成本占矿业总成本 35–40%%）。</td></tr>
</table></div>
<div class="info"><b>量级换算</b>：取中值 +3,000 kt CPO 内需 = 全球消费的 <b>%.1f%%</b> = 全球期末库存的 <b>%.2f 个月</b>
= 全球贸易量（出口 %.1f Mt）的 <b>%.1f%%</b>。<br>
<b>关键理解</b>：B50 不是通过”增加全球总需求“影响价格，而是通过<b>把印尼产量从可贸易池子里永久移除</b>。
印尼出口/产量 = %.1f%%（放大倍数 %.2fx），意味着印尼产量每减少 1%%，出口需减少 %.2f%%（假设国内消费刚性）。
这个杠杆比总量数字看起来更有力。</div>
""" % (100 * 3000 / w26["dom_cons"], 3000 / (w26["dom_cons"] / 12), w26["exp"] / 1000,
       100 * 3000 / w26["exp"], 100 * id26["exp"] / id26["prod"],
       id26["prod"] / id26["exp"], id26["prod"] / id26["exp"]))

A("""<h3>4.2 进口侧：印度是最大边际买家，但其政策与替代选择构成不确定性</h3>
<div class="scroll"><table>
<tr><th>进口方</th><th class="num">MY2026 进口<br>(千吨)</th><th class="num">份额</th><th class="num">累计</th>
<th class="num">工业/国内消费</th><th>需求性质与近期动向</th></tr>""")
imps = SCEN.get("_imps") or []
for i, (cc, nm, imp, ind, dom) in enumerate([
        ("IN", "印度", 8700, 650, 8875), ("CH", "中国", 3900, 1400, 3875),
        ("PK", "巴基斯坦", 3700, 75, 3700), ("E4", "欧盟", 3100, 1300, 3000),
        ("BG", "孟加拉", 1725, 50, 1775), ("US", "美国", 1700, 275, 1685)]):
    cum = sum(v for _, _, v, _, _ in [("a", "", 8700, 0, 0), ("b", "", 3900, 0, 0), ("c", "", 3700, 0, 0),
                                       ("d", "", 3100, 0, 0), ("e", "", 1725, 0, 0), ("f", "", 1700, 0, 0)][:i + 1])
    note = {
        "IN": "全球最大植物油进口国。<b>2026年9月下调棕榈油/豆油进口关税减半、葵花油归零</b>，排灯节前放宽进口窗口；"
              "但路透引交易商称 10月起进口将从 8–9月的高位回落，且因价差收窄转向豆油/葵花油。",
        "CH": "工业占比 36%（含生柴与油化）。MY2024 进口从 6,190 kt（MY2022）大幅降至 3,203 kt 后企稳于 3,900 kt。",
        "PK": "几乎纯食用需求（工业仅 2%），价格敏感度最高，是 P-D 价差收窄时最先切换的买家。",
        "E4": "工业占比 43%（生柴），但受 <b>EUDR（欧盟零毁林法规）</b>与 RED II 棕榈油生柴逐步淘汰政策压制，"
              "进口从 MY2020 的 5,951 kt 降至 3,100 kt（−48%）。",
        "BG": "纯食用需求，USDA GAIN 提及为马来出口增长的重要目的地之一。",
        "US": "工业占比 16%。<b>注意</b>：45Z 税收抵免限定北美原料，棕榈油不具备资格，因此美国生柴扩张<b>不</b>利好棕榈油。",
    }[cc]
    A("<tr><td><b>%s</b> <span class='sig'>(%s)</span></td><td class='num'>%.0f</td><td class='num'>%.1f%%</td>"
      "<td class='num'>%.1f%%</td><td class='num'>%.1f%%</td><td style='white-space:normal'>%s</td></tr>" % (
          nm, cc, imp, 100 * imp / w26["exp"], 100 * cum / w26["exp"],
          100 * ind / dom if dom else 0, note))
A("""</table></div>
<div class="note">▲ 份额分母为全球出口总量 %.0f kt。各国“国内消费”含转口，故份额合计略高于 100%%。
数据来源：USDA FAS PSD，vintage 2026-09。</div>
</div>""" % w26["exp"])

# ================= 五、MPOB 月度 =================
A("""<div class="card">
<h2>五、月度实况：马来西亚正在走向历史最高库存</h2>
<div class="contra"><b>核心矛盾：USDA 与 MPOB 的数字无法同时为真</b>
<ul>
<li>USDA PSD MY2025（市场年 2025-10 ~ 2026-09，期末即 2026年9月）马来西亚期末库存 = <b>%.0f 万吨</b>，
该记录 vintage 标记为 <b>2026-09</b>。</li>
<li>但 MPOB 已于 2026-09-10 <b>官方公布</b> 8月实绩库存 = <b>%.0f 万吨</b>（环比 +7.48%%，连续第 5 个月累库）。</li>
<li>船运调查机构 ITS 估 9月出口 %.1f 万吨（环比 −17.1%%）；路透调查预估 9月末库存 <b>%.0f 万吨</b>（环比 +19.5%%，连续第 6 个月累库）。</li>
<li>⇒ <b>USDA 低估 34–90 万吨（−12%% ~ −27%%）</b>。原因：PSD 的 MY2025 记录虽标 vintage 2026-09，
但其数字框架仍沿袭 2026-07-01 的 GAIN 马来报告（该报告给 MY2025/26 期末 280 万吨，且未含 8–9月累库）。
<b>本报告中凡涉及马来库存，一律以 MPOB 月度实绩为准，PSD 仅用于跨国平衡表框架。</b></li>
</ul></div>
<div id="c7" class="chart tall"></div>
<div class="scroll"><table style="margin-top:12px">
<tr><th>月份</th><th class="num">总库存<br>(万吨)</th><th class="num">CPO库存</th><th class="num">加工品库存</th>
<th class="num">产量</th><th class="num">出口</th><th class="num">进口</th><th>环比与数据来源</th></tr>
""" % (247.5, mpob["2026-08"]["total_stocks_wt"] or 0, 113,
       mpob["2026-09"]["total_stocks_wt"] or 0))
prev = None
for m in D["mpob"]:
    ts = m["total_stocks_wt"]
    mom = (100 * (ts - prev) / prev) if (prev and ts) else None
    est = "2026-09" == m["ym"]
    A("<tr%s><td><b>%s</b>%s</td><td class='num'>%s</td><td class='num'>%s</td><td class='num'>%s</td>"
      "<td class='num'>%s</td><td class='num'>%s</td><td class='num'>%s</td><td style='white-space:normal'>%s%s</td></tr>" % (
          ' class="hl-row"' if est else "", m["ym"], "（预估）" if est else "",
          ("%.0f" % ts) if ts else "—", ("%.0f" % m["cpo_stocks_wt"]) if m.get("cpo_stocks_wt") else "—",
          ("%.0f" % m["processed_stocks_wt"]) if m.get("processed_stocks_wt") else "—",
          ("%.0f" % m["production_wt"]) if m.get("production_wt") else "—",
          ("%.0f" % m["exports_wt"]) if m.get("exports_wt") else "—",
          ("%.1f" % m["imports_wt"]) if m.get("imports_wt") not in (None, 0) else "0",
          ("环比 %+.1f%% ｜ " % mom) if mom is not None else "", m["note"]))
    if ts: prev = ts
A("""</table></div>
<div class="note">▲ 历史参照：<b>2018年12月 322 万吨</b>为 MPOB 有记录以来最高（The Edge / Reuters 引 MPOB 官方数据，
当月环比 +6.92%%，连续第 7 个月累库）。2025年12月曾达 300 万吨以上（Reuters 报道，当时 BMD 期货跌至约 RM4,000/吨）。
The Edge（2026-09-24）指出：<b>马来月度库存历史上仅 5 次突破 300 万吨</b>。</div>
<div class="warn"><b>10月12日 MPOB 报告是最近的关键验证节点</b>（北京时间 12:30）。市场共识：产量 %.0f 万吨（环比 +15.7%%，
将打破 2015年8月历史纪录，连续第 4 个月环比增长）、出口 %.0f 万吨（环比 −7.3%%，连续第 2 个月下滑）、
库存 <b>%.0f 万吨</b>（环比 +19.5%%，连续第 6 个月累库，将创历史新高）。
路透调查显示部分分析师预估 300 万吨左右或更高。<b>若实绩超 337 万吨，则利空超预期兑现；若低于 300 万吨，则空头逻辑部分瓦解。</b></div>
""" % (210, 120, mpob["2026-09"]["total_stocks_wt"] or 0))
A("</div>")

# ================= 六、油脂替代 =================
A("""<div class="card">
<h2>六、油脂板块：P-D 价差极端走阔，但成因对棕榈油并非利好</h2>
<div id="c8" class="chart tall"></div>
<div class="scroll"><table style="margin-top:12px">
<tr><th>价格口径分段</th><th class="num">样本 n</th><th class="num">P-D 均值</th><th class="num">中位</th>
<th class="num">区间</th><th>说明</th></tr>""")
segs = [("1960–1998（马5%CIF NWE vs FOB NL）", "1960-01", "1998-12", "早期口径"),
        ("1999–2020/12（RBD CIF Rotterdam vs FOB NWE）", "1999-01", "2020-12", "旧口径"),
        ("2021-01–2024-10（RBD FOB Malaysia vs EXW Dutch）", "2021-01", "2024-10", "过渡口径"),
        ("2024-11–现行（5%Bulk CIF NWE vs EXW Dutch）", "2024-11", "2099-12", "<b>现行口径，唯一可比段</b>")]
for nm, lo, hi, lbl in segs:
    vs = [p["pd_spread"] for p in D["price"] if p.get("pd_spread") is not None and lo <= p["ym"] <= hi]
    if len(vs) < 6: continue
    import statistics as _st
    A("<tr%s><td><b>%s</b></td><td class='num'>%d</td><td class='num'>%+.0f</td><td class='num'>%+.0f</td>"
      "<td class='num'>[%+.0f, %+.0f]</td><td>%s</td></tr>" % (
          ' class="hl-row"' if "现行" in lbl else "", nm, len(vs), _st.mean(vs), _st.median(vs),
          min(vs), max(vs), lbl))
A("""</table></div>
<div class="warn"><b>口径陷阱（必读）</b>：世界银行 Pink Sheet 的棕榈油价格序列在 <b>2024年11月</b>发生基准切换 ——
从「RBD palm olein, FOB Malaysia Ports」改为「Palm oil Malaysia 5% bulk, CIF North West Europe」；
豆油序列也在 2021年1月从「FOB NW Europe」改为「Dutch Soyoil Crude Degummed, EXW Dutch Mills」。
两次切换都改变了运费/精炼度/交货条款的包含范围。<b>因此 P-D 价差跨期不可直接比较</b>：
全样本分位 <b>98.7%</b>（n=799）会被高估，现行口径段分位 <b>92.9%</b>（n=21）才是可比数字，
2021年以来分位 84.3%。<b>本报告采用现行口径段的 92.9% 作为主结论，并披露其余两个以供参照。</b>
（口径定义来源：世界银行 CMO 数据文件 Description 页，已直接读取核实。）</div>
""")

A("""<h3>6.1 价差走阔的成因拆解：豆油单边暴涨，棕榈油原地踏步</h3>
<div class="scroll"><table>
<tr><th>指标</th><th class="num">2024-12</th><th class="num">%s</th><th class="num">变化</th><th class="num">变化%%</th><th>驱动</th></tr>
<tr><td>棕榈油（IMF, $/t）</td><td class="num">1,128</td><td class="num">%.0f</td><td class="num dn">%+.0f</td>
<td class="num dn">%+.0f%%</td><td>马来累库 + 出口疲软压制</td></tr>
<tr><td>豆油（IMF, $/t）</td><td class="num">903</td><td class="num">%.0f</td><td class="num up">%+.0f</td>
<td class="num up">%+.0f%%</td><td>美国 RVO 扩容 + 45Z 细则</td></tr>
<tr class="hl-row"><td><b>P-D 价差</b></td><td class="num"><b>−225</b></td><td class="num"><b>%+.0f</b></td>
<td class="num up"><b>%+.0f</b></td><td class="num">—</td><td><b>几乎全部来自豆油上涨</b></td></tr>
</table></div>
<div class="contra"><b>为什么这不是棕榈油的利好，而是一个需要警惕的信号</b>
<ul>
<li>豆油上涨的驱动是<b>美国 45Z 清洁燃料生产税收抵免</b>（2026-02-04 财政部/IRS 拟议细则）：
①自 2026-01-01 起<b>只有美国/墨西哥/加拿大种植的原料</b>制成的燃料才有资格获退税 —— <b>棕榈油被明确排除</b>；
②取消豆油的 ILUC（间接土地利用变化）“碳惩罚”，使豆油 CI 评分大幅下修；③强制使用 45ZCF-GREET 模型锁定核算标准。</li>
<li>叠加 EPA 的 RVO 扩容：2026年 BBD RVO 拟设 71.2 亿 RINs（约 56.1 亿加仑），2027年 58.6 亿加仑，
远高于上届政府为 2025年设定的 33.5 亿加仑。USDA ERS 预计 2026/27 美国豆油生柴用量达 <b>178 亿磅</b>（+36 亿磅）。</li>
<li>进口废油脂（UCO）因失去约 1 美元/加仑退税而被挤出（实际采购成本变相增加约 300 美元/吨），
若 60%% 由本土豆油替代，额外创造约 200 万吨/年豆油需求。</li>
<li><b>对棕榈油的真实含义</b>：全球最大的一块新增生柴需求（美国）<b>结构性地绕开了棕榈油</b>。
棕榈油能获得的只是「豆油太贵 → 食用领域替代」这一间接效应，而这一效应的强度取决于印度/中国/巴基斯坦的价格敏感度，
并非美国政策红利。<b>把 P-D 价差走阔直接读作棕榈油利多是错误的</b>。</li>
</ul></div>
""" % (lat["ym"], lat["palm"], lat["palm"] - 1128, 100 * (lat["palm"] - 1128) / 1128,
       lat["soy"], lat["soy"] - 903, 100 * (lat["soy"] - 903) / 903,
       lat["pd_spread"] or 0, (lat["pd_spread"] or 0) + 225))

A("""<h3>6.2 油脂板块横向对比（MY2026）</h3>
<div class="grid2"><div><div id="c9" class="chart mid"></div></div>
<div><div class="scroll"><table>
<tr><th>油脂</th><th class="num">产量<br>(千吨)</th><th class="num">产量份额</th><th class="num">期末库存</th>
<th class="num">STU%</th><th class="num">MY2015<br>STU%</th></tr>""")
tot_oil = sum(next((r["prod"] for r in rows if r["my"] == "2026"), 0) for rows in D["oils"].values())
NM = {"palm": "棕榈油", "soyoil": "豆油", "rapeseed": "菜油", "sunflower": "葵花油",
      "pko": "棕榈仁油", "coconut": "椰子油"}
for nm in ["palm", "soyoil", "rapeseed", "sunflower", "pko", "coconut"]:
    rows = D["oils"][nm]
    r = next((x for x in rows if x["my"] == "2026"), None)
    r15 = next((x for x in rows if x["my"] == "2015"), None)
    if not r: continue
    A("<tr%s><td><b>%s</b></td><td class='num'>%.0f</td><td class='num'>%.1f%%</td><td class='num'>%.0f</td>"
      "<td class='num'>%.1f</td><td class='num'>%.1f</td></tr>" % (
          ' class="hl-row"' if nm == "palm" else "", NM[nm], r["prod"], 100 * r["prod"] / tot_oil,
          r["end"], r["stu"] or 0, (r15["stu"] or 0) if r15 else 0))
A("""</table></div>
<div class="note" style="margin-top:10px">▲ <b>棕榈油 STU（%.1f%%）是六大油脂中最高的</b>，远高于豆油（%.1f%%）与菜油（%.1f%%）。
这在直观上与“棕榈油紧张”的叙事相反。解释有二：
①棕榈油是<b>多年生作物、全年连续采收</b>，产业链各环节的周转库存天然高于一年生的豆油/菜油；
②豆油/菜油的库存统计口径不含在途与压榨厂原料库存，而棕榈油库存含种植园与压榨厂在库。<br>
<b>⇒ 跨品种比较 STU 绝对值无意义</b>，应比较各自的<b>历史分位</b>与<b>边际变化方向</b>。
棕榈油份额从 2000 年 30.5%% 升至 2020 年 37.9%% 后，2026 年回落至 35.1%%，豆油同期回升至 32.5%% ——
份额此消彼长的拐点恰与马来单产见顶（MY%s）吻合。</div></div></div>
""" % (W["2026"]["stu"], next(x for x in D["oils"]["soyoil"] if x["my"] == "2026")["stu"],
       next(x for x in D["oils"]["rapeseed"] if x["my"] == "2026")["stu"], my_yld_peak[0]))

A("""<h3>6.3 价格定位与期货曲线</h3>
<div class="scroll"><table>
<tr><th>指标</th><th class="num">数值</th><th>分位 / 说明</th></tr>
<tr><td>棕榈油 IMF 月均（%s）</td><td class="num"><b>%.0f $/t</b></td>
<td>1980以来 <b>%.1f%%</b>（n=559，区间 %.0f–%.0f，均值 %.0f）｜近10年 %.1f%%｜近5年 %.1f%%</td></tr>
<tr><td>历史最高 / 最低</td><td class="num">1,653 / 185 $/t</td><td>最高 2022-03（俄乌冲突 + 印尼出口禁令）；最低 2001-02</td></tr>
<tr><td>豆油 IMF 月均</td><td class="num">%.0f $/t</td><td>1980以来分位 <b>98.8%%</b> —— <b>豆油比棕榈油更接近历史极值</b></td></tr>
<tr><td>USD/MYR</td><td class="num">4.082</td><td>2026-10-02；林吉特口径棕榈油约 4,517 MYR/t</td></tr>
</table></div>
<h4>BMD FCPO 期货曲线（2026-10-07 收盘，MYR/吨）</h4>
<div class="scroll"><table>
<tr><th>合约</th><th class="num">收盘</th><th class="num">涨跌</th><th class="num">成交量</th><th class="num">持仓量</th></tr>
<tr><td>Oct 2026（现货月）</td><td class="num">4,310</td><td class="num dn">−30</td><td class="num" rowspan="6">70,612 手<br><span class="note">（前日 92,828）</span></td>
<td class="num" rowspan="6">328,944 手<br><span class="note">（前日 329,375）</span></td></tr>
<tr><td>Nov 2026</td><td class="num">4,413</td><td class="num dn">−44</td></tr>
<tr class="hl-row"><td><b>Dec 2026（第三月/基准）</b></td><td class="num"><b>4,524</b></td><td class="num dn">−36</td></tr>
<tr><td>Jan 2027</td><td class="num">4,636</td><td class="num dn">−27</td></tr>
<tr><td>Feb 2027</td><td class="num">4,739</td><td class="num dn">−19</td></tr>
<tr><td>Mar 2027</td><td class="num">4,834</td><td class="num dn">−9</td></tr>
</table></div>
<div class="keypoint"><b>曲线结构解读（这是最重要的价格信号）</b>
<ul>
<li><b>完全 Contango</b>：Oct-26 RM4,310 → Mar-27 RM4,834，远月升水 <b>+524 MYR（+12.2%%）</b>；
Dec-26 → Mar-27 升水 310 MYR（+6.9%%）。近月贴水直接反映马来当前库存压力。</li>
<li><b>跌幅随合约月份递减</b>（−30 / −44 / −36 / −27 / −19 / −9）：当日利空（豆油走弱 + 库存担忧）主要打击近月，
远月相对抗跌 → <b>市场已在定价 2027 年的供给收紧</b>（厄尔尼诺 + B50 逻辑已部分进入曲线）。</li>
<li>现货 CPO（10月南方）RM4,350，较 Oct 合约小幅升水 40 MYR。</li>
<li>成交量从 92,828 降至 70,612 手、持仓量小幅下降 —— <b>缩量下行</b>，属获利了结与观望，非恐慌性抛售。</li>
<li>MPOC 官方预期：CPO 2026 剩余时间维持在 1,154 $/t 以上、9月维持 RM4,600/吨以上。
<b>当前 IMF 月均 1,106 $/t 已低于 MPOC 的 1,154 门槛</b>，该预测面临下修压力。</li>
</ul></div>
<div class="note">▲ 期货数据来源：Bernama（2026-10-07 收盘报道，引 Iceberg X Sdn Bhd 交易员 David Ng 评论：
支撑 RM4,500 / 阻力 RM4,650 —— 注意其支撑位已在当日收盘价上方，显示技术面亦偏弱）。</div>
</div>""" % (lat["ym"], lat["palm"], SUP["price"]["palm_pctile_all"], SUP["price"]["palm_min"],
            SUP["price"]["palm_max"], SUP["price"]["palm_mean_all"],
            SUP["price"]["palm_pctile_10y"], SUP["price"]["palm_pctile_5y"], lat["soy"]))

# ================= 七、ENSO =================
A("""<div class="card">
<h2>七、厄尔尼诺：产业共识很强，但统计证据不支持</h2>
<div class="info"><b>当前 ENSO 状态（CPC ONI，已核实）</b><br>
ONI 序列：2025-11 = −0.61（拉尼娜）→ 2026-01 = −0.39 → 2026-03 = +0.11 → 2026-05 = +0.95 →
2026-07（JJA）= +1.80 → <b>2026-08（JAS）= +2.16</b>。<br>
<b>历史强厄尔尼诺峰值排序</b>：2015-12 NDJ = +2.59 ＞ 1997-12 NDJ = +2.37 ＞ <b>2026-08 JAS = +2.16</b> ＞
1983-01 = +2.14 ＞ 2023-12 = +1.99 ＞ 1972-11 = +1.84 ＞ 1965-11 = +1.82 ＞ 1958-01 = +1.69。<br>
⇒ 本轮已达<b>历史第 3 强</b>，且<b>异常早期</b>：历史强 EN 峰值几乎都落在 11月–次年1月（NDJ/DJF），
本轮在 <b>8月（JAS）</b>即达 +2.16，此后若按常态继续增强，峰值可能超过 2015 年的 +2.59。
马来西亚气象局（2026-08-18）称 10–12月达到"very strong / Super El Niño"级别的概率已升至 <b>90% 以上</b>。</div>
<div id="c10" class="chart tall"></div>
""")

A("""<h3>7.1 统计检验：去趋势 + 多滞后扫描 + 多重比较校正</h3>
<div class="note" style="margin-bottom:10px">方法：①对单产序列做 OLS 去趋势（线性 vs 二次，按 R² 改善自动选择）；
②残差与 ONI 的市场年均值做多滞后（0–18 月）Pearson 相关；③对全部 3 地区 × 19 滞后 = 57 项检验做 Bonferroni 与 Benjamini–Hochberg FDR 校正。
样本 = MY1990–MY2025（n=36，剔本轮）。</div>
<div class="scroll"><table>
<tr><th>地区</th><th class="num">去趋势阶数</th><th class="num">趋势 R²</th><th class="num">残差 SD<br>(t/ha)</th>
<th class="num">最强滞后</th><th class="num">r</th><th class="num">t 值</th><th class="num">原始 p</th>
<th class="num">Bonferroni p</th><th>结论</th></tr>""")
for nm in ["全球", "马来", "印尼"]:
    R = ENSO[nm]
    best = min(R["rows"], key=lambda r: abs(r["t"])) if R["best_t"] else None
    br = max(R["rows"], key=lambda r: abs(r["t"] or 0))
    A("<tr><td><b>%s</b></td><td class='num'>%d 次</td><td class='num'>%.3f</td><td class='num'>%.4f</td>"
      "<td class='num'>%d 月</td><td class='num'>%+.3f</td><td class='num'>%+.2f</td>"
      "<td class='num'>%.4f</td><td class='num'><b>%.4f</b></td><td>%s</td></tr>" % (
          nm, R["detrend_deg"], R["detrend_r2"], R["resid_sd"], br["lag"], br["r"], br["t"],
          br.get("p", 0), br.get("p_bonf", 1),
          '<span class="hl">不显著</span>（校正后）' if br.get("p_bonf", 1) > 0.05 else "显著"))
A("""</table></div>
<div class="contra"><b>统计结论（诚实表述）</b>
<ul>
<li>57 项检验中最小原始 p 值 = <b>0.0174</b>（马来 lag10，r=+0.394，t=+2.50）——
<b>但方向是正的</b>（ONI 越高、单产残差越高），与“厄尔尼诺减产”的共识<b>相反</b>，这本身就是该相关性是伪关系的强烈暗示。</li>
<li>Bonferroni 校正后 p = <b>0.9922</b>；Benjamini–Hochberg FDR(5%) <b>拒绝 0 / 57 项</b>原假设。
⇒ <b>在本数据与本口径下，无法拒绝「ONI 与去趋势单产残差无线性关系」。</b></li>
<li><b>事件研究同样不支持</b>：强 EN 年份（峰值≥1.5）单产低于趋势的次数 —— 全球 2/5、马来 2/5、印尼 4/5。
n=4~5 的样本不具备推断力。</li>
</ul></div>
<div class="warn"><b>为什么统计检验失败，但产业共识依然强烈？三个原因，都不应被忽略</b>
<ul>
<li><b>功效不足</b>：n=36 个市场年，其中强 EN 事件仅 4–5 次。要在 α=0.05、功效 0.8 下检出 r=0.35 的效应，
需要 n≈62。<b>样本天然稀缺，不是效应不存在。</b></li>
<li><b>数据是事后修订值</b>：USDA PSD 单产是最后一次批量修订的结果（马来 MY2019–2020 停在 vintage 2024-10、
MY2021–2024 停在 2026-04），含平滑，会系统性削弱真实波动幅度。用 MPOB 原始月度单产重做可能得到不同结果，
<b>但本项目尚无 MPOB 长序列月度数据</b>。</li>
<li><b>市场年口径掩盖了季节内时点</b>：MY = 10月–9月的年均 ONI 把“峰值出现在 MY 之前还是之中”抹平了。
产业界讲的“滞后 9–12 月”是<b>从干旱发生月算起</b>，与本报告“从市场年起点算起”的滞后定义不同。
这是口径差异，不是数据矛盾。</li>
</ul></div>
""")

A("""<h3>7.2 产业共识与机构预测（作为情景参照，非统计结论）</h3>
<div class="scroll"><table>
<tr><th style="width:180px">来源</th><th style="width:110px">时点</th><th>预测内容与滞后机制表述</th></tr>
<tr><td>MPOC（马来棕榈油委员会）<br>CEO Belvinder Sron</td><td>2026-08-25</td>
<td>厄尔尼诺影响<b>滞后 9–12 个月</b>显现。参照：上一次 Super El Niño（2015）导致马来次年产量<b>下降 13%，即 260 万吨</b>。
但指出本轮干旱出现时间晚于 2015 年，<b>9–11月降雨是决定 2027 年影响程度的关键</b>；12月季风可能缓解冲击。
同时强调近端干旱反而<b>有利于采收与 FFB 运输</b>（田间通行改善、减少洪涝中断）。
风险来自“持续 3 个月以上的长期干旱”。</td></tr>
<tr><td>彭博 7 位分析师调查</td><td>2026-09</td>
<td>2027 年印尼产量降至 <b>4,900 万吨</b>、马来降至 <b>1,950 万吨</b>，两国合计同比 <b>−3%</b>。</td></tr>
<tr><td>GAPKI（印尼棕榈油协会）</td><td>2026-09</td>
<td>将 2027 年产量降幅预期<b>从 −5% 修正收窄至 −3%</b> —— 承认减产但烈度低于最悲观预期。</td></tr>
<tr><td>USDA FAS GAIN 马来报告</td><td>2026-07-01</td>
<td>MY2026/27 产量从 2,000 万吨<b>下调至 1,970 万吨（−30 万吨）</b>，理由为 EN 干旱限制 FFB 单产；
影响“主要反映在市场年第 3–4 季度”（即 2027年4–9月），因油棕对水分胁迫的反应存在滞后。
<b>⇒ USDA 已部分计入 EN，但仅 −1.5%。</b></td></tr>
<tr><td>广发期货（王泽辉）</td><td>2026-09</td>
<td>“棕榈油是对厄尔尼诺反应最敏感的品种”；历史强 EN 周期东南亚单产普遍下滑 <b>10–25%</b>，滞后 <b>9–12 个月</b>。
指出<b>印尼库存处近 5 年低位</b>叠加 B50，易形成趋势性缺口。</td></tr>
<tr><td>中金公司研究部</td><td>2026</td>
<td>1970 年以来四次强 EN 后马来油棕果单产降幅分别为 <b>12%、24%、14%、15%</b>；测算滞后约 <b>10 个月</b>。
机制：油棕<b>花性别分化期</b>对水分敏感，干旱促使雄花增多、雌花减少，降低结果率。
1991–92 年长达 14 个月的强事件导致单产下降 15%，创十年低位。</td></tr>
<tr><td>印尼气象局 / EcoPalm</td><td>2026-09</td>
<td>雨季通常 10 月开始，今年恐推迟至 11–12 月且周期缩短。加里曼丹（Kalimantan）火点数量升至<b>十年最高</b>，
林火雾霾影响采收、施肥与运输物流，预计承受明年减产最大份额。</td></tr>
<tr class="warn-row"><td><b>本报告统计检验</b></td><td>2026-10-07</td>
<td><b>未能证实</b>滞后关系（57 项检验，BH-FDR 拒绝 0 项）。<b>但需强调：这是“证据不足”，不是“证据反驳”。</b>
在 n=36、事件仅 4–5 次的样本下，检验功效本身就很低。</td></tr>
</table></div>
<div class="keypoint"><b>如何正确使用这些相互矛盾的信息</b><br>
① <b>不要把 EN 减产当作已确立的统计规律</b>来做仓位判断 —— 本报告的检验不支持。<br>
② <b>但也不要因为统计不显著就否定它</b> —— 生物机制（花性别分化对水分敏感）是明确的，
且 MPOC 用 2015 年实例给出了可核实的量级（−13%、−260 万吨）。<br>
③ 正确做法：<b>把 EN 作为情景变量而非基线假设</b>。第八节的情景阶梯正是这样处理的 ——
基线用 USDA 数字，EN 冲击放在 −3% / −5% / −9.8% 三档情景里，明确标注每档的来源与概率无法量化。<br>
④ <b>最关键的跟踪指标是 9–11 月东南亚降雨</b>（MPOC 明确指出这是决定 2027 影响程度的窗口），
以及 MPOB 月度单产（yield）与 OER（出油率）—— 这是比 ONI 更直接的先行指标。</div>
</div>""")

# ================= 八、库存分层与情景 =================
A("""<div class="card">
<h2>八、库存分层与情景推演：硬缓冲有多厚？</h2>
<div class="info"><b>为什么不能直接用“期末库存 ÷ 消费”衡量缓冲能力</b><br>
库存的可用性取决于<b>谁有权决定释放</b>，以及<b>释放是否会减少该国自己的必需消费</b>。
把印尼被 B50 强制掺混锁定的库存与马来西亚可供出口的商业库存加总，会严重高估真实缓冲。
本节按释放决策权分层（沿用本项目糖研究的分层方法论）。</div>
<h3>8.1 MY2026 全球期末库存 %.2f Mt 的分层</h3>
<div class="scroll"><table>
<tr><th>层级</th><th>国家</th><th class="num">期末库存<br>(千吨)</th><th class="num">份额</th>
<th class="num">净贸易<br>(出口−进口)</th><th class="num">工业/国内<br>消费</th><th>可用性判断</th></tr>""" % (w26["end"] / 1000))
tier_txt = {1: ("① 净出口国持有", "<b>唯一可立即动用</b>。但印尼部分受 B50 强制掺混锁定，实际可用量低于名义值。"),
            2: ("② 平衡型", "自产自用，部分可动，对全球市场影响有限。"),
            3: ("③ 净进口国持有", "只能通过<b>减少进口</b>间接影响世界市场，属“需求侧缓冲”而非供给侧。")}
tiers = {}
for l in SCEN["stock_layers"]:
    nt = l["net_trade"]
    t = 1 if nt > 500 else (2 if abs(nt) <= 500 else 3)
    tiers.setdefault(t, []).append(l)
for t in [1, 2, 3]:
    ls = tiers.get(t, [])
    for i, l in enumerate(ls):
        nm, avail = tier_txt[t]
        A("<tr%s><td>%s</td><td><b>%s</b> <span class='sig'>(%s)</span></td><td class='num'>%.0f</td>"
          "<td class='num'>%.1f%%</td><td class='num %s'>%+.0f</td><td class='num'>%.1f%%</td>"
          "<td style='white-space:normal'>%s</td></tr>" % (
              ' class="hl-row"' if t == 1 else "", nm if i == 0 else "", l["name"], l["cc"], l["end"],
              l["share"], "up" if l["net_trade"] > 0 else "dn", l["net_trade"], l["bio_lock_pct"],
              avail if i == 0 else ""))
rest = w26["end"] - sum(l["end"] for l in SCEN["stock_layers"])
A("<tr><td>—</td><td>其余国家合计</td><td class='num'>%.0f</td><td class='num'>%.1f%%</td>"
  "<td class='num'>—</td><td class='num'>—</td><td style='white-space:normal'>多为小型净进口国</td></tr>" % (
      rest, 100 * rest / w26["end"]))
t1 = sum(l["end"] for l in tiers.get(1, []))
A("""</table></div>
<div class="kpis" style="margin-top:14px">
<div class="kpi"><div class="num blue">%.0f kt</div><div class="lab">① 净出口国持有层<br>= 全球库存 %.1f%%</div></div>
<div class="kpi"><div class="num warn">%.1f 天</div><div class="lab">折算全球消费天数<br>（全球期末库存合计 %.1f 个月）</div></div>
<div class="kpi"><div class="num">%.1f%%</div><div class="lab">占全球出口量<br>（出口 %.1f Mt）</div></div>
<div class="kpi"><div class="num dn">%.0f kt</div><div class="lab">印尼工业消费（B50 锁定池）<br>约 85%% 为生柴 = %.0f kt</div></div>
</div>
<div class="note">▲ 历史对照：①层占全球库存的份额 MY2015–2026 稳定在 <b>36–57%%</b>（MY2026 = %.1f%%），
说明<b>“净出口国持有的库存只占全球一半左右”是结构性的，不是今年特别紧</b>。
真正的边际变化在于：这一层的绝对量 MY2021 见顶 %.0f kt 后已连续 5 年下降至 %.0f kt（−%.0f%%），
而同期全球消费增长 %.0f%%。</div>
""" % (t1, 100 * t1 / w26["end"], t1 / w26["dom_cons"] * 365, w26["end"] / (w26["dom_cons"] / 12),
       100 * t1 / w26["exp"], w26["exp"] / 1000, id26["industrial"], id26["industrial"] * 0.85,
       44.3, 9627, 6411, 100 * (9627 - 6411) / 9627, 100 * (w26["dom_cons"] / W["2021"]["dom_cons"] - 1)))

A("""<h3>8.2 情景阶梯：2027 年产量冲击 → STU → 历史分位</h3>
<div class="note" style="margin-bottom:9px">推演方法（沿用本项目糖研究纪律）：
<b>只改分子</b> —— 期末库存 = 基线库存 + 产量偏差 −（消费增量）；<b>不重复计入基线盈余</b>。
消费按 MY2025→MY2026 的实际增速（+%.2f%%）外推一年。分位分布 = MY1989–2025 已实现年（n=37）。
单位：产量/消费/库存为千吨。</div>
<div id="c11" class="chart mid"></div>
<div class="scroll"><table style="margin-top:12px">
<tr><th>情景</th><th class="num">产量变化</th><th class="num">产量<br>(Mt)</th><th class="num">消费<br>(Mt)</th>
<th class="num">期末库存<br>(Mt)</th><th class="num">STU%%</th><th class="num">历史分位</th><th>来源与可信度</th></tr>""" % (
    100 * (w26["dom_cons"] - w25["dom_cons"]) / w25["dom_cons"]))
src_note = {
    "USDA MY2026 基线（无新增减产）": "USDA PSD vintage 2026-09。<b>注意：这不是“无冲击”情景</b> —— 它已含消费 +%.2f%% 的外推，"
                                      "因此 STU 从 %.1f%% 降至 %.1f%%。仅表示“产量不再额外下降”。",
    "彭博调查共识（两国 −3%）": "彭博 7 位分析师调查（2026-09）+ GAPKI 修正后指引（−5%→−3%）。<b>可信度最高的外部共识。</b>",
    "GAPKI 悲观情形（−5%）": "GAPKI 修正前的原指引。已被其自身下修至 −3%，属保守情景。",
    "历史强EN中位（马来−2.0/印尼−6.9）": "本报告事件研究的中位数（n=4）。<b>统计不显著，仅作参照。</b>",
    "MY2015 类比（全球单产 −9.8%）": "上一轮 Super El Niño（ONI +2.59）的实际全球单产偏差。马来当年 −15.8%（MPOC 口径 −13%、−260 万吨）。",
    "极端：马来 −15.8%（2015实际）全球折算": "把马来 2015 年的单产跌幅直接套到全球。<b>明显过度，仅作压力测试上限。</b>",
}
for s in SCEN["scenarios"]:
    nt = src_note.get(s["name"], "")
    if "基线" in s["name"]:
        nt = nt % (100 * (w26["dom_cons"] - w25["dom_cons"]) / w25["dom_cons"], w26["stu"], s["stu"])
    cls = ' class="hl-row"' if "彭博" in s["name"] else (' class="warn-row"' if "极端" in s["name"] else "")
    A("<tr%s><td><b>%s</b></td><td class='num %s'>%+.1f%%</td><td class='num'>%.1f</td><td class='num'>%.1f</td>"
      "<td class='num'>%.2f</td><td class='num'>%.1f</td><td class='num'><b>%.1f%%</b></td>"
      "<td style='white-space:normal'>%s</td></tr>" % (
          cls, s["name"], "dn" if s["dev_pct"] < 0 else "", s["dev_pct"], s["prod"] / 1000,
          s["cons"] / 1000, s["end"] / 1000, s["stu"], s["pctile"], nt))
A("""</table></div>
<div class="contra"><b>情景推演的三个致命局限（必须与结论一起读）</b>
<ul>
<li><b>极端情景在物理上不可行</b>：−15.8%% 情景给出 STU = <b>−0.5%%</b>，即期末库存为负。
这说明该情景<b>必然触发价格配给</b>（需求被高价强制压缩），不能用“库存不变、消费不变”的线性外推来描述。
真实世界里 −9.8%% 的产量冲击会同时引发：①进口国抢购囤货 ②P-D 价差进一步走阔触发替代 ③印尼可能放松 B50 兑现率或下调出口税。
<b>情景表给出的是“若无任何调节机制的算术结果”，不是预测。</b></li>
<li><b>消费外推可能过于机械</b>：按 +%.2f%% 外推一年意味着 MY2027 消费达 %.1f Mt。
但 B50 是<b>一次性台阶式跳升</b>（+300 万吨），不会每年重复；食用消费增速也在放缓（2020→2026 食用增量仅 %.0f kt，
远小于 2010→2020 的 %.0f kt）。<b>消费外推偏高会使所有情景的 STU 系统性偏低。</b></li>
<li><b>基线本身含 vintage 风险</b>：USDA MY2026 的马来库存已被 MPOB 实绩证伪（低估 34–90 万吨）。
若按 MPOB 口径上调马来期末库存，全球基线 STU 会<b>上移</b>，所有情景分位相应上移 —— 即“看起来没那么紧”。</li>
</ul></div>
""" % (100 * (w26["dom_cons"] - w25["dom_cons"]) / w25["dom_cons"],
       w26["dom_cons"] * (1 + (w26["dom_cons"] - w25["dom_cons"]) / w25["dom_cons"]) / 1000,
       w26["food"] - W["2020"]["food"], W["2020"]["food"] - W["2010"]["food"]))

A("""<h3>8.3 三层非库存缓冲（否则会高估紧张程度）</h3>
<div class="scroll"><table>
<tr><th style="width:150px">缓冲类型</th><th style="width:200px">量级估算</th><th>性质与触发条件</th></tr>
<tr><td><b>① 供给侧弹性</b><br>（产量调节）</td><td class="num">马来 B15 已锁定<br>印尼 B50 兑现率可调</td>
<td>棕榈油<b>没有类似巴西糖醇比的快速切换开关</b> —— 油棕是多年生作物，采收节奏由生物周期决定，
短期只能通过<b>减少采收频次/推迟采收</b>来压低产量（这会降低 OER 与品质）。
<b>反向弹性存在</b：若价格暴跌，种植园可减少施肥、延缓翻种，但这是损害长期产能的自残式调节。
真正可调的是<b>印尼 B50 的兑现率</b> —— 政府可按国内库存与价格灵活调整（经济学家 Achmad Nur Hidayat 已公开建议此机制）。</td></tr>
<tr><td><b>② 需求侧配给</b><br>（价格触发）</td><td class="num">前 6 大进口国合计<br>%.0f kt（占出口 %.1f%%）</td>
<td>P-D 价差 %.0f $/t（现行口径段 92.9 分位）→ <b>替代空间已完全打开</b>。
印度 2026-09 已将棕榈油/豆油进口关税减半、葵花油归零，进口窗口放宽。
巴基斯坦（工业仅 2%%）、孟加拉（3%%）为纯食用需求，价格敏感度最高，是最先切换的买家。
<b>这一层不是储备，它本身就是价格机制 —— 需要足够高的相对价格才触发。</b></td></tr>
<tr><td><b>③ 净进口国在库</b><br>（方向信号）</td><td class="num">③层合计 %.0f kt<br>= 全球消费 %.2f 个月</td>
<td>印度 1,968 + 中国 409 + 欧盟 338 + 巴基斯坦 281 + 孟加拉 125 + 美国 136 kt。
<b>方向比水平更重要</b>：印度库存 MY2022 峰值 2,419 kt → MY2026 1,968 kt（−%.0f%%）；
中国 MY2020 的 1,149 kt → MY2026 409 kt（−%.0f%%）；欧盟 MY2020 568 → 338 kt（−%.0f%%）。
<b>三大进口方库存同步下降 = 未来进口需求还会增加</b>，这是收紧信号而非缓冲。</td></tr>
</table></div>
<div class="keypoint"><b>综合缓冲评估</b><br>
<b>硬缓冲</b>（可立即动用）：净出口国持有 %.0f kt，但扣除印尼 B50 锁定池后，真正可自由出口调节的部分显著更小 ——
印尼期末库存 %.0f kt vs 其被锁定的工业消费 %.0f kt，<b>库存量级远小于锁定量级</b>，说明印尼的调节余量主要靠<b>削减出口</b>而非释放库存。<br>
<b>软缓冲</b>（需价格触发）：需求侧替代空间完全打开（P-D 价差 92.9 分位），覆盖前 6 大进口国 %.0f kt 进口量。<br>
<b>覆盖率</b>：全球期末库存 %.2f Mt = 消费 %.1f 个月 = %.0f 天。若 2027 年产量按彭博共识 −3%%（−%.1f Mt），
<b>仅此一项缺口就超过全球库存降幅的全部空间</b> —— 这是“远端偏紧”判断的算术基础。</div>
""" % (8700 + 3900 + 3700 + 3100 + 1725 + 1700, 100 * (8700 + 3900 + 3700 + 3100 + 1725 + 1700) / w26["exp"],
       lat["pd_spread"] or 0, sum(l["end"] for l in tiers.get(3, [])),
       sum(l["end"] for l in tiers.get(3, [])) / (w26["dom_cons"] / 12),
       100 * (1 - 1968 / 2419), 100 * (1 - 409 / 1149), 100 * (1 - 338 / 568),
       t1, id26["end"], id26["industrial"], 8700 + 3900 + 3700 + 3100 + 1725 + 1700,
       w26["end"] / 1000, w26["end"] / (w26["dom_cons"] / 12), w26["end"] / w26["dom_cons"] * 365,
       w26["prod"] * 0.03 / 1000))
A("</div>")

# ================= 九、综合判断 =================
A("""<div class="card">
<h2>九、综合判断与置信度</h2>
<div class="scroll"><table>
<tr><th style="width:200px">判断</th><th style="width:90px">方向</th><th style="width:80px">置信度</th><th>依据与反例</th></tr>
<tr><td><b>近端（0–3月）马来库存将创历史新高</b></td><td><span class="tag bear">利空</span></td><td><b>高</b></td>
<td>依据：MPOB 已连续 5 个月累库（3月 227 → 8月 282 万吨），9月产量预估创纪录 210 万吨、出口连续两月下滑。<br>
反例/风险：<b>10-12 MPOB 正式数据尚未公布</b>，337 万吨为路透调查预估；若实绩低于 300 万吨则利空不及预期。
9–11月降雨若明显偏多，10月起产量季节性回落可能快于预期。</td></tr>
<tr><td><b>USDA MY2025 马来库存数字已被证伪</b></td><td><span class="tag neu">口径</span></td><td><b>高</b></td>
<td>依据：PSD 给 247.5 万吨（vintage 2026-09），MPOB 8月实绩已达 282 万吨。差距 −34.5 万吨（−12%%），
且方向明确。<b>⇒ 使用 PSD 做马来库存分析会系统性低估。</b></td></tr>
<tr><td><b>B50 将持续削减印尼可出口量</b></td><td><span class="tag bull">利多</span></td><td><b>中高</b></td>
<td>依据：政策已于 2026-07-01 落地（可核实）；GAPKI 与印尼能矿部双口径给出 +300–350 万吨年增内需；
出口税 12.5%% 提供稳定融资。<br>
反例/风险：①<b>政策摇摆有先例</b> —— 2026年1月曾宣布放弃 B50 后反转；②兑现率依赖 BPDPKS 补贴资金，
若 CPO 价格下跌则税收减少、补贴能力下降（<b>负反馈</b>，与高价时的正反馈相反）；
③矿业与重型设备行业的技术阻力仍在；④2026年初阶段增量仅 150–170 万吨，全年爬坡。</td></tr>
<tr><td><b>供给增长引擎已结构性减速</b></td><td><span class="tag bull">利多</span></td><td><b>高</b></td>
<td>依据：<b>USDA PSD 实绩序列，可核实</b>。全球单产 CAGR 2020–26 = %.2f%%/年（1990–2000 为 +1.21%%）；
面积 CAGR 从 +6.93%% 降至 +1.79%%；马来单产二次趋势 R²=0.650，峰值 MY%s 后回落。<br>
反例/风险：GAPKI 称印尼<b>潜在产能可达 6,000 万吨/年</b>（vs 当前约 4,700 万吨），
瓶颈是 PSR 翻种进度而非土地 —— 若 PSR 加速，中期供给弹性会恢复。</td></tr>
<tr><td><b>P-D 价差走阔会触发替代需求回流棕榈油</b></td><td><span class="tag bull">利多</span></td><td><b>中</b></td>
<td>依据：价差 %.0f $/t（现行口径段 92.9 分位），印度已下调关税、排灯节备货期临近。<br>
反例/风险：①路透引新德里交易商称<b>价差已在收窄</b>，印度买家正转向豆油/葵花油（与本判断相反的直接证据）；
②MPOB 8月出口环比 −7.5%%、ITS 9月 −17.1%%，<b>替代需求尚未在出口数据中兑现</b>；
③价差走阔主因是豆油暴涨（+76%%）而非棕榈油下跌（−2%%），若豆油回落则替代逻辑自动消失。</td></tr>
<tr class="warn-row"><td><b>厄尔尼诺将在 2027 年造成显著减产</b></td><td><span class="tag neu">不确定</span></td><td><b>低</b></td>
<td>依据（产业侧）：ONI +2.16 为历史第 3 强；MPOC/中金/广发一致给出“滞后 9–12 月、单产降 10–25%%”；
彭博调查 −3%%；2015 年实例 −13%%（−260 万吨）。<br>
<b>反例（本报告统计检验）</b>：57 项滞后检验，Bonferroni 校正后最小 p=0.99，BH-FDR 拒绝 0 项；
强 EN 年单产低于趋势仅 2/5（全球）、2/5（马来）、4/5（印尼）。<br>
<b>⇒ 置信度评为”低“，不是因为没有证据，而是因为正反证据都存在且无法调和。</b>
这是本报告与市场共识最大的分歧点，已完整披露。</td></tr>
<tr><td><b>全球 STU 将继续下行</b></td><td><span class="tag bull">利多</span></td><td><b>中</b></td>
<td>依据：USDA 路径 MY2021 的 %.1f%% → MY2026 的 %.1f%%，连续 5 年下行；情景推演各档均继续下行。<br>
反例：①窗口敏感 —— 1989–2025 分位 %.1f%%（偏松）vs 2010–2025 分位 %.1f%%（偏紧），结论方向相反；
②<b>马来库存被 USDA 低估 34–90 万吨</b>，按 MPOB 口径修正后全球 STU 会上移；
③消费外推（+%.2f%%/年）可能过高，B50 是一次性台阶而非持续增速。</td></tr>
</table></div>
""" % (yld_cagr_2026, my_yld_peak[0], lat["pd_spread"] or 0, W["2021"]["stu"], w26["stu"],
       w26.get("stu_pctile_1989-2025", 0), w26.get("stu_pctile_2010-2025", 0),
       100 * (w26["dom_cons"] - w25["dom_cons"]) / w25["dom_cons"]))

A("""<div class="keypoint"><b>总体判断（四段式）</b>
<ul>
<li><b>[前提校验]</b> “棕榈油基本面紧张”这一常见表述<b>在近端不成立</b>：马来库存正走向历史峰值，全球仍有 %+.2f Mt 盈余，
棕榈油 STU（%.1f%%）在六大油脂中最高。紧张叙事成立的范围是<b>2027 年及以后的远端</b>，且依赖两个尚未兑现的假设
（B50 足额兑现 + EN 造成减产）。</li>
<li><b>[关键数据]</b> 三条最硬的证据：①全球单产 CAGR 2020–26 转负（−%.2f%%/年，USDA 实绩）；
②印尼工业消费 11 年增 %.0f%%（3,700→15,850 kt，USDA 实绩）；③P-D 价差 %.0f $/t，现行口径段 92.9 分位（IMF 实绩）。
三条均为可核实的已发生事实，不依赖预测。</li>
<li><b>[客观分析]</b> 市场当前处于典型的<b>”近松远紧“</b>结构，且期货曲线已明确定价这一结构 ——
完全 Contango，Oct-26 → Mar-27 升水 +12.2%%，且当日跌幅随月份递减。<b>这意味着远端收紧逻辑已进入价格，
不是未被发现的alpha</b>。真正的信息不对称在于：①10-12 MPOB 数据是否超 337 万吨（近端利空强度）；
②B50 兑现率的月度跟踪（GAPKI 生柴消费数据，2026-05 为 1,035 kt/月）；③9–11月东南亚实际降雨。</li>
<li><b>[结论与置信度]</b> 近端利空<b>高置信度</b>（待 10-12 验证）；中端 B50 利多<b>中高置信度</b>（政策已落地，兑现率待跟踪）；
远端供给引擎减速<b>高置信度</b>（实绩数据）；远端 EN 减产<b>低置信度</b>（统计检验未能证实，与产业共识冲突，已完整披露）。
<b>综合：方向上偏多头结构，但时间上不在当下，且远端逻辑的核心支柱之一（EN）证据不足。</b></li>
</ul></div>
""" % (w26["surplus"] / 1000, w26["stu"], abs(yld_cagr_2026),
       100 * (SUP["biodiesel"]["id_industrial_2026"] / SUP["biodiesel"]["id_industrial_2015"] - 1),
       lat["pd_spread"] or 0))

A("""<h3>关键跟踪日历</h3>
<div class="scroll"><table>
<tr><th style="width:130px">时点</th><th style="width:190px">事件</th><th>关注要点</th></tr>
<tr class="hl-row"><td><b>2026-10-12</b><br>北京时间 12:30</td><td>MPOB 9月供需报告</td>
<td>库存是否超 337 万吨（历史新高）；产量是否达 210 万吨（打破 2015年8月纪录）；出口降幅是否收窄。
<b>这是最近、最确定的验证节点。</b></td></tr>
<tr><td>每月 10 日前后</td><td>MPOB 月度报告</td><td>库存拐点（MPOC 与 IFFCO 均预期 10月起随产量季节性回落而开始去库）；
单产与 OER（出油率）—— 比 ONI 更直接的 EN 影响先行指标。</td></tr>
<tr><td>每月中旬</td><td>GAPKI 印尼月度数据</td><td>生柴消费量（B50 兑现率的直接度量，2026-05 = 1,035 kt）；
库存（2026-05 = 304.2 万吨，为近 5 年低位）；分国别出口。</td></tr>
<tr><td>每月</td><td>CPC ONI 更新</td><td>JAS = +2.16。若 ASO/SON/OND 继续升破 +2.59，将超越 2015 年成为有记录以来最强。</td></tr>
<tr><td>2026年9–11月</td><td><b>东南亚降雨（关键窗口）</b></td>
<td>MPOC 明确指出这是决定 2027 年影响程度的窗口。印尼雨季通常 10月开始，今年恐推迟至 11–12月且周期缩短。
加里曼丹火点已升至十年最高。</td></tr>
<tr><td>2026年10月</td><td>印度排灯节备货</td><td>关税减半后的实际采购量；是否在棕榈油与豆油/葵花油间切换（价差已收窄）。</td></tr>
<tr><td>持续</td><td>印尼政策</td><td>B50 兑现率是否调整；出口税/levy 变动（当前 CPO 12.5%）；DMO 政策；
EUDR 合规进展。<b>注意 2026年1月曾宣布放弃 B50 后反转的先例。</b></td></tr>
</table></div>
""")

# ================= 附录 =================
A("""<div class="dis">
<b>数据与口径附录</b><br><br>
<b>1. 数据来源与 vintage</b><br>
· <b>USDA FAS PSD API</b>（主口径）：商品码 <code>4243000</code> Oil, Palm；另采集 <code>4232000</code> 豆油、
<code>4239100</code> 菜油、<code>4236000</code> 葵花油、<code>4242000</code> 椰子油、<code>4244000</code> 棕榈仁油用于板块对比。
覆盖 MY1989–MY2026（38 年）× 全球 + 16 国。<b>全球记录 vintage = 2026-09</b>；
分国 vintage 不齐（马来 MY2019–20 = 2024-10、MY2021–24 = 2026-04、MY2025–26 = 2026-09；
印尼 MY2022–24 = 2026-03、MY2025 = 2026-08、MY2026 = 2026-09）。<b>历史年为最后一次修订值，非当年发布值</b> ——
PSD API 不返回历史 vintage 序列。<br>
· <b>MPOB</b>（马来西亚棕榈油局）月度实绩：2026年1–8月经官方发布核实（Bernama / The Star / The Edge / 卓创资讯 sci99 交叉验证）；
9月为路透调查预估，正式数据 2026-10-12 发布。<br>
· <b>GAPKI</b>（印尼棕榈油协会）月度数据：2026年1–5月经其官方新闻稿核实（gapki.id）。<br>
· <b>价格</b>：IMF Primary Commodity Prices via FRED（<code>PPOILUSDM</code> 棕榈油、<code>PSOILUSDM</code> 豆油、
<code>PSUNOUSDM</code> 葵花油、<code>PROILUSDM</code> 菜油），月度，1980-01–2026-07（发布滞后约 2 个月）；
1960–1979 用世界银行 Pink Sheet CMO 月度数据补齐（<code>data/price/palm/wb_cmo_vegoil_monthly_1960_2024.csv</code>）。
Brent 原油 <code>DCOILBRENTEU</code>；USD/MYR <code>DEXMAUS</code>。<br>
· <b>ENSO</b>：NOAA/CPC ONI（<code>oni.ascii.txt</code>），3 个月滑动均值，气候基准期 1981–2010。<br>
· <b>BMD FCPO 期货</b>：Bernama 2026-10-07 收盘报道。<br><br>

<b>2. 关键口径纪律（踩过的坑，务必遵守）</b><br>
· <b>棕榈油市场年 = 10月–次年9月</b>（与糖不同：糖为 5月–4月世界口径、巴西 4月–3月、泰国 12月–11月）。
<code>MY2026</code> = 2026/27 = 2026-10 ~ 2027-09，<b>当前正在进行，属预测值</b>；
<code>MY2025</code> = 2025/26 = 2025-10 ~ 2026-09，<b>刚于 2026年9月收官</b>。<br>
· <b>消费码必须用 125 <code>Domestic Consumption</code>，不能用 126</b>。棕榈油的 125 = 140 工业 + 149 食用 + 161 饲料损耗
（已跑恒等式校验：38 年 × 全球，供给端与分配端各 0 个不平）。<b>这与糖相反</b> —— 糖必须用 126（Total Disappearance），
用 139 会导致 174 个国家-年不平。跨品种套用消费码是本项目已识别的高风险陷阱。<br>
· <b>STU 必须自行计算</b>：<code>176 期末库存 ÷ 125 总消费</code>。PSD 的 <code>195 Stocks-to-Use</code> 字段在棕榈油数据中<b>未填充</b>。<br>
· <b>分国 STU 不可横向比较</b>：马来 MY2026 STU = %.1f%%（因国内消费基数仅 %.0f kt）vs 印尼 %.1f%%。
应比较库存绝对量与净贸易方向。<br>
· <b>P-D 价差必须分段计算分位</b>：世行棕榈油价格序列 2024-11 从 RBD FOB Malaysia 切换为 5%% Bulk CIF NW Europe；
豆油 2021-01 从 FOB NW Europe 切换为 EXW Dutch Mills。全样本分位会高估约 6 个百分点。<br>
· <b>单位</b>：PSD <code>unitId=8</code> = 1000 MT；<code>unitId=4</code> = 1000 HA（面积）；
<code>unitId=26</code> = MT/HA（单产）。MPOB/GAPKI 常以“万吨”或“千吨”报道，本报告表格统一千吨，正文混用万吨并明确标注。<br><br>

<b>3. 平衡表恒等式校验（已通过）</b><br>
<code>期初(20) + 产量(28) + 进口(57) = 总供给(86)</code> ｜
<code>总消费(125) + 出口(88) + 期末(176) = 总分配(178) = 总供给(86)</code> ｜
<code>总消费(125) = 工业(140) + 食用(149) + 饲料损耗(161)</code><br>
MY1989–MY2026 全球序列：供给端 0 个不平，分配端 0 个不平。<br><br>

<b>4. 统计方法说明</b><br>
· <b>反事实基准</b>：产量/单产偏差用“前 3 年均值”作反事实，不用 YoY（YoY 在趋势上行期系统性低估减产）。<br>
· <b>去趋势</b>：OLS 拟合 1 次 vs 2 次多项式，按 R² 改善 >0.05 自动选择阶数。
马来西亚单产必须用 2 次（线性 R²=0.005 vs 二次 R²=0.650，呈倒 U 型）。<br>
· <b>多重比较校正</b>：3 地区 × 19 滞后 = 57 项检验，同时报告 Bonferroni 与 Benjamini–Hochberg FDR(5%%)。<br>
· <b>情景推演</b>：只改分子（期末库存 = 基线 + 产量偏差 − 消费增量），<b>不重复计入基线盈余</b>。<br>
· <b>分位计算</b>：(小于当前值的样本数 + 0.5) / n。<b>多窗口并列披露</b>。<br><br>

<b>5. 已知数据局限</b><br>
· <b>MPOB 长序列月度数据未入库</b>：本项目仅核实了 2026年1–9月共 9 个月 + 2018-12 历史峰值。
因此无法用 MPOB 原始月度单产重做 ENSO 检验（PSD 年度修订值含平滑，削弱了检验功效）。<b>这是第七节统计结论的最主要局限。</b><br>
· <b>CFTC 持仓数据缺失</b>：CFTC 不单独发布棕榈油 COT 报告（BMD FCPO 属马来西亚交易所，
ICE 无棕榈油期货）。因此本报告<b>不含持仓面分析</b>，与本项目糖/棉花报告的“基本面 + 持仓面”双轨范式不同。
可获得的替代观测：BMD FCPO 成交量与持仓量（2026-10-07 为 70,612 手 / 328,944 手）。<br>
· <b>树龄结构数据缺失</b>：PSD 无油棕树龄分布字段。“马来单产倒 U 型 = 树龄老化”的归因来自产业文献与 USDA FAS GAIN 定性表述，
<b>未用树龄结构数据直接验证</b>。<br>
· <b>印尼库存口径差异</b>：GAPKI 月度库存（2026-05 = 304.2 万吨）与 USDA PSD 印尼期末库存（MY2026 = 406.6 万吨）
量级接近但时点与市场年定义不同（GAPKI 为历年月末，PSD 为市场年 9月末），<b>不可直接相减</b>。<br><br>

<b>6. 本地产出文件</b><br>
· <code>data/fundamentals/palm/psd_vegoil_world.json</code> — 6 油脂品种 × 38 年全球平衡表<br>
· <code>data/fundamentals/palm/psd_palm_countries.json</code> — 棕榈油 16 国 × 38 年<br>
· <code>data/fundamentals/palm/palm_indicators.json</code> — 核心指标（平衡表/STU分位/价格/ONI）<br>
· <code>data/fundamentals/palm/palm_world_balance.csv</code> — 全球平衡表 CSV<br>
· <code>data/fundamentals/palm/palm_enso_lag.json</code> — ENSO 滞后扫描与事件研究（v1）<br>
· <code>data/fundamentals/palm/palm_enso_detrended.json</code> — 去趋势后 ENSO 检验（v2，含 p 值）<br>
· <code>data/fundamentals/palm/palm_multiple_testing.json</code> — 多重比较校正结果<br>
· <code>data/fundamentals/palm/palm_scenario.json</code> — 库存分层与情景推演<br>
· <code>data/fundamentals/palm/palm_supplement.json</code> — 面积/单产分解、集中度、价格分位<br>
· <code>data/fundamentals/palm/mpob_monthly_2026.csv</code> — MPOB 2026 月度实况<br>
· <code>data/price/palm/</code> — FRED 油脂价格 CSV × 7 + 世行 CMO xlsx + 棕榈油月度 CSV（1960–2024）+ ONI<br>
· <code>scripts/palm_pull_psd.py</code> / <code>palm_indicators.py</code> / <code>palm_enso_lag.py</code> /
<code>palm_enso_v2.py</code> / <code>palm_scenario.py</code> / <code>palm_supplement.py</code> /
<code>palm_export_report_data.py</code> / <code>build_report_110.py</code><br><br>

<b>7. 免责声明</b><br>
本报告基于公开数据源编制，所有数字均标注来源与 vintage；标注“预估/调查”的项目尚未有官方实绩。
第九节的置信度评级反映的是<b>证据强度</b>，不是价格方向预测。本报告不构成投资建议。
棕榈油市场受政策（印尼出口税/levy、B50 兑现率、DMO、EUDR）与天气双重外生冲击影响，
<b>政策摇摆有明确先例</b>（2026年1月印尼宣布放弃 B50 后于 7月反转实施），任何基于当前政策的推演都存在被推翻的风险。<br>
生成时间：2026-10-07 ｜ 报告编号 110 ｜ 配色：Okabe–Ito 色弱安全方案，全部图表叠加线型/标记/直接标注等非颜色线索。
</div>
</div>""" % (my26["stu"], my26["dom"], id26["stu"]))

# ================= 图表脚本 =================
DATA_JSON = json.dumps(D, ensure_ascii=False)
A("<script>const D=%s;const W={};D.world.forEach(w=>W[w.my]=w);const YRS=D.world.map(w=>w.my);" % DATA_JSON)

A(r"""
const OK={b:'#0072B2',o:'#E69F00',sb:'#56B4E9',pr:'#CC79A7',vr:'#D55E00',gr:'#009E73',k:'#000000'};
const AX={axisLine:{lineStyle:{color:'#9ca3af'}},axisLabel:{color:'#4b5563',fontSize:11},
          splitLine:{lineStyle:{color:'#eef0f3'}}};
const TT={trigger:'axis',axisPointer:{type:'cross'},backgroundColor:'rgba(255,255,255,.97)',
          borderColor:'#d1d5db',textStyle:{color:'#1f2329',fontSize:12}};
function mk(id,opt){const el=document.getElementById(id);if(!el)return;
  const c=echarts.init(el);c.setOption(opt);window.addEventListener('resize',()=>c.resize());}

/* c1 全球平衡表 */
mk('c1',{tooltip:TT,legend:{data:['产量','总消费','期末库存','STU%'],top:0,textStyle:{fontSize:12}},
 grid:{left:64,right:66,top:44,bottom:56},
 xAxis:Object.assign({type:'category',data:YRS,axisLabel:{color:'#4b5563',fontSize:10.5,rotate:60}},
   {axisLine:AX.axisLine}),
 yAxis:[Object.assign({type:'value',name:'千吨',nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
        Object.assign({type:'value',name:'STU %',min:5,max:28,nameTextStyle:{color:'#6b7280',fontSize:11},
          splitLine:{show:false}},AX)],
 series:[
  {name:'产量',type:'bar',data:YRS.map(y=>W[y].prod),itemStyle:{color:OK.b},barGap:'-32%',barWidth:'46%'},
  {name:'总消费',type:'bar',data:YRS.map(y=>W[y].dom_cons),itemStyle:{color:OK.sb},barWidth:'46%'},
  {name:'期末库存',type:'line',data:YRS.map(y=>W[y].end),lineStyle:{color:OK.vr,width:2.6},
   symbol:'circle',symbolSize:5,itemStyle:{color:OK.vr},
   markArea:{itemStyle:{color:'rgba(0,0,0,.045)'},data:[[{xAxis:'2026',name:'MY2026 进行中'},{xAxis:'2026'}]],
     label:{color:'#6b7280',fontSize:10}}},
  {name:'STU%',type:'line',yAxisIndex:1,data:YRS.map(y=>W[y].stu),
   lineStyle:{color:OK.k,width:2.2,type:'dashed'},symbol:'triangle',symbolSize:7,itemStyle:{color:OK.k},
   markPoint:{data:[{coord:['2021',W['2021'].stu],value:'峰 '+W['2021'].stu+'%',
     itemStyle:{color:OK.o},label:{fontSize:10.5,fontWeight:'bold'}}]}}
 ]});

/* c2 STU 分位 */
(function(){
 const s=YRS.filter(y=>y>='1989').map(y=>({y,v:W[y].stu}));
 const wins=[{n:'1989–2025',lo:'1989',c:OK.b,ls:'solid'},
             {n:'2000–2025',lo:'2000',c:OK.o,ls:'dashed'},
             {n:'2010–2025',lo:'2010',c:OK.vr,ls:'dotted'}];
 const ser=[{name:'STU 实际值',type:'line',data:s.map(d=>d.y),
   showSymbol:false,lineStyle:{width:0},tooltip:{show:false},stack:'x',silent:true,data:[]}];
 mk('c2',{tooltip:TT,legend:{top:0,data:['STU%'].concat(wins.map(w=>w.n+' 均值')),textStyle:{fontSize:11.5}},
  grid:{left:56,right:30,top:42,bottom:54},
  xAxis:Object.assign({type:'category',data:s.map(d=>d.y),
    axisLabel:{color:'#4b5563',fontSize:10.5,rotate:60}},{axisLine:AX.axisLine}),
  yAxis:Object.assign({type:'value',name:'STU %',nameTextStyle:{color:'#6b7280',fontSize:11},min:8},AX),
  series:[{name:'STU%',type:'line',data:s.map(d=>d.v),lineStyle:{color:OK.k,width:2.6},
    symbol:'circle',symbolSize:4.5,itemStyle:{color:OK.k},
    markPoint:{data:[{coord:['2026',W['2026'].stu],value:'MY2026\n'+W['2026'].stu+'%',
      symbolSize:58,itemStyle:{color:OK.o},label:{fontSize:10,fontWeight:'bold',color:'#fff'}}]}}].concat(
   wins.map(w=>{const sub=s.filter(d=>d.y>=w.lo&&d.y<='2025').map(d=>d.v);
     const m=sub.reduce((a,b)=>a+b,0)/sub.length;
     return {name:w.n+' 均值',type:'line',data:s.map(d=>(d.y>=w.lo?+m.toFixed(2):null)),
       lineStyle:{color:w.c,width:2,type:w.ls},symbol:'none',itemStyle:{color:w.c},
       endLabel:{show:true,formatter:w.n+' '+m.toFixed(1)+'%',color:w.c,fontSize:10.5,fontWeight:'bold'}};}))
 });
})();

/* c3 产量集中度 */
(function(){
 const yrs=['2000','2005','2010','2015','2020','2024','2025','2026'];
 mk('c3',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},grid:{left:62,right:26,top:40,bottom:36},
  xAxis:Object.assign({type:'category',data:yrs.map(y=>'MY'+y.slice(2))},{axisLine:AX.axisLine}),
  yAxis:Object.assign({type:'value',name:'千吨',nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
  series:[
   {name:'印尼产量',type:'bar',stack:'p',data:yrs.map(y=>D.id[y]?D.id[y].prod:null),itemStyle:{color:OK.b}},
   {name:'马来产量',type:'bar',stack:'p',data:yrs.map(y=>D.my[y]?D.my[y].prod:null),itemStyle:{color:OK.o}},
   {name:'其他国产量',type:'bar',stack:'p',data:yrs.map(y=>W[y].prod-(D.id[y]?D.id[y].prod:0)-(D.my[y]?D.my[y].prod:0)),
    itemStyle:{color:OK.sb}},
   {name:'两国合计占比%',type:'line',yAxisIndex:0,data:yrs.map(y=>
      +(((D.id[y]?D.id[y].prod:0)+(D.my[y]?D.my[y].prod:0))/W[y].prod*100*1000).toFixed(0)),
    lineStyle:{width:0},symbol:'none',tooltip:{show:false}}
  ]});
})();

/* c4 进口方份额 */
(function(){
 const imps=[['印度',8700,OK.b],['中国',3900,OK.o],['巴基斯坦',3700,OK.sb],['欧盟',3100,OK.pr],
   ['孟加拉',1725,OK.vr],['美国',1700,OK.gr],['其他',Math.max(0,W['2026'].exp-8700-3900-3700-3100-1725-1700),'#9ca3af']];
 mk('c4',{tooltip:Object.assign({trigger:'item',formatter:'{b}: {c} kt ({d}%)'},{backgroundColor:TT.backgroundColor,
   borderColor:TT.borderColor,textStyle:TT.textStyle}),
  legend:{orient:'vertical',right:6,top:'middle',textStyle:{fontSize:11.5}},
  series:[{type:'pie',radius:['42%','70%'],center:['38%','52%'],
   data:imps.map(d=>({name:d[0],value:d[1],itemStyle:{color:d[2]}})),
   label:{fontSize:11,formatter:'{b}\n{d}%',color:'#374151'},
   labelLine:{length:9,length2:9}}]});
})();

/* c5 面积 vs 单产 */
(function(){
 const yrs=YRS.filter(y=>y>='1990');
 mk('c5',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},
  grid:[{left:60,right:'53%',top:40,bottom:56},{left:'53%',right:56,top:40,bottom:56}],
  xAxis:[Object.assign({type:'category',gridIndex:0,data:yrs,axisLabel:{color:'#4b5563',fontSize:10,rotate:60}},{axisLine:AX.axisLine}),
         Object.assign({type:'category',gridIndex:1,data:yrs,axisLabel:{color:'#4b5563',fontSize:10,rotate:60}},{axisLine:AX.axisLine})],
  yAxis:[Object.assign({type:'value',gridIndex:0,name:'千公顷',nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
         Object.assign({type:'value',gridIndex:1,name:'吨/公顷',min:2,max:5,nameTextStyle:{color:'#6b7280',fontSize:11},splitLine:{show:false}},AX)],
  series:[
   {name:'全球面积',type:'line',xAxisIndex:0,yAxisIndex:0,data:yrs.map(y=>W[y].area_kha),
    lineStyle:{color:OK.b,width:2.4},symbol:'none',areaStyle:{color:'rgba(0,114,178,.10)'}},
   {name:'印尼面积',type:'line',xAxisIndex:0,yAxisIndex:0,data:yrs.map(y=>D.id[y]?D.id[y].area_kha:null),
    lineStyle:{color:OK.o,width:2,type:'dashed'},symbol:'none'},
   {name:'马来面积',type:'line',xAxisIndex:0,yAxisIndex:0,data:yrs.map(y=>D.my[y]?D.my[y].area_kha:null),
    lineStyle:{color:OK.vr,width:2,type:'dotted'},symbol:'none'},
   {name:'全球单产',type:'line',xAxisIndex:1,yAxisIndex:1,data:yrs.map(y=>W[y].yield),
    lineStyle:{color:OK.b,width:2.4},symbol:'circle',symbolSize:4},
   {name:'印尼单产',type:'line',xAxisIndex:1,yAxisIndex:1,data:yrs.map(y=>D.id[y]?D.id[y].yield:null),
    lineStyle:{color:OK.o,width:2,type:'dashed'},symbol:'triangle',symbolSize:5},
   {name:'马来单产',type:'line',xAxisIndex:1,yAxisIndex:1,data:yrs.map(y=>D.my[y]?D.my[y].yield:null),
    lineStyle:{color:OK.vr,width:2,type:'dotted'},symbol:'rect',symbolSize:5,
    markPoint:{data:[{type:'max',name:'马来峰值',itemStyle:{color:OK.vr},label:{fontSize:10,formatter:'马来峰 {c}'}}]}}
  ]});
})();

/* c6 需求结构 */
(function(){
 const yrs=YRS.filter(y=>y>='1990');
 mk('c6',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},grid:{left:64,right:64,top:42,bottom:56},
  xAxis:Object.assign({type:'category',data:yrs,axisLabel:{color:'#4b5563',fontSize:10.5,rotate:60}},{axisLine:AX.axisLine}),
  yAxis:[Object.assign({type:'value',name:'千吨',nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
         Object.assign({type:'value',name:'工业占比 %',min:0,max:45,splitLine:{show:false},
           nameTextStyle:{color:'#6b7280',fontSize:11}},AX)],
  series:[
   {name:'食用消费',type:'bar',stack:'d',data:yrs.map(y=>W[y].food),itemStyle:{color:OK.sb}},
   {name:'工业消费(生柴+油化)',type:'bar',stack:'d',data:yrs.map(y=>W[y].industrial),itemStyle:{color:OK.vr}},
   {name:'工业占比%',type:'line',yAxisIndex:1,data:yrs.map(y=>W[y].biodiesel_share),
    lineStyle:{color:OK.k,width:2.6,type:'dashed'},symbol:'triangle',symbolSize:7,itemStyle:{color:OK.k},
    markLine:{data:[{xAxis:'2026',label:{formatter:'MY2026 '+W['2026'].biodiesel_share+'%',fontSize:10.5,fontWeight:'bold'},
      lineStyle:{color:OK.o,width:2}}]}},
   {name:'印尼工业消费',type:'line',data:yrs.map(y=>D.id[y]?D.id[y].industrial:null),
    lineStyle:{color:OK.b,width:2.2},symbol:'circle',symbolSize:4.5,itemStyle:{color:OK.b}}
  ]});
})();

/* c7 MPOB 月度库存 */
(function(){
 const m=D.mpob, labs=m.map(x=>x.ym), tot=m.map(x=>x.total_stocks_wt);
 mk('c7',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},grid:{left:58,right:60,top:44,bottom:38},
  xAxis:Object.assign({type:'category',data:labs},{axisLine:AX.axisLine}),
  yAxis:[Object.assign({type:'value',name:'万吨',min:150,nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
         Object.assign({type:'value',name:'产量/出口 万吨',min:80,max:230,splitLine:{show:false},
           nameTextStyle:{color:'#6b7280',fontSize:11}},AX)],
  series:[
   {name:'总库存',type:'bar',data:tot.map((v,i)=>({value:v,
      itemStyle:{color:i===tot.length-1?OK.vr:OK.b,
        opacity:i===tot.length-1?.62:1,
        borderColor:i===tot.length-1?OK.vr:'transparent',borderWidth:i===tot.length-1?2:0,
        borderType:i===tot.length-1?'dashed':'solid'}})),
    label:{show:true,position:'top',fontSize:10.5,fontWeight:'bold',color:'#374151',
      formatter:p=>p.dataIndex===tot.length-1?p.value+' (预估)':p.value},
    markLine:{data:[{yAxis:322,label:{formatter:'历史峰值 322 (2018-12)',position:'insideEndTop',
      fontSize:10.5,fontWeight:'bold',color:OK.vr},lineStyle:{color:OK.vr,width:2,type:'dashed'}},
      {yAxis:300,label:{formatter:'300 万吨关口（史上仅5次突破）',position:'insideEndBottom',
        fontSize:10,color:'#6b7280'},lineStyle:{color:'#9ca3af',width:1.4,type:'dotted'}}]}},
   {name:'CPO库存',type:'line',data:m.map(x=>x.cpo_stocks_wt),lineStyle:{color:OK.o,width:2.2},
    symbol:'circle',symbolSize:5,itemStyle:{color:OK.o},connectNulls:true},
   {name:'产量',type:'line',yAxisIndex:1,data:m.map(x=>x.production_wt),
    lineStyle:{color:OK.gr,width:2,type:'dashed'},symbol:'triangle',symbolSize:6,itemStyle:{color:OK.gr},connectNulls:true},
   {name:'出口',type:'line',yAxisIndex:1,data:m.map(x=>x.exports_wt),
    lineStyle:{color:OK.pr,width:2,type:'dotted'},symbol:'rect',symbolSize:6,itemStyle:{color:OK.pr},connectNulls:true}
  ]});
})();

/* c8 价格与 P-D 价差 */
(function(){
 const p=D.price.filter(x=>x.ym>='1990-01'&&x.palm);
 const l1=p.map(x=>x.ym), pa=p.map(x=>x.palm), so=p.map(x=>x.soy), sp=p.map(x=>x.pd_spread);
 mk('c8',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},grid:{left:60,right:64,top:44,bottom:56},
  xAxis:Object.assign({type:'category',data:l1,axisLabel:{color:'#4b5563',fontSize:10.5,rotate:60,
    formatter:v=>v.endsWith('-01')?v.slice(0,4):''}},{axisLine:AX.axisLine}),
  yAxis:[Object.assign({type:'value',name:'$/吨',nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
         Object.assign({type:'value',name:'P-D 价差 $/吨',splitLine:{show:false},
           nameTextStyle:{color:'#6b7280',fontSize:11}},AX)],
  series:[
   {name:'棕榈油',type:'line',data:pa,lineStyle:{color:OK.o,width:2.4},symbol:'none',
    markLine:{data:[{yAxis:1106,label:{formatter:'2026-07 = 1106',fontSize:10,color:OK.o},
      lineStyle:{color:OK.o,type:'dotted',width:1.2}}]}},
   {name:'豆油',type:'line',data:so,lineStyle:{color:OK.b,width:2.4},symbol:'none'},
   {name:'P-D 价差（右轴）',type:'line',yAxisIndex:1,data:sp,
    lineStyle:{color:OK.k,width:2.2,type:'dashed'},symbol:'none',
    areaStyle:{color:'rgba(0,0,0,.05)'},
    markArea:{itemStyle:{color:'rgba(213,94,0,.09)'},
      data:[[{xAxis:'2024-11',name:'现行口径段\n(2024-11起)'},{xAxis:l1[l1.length-1]}]],
      label:{color:OK.vr,fontSize:10,fontWeight:'bold'}},
    markLine:{data:[{yAxis:84,label:{formatter:'全样本均值 +84',fontSize:10,color:'#6b7280'},
      lineStyle:{color:'#9ca3af',type:'dotted',width:1.2}}]}}
  ]});
})();

/* c9 油脂板块 STU */
(function(){
 const nm={palm:'棕榈油',soyoil:'豆油',rapeseed:'菜油',sunflower:'葵花油',pko:'棕榈仁油',coconut:'椰子油'};
 const ord=['palm','soyoil','rapeseed','sunflower','pko','coconut'];
 const col={palm:OK.vr,soyoil:OK.b,rapeseed:OK.o,sunflower:OK.sb,pko:OK.pr,coconut:OK.gr};
 const yrs=YRS.filter(y=>y>='2000');
 mk('c9',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11}},grid:{left:48,right:26,top:40,bottom:52},
  xAxis:Object.assign({type:'category',data:yrs,axisLabel:{color:'#4b5563',fontSize:10,rotate:60}},{axisLine:AX.axisLine}),
  yAxis:Object.assign({type:'value',name:'STU %',nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
  series:ord.map(k=>({name:nm[k],type:'line',
    data:yrs.map(y=>{const r=D.oils[k].find(x=>x.my===y);return r&&r.stu?r.stu:null;}),
    lineStyle:{color:col[k],width:k==='palm'?3:1.8,type:k==='palm'?'solid':'dashed'},
    symbol:k==='palm'?'circle':'none',symbolSize:5,itemStyle:{color:col[k]}}))
 });
})();

/* c10 ONI vs 马来单产残差 */
(function(){
 const R=D.enso['马来']; if(!R)return;
 const yrs=R.years;
 // ONI 市场年均值（用 events 的 peak_oni 补）
 const ev={};(R.events||[]).forEach(e=>ev[e.my]=e);
 mk('c10',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},grid:{left:62,right:64,top:44,bottom:56},
  xAxis:Object.assign({type:'category',data:yrs.map(y=>'MY'+y.slice(2)),
    axisLabel:{color:'#4b5563',fontSize:10,rotate:60}},{axisLine:AX.axisLine}),
  yAxis:[Object.assign({type:'value',name:'马来单产 t/ha',min:2.4,max:4.8,
    nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
   Object.assign({type:'value',name:'单产残差 (t/ha)',splitLine:{show:false},
    nameTextStyle:{color:'#6b7280',fontSize:11}},AX)],
  series:[
   {name:'马来单产（实际）',type:'line',yAxisIndex:0,data:yrs.map(y=>D.my[y]?D.my[y].yield:null),
    lineStyle:{color:OK.o,width:2.6},symbol:'circle',symbolSize:4.5,itemStyle:{color:OK.o},
    markPoint:{data:yrs.filter(y=>ev[y]).map(y=>({coord:[yrs.indexOf(y),D.my[y].yield],
      value:'EN',symbolSize:26,itemStyle:{color:OK.vr},label:{fontSize:9,color:'#fff',fontWeight:'bold'},
      tooltip:{formatter:'MY'+y+' 强EN<br>峰值ONI '+ev[y].peak_oni.toFixed(2)+'<br>单产残差 '+
        ev[y].resid.toFixed(3)+' ('+ev[y].z.toFixed(2)+'σ)'}}))}},
   {name:'去趋势残差（右轴）',type:'bar',yAxisIndex:1,
    data:yrs.map((y,i)=>({value:R.resid[i],itemStyle:{color:R.resid[i]<0?OK.b:'#c7ccd4'}})),barWidth:'52%'},
   {name:'残差零线',type:'line',yAxisIndex:1,data:yrs.map(()=>0),lineStyle:{color:OK.k,width:1.4},
    symbol:'none',tooltip:{show:false}}
  ]});
})();

/* c11 情景阶梯 */
(function(){
 const s=D.scen.scenarios;
 mk('c11',{tooltip:TT,legend:{top:0,textStyle:{fontSize:11.5}},grid:{left:56,right:60,top:42,bottom:78},
  xAxis:Object.assign({type:'category',data:s.map(x=>x.name),
    axisLabel:{color:'#374151',fontSize:10.5,interval:0,rotate:22,
      formatter:v=>v.length>16?v.slice(0,15)+'…':v}},{axisLine:AX.axisLine}),
  yAxis:[Object.assign({type:'value',name:'STU %',min:-2,max:20,nameTextStyle:{color:'#6b7280',fontSize:11}},AX),
         Object.assign({type:'value',name:'历史分位 %',min:0,max:100,splitLine:{show:false},
           nameTextStyle:{color:'#6b7280',fontSize:11}},AX)],
  series:[
   {name:'情景 STU%',type:'bar',data:s.map(x=>({value:x.stu,
      itemStyle:{color:x.stu<8?OK.vr:x.stu<13?OK.o:OK.b}})),barWidth:'46%',
    label:{show:true,position:'top',fontSize:11,fontWeight:'bold',color:'#374151',formatter:'{c}%'}},
   {name:'历史分位%（右轴）',type:'line',yAxisIndex:1,data:s.map(x=>x.pctile),
    lineStyle:{color:OK.k,width:2.4,type:'dashed'},symbol:'triangle',symbolSize:8,itemStyle:{color:OK.k},
    label:{show:true,position:'bottom',fontSize:10,color:OK.k,formatter:'{c}'}},
   {name:'MY2026 实际 STU',type:'line',data:s.map(()=>W['2026'].stu),
    lineStyle:{color:OK.gr,width:2,type:'dotted'},symbol:'none',tooltip:{show:false}}
  ]});
})();
</script>
</div></body></html>""")

html = "".join(HTML)
path = os.path.join(OUT, "index.html")
io.open(path, "w", encoding="utf-8").write(html)
print("written:", path, "%.1f KB" % (len(html.encode("utf-8")) / 1024))
