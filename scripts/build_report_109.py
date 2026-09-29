# -*- coding: utf-8 -*-
"""109 号报告：白糖四轮牛市逐段讯息流（段级驱动标注 + 逐段讯息时间线）
数据源：
  data/price/sugar/sb_price_weekly.csv        周K（2011-12-23 ~ 2026-09-25）
  data/price/sugar/sugar_bull_segments.json   46 段 × 带日期讯息（本次考证产物）
  data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv  CFTC Legacy Futures-Only 非商业净持仓
输出：reports/109_白糖牛市逐段讯息流_段级驱动标注/index.html
"""
import json, csv, os, sys

ROOT = r"C:\Users\Administrator\Desktop\农业"
OUT_DIR = os.path.join(ROOT, "reports", "109_白糖牛市逐段讯息流_段级驱动标注")

# ---------- 读取周K ----------
weekly = []
with open(os.path.join(ROOT, "data", "price", "sugar", "sb_price_weekly.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        weekly.append([r["time"], float(r["open"]), float(r["close"]), float(r["low"]), float(r["high"])])
wk_dates = [w[0] for w in weekly]
wk_set = set(wk_dates)

# ---------- 读取 CFTC ----------
cftc = {}
with open(os.path.join(ROOT, "data", "cftc", "sugar", "sugar_cftc_futonly_1986_2026.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        d = r["date"]
        try:
            cftc[d] = (int(float(r["nc_net"])), int(float(r["oi"])))
        except Exception:
            pass
cftc_dates = sorted(cftc.keys())

def nearest_cftc(d):
    """取 <= d 的最近一期 CFTC（周二报告日）"""
    best = None
    for cd in cftc_dates:
        if cd <= d:
            best = cd
        else:
            break
    return best

# ---------- 读取段数据 ----------
with open(os.path.join(ROOT, "data", "price", "sugar", "sugar_bull_segments.json"), encoding="utf-8") as f:
    SEG = json.load(f)

ROUNDS = ["2015-16", "2020-22", "2022-24", "2025-26"]
NATURE = SEG["meta"]["nature_legend"]

# 校验段端点日期均落在周K上
miss = []
for rk in ROUNDS:
    for s in SEG["rounds"][rk]["segments"]:
        for k in ("d0", "d1"):
            if s[k] not in wk_set:
                miss.append((rk, s["idx"], k, s[k]))
if miss:
    print("[WARN] 段端点日期未匹配周K：", miss)

# ---------- 每轮图的窗口 ----------
PAD_W = 6
def window(rk):
    segs = SEG["rounds"][rk]["segments"]
    a, b = segs[0]["d0"], segs[-1]["d1"]
    i0 = max(0, wk_dates.index(a) - PAD_W)
    i1 = min(len(wk_dates) - 1, wk_dates.index(b) + PAD_W)
    return i0, i1

charts = []
for rk in ROUNDS:
    i0, i1 = window(rk)
    sub = weekly[i0:i1 + 1]
    cftc_line = []
    for w in sub:
        cd = nearest_cftc(w[0])
        cftc_line.append(None if cd is None else cftc[cd][0])
    segs = SEG["rounds"][rk]["segments"]
    charts.append({
        "rk": rk,
        "label": SEG["rounds"][rk]["label"],
        "summary": SEG["rounds"][rk]["summary"],
        "dates": [w[0] for w in sub],
        "kdata": [[w[1], w[2], w[3], w[4]] for w in sub],
        "nc": cftc_line,
        "segs": segs,
    })

# 总览图：2015-01 起
ov_i0 = wk_dates.index("2015-01-02") if "2015-01-02" in wk_set else next(i for i, d in enumerate(wk_dates) if d >= "2015-01-01")
ov_dates = wk_dates[ov_i0:]
ov_k = [[w[1], w[2], w[3], w[4]] for w in weekly[ov_i0:]]
ov_nc = []
for d in ov_dates:
    cd = nearest_cftc(d)
    ov_nc.append(None if cd is None else cftc[cd][0])

all_segs_flat = []
for rk in ROUNDS:
    for s in SEG["rounds"][rk]["segments"]:
        ss = dict(s)
        ss["rk"] = rk
        all_segs_flat.append(ss)

payload = {
    "nature": NATURE,
    "charts": charts,
    "ov": {"dates": ov_dates, "k": ov_k, "nc": ov_nc},
    "segs": all_segs_flat,
    "meta": SEG["meta"],
}

os.makedirs(OUT_DIR, exist_ok=True)

# ---------- HTML ----------
NAT_COLOR = {k: v["color"] for k, v in NATURE.items()}

def fmt_nc(v):
    if v is None:
        return "—"
    s = "+" if v > 0 else ""
    return f"{s}{v:,}"

def seg_rows_html(rk):
    out = []
    segs = SEG["rounds"][rk]["segments"]
    for s in segs:
        nat = NATURE[s["nature"]]
        col = nat["color"]
        pct = s["pct"]
        cls = "up" if pct > 0 else "down"
        arrow = "▲" if pct > 0 else "▼"
        msgs = []
        for m in s["msgs"]:
            msgs.append(
                f'<li><span class="md">{m["d"]}</span> {m["e"]} <span class="ms">[{m["s"]}]</span></li>'
            )
        cons = "一致" if s["consistency"] == "consistent" else "部分一致"
        out.append(f'''
<tr class="segrow">
  <td class="num"><span class="badge" style="background:{col}">{rk}·{s["idx"]}</span></td>
  <td class="nowrap sm">{s["d0"]}<br><span class="dim">→ {s["d1"]}</span></td>
  <td class="num sm">{s["v0"]:.2f} → {s["v1"]:.2f}</td>
  <td class="num {cls}">{arrow} {pct:+.1f}%</td>
  <td class="num sm">{s["weeks"]}周</td>
  <td class="num sm">{fmt_nc(s["ncchg"])}</td>
  <td class="sm"><span class="ktag" style="border-color:{col};color:{col}">{nat["zh"]}</span><br><span class="dim">{cons}</span></td>
  <td class="sm dim nowrap">{s["oni"]}</td>
</tr>
<tr class="msgrow"><td></td><td colspan="7"><ul class="msgs">{''.join(msgs)}</ul></td></tr>''')
    return "".join(out)

round_sections = []
for ci, ch in enumerate(charts):
    rk = ch["rk"]
    round_sections.append(f'''
<h2>{ci+2}. {ch["label"]}</h2>
<p class="lede">{ch["summary"]}</p>
<div class="sec">
  <div id="chart{ci}" class="chart tall"></div>
  <div class="legend">
    <span class="it"><i class="sw" style="background:{NAT_COLOR["A"]};border-radius:50%"></i>A 资金讯息共振（价涨+净持仓大增，●）</span>
    <span class="it"><i class="sw" style="background:{NAT_COLOR["B"]}"></i>B 现货挤兑/空头回补（价涨钱撤，■）</span>
    <span class="it"><i class="sw" style="background:{NAT_COLOR["C"]};transform:rotate(45deg)"></i>C 技术性回调（无新讯息，◆）</span>
    <span class="it"><i class="sw" style="background:{NAT_COLOR["D"]};clip-path:polygon(50% 0,100% 100%,0 100%)"></i>D 讯息证伪/多头离场（▲）</span>
    <span class="it"><i class="sw" style="background:#D55E00"></i>K线涨（朱红）</span>
    <span class="it"><i class="sw" style="background:#56B4E9"></i>K线跌（天蓝）</span>
  </div>
</div>
<div class="scrollx"><table>
<thead><tr><th>段</th><th>起止（周线）</th><th>价格 ¢/lb</th><th>涨跌</th><th>历时</th><th>非商业净持仓变化(手)</th><th>性质</th><th>ONI</th></tr></thead>
<tbody>{seg_rows_html(rk)}</tbody></table></div>
''')

corr_html = "".join(f"<li>{c}</li>" for c in SEG["meta"]["corrections"])

# 性质统计
nat_count = {}
for s in all_segs_flat:
    nat_count[s["nature"]] = nat_count.get(s["nature"], 0) + 1
b_segs = [(s["rk"], s["idx"], s["pct"], s["weeks"], s["ncchg"]) for s in all_segs_flat if s["nature"] == "B"]

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>109号 · 白糖四轮牛市逐段讯息流（46段驱动标注）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>:root{{
  --bg:#14171c; --card:#1c2028; --card2:#232933; --line:#303642;
  --tx:#e8eaee; --dim:#9aa3b2; --dim2:#7c8698;
  --accent:#4c9be8; --warn:#e8a33d;
  --up:#D55E00; --down:#56B4E9;
}}
*{{box-sizing:border-box;}}
body{{margin:0;background:var(--bg);color:var(--tx);
  font:15px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}}
.wrap{{max-width:1280px;margin:0 auto;padding:34px 22px 70px;}}
h1{{font-size:26px;margin:0 0 8px;line-height:1.4;}}
h2{{font-size:20px;margin:38px 0 6px;padding-top:22px;border-top:1px solid var(--line);}}
h3{{font-size:16.5px;margin:24px 0 8px;color:#dfe4ec;}}
p{{margin:11px 0;font-size:14.2px;line-height:1.85;}}
.lede{{color:var(--dim);font-size:13px;margin:6px 0 18px;}}
.meta{{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 8px;}}
.meta span{{background:var(--card2);border:1px solid var(--line);border-radius:8px;
  padding:5px 11px;font-size:11.8px;color:var(--dim);}}
.sec{{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:20px 24px 14px;margin:18px 0;}}
.kicker{{background:linear-gradient(90deg,#232933,#1c2028);border:1px solid var(--line);
  border-left:4px solid #E69F00;border-radius:10px;padding:15px 20px;margin:16px 0;
  font-size:14.5px;line-height:1.8;}}
.kicker b{{color:#fff;}}
.note{{color:var(--dim);font-size:13px;border-left:3px solid var(--accent);
  padding-left:13px;margin:14px 2px;line-height:1.75;}}
.warn{{background:#2a2218;border:1px solid #5c4a22;border-radius:9px;padding:12px 15px;
  font-size:13.2px;color:#e6d3ab;margin:14px 0;line-height:1.8;}}
.warn b{{color:#ffd79a;}}
.warn ul{{margin:6px 0 2px;padding-left:20px;}}
table{{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:13.2px;}}
th{{text-align:left;background:var(--card2);color:var(--dim);font-weight:600;
  padding:9px 10px;border-bottom:2px solid var(--line);white-space:nowrap;font-size:12.6px;}}
td{{padding:8px 10px;border-bottom:1px solid #2a2f3a;vertical-align:top;}}
tr.segrow:hover td{{background:#20242e;}}
tr.msgrow td{{padding:0 10px 12px;border-bottom:1px solid #2a2f3a;background:#191d24;}}
ul.msgs{{margin:8px 0 0;padding-left:18px;font-size:12.9px;line-height:1.85;color:#d3d9e3;}}
ul.msgs li{{margin:4px 0;}}
.md{{display:inline-block;min-width:78px;color:#E69F00;font-weight:600;
  font-variant-numeric:tabular-nums;font-size:12.3px;}}
.ms{{color:var(--dim2);font-size:11.6px;}}
.num{{font-variant-numeric:tabular-nums;text-align:right;}}
.nowrap{{white-space:nowrap;}}
.up{{color:#D55E00;font-weight:700;}}
.down{{color:#56B4E9;font-weight:700;}}
.dim{{color:var(--dim2);}}
.sm{{font-size:12.2px;}}
.chart{{width:100%;height:520px;margin:8px 0 4px;}}
.chart.tall{{height:640px;}}
.src{{color:var(--dim2);font-size:11.6px;margin:2px 2px 16px;line-height:1.65;}}
.badge{{display:inline-block;min-width:56px;height:20px;line-height:20px;border-radius:10px;
  color:#14171c;font-weight:700;font-size:11.2px;text-align:center;padding:0 8px;white-space:nowrap;}}
.ktag{{display:inline-block;border:1px solid;border-radius:6px;padding:1px 8px;font-size:11.5px;white-space:nowrap;}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0 4px;font-size:12.4px;color:var(--dim);}}
.legend .it{{display:flex;align-items:center;gap:6px;}}
.legend .sw{{width:14px;height:14px;border-radius:3px;display:inline-block;}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:11px;margin:14px 0;}}
.card{{background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:13px 15px;}}
.card .k{{color:var(--dim2);font-size:11.4px;}}
.card .v{{font-size:21px;font-weight:700;font-variant-numeric:tabular-nums;margin:3px 0 1px;}}
.card .d{{font-size:11.6px;color:var(--dim);line-height:1.55;}}
.scrollx{{overflow-x:auto;}}
</style>
</head>
<body><div class="wrap">

<h1>109号 · 白糖四轮牛市逐段讯息流 —— 46 个价格摆动段，每段当时收到了什么讯息</h1>
<div class="lede">ICE No.11 周K（2011-12-23 ~ 2026-09-25）按 10% 反转阈值切分为 46 个摆动段；每段标注<b>当时的具体讯息</b>（带日期的机构报告/政策/天气/物流/持仓行为），而非整轮牛市主题。</div>
<div class="meta">
  <span>编制日期: 2026-09-28</span>
  <span>切段方法: ZigZag 10% 反转阈值（周线 high/low 口径）</span>
  <span>段数: 2015-16 轮 13 / 2020-22 轮 17 / 2022-24 轮 7 / 2025-26 轮 9</span>
  <span>持仓: CFTC Legacy Futures-Only 非商业净持仓（手）</span>
  <span>ONI: NOAA 季节值</span>
</div>

<div class="kicker"><b>核心结论：</b>把牛市拆成段之后，"驱动因素"其实分成四种性质完全不同的东西，而<b>性质决定了顶部形态</b>：
<b>A 资金讯息共振</b>（价涨+净持仓大增，{nat_count.get("A",0)} 段）= 市场收到新讯息、资金同向确认，是最健康的上涨；
<b>B 现货挤兑/空头回补</b>（价涨钱撤，{nat_count.get("B",0)} 段）= 交割挤兑、物流瓶颈、商业空头回补推价而投机缺席，历史上出现在<b>三个大顶之前</b>（2021-02、2021-11、2023-11）；
<b>C 技术性回调</b>（{nat_count.get("C",0)} 段）= 获利了结/宏观扰动，无新利空基本面；
<b>D 讯息证伪/多头离场</b>（{nat_count.get("D",0)} 段）= 产量上修、政策转向、油价崩盘等具体利空落地。
<br>本轮（2025-26）段9 主升属 <b>A 型</b>：+42.4%、净持仓 +292,608 手（纪录净空翻净多）、OI 创 1,276,579 手纪录 —— 与前三轮顶部前的 B 型结构不同。</div>

<h2>1. 总览：四轮牛市在周K上的 46 段</h2>
<div class="sec">
  <div id="chartOv" class="chart tall"></div>
  <div class="legend">
    <span class="it"><i class="sw" style="background:{NAT_COLOR["A"]}"></i>A 资金讯息共振</span>
    <span class="it"><i class="sw" style="background:{NAT_COLOR["B"]}"></i>B 现货挤兑/空头回补（价涨钱撤）</span>
    <span class="it"><i class="sw" style="background:{NAT_COLOR["C"]}"></i>C 技术性回调</span>
    <span class="it"><i class="sw" style="background:{NAT_COLOR["D"]}"></i>D 讯息证伪/多头离场</span>
    <span class="it"><i class="sw" style="background:#D55E00"></i>K线涨</span>
    <span class="it"><i class="sw" style="background:#56B4E9"></i>K线跌</span>
    <span class="it">下方折线 = CFTC 非商业净持仓（手）</span>
  </div>
</div>
<div class="src">鼠标悬停任意段端点标记可查看该段全部讯息（日期+事件+来源）。数据: data/price/sugar/sb_price_weekly.csv · data/price/sugar/sugar_bull_segments.json · data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv</div>

<div class="cards">
  <div class="card"><div class="k">B 型"价涨钱撤"段</div><div class="v">{nat_count.get("B",0)}</div>
    <div class="d">{'; '.join(f'{a}·{b}({c:+.1f}%/{d}周/净持仓{e:+,})' for a,b,c,d,e in b_segs)}</div></div>
  <div class="card"><div class="k">最大资金增持段</div><div class="v">+292,608</div><div class="d">2025-26·9（+42.4%，11周，OI 840k→1,277k）；其次 2020-21·4（+201,300）、2015-16·2（+196,633）、2025-26·5（+179,917）</div></div>
  <div class="card"><div class="k">最长下跌段</div><div class="v">21 周</div><div class="d">2025-26·4（-19.4%，净空 -130,227 手，把基金压到 1986 年来最深净空 -253,592）；2021-11 起同长 21 周为上涨段</div></div>
  <div class="card"><div class="k">最猛崩塌段</div><div class="v">-28.8%</div><div class="d">2022-24·5（2023-11-10→12-29，7周，净多撤离 -153,540 手 / -67.8%）</div></div>
</div>

<h3>本轮与前两轮顶部的结构差异（持仓口径）</h3>
<div class="scrollx"><table>
<thead><tr><th>顶部/主升段</th><th>周期</th><th>价格表现</th><th>非商业净持仓</th><th>结构判定</th></tr></thead>
<tbody>
<tr><td>2020-21·8</td><td class="nowrap">2020-12-18→2021-02-26</td><td class="num up">+34.4% / 10周</td><td class="num down">-6,532</td><td class="sm">B 型：CzApp 点名 3 月合约软逼仓 + 集装箱荒 + 泰国 6.9Mt 十年低；投机缺席</td></tr>
<tr><td>2021-11 顶（2020-21·12）</td><td class="nowrap">2021-06-25→2021-11-19</td><td class="num up">+27.8% / 21周</td><td class="num down">-14,602</td><td class="sm">B 型：三轮霜冻（6/28、7/19、7/28）+ Czarnikow 下调中南部 34.1→29-33Mt；商业空头回补推价</td></tr>
<tr><td>2023-11 顶（2022-24·4）</td><td class="nowrap">2023-06-30→2023-11-10</td><td class="num up">+29.0% / 19周</td><td class="num up">+11,909</td><td class="sm">B 型：印度七年首次零出口 + 桑托斯 CLI 17→33 天 + 10月合约 287万吨纪录交割</td></tr>
<tr><td>2026-09（2025-26·9）</td><td class="nowrap">2026-06-26→2026-09-11</td><td class="num up">+42.4% / 11周</td><td class="num up">+292,608</td><td class="sm"><b>A 型</b>：糖醇比崩塌（51.0→42.5%）+ 印度禁令转进口 + 强厄尔尼诺三火叠加，资金与讯息共振；净多/OI 12.4%（51.7 百分位）仍属中位</td></tr>
</tbody></table></div>
<div class="note">读法：B 型段的价格新高不代表持仓新高——三个历史大顶都出现在投机资金已经不再加仓的段落里。本轮 2025-26·9 是四段中唯一"价、量、讯息"三者同步的，但代价是它同时把净空极值（-253,592 手）当作了燃料，因此上涨的持续性取决于<b>缺口预估是否继续上修</b>（ISO 11月 QMO、ISMA 2026/27 首版、UNICA 榨季收尾为三个验证节点）。</div>

{''.join(round_sections)}

<h2>6. 本轮考证中的纠错与口径说明</h2>
<div class="warn"><b>已采纳的纠错（与本项目此前记录不一致处）：</b><ul>{corr_html}</ul></div>
<div class="note"><b>口径纪律：</b>①所有机构数字标注发布月份（vintage），不使用"USDA/ISO 说 X"的无时间表述；②ISO/ISMA/泰国/欧盟榨季为 10-9 月，UNICA 为 4-3 月，二者相差 6 个月，跨机构比较前先对齐；③CFTC 拥挤度比较用 /OI 归一 + 全样本百分位，禁用绝对手数（糖 OI 已从 2015 年 ~74 万手增至 2026 年 ~128 万手）；④ISO 每年 8 月的新季首版为"无天气情景的地板数"，不等于中性共识。</div>

<h2>7. 数据与方法</h2>
<p class="sm"><b>切段</b>：对周K（本地日线按 ISO 周聚合，771 根）以 10% 反转阈值做 ZigZag，取四个牛市窗口内的摆动段共 46 段；段端点价格取周线 high/low，因此段幅度略大于收盘价口径。</p>
<p class="sm"><b>持仓</b>：CFTC Legacy Futures-Only 非商业（large spec）净持仓，按周二报告日对齐到最近的周K日期；段净持仓变化 = 段末 - 段初。</p>
<p class="sm"><b>性质判定规则</b>：A = |净持仓变化| 与价格方向同向且量级显著（≥3 万手或 ≥15% 持仓变动）；B = 价涨但净持仓持平或下降；C = 无清晰新讯息的短段回调（通常 ≤5 周）；D = 价跌且净多大幅撤离、有具体利空落地。判定为定性归纳，边界段（如 2020-21·11）以持仓变化为主依据。</p>
<p class="sm"><b>讯息来源</b>：ISO Quarterly Market Outlook / World Sugar Balance（本地 balance_pdfs 36 期原文）、UNICA 双周报、ISMA、OCSB、Czarnikow、Licht、StoneX、Green Pool、Covrig、ED&F Man Monthly Note、Nordzucker、FAO 食品价格指数、NOAA/CPC ONI、IMD、DGFT 与印度财政部官方通知、路透、新华社/中央社、云糖网/沐甜/台糖月报、CFTC COT。未能核实到确切日期者以月份或"结构"标注。</p>
<p class="sm"><b>未核实/待验证</b>：2025-16 轮段3、段7、段9 与 2020-22 轮段2、段5、段7、段11 的具体触发讯息以"无清晰新讯息 + 持仓行为"为依据，属回调性质判定（C 型），非事件考证结论；2026/27 季各机构缺口预估仍在快速修订中，本报告仅记录截至 2026-09-25 的 vintage。</p>

</div>
<script>
const PAYLOAD = {json.dumps(payload, ensure_ascii=False)};
const NC = {{A:"{NAT_COLOR["A"]}",B:"{NAT_COLOR["B"]}",C:"{NAT_COLOR["C"]}",D:"{NAT_COLOR["D"]}"}};
const NATURE_ZH = {{A:"资金讯息共振",B:"现货挤兑/空头回补",C:"技术性回调",D:"讯息证伪/多头离场"}};
const UP="#D55E00", DN="#56B4E9", BG="#14171c", CARD="#1c2028", LINE="#303642", TX="#e8eaee", DIM="#9aa3b2";

const SYM = {{A:"circle",B:"rect",C:"diamond",D:"triangle"}};   // 性质→形状（色弱安全的非颜色线索）
function segTip(rk, idx){{
  const s = PAYLOAD.segs.find(x=>x.rk===rk&&x.idx===idx);
  if(!s) return "";
  const cls = s.pct>0?UP:DN, sign = s.pct>0?"▲":"▼";
  let h = `<div style="max-width:520px"><b style="color:${{NC[s.nature]}}">${{rk}}·${{s.idx}} ${{NATURE_ZH[s.nature]}}</b><br>`;
  h += `<span style="color:${{DIM}}">${{s.d0}} → ${{s.d1}}（${{s.weeks}}周）</span><br>`;
  h += `<b style="color:${{cls}}">${{sign}} ${{s.pct.toFixed(1)}}%</b> ${{s.v0.toFixed(2)}}→${{s.v1.toFixed(2)}}¢　净持仓 ${{(s.ncchg>0?"+":"")+s.ncchg.toLocaleString()}}手<br>`;
  h += `<span style="color:${{DIM}};font-size:11px">ONI ${{s.oni}}</span><ul style="margin:6px 0 0;padding-left:16px;font-size:12px;line-height:1.7">`;
  s.msgs.forEach(m=>{{ h += `<li><span style="color:#E69F00">${{m.d}}</span> ${{m.e}} <span style="color:${{DIM}};font-size:11px">[${{m.s}}]</span></li>`; }});
  return h+"</ul></div>";
}}

function buildChart(domId, cfg, showAll){{
  const el = document.getElementById(domId);
  const chart = echarts.init(el, null, {{renderer:"canvas"}});
  const marks = [], pts = [];
  cfg.segs.forEach(s=>{{
    const c = NC[s.nature];
    marks.push([
      {{coord:[s.d0, s.v0], symbol:"none"}},
      {{coord:[s.d1, s.v1], symbol:"none",
        lineStyle:{{color:c,width:s.nature==="B"?3:2,type:s.nature==="C"?"dashed":"solid",opacity:0.95}}}}
    ]);
    pts.push({{
      value:[s.d1, s.v1], name:`${{s.rk||cfg.rk}}·${{s.idx}}`,
      itemStyle:{{color:c,borderColor:BG,borderWidth:1.5}},
      label:{{show:true, formatter:String(s.idx), color:"#14171c", fontSize:10, fontWeight:700, position:"inside"}},
      symbol: SYM[s.nature] || "circle",
      symbolSize: showAll?15:19,
      _rk:(s.rk||cfg.rk), _idx:s.idx, _nat:s.nature, _pct:s.pct, _d0:s.d0, _d1:s.d1
    }});
  }});
  const opt = {{
    backgroundColor:"transparent",
    animation:true, animationDuration:600,
    tooltip:{{trigger:"item", backgroundColor:"#1c2028", borderColor:LINE, borderWidth:1,
      textStyle:{{color:TX,fontSize:12}}, confine:true, enterable:true,
      formatter:(p)=>{{
        if(p.seriesType==="scatter" && p.data && p.data._rk) return segTip(p.data._rk, p.data._idx);
        if(p.seriesType==="candlestick"){{
          const v=p.data; return `<b>${{p.name}}</b><br>开 ${{v[1]}} 收 ${{v[2]}}<br>低 ${{v[3]}} 高 ${{v[4]}}`;
        }}
        if(p.seriesType==="line") return `${{p.name}}<br>非商业净持仓 <b>${{p.value==null?"—":p.value.toLocaleString()}}</b> 手`;
        return "";
      }} }},
    axisPointer:{{link:[{{xAxisIndex:"all"}}]}},
    grid:[
      {{left:58,right:22,top:26,height: showAll?"62%":"66%"}},
      {{left:58,right:22,top: showAll?"76%":"79%",height: showAll?"16%":"15%"}}
    ],
    xAxis:[
      {{type:"category",data:cfg.dates,boundaryGap:true,axisLine:{{lineStyle:{{color:LINE}}}},
        axisLabel:{{color:DIM,fontSize:10.5}},splitLine:{{show:false}},axisPointer:{{label:{{show:false}}}}}},
      {{type:"category",gridIndex:1,data:cfg.dates,boundaryGap:true,axisLine:{{lineStyle:{{color:LINE}}}},
        axisLabel:{{show:false}},axisTick:{{show:false}},splitLine:{{show:false}}}}
    ],
    yAxis:[
      {{scale:true,splitLine:{{lineStyle:{{color:"#232933"}}}},axisLabel:{{color:DIM,fontSize:10.5,formatter:"{{value}}¢"}},
        name:"ICE No.11 周K ¢/lb",nameTextStyle:{{color:DIM,fontSize:10.5,align:"left"}}}},
      {{gridIndex:1,scale:true,splitLine:{{show:false}},axisLabel:{{color:DIM,fontSize:9.5,formatter:(v)=>(v/1000).toFixed(0)+"k"}},
        name:"净持仓",nameTextStyle:{{color:DIM,fontSize:9.5}}}}
    ],
    dataZoom:[{{type:"inside",xAxisIndex:[0,1],start:0,end:100}}],
    series:[
      {{name:"K",type:"candlestick",data:cfg.kdata,z:2,
        itemStyle:{{color:UP,color0:DN,borderColor:UP,borderColor0:DN}},
        markLine:{{silent:true,symbol:["none","none"],data:marks,
          label:{{show:false}},emphasis:{{disabled:true}}}} }},
      {{name:"段端点",type:"scatter",data:pts,z:5,symbolSize:16}},
      {{name:"净持仓",type:"line",xAxisIndex:1,yAxisIndex:1,data:cfg.nc,z:3,
        showSymbol:false,connectNulls:true,lineStyle:{{color:"#CC79A7",width:1.4}},
        areaStyle:{{color:"rgba(204,121,167,0.10)"}} }}
    ]
  }};
  chart.setOption(opt);
  window.addEventListener("resize",()=>chart.resize());
  return chart;
}}

// 总览
buildChart("chartOv", {{rk:"OV", dates:PAYLOAD.ov.dates, kdata:PAYLOAD.ov.k, nc:PAYLOAD.ov.nc,
  segs:PAYLOAD.segs.map(s=>({{...s}}))}}, true);
// 四轮
PAYLOAD.charts.forEach((c,i)=>{{ buildChart("chart"+i, c, false); }});
</script>
</body></html>'''

with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("OK ->", os.path.join(OUT_DIR, "index.html"), f"{len(html)/1024:.0f} KB")
print("nature counts:", nat_count)
