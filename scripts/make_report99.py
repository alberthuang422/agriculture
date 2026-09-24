# -*- coding: utf-8 -*-
"""99号：ICE原糖 CFTC非商业头寸 x 价格关系 报告生成器
数据全部实时计算内嵌, 图表用 ECharts5, Okabe-Ito 色盲安全配色, 涨红跌绿
窗口: CFTC 2009-01 起; 价格锚定 2011-12~2026-09 (768 报告周)
"""
import csv, json, math, statistics
from datetime import date, timedelta
from collections import defaultdict

ROOT = "C:/Users/Administrator/Desktop/农业"
CFTC_CSV = ROOT + "/data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"
PX_CSV   = ROOT + "/data/price/sugar/sb_price_daily.csv"
OUT_HTML = ROOT + "/reports/99_白糖CFTC持仓价格关系_2009_2026/index.html"
OUT_JSON = ROOT + "/data/cftc/results_cot/sugar_position_price_report99_data.json"

def fnum(x):
    try: return float(x)
    except: return None

# ========== price ==========
prows = list(csv.DictReader(open(PX_CSV, encoding="utf-8-sig")))
px_dates = [date.fromisoformat(r["time"]) for r in prows]
px_close = [float(r["close"]) for r in prows]
N = len(px_dates)

def idx_on_or_before(d):
    import bisect
    i = bisect.bisect_right(px_dates, d) - 1
    return i if i >= 0 else None

def ret_idx(i0, n):
    i1 = i0 + n
    if i1 >= N or i1 < 0: return None
    return (px_close[i1]/px_close[i0]-1)*100.0

def path_weekly(i0, before=8, after=16):
    out = {}
    for w in range(-before, after+1):
        out[w] = ret_idx(i0, w*5)
    return out

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
    look = max(0, i0-249)
    hist = px_close[look:i0+1]
    rec["px250"] = 100.0*sum(1 for p in hist if p <= px_close[i0])/len(hist) if len(hist)>=60 else None
    rec["w_ret"] = ret_idx(i0, 5)
    rec["mom4w"] = ret_idx(i0, -20)
    rec["mom12w"] = ret_idx(i0, -60)
    weeks.append(rec)

ROOT_D = weeks[0]["date"]; LAST_D = weeks[-1]["date"]

# 高位定义
ratios = sorted(w["nc_net"]/w["oi"] for w in weeks if w["oi"] and w["oi"]>0)
P60 = ratios[int(0.60*(len(ratios)-1))]
def is_high(w):
    return (w["px250"] is not None and w["px250"] >= 80 and w["nc_net"]/w["oi"] >= P60)

# ========== baseline ==========
BLS = {"w": None, "t5": 5, "t10": 10, "t20": 20, "t40": 40, "t60": 60}
def hz_ret(w, n):
    if n is None:
        j = min(N-1, max(w["px_idx"]+5, idx_on_or_before(w["date"]+timedelta(days=7)) or w["px_idx"]))
        return (px_close[j]/px_close[w["px_idx"]]-1)*100.0 if j > w["px_idx"] else None
    return ret_idx(w["px_idx"], n)

baseline = {}
for lbl, n in BLS.items():
    vals = [hz_ret(w,n) for w in weeks]; vals=[v for v in vals if v is not None]
    baseline[lbl] = {"n":len(vals), "mean":round(statistics.mean(vals),2),"med":round(statistics.median(vals),2),
                     "win":round(100*sum(1 for v in vals if v>0)/len(vals),1)} if vals else None

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
    # 事件路径 [-8..+16]周
    sums, cnt = defaultdict(float), defaultdict(int)
    for w in wl:
        for wk, v in path_weekly(w["px_idx"]).items():
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
# S2 详情补齐 4周多头累计变动 + t20/t60 (周记录无此字段, 单独计算)
scen["S2_high_stall"]["detail"] = []
for w in s2_stall()[:12]:
    i = weeks.index(w)
    cum = sum(weeks[j]["d_nc_l"] for j in range(i-3, i+1) if weeks[j]["d_nc_l"] is not None)
    scen["S2_high_stall"]["detail"].append({
        "date": str(w["date"]), "close": round(px_close[w["px_idx"]],2),
        "px250": round(w["px250"],0) if w["px250"] is not None else None,
        "nc_net": int(w["nc_net"]), "d_nc_l_4w": int(cum),
        "t20": round(ret_idx(w["px_idx"],20),2) if ret_idx(w["px_idx"],20) is not None else None,
        "t60": round(ret_idx(w["px_idx"],60),2) if ret_idx(w["px_idx"],60) is not None else None})

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

# S3 空头明显减仓 (d_nc_s <= -5000)
wl3 = [w for w in weeks if w["d_nc_s"] is not None and w["d_nc_s"] <= -5000]
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
mk("S6_both_up", [w for w in weeks if w["d_nc_l"] is not None and w["d_nc_s"] is not None and w["d_nc_l"]>2500 and w["d_nc_s"]>2500])

# S7 OI 萎缩 / 扩张
mk("S7_oi_shrink", [w for w in weeks if w["d_oi"] is not None and w["d_oi"] <= -20000])
mk("S7b_oi_expand", [w for w in weeks if w["d_oi"] is not None and w["d_oi"] >= 20000])

