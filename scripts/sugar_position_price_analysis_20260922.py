# -*- coding: utf-8 -*-
"""99号：ICE原糖 CFTC 非商业/商业/OI 持仓 x 价格关系统计研究（2012-2026）
场景:
  S1 非商业多头(nc_l)持续增仓 k=2/3/4 周            -> 同期周涨跌 + 前瞻
  S2 高位 + 非商业多头增仓停滞(横盘观望)           -> 前瞻演绎
  S3 非商业空头(nc_s)明显减仓                      -> 价格支撑检验
  S4 非商业多头持续增仓后 t+N 交易日收益           -> 滞后统计
  S5 非商业空头持续增仓                            -> 价格压力检验
  S6 多空同步增仓                                  -> 分歧加剧
  S7 总持仓(OI)显著萎缩                            -> 流动性/趋势信号
  S8 背离: nc_net 明显增仓但价格下跌 / 明显减仓但价涨
口径:
  - 持仓: data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv (Futures Only, 周度, 周二快照)
  - 价格: data/price/sugar/sb_price_daily.csv (ICEUS SB1! 日线 close)
  - 锚点: 每个 CFTC 报告日 t, 对齐到 <=t 最近交易日收盘
  - "明显": |Δ|/OI 进入全样本前 10% 分位 (且 |Δ|>=5000手)
  - "持续": 连续 k 周同向(Δnc_l>0 等)
  - "高位": 价格 250 日分位 >=80% 且 nc_net/OI>=历史 60% 分位
  - 前瞻: t+N 交易日 (5/10/20/40/60)
  - 基准: 全样本同时期/同窗口收益
"""
import csv, json, math, statistics
from datetime import date, timedelta

ROOT = "C:/Users/Administrator/Desktop/农业"
CFTC_CSV = ROOT + "/data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"
PX_CSV   = ROOT + "/data/price/sugar/sb_price_daily.csv"
OUT_JSON = ROOT + "/data/cftc/results_cot/sugar_position_price_analysis_20260922.json"
OUT_CSV  = ROOT + "/data/cftc/results_cot/sugar_position_price_analysis_20260922.csv"

def fnum(x):
    try: return float(x)
    except: return None

# ---------- load price ----------
prows = list(csv.DictReader(open(PX_CSV, encoding="utf-8-sig")))
px_dates = []
px_close = []
for r in prows:
    d = date.fromisoformat(r["time"])
    px_dates.append(d)
    px_close.append(float(r["close"]))
N = len(px_dates)

def idx_on_or_before(d):
    import bisect
    i = bisect.bisect_right(px_dates, d) - 1
    return i if i >= 0 else None

def fwd_ret_trading(d, n):
    """t(锚点日d) 起第 n 个交易日收益, 返回 (ret_pct, anchor_idx)"""
    i0 = idx_on_or_before(d)
    if i0 is None: return None, None
    i1 = i0 + n
    if i1 >= N: return None, i0
    return (px_close[i1]/px_close[i0]-1)*100.0, i0

# ---------- load CFTC ----------
rows = list(csv.DictReader(open(CFTC_CSV, encoding="utf-8-sig")))
weeks = []
prev = None
for r in rows:
    d = date.fromisoformat(r["date"])
    if d < date(2009,1,1):   # 窗口: 2009-01 起 (价格数据 2011-12 起, 之前无法锚定自动跳过)
        prev = r
        continue
    rec = {
        "date": d,
        "oi": fnum(r["oi"]),
        "nc_l": fnum(r["nc_l"]), "nc_s": fnum(r["nc_s"]),
        "nc_net": fnum(r["nc_net"]),
        "c_net": fnum(r["c_net"]),
        "nr_net": fnum(r.get("nr_net")),
    }
    if prev is not None:
        rec["d_nc_l"] = rec["nc_l"] - fnum(prev["nc_l"])
        rec["d_nc_s"] = rec["nc_s"] - fnum(prev["nc_s"])
        rec["d_nc_net"] = rec["nc_net"] - fnum(prev["nc_net"])
        rec["d_oi"] = rec["oi"] - fnum(prev["oi"])
    else:
        rec["d_nc_l"] = rec["d_nc_s"] = rec["d_nc_net"] = rec["d_oi"] = None
    prev = r
    weeks.append(rec)

