# -*- coding: utf-8 -*-
"""97 棉花基本面全景 报告生成器 (v2 clean)
输入: data/fundamentals/cotton_survey_20260920.json, data/cftc/cotton/cotton_cot_ncnet_monthly_20260920.json,
      data/cftc/results_cot/cotton_cot_stats_20260920.json, data/price/cotton/cotton_wb_monthly.csv
输出: reports/97_棉花基本面全景_20260920/index.html
"""
import json, csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
SRV = json.load(open(os.path.join(D, "fundamentals", "cotton", "cotton_survey_20260920.json")))
COT = json.load(open(os.path.join(D, "cftc", "cotton", "cotton_cot_ncnet_monthly_20260920.json")))
STATS = json.load(open(os.path.join(D, "cftc", "results_cot", "cotton_cot_stats_20260920.json")))
WB = []
with open(os.path.join(D, "price", "cotton", "cotton_wb_monthly.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        WB.append((r["month"], float(r["cotton_a"])))

world = SRV["world"]
def series(k):
    return [[int(y), w[k]] for y, w in world.items() if w.get(k) is not None]
prod_s, dom_s, end_s = series("prod"), series("dom"), series("end")
pm_s = [[int(y), w.get("prod", 0) - w.get("dom", 0)] for y, w in world.items()]
stu_s = [[int(y), w["stu"]] for y, w in world.items() if w.get("stu")]
stu_t_s = [[int(y), w["stu_t"]] for y, w in world.items() if w.get("stu_t")]
excn_s = [[int(y), v["stu"]] for y, v in sorted(SRV["ex_cn"].items(), key=lambda kv: int(kv[0])) if v.get("stu")]
exc2_s = [[int(y), v["stu"]] for y, v in sorted(SRV["ex_c2i"].items(), key=lambda kv: int(kv[0])) if v.get("stu")]

def pct(series_, v):
    s = sorted(series_)
    return round(100.0 * sum(1 for x in s if x < v) / len(s), 1)
cur_stu = world["2026"]["stu"]
stu_all = [w["stu"] for w in world.values() if w.get("stu")]
stu_last10 = [w["stu"] for w in world.values() if w.get("stu") and int([k for k, ww in world.items() if ww is w][0]) >= 2016]

rk_p = [(x["name"], x["val"]) for x in SRV["rank"]["prod"][:10]]
rk_e = [(x["name"], x["val"]) for x in SRV["rank"]["exp"][:10]]
rk_i = [(x["name"], x["val"]) for x in SRV["rank"]["imp"][:10]]
rk_s = [(x["name"], x["val"]) for x in SRV["rank"]["end"][:10]]

hist = SRV["hist"]
def cn_hist(name):
    return {e["y"]: e.get("prod") for e in hist.get(name, []) if e.get("prod")}
H = {n: cn_hist(n) for n in ("United States", "China", "India", "Brazil")}
tick = [1960, 1970, 1980, 1990, 2000, 2010, 2020, 2026]
share = []
for y in tick:
    share.append([y, H["United States"].get(y), H["China"].get(y),
                  H["India"].get(y), H["Brazil"].get(y)])

wb_x = [m for m, _ in WB]; wb_y = [v for _, v in WB]
wb_zoom = [[m, v] for m, v in WB if m >= "2024M06"]
cot_x = [d for d, _, _ in COT]; cot_y = [n for _, n, _ in COT]

net_trade = [("越南", 8.2), ("孟加拉", 7.4), ("土耳其", 5.0), ("巴基斯坦", 5.1), ("中国", 7.0 - 0.08),
             ("印度", 3.0 - 1.5), ("澳大利亚", -4.5), ("美国", -12.3), ("巴西", -15.5)]

DATA = {
 "prod": prod_s, "dom": dom_s, "end": end_s, "pm": pm_s, "stu": stu_s,
 "excn": excn_s, "exc2": exc2_s, "share": share, "rk_p": rk_p, "rk_s": rk_s,
 "wb_x": wb_x, "wb_y": wb_y, "wb_zoom": wb_zoom, "cot_x": cot_x, "cot_y": cot_y,
 "net_trade": net_trade,
 "stats": {"stu_cur": cur_stu, "stu_pct_full": pct(stu_all, cur_stu),
           "stu_pct10": pct(stu_last10, cur_stu), "stu_excn": SRV["ex_cn"]["2026"]["stu"],
           "stu_exc2": SRV["ex_c2i"]["2026"]["stu"],
           "cot_last": STATS["nc_net_last"], "cot_12w": STATS["chg_12w"]}
}
DATA_JS = json.dumps(DATA, ensure_ascii=False)

hist_rows = ""
tbl = [
 ("2021/22", 112.7, 115.2, 70.9, -2.5, "61.5%", "44.9%", ""),
 ("2022/23", 114.3, 112.3, 75.5, 2.0, "67.2%", "50.8%", "up"),
 ("2023/24", 111.3, 114.4, 73.2, -3.2, "64.0%", "46.3%", "dn"),
 ("2024/25", 119.5, 119.1, 74.8, 0.4, "62.8%", "46.3%", ""),
 ("2025/26", 121.9, 121.1, 75.3, 0.8, "62.2%", "45.2%", ""),
 ("2026/27", 117.3, 122.9, 69.9, -5.6, "56.8%", "41.8%", "hl"),
]
for y, p, d, e, pm, stu, stut, flag in tbl:
    cls = "" if flag != "hl" else ' class="hl-row"'
    pmc = '<td class="dn">%+.1f</td>' % pm if pm < 0 else ('<td class="up">%+.1f</td>' % pm if pm > 0 else "<td>%.1f</td>" % pm)
    hist_rows += f"<tr{cls}><td>{'<b>'+y+'</b>' if flag=='hl' else y}</td>"
    for v in (p, d, e):
        hist_rows += f"<td>{'<b>'+str(v)+'</b>' if flag=='hl' else v}</td>"
    hist_rows += pmc
    for v in (stu, stut):
        hist_rows += f"<td>{'<b>'+v+'</b>' if flag=='hl' else v}</td></tr>\n"

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>97 棉花基本面全景 · 产需缺口第二年 · 机构口径之争</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;--red:#d9381e;--green:#0b8a5f;
      --blue:#1e66d6;--o1:#0072B2;--o2:#E69F00;--o3:#56B4E9;--o4:#CC79A7;--o5:#D55E00;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--ink);font:14px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:26px 16px 60px;}
.wrap{max-width:1240px;margin:0 auto;}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
h1{font-size:22px;line-height:1.4;margin-bottom:6px;color:#111827;}
.meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
h2{font-size:16.5px;margin:4px 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
h3{font-size:14px;margin:14px 0 8px;color:#374151;}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:14px;}
.kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
.kpi .num{font-size:20px;font-weight:700;}
.kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);} .kpi .num.blue{color:var(--blue);}
.kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
.chart{width:100%;height:400px;}
.chart.sm{height:300px;} .chart.mid{height:340px;}
table{width:100%;border-collapse:collapse;font-size:12.5px;}
th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);font-weight:600;white-space:nowrap;}
td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;}
tr.hl-row td{background:#eef6ff;}
.scroll{overflow-x:auto;}
.note{color:var(--sub);font-size:12px;margin-top:8px;}
.keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.8px;color:#17442f;margin:12px 0 4px;}
.warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.8px;color:#7c4a03;margin:12px 0 4px;}
.contra{background:#fdf1f1;border:1px solid #f2cfcf;border-radius:10px;padding:12px 16px;font-size:12.8px;color:#7c1f1f;margin:12px 0 4px;}
.dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
.hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
.contra ul{margin:8px 0 0 18px;} .contra li{margin-bottom:4px;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
<h1>97 · 棉花基本面全景：产需缺口第二年 · 库存去化与机构口径之争</h1>
<div class="meta">数据：USDA PSD（9/11 快照 + 9/20 API 交叉）、USDA WASDE 9 月、ICAC 9/1、CONAB 9/15、CAI、World Bank Pink Sheet（至 2026-08）、CFTC COT（至 09-01）｜as-of：2026-09-20｜单位：百万包（480 lb）或标注</div>
<div class="kpis">
  <div class="kpi"><div class="num dn">56.8%</div><div class="lab">全球库消比 26/27（10 年最低；全史 61 分位）</div></div>
  <div class="kpi"><div class="num dn">−5.6M 包</div><div class="lab">26/27 全球产需缺口（产量 117.3 vs 消费 122.9）</div></div>
  <div class="kpi"><div class="num up">95.7¢</div><div class="lab">Cotton A Index 8 月（全史 92.5 分位）</div></div>
  <div class="kpi"><div class="num up">133.1K</div><div class="lab">CFTC 棉花非商净多（1995 年以来新高）</div></div>
  <div class="kpi"><div class="num blue">±152万t</div><div class="lab">USDA 缺口 122 万t vs ICAC 盈余 30 万t</div></div>
</div>
<div class="keypoint"><b>一句话结论：</b>2026/27 全球棉花进入<b>产需缺口第二年</b>——消费连续两年站上 1.2 亿包、产量两连降，缺口 5.6M 包靠库存回补（全球连 3 年去库）；美棉减产 + 亚洲需求双旺使<b>库消比 62.2%→56.8%、近 10 年最低</b>。但<b>ICAC 同季预测却是盈余 +30 万吨</b>——机构方向相反是本季最大分歧。拥挤度上投机净多已创 31 年新高、价格全史 92 分位，<b>极值共振 = 双向高波动</b>。方向中性偏多、处分歧区。</div>
</div>

<div class="card">
<h2>一、全球总量平衡：缺口第二年，库存连续去化</h2>
<div id="c1" class="chart"></div>
<div class="note">全球皮棉产量 / 消费 / 期末库存（1000 480-lb 包，USDA PSD）。26/27 产量 117.3M 包为六年最低，消费 122.9M 连续第二年＞120M；产消缺口 5.6M 包由库存弥补。（悬停可见年度值）</div>
<div class="scroll" style="margin-top:12px;">
<table>
<thead><tr><th>市场年</th><th>产量(M)</th><th>消费(M)</th><th>期末库存(M)</th><th>产消差额(M)</th><th>库消比</th><th>库消(+出口)</th></tr></thead>
<tbody>
__HIST__
</tbody>
</table>
</div>
<div class="note">2026/27：期初 75.3 → 期末 69.9（去库 5.4M）；USDA 9 月 vs 8 月：产量 −0.31、期初 +0.51 → 期末仅 +0.17（↑至 69.86），USDA 自身也承认"缺口年但库存降幅有限"。上一轮同水位 58.4% 为 2020/21（疫情扰动年）。</div>
</div>

<div class="card">
<h2>二、库存水位：整体偏紧，但集中在中国"政策口袋"</h2>
<div id="c2" class="chart"></div>
<div class="note">三种口径：全口径 56.8%；剥离中国 43.5%；剥中印 45.7%。（副轴 = 期末库存 M 包）</div>
<div class="twocol" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px;">
<div><h3>库存地理 Top10（26/27，M 包）</h3><div id="c3" class="chart sm"></div></div>
<div><h3>美/中/印/巴 四强产量占比（%）</h3><div id="c4" class="chart sm"></div></div>
</div>
<div class="warn"><b>口径警示：</b>全球库存 53% 在中国（34.7/69.9M 包），而中国库存以<b>国储为主、释放由政策决定</b>（当前正轮出补现货）。市场化可贸易库存（剥中、含出口口径 STU≈28%）接近 2011 年以来低位。<b>注意：93 号已证伪"低库存=自动上涨"</b>——真正定价的是缺口方向 + 释放弹性，不是库存水位本身。糖系先例表明"政策口袋"可以长时间不释放、但也可以在窗口内快速平抑价格。</div>
</div>

<div class="card">
<h2>三、主产国全景：一家减产、两家增产、买方市场成型</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
<div><h3>26/27 产量 Top10（千包）</h3><div id="c5" class="chart mid"></div></div>
<div><h3>26/27 净贸易（M 包，红出绿进）</h3><div id="c6" class="chart mid"></div></div>
</div>
<div class="scroll" style="margin-top:10px;">
<table>
<thead><tr><th>国家</th><th>26/27 产量</th><th>25/26</th><th>产量Δ</th><th>26/27 消费</th><th>出口</th><th>进口</th><th>期末库存</th><th>格局</th></tr></thead>
<tbody>
<tr><td>美国</td><td>13.20</td><td>13.90</td><td class="dn">−0.70（−5%）</td><td>1.50</td><td>12.30</td><td>—</td><td>3.60</td><td class="hlb">减产至 6 年低 + 库存缩至 4 年低</td></tr>
<tr><td>中国</td><td>33.50</td><td>35.80</td><td class="dn">−2.30（−6%）</td><td>42.00</td><td>0.08</td><td>7.00</td><td>34.67</td><td>新疆调减 + 买买买补缺</td></tr>
<tr><td>印度</td><td>24.00</td><td>23.80</td><td class="up">+0.20（+1%）</td><td>26.50</td><td>1.50</td><td>3.00</td><td>10.32</td><td class="hl">由净出口转净进口（结构变化）</td></tr>
<tr><td>巴西</td><td>18.50</td><td>18.75</td><td class="dn">−0.25（−1%）</td><td>3.40</td><td>15.50</td><td>—</td><td>3.21</td><td class="hlg">产量纪录后微降，出口全球第一</td></tr>
<tr><td>巴基斯坦</td><td>5.00</td><td>5.30</td><td class="dn">−0.30</td><td>10.20</td><td>0.05</td><td>5.10</td><td>1.90</td><td>缺口扩大：进口 2.6 倍于自身产量</td></tr>
<tr><td>土耳其</td><td>2.40</td><td>3.05</td><td class="dn">−0.65（−21%）</td><td>6.80</td><td>0.60</td><td>5.00</td><td>1.15</td><td>严重依赖进口</td></tr>
<tr><td>乌兹别克</td><td>3.40</td><td>3.45</td><td>−0.05</td><td>4.00</td><td>0.00</td><td>0.25</td><td>1.38</td><td>自给转型</td></tr>
<tr><td>澳大利亚</td><td>3.00</td><td>4.50</td><td class="dn">−1.50（−33%）</td><td>—</td><td>4.50</td><td>—</td><td>2.47</td><td>水情转差，出口收缩 1/3</td></tr>
<tr><td>孟加拉</td><td>0.15</td><td>0.15</td><td>0</td><td>7.60</td><td>—</td><td>7.40</td><td>1.62</td><td class="hl">全球最大进口国之一</td></tr>
<tr><td>越南</td><td>0.00</td><td>0.00</td><td>0</td><td>8.20</td><td>—</td><td>8.20</td><td>1.03</td><td class="hl">加工枢纽、100% 进口</td></tr>
</tbody>
</table>
</div>
<div class="keypoint"><b>结构性要点：</b>① <b>贸易两端高度集中</b>——巴西+美国合计出口 27.8M 包、占全球出口 63%；越南+孟加拉+巴基斯坦+土耳其合计进口 25.7M 包、占全球 58%，四国自身产量合计不足 8M 包，<b>原料缺口 3 倍于本土供应</b>；② <b>印度从边际出口变边际进口</b>，25/26 进口创纪录（CAI 62 lac 包），26/27 进口 3.0M 包确立净进口结构——需求端最确定增量；③ 美国 26/27 出口销售累计同比 +19%（9/4 周净销售 7.39 万包），但装运低于目标，进度仍在消化。</div>
</div>

<div class="card">
<h2>四、价格与持仓：历史极值共振</h2>
<div id="c7" class="chart"></div>
<div class="note">Cotton A Index（$/kg，月度，1960–2026-08）：8 月 2.11 $/kg ≈ 95.7¢/lb，全史 92.5 分位、近 10 年 76.7 分位。历史峰值 5.06（2011 中国补库潮）。</div>
<div id="c8" class="chart"></div>
<div class="note">ICE 棉花 #2 非商业净多（CFTC，1995–2026-09-01）：<b>133,147 手 = 31 年历史新高</b>（超越 2017-03 的 132,318）；12 周净增 +53,960（+68%）；总持仓 543K 亦处高分位。9/8 当周对冲基金净多 −13,118 手（已开始获利离场）。</div>
<div class="scroll" style="margin-top:12px;">
<table>
<thead><tr><th>价格/持仓指标</th><th>最新</th><th>口径与日期</th></tr></thead>
<tbody>
<tr><td>ICE 棉花 12 月合约</td><td class="up">84.36¢（9/16）；8/31 摸 93.74 合约新高 → 9 月回撤 −9.4%；9/18 82.17</td><td>ICE，as-of 09/18</td></tr>
<tr><td>Cotton A Index</td><td class="up">95.7¢/lb（8 月均值）</td><td>Cotlook，全史 92.5 分位</td></tr>
<tr><td>郑棉主力 CF2701</td><td class="dn">15,750 元/t（9/18）</td><td>较 5 月高点 1.70 万回落；现货 3128B ≈18,180</td></tr>
<tr><td>美棉 7 市场现货均价</td><td class="dn">76.17¢（9/17，周 −201 点）</td><td>USDA，高于去年同期 62.98</td></tr>
<tr><td>USDA 美棉农场均价 26/27</td><td class="up">78¢（9 月 +3¢：75→78）</td><td>WASDE 9/11</td></tr>
<tr><td>CFTC 棉花非商净多</td><td class="up">133,147 手（09-01）</td><td>1995 年以来历史最高</td></tr>
<tr><td>全球库消比 26/27</td><td class="dn">56.8%</td><td>近 10 年最低</td></tr>
</tbody>
</table>
</div>
</div>

<div class="card">
<h2>五、机构口径之争：USDA 缺口 vs ICAC 盈余</h2>
<div class="scroll">
<table>
<thead><tr><th>口径</th><th>产量</th><th>消费</th><th>差额</th><th>期末库存</th><th>库消比</th><th>as-of</th></tr></thead>
<tbody>
<tr><td><b>USDA WASDE</b></td><td>117.3M 包（25.54Mt）</td><td>122.9M 包（26.76Mt）</td><td class="dn"><b>缺口 5.6M（≈122万t）</b></td><td>69.9M（15.21Mt）</td><td class="dn">56.8%</td><td>09-11</td></tr>
<tr><td><b>ICAC</b></td><td>26.2Mt</td><td>25.9Mt</td><td class="up"><b>盈余 +30万t</b></td><td>18.23Mt（+30万t）</td><td class="up">70%</td><td>09-01</td></tr>
</tbody>
</table>
</div>
<div class="contra">
<b>为什么方向相反？（四个差离点）</b>
<ul>
<li><b>消费校准：</b>USDA 消费 122.9M 包 vs ICAC ≈118–119M（25.9Mt×4.68 包/t）——对印度/中国/越南加工需求的上修力度不同。USDA 在中国 42.0、印度 26.5、越南 8.2、巴基斯坦 10.2M 包的高消费假设，ICAC 未完全跟进。</li>
<li><b>中国产量口径：</b>USDA 26/27 中国 33.5M 包（≈729 万t，−6%）；ICAC 强调新疆天气风险与储备轮出后<b>补库</b>或上调中国进口——上修进口即放大缺口方向。</li>
<li><b>ICAC 自带的季节性下修机制：</b>ICAC 产量初值历史上逐月下调约 10 万t/月（"正常季节性回落"），其 26.2Mt 将向 26.0–26.1 收敛，与 USDA 差距仍约 70–90 万t级。</li>
<li><b>统计时点与期初库存定义：</b>两套体系市场年拼接、数字不可直接相减（USDA 包 vs ICAC 吨、期初定义不同）。</li>
</ul>
<b style="color:#7c1f1f">判断：</b>USDA 的"全球缺口"是主流叙事（美减、需求强、去库存三年），ICAC 的"微弱盈余"是保守消费 + 高产量底线的逆向视角。<b>若新疆减产 7–9% 兑现、印度/越南需求韧性延续，ICAC 的盈余大概率在 10 月起向缺口收敛；反之若巴西/澳超预期丰产（CONAB 4.16Mt）、中国消费被证伪，USDA 的 122.9M 也会被下修。</b>这是 10 月 WASDE + 11 月 ICAC 的必看焦点。
</div>
</div>

<div class="card">
<h2>六、vintage 追踪表（USDA 预测 vs 行业最新指引）</h2>
<div class="scroll">
<table>
<thead><tr><th>主体</th><th>USDA（26/27）</th><th>行业最新</th><th>偏离判断</th></tr></thead>
<tbody>
<tr><td><b>全球</b></td><td>缺 5.6M 包</td><td>ICAC 盈 +30万t</td><td class="hlb">方向相反（见上章）</td></tr>
<tr><td><b>美国</b></td><td>产量 13.2M、单产 776lb、库 3.6M、库销比 26.1%、价格 78¢</td><td>NASS 优良率 36%（9/13，去年同期 52%、5 年均 44%）；干旱区 59%；现货 76.17¢（9/17）</td><td class="hl">单产/优良率系统性低于近年——USDA 产量仍偏乐观 2–3%，天气风险未完全计入</td></tr>
<tr><td><b>中国</b></td><td>产量 33.5M（≈729 万t，−6%）</td><td>BCO 9 月：742 万t（−36 万t）上调 16 万t；新疆面积实际减 2.4%（政策目标 −10%）</td><td class="hl">USDA 偏保守：面积减幅远低于政策目标，产量上修方向</td></tr>
<tr><td><b>印度</b></td><td>产量 24.0M（≈5.2Mt）、进口 3.0M</td><td>CAI：25/26 压榨 33.9M lac 包（≈5.8Mt）创纪录上调；26/27 进口 62 lac 包创纪录后回落</td><td class="hl">USDA 印度产量口径偏低约 0.5–0.6Mt；进口结构（净进口）方向一致</td></tr>
<tr><td><b>巴西</b></td><td>产量 4.03Mt（9 月 +1.4%）</td><td>CONAB 9/15：4.157Mt（25/26 4.144 创纪录）</td><td>USDA 略保守（−3%）但方向一致</td></tr>
<tr><td><b>巴基斯坦</b></td><td>产量 5.0M、进口 5.1M</td><td>ICAC：产量 1.10Mt（↓4%）、进口依赖扩大</td><td>一致</td></tr>
<tr><td><b>澳大利亚</b></td><td>产量 3.0M、出口 4.5M</td><td>ICAC：面积减 → 出口收缩</td><td>一致（−33%）</td></tr>
</tbody>
</table>
</div>
<div class="note">跨机构口径差异主线：ICAC 用轧花/原棉口径、USDA 用皮棉 480-lb 包、CAI 用 170kg 包。换算：1 包 480lb ≈ 217.7kg；1Mt ≈ 4.59M 包（USDA）或 ICAC 约 4.68M 包口径。绝对水平不可直接比，方向与变化才可比。</div>
</div>

<div class="card">
<h2>七、中国因素：储备轮出、新疆调减、进口配额</h2>
<ul style="margin:0 0 0 18px;font-size:13px;line-height:1.8;">
<li><b>储备轮出</b>：7/20 启动、日均约 8,000t，至 9/11 累计 32.1 万t、成交率 99.92%；节奏推算总轮出 40 万t+，最晚 11 月收官——<b>短期国内不缺货、加价幅度已收窄</b>；但轮出后必然补库，是中周期进口或涨价支撑（ICAC 已提示上调中国进口）。</li>
<li><b>新疆调减"未兑现"</b>：政策目标 3,600 万亩（−10%+），调研显示全国面积实际仅 −2.4%（补种/套种对冲）——<b>政策目标 vs 现实偏差是本季中国供应最大的预期差</b>；高温干旱 + 调减使新疆总产预期 −3.5%~−9%（机构分歧大）。</li>
<li><b>进口配额</b>：2026 关税配额 89.4 万t + 滑准税加工贸易 30 万t；1–7 月进口 102.6 万t（巴西 56、澳 15.3、美 11.45）——<b>美棉份额降至十年低位 ~11%（7 月单月 7%）</b>，澳 7 月占比 60% 跃居第一，进口来源加速多元化。</li>
<li><b>内外价差</b>：CCIndex3128B ≈18,180 元/t、郑棉 15,750 元/t、CotlookA 折 1% 关税 ≈16,023 元/t → 进口利润窗口打开，内外联动增强。</li>
<li><b>需求端</b>：8 月纺织纱线出口 +2.4%、服装出口 +12.3%；但"金九银十"开机未升温、订单碎片化，旺季证伪风险仍在。</li>
</ul>
</div>

<div class="card">
<h2>八、结论与置信度</h2>
<div class="keypoint" style="background:#f4f6fb;border-color:#d5e2f7;color:#1e3a6e;">
<b>[前提校验]</b> 缺口叙事依赖三前提：USDA 消费 122.9M 包、美/澳双减产、新疆减产 6%。任一被证伪（巴西 4.16Mt+ 超预期、中国面积超预期、消费不及 122M）都会收窄缺口。<br>
<b>[数据依据]</b> 库消比 56.8%（10 年最低）、全球连三年去库（−5.4/−5.5M）；剥中国含出口口径 ≈28% 逼近历史低位；价格 92.5 分位；CFTC 净多历史新高。三项极值共振为近十年未见。<br>
<b>[客观对比]</b> USDA（缺 5.6M）vs ICAC（盈 0.3Mt）方向相反，差异集中在消费校准与中国产量口径；巴西 CONAB 与 USDA 同向但绝对水平更高（4.16 vs 4.03Mt）、印度 CAI 口径显著高于 USDA（5.8 vs 5.2Mt）→<b>风险偏侧：供应或未被低估、缺口或被高估</b>……但美棉单产/优良率的系统性偏差又指向相反方向（USDA 美棉偏乐观）。双向风险均等存在。<br>
<b>[结论·置信度]</b> <b>方向中性偏多（底部支撑明确：去库存 + 需求韧性强），但当前处分歧区、且投机仓位与价格同处历史极值</b>（置信度：中）。9 月已回撤 −9.4%，追高性价比差；回调至缺口平衡区（A 指数 88–92¢ / ICE 78–82¢）且 CFTC 拥挤度回落后的多单窗口更优。关键节点：<b>10 月 WASDE（单产终值）、10/1 ICAC 修正、11 月美棉收获与植棉结束、中美对等降税框架</b>。
</div>
<div class="dis">本报告为数据研究，不构成投资建议。机构数字均标注来源与 as-of；USDA/ICAC 为预测值，历史规律提示初始预测逐月下修。跨机构绝对水平不可比，请以方向与变化为准。</div>
</div>

</div>
<script>
const D = __DATA__;
const P = ['#0072B2','#E69F00','#56B4E9','#CC79A7','#D55E00','#000000'];
const RED='#d9381e', GREEN='#0b8a5f', GREY='#9aa4af';
const AX = {textStyle:{color:'#6b7280'},nameTextStyle:{color:'#6b7280'}};
function mk(id, opt){const el=document.getElementById(id); const c=echarts.init(el); c.setOption(opt); return c;}
const charts = {};
charts.c1 = mk('c1',{backgroundColor:'transparent',tooltip:{trigger:'axis'},legend:{data:['产量','消费','期末库存'],top:0,textStyle:{color:'#374151'}},
 grid:{left:55,right:35,top:40,bottom:30},
 xAxis:{type:'category',data:D.prod.map(x=>x[0]),...AX},
 yAxis:{type:'value',axisLabel:{formatter:v=>v/1000+'M'},...AX},
 series:[
  {name:'产量',type:'line',smooth:true,data:D.prod.map(x=>x[1]),lineStyle:{width:2,color:P[0]},itemStyle:{color:P[0]},symbolSize:4},
  {name:'消费',type:'line',smooth:true,data:D.dom.map(x=>x[1]),lineStyle:{width:2,color:P[1]},itemStyle:{color:P[1]},symbolSize:4},
  {name:'期末库存',type:'line',smooth:true,data:D.end.map(x=>x[1]),lineStyle:{width:2,color:P[2]},itemStyle:{color:P[2]},symbolSize:4}]});

charts.c2 = mk('c2',{backgroundColor:'transparent',tooltip:{trigger:'axis',valueFormatter:v=>(v==null?'':(v<400?v+'%':(v/1000).toFixed(1)+'M'))},legend:{data:['全球','剥中国','剥中印','期末库存'],top:0,textStyle:{color:'#374151'}},
 grid:{left:50,right:50,top:40,bottom:30},
 xAxis:{type:'category',data:D.stu.map(x=>x[0]),...AX},
 yAxis:[{type:'value',axisLabel:{formatter:'{value}%'},...AX},{type:'value',axisLabel:{formatter:v=>(v/1000)+'M'},splitLine:{show:false},...AX}],
 series:[
  {name:'全球',type:'line',smooth:true,data:D.stu.map(x=>x[1]),lineStyle:{width:2.5,color:P[0]},itemStyle:{color:P[0]},symbolSize:4},
  {name:'剥中国',type:'line',smooth:true,data:D.excn.map(x=>x[1]),lineStyle:{width:2,color:P[1],type:'dashed'},itemStyle:{color:P[1]},symbol:'triangle',symbolSize:6},
  {name:'剥中印',type:'line',smooth:true,data:D.exc2.map(x=>x[1]),lineStyle:{width:2,color:P[4],type:'dotted'},itemStyle:{color:P[4]},symbol:'diamond',symbolSize:6},
  {name:'期末库存',type:'bar',data:D.end.map(x=>[x[0],x[1]]),barWidth:'42%',itemStyle:{color:'#999999',opacity:.22},yAxisIndex:1}]});

charts.c3 = mk('c3',{backgroundColor:'transparent',tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v+'M 包'},
 grid:{left:120,right:25,top:6,bottom:22},xAxis:{type:'value',...AX},yAxis:{type:'category',inverse:true,data:D.rk_s.map(x=>x.name),...AX},
 series:[{type:'bar',data:D.rk_s.map(x=>x.val/1000),barWidth:'58%',itemStyle:{color:function(p){return D.rk_s[p.dataIndex][0]==='China'?P[4]:P[0]}}}]});

charts.c4 = mk('c4',{backgroundColor:'transparent',tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},legend:{data:['美国','中国','印度','巴西'],top:0,textStyle:{color:'#374151'}},
 grid:{left:50,right:25,top:40,bottom:25},xAxis:{type:'category',data:D.share.map(x=>x[0]),...AX},yAxis:{type:'value',axisLabel:{formatter:'{value}%'},...AX},
 series:[
  {name:'美国',type:'line',smooth:true,stack:'s',data:D.share.map(x=>x[1]),areaStyle:{opacity:.35},lineStyle:{width:1.5,color:P[0]},itemStyle:{color:P[0]},symbolSize:3},
  {name:'中国',type:'line',smooth:true,stack:'s',data:D.share.map(x=>x[2]),areaStyle:{opacity:.45},lineStyle:{width:1.5,color:P[1]},itemStyle:{color:P[1]},symbolSize:3},
  {name:'印度',type:'line',smooth:true,stack:'s',data:D.share.map(x=>x[3]),areaStyle:{opacity:.55},lineStyle:{width:1.5,color:P[2]},itemStyle:{color:P[2]},symbolSize:3},
  {name:'巴西',type:'line',smooth:true,stack:'s',data:D.share.map(x=>x[4]),areaStyle:{opacity:.65},lineStyle:{width:1.5,color:P[4]},itemStyle:{color:P[4]},symbolSize:3}]});

charts.c5 = mk('c5',{backgroundColor:'transparent',tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v+'k 包'},
 grid:{left:100,right:30,top:6,bottom:22},xAxis:{type:'value',...AX},yAxis:{type:'category',inverse:true,data:D.rk_p.map(x=>x.name),...AX},
 series:[{type:'bar',data:D.rk_p.map(x=>x.val/1000),barWidth:'58%',itemStyle:{color:function(p){return p.dataIndex<3?P[0]:GREY}}}]});