# S8 背离
wl8a = [w for w in weeks if w["d_nc_net"] is not None and w["d_nc_net"] >= 10000 and (w["w_ret"] or 0) < -1.0]
wl8b = [w for w in weeks if w["d_nc_net"] is not None and w["d_nc_net"] <= -10000 and (w["w_ret"] or 0) > 1.0]
mk("S8a_up_price_down", wl8a, ["date","d_nc_net","w_ret","close"])
mk("S8b_down_price_up", wl8b, ["date","d_nc_net","w_ret","close"])

# ========== 时间序列 (价格 + nc_net) 周度 ==========
series = [{"date": str(w["date"]), "close": round(px_close[w["px_idx"]],2),
           "nc_net": int(w["nc_net"]), "nc_l": int(w["nc_l"]), "nc_s": int(w["nc_s"]),
           "oi": int(w["oi"])} for w in weeks]

# ========== 分段 (2012-2016/2017-2019/2020-2024/2025+) 关键场景 t20/t60 胜率 ==========
SEG = [("2012-16 熊市回落", date(2012,1,1), date(2016,12,31)),
       ("2017-19 底部区间", date(2017,1,1), date(2019,12,31)),
       ("2020-24 上行震荡", date(2020,1,1), date(2024,12,31)),
       ("2025+ 缺口行情", date(2025,1,1), date(2026,12,31))]
seg_table = {}
for name, d0, d1 in SEG:
    row = {}
    for wk, wl_key in [("S1_多头连增3周", scen["S1_nc_l_up_3w"]), ("S2_高位观望", scen["S2_high_stall"]),
                       ("S5_空头连增2周", scen["S5_nc_s_up_2w"]), ("S7_OI萎缩", scen["S7_oi_shrink"]),
                       ("S8a_背离增仓价跌", scen["S8a_up_price_down"])]:
        # 需要原始事件: 从 scen 拿不到周对象, 用 stats 近似 (已在 mk 里全样本), 改为在构建时存 seg 统计
        pass
    seg_table[name] = row

# 修正: 对关键场景做分段统计 (直接基于事件周列表重算)
raw_events = {}
def ev_for(key):
    if key == "S1_3w":
        return [weeks[i] for i in range(2, len(weeks)) if all(weeks[j]["d_nc_l"] and weeks[j]["d_nc_l"]>0 for j in range(i-2,i+1))]
    if key == "S2_stall": return s2_stall()
    if key == "S5_2w":
        return [weeks[i] for i in range(1, len(weeks)) if weeks[i]["d_nc_s"] and weeks[i-1]["d_nc_s"] and weeks[i]["d_nc_s"]>0 and weeks[i-1]["d_nc_s"]>0]
    if key == "S7_shrink": return [w for w in weeks if w["d_oi"] is not None and w["d_oi"] <= -20000]
    if key == "S8a": return wl8a
    if key == "S3_cover": return wl3
for key in ["S1_3w","S2_stall","S5_2w","S7_shrink","S8a","S3_cover"]:
    raw_events[key] = ev_for(key)
# 分段统计的场景 key 与 HTML 场景名对齐 (供 t_s5/t_s6/t_s7 分段子表)
raw_events["S5_nc_s_up_2w"] = raw_events["S5_2w"]
raw_events["S6_both_up"] = [w for w in weeks if w["d_nc_l"] is not None and w["d_nc_s"] is not None and w["d_nc_l"]>2500 and w["d_nc_s"]>2500]
raw_events["S7_oi_shrink"] = raw_events["S7_shrink"]

seg_stats = {}
for seg_name, d0, d1 in SEG:
    seg_stats[seg_name] = {}
    for key, wl in raw_events.items():
        sub = [w for w in wl if d0 <= w["date"] <= d1]
        v20 = [hz_ret(w,20) for w in sub]; v20=[v for v in v20 if v is not None]
        v60 = [hz_ret(w,60) for w in sub]; v60=[v for v in v60 if v is not None]
        seg_stats[seg_name][key] = {"n":len(sub),
            "t20": round(statistics.mean(v20),2) if v20 else None,
            "t20w": round(100*sum(1 for v in v20 if v>0)/len(v20),0) if v20 else None,
            "t60": round(statistics.mean(v60),2) if v60 else None,
            "t60w": round(100*sum(1 for v in v60 if v>0)/len(v60),0) if v60 else None}

data = {"meta": {"window_cftc": f"{ROOT_D} ~ {LAST_D}", "n_weeks": len(weeks),
                 "window_px": f"{px_dates[0]} ~ {px_dates[-1]}", "seg_labels": [s[0] for s in SEG]},
        "baseline": baseline, "scenarios": scen, "series": series, "seg_stats": seg_stats}
json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False)
print("data saved, n_weeks:", len(weeks))
print("S1 2w:", scen["S1_nc_l_up_2w"]["n"], "| S2:", scen["S2_high_stall"]["n"], "| S3:", scen["S3_cover_big"]["n"],
      "| S5 2w:", scen["S5_nc_s_up_2w"]["n"], "| S6:", scen["S6_both_up"]["n"], "| S7:", scen["S7_oi_shrink"]["n"],
      "| S8a:", scen["S8a_up_price_down"]["n"], "| S8b:", scen["S8b_down_price_up"]["n"])
print("baseline t20:", baseline["t20"], "t60:", baseline["t60"])