# 只保留有价格锚点的周
anchored = []
for w in weeks:
    i0 = idx_on_or_before(w["date"])
    if i0 is None: continue
    w["px_idx"] = i0
    # 250日分位 (数据起点2011-12, 2012年内滚动不够250天则用可用)
    look = max(0, i0-249)
    hist = px_close[look:i0+1]
    if len(hist) >= 60:
        pct = 100.0 * sum(1 for p in hist if p <= px_close[i0]) / len(hist)
    else:
        pct = None
    w["px_pctile250"] = pct
    anchored.append(w)

print("weeks anchored:", len(anchored))

# ---------- baseline ----------
BL_LBL = ["w", "t5", "t10", "t20", "t40", "t60"]
def ret_series(w, label):
    if label == "w":
        # 报告周内: 锚点收盘 -> 下一报告日锚点收盘(近似 7 天跨度)
        i = w["px_idx"]
        j = min(N-1, max(i, idx_on_or_before(w["date"]+timedelta(days=7)) or i))
        if j <= i: return None
        return (px_close[j]/px_close[i]-1)*100.0
    n = int(label[1:])
    v, _ = fwd_ret_trading(w["date"], n)
    return v

baseline = {}
for lbl in BL_LBL:
    vals = [ret_series(w, lbl) for w in anchored]
    vals = [v for v in vals if v is not None]
    if vals:
        baseline[lbl] = {"n": len(vals), "mean": round(statistics.mean(vals),3),
                         "median": round(statistics.median(vals),3),
                         "win": round(100.0*sum(1 for v in vals if v>0)/len(vals),1),
                         "p05": round(sorted(vals)[int(0.05*(len(vals)-1))],2),
                         "p95": round(sorted(vals)[int(0.95*(len(vals)-1))],2)}

# ---------- thresholds ----------
d_nc_l_abs = [abs(w["d_nc_l"]) for w in anchored if w["d_nc_l"] is not None]
d_nc_s_abs = [abs(w["d_nc_s"]) for w in anchored if w["d_nc_s"] is not None]
d_oi_abs   = [abs(w["d_oi"]) for w in anchored if w["d_oi"] is not None]
THR_NCL = sorted(d_nc_l_abs)[int(0.90*(len(d_nc_l_abs)-1))]
THR_NCS = sorted(d_nc_s_abs)[int(0.90*(len(d_nc_s_abs)-1))]
THR_OI  = sorted(d_oi_abs)[int(0.90*(len(d_oi_abs)-1))]
FLOOR = 5000.0

# 高位定义: 价格分位>=80 且 nc_net/OI 相对持仓占比分位 >= 60 (用全体周占比序列own的60分位)
ratios = sorted(w["nc_net"]/w["oi"] for w in anchored if w["oi"] and w["oi"]>0)
RATIO_P60 = ratios[int(0.60*(len(ratios)-1))] if ratios else 0

def is_high(w):
    if w["px_pctile250"] is None: return False
    return w["px_pctile250"] >= 80 and (w["nc_net"]/w["oi"] if w["oi"] else 0) >= RATIO_P60

# 连续同向检测
def streak(wl, field, direction, k):
    """from index i of wl (not incl), 往前 k 周均同向真"""
    pass

# ---------- scenario stats ----------
def stat_block(wl, label, describe=True):
    vals = [ret_series(w, label) for w in wl]
    vals = [v for v in vals if v is not None]
    if not vals: return None
    out = {"n": len(vals), "mean": round(statistics.mean(vals),3),
           "median": round(statistics.median(vals),3),
           "win": round(100.0*sum(1 for v in vals if v>0)/len(vals),1)}
    if describe:
        out["p05"] = round(sorted(vals)[int(0.05*(len(vals)-1))],2)
        out["p95"] = round(sorted(vals)[int(0.95*(len(vals)-1))],2)
        out["p75"] = round(sorted(vals)[int(0.75*(len(vals)-1))],2)
        out["p25"] = round(sorted(vals)[int(0.25*(len(vals)-1))],2)
    return out

