# -*- coding: utf-8 -*-
"""103号：ICE棉花2号 CFTC非商业头寸 x 价格关系 报告数据生成器
改编自 make_report99.py (白糖版)，价格锚定改为周线:
  - 持仓: data/cftc/cotton/cotton_cftc_futonly_1995_2026.csv (Futures Only, 周二快照)
  - 价格: data/price/cotton/ct1_weekly_1988_2026.csv (ICE CT1! 周线, TradingView)
  - 窗口: CFTC 2009-01 起（与99号口径一致）；价格锚定覆盖全部报告周
  - 前瞻以周计: t+1w/t+2w/t+4w/t+8w/t+12w ≈ 白糖版 t+5/10/20/40/60 交易日
  - 阈值按棉花 OI 规模缩放: FLOOR=3000手(白糖5000), S6=1500(2500), S7=10000(20000), S8=6000(10000)
"""
import csv, json, statistics
from datetime import date, timedelta
from collections import defaultdict

ROOT = "/Users/alberthuang/agriculture"
CFTC_CSV = ROOT + "/data/cftc/cotton/cotton_cftc_futonly_1995_2026.csv"
PX_CSV   = ROOT + "/data/price/cotton/ct1_weekly_1988_2026.csv"
OUT_JSON = ROOT + "/data/cftc/results_cot/cotton_position_price_report103_data.json"

FLOOR    = 3000.0    # 单品种明显变动
FLOOR_S6 = 1500.0
FLOOR_S7 = 10000.0
FLOOR_S8 = 6000.0

def fnum(x):
    try: return float(x)
    except: return None

# ========== price (周线) ==========
prows = list(csv.DictReader(open(PX_CSV, encoding="utf-8-sig")))
px_dates = [date.fromisoformat(r["time"]) for r in prows]
px_close = [float(r["close"]) for r in prows]
N = len(px_dates)

def idx_on_or_before(d):
    """报告日(周二)所在周 = 该周一戳记的周线 bar; 若报告日在周一时恰好等于戳记日"""
    import bisect
    i = bisect.bisect_right(px_dates, d) - 1
    return i if i >= 0 else None

def ret_wk(i0, n):
    """从锚点周收盘起第 n 周收益%"""
    i1 = i0 + n
    if i1 >= N or i1 < 0: return None
    return (px_close[i1]/px_close[i0]-1)*100.0

# ========== CFTC ==========
rows = list(csv.DictReader(open(CFTC_CSV, encoding="utf-8-sig")))
weeks, prev = [], None
for r in rows:
    d = date.fromisoformat(r["date"])
    if d < date(2009,1,1):
        prev = r; continue
    rec = {"date": d, "oi": fnum(r["oi"]), "nc_l": fnum(r["nc_l"]), "nc_s": fnum(r["nc_s"]),
           "nc_net": fnum(r["nc_net"]), "c_net": fnum(r["c_net"])}
    if prev:
        rec["d_nc_l"] = rec["nc_l"] - fnum(prev["nc_l"])
        rec["d_nc_s"] = rec["nc_s"] - fnum(prev["nc_s"])
        rec["d_nc_net"] = rec["nc_net"] - fnum(prev["nc_net"])
        rec["d_oi"] = rec["oi"] - fnum(prev["oi"])
    else:
        rec["d_nc_l"]=rec["d_nc_s"]=rec["d_nc_net"]=rec["d_oi"]=None
    prev = r
    i0 = idx_on_or_before(d)
    if i0 is None: continue
    rec["px_idx"] = i0
    # 52周分位 (≈250交易日分位)
    look = max(0, i0-51)
    hist = px_close[look:i0+1]
    rec["px250"] = 100.0*sum(1 for p in hist if p <= px_close[i0])/len(hist) if len(hist)>=26 else None
    rec["w_ret"] = ret_wk(i0, 1)
    weeks.append(rec)

ROOT_D = weeks[0]["date"]; LAST_D = weeks[-1]["date"]
print("anchored weeks:", len(weeks), ROOT_D, "~", LAST_D)

