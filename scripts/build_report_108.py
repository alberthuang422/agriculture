# -*- coding: utf-8 -*-
"""生成 108 号报告: 白糖历史牛市时间线 + 周K驱动标注"""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'reports', '108_白糖历史牛市时间线_周线驱动标注', 'index.html')

# ---- 数据 ----
wb = json.load(open(os.path.join(ROOT,'data','price','sugar','wb_isa_world_monthly_clb_1960_2024.json'), encoding='utf-8'))
weekly = []
with open(os.path.join(ROOT,'data','price','sugar','sb_price_weekly.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        weekly.append([r['time'], float(r['open']), float(r['close']), float(r['low']), float(r['high'])])
ev = json.load(open(os.path.join(ROOT,'data','price','sugar','sugar_bull_events.json'), encoding='utf-8'))
fund = json.load(open(os.path.join(ROOT,'data','price','sugar','sugar_bull_fundamentals.json'), encoding='utf-8'))

PA, PB = ev['panelA'], ev['panelB']

# 面板A x 轴: '1963M11' -> '1963-11'
wb_x = [k.replace('M','-') for k,_ in wb]
wb_y = [v for _,v in wb]

KIND_CN = dict(start='起点/底部', driver='驱动事件', peak='顶部', end='终结/崩塌', now='当前')
KIND_COLOR = dict(start='#56B4E9', driver='#E69F00', peak='#D55E00', end='#8b93a1', now='#CC79A7')
KIND_SYM = dict(start=('triangle',180), driver=('circle',0), peak=('triangle',0), end=('diamond',0), now=('pin',0))

def mp_panelA():
    out=[]
    for i,e in enumerate(PA,1):
        sym,rot = KIND_SYM[e['kind']]
        xi = e['x'].replace('M','-')
        out.append(dict(name=str(i), coord=[xi, e['y']], value=str(i),
            symbol=sym, symbolRotate=rot, symbolSize=21,
            itemStyle=dict(color=KIND_COLOR[e['kind']], borderColor='#14171c', borderWidth=1.5),
            label=dict(show=True, formatter=str(i), color='#14171c', fontSize=10, fontWeight=700,
                       position='inside'),
            _t=e['t'], _d=e['d'], _kind=e['kind'], _bull=e['bull']))
    return out

def mp_panelB():
    """密集区自动错开 label 位置(上/下交替), 避免编号重叠"""
    wk_idx = {r[0]: i for i, r in enumerate(weekly)}
    out=[]; last_i=-99; flip=0
    for i,e in enumerate(PB,1):
        sym,rot = KIND_SYM[e['kind']]
        ci = wk_idx.get(e['wk_date'], -1)
        if ci - last_i < 7:            # 与前一个标注相隔不足7周 -> 错开
            flip ^= 1
            pos = 'top' if flip else 'bottom'
        else:
            pos = 'inside'; flip = 0
        last_i = ci
        out.append(dict(name=str(i), coord=[e['wk_date'], e['y']], value=str(i),
            symbol=sym, symbolRotate=rot, symbolSize=21,
            itemStyle=dict(color=KIND_COLOR[e['kind']], borderColor='#14171c', borderWidth=1.5),
            label=dict(show=True, formatter=str(i),
                       color=('#e8eaee' if pos!='inside' else '#14171c'),
                       fontSize=10, fontWeight=700, position=pos),
            _t=e['t'], _d=e['d'], _kind=e['kind'], _date=e['date'], _wk=e['wk_date'], _y=e['y']))
    return out

MPA, MPB = mp_panelA(), mp_panelB()

# 牛市区间着色 (面板A)
BULL_A = [
    ('1962-12','1963-11','I · 1963'),
    ('1971-09','1974-11','II · 1972-74'),
    ('1979-01','1980-10','III · 1979-80'),
    ('1985-06','1990-03','IV · 1985-90'),
    ('1994-01','1995-01','V · 1994-95'),
    ('2004-01','2006-02','VI · 2005-06'),
    ('2008-12','2011-01','VII · 2009-11'),
]
BAND_A = [dict(name=t, xAxis=[a,b], itemStyle=dict(color='rgba(230,159,0,0.07)')) for a,b,t in BULL_A]

BULL_B = [
    ('2015-08-28','2016-10-07','VIII · 2015-16 厄尔尼诺牛'),
    ('2020-05-01','2021-11-19','IX · 2020-21 拉尼娜牛'),
    ('2022-10-07','2023-11-10','X · 2022-23 印度零出口牛'),
    ('2026-04-17','2026-09-25','XI · 2025-26 进行中'),
]
BAND_B = [dict(name=t, xAxis=[a,b], itemStyle=dict(color='rgba(230,159,0,0.07)')) for a,b,t in BULL_B]

# ---- 事件表 HTML ----
def ev_table(events, panel):
    rows=[]
    for i,e in enumerate(events,1):
        c = KIND_COLOR[e['kind']]
        if panel=='A':
            date = e['x'].replace('M','-'); extra = e.get('bull','')
        else:
            date = e['date']; extra = f"锚定周 {e['wk_date']} · {e['y']:.2f}¢"
        rows.append(
            f'<tr><td class="num"><span class="badge" style="background:{c}">{i}</span></td>'
            f'<td class="nowrap">{date}</td>'
            f'<td><span class="ktag" style="border-color:{c};color:{c}">{KIND_CN[e["kind"]]}</span></td>'
            f'<td><b>{e["t"]}</b></td><td class="dim sm">{e["d"]}</td></tr>')
    return '\n'.join(rows)

# ---- 牛市汇总表 ----
BULLS = [
 dict(n='I',name='1963 古巴危机',src='ISA月度',lo='1962-01 · 2.11¢',hi='1963-11 · 11.53¢',chg='+9.42¢ (×5.5)',dur='~22个月',
      drv='古巴革命+美国禁运→最大出口国退出自由市场；苏联溢价收购不转售；欧洲甜菜寒害歉收；进口国恐慌性补库',
      fun='全球产销差为正(1963年+5.3 Mt)——涨价源于<b>自由市场可贸易供给</b>崩塌，而非全球实体短缺'),
 dict(n='II',name='1972-74 古典大牛市',src='ISA月度',lo='1971-09 · 3.99¢',hi='1974-11 · 56.14¢',chg='+52.15¢ (×14)',dur='38个月',
      drv='苏联甜菜歉收转大规模净进口；欧洲甜菜黄化病毒单产-30%；石油危机后油元国家抢购保值；菲/巴等出口国限制出口；低库消比(1973年18.2%)',
      fun='MY1973产销差 -1.15 Mt、库消比18.2%(战后低位)；历史最高价，至今未被超越'),
 dict(n='III',name='1979-80 六国减产',src='ISA月度',lo='1979-01 · 7.57¢',hi='1980-10 · 40.55¢',chg='+32.98¢ (×5.4)',dur='21个月',
      drv='印度季风不足+巴西干旱+古巴锈病(波及40%作物)+泰国旱灾+苏联甜菜缺口+西班牙减产，六国合计33.9→28.1 Mt；ISA取消出口配额未能压价',
      fun='MY1979产销差 -6.46 Mt(本表历史最深缺口之一)、库消比22.5%→19.3%'),
 dict(n='IV',name='1985-90 长牛',src='ISA月度',lo='1985-06 · 2.78¢',hi='1990-03 · 15.36¢',chg='+12.58¢ (×5.5)',dur='57个月',
      drv='历史绝对底部后的五年慢牛：1985/86-1989/90多季短缺；1988年美国大旱(密西西比流域)+拉尼娜；苏联进口需求旺盛；巴西乙醇计划分流甘蔗',
      fun='FAO称1988-97为糖价"黄金时代"(12-13¢平台)；本表产销差多数年份为正——支撑来自需求侧(苏联)与乙醇结构性分流'),
 dict(n='V',name='1994-95',src='ISA月度',lo='1994-01 · 10.30¢',hi='1995-01 · 14.76¢',chg='+4.46¢ (+43%)',dur='12个月',
      drv='欧盟甜菜面积下调+巴西中南部干旱；1994/95季全球短缺；FAO确认ISA日价1995-01见顶15.45¢/lb(五年高点)',
      fun='1995-08/09随1995/96大增产预期急跌；1998亚洲金融危机+巴西放量→1999年均6.61¢'),
 dict(n='VI',name='2005-06 乙醇牛I',src='ISA月度',lo='2004-01 · 5.81¢',hi='2006-02 · 18.04¢',chg='+12.23¢ (×3.1)',dur='25个月',
      drv='印度减产转净进口；泰国旱灾；巴西降雨拖累压榨；原油上行(60美元+)首次确立"糖-乙醇-原油"联动框架',
      fun='USDA全球产销差为正(2006年+13.4 Mt)——边际定价来自印度进口需求与巴西出口能力，而非全球总量'),
 dict(n='VII',name='2009-11 印度季风牛',src='ISA月度',lo='2008-12 · 11.75¢',hi='2011-01 · 29.61¢',chg='+17.86¢ (×2.5)',dur='25个月',
      drv='2009印度季风1972年来最弱→印度转为最大进口国(6-7 Mt)；2010巴西中南部降雨拖累压榨；2010底澳大利亚昆士兰洪水(第三大出口国)；油价回升',
      fun='MY2009产销差 -1.28 Mt、库消比17.9%；29.61¢为1980年后30年次高'),
 dict(n='VIII',name='2015-16 厄尔尼诺牛',src='ICE期货',lo='2015-08-24 · 10.13¢',hi='2016-10-06 · 23.90¢',chg='+13.77¢ (×2.4)',dur='~13.5个月',
      drv='超强厄尔尼诺；印度连续两季减产(25.1→20.3 Mt)+泰国旱灾；中国保障措施立案(2016-09-22)；空头拥挤后回补(9月单月+24%)',
      fun='ISO口径2015/16短缺-6.4 Mt(USDA表MY2015 -4.21 Mt)；顶后中国配外95%关税(2017-05-22)反噬需求→2018熊底9.83¢'),
 dict(n='IX',name='2020-21 拉尼娜牛',src='ICE期货',lo='2020-04-28 · 9.05¢',hi='2021-11-18 · 20.69¢',chg='+11.64¢ (×2.3)',dur='~18.6个月',
      drv='疫情底(WTI负油价)后反转：拉尼娜→巴西中南部2021大旱+6-7月霜冻(2021/22季减产~9 Mt)；泰国减产(8.3→5.7 Mt)；油价回升强化乙醇分流',
      fun='USDA产销差两年均为正——牛市由巴西出口能力收缩(天气)定价，而非全球总量短缺'),
 dict(n='X',name='2022-23 印度零出口牛',src='ICE期货',lo='2022-10-03 · 17.36¢',hi='2023-11-07 · 28.14¢(盘中)',chg='+10.78¢ (+62%)',dur='13个月',
      drv='印度2022/23减产(36.5→32.9 Mt)+出口限额10→6.1 Mt→2023/24季零出口(四年首次)；泰国减产预期；巴西桑托斯港挤兑(排队30天+，白糖升水180美元/吨+)',
      fun='CFTC净多峰值+279,528手(2023-04-25)早于价格顶6个月；顶部为"物流瓶颈放大基本面紧张"，2023-12单月崩塌-24.3%'),
 dict(n='XI',name='2025-26 进行中',src='ICE期货',lo='2026-04-17 · 13.22¢',hi='2026-09-10 · 18.88¢',chg='+5.66¢ (+43%)',dur='5个月(至今)',
      drv='巴西E30掺混令(2025-08)→糖醇比崩塌51.0→42.5%、中南部产糖-12.4%；印度2026-05出口禁令(至9/30)+转进口(授权1 Mt)；季风-40%为11年最弱；强厄尔尼诺(ONI MJJ +1.39)；CFTC从纪录净空(-253,592手,2026-02-17)翻多(+158,186手,2026-09-08)',
      fun='ISO首版(Aug-2026) 2026/27缺口-0.234 Mt为"地板数"；Covrig -0.3、StoneX -1.7、Green Pool -3.3 Mt——按vintage纪律，缺口大概率上修'),
]
def bull_rows():
    out=[]
    for b in BULLS:
        out.append(f'''<tr><td><b>{b['n']}</b></td><td><b>{b['name']}</b><div class="dim sm">{b['src']}</div></td>
<td class="nowrap">{b['lo']}</td><td class="nowrap">{b['hi']}</td><td class="num up">{b['chg']}</td>
<td class="nowrap">{b['dur']}</td><td class="sm">{b['drv']}</td><td class="dim sm">{b['fun']}</td></tr>''')
    return '\n'.join(out)

# ---- 基本面表 ----
def fund_rows():
    out=[]
    for bull, ys in fund.items():
        cells=[]
        for y in ys:
            pm=y['prodminususe']; cls='up' if pm<0 else 'down'
            # 注: 产销差为负=短缺(利多,红), 正=过剩(绿) — 中国惯例红涨绿跌语义迁移
            cells.append(f"MY{y['my']}: <span class='{cls}'>{pm:+.2f}</span> · S/U {y['s2u']}%")
        out.append(f"<tr><td><b>{bull}</b></td><td class='sm'>{' ｜ '.join(cells)}</td></tr>")
    return '\n'.join(out)

HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>108号 · 白糖历史牛市时间线（1963-2026）与周K驱动标注</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>:root{
  --bg:#14171c; --card:#1c2028; --card2:#232933; --line:#303642;
  --tx:#e8eaee; --dim:#9aa3b2; --dim2:#7c8698;
  --accent:#4c9be8; --warn:#e8a33d;
  --oi-blue:#56B4E9; --oi-orange:#E69F00; --oi-sky:#8fd0f5;
  --oi-pink:#CC79A7; --oi-verm:#F0793B; --oi-yellow:#F0E442;
  --up:#ff6b6b; --down:#3ddc97;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--tx);
  font:15px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:1240px;margin:0 auto;padding:34px 22px 70px;}
h1{font-size:26px;margin:0 0 8px;line-height:1.4;}
h2{font-size:20px;margin:38px 0 6px;padding-top:22px;border-top:1px solid var(--line);}
h3{font-size:16.5px;margin:24px 0 8px;color:#dfe4ec;}
p{margin:11px 0;font-size:14.2px;line-height:1.85;}
a{color:var(--accent);text-decoration:none;}
.lede{color:var(--dim);font-size:13px;margin:6px 0 18px;}
.meta{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 8px;}
.meta span{background:var(--card2);border:1px solid var(--line);border-radius:8px;
  padding:5px 11px;font-size:11.8px;color:var(--dim);}
.sec{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:20px 24px 14px;margin:18px 0;}
.kicker{background:linear-gradient(90deg,#232933,#1c2028);border:1px solid var(--line);
  border-left:4px solid var(--oi-orange);border-radius:10px;padding:15px 20px;margin:16px 0;
  font-size:14.5px;line-height:1.8;}
.kicker b{color:#fff;}
.note{color:var(--dim);font-size:13px;border-left:3px solid var(--accent);
  padding-left:13px;margin:14px 2px;line-height:1.75;}
.note.b{border-left-color:var(--warn);}
.warn{background:#2a2218;border:1px solid #5c4a22;border-radius:9px;padding:12px 15px;
  font-size:13.2px;color:#e6d3ab;margin:14px 0;line-height:1.75;}
.warn b{color:#ffd79a;}
table{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:13.2px;}
th{text-align:left;background:var(--card2);color:var(--dim);font-weight:600;
  padding:9px 10px;border-bottom:2px solid var(--line);white-space:nowrap;font-size:12.6px;}
td{padding:8px 10px;border-bottom:1px solid #2a2f3a;vertical-align:top;}
tr:hover td{background:#20242e;}
.num{font-variant-numeric:tabular-nums;text-align:right;}
.nowrap{white-space:nowrap;}
.up{color:var(--up);font-weight:600;}
.down{color:var(--down);font-weight:600;}
.dim{color:var(--dim2);}
.sm{font-size:12.2px;}
.chart{width:100%;height:520px;margin:8px 0 4px;}
.chart.tall{height:620px;}
.src{color:var(--dim2);font-size:11.6px;margin:2px 2px 16px;line-height:1.65;}
.badge{display:inline-block;min-width:20px;height:20px;line-height:20px;border-radius:10px;
  color:#14171c;font-weight:700;font-size:11.5px;text-align:center;padding:0 4px;}
.ktag{display:inline-block;border:1px solid;border-radius:6px;padding:1px 8px;font-size:11.5px;white-space:nowrap;}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0 4px;font-size:12.5px;color:var(--dim);}
.legend .it{display:flex;align-items:center;gap:6px;}
.legend .sw{width:14px;height:14px;border-radius:3px;display:inline-block;}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:11px;margin:14px 0;}
.card{background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:13px 15px;}
.card .k{color:var(--dim2);font-size:11.4px;}
.card .v{font-size:21px;font-weight:700;font-variant-numeric:tabular-nums;margin:3px 0 1px;}
.card .d{font-size:11.6px;color:var(--dim);line-height:1.55;}
.scrollx{overflow-x:auto;}
</style>
</head>
<body><div class="wrap">

<h1>108号 · 白糖历史牛市时间线（1963-2026）与周K驱动标注</h1>
<div class="lede">11轮牛市全梳理 · 驱动因素按时间线标注在价格图上 · 面板A为世行ISA月度（1960-2024），面板B为ICE No.11周K蜡烛（2011-12 ~ 2026-09，本地日线按ISO周聚合）</div>
<div class="meta">
  <span>编制日期: 2026-09-28</span><span>价格单位: 美分/磅 (¢/lb)</span>
  <span>面板A: 世界银行 Pink Sheet · ISA日价月均 (1960M01-2024M12, 780点)</span>
  <span>面板B: ICE No.11 连续日线 → 周线 771根 (2011-12-23 ~ 2026-09-25)</span>
  <span>持仓: CFTC Legacy Futures-Only 非商业净持仓 (1986-2026)</span>
</div>

<div class="kicker"><b>核心结论:</b> 1963年以来白糖共出现 <b>11轮可辨识牛市</b>。驱动因素高度收敛于四类:
① <b>印度季风/产量冲击</b>（1979、2009、2015-16、2022-23、2026，出现频率最高——印度是全球最大产消国与边际进口国）;
② <b>巴西供给/乙醇分流</b>（1985-90、2005-06、2020-21、2025-26——糖醇比是2005年后新增的结构性变量）;
③ <b>ENSO天气</b>（厄尔尼诺: 2015-16、2026; 拉尼娜: 1988、2020-21）;
④ <b>政策与贸易流</b>（1963古巴禁运、1973-74出口限制与油元抢购、2016-17中国保障措施、2023印度零出口、2026印度禁令）。
值得注意: 1963、2005-06、2020-21三轮牛市中<b>全球产销差为正</b>——价格由「可贸易供给+边际流量」定价，而非全球实体缺口，与本报告94号「可贸易库存」框架一致。</div>

<h2>一、面板A · 长周期牛市全景（1960-2024，世行ISA月度）</h2>
<div class="note">2011年前的周级/日级期货K线经多渠道尝试（stooq/Yahoo/FRED/investing/TradingView）均被反爬拦截无法获取，故长史部分采用世行Pink Sheet的ISA日价月均值（加勒比港口FOB原糖，$/kg×45.359237换算为¢/lb）。<b>月度均价口径</b>较期货盘中价平滑且滞后，峰谷绝对值低于同期期货（如1980年期货盘中45¢+ vs 月均40.55¢），但摆动结构完整。</div>
<div class="legend">
  <span class="it"><span class="sw" style="background:#56B4E9"></span>起点/底部（▼）</span>
  <span class="it"><span class="sw" style="background:#E69F00"></span>驱动事件（●）</span>
  <span class="it"><span class="sw" style="background:#D55E00"></span>顶部（▲）</span>
  <span class="it"><span class="sw" style="background:#8b93a1"></span>终结（◆）</span>
  <span class="it">橙色底纹 = 牛市区间</span>
</div>
<div id="chartA" class="chart"></div>
<div class="src">数据: World Bank CMO Pink Sheet「Sugar, world」= ISA日价月均 (1960M01-2024M12)。事件编号1-28对应下表。</div>

<div class="sec scrollx">
<h3>面板A事件时间线（编号与图中一致）</h3>
<table>
<thead><tr><th>#</th><th>月份</th><th>类型</th><th>事件</th><th>驱动详情</th></tr></thead>
<tbody>__TBL_A__</tbody>
</table>
</div>

<h2>二、面板B · 周K蜡烛与驱动标注（2011-12 ~ 2026-09）</h2>
<div class="note">本地 <code>sb_price_daily.csv</code>（3,713根日线）按ISO周聚合为771根周线（周收盘=周内最后交易日收盘，周高/低=周内极值），已落盘 <code>data/price/sugar/sb_price_weekly.csv</code>。事件锚定到所在周，蜡烛颜色遵循国内惯例（红涨绿跌）。</div>
<div id="chartB" class="chart tall"></div>
<div class="src">数据: ICE No.11 连续合约日线（本地 data/price/sugar/sb_price_daily.csv, 2011-12-23~2026-09-25）→ 周线聚合。事件编号B1-B36对应下表。CFTC数据: data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv。</div>

<div class="sec scrollx">
<h3>面板B事件时间线（编号与图中一致）</h3>
<table>
<thead><tr><th>#</th><th>日期</th><th>类型</th><th>事件</th><th>驱动详情</th></tr></thead>
<tbody>__TBL_B__</tbody>
</table>
</div>

<h2>三、11轮牛市汇总表</h2>
<div class="sec scrollx">
<table>
<thead><tr><th>轮</th><th>牛市</th><th>低点</th><th>高点</th><th>涨幅</th><th>历时</th><th>核心驱动</th><th>基本面/持仓注记</th></tr></thead>
<tbody>__TBL_BULL__</tbody>
</table>
<div class="note b">涨幅为绝对值口径（¢/lb），括号内为倍数。I-VII轮为ISA月度均价口径，VIII-XI轮为ICE期货口径（周K/日线极值），两种口径不可直接横向比较幅度。</div>
</div>

<h2>四、全球供需背景（USDA产销差，raw value口径）</h2>
<div class="sec scrollx">
<table>
<thead><tr><th>牛市</th><th>对应市场年产销差（Mt）与库消比</th></tr></thead>
<tbody>__TBL_FUND__</tbody>
</table>
<div class="note">产销差为负（红色）=短缺。USDA PS历史数据为raw value口径，与ISO白砂糖口径存在系统性差异，仅作方向参考。多轮牛市（1963/1985-90/2005-06/2020-21）全球产销差为正，印证糖价由<b>可贸易边际流量</b>（印度进出口、巴西出口能力、物流与政策）定价，而非全球总量平衡。</div>
</div>

<h2>五、跨牛市规律（数据观察）</h2>
<div class="sec">
<p>1. <b>印度是最高频驱动源</b>: 11轮牛市中6轮以印度产量/政策冲击为第一或第二驱动（1979季风、2009季风、2015-16连续两季减产、2022-23零出口、2026禁令+季风-40%、以及1974年的进口抢购参与者）。机制: 印度产量摆动幅度大（20-33 Mt区间），且其进出口方向切换直接改写全球可贸易流量表。</p>
<p>2. <b>巴西角色在2005年后结构性变化</b>: 2005年前巴西仅是"另一个产国"; 2005年后糖醇比使巴西供给内生于原油/乙醇价格，2025-26年E30掺混令将这一机制制度化——本轮牛市的糖醇比崩塌（51.0%→42.5%）等价于巴西主动收缩出口供给约5-6 Mt。</p>
<p>3. <b>持仓极值是可靠的周期转折确认信号</b>: 2015-08底部（空头拥挤）→ 2023-04净多峰+279,528手（领先价格顶6个月）→ 2026-02纪录净空-253,592手（领先本轮价格底约2个月）→ 2026-08-11翻多。按/OI归一口径，当前净多/OI 12.4%（51.7百分位）仍处中位，与2016-09（38.4%）、2023-04（29.1%）的顶部拥挤度有显著距离。</p>
<p>4. <b>顶部形态分两类</b>: 政策/需求反噬型（2016-10中国关税、1974-11需求破坏）见顶后趋势性回落; 物流瓶颈型（2023-11桑托斯挤兑）瓶颈解除后单月崩塌-24.3%。当前（2026-09）尚无明确顶部信号，待验证节点: ISMA 2026/27首版（10月底-11月）、ISO 11月QMO、UNICA榨季收尾糖醇比。</p>
</div>

<h2>六、数据口径与校验</h2>
<div class="sec">
<p class="sm"><b>面板A</b>: World Bank CMO Pink Sheet (2025-01-03更新)「Sugar, world」列 = ISA日价（加勒比港口FOB原糖），$/kg×45.359237→¢/lb，1960M01-2024M12共780点，已落盘 <code>data/price/sugar/wb_isa_world_monthly_clb_1960_2024.json</code>。</p>
<p class="sm"><b>面板B</b>: 本地日线3,713根 → 周线771根（ISO周，周日期=周内最后交易日）。周线极值校验: 2015低10.13(8/28周)、2016高23.90(10/7周)、2018低9.83、2020低9.05、2021高20.69(11/19周)、2023高28.14(11/10周)、2026低13.22(4/17周)、2026高18.88(9/11周)——与报告102日线口径逐点一致。</p>
<p class="sm"><b>CFTC</b>: Legacy Futures-Only非商业持仓，2026-02-17净空-253,592手（1986年以来最深）、2026-08-11翻正+27,387手、2026-09-08净多+158,186手/OI 1,276,579手（纪录）。</p>
<p class="sm"><b>事件考证来源</b>: 1963/1972-74/1979-80为CIA解密备忘录、USDA 1963演讲、USDA SSS 1980-09-30报告、World Bank背景报告; 1994-95为FAO《The State of Agriculture 1996》(ISA日价峰15.45¢/lb, 1995-01); 1988-97"黄金时代"为FAO/ISO文件; 2015-2023为本项目报告102逐日时间线; 2025-26为UNICA双周报、Mysteel/Borsaya/commodity-board行情综述及本仓库CFTC与ONI数据（ONI MJJ 2026=+1.39）。未能核实的早期细节均已在事件描述中注明来源类型。</p>
<div class="warn"><b>vintage纪律提示:</b> 2026/27季平衡表数字随机构与月份剧烈摆动（ISO Aug-2026首版-0.234 Mt为强假设下的"地板数"，Covrig -0.3 / StoneX -1.7 / Green Pool -3.3 Mt）。本报告正文所有2026/27引用均标注机构与月份，11月ISMA首版与ISO QMO为下一个对账节点。</div>
</div>

<script>
const WBX=__WBX__, WBY=__WBY__;
const WK=__WK__;
const MPA=__MPA__, MPB=__MPB__;
const BANDA=__BANDA__, BANDB=__BANDB__;
const KIND_CN=__KINDCN__;

function mkMeta(mp){return mp.map(m=>({name:m.name,coord:m.coord,value:m.value,symbol:m.symbol,
  symbolRotate:m.symbolRotate||0,symbolSize:m.symbolSize,
  itemStyle:m.itemStyle,label:m.label,_t:m._t,_d:m._d,_kind:m._kind}));}

const ttFmtA=(p)=>{const d=p.data;return d&&d._t?
  '<b>#'+d.name+' · '+KIND_CN[d._kind]+'</b><br>'+d._t+'<br><span style="color:#9aa3b2;max-width:420px;display:inline-block;white-space:normal">'+d._d+'</span>':'';};

// ---------- 面板A ----------
const cA=echarts.init(document.getElementById('chartA'),null,{renderer:'canvas'});
cA.setOption({
  backgroundColor:'transparent',
  tooltip:{trigger:'item',backgroundColor:'#1c2028',borderColor:'#303642',textStyle:{color:'#e8eaee',fontSize:12},
    formatter:(p)=>{if(p.seriesType==='line')return p.name+' · '+p.value+' ¢/lb';return ttFmtA(p);}},
  grid:{left:52,right:20,top:30,bottom:74},
  xAxis:{type:'category',data:WBX,axisLabel:{color:'#9aa3b2',fontSize:11,
      formatter:(v)=>v.endsWith('-01')?v.slice(0,4):'',interval:0,rotate:0},
    axisLine:{lineStyle:{color:'#303642'}},axisTick:{show:false}},
  yAxis:{type:'value',name:'¢/lb',nameTextStyle:{color:'#7c8698'},max:60,
    axisLabel:{color:'#9aa3b2'},splitLine:{lineStyle:{color:'#242a34'}}},
  dataZoom:[{type:'inside',start:0,end:100},{type:'slider',height:22,bottom:14,
    borderColor:'#303642',backgroundColor:'#1c2028',fillerColor:'rgba(86,180,233,0.15)',
    textStyle:{color:'#9aa3b2'}}],
  series:[{
    type:'line',data:WBY,showSymbol:false,sampling:'lttb',
    lineStyle:{color:'#56B4E9',width:1.6},
    areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[
      {offset:0,color:'rgba(86,180,233,0.18)'},{offset:1,color:'rgba(86,180,233,0.01)'}]}},
    markArea:{silent:true,data:BANDA.map(b=>([
      {name:b.name,xAxis:b.xAxis[0],itemStyle:b.itemStyle,
       label:{show:true,position:'insideTop',color:'#E69F00',fontSize:10.5,fontWeight:600}},
      {xAxis:b.xAxis[1]}]))},
    markPoint:{data:mkMeta(MPA),tooltip:{formatter:ttFmtA}}
  }]
});

// ---------- 面板B ----------
const cB=echarts.init(document.getElementById('chartB'),null,{renderer:'canvas'});
const wkDates=WK.map(r=>r[0]);
cB.setOption({
  backgroundColor:'transparent',
  tooltip:{trigger:'item',backgroundColor:'#1c2028',borderColor:'#303642',textStyle:{color:'#e8eaee',fontSize:12},
    formatter:(p)=>{
      if(p.seriesType==='candlestick'){const d=p.data;
        return '<b>'+wkDates[p.dataIndex]+' 周</b><br>开 '+d[1]+' · 收 '+d[2]+'<br>低 '+d[3]+' · 高 '+d[4];}
      return ttFmtA(p);}},
  grid:{left:52,right:20,top:30,bottom:74},
  xAxis:{type:'category',data:wkDates,axisLabel:{color:'#9aa3b2',fontSize:11},
    axisLine:{lineStyle:{color:'#303642'}},axisTick:{show:false}},
  yAxis:{type:'value',name:'¢/lb',scale:true,nameTextStyle:{color:'#7c8698'},
    axisLabel:{color:'#9aa3b2'},splitLine:{lineStyle:{color:'#242a34'}}},
  dataZoom:[{type:'inside',start:0,end:100},{type:'slider',height:22,bottom:14,
    borderColor:'#303642',backgroundColor:'#1c2028',fillerColor:'rgba(86,180,233,0.15)',
    textStyle:{color:'#9aa3b2'}}],
  series:[{
    type:'candlestick',data:WK.map(r=>[r[1],r[2],r[3],r[4]]),
    itemStyle:{color:'#ff6b6b',color0:'#3ddc97',borderColor:'#ff6b6b',borderColor0:'#3ddc97'},
    markArea:{silent:true,data:BANDB.map(b=>([
      {name:b.name,xAxis:b.xAxis[0],itemStyle:b.itemStyle,
       label:{show:true,position:'insideTop',color:'#E69F00',fontSize:10.5,fontWeight:600}},
      {xAxis:b.xAxis[1]}]))},
    markPoint:{data:mkMeta(MPB),tooltip:{formatter:ttFmtA}}
  }]
});
window.addEventListener('resize',()=>{cA.resize();cB.resize();});
</script>
</div></body></html>
'''

# candlestick data 顺序: [open, close, low, high]
HTML = (HTML
  .replace('__TBL_A__', ev_table(PA,'A'))
  .replace('__TBL_B__', ev_table(PB,'B'))
  .replace('__TBL_BULL__', bull_rows())
  .replace('__TBL_FUND__', fund_rows())
  .replace('__WBX__', json.dumps(wb_x))
  .replace('__WBY__', json.dumps(wb_y))
  .replace('__WK__', json.dumps(weekly))
  .replace('__MPA__', json.dumps(MPA, ensure_ascii=False))
  .replace('__MPB__', json.dumps(MPB, ensure_ascii=False))
  .replace('__BANDA__', json.dumps(BAND_A, ensure_ascii=False))
  .replace('__BANDB__', json.dumps(BAND_B, ensure_ascii=False))
  .replace('__KINDCN__', json.dumps(KIND_CN, ensure_ascii=False)))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT,'w',encoding='utf-8').write(HTML)
print('written:', OUT, len(HTML), 'bytes')
