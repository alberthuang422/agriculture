# -*- coding: utf-8 -*-
"""103号：棉花价格 × CFTC 非商业多/空/净持仓 四窗联动图（100号白糖四窗图同款）"""
import json, os

ROOT = "/Users/alberthuang/agriculture"
DATA_JSON = ROOT + "/data/cftc/results_cot/cotton_position_price_report103_data.json"
OUT_HTML = ROOT + "/reports/103_棉花CFTC价格多空净四窗图/index.html"

d = json.load(open(DATA_JSON, encoding="utf-8"))
ser = d["series"]
data_js = json.dumps({"series": ser}, ensure_ascii=False, separators=(",", ":"))
n = len(ser)
w0, w1 = ser[0]["date"], ser[-1]["date"]
last = ser[-1]

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ICE棉花价格 × CFTC非商业多/空/净持仓 四窗联动图</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#f5f7fa;color:#1a2330;margin:0;padding:18px 14px 40px;}
  .wrap{max-width:1280px;margin:0 auto;}
  .hd{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:6px;}
  .hd h1{font-size:19px;color:#12365e;margin:0;}
  .hd .meta{font-size:12px;color:#5a6a7d;}
  #chart{width:100%;height:780px;background:#fff;border:1px solid #dde4ec;border-radius:10px;}
  .note{font-size:12px;color:#5a6a7d;margin-top:8px;line-height:1.6;}
  .legend{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 4px;font-size:12.5px;}
  .legend span{display:inline-flex;align-items:center;gap:5px;}
  .sw{display:inline-block;width:14px;height:3px;border-radius:2px;}
  .flipbtn{margin-left:4px;padding:1px 10px;font-size:12px;border:1px solid #56B4E9;background:#fff;color:#2a6fa8;border-radius:12px;cursor:pointer;line-height:1.6;}
  .flipbtn:hover{background:#eaf4fc;}
  .flipbtn.on{background:#56B4E9;color:#fff;}
  .flip-tip{font-size:11px;color:#b47400;margin-top:2px;font-weight:600;}
</style>
</head>
<body>
<div class="wrap">
  <div class="hd">
    <h1>ICE 棉花 2 号价格 × CFTC 非商业多/空/净持仓（周度联动）</h1>
    <span class="meta">__META__</span>
  </div>
  <div class="legend">
    <span><i class="sw" style="background:#12365e"></i>价格（ICE CT1! 周线收盘）</span>
    <span><i class="sw" style="background:#E69F00"></i>非商业多头</span>
    <span id="lg_s"><i class="sw" style="background:#56B4E9"></i>非商业空头 <button id="btnFlip" type="button" class="flipbtn" title="纵向翻转空头曲线，空头增加↓、减少↑">↕ 反转</button></span>
    <span><i class="sw" style="background:#CC79A7"></i>净多（多头−空头）</span>
    <span style="color:#5a6a7d">滚轮/拖拽可联动缩放，悬停十字线对齐四窗</span>
  </div>
  <div id="chart"></div>
  <div class="note">四窗共享时间轴：上一窗=价格走势，下三窗=CFTC 非商业(投机)多/空/净持仓（Futures Only，棉花 2 号 ICE）。多空同增=分歧放大；价跌但净多增=背离（偏空信号）；价涨但净多减=逼空（短期强、持续性弱）。最新（__LASTDATE__）：净多 __NET__ 万手、OI __OI__ 万手，均处多年高位区。</div>
</div>

<script>
var DATA = __DATA_JS__;
var ser = DATA.series;
var N = ser.length;
var x = ser.map(function(r){return r.date;});
var close = ser.map(function(r){return r.close;});
var nc_l = ser.map(function(r){return r.nc_l;});
var nc_s = ser.map(function(r){return r.nc_s;});
var nc_net = ser.map(function(r){return r.nc_net;});

var AX = {splitLine:{lineStyle:{color:'#eef2f7'}}, axisLabel:{color:'#5a6a7d',fontSize:10}};
// 布局: 画布高780, 四窗等高均分填满 (top 8 ~ 746), 底部仅缩放滑块(34px)
// 每窗 H=165, 间隔 GAP=26 → top: 8 / 199 / 390 / 581, 末窗底=746
var GRID_TOP=8, GRID_H=165, GRID_GAP=26;
var grids = [0,1,2,3].map(function(i){
  return {left:64, right:56, top:GRID_TOP + i*(GRID_H+GRID_GAP), height:GRID_H};
});
var xAxis = [0,1,2,3].map(function(i){
  return {type:'category', gridIndex:i, data:x, boundaryGap:false,
          axisLabel:{show:i===3, color:'#5a6a7d', fontSize:10},
          axisLine:{lineStyle:{color:'#c9d4e0'}}, axisTick:{show:i===3}};
});
function seriesOpt(name, data, color, width){
  return {name:name, type:'line', data:data, showSymbol:false,
          lineStyle:{width:width||1.8, color:color}, itemStyle:{color:color},
          emphasis:{focus:'series'}};
}
function buildOption(flipShort){
  var yAxis = [
    {gridIndex:0, type:'value', name:'美分/磅', nameTextStyle:{color:'#5a6a7d',fontSize:10}, ...AX},
    {gridIndex:1, type:'value', name:'手', nameTextStyle:{color:'#5a6a7d',fontSize:10}, ...AX, axisLabel:{color:'#5a6a7d',fontSize:10, formatter:function(v){return (v/10000).toFixed(0)+'万';}}},
    {gridIndex:2, type:'value', name:'手', nameTextStyle:{color:'#5a6a7d',fontSize:10}, ...AX, axisLabel:{color:'#5a6a7d',fontSize:10, formatter:function(v){return (v/10000).toFixed(0)+'万';}}, inverse: !!flipShort},
    {gridIndex:3, type:'value', name:'手', nameTextStyle:{color:'#5a6a7d',fontSize:10}, ...AX, axisLabel:{color:'#5a6a7d',fontSize:10, formatter:function(v){return (v/10000).toFixed(0)+'万';}}, splitLine:{show:true}, min:function(v){return Math.min(0, v.min);}, max:function(v){return Math.max(0, v.max);}}
  ];
  return {
    tooltip:{trigger:'axis', axisPointer:{type:'cross', link:[{xAxisIndex:'all'}]}},
    axisPointer:{link:[{xAxisIndex:'all'}]},
    grid: grids,
    xAxis: xAxis,
    yAxis: yAxis,
    dataZoom:[
      {type:'inside', xAxisIndex:[0,1,2,3], start:0, end:100},
      {type:'slider', xAxisIndex:[0,1,2,3], bottom:2, height:18, start:0, end:100}
    ],
    series:[
      Object.assign(seriesOpt('价格', close, '#12365e', 1.6), {xAxisIndex:0, yAxisIndex:0}),
      Object.assign(seriesOpt('非商业多头', nc_l, '#E69F00', 1.4), {xAxisIndex:1, yAxisIndex:1}),
      Object.assign(seriesOpt('非商业空头', nc_s, '#56B4E9', 1.4), {xAxisIndex:2, yAxisIndex:2}),
      Object.assign(seriesOpt('净多', nc_net, '#CC79A7', 1.6), {xAxisIndex:3, yAxisIndex:3})
    ]
  };
}
var chart = echarts.init(document.getElementById('chart'));
chart.setOption(buildOption(false));
window.addEventListener('resize', function(){chart.resize();});

// ===== 非商业空头窗 反转按钮 =====
var btnFlip = document.getElementById('btnFlip');
var flipOn = false;
function renderFlip(){
  // 全量重建: clear + 重新 setOption, 确保 inverse 切换 100% 生效 (ECharts merge对轴方向更新不可靠)
  chart.clear();
  chart.setOption(buildOption(flipOn));
  btnFlip.classList.toggle('on', flipOn);
  btnFlip.textContent = flipOn ? '↕ 已反转' : '↕ 反转';
  var tip = document.getElementById('flipTip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'flipTip';
    tip.className = 'flip-tip';
    document.querySelector('.legend').appendChild(tip);
  }
  tip.textContent = flipOn ? '非商业空头已纵向镜像：空头增加 ↓、减少 ↑（数值不变，仅翻转坐标轴）' : '';
}
btnFlip.addEventListener('click', function(){
  flipOn = !flipOn;
  renderFlip();
});
</script>
</body>
</html>
"""

HTML = (HTML.replace("__DATA_JS__", data_js)
            .replace("__META__", f"数据窗口 {w0} ~ {w1} · {n} 个 CFTC 报告周 · 单位：价格=美分/磅，持仓=手")
            .replace("__LASTDATE__", w1)
            .replace("__NET__", f"{last['nc_net']/10000:.1f}")
            .replace("__OI__", f"{last['oi']/10000:.1f}"))

os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
open(OUT_HTML, "w", encoding="utf-8").write(HTML)
print("saved:", OUT_HTML, "weeks:", n)