// c6 净贸易
const nt = D.net_trade;
charts.c6 = mk('c6',{backgroundColor:'transparent',tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v+'M 包'},
 grid:{left:100,right:30,top:6,bottom:22},xAxis:{type:'value',...AX},yAxis:{type:'category',inverse:true,data:nt.map(x=>x[0]),...AX},
 series:[{type:'bar',data:nt.map(x=>x[1]),barWidth:'58%',itemStyle:{color:function(p){return p.value<0?P[0]:(p.value>0?P[4]:GREY)}}}]});

charts.c7 = mk('c7',{backgroundColor:'transparent',tooltip:{trigger:'axis',valueFormatter:v=>v+' $/kg'},legend:{data:['Cotton A Index'],top:0,textStyle:{color:'#374151'}},
 grid:{left:50,right:30,top:36,bottom:30},xAxis:{type:'category',data:D.wb_x,...AX},yAxis:{type:'value',...AX},
 series:[{name:'Cotton A Index',type:'line',data:D.wb_y,smooth:true,showSymbol:false,lineStyle:{width:1.5,color:P[0]},areaStyle:{opacity:.1,color:P[0]},itemStyle:{color:P[0]},
  markPoint:{data:[{type:'max',name:'历史峰值',symbolSize:34,itemStyle:{color:RED},label:{color:'#fff'}}]}}]});