# 高位定义: 52周分位>=80 且 nc_net/OI >= 历史60分位
ratios = sorted(w["nc_net"]/w["oi"] for w in weeks if w["oi"] and w["oi"]>0)
P60 = ratios[int(0.60*(len(ratios)-1))]
def is_high(w):
    return (w["px250"] is not None and w["px250"] >= 80 and w["nc_net"]/w["oi"] >= P60)

# ========== baseline ==========
BLS = {"w": 1, "t1w": 1, "t2w": 2, "t4w": 4, "t8w": 8, "t12w": 12}
def hz_ret(w, n):
    if n is None or n == 1:
        return w["w_ret"]
    return ret_wk(w["px_idx"], n)

baseline = {}
for lbl, n in BLS.items():
    vals = [hz_ret(w,n) for w in weeks]; vals=[v for v in vals if v is not None]
    baseline[lbl] = {"n":len(vals), "mean":round(statistics.mean(vals),2),"med":round(statistics.median(vals),2),
                     "win":round(100*sum(1 for v in vals if v>0)/len(vals),1)} if vals else None
print("baseline t4w:", baseline["t4w"], "t12w:", baseline["t12w"])

# ========== scenarios ==========
scen = {}

def mk(name, wl, detail_keys=()):
    n = len(wl)
    stats = {}
    for lbl, nd in BLS.items():
        vals = [hz_ret(w, nd) for w in wl]; vals=[v for v in vals if v is not None]
        if not vals: continue
        s = {"n":len(vals),"mean":round(statistics.mean(vals),2),"med":round(statistics.median(vals),2),
             "win":round(100*sum(1 for v in vals if v>0)/len(vals),1)}
        if baseline[lbl]:
            s["lift"] = round(s["win"]-baseline[lbl]["win"],1)
        stats[lbl] = s
    # 事件路径 [-8..+16]周 (周线, 直接逐步)
    sums, cnt = defaultdict(float), defaultdict(int)
    for w in wl:
        for wk in range(-8, 17):
            v = ret_wk(w["px_idx"], wk)
            if v is not None: sums[wk]+=v; cnt[wk]+=1
    path = {str(k): round(sums[k]/cnt[k],2) for k in sorted(sums) if cnt[k]}
    detail = []
    if detail_keys:
        for w in wl[:12]:
            row = {}
            for k in detail_keys:
                if k == "close": row[k] = round(px_close[w["px_idx"]],2)
                elif k == "w_ret": row[k] = round(w["w_ret"],2) if w["w_ret"] is not None else None
                elif k == "date": row[k] = str(w[k])
                else: row[k] = w.get(k)
            detail.append(row)
    scen[name] = {"n": n, "stats": stats, "path": path, "detail": detail}

# S1 多头连增 2/3/4周
for k in (2,3,4):
    wl = []
    for i in range(k-1, len(weeks)):
        if all(weeks[j]["d_nc_l"] is not None and weeks[j]["d_nc_l"]>0 for j in range(i-k+1,i+1)):
            wl.append(weeks[i])
    mk(f"S1_nc_l_up_{k}w", wl, ["date","nc_l","d_nc_l","close","w_ret"])

# S1 当周共振 vs 背离
wl1 = []
for i in range(1, len(weeks)):
    if weeks[i]["d_nc_l"] and weeks[i-1]["d_nc_l"] and weeks[i]["d_nc_l"]>0 and weeks[i-1]["d_nc_l"]>0:
        wl1.append(weeks[i])
mk("S1_resonance_up", [w for w in wl1 if (w["w_ret"] or 0) > 1.0])
mk("S1_diverge_down", [w for w in wl1 if (w["w_ret"] or 0) < -1.0])

# S2 高位多头观望
def s2_stall():
    out = []
    for i in range(4, len(weeks)):
        w = weeks[i]
        if not is_high(w) or w["d_nc_l"] is None: continue
        cum = sum(weeks[j]["d_nc_l"] for j in range(i-3,i+1) if weeks[j]["d_nc_l"] is not None)
        if abs(cum) <= 0.005*w["oi"]: out.append(w)
    return out