def build_scen(wl):
    res = {}
    for lbl in BL_LBL:
        res[lbl] = stat_block(wl, lbl)
        if res[lbl] and lbl in baseline and baseline[lbl]["win"]:
            res[lbl]["lift_win_vs_base_pp"] = round(res[lbl]["win"] - baseline[lbl]["win"],1)
            # 单侧二项: 胜率是否显著高于基准
            from math import sqrt, erfc
            p0 = baseline[lbl]["win"]/100.0
            k = sum(1 for w in wl if (ret_series(w,lbl) or -999) > 0)
            n = res[lbl]["n"]
            if n and p0>0 and 0<p0<1:
                mu, sd = n*p0, sqrt(n*p0*(1-p0))
                if sd>0:
                    z = (k-0.5-mu)/sd
                    res[lbl]["p_binom_pos"] = round(0.5*erfc(z/sqrt(2)),3)
                else:
                    res[lbl]["p_binom_pos"] = None
        if res[lbl] is not None:
            mean = res[lbl]["mean"]
            n = res[lbl]["n"]
            sd = statistics.stdev([ret_series(w,lbl) for w in wl if ret_series(w,lbl) is not None])
            res[lbl]["t_p"] = round(2*min(0.5*(1+math.erf(mean/max(sd,1e-9)/math.sqrt(n)/math.sqrt(2))), 0.5),3) if sd>0 and n>1 else None
    return res

def make_scen(name, wl):
    print(f"  {name}: {len(wl)} events")
    return {"n": len(wl), "stats": build_scen(wl)}

scen = {}

# S1 非商业多头持续增仓: nc_l 连续 k 周上升
for k in (2,3,4):
    wl = []
    for i in range(k-1, len(anchored)):
        ok = all(anchored[j]["d_nc_l"] is not None and anchored[j]["d_nc_l"]>0 for j in range(i-k+1, i+1))
        if ok: wl.append(anchored[i])
    scen[f"S1_nc_l_up_{k}w"] = make_scen(f"S1 多头增仓{k}周", wl)

# S2 高位 + 多头增仓停滞(横盘观望): is_high 且 前4周累计 |Δnc_l| <= 0.5% OI (不增不减)
wl = []
for i in range(4, len(anchored)):
    w = anchored[i]
    if not is_high(w): continue
    if w["d_nc_l"] is None: continue
    cum = sum(anchored[j]["d_nc_l"] for j in range(i-3, i+1) if anchored[j]["d_nc_l"] is not None)
    cum = cum if cum is not None else 0
    if abs(cum) <= 0.005 * w["oi"]:
        wl.append(w)
scen["S2_high_nc_l_stall"] = make_scen("S2 高位多头观望", wl)
# S2b 高位 + 多头持续增仓(强势突破) 对照
wl = []
for i in range(4, len(anchored)):
    w = anchored[i]
    if not is_high(w): continue
    if w["d_nc_l"] is None: continue
    cum = sum(anchored[j]["d_nc_l"] for j in range(i-3, i+1) if anchored[j]["d_nc_l"] is not None)
    if cum >= 0.005 * w["oi"]:
        wl.append(w)
scen["S2b_high_nc_l_accum"] = make_scen("S2b 高位多头增仓", wl)

# S3 非商业空头明显减仓: d_nc_s <= -max(THR_NCS, FLOOR)
wl = [w for w in anchored if w["d_nc_s"] is not None and w["d_nc_s"] <= -max(THR_NCS, FLOOR)]
scen["S3_nc_s_cover_big"] = make_scen("S3 空头明显减仓", wl)
# S3b 空头连续减仓 2 周
wl = []
for i in range(1, len(anchored)):
    if anchored[i]["d_nc_s"] is not None and anchored[i-1]["d_nc_s"] is not None:
        if anchored[i]["d_nc_s"]<0 and anchored[i-1]["d_nc_s"]<0:
            wl.append(anchored[i])
