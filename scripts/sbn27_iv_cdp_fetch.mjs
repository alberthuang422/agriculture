// sbn27_iv_cdp_fetch.mjs — Barchart SBN27 期权链抓取 + 全链 Call 隐含波动率计算
// 通路: 本机真实 Chrome(过 CloudFront) + CDP 9222 + 网络层拦截 options API 响应
// 用法: node scripts/sbn27_iv_cdp_fetch.mjs
// 产物: data/price/sugar/sbn27_iv_chain_<timestamp>.json / .csv + sbn27_iv_chain_latest.json
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const CHROME = 'C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe';
const PROFILE = path.join(ROOT, '.workbuddy', 'tmp_chrome_cdp');
const OUTDIR = path.join(ROOT, 'data', 'price', 'sugar');
const PAGE_URL = 'https://www.barchart.com/futures/quotes/SBN27/options/jul-27?futuresOptionsView=merged';
const SYMBOL = 'SBN27';
const EXPIRY = '2027-06-15';       // SBN27 期权到期日
const R_RATE = 0.0;                // Black-76 r=0（商品期货期权惯例）
const R_STOCK = 0.04;              // Black-Scholes（股票模型）r=4%，可调

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------- Black-76 ----------
function normCdf(x) {
  // Abramowitz-Stegun 7.1.26
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989422804014327 * Math.exp(-x * x / 2);
  let p = d * t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  return x >= 0 ? 1 - p : p;
}
function black76Call(F, K, T, sigma, r = R_RATE) {
  if (T <= 0) return Math.max(F - K, 0);
  if (sigma <= 0) return Math.max(F - K, 0);
  const df = Math.exp(-r * T);
  const sT = sigma * Math.sqrt(T);
  const d1 = (Math.log(F / K) + 0.5 * sigma * sigma * T) / sT;
  const d2 = d1 - sT;
  return df * (F * normCdf(d1) - K * normCdf(d2));
}
function bsCall(S, K, T, sigma, r = R_STOCK) {
  // 股票模型 Black-Scholes：标的价直接取期货最新价，贴现率 r=R_STOCK
  if (T <= 0) return Math.max(S - K, 0);
  if (sigma <= 0) return Math.max(S - K * Math.exp(-r * T), 0);
  const sT = sigma * Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / sT;
  const d2 = d1 - sT;
  return S * normCdf(d1) - K * Math.exp(-r * T) * normCdf(d2);
}
function impliedVol(price, pricingFn, underlying, K, T) {
  // bisection；返回 null=数学上无解（权利金≤内在价值/超出上限），返回下界=触底标记
  let lo = 0.005, hi = 5.0;
  if (price <= pricingFn(underlying, K, T, lo)) return lo;   // 触下界
  if (price >= pricingFn(underlying, K, T, hi)) return null; // 超上限
  for (let i = 0; i < 80; i++) {
    const mid = (lo + hi) / 2;
    if (pricingFn(underlying, K, T, mid) < price) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

// ---------- CDP helpers ----------
async function getTargetWs(port) {
  const res = await fetch(`http://127.0.0.1:${port}/json`);
  const targets = await res.json();
  const page = targets.find(t => t.type === 'page');
  if (!page) throw new Error('no page target');
  return page.webSocketDebuggerUrl;
}
function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0; const pending = new Map(); const listeners = [];
    ws.onopen = () => resolve({
      send(method, params = {}) {
        return new Promise((res2, rej2) => {
          const mid = ++id;
          pending.set(mid, { res: res2, rej: rej2 });
          ws.send(JSON.stringify({ id: mid, method, params }));
        });
      },
      onMessage(fn) { listeners.push(fn); },
      close: () => ws.close(),
    });
    ws.onmessage = ev => {
      const msg = JSON.parse(ev.data);
      for (const fn of listeners) fn(msg);
      if (msg.id && pending.has(msg.id)) {
        const p = pending.get(msg.id); pending.delete(msg.id);
        msg.error ? p.rej(new Error(JSON.stringify(msg.error))) : p.res(msg.result);
      }
    };
    ws.onerror = reject;
  });
}

