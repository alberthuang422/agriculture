# -*- coding: utf-8 -*-
"""扫描各农产品品种：非商业多头 / 净多头 的全样本历史百分位（1995~最新周）。
口径：Legacy futures-only（deahistfo 本地历史 + deacot2026 增量），/OI 归一为主、绝对手数为辅。
输出：控制台表格 + data/cftc/results_cot/agri_pct_scan_20260930.csv
"""
import csv, json, os, sys, urllib.request, zipfile, io

BASE = r"C:\Users\Administrator\Desktop\农业"
HIST = os.path.join(BASE, "data", "cftc", "results_cot", "agri_cot_futonly_1986_2026.csv")
OUT  = os.path.join(BASE, "data", "cftc", "results_cot", "agri_pct_scan_20260930.csv")
TMP  = os.path.join(BASE, "data", "cftc", "latest")
URL  = "https://www.cftc.gov/files/dea/history/deacot2026.zip"

def fnum(x):
    x = (x or "").strip().replace(",", "")
    try: return float(x)
    except Exception: return None

# ---------- 1. 本地历史 ----------
hist = {}   # market -> list[dict]
with open(HIST, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        m = r["market"].strip()
        hist.setdefault(m, []).append({
            "date": r["date"], "oi": fnum(r["oi"]), "nc_l": fnum(r["nc_l"]),
            "nc_s": fnum(r["nc_s"]), "nc_net": fnum(r["nc_net"]),
        })

# 小麦三合约合计（三合约按报告日对齐求和）
_wl = ["小麦 SRW (CBOT)", "小麦 HRW (KCBT→CBOT)", "小麦 HRS (MGE→MIAX)"]
if all(w in hist for w in _wl):
    _idx = {w: {x["date"]: x for x in hist[w]} for w in _wl}
    _common = sorted(set(_idx[_wl[0]]) & set(_idx[_wl[1]]) & set(_idx[_wl[2]]))
    hist["小麦 三合约合计"] = [{
        "date": d, "oi": sum(_idx[w][d]["oi"] for w in _wl),
        "nc_l": sum(_idx[w][d]["nc_l"] for w in _wl),
        "nc_s": sum(_idx[w][d]["nc_s"] for w in _wl),
        "nc_net": sum(_idx[w][d]["nc_net"] for w in _wl),
    } for d in _common]

# ---------- 2. 下载 deacot2026 ----------
zpath = os.path.join(TMP, "deacot2026.zip")
if not os.path.exists(zpath):
    urllib.request.urlretrieve(URL, zpath)
with zipfile.ZipFile(zpath) as z:
    name = [n for n in z.namelist() if n.lower().endswith(".txt")][0]
    raw = z.read(name).decode("latin-1")
rows = list(csv.reader(io.StringIO(raw)))
# 表头缺第一列：data[i] <- header[i+1]（skill 校准）
dates = sorted({r[1] for r in rows[1:] if len(r) > 40})
last2 = dates[-2:]
print(f"[deacot2026] rows={len(rows)-1}  最新两个报告日={last2}")

NAME_MAP = [
    ("WHEAT-SRW", "小麦 SRW (CBOT)"),
    ("WHEAT-HRW", "小麦 HRW (KCBT→CBOT)"),
    ("WHEAT-HRS", "小麦 HRS (MGE→MIAX)"),
    ("CORN",      "玉米 (CBOT)"),
    ("SOYBEANS",  "大豆 (CBOT)"),
    ("SOYBEAN OIL", "豆油 (CBOT)"),
    ("SOYBEAN MEAL", "豆粕 (CBOT)"),
    ("ROUGH RICE", "糙米 (CBOT)"),
    ("OATS",      "燕麦 (CBOT)"),
    ("CANOLA",    "油菜籽 (ICE)"),
    ("COTTON NO. 2", "棉花 2号 (ICE)"),
    ("SUGAR NO. 11", "糖 11号 (ICE)"),
    ("COFFEE C",  "咖啡 C (ICE)"),
    ("COCOA",     "可可 (ICE)"),
    ("ORANGE JUICE", "冻橙汁 (ICE)"),
    ("LIVE CATTLE", "活牛 (CME)"),
    ("FEEDER CATTLE", "育肥牛 (CME)"),
    ("LEAN HOGS", "瘦肉猪 (CME)"),
    ("MILK, CLASS III", "三级牛奶 (CME)"),
    ("BUTTER",    "黄油 (CME)"),
    ("CHEESE",    "奶酪 (CME)"),
    ("NONFAT",    "脱脂奶粉 (CME)"),
    ("DRY WHEY",  "乳清粉 (CME)"),
]

fresh = {}   # market -> {date, oi, nc_l, nc_s, nc_net}
prev  = {}   # market -> prev week dict
vintage_ok = 0; vintage_bad = []
for r in rows[1:]:
    if len(r) < 13: continue
    nm = r[0].strip()
    if "MINI" in nm.upper() or "MICRO" in nm.upper(): continue
    if r[1] not in last2: continue
    mkey = None
    for kw, cn in NAME_MAP:
        if nm.upper().startswith(kw): mkey = cn; break
    if not mkey: continue
    rec = {"date": f"20{r[1][:2]}-{r[1][2:4]}-{r[1][4:]}",
           "oi": fnum(r[7]), "nc_l": fnum(r[8]), "nc_s": fnum(r[9]),
           "nc_net": (fnum(r[8]) or 0) - (fnum(r[9]) or 0)}
    if r[1] == last2[-1]: fresh[mkey] = rec
    else: prev[mkey] = rec

# vintage 校验：deacot2026 与本地历史 2026-09-01 重叠周比对（以糖为例）
s_local = {x["date"]: x for x in hist.get("糖 11号 (ICE)", [])}.get("2026-09-01")
s_fresh = [x for x in rows[1:] if x[1]=="260901" and x[0].upper().startswith("SUGAR NO. 11")]
if s_local and s_fresh:
    ratio = (fnum(s_fresh[0][7]) or 0) / (s_local["oi"] or 1)
    tag = "OK(futures-only)" if 0.98 < ratio < 1.02 else f"MISMATCH ratio={ratio:.3f}"
    print(f"[vintage check] 糖 2026-09-01 OI 本地={s_local['oi']:.0f} deacot={fnum(s_fresh[0][7]):.0f} -> {tag}")

# 小麦三合约合计（增量行）
wl = ["小麦 SRW (CBOT)", "小麦 HRW (KCBT→CBOT)", "小麦 HRS (MGE→MIAX)"]
for store in (fresh, prev):
    if all(w in store for w in wl):
        store["小麦 三合约合计"] = {
            "date": store[wl[0]]["date"],
            "oi": sum(store[w]["oi"] for w in wl),
            "nc_l": sum(store[w]["nc_l"] for w in wl),
            "nc_s": sum(store[w]["nc_s"] for w in wl),
            "nc_net": sum(store[w]["nc_net"] for w in wl),
        }

# ---------- 3. 分位计算 ----------
def pct(series, v):
    s = [x for x in series if x is not None]
    if not s or v is None: return None
    return 100.0 * sum(1 for x in s if x <= v) / len(s)

results = []
for m, rec in fresh.items():
    base = hist.get(m)
    if base is None:
        print(f"[warn] 本地历史无该品种: {m}"); continue
    last_local_date = max(x["date"] for x in base)
    series = list(base)
    # 增量：把本地缺失的 deacot2026 周次并入样本
    if rec["date"] > last_local_date:
        series = series + [rec]
    p_raw_l   = pct([x["nc_l"] for x in series], rec["nc_l"])
    p_raw_net = pct([x["nc_net"] for x in series], rec["nc_net"])
    p_oi_l    = pct([ (x["nc_l"]/x["oi"]) if x["oi"] else None for x in series],
                    (rec["nc_l"]/rec["oi"]) if rec["oi"] else None)
    p_oi_net  = pct([ (x["nc_net"]/x["oi"]) if x["oi"] else None for x in series],
                    (rec["nc_net"]/rec["oi"]) if rec["oi"] else None)
    d = rec["nc_net"] - prev[m]["nc_net"] if m in prev else None
    results.append({
        "market": m, "date": rec["date"], "oi": rec["oi"],
        "nc_l": rec["nc_l"], "nc_s": rec["nc_s"], "nc_net": rec["nc_net"],
        "p_raw_l": p_raw_l, "p_raw_net": p_raw_net,
        "p_oi_l": p_oi_l, "p_oi_net": p_oi_net, "chg_net": d,
        "n_obs": len(series),
    })

results.sort(key=lambda r: max(r["p_oi_l"] or 0, r["p_oi_net"] or 0, r["p_raw_l"] or 0, r["p_raw_net"] or 0), reverse=True)

# ---------- 4. 输出 ----------
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader(); w.writerows(results)

hdr = f"{'品种':<18}{'报告日':<12}{'OI':>10}{'NC多':>9}{'NC净多':>9}{'多头%raw':>9}{'净多%raw':>9}{'多头%/OI':>9}{'净多%/OI':>9}{'Δ净多':>9}"
print("\n" + hdr); print("-" * len(hdr))
for r in results:
    def fmt(v): return f"{v:.1f}" if v is not None else "  - "
    flag = " <<<" if max(r["p_oi_l"] or 0, r["p_oi_net"] or 0, r["p_raw_l"] or 0, r["p_raw_net"] or 0) >= 95 else ""
    dl = f"{r['chg_net']:+.0f}" if r["chg_net"] is not None else "-"
    print(f"{r['market']:<18}{r['date']:<12}{r['oi']:>10.0f}{r['nc_l']:>9.0f}{r['nc_net']:>9.0f}"
          f"{fmt(r['p_raw_l']):>9}{fmt(r['p_raw_net']):>9}{fmt(r['p_oi_l']):>9}{fmt(r['p_oi_net']):>9}{dl:>9}{flag}")
print(f"\nsaved -> {OUT}")
