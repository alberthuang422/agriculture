/* 106号报告渲染验证：playwright-core + 本机 Chrome headless，检查 canvas + JS 报错。用完即退。 */
const { chromium } = require('playwright-core');

(async () => {
  const errors = [];
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE-ERROR: ' + m.text()); });
  page.on('requestfailed', r => {
    if (r.url().includes('echarts')) errors.push('CDN-FAIL: ' + r.url());
  });
  await page.goto('file:///Users/alberthuang/agriculture/reports/106_美国棉花出口同期对比_20260925/index.html', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(4000);
  const res = await page.evaluate(() => ({
    canvases: document.querySelectorAll('canvas').length,
    charts: ['c1','c2','c3','c4','c5'].map(id => {
      const el = document.getElementById(id);
      return el ? el.querySelectorAll('canvas').length : -1;
    }),
    tableRows: document.querySelectorAll('#tbl tr').length,
  }));
  console.log(JSON.stringify(res));
  console.log('errors:', errors.length ? errors.join(' | ').slice(0, 1000) : 'none');
  await browser.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