scen["S3b_nc_s_cover_2w"] = make_scen("S3b 空头连减2周", wl)

# S4 已在 S1 的 t+n 列 (保留占位说明, 从 S1 2周 提取事件列表用于 CSV)
scen["_S4_note"] = "S4 见 S1_* 的 t5/t10/t20/t40/t60 列"

# S5 非商业空头持续增仓: nc_s 连续 k 周上升
for k in (2,3):
    wl = []
    for i in range(k-1, len(anchored)):
        ok = all(anchored[j]["d_nc_s"] is not None and anchored[j]["d_nc_s"]>0 for j in range(i-k+1, i+1))
        if ok: wl.append(anchored[i])
    scen[f"S5_nc_s_up_{k}w"] = make_scen(f"S5 空头增仓{k}周", wl)

# S6 多空同步增仓: d_nc_l>FLOOR*0.5 and d_nc_s>FLOOR*0.5
wl = [w for w in anchored if w["d_nc_l"] is not None and w["d_nc_s"] is not None
      and w["d_nc_l"]>FLOOR*0.5 and w["d_nc_s"]>FLOOR*0.5]
scen["S6_both_up"] = make_scen("S6 多空同步增仓", wl)

# S7 总持仓显著萎缩: d_oi <= -max(THR_OI, 20000)
wl = [w for w in anchored if w["d_oi"] is not None and w["d_oi"] <= -max(THR_OI, 20000)]
scen["S7_oi_shrink_big"] = make_scen("S7 总持仓显著萎缩", wl)
# S7b 单周OI大幅扩张对照
wl = [w for w in anchored if w["d_oi"] is not None and w["d_oi"] >= max(THR_OI, 20000)]
scen["S7b_oi_expand_big"] = make_scen("S7b 总持仓显著扩张", wl)

# S8 背离: nc_net 明显增仓(|Δnc_net|>=FLOOR*2) 但价格周跌(背离)
wl = []
for w in anchored:
    if w["d_nc_net"] is None: continue
    if abs(w["d_nc_net"]) < FLOOR*2: continue
    wret = ret_series(w, "w")
    if wret is None: continue
    if w["d_nc_net"] > 0 and wret < -0.5:
        wl.append(w)
scen["S8_nc_up_price_down"] = make_scen("S8a 多头增仓价跌背离", wl)
wl = []
for w in anchored:
    if w["d_nc_net"] is None: continue
    if abs(w["d_nc_net"]) < FLOOR*2: continue
    wret = ret_series(w, "w")
    if wret is None: continue
    if w["d_nc_net"] < 0 and wret > 0.5:
        wl.append(w)
scen["S8_nc_down_price_up"] = make_scen("S8b 多头减仓价涨背离", wl)

# ---------- CSV events ----------
def event_rows(wl, tag):
    out = []
    for w in wl:
        row = {"scenario": tag, "date": str(w["date"]),
               "px_close": px_close[w["px_idx"]],
               "px_pctile250": round(w["px_pctile250"],1) if w["px_pctile250"] is not None else "",
               "oi": w["oi"], "nc_l": w["nc_l"], "nc_s": w["nc_s"], "nc_net": w["nc_net"],
               "d_nc_l": w["d_nc_l"], "d_nc_s": w["d_nc_s"], "d_nc_net": w["d_nc_net"], "d_oi": w["d_oi"]}
        for lbl in BL_LBL:
            row[lbl] = ret_series(w, lbl)
        out.append(row)
    return out

csv_rows = []
want_tags = ["S1_nc_l_up_2w", "S2_high_nc_l_stall", "S3_nc_s_cover_big", "S5_nc_s_up_2w",
             "S6_both_up", "S7_oi_shrink_big", "S8_nc_up_price_down"]
