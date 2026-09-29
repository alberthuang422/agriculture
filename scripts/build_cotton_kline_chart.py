# -*- coding: utf-8 -*-
"""
生成 TradingView 风格的 ICE 棉花 K 线图（离线单文件 HTML），
并标注涨跌停触及K线（红▲=涨停收板，绿▼=跌停收板）。

数据源：
- data/price/cotton/ICEUS_DLY_CT1_1D_2010_2026_raw.csv 日线 2010-08 ~ 2026-09（TradingView CT1! 导出，事件表同源）
- data/price/cotton/ct1_weekly_1988_2026.csv           周线 1988-10 ~ 2026-09
- ICE棉花涨跌停触及及T5统计_收盘价口径.csv             涨跌停事件表（2010 起）

输出：cotton_kline_limit.html（workspace 根目录）
库：scripts/lightweight-charts.standalone.production.js（TradingView v4.2.0，已内嵌）
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_ohlc(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "time": r["time"],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
            })
    return rows

def load_events(path):
    evs = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            evs.append({
                "date": r["date"].strip(),
                "side": r["side"].strip(),
                "prev_close": float(r["prev_close"]),
                "limit_cents": int(float(r["limit_cents"])),
                "upper": float(r["upper_limit"]),
                "lower": float(r["lower_limit"]),
                "close": float(r["close"]),
                "t5_date": r["t5_date"].strip(),
                "t5_close": float(r["t5_close"]) if r["t5_close"].strip() else None,
                "t5_ret": float(r["t5_return_pct"]) if r["t5_return_pct"].strip() else None,
            })
    return evs

daily = load_ohlc(os.path.join(ROOT, "data/price/cotton/ICEUS_DLY_CT1_1D_2010_2026_raw.csv"))
weekly = load_ohlc(os.path.join(ROOT, "data/price/cotton/ct1_weekly_1988_2026.csv"))
events = load_events(os.path.join(ROOT, "ICE棉花涨跌停触及及T5统计_收盘价口径.csv"))

# 事件 -> K线标记（日线：精确日期；周线：落入该周/周一锚定的周bar）
def week_anchor(iso_date, week_times):
    """事件日期落入的周bar：取 <= date 的最近一个周锚点（周bar以周一为time）。"""
    import bisect
    i = bisect.bisect_right(week_times, iso_date) - 1
    if i >= 0:
        # 确认事件日在该周锚点之后7天内
        from datetime import date
        a = date.fromisoformat(week_times[i])
        d = date.fromisoformat(iso_date)
        if (d - a).days <= 6:
            return week_times[i]
    return None

daily_times = [b["time"] for b in daily]
weekly_times = [b["time"] for b in weekly]

# 用日线尾段补一根未完结周bar（聚合，非虚构）：落在最后一个周锚点之后的日线
from datetime import date as _date, timedelta as _td
if daily and weekly:
    last_anchor = _date.fromisoformat(weekly[-1]["time"])
    tail = [b for b in daily if _date.fromisoformat(b["time"]) > last_anchor + _td(days=6)]
    if tail:
        # 本周一锚点
        d0 = _date.fromisoformat(tail[0]["time"])
        mon = d0 - _td(days=d0.weekday())
        weekly.append({
            "time": mon.isoformat(),
            "open": tail[0]["open"],
            "high": max(b["high"] for b in tail),
            "low": min(b["low"] for b in tail),
            "close": tail[-1]["close"],
            "_partial": True,
        })
        weekly_times.append(mon.isoformat())
daily_set = set(daily_times)

marks_daily, marks_weekly, ev_daily, ev_weekly = [], [], [], []
missing = []
for e in events:
    if e["date"] in daily_set:
        marks_daily.append({
            "time": e["date"],
            "position": "belowBar" if e["side"] == "up-limit" else "aboveBar",
            "color": "#ef5350" if e["side"] == "up-limit" else "#26a69a",
            "shape": "arrowUp" if e["side"] == "up-limit" else "arrowDown",
            "text": ("涨停 " if e["side"] == "up-limit" else "跌停 ") + f"{e['limit_cents']}¢",
        })
        ev_daily.append(e)
    wa = week_anchor(e["date"], weekly_times)
    if wa:
        marks_weekly.append({
            "time": wa,
            "position": "belowBar" if e["side"] == "up-limit" else "aboveBar",
            "color": "#ef5350" if e["side"] == "up-limit" else "#26a69a",
            "shape": "arrowUp" if e["side"] == "up-limit" else "arrowDown",
            "text": ("涨停" if e["side"] == "up-limit" else "跌停"),
        })
        ev_weekly.append({"anchor": wa, **e})
    else:
        missing.append(e["date"])

# 同一周bar多事件合并文本
from collections import defaultdict
by_week = defaultdict(list)
for m in marks_weekly:
    by_week[m["time"]].append(m)
marks_weekly = []
for t, ms in by_week.items():
    if len(ms) == 1:
        marks_weekly.append(ms[0])
    else:
        ups = sum(1 for m in ms if m["shape"] == "arrowUp")
        marks_weekly.append({
            "time": t,
            "position": "belowBar" if ups >= len(ms) - ups else "aboveBar",
            "color": "#ef5350" if ups >= len(ms) - ups else "#26a69a",
            "shape": "arrowUp" if ups >= len(ms) - ups else "arrowDown",
            "text": f"{ups}涨{len(ms)-ups}跌" if ups and len(ms) - ups else ("涨停×%d" % ups if ups else "跌停×%d" % (len(ms) - ups)),
        })
marks_weekly.sort(key=lambda m: m["time"])

lib_js = open(os.path.join(ROOT, "scripts/lightweight-charts.standalone.production.js"), encoding="utf-8").read()

payload = {
    "daily": daily, "weekly": [{k: v for k, v in b.items() if not k.startswith("_")} for b in weekly],
    "marksDaily": marks_daily, "marksWeekly": marks_weekly,
    "eventsDaily": ev_daily, "eventsWeekly": ev_weekly,
}

app_js = r"""
const D = window.__DATA__;
const chartEl = document.getElementById('chart');
const chart = LightweightCharts.createChart(chartEl, {
  layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc', fontSize: 12 },
  grid: { vertLines: { color: 'rgba(42,46,57,0.5)' }, horzLines: { color: 'rgba(42,46,57,0.5)' } },
  crosshair: { mode: LightweightCharts.CrosshairMode.Normal,
    vertLine: { labelBackgroundColor: '#363a45' }, horzLine: { labelBackgroundColor: '#363a45' } },
  rightPriceScale: { borderColor: '#2a2e39', scaleMargins: { top: 0.12, bottom: 0.12 } },
  timeScale: { borderColor: '#2a2e39', rightOffset: 6, barSpacing: 8, timeVisible: false },
  localization: { locale: 'zh-CN' },
  handleScroll: true, handleScale: true,
});
const series = chart.addCandlestickSeries({
  upColor: '#ef5350', downColor: '#26a69a', borderUpColor: '#ef5350', borderDownColor: '#26a69a',
  wickUpColor: '#ef5350', wickDownColor: '#26a69a',
  priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
});

