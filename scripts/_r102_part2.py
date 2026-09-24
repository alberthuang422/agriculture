# -*- coding: utf-8 -*-
"""102号报告 HTML 生成器（第二部分：图表 JS + 组装）"""
import io, os, json

BASE = r"C:\Users\Administrator\Desktop\农业"
OUT  = os.path.join(BASE, "reports", "102_白糖两轮牛市全周期复盘_2015_2023")
os.makedirs(OUT, exist_ok=True)

with io.open(os.path.join(BASE, "scripts", "_r102_data.json"), encoding="utf-8") as f:
    P = json.load(f)

J = lambda o: json.dumps(o, ensure_ascii=False)

# ---------------------------------------------------------------- CSS
CSS = """
:root{
  --bg:#14171c; --card:#1c2028; --card2:#232933; --line:#303642;
  --tx:#e8eaee; --dim:#9aa3b2; --dim2:#7c8698;
  --accent:#4c9be8; --warn:#e8a33d;
  /* Okabe-Ito 色弱安全调色板（暗色适配） */
  --oi-blue:#56B4E9; --oi-orange:#E69F00; --oi-sky:#8fd0f5;
  --oi-pink:#CC79A7; --oi-verm:#F0793B; --oi-yellow:#F0E442;
  --up:#ff6b6b; --down:#3ddc97;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--tx);
  font:15px/1.72 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:1200px;margin:0 auto;padding:34px 22px 70px;}
h1{font-size:27px;margin:0 0 8px;letter-spacing:.2px;line-height:1.35;}
h2{font-size:20px;margin:34px 0 4px;padding-top:22px;border-top:1px solid var(--line);}
h3{font-size:16.5px;margin:22px 0 8px;color:#dfe4ec;}
h4{font-size:14px;margin:16px 0 6px;color:var(--dim);font-weight:600;letter-spacing:.4px;}
.lede{color:var(--dim);font-size:13px;margin:6px 0 18px;}
.meta{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 8px;}
.meta span{background:var(--card2);border:1px solid var(--line);border-radius:8px;
  padding:5px 11px;font-size:12px;color:var(--dim);}
.sec{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:22px 24px 14px;margin:18px 0;}
.kicker{background:linear-gradient(90deg,#232933,#1c2028);border:1px solid var(--line);
  border-left:4px solid var(--oi-orange);border-radius:10px;padding:16px 20px;margin:16px 0;}
.kicker b{color:#fff;}
.note{color:var(--dim);font-size:13px;border-left:3px solid var(--accent);
  padding-left:13px;margin:14px 2px;}
.note.b{border-left-color:var(--warn);}
.note.k{border-left-color:var(--oi-pink);}
.warn{background:#2a2218;border:1px solid #5c4a22;border-radius:9px;padding:12px 15px;
  font-size:13.2px;color:#e6d3ab;margin:14px 0;}
.warn b{color:#ffd79a;}
table{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:13.3px;}
th{text-align:left;background:var(--card2);color:var(--dim);font-weight:600;
  padding:9px 10px;border-bottom:2px solid var(--line);white-space:nowrap;}
td{padding:8px 10px;border-bottom:1px solid #2a2f3a;vertical-align:top;}
tr:hover td{background:#20242e;}
.num{font-variant-numeric:tabular-nums;text-align:right;}
td.num,th.num{text-align:right;}
.up{color:var(--up);font-weight:600;}
.down{color:var(--down);font-weight:600;}
.dim{color:var(--dim2);}
.sm{font-size:12.3px;}
.chart{width:100%;height:430px;margin:6px 0 4px;}
.chart.tall{height:520px;}
.chart.short{height:330px;}
.src{color:var(--dim2);font-size:11.8px;margin:2px 2px 14px;line-height:1.6;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
@media(max-width:900px){.grid2{grid-template-columns:1fr;}}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:11px;margin:14px 0;}
.card{background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:13px 15px;}
.card .k{color:var(--dim2);font-size:11.6px;letter-spacing:.3px;}
.card .v{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums;margin:3px 0 1px;}
.card .d{font-size:11.8px;color:var(--dim);}
.tl{position:relative;margin:14px 0 18px;padding-left:26px;}
.tl:before{content:"";position:absolute;left:7px;top:6px;bottom:6px;width:2px;background:var(--line);}
.tl .ev{position:relative;margin:0 0 15px;}
.tl .ev:before{content:"";position:absolute;left:-24px;top:7px;width:10px;height:10px;
  border-radius:50%;background:var(--oi-blue);border:2px solid var(--bg);}
.tl .ev.hot:before{background:var(--oi-orange);}
.tl .ev.peak:before{background:var(--oi-verm);}
.tl .ev.bad:before{background:var(--oi-pink);}
.tl .dt{font-size:12px;color:var(--dim2);font-variant-numeric:tabular-nums;letter-spacing:.4px;}
.tl .ti{font-size:14.3px;font-weight:600;margin:1px 0 2px;}
.tl .tb{font-size:13px;color:var(--dim);line-height:1.66;}
.tl .tb b{color:#dfe4ec;font-weight:600;}
.tag{display:inline-block;padding:1px 8px;border-radius:11px;font-size:11.3px;
  border:1px solid var(--line);background:var(--card2);color:var(--dim);margin-left:6px;}
.tag.b{border-color:#5c4a22;background:#2a2218;color:#ffd79a;}
.tag.r{border-color:#5c2b2b;background:#2a1c1c;color:#ffa8a8;}
.tag.g{border-color:#2b4a5c;background:#1c2530;color:#9fd4f0;}
ul{margin:8px 0 14px;padding-left:22px;}
li{margin:5px 0;}
ol{margin:8px 0 14px;padding-left:22px;}
code{background:var(--card2);border:1px solid var(--line);border-radius:4px;
  padding:1px 5px;font-size:12.4px;color:#c9d6e8;}
footer{color:var(--dim2);font-size:11.8px;margin-top:34px;text-align:center;line-height:1.8;}
a{color:var(--accent);text-decoration:none;}
.hl{background:#2a2218;border-radius:3px;padding:0 4px;color:#ffd79a;}
.hl2{background:#1c2530;border-radius:3px;padding:0 4px;color:#9fd4f0;}
"""

