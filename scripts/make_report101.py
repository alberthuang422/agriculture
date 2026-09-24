# -*- coding: utf-8 -*-
"""101号报告: 价格横盘 + CFTC非商业净持仓大幅变化 → 前瞻4/8/12周收益研究"""
import json, html

ROOT = "C:/Users/Administrator/Desktop/农业"
SRC = ROOT + "/data/cftc/results_cot/diverge_events_20260923.json"
OUT = ROOT + "/reports/101_软商品横盘与持仓背离前瞻/index.html"

d = json.load(open(SRC, encoding="utf-8"))
events = d["events"]["0.08"]      # 主阈值
events_lo = d["events"]["0.05"]
events_hi = d["events"]["0.1"]
base = d["base"]
params = d["params"]

MARKETS = ["咖啡 C (ICE)", "可可 (ICE)", "糖 11号 (ICE)"]
M_CN = {"咖啡 C (ICE)": "咖啡 C", "可可 (ICE)": "可可", "糖 11号 (ICE)": "糖 11号"}

def esc(x):
    return html.escape(str(x))

def fmt_pct(x, sign=True):
    if x is None: return "—"
    s = f"{x:+.1f}%" if sign else f"{x:.1f}%"
    return s

def cls_ret(x):
    if x is None: return "na"
    if x > 0: return "up"      # 涨(红)
    if x < 0: return "down"    # 跌(绿)
    return "flat"

# ---------- 各品种事件明细 ----------
def ev_rows(m, evs):
    rows = ""
    for e in evs:
        f4, f8, f12 = e["fwd4"], e["fwd8"], e["fwd12"]
        rows += f"""<tr>
  <td class="cid">{esc(e['start'])}<br><span class="sub">{esc(e['end'])}</span></td>
  <td>{e['L']}周</td>
  <td>{esc(e['close0'])}</td>
  <td class="hidx">{e['band_hi_pct']:+.1f}%<br><span class="sub">{e['band_lo_pct']:+.1f}%</span></td>
  <td class="dir">{esc(e['dir'])}</td>
  <td class="num">{e['d_nc_net']:+,}</td>
  <td class="num">{e['d_nc_net_pct_oi']:.1f}%</td>
  <td class="sub2">+{e['oi_avg']:,}</td>
  <td class="ret {cls_ret(f4)}">{fmt_pct(f4)}</td>
  <td class="ret {cls_ret(f8)}">{fmt_pct(f8)}</td>
  <td class="ret {cls_ret(f12)}">{fmt_pct(f12)}</td>
</tr>"""
    return rows