const legend = document.getElementById('legend');
const info = document.getElementById('info');
const barFromTime = {}; // time -> bar (current interval)
let curEvents = [];

function setIntervalKind(kind){
  const bars = kind === 'daily' ? D.daily : D.weekly;
  const marks = kind === 'daily' ? D.marksDaily : D.marksWeekly;
  curEvents = kind === 'daily' ? D.eventsDaily : D.eventsWeekly;
  series.setData(bars);
  series.setMarkers(marks);
  bars.forEach(b => barFromTime[b.time] = b);
  document.getElementById('interval').textContent = kind === 'daily' ? '日线' : '周线';
  info.style.display = 'none';
  chart.timeScale().fitContent();
}

// 十字光标 OHLC 图例（TradingView 风格，涨红跌绿 + 正负号冗余）
function fmt(v){ return v == null ? ' - ' : v.toFixed(2); }
function sign(v){ return (v >= 0 ? '+' : '') + v; }
chart.subscribeCrosshairMove(p => {
  if (!p.time || !barFromTime[p.time]) { legend.querySelectorAll('.ohlc').forEach(x=>x.textContent=''); return; }
  const b = barFromTime[p.time];
  const prev = barsPrev(b.time);
  const chg = prev ? (b.close - prev.close) : null;
  const cls = b.close >= b.open ? 'u' : 'd';
  const q = s => `<span class="${cls}">${s}</span>`;
  document.getElementById('l-o').innerHTML = q(fmt(b.open));
  document.getElementById('l-h').innerHTML = q(fmt(b.high));
  document.getElementById('l-l').innerHTML = q(fmt(b.low));
  document.getElementById('l-c').innerHTML = q(fmt(b.close) + (chg != null ? ` (${sign(chg.toFixed(2))})` : ''));
});
let barsArr = [];
function barsPrev(t){
  const i = barsArr.findIndex(b => b.time === t);
  return i > 0 ? barsArr[i-1] : null;
}
// 包一层以维护 barsArr
const _setIntervalKind = setIntervalKind;
setIntervalKind = function(kind){
  barsArr = kind === 'daily' ? D.daily : D.weekly;
  _setIntervalKind(kind);
};