mk("S2_high_stall", s2_stall(), ["date","close","px250","nc_net"])
scen["S2_high_stall"]["detail"] = []
for w in s2_stall()[:12]:
    i = weeks.index(w)
    cum = sum(weeks[j]["d_nc_l"] for j in range(i-3, i+1) if weeks[j]["d_nc_l"] is not None)
    scen["S2_high_stall"]["detail"].append({
        "date": str(w["date"]), "close": round(px_close[w["px_idx"]],2),
        "px250": round(w["px250"],0) if w["px250"] is not None else None,
        "nc_net": int(w["nc_net"]), "d_nc_l_4w": int(cum),
        "t4w": round(ret_wk(w["px_idx"],4),2) if ret_wk(w["px_idx"],4) is not None else None,
        "t12w": round(ret_wk(w["px_idx"],12),2) if ret_wk(w["px_idx"],12) is not None else None})

# S2b 高位多头继续增仓
def s2b():
    out = []
    for i in range(4, len(weeks)):
        w = weeks[i]
        if not is_high(w) or w["d_nc_l"] is None: continue
        cum = sum(weeks[j]["d_nc_l"] for j in range(i-3,i+1) if weeks[j]["d_nc_l"] is not None)
        if cum >= 0.005*w["oi"]: out.append(w)
    return out
mk("S2b_high_accum", s2b())

# S3 空头明显减仓 (d_nc_s <= -3000)
wl3 = [w for w in weeks if w["d_nc_s"] is not None and w["d_nc_s"] <= -FLOOR]
mk("S3_cover_big", wl3, ["date","nc_s","d_nc_s","close","px250"])
mk("S3_cover_low", [w for w in wl3 if (w["px250"] or 50) < 40])
mk("S3_cover_high", [w for w in wl3 if (w["px250"] or 50) >= 40])

# S5 空头连增 2/3周
for k in (2,3):
    wl = []
    for i in range(k-1, len(weeks)):
        if all(weeks[j]["d_nc_s"] is not None and weeks[j]["d_nc_s"]>0 for j in range(i-k+1,i+1)):
            wl.append(weeks[i])
    mk(f"S5_nc_s_up_{k}w", wl)

# S6 多空同步增仓
mk("S6_both_up", [w for w in weeks if w["d_nc_l"] is not None and w["d_nc_s"] is not None and w["d_nc_l"]>FLOOR_S6 and w["d_nc_s"]>FLOOR_S6])

# S7 OI 萎缩 / 扩张
mk("S7_oi_shrink", [w for w in weeks if w["d_oi"] is not None and w["d_oi"] <= -FLOOR_S7])
mk("S7b_oi_expand", [w for w in weeks if w["d_oi"] is not None and w["d_oi"] >= FLOOR_S7])

# S8 背离
wl8a = [w for w in weeks if w["d_nc_net"] is not None and w["d_nc_net"] >= FLOOR_S8 and (w["w_ret"] or 0) < -1.0]
wl8b = [w for w in weeks if w["d_nc_net"] is not None and w["d_nc_net"] <= -FLOOR_S8 and (w["w_ret"] or 0) > 1.0]
mk("S8a_up_price_down", wl8a, ["date","d_nc_net","w_ret","close"])
mk("S8b_down_price_up", wl8b, ["date","d_nc_net","w_ret","close"])

# ========== 时间序列 (价格 + 持仓, 周度) ==========
series = [{"date": str(w["date"]), "close": round(px_close[w["px_idx"]],2),
           "nc_net": int(w["nc_net"]), "nc_l": int(w["nc_l"]), "nc_s": int(w["nc_s"]),
           "oi": int(w["oi"])} for w in weeks]

# ========== 分段统计 ==========
SEG = [("2009-11 危机后修复", date(2009,1,1), date(2011,7,31)),
       ("2011-14 牛市筑顶回落", date(2011,8,1), date(2014,12,31)),
       ("2015-19 低价磨底", date(2015,1,1), date(2019,12,31)),
       ("2020-22 疫情V型牛", date(2020,1,1), date(2022,5,31)),
       ("2022-25 回落震荡", date(2022,6,1), date(2024,12,31)),
       ("2025+ 当前区间", date(2025,1,1), date(2026,12,31))]