for tag in want_tags:
    # 重新收集该场景事件 (与上面一致)
    if tag == "S1_nc_l_up_2w":
        wl = [anchored[i] for i in range(1, len(anchored)) if anchored[i]["d_nc_l"] is not None and anchored[i]["d_nc_l"]>0 and anchored[i-1]["d_nc_l"] is not None and anchored[i-1]["d_nc_l"]>0]
        csv_rows += event_rows(wl, tag)
    elif tag == "S2_high_nc_l_stall":
        wl = []
        for i in range(4, len(anchored)):
            w = anchored[i]
            if not is_high(w) or w["d_nc_l"] is None: continue
            cum = sum(anchored[j]["d_nc_l"] for j in range(i-3,i+1) if anchored[j]["d_nc_l"] is not None) or 0
            if abs(cum) <= 0.005*w["oi"]: wl.append(w)
        csv_rows += event_rows(wl, tag)
    elif tag == "S3_nc_s_cover_big":
        wl = [w for w in anchored if w["d_nc_s"] is not None and w["d_nc_s"] <= -max(THR_NCS, FLOOR)]
        csv_rows += event_rows(wl, tag)
    elif tag == "S5_nc_s_up_2w":
        wl = [anchored[i] for i in range(1,len(anchored)) if anchored[i]["d_nc_s"] is not None and anchored[i]["d_nc_s"]>0 and anchored[i-1]["d_nc_s"] is not None and anchored[i-1]["d_nc_s"]>0]
        csv_rows += event_rows(wl, tag)
    elif tag == "S6_both_up":
        wl = [w for w in anchored if w["d_nc_l"] is not None and w["d_nc_s"] is not None and w["d_nc_l"]>FLOOR*0.5 and w["d_nc_s"]>FLOOR*0.5]
        csv_rows += event_rows(wl, tag)
    elif tag == "S7_oi_shrink_big":
        wl = [w for w in anchored if w["d_oi"] is not None and w["d_oi"] <= -max(THR_OI, 20000)]
        csv_rows += event_rows(wl, tag)
    elif tag == "S8_nc_up_price_down":
        wl = []
        for w in anchored:
            if w["d_nc_net"] is None or abs(w["d_nc_net"]) < FLOOR*2: continue
            wr = ret_series(w,"w")
            if wr is not None and w["d_nc_net"]>0 and wr < -0.5: wl.append(w)
        csv_rows += event_rows(wl, tag)

with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    if csv_rows:
        wcsv = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        wcsv.writeheader(); wcsv.writerows(csv_rows)

# ---------- dump ----------
out = {"meta": {
    "title": "ICE原糖 CFTC持仓 x 价格 关系统计 (2012-2026)",
    "window_cftc": f"{anchored[0]['date']} ~ {anchored[-1]['date']}",
    "n_weeks": len(anchored),
    "thr_nc_l_big": THR_NCL, "thr_nc_s_big": THR_NCS, "thr_oi_big": THR_OI,
    "floor_lots": FLOOR,
    "high_def": "px250>=80pct & nc_net/OI>=P60",
    "baseline_note": "全样本所有周",
    "disclaimer": "仅统计研究, 非投资建议; 端点在样本尾部收益可能缺失",
},
    "baseline": baseline,
    "scenarios": {k:v for k,v in scen.items() if not k.startswith("_")},
}
json.dump(out, open(OUT_JSON,"w",encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n== BASELINE ==")
for k,v in baseline.items(): print(" ", k, v)
print("\n== SCENARIOS ==")
for k,v in out["scenarios"].items():
    if k.startswith("S"):
        st = v["stats"]
        print(f"{k}: n={v['n']}")
        for lbl in BL_LBL:
            if st.get(lbl): print(f"   {lbl}: mean={st[lbl]['mean']} med={st[lbl]['median']} win={st[lbl]['win']}% lift={st[lbl].get('lift_win_vs_base_pp')} p={st[lbl].get('t_p')}")
print("\nCSV events:", len(csv_rows))