charts.c8 = mk('c8',{backgroundColor:'transparent',tooltip:{trigger:'axis',valueFormatter:v=>v.toLocaleString()+' 手'},legend:{data:['非商业净多'],top:0,textStyle:{color:'#374151'}},
 grid:{left:60,right:30,top:36,bottom:30},xAxis:{type:'category',data:D.cot_x,...AX},yAxis:{type:'value',...AX},
 series:[{name:'非商业净多',type:'line',data:D.cot_y,showSymbol:false,lineStyle:{width:1.6,color:P[1]},areaStyle:{opacity:.14,color:P[1]},itemStyle:{color:P[1]},
  markLine:{symbol:'none',data:[{yAxis:D.stats.cot_last,name:'当前 133,147',label:{formatter:'当前 '+D.stats.cot_last.toLocaleString(),color:RED,position:'end'},lineStyle:{color:RED,type:'dashed',width:1.4}}]}}]});

window.addEventListener('resize',()=>{Object.values(charts).forEach(c=>c.resize());});
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", DATA_JS).replace("__HIST__", hist_rows)

out_dir = os.path.join(ROOT, "reports", "97_棉花基本面全景_20260920")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "index.html")
open(out, "w", encoding="utf-8").write(HTML)
print("WROTE", out, len(HTML), "bytes")

# 语法检查（无头验证 echarts 初始化前 DOM 存在性由浏览器处理，这里仅静态检查关键 token）
assert DATA_JS in HTML and "c8" in HTML and "markLine" in HTML
print("OK")