def market_section(m, evs, note=""):
    n_add = sum(1 for e in evs if e["dir"]=="增仓")
    n_cut = sum(1 for e in evs if e["dir"]=="减仓")
    b = base[m]
    head = f"""
<div class="sec" id="{esc(m)}">
<h3>{esc(M_CN[m])} <span class="sub">({esc(m)})</span></h3>
<div class="chiprow">
  <span class="chip">事件数 <b>{len(evs)}</b></span>
  <span class="chip">增仓 <b>{n_add}</b> / 减仓 <b>{n_cut}</b></span>
  <span class="chip">横盘带 ±5% &nbsp;长度 4–12周</span>
  <span class="chip">仓位变化 |Δ净仓|/OI ≥ 8%</span>
</div>"""
    if note:
        head += f'<div class="note">{note}</div>'
    # 前瞻概览
    ov = {}
    for k in (4,8,12):
        vals = [e[f"fwd{k}"] for e in evs if e[f"fwd{k}"] is not None]
        med = sorted(vals)[len(vals)//2] if vals else None
        pos = sum(1 for v in vals if v>0)/len(vals) if vals else None
        ov[k] = (med, pos)
    tbl1 = f"""
<table class="mini">
<thead><tr><th>前瞻窗口</th><th>事件后中位收益</th><th>上涨占比</th><th>全样本基准中位</th><th>基准上涨占比</th><th>对照解读</th></tr></thead>
<tbody>
<tr><td>+4周</td><td class="ret {cls_ret(ov[4][0])}">{fmt_pct(ov[4][0])}</td><td>{ov[4][1]*100:.0f}%</td>
    <td class="ret {cls_ret(b['4']['med'])}">{fmt_pct(b['4']['med'])}</td><td>{b['4']['pos_pct']}%</td>
    <td class="dim">{"跑赢基准" if (ov[4][0] or 0) > b['4']['med'] else "低于基准"}</td></tr>
<tr><td>+8周</td><td class="ret {cls_ret(ov[8][0])}">{fmt_pct(ov[8][0])}</td><td>{ov[8][1]*100:.0f}%</td>
    <td class="ret {cls_ret(b['8']['med'])}">{fmt_pct(b['8']['med'])}</td><td>{b['8']['pos_pct']}%</td>
    <td class="dim">{"跑赢基准" if (ov[8][0] or 0) > b['8']['med'] else "低于基准"}</td></tr>
<tr><td>+12周</td><td class="ret {cls_ret(ov[12][0])}">{fmt_pct(ov[12][0])}</td><td>{ov[12][1]*100:.0f}%</td>
    <td class="ret {cls_ret(b['12']['med'])}">{fmt_pct(b['12']['med'])}</td><td>{b['12']['pos_pct']}%</td>
    <td class="dim">{"跑赢基准" if (ov[12][0] or 0) > b['12']['med'] else "低于基准"}</td></tr>
</tbody></table>"""
    tbl2 = f"""
<table class="ev">
<thead><tr><th>横盘起点→终点</th><th>长度</th><th>期初价</th><th>带内高/低</th><th>方向</th><th>Δ净仓(手)</th><th>变动/OI</th><th>OI均值</th><th>+4周</th><th>+8周</th><th>+12周</th></tr></thead>
<tbody>{ev_rows(m, evs)}</tbody>
</table>"""
    return head + tbl1 + tbl2 + "</div>"

# ---------- 方向一致性 & 波动检验 ----------
def stat_section():
    # 方向一致性
    cons = {}
    for m in MARKETS:
        es = [e for e in events[m] if e["fwd4"] is not None and e["fwd12"] is not None]
        row = []
        for k in (4,8,12):
            agree = sum(1 for e in es if (e["dir"]=="增仓" and e[f"fwd{k}"]>0) or (e["dir"]=="减仓" and e[f"fwd{k}"]<0))
            row.append(f"{agree}/{len(es)} ({agree/len(es)*100:.0f}%)")
        cons[m] = row
    rows = ""
    for m in MARKETS:
        rows += f"""<tr><td class="mk">{esc(M_CN[m])}</td>
<td>{cons[m][0]}</td><td>{cons[m][1]}</td><td>{cons[m][2]}</td></tr>"""
    # 波动: 事件 SD vs 基准 SD (p10-p90 估算)
    vol = {}
    for m in MARKETS:
        b = base[m]
        row = []
        for k in (4,8,12):
            ev_vals = [e[f"fwd{k}"] for e in events[m] if e[f"fwd{k}"] is not None]
            if len(ev_vals) > 1:
                import statistics
                ev_sd = statistics.pstdev(ev_vals)
                b_sd = (b[str(k)]["p90"]-b[str(k)]["p10"])/2.56
                row.append(f"{ev_sd:.1f}% / ~{b_sd:.1f}% ({ev_sd/b_sd:.2f}x)" if b_sd else "—")
            else:
                row.append("—")
        vol[m] = row
    rows2 = ""
    for m in MARKETS:
        rows2 += f"""<tr><td class="mk">{esc(M_CN[m])}</td>
<td>{vol[m][0]}</td><td>{vol[m][1]}</td><td>{vol[m][2]}</td></tr>"""
    return f"""
<div class="sec" id="stat">
<h3>统计检验: 净仓方向能否预测未来方向? (主口径 ≥8%)</h3>
<h4 style="margin:6px 0">方向一致性 — 增仓后应上涨 / 减仓后应下跌 的比例</h4>
<table class="mini">
<thead><tr><th>品种</th><th>+4周 (n=)</th><th>+8周 (n=)</th><th>+12周 (n=)</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="note b">核心发现: 一致性 43%–64%, 接近抛硬币 (50%)。横盘期间非商业净仓的大幅变化, <b>对后续价格方向几乎没有方向性预测力</b>。白糖+8周达 64% 是唯一略高于随机的点, 但 n=25, 不构成稳健证据。</div>
<h4 style="margin:14px 0 6px">波动幅度 — 事件后收益标准差 vs 全样本基准 (p10–p90 估算)</h4>
<table class="mini">
<thead><tr><th>品种</th><th>+4周 事件SD/基准SD</th><th>+8周</th><th>+12周</th></tr></thead>
<tbody>{rows2}</tbody>
</table>
<div class="note b">波动检验: 除咖啡 +8/+12 周略放大 (1.4–1.6x) 外, 可可/白糖事件后波动与基准相当甚至更低。整体无系统性"横盘蓄势后爆发"证据; 但事件收益平均值显著高于中位数(右偏), 表明少数大行情贡献了大部分回报, 分布厚尾。</div>
</div>"""

# ---------- 汇总章节 ----------
def summary_section():
    rows = ""
    for m in MARKETS:
        n = len(events[m])
        f12 = [e["fwd12"] for e in events[m] if e["fwd12"] is not None]
        f4 = [e["fwd4"] for e in events[m] if e["fwd4"] is not None]
        med12 = sorted(f12)[len(f12)//2] if f12 else None
        med4 = sorted(f4)[len(f4)//2] if f4 else None
        rows += f"""<tr><td class="mk">{esc(M_CN[m])}</td><td>{n}</td>
<td class="ret {cls_ret(med4)}">{fmt_pct(med4)}</td>
<td class="ret {cls_ret(med12)}">{fmt_pct(med12)}</td>
<td>{len(f12) and round(100*sum(1 for v in f12 if v>0)/len(f12),0):.0f}%</td></tr>"""
    return f"""
<div class="sec" id="summary">
<h3>三品种汇总 · 主口径 |Δ净仓|/OI ≥ 8%</h3>
<table class="mini">
<thead><tr><th>品种</th><th>事件数</th><th>事件后4周中位</th><th>事件后12周中位</th><th>12周上涨占比</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="note">基准中位数(任意周买入): 咖啡 +4周 -0.2% / +12周 +0.3%; 可可 +4周 +0.5% / +12周 +1.0%; 白糖 +4周 -0.7% / +12周 -1.5%。<br>
显著性提醒: 事件样本 20–28 个/品种, 统计功效有限, 以下差异仅为方向性参考。</div>
</div>"""

# ---------- 方向分组: 增仓 vs 减仓 ----------
def dir_section():
    blocks = ""
    for m in MARKETS:
        add = [e for e in events[m] if e["dir"]=="增仓"]
        cut = [e for e in events[m] if e["dir"]=="减仓"]
        def med(e2, k):
            vs = [e[f"fwd{k}"] for e in e2 if e[f"fwd{k}"] is not None]
            return sorted(vs)[len(vs)//2] if vs else None
        def posr(e2, k):
            vs = [e[f"fwd{k}"] for e in e2 if e[f"fwd{k}"] is not None]
            return (round(100*sum(1 for v in vs if v>0)/len(vs),0) if vs else None)
        blocks += f"""<tr>
<td class="mk">{esc(M_CN[m])}</td>
<td class="dir">增仓<br><span class="sub">n={len(add)}</span></td>
<td class="ret {cls_ret(med(add,4))}">{fmt_pct(med(add,4))}</td>
<td class="ret {cls_ret(med(add,8))}">{fmt_pct(med(add,8))}</td>
<td class="ret {cls_ret(med(add,12))}">{fmt_pct(med(add,12))}</td>
<td>{posr(add,12)}%</td>
<td class="dir">减仓<br><span class="sub">n={len(cut)}</span></td>
<td class="ret {cls_ret(med(cut,4))}">{fmt_pct(med(cut,4))}</td>
<td class="ret {cls_ret(med(cut,8))}">{fmt_pct(med(cut,8))}</td>
<td class="ret {cls_ret(med(cut,12))}">{fmt_pct(med(cut,12))}</td>
<td>{posr(cut,12)}%</td></tr>"""
    return f"""
<div class="sec" id="dir">
<h3>方向拆分: 净仓增仓 vs 减仓</h3>
<table class="mini">
<thead><tr><th>品种</th>
<th colspan="5">非商业净仓 增仓</th>
<th colspan="5">非商业净仓 减仓</th></tr>
<tr><th></th><th>+4周</th><th>+8周</th><th>+12周</th><th>12周涨占</th><th></th>
<th>+4周</th><th>+8周</th><th>+12周</th><th>12周涨占</th></tr></thead>
<tbody>{blocks}</tbody>
</table>
<div class="note">按方向拆开后样本进一步减半 (单组 n=7–14), 组间中位差异 (咖啡增仓 +6.9% vs 减仓 -0.8%) 受尾部案例影响大, 仅作探索性参考, 不构成稳健信号。</div>
</div>"""

# ---------- 阈值敏感性 ----------
def sens_section():
    rows = ""
    for t in ["0.05", "0.08", "0.1"]:
        tot = d["summary"][t]["tot"]
        per = ""
        for m in MARKETS:
            evs = d["events"][t][m]
            v12 = [e["fwd12"] for e in evs if e["fwd12"] is not None]
            med12 = round(sorted(v12)[len(v12)//2], 2) if v12 else None
            per += f" {esc(M_CN[m])}: n={len(evs)} 中位{fmt_pct(med12)}"
        rows += f"<tr><td>≥{float(t)*100:.0f}%</td><td>{tot}</td><td class='dim'>{per}</td></tr>"
    return f"""
<div class="sec" id="sens">
<h3>阈值敏感性</h3>
<table class="mini">
<thead><tr><th>变动/OI 阈值</th><th>事件总数</th><th>各品种 事件数 · +12周中位</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="note">阈值越高(事件越极端), 可可+12周中位从 +1.0%(≥5%) → +6.6%(≥8%) → +9.2%(≥10%) 单调抬升, 咖啡均值亦抬升, 但 n 仅 11–18 且方向一致性检验显示无预测力, 提示这是"厚尾大行情"而非方向性规律; 白糖 12 周维度无稳定盈余。综合: 极端净仓异动后软商品 12 周内波动可能放大, 但方向不可预知。</div>
</div>"""

# ---------- HTML 骨架 ----------
HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>101号 · 软商品横盘与持仓背离前瞻研究 (2011–2026)</title>
<style>
:root {{
  --bg:#14171c; --card:#1c2028; --card2:#232933; --line:#303642;
  --tx:#e8eaee; --dim:#9aa3b2; --up:#ff5d5d; --down:#38c976; --flat:#c9d1dc;
  --accent:#4c9be8; --warn:#e8a33d;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--tx);
  font:15px/1.6 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:32px 20px 60px; }}
h1 {{ font-size:26px; margin:0 0 6px; letter-spacing:.3px; }}
h3 {{ font-size:19px; margin:0 0 12px; }}
.sub {{ color:var(--dim); font-size:12.5px; font-weight:400; }}
.lede {{ color:var(--dim); margin:8px 0 22px; }}
.meta {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0 26px; }}
.meta span {{ background:var(--card2); border:1px solid var(--line); border-radius:8px;
  padding:6px 12px; font-size:12.5px; color:var(--dim); }}
.sec {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
  padding:22px 22px 10px; margin:22px 0; }}
.note {{ color:var(--dim); font-size:13px; border-left:3px solid var(--accent);
  padding-left:12px; margin:12px 4px 16px; }}
.note.b {{ border-left-color:var(--warn); color:#cbd3de; }}
h4 {{ color:var(--dim); font-weight:600; font-size:14px; }}
.chiprow {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }}
.chip {{ background:var(--card2); border:1px solid var(--line); padding:4px 10px;
  border-radius:20px; font-size:12.5px; color:var(--dim); }}
.chip b {{ color:var(--tx); }}
table {{ border-collapse:collapse; width:100%; margin:8px 0 18px; font-size:13.5px; }}
th {{ text-align:left; background:var(--card2); color:var(--dim); font-weight:600;
  padding:8px 10px; border-bottom:2px solid var(--line); }}
td {{ padding:7px 10px; border-bottom:1px solid #2a2f3a; }}
tr:hover td {{ background:#20242e; }}
.ret {{ font-weight:700; font-variant-numeric:tabular-nums; }}
.up {{ color:var(--up); }} .down {{ color:var(--down); }} .flat {{ color:var(--flat); }}
.na {{ color:var(--dim); }}
.num {{ font-variant-numeric:tabular-nums; }}
.dir {{ font-weight:600; }}
.hidx {{ font-variant-numeric:tabular-nums; }}
.mk {{ font-weight:600; }}
.dim {{ color:var(--dim); font-size:12.5px; }}
table.mini td, table.mini th {{ padding:8px 12px; }}
table.ev td {{ font-variant-numeric:tabular-nums; }}
.cid {{ font-variant-numeric:tabular-nums; }}
footer {{ color:var(--dim); font-size:12px; margin-top:30px; text-align:center; }}
a {{ color:var(--accent); text-decoration:none; }}
</style></head><body><div class="wrap">
<h1>价格横盘 ±5% 期间，非商业净持仓大幅异动后，价格怎么走？</h1>
<div class="lede">2011–2026 · 咖啡 C / 可可 / 糖 11号 (ICE) &nbsp;|&nbsp; 数据: CFTC 周度持仓 (Futures+Options), TradingView 周线 / 自聚合周线</div>
<div class="meta">
  <span>事件定义: 横盘4–12周(周收盘相对起点±5%内) 且 期间 |Δ净仓|/OI ≥ 8%</span>
  <span>前瞻: 事件终点后 +4/+8/+12 周</span>
  <span>基准: 全样本任意周等间隔收益</span>
  <span>口径: 非商业 = 投机净持仓(CFTC Legacy)</span>
  <span>生成: 2026-09-23 (vintage=2026-09)</span>
</div>

{summary_section()}
{stat_section()}
{dir_section()}
{market_section("咖啡 C (ICE)", events["咖啡 C (ICE)"], note="2023 年出现 3 次事件; 2021 年价格历史高位横盘后净仓大幅减仓的案例集中。")}
{market_section("可可 (ICE)", events["可可 (ICE)"], note="2014/2019/2022 事件较集中; 减仓型案例 12 周中位收益明显高于增仓型。")}
{market_section("糖 11号 (ICE)", events["糖 11号 (ICE)"], note="2019/2022 事件较集中; 12 周维度方向性弱于咖啡/可可。")}
{sens_section()}

<div class="sec">
<h3>方法说明与局限</h3>
<ul style="color:var(--dim);font-size:13px;padding-left:20px;line-height:1.9;">
<li>持仓数据为 CFTC Legacy 口径的期货+期权非商业净持仓; 价格用周收盘(周五)对齐 CFTC 周二快照所在周。</li>
<li>横盘窗口以「所有周收盘相对起点 ±5% 内」判定; 4–12周为窗口长度区间, 事件取窗口内 |Δ净仓| 最大的一次并做重叠去重。</li>
<li>"大幅变化"主口径 = |Δ净仓|/OI ≥ 8%（诊断显示咖啡/可可/白糖 p90 约 7–14%），并给出 ≥5%/≥10% 敏感性。</li>
<li>样本量 20–28/品种, 置信区间宽, 结论为方向性参考而非稳健统计信号; 未做多重检验校正。</li>
<li>价格受宏观/基本面外生冲击(如 2014 可可 Ebola、2021 巴西霜冻、疫情)影响, 未单独剔除。</li>
</ul></div>
<footer>101号研究报告 · 农业项目 · 内部研究用</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(HTML)
print("saved:", OUT)