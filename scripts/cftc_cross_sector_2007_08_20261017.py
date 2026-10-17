# -*- coding: utf-8 -*-
"""跨品种验证：2007末-2008初 非商业投机头寸高企是否为商品市场普遍现象。
口径（遵循项目纪律）：非商净多 nc_net = nc_l - nc_s，归一为 nc_net/OI（%），
百分位 = 各品种自身全样本（1986~2026 futures-only）周度序列内的分位；
另给无前视口径（截至该峰值周的历史）。
窗口 2007-10-01 ~ 2008-03-31，取窗口内 nc_net/OI 峰值周。
输出: data/cftc/results_cot/cross_sector_ncpct_2007_08_20261017.csv
锚校验: 糖 2015-09-01 OI == 818040
"""
import csv, io, os, zipfile, datetime, urllib.request, json

LATEST = r"C:\Users\Administrator\Desktop\农业\data\cftc\latest"
OUT    = r"C:\Users\Administrator\Desktop\农业\data\cftc\results_cot\cross_sector_ncpct_2007_08_20261017.csv"
BARK   = "https://api.day.app/ehGL5HsAui7weuiBEQFaY6"

SECTORS = {
    "软商品": ["糖 11号 (ICE)", "棉花 2号 (ICE)", "咖啡 C (ICE)", "可可 (ICE)"],
    "谷物油籽": ["玉米 (CBOT)", "大豆 (CBOT)", "豆粕 (CBOT)", "豆油 (CBOT)", "小麦 SRW (CBOT)"],
    "贵金属": ["黄金 (COMEX)", "白银 (COMEX)"],
    "工业品(参照)": ["原油 (NYMEX)", "铜 (COMEX)"],
}

def map_market(nm):
    nm = nm.upper().strip()
    if "SPOT" in nm or "MIDAM" in nm: return None
    if nm.startswith("COTTON NO. 2"): return "棉花 2号 (ICE)"
    if nm.startswith("SUGAR NO. 11"): return "糖 11号 (ICE)"
    if nm.startswith("COFFEE C"):     return "咖啡 C (ICE)"
    if nm.startswith("COCOA"):        return "可可 (ICE)"
    if nm.startswith("CORN"):         return "玉米 (CBOT)"
    if nm.startswith("SOYBEANS"):     return "大豆 (CBOT)"
    if nm.startswith("SOYBEAN OIL"):  return "豆油 (CBOT)"
    if nm.startswith("SOYBEAN MEAL"): return "豆粕 (CBOT)"
    if nm.startswith("WHEAT"):
        if "BLACK SEA" in nm or "DURUM" in nm or "WHITE" in nm: return None
        if "WHEAT-SRW" in nm or ("WHEAT " in nm and "CHICAGO" in nm): return "小麦 SRW (CBOT)"
        return None
    if nm.startswith("GOLD") and "COMMODITY EXCHANGE" in nm:   return "黄金 (COMEX)"
    if nm.startswith("SILVER") and "COMMODITY EXCHANGE" in nm: return "白银 (COMEX)"
    if nm.startswith("CRUDE OIL, LIGHT") and "MERCANTILE" in nm and "BRENT" not in nm: return "原油 (NYMEX)"
    if nm.startswith("COPPER") and "COMMODITY EXCHANGE" in nm: return "铜 (COMEX)"
    return None

W_START, W_END = "2007-10-01", "2008-03-31"
best = {}        # market -> date -> (oi, nc_net)  保留 OI 较大者
n_raw = 0
anchor_ok = None

zips = (["deacot1986_2016.zip"] + [f"deacot{y}.zip" for y in range(2017, 2026)]
        + ["deacot2026_fresh_20261017.zip"])