// ---------- main ----------
async function capture(port = 9222) {
  const cdp = await connect(await getTargetWs(port));
  try {
    await cdp.send('Page.enable');
    await cdp.send('Network.enable');
    const hits = [];
    cdp.onMessage(msg => {
      if (msg.method === 'Network.responseReceived') {
        const u = msg.params.response.url;
        if (u.includes('www.barchart.com/proxies/') && msg.params.response.status === 200) {
          hits.push({ requestId: msg.params.requestId, url: u });
        }
      }
    });
    await cdp.send('Page.navigate', { url: PAGE_URL });
    for (let i = 0; i < 60 && hits.length === 0; i++) await sleep(1000);
    await sleep(2500);
    // 找 options 响应
    let chainBody = null, chainUrl = null;
    for (const h of hits) {
      if (!h.url.includes('list=futures.options')) continue;
      for (let k = 0; k < 6 && !chainBody; k++) {
        try { const r = await cdp.send('Network.getResponseBody', { requestId: h.requestId }); chainBody = r.body; chainUrl = h.url; }
        catch { await sleep(1200); }
      }
    }
    if (!chainBody) throw new Error('NO_CHAIN_CAPTURED');
    // 页面内直接 fetch 期货最新价（同源带 cookie）
    let futQuote = null;
    try {
      const r = await cdp.send('Runtime.evaluate', {
        expression: `(async () => {
          const m = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
          const tok = m ? decodeURIComponent(m[1]) : '';
          const u = '/proxies/core-api/v1/quotes/get?symbol=${SYMBOL}&list=futures.quotes&fields=lastPrice%2CbidPrice%2CaskPrice%2CpriceChange%2CtradeTime&raw=1';
          const resp = await fetch(u, { headers: { 'X-XSRF-TOKEN': tok }, credentials: 'include' });
          return await resp.json();
        })()`,
        returnByValue: true, awaitPromise: true, timeout: 20000,
      });
      futQuote = r.result.value;
    } catch (e) { futQuote = { error: String(e).slice(0, 200) }; }
    return { chain: JSON.parse(chainBody), chainUrl, futQuote };
  } finally { cdp.close(); }
}

const num = s => {
  if (s == null) return null;
  const v = parseFloat(String(s).replace(/[,s]/g, ''));
  return Number.isFinite(v) ? v : null;
};

