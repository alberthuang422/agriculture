const fs = require('fs');
const path = 'C:/Users/Administrator/Desktop/农业/reports/100_CFTC四窗联动图_白糖棉花Tab版/index.html';
const html = fs.readFileSync(path, 'utf8');
let fail = 0;
function chk(name, ok, extra) {
  console.log((ok ? 'PASS' : 'FAIL') + ' ' + name + (extra ? ' | ' + extra : ''));
  if (!ok) fail++;
}

// 1. extract inline script and syntax-check
const m = html.match(/<script>([\s\S]*?)<\/script>/);
chk('inline script found', !!m);
if (m) {
  fs.writeFileSync('C:/Users/Administrator/Desktop/农业/data/cftc/latest/_r100_inline.js', m[1]);
}

// 2. parse data arrays
const lines = html.split(/\r?\n/);
function get(name) {
  const ln = lines.find(l => l.startsWith('var ' + name + ' ='));
  return JSON.parse(ln.slice(('var ' + name + ' =').length).replace(/;\s*$/, ''));
}
const S = get('DATA_SUGAR'), C = get('DATA_COTTON');
chk('sugar count == 771', S.series.length === 771, 'n=' + S.series.length);
chk('cotton count == 926', C.series.length === 926, 'n=' + C.series.length);
const sl = S.series[S.series.length - 1], cl = C.series[C.series.length - 1];
chk('sugar last date 2026-09-29', sl.date === '2026-09-29', sl.date);
chk('cotton last date 2026-09-29', cl.date === '2026-09-29', cl.date);
chk('sugar last nc_net == nc_l - nc_s', sl.nc_net === sl.nc_l - sl.nc_s, sl.nc_net + ' vs ' + (sl.nc_l - sl.nc_s));
chk('cotton last nc_net == nc_l - nc_s', cl.nc_net === cl.nc_l - cl.nc_s, cl.nc_net + ' vs ' + (cl.nc_l - cl.nc_s));
// monotonic dates
function mono(a) { for (let i = 1; i < a.length; i++) if (a[i].date <= a[i-1].date) return false; return true; }
chk('sugar dates strictly increasing', mono(S.series));
chk('cotton dates strictly increasing', mono(C.series));

// 3. COT_SNAP parse
const snapMatch = html.match(/var COT_SNAP = \{[\s\S]*?\n\};/);
chk('COT_SNAP found', !!snapMatch);
const COT_SNAP = eval('(' + snapMatch[0].replace('var COT_SNAP = ', '').replace(/;\s*$/, '') + ')');
for (const k of ['sb', 'ct']) {
  const s = COT_SNAP[k];
  chk(k + ' snap date == 2026-09-29 == series last', s.date === '2026-09-29' && (k === 'sb' ? sl.date : cl.date) === s.date, s.date);
  const [ncl, ncs, spd, cml, cms, tll, tls, nrl, nrs] = s.vals;
  chk(k + ' Total Long = NC L + Spreads + Comm L', tll === ncl + spd + cml, tll + ' = ' + ncl + '+' + spd + '+' + cml);
  chk(k + ' Total Short = NC S + Spreads + Comm S', tls === ncs + spd + cms, tls + ' = ' + ncs + '+' + spd + '+' + cms);
  chk(k + ' OI = Total Long + NonRep Long', s.oi === tll + nrl, s.oi + ' = ' + tll + '+' + nrl);
  chk(k + ' OI = Total Short + NonRep Short', s.oi === tls + nrs, s.oi + ' = ' + tls + '+' + nrs);
  chk(k + ' vals/chg/traders lengths', s.vals.length === 9 && s.chg.length === 9 && s.traders.length === 7);
}

// 4. meta consistency
chk('sb meta says 771', html.includes('2011-12 ~ 2026-09 · 771 个 CFTC 报告周'));
chk('ct meta says 926 / 2026-09-29', html.includes('2009-01-06 ~ 2026-09-29 · 926 个 CFTC 报告周'));
chk('ct note updated', html.includes('最新（2026-09-29）：净多 9.7 万手、OI 38.9 万手'));

console.log(fail === 0 ? 'ALL CHECKS PASSED' : fail + ' CHECKS FAILED');
process.exit(fail === 0 ? 0 : 1);