raw_events = {}
def ev_for(key):
    if key == "S1_3w":
        return [weeks[i] for i in range(2, len(weeks)) if all(weeks[j]["d_nc_l"] and weeks[j]["d_nc_l"]>0 for j in range(i-2,i+1))]
    if key == "S2_stall": return s2_stall()
    if key == "S5_2w":
        return [weeks[i] for i in range(1, len(weeks)) if weeks[i]["d_nc_s"] and weeks[i-1]["d_nc_s"] and weeks[i]["d_nc_s"]>0 and weeks[i-1]["d_nc_s"]>0]
    if key == "S7_shrink": return [w for w in weeks if w["d_oi"] is not None and w["d_oi"] <= -FLOOR_S7]
    if key == "S8a": return wl8a
    if key == "S3_cover": return wl3
for key in ["S1_3w","S2_stall","S5_2w","S7_shrink","S8a","S3_cover"]:
    raw_events[key] = ev_for(key)
raw_events["S5_nc_s_up_2w"] = raw_events["S5_2w"]
raw_events["S6_both_up"] = [w for w in weeks if w["d_nc_l"] is not None and w["d_nc_s"] is not None and w["d_nc_l"]>FLOOR_S6 and w["d_nc_s"]>FLOOR_S6]
raw_events["S7_oi_shrink"] = raw_events["S7_shrink"]

seg_stats = {}
for seg_name, d0, d1 in SEG:
    seg_stats[seg_name] = {}
    for key, wl in raw_events.items():
        sub = [w for w in wl if d0 <= w["date"] <= d1]
        v4 = [hz_ret(w,4) for w in sub]; v4=[v for v in v4 if v is not None]
        v12 = [hz_ret(w,12) for w in sub]; v12=[v for v in v12 if v is not None]
        seg_stats[seg_name][key] = {"n":len(sub),
            "t4w": round(statistics.mean(v4),2) if v4 else None,
            "t4w_w": round(100*sum(1 for v in v4 if v>0)/len(v4),0) if v4 else None,
            "t12w": round(statistics.mean(v12),2) if v12 else None,
            "t12w_w": round(100*sum(1 for v in v12 if v>0)/len(v12),0) if v12 else None}

data = {"meta": {"window_cftc": f"{ROOT_D} ~ {LAST_D}", "n_weeks": len(weeks),
                 "window_px": f"{px_dates[0]} ~ {px_dates[-1]}", "seg_labels": [s[0] for s in SEG]},
        "baseline": baseline, "scenarios": scen, "series": series, "seg_stats": seg_stats}
json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False)
print("data saved:", OUT_JSON)
print("S1 2w:", scen["S1_nc_l_up_2w"]["n"], "| S2:", scen["S2_high_stall"]["n"], "| S3:", scen["S3_cover_big"]["n"],
      "| S5 2w:", scen["S5_nc_s_up_2w"]["n"], "| S6:", scen["S6_both_up"]["n"], "| S7:", scen["S7_oi_shrink"]["n"],
      "| S8a:", scen["S8a_up_price_down"]["n"], "| S8b:", scen["S8b_down_price_up"]["n"])

# 关键统计打印 (供撰写叙述)
def show(name):
    s = scen[name]; st = s["stats"]
    line = f"{name} (n={s['n']}): "
    for lbl in ["t1w","t2w","t4w","t8w","t12w"]:
        if lbl in st:
            v = st[lbl]; line += f"{lbl} m={v['mean']} w={v['win']}% lift={v.get('lift')} | "
    print(line)
for nm in ["S1_nc_l_up_2w","S1_nc_l_up_3w","S1_nc_l_up_4w","S1_resonance_up","S1_diverge_down",
           "S2_high_stall","S2b_high_accum","S3_cover_big","S3_cover_low","S3_cover_high",
           "S5_nc_s_up_2w","S5_nc_s_up_3w","S6_both_up","S7_oi_shrink","S7b_oi_expand",
           "S8a_up_price_down","S8b_down_price_up"]:
    show(nm)
print("\n== 分段 (t4w均值/胜率, t12w均值/胜率) ==")
for seg in SEG:
    nm = seg[0]
    row = seg_stats[nm]
    parts = []
    for key in ["S1_3w","S2_stall","S5_2w","S7_shrink","S8a","S3_cover"]:
        v = row.get(key, {})
        if v and v.get("n"):
            parts.append(f"{key}:n{v['n']} {v['t4w']}/{v['t4w_w']}% → {v['t12w']}/{v['t12w_w']}%")
    print(nm, "::", " ; ".join(parts))