// 点击有标记的K线 → 事件详情（涨跌停板 & T5）
const evByTime = {};
function rebuildEvIndex(kind){
  for (const k in evByTime) delete evByTime[k];
  if (kind === 'daily') D.eventsDaily.forEach(e => evByTime[e.date] = e);
  else D.eventsWeekly.forEach(e => { (evByTime[e.anchor] = evByTime[e.anchor] || []).push(e); });
}
let curKind = 'daily';
chart.subscribeClick(p => {
  const t = p.time && p.seriesData ? p.time : (p.time);
  if (!t) { info.style.display = 'none'; return; }
  const ev = curKind === 'daily' ? evByTime[t] : evByTime[t];
  if (!ev) { info.style.display = 'none'; return; }
  const list = Array.isArray(ev) ? ev : [ev];
  info.innerHTML = list.map(e => `
    <div class="ev-title ${e.side === 'up-limit' ? 'u' : 'd'}">▲${e.date} 涨停触及（收板）</div>
    <div class="ev-grid">
      <span>前收</span><b>${e.prev_close.toFixed(2)}</b>
      <span>涨跌停板</span><b>${e.limit_cents}¢</b>
      <span>停板区间</span><b>${e.lower.toFixed(2)} ~ ${e.upper.toFixed(2)}</b>
      <span>收盘</span><b>${e.close.toFixed(2)}</b>
      <span>T5 (${e.t5_date})</span><b>${e.t5_close.toFixed(2)} (${sign(e.t5_ret.toFixed(2))}%)</b>
    </div>`).join('');
  info.style.display = 'block';
});

// 周期切换按钮
document.querySelectorAll('.btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    curKind = btn.dataset.kind;
    rebuildEvIndex(curKind);
    setIntervalKind(curKind);
  });
});

// 初始化
curKind = 'daily';
rebuildEvIndex('daily');
setIntervalKind('daily');
"""

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>ICE 棉花 No.2 (CT) · 涨跌停K线图</title>
<style>
  html, body { margin: 0; padding: 0; background: #131722; height: 100%; overflow: hidden; }
  #wrap { position: relative; width: 100vw; height: 100vh; }
  #chart { position: absolute; inset: 0; }
  #legend { position: absolute; top: 8px; left: 10px; z-index: 5; font: 12px/1.7 'Segoe UI', 'Microsoft YaHei', sans-serif;
    color: #d1d4dc; background: rgba(19,23,34,0.7); padding: 6px 10px; border-radius: 4px; pointer-events: none; }
  #legend .sym { font-weight: 600; font-size: 13px; }
  #legend .u { color: #ef5350; } #legend .d { color: #26a69a; }
  #legend .ohlc b { font-weight: 500; margin-left: 4px; }
  #legend .mark-hint { color: #787b86; font-size: 11px; }
  #legend .mark-hint .u { color: #ef5350; } #legend .mark-hint .d { color: #26a69a; }
  .tabs { position: absolute; top: 8px; right: 12px; z-index: 6; display: flex; gap: 6px; }
  .btn { background: #2a2e39; color: #d1d4dc; border: 1px solid #363a45; border-radius: 4px;
    padding: 4px 12px; font: 12px 'Segoe UI', 'Microsoft YaHei'; cursor: pointer; }
  .btn.active { background: #363a45; border-color: #5d606b; color: #fff; }
  #info { display: none; position: absolute; bottom: 46px; left: 10px; z-index: 5;
    background: rgba(25,29,40,0.95); border: 1px solid #363a45; border-radius: 6px;
    padding: 8px 12px; font: 12px/1.6 'Segoe UI', 'Microsoft YaHei'; color: #d1d4dc; max-width: 320px; }
  #info .ev-title { font-weight: 600; margin-bottom: 4px; }
  #info .ev-title.u { color: #ef5350; } #info .ev-title.d { color: #26a69a; }
  #info .ev-grid { display: grid; grid-template-columns: auto 1fr auto 1fr; gap: 2px 10px; }
  #info .ev-grid span { color: #787b86; } #info .ev-grid b { font-weight: 500; text-align: right; }
</style>
<script>__LIB__</script>
<script>window.__DATA__ = __DATA_JSON__;</script>
</head>
<body>
<div id="wrap">
  <div id="chart"></div>
  <div id="legend">
    <div><span class="sym">ICE 棉花 No.2 (CT1)</span> · <span id="interval">日线</span>
      &nbsp; O<b id="l-o" class="ohlc"></b> H<b id="l-h" class="ohlc"></b> L<b id="l-l" class="ohlc"></b> C<b id="l-c" class="ohlc"></b></div>
    <div class="mark-hint">▲涨停触及（红）/ ▼跌停触及（绿）· 点击带标记K线查看停板与 T5 详情</div>
  </div>
  <div class="tabs">
    <button class="btn active" data-kind="daily">日线</button>
    <button class="btn" data-kind="weekly">周线</button>
  </div>
  <div id="info"></div>
</div>
<script>__APP__</script>
</body>
</html>
"""

html = html.replace("__LIB__", lib_js).replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False)).replace("__APP__", app_js)

out = os.path.join(ROOT, "cotton_kline_limit.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print(f"daily bars: {len(daily)} ({daily[0]['time']} ~ {daily[-1]['time']})")
print(f"weekly bars: {len(weekly)} ({weekly[0]['time']} ~ {weekly[-1]['time']})")
print(f"events total: {len(events)}, marked on daily: {len(ev_daily)}, on weekly: {len(ev_weekly)}, not covered: {missing}")
print(f"out: {out} ({os.path.getsize(out)/1024:.0f} KB)")
