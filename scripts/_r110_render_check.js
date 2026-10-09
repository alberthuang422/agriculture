// 报告 110（棕榈油基本面全景）无头渲染校验
// 用法：NODE_PATH=<node workspace>/node_modules node scripts/_r110_render_check.js
const puppeteer = require('puppeteer-core');
const path = require('path');
const FILE = path.resolve('reports/110_棕榈油基本面全景_20261007/index.html');
const EDGE = 'C://Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const IDS = ['c1','c2','c3','c4','c5','c6','c7','c8','c9','c10','c11'];

(async () => {
  const errors = [];
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']
  });
  const page = await browser.newPage();
  await page.setViewport({width:1360, height:950});
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });
  page.on('requestfailed', r => {
    const u = r.url();
    if (u.includes('echarts')) errors.push('CDN-FAIL: ' + u);
  });
  await page.goto('file:///' + FILE.replace(/\\/g, '/'), {waitUntil: 'networkidle2', timeout: 120000});
  await new Promise(r => setTimeout(r, 6000));

  const res = await page.evaluate((ids) => {
    // 1) 图表是否真正绘制
    const charts = ids.map(id => {
      const el = document.getElementById(id);
      if (!el) return {id, present: false};
      const cv = el.querySelector('canvas');
      return {id, present: true, canvas: !!cv, size: cv ? (cv.width + 'x' + cv.height) : null};
    });

    // 2) 数值列对齐：表头 th.num 右边界 vs 首行数据 td 右边界
    const align = [];
    document.querySelectorAll('table').forEach((tbl, ti) => {
      const ths = [...tbl.querySelectorAll('tr:first-child th')];
      if (!ths.some(th => th.classList.contains('num'))) return;
      const row = tbl.querySelector('tr:nth-child(2)');
      if (!row) return;
      const tds = [...row.querySelectorAll('td')];
      ths.forEach((th, i) => {
        if (!th.classList.contains('num')) return;
        const td = tds[i];
        if (!td) return;
        const d = Math.round(th.getBoundingClientRect().right - td.getBoundingClientRect().right);
        if (Math.abs(d) > 2) align.push({table: ti, col: th.innerText.trim(), delta: d});
      });
    });

    // 3) 未渲染的 Python 占位符 / 双百分号 / 残留 None-nan
    const txt = document.body.innerText;
    const leftover = (txt.match(/%\+?[-0 #]*\d*\.?\d*[dfs]/g) || []).slice(0, 10);
    const dblPct = (txt.match(/%%/g) || []).length;
    const badTok = ['None','nan','undefined','Traceback','KeyError']
      .filter(k => txt.includes(k));

    return {
      echarts: window.echarts ? window.echarts.version : null,
      charts, align,
      leftover, dblPct, badTok,
      h2: document.querySelectorAll('h2').length,
      h3: document.querySelectorAll('h3').length,
      tables: document.querySelectorAll('table').length,
      kpi: document.querySelectorAll('.kpi').length,
      bodyLen: txt.length,
      scrollH: document.documentElement.scrollHeight,
      emptyCells: [...document.querySelectorAll('td')].filter(td => !td.innerText.trim()
        && !td.querySelector('img,canvas,div')).length
    };
  }, IDS);

  console.log(JSON.stringify({errors, res}, null, 2));
  await browser.close();
  const bad = (res.charts || []).filter(c => !c.canvas).map(c => c.id);
  if (errors.length || bad.length || (res.align || []).length || res.dblPct
      || (res.leftover || []).length || (res.badTok || []).length) {
    console.log('VERDICT: FAIL');
    process.exit(2);
  }
  console.log('VERDICT: PASS');
})().catch(e => { console.log('FATAL: ' + (e && e.message)); process.exit(1); });