for zn in zips:
    zp = os.path.join(LATEST, zn)
    if not os.path.exists(zp):
        print("跳过缺失:", zn); continue
    z = zipfile.ZipFile(zp)
    tn = [x for x in z.namelist() if x.lower().endswith(".txt")][0]
    for r in csv.reader(io.StringIO(z.read(tn).decode("latin-1"))):
        if len(r) < 13: continue
        m = map_market(r[0])
        if not m: continue
        try:
            yy = int(r[1][:2]); d = f"{19 if yy >= 70 else 20}{r[1][:2]}-{r[1][2:4]}-{r[1][4:]}"
            oi = float(r[7]); ncl = float(r[8]); ncs = float(r[9])
        except ValueError:
            continue
        n_raw += 1
        if m == "糖 11号 (ICE)" and d == "2015-09-01" and oi == 818040.0:
            anchor_ok = True
        cur = best.setdefault(m, {}).get(d)
        if cur is None or oi > cur[0]:
            best[m][d] = (oi, ncl - ncs, ncl)

assert anchor_ok, "锚校验失败"
print(f"原始行 {n_raw}，品种 {len(best)}")

def pctile(sample, v):
    return 100.0 * sum(1 for x in sample if x < v) / len(sample)

rows = []
for sector, mkts in SECTORS.items():
    for m in mkts:
        d2 = best.get(m)
        if not d2:
            print("缺品种:", m); continue
        series = sorted(d2.items())
        vals = [(d, 100.0 * nn / oi, ncl) for d, (oi, nn, ncl) in series if oi > 0]
        win = [(d, v, ncl) for d, v, ncl in vals if W_START <= d <= W_END]
        pk_d, pk_v, pk_ncl = max(win, key=lambda x: x[1])
        full = [v for _, v, _ in vals]
        exant = [v for d, v, _ in vals if d <= pk_d]
        prior = [(d, v, ncl) for d, v, ncl in vals if d < W_START]
        prior_max_n = max(v for _, v, _ in prior) if prior else None
        prior_max_l = max(ncl for _, _, ncl in prior) if prior else None
        win_max_l = max(ncl for _, _, ncl in win)
        rec_norm = prior_max_n is not None and pk_v > prior_max_n
        rec_abs = prior_max_l is not None and win_max_l > prior_max_l
        n_hi = sum(1 for d, v, _ in win if v >= 90)  # 窗口内进入历史90分位以上的周数
        rows.append({"sector": sector, "market": m, "peak_date": pk_d,
                     "ncnet_oi_pct": round(pk_v, 1),
                     "pctile_full": round(pctile(full, pk_v), 1),
                     "pctile_exante": round(pctile(exant, pk_v), 1),
                     "record_norm": rec_norm, "record_abs_longs": rec_abs,
                     "prior_max_ncnet_oi": round(prior_max_n, 1) if prior_max_n is not None else None,
                     "weeks_ge90_in_window": n_hi, "n_weeks": len(full),
                     "start": vals[0][0], "end": vals[-1][0]})

rows.sort(key=lambda r: -r["pctile_full"])
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("saved ->", OUT)

hdr = f"{'板块':<8}{'品种':<16}{'峰值周':<12}{'净多/OI%':>9}{'破纪录(净多/OI)':>12}{'破纪录(绝对多头)':>12}{'无前视分位':>10}"
print(hdr)
for r in rows:
    print(f"{r['sector']:<8}{r['market']:<16}{r['peak_date']:<12}{r['ncnet_oi_pct']:>9.1f}"
          f"{('是' if r['record_norm'] else '否'):>12}{('是' if r['record_abs_longs'] else '否'):>14}{r['pctile_exante']:>10.1f}")

n_rec = sum(1 for r in rows if r["record_norm"] or r["record_abs_longs"])
msg = (f"修正判定:以07-10~08-03为节点,窗口峰值周是否刷新此前全部历史纪录(futures-only,1986起):\n"
       + "\n".join(f"{r['market']}: 峰值周{r['peak_date']} 净多/OI{r['ncnet_oi_pct']}%"
                   f" 破净多/OI纪录:{'是' if r['record_norm'] else '否'}"
                   f" 破绝对多头手数纪录:{'是' if r['record_abs_longs'] else '否'}"
                   f" (无前视分位{r['pctile_exante']})" for r in rows)
       + f"\n合计{n_rec}/{len(rows)}个品种当时刷新了至少一项历史纪录。")
body = json.dumps({"title": "07末-08初投机头寸高企: 跨品种验证",
                   "body": msg, "group": "Sugar"}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(BARK, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    print("Bark:", resp.read().decode("utf-8")[:120])