(async () => {
  const t0 = Date.now();
  // 1. 启动 Chrome
  const chrome = spawn(CHROME, [
    '--remote-debugging-port=9222',
    `--user-data-dir=${PROFILE}`,
    '--no-first-run', '--no-default-browser-check', '--window-position=-32000,-32000',
    'about:blank',
  ], { stdio: 'ignore' });
  try {
    for (let i = 0; i < 20; i++) {
      try { await fetch('http://127.0.0.1:9222/json/version'); break; } catch { await sleep(800); }
    }
    // 2. 抓取
    const { chain, chainUrl, futQuote } = await capture();
    const calls = chain.data.Call || [];
    const puts = chain.data.Put || [];

    // 3. 期货价格: 优先 API, 兜底 put-call parity 中位数
    let F = num(futQuote?.data?.[0]?.lastPrice) ?? num(futQuote?.lastPrice);
    let FSource = F != null ? 'futures.quotes_api' : 'parity_estimate';
    if (F == null) {
      const est = [];
      const pmap = new Map(puts.map(p => [num(p.strike), p]));
      for (const c of calls) {
        const K = num(c.strike); const p = pmap.get(K);
        if (!p) continue;
        const cb = num(c.bidPrice), ca = num(c.askPrice), pb = num(p.bidPrice), pa = num(p.askPrice);
        if (cb == null || ca == null || pb == null || pa == null) continue;
        est.push(K + (cb + ca) / 2 - (pb + pa) / 2);
      }
      if (est.length) { est.sort((a, b) => a - b); F = est[Math.floor(est.length / 2)]; }
    }
    if (F == null) throw new Error('NO_UNDERLYING_PRICE');

    // 4. 全链 Call IV（两套模型：Black-76 期货模型 / Black-Scholes 股票模型）
    const T = (Date.parse(EXPIRY + 'T00:00:00Z') - Date.now()) / (365 * 86400e3);
    const rows = calls.map(c => {
      const K = num(c.strike);
      const bid = num(c.bidPrice), ask = num(c.askPrice), last = num(c.lastPrice);
      const hasQuote = bid != null && ask != null && ask > 0;
      const mid = hasQuote ? (bid + ask) / 2 : null;
      const price = mid ?? last;
      let iv76 = null, ivbs = null;
      let flag = 'no_quote';   // 无任何可用于定价的价格
      if (price != null && price > 0) {
        flag = hasQuote ? 'mid' : 'last_fallback';   // 价格来源：双边中间价 / last 回退
        const a = impliedVol(price, black76Call, F, K, T);
        const b = impliedVol(price, bsCall, F, K, T);
        if (a != null) { iv76 = +(a * 100).toFixed(2); if (a <= 0.005) flag += '+floor76'; }
        if (b != null) { ivbs = +(b * 100).toFixed(2); if (b <= 0.005) flag += '+floorbs'; }
        if (iv76 == null && ivbs == null) flag = hasQuote ? 'mid_no_iv' : 'last_no_iv'; // 权利金≤内在价值等无解
      }
      return {
        strike: K,
        bid: bid, ask: ask, mid: mid, last: last,
        volume: num(c.volume), openInterest: num(c.openInterest),
        premium: c.premium ?? null,
        iv76: iv76,      // %，Black-76 期货模型 (r=0)
        ivbs: ivbs,      // %，Black-Scholes 股票模型 (r=4%)
        flag,
      };
    });

    // ATM IV: 距 F 最近的行权价（优先双边报价行权价）
    const okRows = rows.filter(r => r.flag === 'mid');
    const ivRows76 = rows.filter(r => r.iv76 != null);
    const ivRowsbs = rows.filter(r => r.ivbs != null);
    const nearest = (arr) => arr.slice().sort((a, b) => Math.abs(a.strike - F) - Math.abs(b.strike - F))[0] || null;
    const atm76 = nearest(ivRows76), atm76ok = nearest(okRows.filter(r => r.iv76 != null));
    const atmbs = nearest(ivRowsbs), atmbsok = nearest(okRows.filter(r => r.ivbs != null));
    const putOI = puts.reduce((a, p) => a + (num(p.openInterest) || 0), 0);
    const callOI = calls.reduce((a, c) => a + (num(c.openInterest) || 0), 0);

    // 5. 落盘——两套模型分别存放，不混存
    const now = new Date();
    const stamp = now.toISOString().replace(/[-:T]/g, '').slice(0, 13) + 'Z';
    const base = {
      symbol: SYMBOL, generatedAt: now.toISOString(),
      futuresPrice: F, futuresPriceSource: FSource, futuresQuoteRaw: futQuote,
      expiry: EXPIRY, Tyears: +T.toFixed(4),
      callOI, putOI, pcOIRatio: callOI ? +(putOI / callOI).toFixed(3) : null,
      chainApiUrl: chainUrl, nCalls: calls.length, nPuts: puts.length,
    };
    fs.mkdirSync(OUTDIR, { recursive: true });
    const writeSet = (suffix, model, rate, ivKey, atmRow, atmOkRow) => {
      const meta = { ...base, model, rate, atmIV: atmRow?.[ivKey] ?? null, atmStrike: atmRow?.strike ?? null, atmIV_twoSided: atmOkRow?.[ivKey] ?? null, atmStrike_twoSided: atmOkRow?.strike ?? null, rows: rows.map(({ iv76, ivbs, ...rest }) => ({ ...rest, [ivKey]: ivKey === 'iv76' ? iv76 : ivbs })) };
      const fJson = path.join(OUTDIR, `sbn27_${suffix}_chain_${stamp}.json`);
      fs.writeFileSync(fJson, JSON.stringify(meta, null, 1));
      fs.writeFileSync(path.join(OUTDIR, `sbn27_${suffix}_chain_latest.json`), JSON.stringify(meta, null, 1));
      const csv = [`strike,bid,ask,mid,last,volume,openInterest,iv_pct,flag`,
        ...rows.map(r => [r.strike, r.bid ?? '', r.ask ?? '', r.mid ?? '', r.last ?? '', r.volume ?? '', r.openInterest ?? '', r[ivKey] ?? '', r.flag].join(','))].join('\n');
      const fCsv = path.join(OUTDIR, `sbn27_${suffix}_chain_${stamp}.csv`);
      fs.writeFileSync(fCsv, csv);
      return [fJson, fCsv];
    };
    const files76 = writeSet('iv76', 'Black-76 (futures options, r=0)', R_RATE, 'iv76', atm76, atm76ok);
    const filesbs = writeSet('ivbs', 'Black-Scholes (stock model, r=4%)', R_STOCK, 'ivbs', atmbs, atmbsok);
    const iv76s = ivRows76.map(r => r.iv76), ivbss = ivRowsbs.map(r => r.ivbs);

    // 6. 完成（按用户要求：不推送，仅落盘）
    console.log(JSON.stringify({
      status: 'ok', futuresPrice: F, futuresPriceSource: FSource,
      atmIV76: atm76?.iv76 ?? null, atmStrike76: atm76?.strike ?? null,
      atmIV76_twoSided: atm76ok?.iv76 ?? null,
      atmIVbs: atmbs?.ivbs ?? null, atmStrikebs: atmbs?.strike ?? null,
      atmIVbs_twoSided: atmbsok?.ivbs ?? null,
      iv76Min: iv76s.length ? Math.min(...iv76s) : null, iv76Max: iv76s.length ? Math.max(...iv76s) : null,
      ivbsMin: ivbss.length ? Math.min(...ivbss) : null, ivbsMax: ivbss.length ? Math.max(...ivbss) : null,
      pcOIRatio: callOI ? +(putOI / callOI).toFixed(3) : null,
      nCalls: rows.length, withIV76: ivRows76.length, withIVbs: ivRowsbs.length, twoSided: okRows.length,
      files76, filesbs, elapsedSec: +((Date.now() - t0) / 1000).toFixed(1),
    }, null, 1));
  } finally {
    chrome.kill();
    await sleep(1500);
    spawn('taskkill', ['/F', '/T', '/PID', String(chrome.pid)], { stdio: 'ignore' });
  }
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