# ---------------------------------------------------------------- JS charts
JS = r"""
var P = __PAYLOAD__;
var OK = {blue:'#56B4E9', orange:'#E69F00', sky:'#8fd0f5', pink:'#CC79A7',
          verm:'#F0793B', yellow:'#F0E442', dim:'#9aa3b2', line:'#303642',
          card:'#1c2028', tx:'#e8eaee'};
var BASE_GRID = {left:62, right:66, top:38, bottom:56, containLabel:false};
function axStyle(){return {axisLine:{lineStyle:{color:OK.line}},axisTick:{lineStyle:{color:OK.line}},
  axisLabel:{color:OK.dim,fontSize:11},splitLine:{lineStyle:{color:'#252b35'}}};}
function tt(){return {trigger:'axis',backgroundColor:'#232933',borderColor:OK.line,
  textStyle:{color:OK.tx,fontSize:12},axisPointer:{lineStyle:{color:'#4a5364'}}};}

/* ============ C1: 归一化价格叠加（两轮对齐底部） ============ */
(function(){
  var el = document.getElementById('c1'); if(!el) return;
  var ch = echarts.init(el, null, {renderer:'canvas'});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:Object.assign(tt(),{formatter:function(ps){
      var s = '<b>距底部第 '+ps[0].value[0]+' 个交易日</b><br/>';
      ps.forEach(function(p){ if(p.value[1]!=null)
        s += p.marker+p.seriesName+': <b>'+(p.value[1]-100).toFixed(1)+'%</b> ('+(p.value[1]/ (p.seriesName.indexOf('2015')>=0?10.39:17.42)).toFixed(2)+' c/lb)<br/>';});
      return s;}}),
    legend:{data:['2015/16 牛市','2023 牛市'],textStyle:{color:OK.dim,fontSize:12},top:4,
      itemWidth:26,itemHeight:3},
    grid:BASE_GRID,
    xAxis:Object.assign(axStyle(),{type:'value',name:'距底部交易日数',nameLocation:'middle',
      nameGap:30,nameTextStyle:{color:OK.dim,fontSize:11},min:0,max:560}),
    yAxis:Object.assign(axStyle(),{type:'value',name:'指数（底部=100）',nameTextStyle:{color:OK.dim,fontSize:11},
      min:80,max:250}),
    series:[
      {name:'2015/16 牛市',type:'line',data:P.N15,showSymbol:false,
       lineStyle:{width:2.6,color:OK.orange},itemStyle:{color:OK.orange},
       markPoint:{symbol:'circle',symbolSize:9,data:[{coord:[282,229.2],itemStyle:{color:OK.verm}}],
         label:{show:true,position:'top',formatter:'顶 +129%',color:OK.verm,fontSize:11,fontWeight:'bold'}}},
      {name:'2023 牛市',type:'line',data:P.N23,showSymbol:false,
       lineStyle:{width:2.6,color:OK.blue,type:'dashed'},itemStyle:{color:OK.blue},
       markPoint:{symbol:'diamond',symbolSize:10,data:[{coord:[267,158.6],itemStyle:{color:OK.sky}}],
         label:{show:true,position:'top',formatter:'顶 +59%',color:OK.sky,fontSize:11,fontWeight:'bold'}},
       markLine:{silent:true,symbol:'none',lineStyle:{color:'#4a5364',type:'dotted'},
         label:{color:OK.dim,fontSize:10,formatter:'第267日'},data:[{xAxis:267}]}}
    ]
  });
  window.addEventListener('resize',function(){ch.resize();});
})();

/* ============ C2 / C3: 价格 × 持仓 双轴 ============ */
function dual(id, W, tag, cMain, cNet, cL, cS, marks){
  var el=document.getElementById(id); if(!el) return;
  var ch=echarts.init(el,null,{renderer:'canvas'});
  var d=W.map(function(r){return r.d;}), c=W.map(function(r){return r.c;}),
      n=W.map(function(r){return r.net;}), l=W.map(function(r){return r.l;}),
      s=W.map(function(r){return r.s;});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:Object.assign(tt(),{formatter:function(ps){
      var s2='<b>'+ps[0].axisValue+'</b><br/>';
      ps.forEach(function(p){
        var v=p.value;
        s2+=p.marker+p.seriesName+': <b>'+(p.seriesName.indexOf('价格')>=0? v.toFixed(2)+' c/lb'
            : (v>=0?'+':'')+v.toLocaleString()+' 手')+'</b><br/>';});
      return s2;}}),
    legend:{data:['价格 (ICE 11号原糖)','非商业净持仓','非商业多头','非商业空头'],
      textStyle:{color:OK.dim,fontSize:11.5},top:4,itemWidth:24,itemHeight:3},
    grid:[{left:60,right:78,top:38,height:'44%'},{left:60,right:78,top:'58%',height:'34%'}],
    xAxis:[
      Object.assign(axStyle(),{type:'category',data:d,gridIndex:0,axisLabel:{show:false},boundaryGap:false}),
      Object.assign(axStyle(),{type:'category',data:d,gridIndex:1,boundaryGap:false,
        axisLabel:{color:OK.dim,fontSize:10,interval:Math.floor(d.length/9),
          formatter:function(v){return v.slice(0,7);}}})],
    yAxis:[
      Object.assign(axStyle(),{type:'value',gridIndex:0,name:'美分/磅',scale:true,
        nameTextStyle:{color:OK.dim,fontSize:10}}),
      Object.assign(axStyle(),{type:'value',gridIndex:1,name:'手',
        nameTextStyle:{color:OK.dim,fontSize:10},
        axisLabel:{color:OK.dim,fontSize:10,formatter:function(v){return (v/10000).toFixed(0)+'万';}}})],
    series:[
      {name:'价格 (ICE 11号原糖)',type:'line',xAxisIndex:0,yAxisIndex:0,data:c,showSymbol:false,
       lineStyle:{width:2.4,color:cMain},itemStyle:{color:cMain},
       areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[
         {offset:0,color:cMain+'33'},{offset:1,color:cMain+'05'}]}},
       markPoint:{data:marks,symbolSize:9}},
      {name:'非商业净持仓',type:'line',xAxisIndex:1,yAxisIndex:1,data:n,showSymbol:false,
       lineStyle:{width:2.2,color:cNet},itemStyle:{color:cNet},
       markLine:{silent:true,symbol:'none',lineStyle:{color:'#4a5364',type:'dashed',width:1},
        label:{color:OK.dim,fontSize:10},data:[{yAxis:0}]}},
      {name:'非商业多头',type:'line',xAxisIndex:1,yAxisIndex:1,data:l,showSymbol:false,
       lineStyle:{width:1.3,color:cL,type:'dotted'},itemStyle:{color:cL}},
      {name:'非商业空头',type:'line',xAxisIndex:1,yAxisIndex:1,data:s,showSymbol:false,
       lineStyle:{width:1.3,color:cS,type:'dashed'},itemStyle:{color:cS}}
    ]
  });
  window.addEventListener('resize',function(){ch.resize();});
}

function idx(W,date){for(var i=0;i<W.length;i++){if(W[i].d>=date)return i;}return -1;}
var i15p=idx(P.W15,'2016-10-04'), i15b=idx(P.W15,'2015-08-25');
dual('c2',P.W15,'2015',OK.orange,OK.pink,OK.sky,OK.blue,[
  {coord:[i15b,P.W15[i15b].c],itemStyle:{color:OK.blue},
   label:{show:true,position:'bottom',formatter:'底 10.39',color:OK.blue,fontSize:10.5,fontWeight:'bold'}},
  {coord:[i15p,P.W15[i15p].c],itemStyle:{color:OK.verm},
   label:{show:true,position:'top',formatter:'顶 23.90',color:OK.verm,fontSize:10.5,fontWeight:'bold'}}
]);
var i23p=idx(P.W23,'2023-11-07'), i23a=idx(P.W23,'2023-04-25'), i23b=idx(P.W23,'2022-10-04');
dual('c3',P.W23,'2023',OK.blue,OK.pink,OK.sky,OK.orange,[
  {coord:[i23b,P.W23[i23b].c],itemStyle:{color:OK.blue},
   label:{show:true,position:'bottom',formatter:'底 17.42',color:OK.blue,fontSize:10.5,fontWeight:'bold'}},
  {coord:[i23a,P.W23[i23a].c],itemStyle:{color:OK.yellow},
   label:{show:true,position:'top',formatter:'净多峰 +27.95万手',color:OK.yellow,fontSize:10.5,fontWeight:'bold'}},
  {coord:[i23p,P.W23[i23p].c],itemStyle:{color:OK.verm},
   label:{show:true,position:'top',formatter:'价峰 28.14',color:OK.verm,fontSize:10.5,fontWeight:'bold'}}
]);

/* ============ C4: ISO 平衡表 vintage 修订路径 ============ */
(function(){
  var el=document.getElementById('c4'); if(!el) return;
  var ch=echarts.init(el,null,{renderer:'canvas'});
  var order=['2015/16','2016/17','2017/18','2021/22','2022/23','2023/24'];
  var cols=[OK.orange,OK.verm,OK.pink,OK.sky,OK.blue,OK.yellow];
  var series=order.map(function(my,i){
    var path=P.vintage[my]||[];
    return {name:my,type:'line',data:path.map(function(p){return [p[0],p[1]];}),
      showSymbol:true,symbolSize:5,symbol:i<3?'circle':'rect',
      lineStyle:{width:2.2,color:cols[i],type:i<3?'solid':'dashed'},itemStyle:{color:cols[i]},
      connectNulls:true};
  });
  var allV=[];order.forEach(function(my){(P.vintage[my]||[]).forEach(function(p){if(allV.indexOf(p[0])<0)allV.push(p[0]);});});
  allV.sort();
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:Object.assign(tt(),{trigger:'item',formatter:function(p){
      return '<b>'+p.seriesName+'</b><br/>vintage '+p.value[0]+': <b>'+(p.value[1]>0?'+':'')+p.value[1].toLocaleString()+' kt</b><br/>'
        + (p.value[1]>0?'<span style="color:#8fd0f5">过剩（利空）</span>':'<span style="color:#F0793B">缺口（利多）</span>');}}),
    legend:{data:order,textStyle:{color:OK.dim,fontSize:11.5},top:4,itemWidth:22,itemHeight:3},
    grid:{left:74,right:34,top:44,bottom:64},
    xAxis:Object.assign(axStyle(),{type:'category',data:allV,name:'预测发布 vintage',
      nameLocation:'middle',nameGap:34,nameTextStyle:{color:OK.dim,fontSize:11},
      axisLabel:{color:OK.dim,fontSize:10,rotate:45}}),
    yAxis:Object.assign(axStyle(),{type:'value',name:'全球产销差 (kt, tel quel)',
      nameTextStyle:{color:OK.dim,fontSize:11},
      axisLabel:{color:OK.dim,fontSize:10,formatter:function(v){return (v/1000).toFixed(0)+'k';}}}),
    series:series.concat([{
      type:'line',data:[],markLine:{silent:true,symbol:'none',
        lineStyle:{color:'#6b7688',width:1.5},
        label:{color:OK.dim,fontSize:10.5,formatter:'0 = 平衡'},
        data:[{yAxis:0}]}}])
  });
  window.addEventListener('resize',function(){ch.resize();});
})();

/* ============ C5: 库存分层（世界 / 锁定层 / 残差） ============ */
(function(){
  var el=document.getElementById('c5'); if(!el) return;
  var ch=echarts.init(el,null,{renderer:'canvas'});
  var ys=P.years.map(String);
  var lock=ys.map(function(y){return P.locked[y];});
  var res=ys.map(function(y){return P.world_end[y]-P.locked[y];});
  var su=ys.map(function(y){var w=P.world[y];return +(w.end/w.disp*100).toFixed(1);});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:Object.assign(tt(),{formatter:function(ps){
      var s='<b>MY '+ps[0].axisValue+'</b><br/>';var tot=0;
      ps.forEach(function(p){if(p.seriesName!=='库消比(右轴)'){tot+=p.value;
        s+=p.marker+p.seriesName+': <b>'+p.value.toLocaleString()+' kt</b><br/>';}});
      s+='<b>合计期末库存: '+tot.toLocaleString()+' kt</b><br/>';
      ps.forEach(function(p){if(p.seriesName==='库消比(右轴)')s+=p.marker+'库消比: <b>'+p.value+'%</b>';});
      return s;}}),
    legend:{data:['锁定层库存（中国国储/印度政策/泰国等）','残差库存（巴西+澳+欧盟+其他）','库消比(右轴)'],
      textStyle:{color:OK.dim,fontSize:11.5},top:4,itemWidth:22,itemHeight:9},
    grid:{left:70,right:66,top:52,bottom:44},
    xAxis:Object.assign(axStyle(),{type:'category',data:ys,name:'市场年（MY2015 = 2015/16榨季）',
      nameLocation:'middle',nameGap:28,nameTextStyle:{color:OK.dim,fontSize:11},
      axisLabel:{color:OK.dim,fontSize:10.5,formatter:function(v){return 'MY'+v.slice(2);}}}),
    yAxis:[Object.assign(axStyle(),{type:'value',name:'期末库存 (kt)',
        nameTextStyle:{color:OK.dim,fontSize:11},
        axisLabel:{color:OK.dim,fontSize:10,formatter:function(v){return (v/1000).toFixed(0)+'k';}}}),
      Object.assign(axStyle(),{type:'value',name:'库消比 %',position:'right',min:20,max:32,
        nameTextStyle:{color:OK.dim,fontSize:11},splitLine:{show:false},
        axisLabel:{color:OK.dim,fontSize:10,formatter:'{value}%'}})],
    series:[
      {name:'锁定层库存（中国国储/印度政策/泰国等）',type:'bar',stack:'s',data:lock,
       itemStyle:{color:OK.blue+'cc'},barWidth:'52%'},
      {name:'残差库存（巴西+澳+欧盟+其他）',type:'bar',stack:'s',data:res,
       itemStyle:{color:OK.orange+'dd'},
       label:{show:true,position:'top',color:OK.orange,fontSize:10.5,fontWeight:'bold',
         formatter:function(p){return (p.value/1000).toFixed(1)+'k';}}},
      {name:'库消比(右轴)',type:'line',yAxisIndex:1,data:su,showSymbol:true,symbolSize:6,
       symbol:'triangle',lineStyle:{width:2.4,color:OK.pink,type:'dashed'},itemStyle:{color:OK.pink}}
    ]
  });
  window.addEventListener('resize',function(){ch.resize();});
})();

/* ============ C6: 国别库存份额（BR/TH/IN/CH） ============ */
(function(){
  var el=document.getElementById('c6'); if(!el) return;
  var ch=echarts.init(el,null,{renderer:'canvas'});
  var ys=P.years.map(String);
  var cfg=[['IN','印度（政策库存）',OK.blue],['TH','泰国（残差累积）',OK.sky],
           ['CH','中国（国储）',OK.pink],['BR','巴西（零库存出口机器）',OK.orange]];
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:Object.assign(tt(),{formatter:function(ps){
      var s='<b>MY '+ps[0].axisValue+'</b><br/>';
      ps.forEach(function(p){
        var tot=P.world_end[p.axisValue];
        s+=p.marker+p.seriesName+': <b>'+p.value.toLocaleString()+' kt</b> ('
          +(p.value/tot*100).toFixed(1)+'% 世界)<br/>';});
      s+='<span style="color:#9aa3b2">世界期末库存: '+tot.toLocaleString()+' kt</span>';
      return s;}}),
    legend:{data:cfg.map(function(x){return x[1];}),textStyle:{color:OK.dim,fontSize:11.5},
      top:4,itemWidth:22,itemHeight:3},
    grid:{left:66,right:34,top:44,bottom:44},
    xAxis:Object.assign(axStyle(),{type:'category',data:ys,boundaryGap:false,
      axisLabel:{color:OK.dim,fontSize:10.5,formatter:function(v){return 'MY'+v.slice(2);}}}),
    yAxis:Object.assign(axStyle(),{type:'value',name:'期末库存 (kt)',
      nameTextStyle:{color:OK.dim,fontSize:11},
      axisLabel:{color:OK.dim,fontSize:10,formatter:function(v){return (v/1000).toFixed(0)+'k';}}}),
    series:cfg.map(function(c,i){
      return {name:c[1],type:'line',data:ys.map(function(y){return P.stocks[c[0]][y];}),
        showSymbol:true,symbolSize:5,symbol:i%2?'rect':'circle',
        lineStyle:{width:2.3,color:c[2],type:i>=2?'dashed':'solid'},itemStyle:{color:c[2]}};})
  });
  window.addEventListener('resize',function(){ch.resize();});
})();

/* ============ C7: 全球产销差（ISO 终值 vs USDA）+ 价格年均 ============ */
(function(){
  var el=document.getElementById('c7'); if(!el) return;
  var ch=echarts.init(el,null,{renderer:'canvas'});
  var mys=[];for(var y=2014;y<=2025;y++)mys.push(y);
  var lab=mys.map(function(y){return y+'/'+String(y+1).slice(2);});
  var iso=mys.map(function(y){var k=y+'/'+String(y+1).slice(2);
    return P.iso_bal[k]? +(P.iso_bal[k].bal*1000).toFixed(0):null;});
  var usda=mys.map(function(y){var w=P.world[String(y)];return w? w.prod+w.imp-w.exp-w.disp:null;});
  var pxAvg=mys.map(function(y){
    // 榨季均价（10月-次年9月）用日历年近似：取该榨季起点年 10月~次年9月
    var a=y+'-10-01', b=(y+1)+'-09-30', sum=0, n=0;
    P.allpx.forEach(function(r){if(r[0]>=a&&r[0]<=b){sum+=r[1];n++;}});
    return n? +(sum/n).toFixed(2):null;});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:Object.assign(tt(),{formatter:function(ps){
      var s='<b>'+ps[0].axisValue+' 榨季</b><br/>';
      ps.forEach(function(p){
        if(p.value==null){s+=p.marker+p.seriesName+': <span style="color:#7c8698">无数据</span><br/>';return;}
        if(p.seriesName.indexOf('价格')>=0) s+=p.marker+p.seriesName+': <b>'+p.value+' c/lb</b><br/>';
        else s+=p.marker+p.seriesName+': <b>'+(p.value>0?'+':'')+p.value.toLocaleString()+' kt</b> '
          +(p.value>0?'▲过剩':'▼缺口')+'<br/>';});
      return s;}}),
    legend:{data:['ISO 全球产销差（终值）','USDA PSD 全球产销差','榨季均价 (右轴)'],
      textStyle:{color:OK.dim,fontSize:11.5},top:4,itemWidth:22,itemHeight:9},
    grid:{left:72,right:64,top:50,bottom:46},
    xAxis:Object.assign(axStyle(),{type:'category',data:lab,
      axisLabel:{color:OK.dim,fontSize:10.5,rotate:38}}),
    yAxis:[Object.assign(axStyle(),{type:'value',name:'产销差 (kt)',
        nameTextStyle:{color:OK.dim,fontSize:11},
        axisLabel:{color:OK.dim,fontSize:10,formatter:function(v){return (v/1000).toFixed(0)+'k';}}}),
      Object.assign(axStyle(),{type:'value',name:'美分/磅',position:'right',splitLine:{show:false},
        nameTextStyle:{color:OK.dim,fontSize:11},axisLabel:{color:OK.dim,fontSize:10}})],
    series:[
      {name:'ISO 全球产销差（终值）',type:'bar',data:iso,barWidth:'34%',
       itemStyle:{color:function(p){return p.value>=0? OK.sky : OK.verm;}}},
      {name:'USDA PSD 全球产销差',type:'bar',data:usda,barWidth:'34%',
       itemStyle:{color:function(p){return p.value>=0? OK.blue+'99' : OK.orange+'cc';}}},
      {name:'榨季均价 (右轴)',type:'line',yAxisIndex:1,data:pxAvg,showSymbol:true,symbolSize:7,
       symbol:'diamond',lineStyle:{width:2.6,color:OK.yellow},itemStyle:{color:OK.yellow}}
    ]
  });
  window.addEventListener('resize',function(){ch.resize();});
})();
"""

with io.open(os.path.join(BASE, "scripts", "_r102_js.txt"), "w", encoding="utf-8") as f:
    f.write(JS.replace("__PAYLOAD__", J({
        "W15": P["W15"], "W23": P["W23"], "N15": P["N15"], "N23": P["N23"],
        "years": P["years"], "world": P["world"], "locked": P["locked"],
        "world_end": P["world_end"], "stocks": P["stocks"], "iso_bal": P["iso_bal"],
        "vintage": P["vintage"], "allpx": P["allpx"],
    })))
print("js ok")
