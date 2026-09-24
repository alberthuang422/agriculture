/* 102号报告渲染验证：headless Edge 加载，检查 canvas 绘制 + JS 报错。用完即退出，不常驻。 */
const puppeteer = require('puppeteer-core');
const path = require('path');

const FILE = path.resolve('reports/102_白糖两轮牛市全周期复盘_2015_2023/index.html');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

(async () => {
  const errors = [], warns = [];
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });

  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => {
    const t = m.type();
    if (t === 'error') errors.push('CONSOLE-ERROR: ' + m.text());
    else if (t === 'warning') warns.push('WARN: ' + m.text());
  });
  page.on('requestfailed', r => {
    const u = r.url();
    if (u.includes('echarts')) errors.push('CDN-FAIL: ' + u + ' | ' + (r.failure() || {}).errorText);
  });

  await page.goto('file:///' + FILE.replace(/\\/g, '/'), {
    waitUntil: 'networkidle2', timeout: 90000,
  });
  await new Promise(r => setTimeout(r, 4000));

  const res = await page.evaluate(() => {
    const ids = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8'];
    const charts = ids.map(id => {
      const el = document.getElementById(id);
      if (!el) return { id, ok: false, reason: 'container missing' };
      const cv = el.querySelector('canvas');
      if (!cv) return { id, ok: false, reason: 'no canvas (init failed)' };
      const w = cv.width, h = cv.height;
      let nonBlank = -1;
      try {
        const ctx = cv.getContext('2d');
        const d = ctx.getImageData(0, 0, Math.min(w, 1200), Math.min(h, 600)).data;
        let painted = 0;
        for (let i = 3; i < d.length; i += 4 * 37) if (d[i] > 8) painted++;
        nonBlank = painted;
      } catch (e) { nonBlank = 'ERR:' + e.message; }
      const inst = window.echarts && window.echarts.getInstanceByDom(el);
      return { id, ok: true, w, h, paintedSamples: nonBlank, hasInstance: !!inst };
    });
    return {
      echartsLoaded: !!(window.echarts && window.echarts.version),
      echartsVersion: window.echarts ? window.echarts.version : null,
      charts,
      h2: document.querySelectorAll('h2').length,
      h3: document.querySelectorAll('h3').length,
      tables: document.querySelectorAll('table').length,
      bodyLen: document.body.innerText.length,
      docHeight: document.documentElement.scrollHeight,
      title: document.title,
    };
  });

  console.log(JSON.stringify({ errors, warnCount: warns.length, warns: warns.slice(0, 6), res }, null, 2));
  await browser.close();
})().catch(e => { console.log('FATAL: ' + (e && e.message)); process.exit(1); });
