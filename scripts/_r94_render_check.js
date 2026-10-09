const puppeteer = require('puppeteer-core');
const path = require('path');
const FILE = path.resolve('reports/94_白糖可贸易国家全景_2000_2026/index.html');
const EDGE = 'C://Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
(async () => {
  const errors = [];
  const browser = await puppeteer.launch({executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']});
  const page = await browser.newPage();
  await page.setViewport({width:1280,height:900});
  page.on('pageerror', e => errors.push('PAGEERROR: '+e.message));
  page.on('console', m => { if(m.type()==='error') errors.push('CONSOLE: '+m.text()); });
  page.on('requestfailed', r => { const u=r.url(); if(u.includes('echarts')) errors.push('CDN-FAIL: '+u); });
  await page.goto('file:///'+FILE.replace(/\\/g,'/'), {waitUntil:'networkidle2',timeout:90000});
  await new Promise(r=>setTimeout(r,4500));

  const r1 = await page.evaluate(() => {
    const ids=['c1','c2','c3','c4','c5','c6','c7','c8'];
    const charts=ids.map(id=>{const el=document.getElementById(id);if(!el)return{id,ok:false};
      const cv=el.querySelector('canvas');return{id,ok:!!cv,painted:cv?cv.width+'x'+cv.height:0};});
    // 附录B 表格对齐检查：比较表头右边界 vs 首行数值单元格右边界
    const tabs=[...document.querySelectorAll('.tabbtn')].map(b=>({t:b.getAttribute('data-tab'),active:b.classList.contains('active'),txt:b.innerText.trim().replace(/\s+/g,' ')}));
    const panes=[...document.querySelectorAll('.tabpane')].map(p=>({id:p.id,show:p.classList.contains('show')}));
    // 对齐：默认显示 pane 的表
    const tbl=document.querySelector('.tabpane.show table');
    let align=null;
    if(tbl){
      const ths=[...tbl.querySelectorAll('tr:first-child th')];
      const tds=[...tbl.querySelectorAll('tr:nth-child(2) td')];
      align=ths.map((th,i)=>{
        const a=th.getBoundingClientRect(), b=tds[i]?tds[i].getBoundingClientRect():null;
        return {col:th.innerText.trim(), thRight:Math.round(a.right), tdRight:b?Math.round(b.right):null,
                delta:b?Math.round(a.right-b.right):null};
      });
    }
    return {echartsVersion:window.echarts?window.echarts.version:null, charts, tabs, panes, align,
            h2:document.querySelectorAll('h2').length, tables:document.querySelectorAll('table').length,
            bodyLen:document.body.innerText.length, scrollH:document.documentElement.scrollHeight};
  });
  // 点击第 3 个 tab（印度）验证切换
  const r2 = await page.evaluate(() => {
    const btns=[...document.querySelectorAll('.tabbtn')];
    btns[2].click();
    return new Promise(res=>setTimeout(()=>{
      const panes=[...document.querySelectorAll('.tabpane')].map(p=>({id:p.id,show:p.classList.contains('show')}));
      const btnState=btns.map(b=>b.classList.contains('active'));
      const shown=document.querySelector('.tabpane.show');
      const cap=shown?shown.querySelector('.panecap').innerText.trim():null;
      const rows=shown?shown.querySelectorAll('table tr').length:0;
      // 校验切换后表格对齐
      const ths=[...shown.querySelectorAll('tr:first-child th')];
      const tds=[...shown.querySelectorAll('tr:nth-child(2) td')];
      const align=ths.map((th,i)=>({col:th.innerText.trim(),
        delta:tds[i]?Math.round(th.getBoundingClientRect().right-tds[i].getBoundingClientRect().right):null}));
      res({activeIdx:btnState.indexOf(true), cap, rows, panes, align});
    },400));
  });
  console.log(JSON.stringify({errors, r1, r2}, null, 2));
  await browser.close();
})().catch(e=>{console.log('FATAL: '+(e&&e.message));process.exit(1);});
