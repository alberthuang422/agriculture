# -*- coding: utf-8 -*-
"""99号 补充稳健性: 事件路径 + 趋势分段 + 动量分组 + 子场景拆分
目的: 区分"持仓信号"的真伪, 避免把总效应(多为趋势/均值回归驱动)误当单个信号
"""
import csv, json, math, statistics
from datetime import date, timedelta

ROOT = "C:/Users/Administrator/Desktop/农业"
CFTC_CSV = ROOT + "/data/cftc/sugar/sugar_cftc_futonly_1986_2026.csv"
PX_CSV   = ROOT + "/data/price/sugar/sb_price_daily.csv"
OUT_JSON = ROOT + "/data/cftc/results_cot/sugar_position_price_robust_20260922.json"

def fnum(x):
    try: return float(x)
    except: return None

# ---------- price ----------
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

def window_path(i0, w_before=4, w_after=12):
    """以触发周锚点收盘为基准, 返回 [-4..+12] 周相对%路径 (用交易日对齐: 一周=5交易日)"""
    path = {}
    for w in range(-w_before, w_after+1):
        v = ret_idx(i0, w*5)
        path[w] = v
    return path

SEG = [("2012-2016 熊市回落", date(2012,1,1), date(2016,12,31)),
       ("2017-2019 底部区间", date(2017,1,1), date(2019,12,31)),
       ("2020-2024 上行与高位震荡", date(2020,1,1), date(2024,12,31)),
       ("2025+ 缺口定价行情", date(2025,1,1), date(2026,12,31))]

# ---------- CFTC ----------
rows = list(csv.DictReader(open(CFTC_CSV, encoding="utf-8-sig")))
weeks, prev = [], None
for r in rows:
    d = date.fromisoformat(r["date"])
    if d < date(2009,1,1):   # 窗口: 2009-01 起 (价格数据 2011-12 起)
        prev = r; continue
    rec = {"date": d, "oi": fnum(r["oi"]),
           "nc_l": fnum(r["nc_l"]), "nc_s": fnum(r["nc_s"]), "nc_net": fnum(r["nc_net"]),
           "c_net": fnum(r["c_net"])}
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
    rec["px_pctile250"] = 100.0*sum(1 for p in hist if p <= px_close[i0])/len(hist) if len(hist)>=60 else None
    # 当前周收益与前4周动量
    rec["w_ret"] = ret_idx(i0, 5)
    rec["mom4w"] = ret_idx(i0, -20)
    rec["mom12w"] = ret_idx(i0, -60)
    weeks.append(rec)

print("weeks anchored:", len(weeks))

def avg_path(wl):
    """wl: list of weeks; 返回 [-4..12] 周平均累积%"""
    import collections
    sums, cnt = collections.defaultdict(float), collections.defaultdict(int)
    for w in wl:
        path = window_path(w["px_idx"])
        for wk, v in path.items():
            if v is not None:
                sums[wk] += v; cnt[wk] += 1
    return {wk: round(sums[wk]/cnt[wk],2) for wk in sorted(sums) if cnt[wk]}

def seg_stats(wl, horizon=(20,60)):
    out = {}
    for name, d0, d1 in SEG:
        sub = [w for w in wl if d0 <= w["date"] <= d1]
        seg = {"n": len(sub)}
        for h in horizon:
            vals = [ret_idx(w["px_idx"], h) for w in sub]
            vals = [v for v in vals if v is not None]
            if vals:
                seg[f"t{h}_mean"] = round(statistics.mean(vals),2)
                seg[f"t{h}_win"] = round(100.0*sum(1 for v in vals if v>0)/len(vals),1)
        out[name] = seg
    return out

# ---------- sub-scenarios ----------
res = {"meta": {"n_weeks": len(weeks), "segments": [s[0] for s in SEG]}, "scenarios": {}}

# 复刻主脚本关键场景事件集
def ev_scen(name, fn):
    wl = fn()
    res["scenarios"][name] = {"n": len(wl), "path_w": avg_path(wl), "seg": seg_stats(wl)}
    print(f"{name}: n={len(wl)}  t20_win={res['scenarios'][name]['seg']}")
    return wl

# S1 多头增仓2周 事件
def s1_2w(field="d_nc_l"):
    out = []
    for i in range(1, len(weeks)):
        if weeks[i][field] is not None and weeks[i-1][field] is not None and weeks[i][field]>0 and weeks[i-1][field]>0:
            out.append(weeks[i])
    return out
wl1 = ev_scen("S1_nc_l_up_2w", s1_2w)

# S1 按动量分组: 多头增仓2周 且 前12周动量>0 (涨势中) vs <0 (跌势中)
for tag, cond in [("mom12_up", lambda w: (w["mom12w"] or 0) > 0),
                  ("mom12_down", lambda w: (w["mom12w"] or 0) < 0),
                  ("mom4_up", lambda w: (w["mom4w"] or 0) > 0),
                  ("mom4_down", lambda w: (w["mom4w"] or 0) < 0)]:
    sub = [w for w in wl1 if cond(w)]
    res["scenarios"][f"S1_2w_{tag}"] = {"n": len(sub), "path_w": avg_path(sub), "seg": seg_stats(sub)}
    print(f"S1_2w_{tag}: n={len(sub)}")

# S1 同周共振拆分: 多头增仓2周 + 当周价涨1% (共振) vs 当周价跌1% (多头接盘/背离)
sub1 = [w for w in wl1 if (w["w_ret"] or 0) > 1.0]
sub2 = [w for w in wl1 if (w["w_ret"] or 0) < -1.0]
res["scenarios"]["S1_2w_price_up1pct"] = {"n": len(sub1), "path_w": avg_path(sub1), "seg": seg_stats(sub1)}
res["scenarios"]["S1_2w_price_down1pct"] = {"n": len(sub2), "path_w": avg_path(sub2), "seg": seg_stats(sub2)}
print("S1_2w_price_up1pct:", len(sub1), "| down1pct:", len(sub2))

# S2b 高位多头增仓 (同主脚本: 高位 + 4周累计增仓>=0.5%OI)
def s2b():
    out = []
    ratios = sorted(w["nc_net"]/w["oi"] for w in weeks if w["oi"])
    p60 = ratios[int(0.60*(len(ratios)-1))]
    for i in range(4, len(weeks)):
        w = weeks[i]
        if w["px_pctile250"] is None or w["px_pctile250"] < 80: continue
        if w["nc_net"]/w["oi"] < p60: continue
        cum = sum(weeks[j]["d_nc_l"] for j in range(i-3, i+1) if weeks[j]["d_nc_l"] is not None)
        if cum >= 0.005*w["oi"]: out.append(w)
    return out
wl2b = ev_scen("S2b_high_nc_l_accum", s2b)

# S3 空头明显减仓, 按价格分位拆: 低(<40) vs 中高(>=40)
def s3():
    out = []
    for w in weeks:
        if w["d_nc_s"] is not None and w["d_nc_s"] <= -5000: out.append(w)
    return out
wl3 = ev_scen("S3_nc_s_cover_big", s3)
lo = [w for w in wl3 if (w["px_pctile250"] or 50) < 40]
hi = [w for w in wl3 if (w["px_pctile250"] or 50) >= 40]
res["scenarios"]["S3_low_price"] = {"n": len(lo), "path_w": avg_path(lo), "seg": seg_stats(lo)}
res["scenarios"]["S3_high_price"] = {"n": len(hi), "path_w": avg_path(hi), "seg": seg_stats(hi)}
print("S3 low:", len(lo), "high:", len(hi))

# S5 空头增仓2周
def s5():
    out = []
    for i in range(1, len(weeks)):
        if weeks[i]["d_nc_s"] is not None and weeks[i-1]["d_nc_s"] is not None and weeks[i]["d_nc_s"]>0 and weeks[i-1]["d_nc_s"]>0:
            out.append(weeks[i])
    return out
wl5 = ev_scen("S5_nc_s_up_2w", s5)

# S6 多空同步增仓
def s6():
    return [w for w in weeks if w["d_nc_l"] is not None and w["d_nc_s"] is not None and w["d_nc_l"]>2500 and w["d_nc_s"]>2500]
wl6 = ev_scen("S6_both_up", s6)

# S7 OI 显著萎缩
def s7():
    return [w for w in weeks if w["d_oi"] is not None and w["d_oi"] <= -20000]
wl7 = ev_scen("S7_oi_shrink_big", s7)

# S8a 多头净增但价跌 (d_nc_net>10000 且 当周价跌>1%)
def s8a():
    out = []
    for w in weeks:
        if w["d_nc_net"] is None or w["d_nc_net"] < 10000: continue
        if (w["w_ret"] or 0) < -1.0: out.append(w)
    return out
wl8 = ev_scen("S8a_nc_up_price_down", s8a)

# S2 高位横盘观望 事件明细 (用于报告案例)
def s2_stall():
    out = []
    ratios = sorted(w["nc_net"]/w["oi"] for w in weeks if w["oi"])
    p60 = ratios[int(0.60*(len(ratios)-1))]
    for i in range(4, len(weeks)):
        w = weeks[i]
        if w["px_pctile250"] is None or w["px_pctile250"] < 80: continue
        if w["nc_net"]/w["oi"] < p60: continue
        cum = sum(weeks[j]["d_nc_l"] for j in range(i-3, i+1) if weeks[j]["d_nc_l"] is not None)
        if abs(cum) <= 0.005*w["oi"]: out.append(w)
    return out
wl2s = ev_scen("S2_high_nc_l_stall", s2_stall)
res["scenarios"]["S2_high_nc_l_stall"]["detail"] = [
    {"date": str(w["date"]), "close": px_close[w["px_idx"]],
     "px250": round(w["px_pctile250"],0) if w["px_pctile250"] is not None else None,
     "nc_net": w["nc_net"], "d_nc_l_4w": round(sum(weeks[weeks.index(w)-3+j]["d_nc_l"] for j in range(4) if weeks.index(w)-3+j>=0 and weeks[weeks.index(w)-3+j]["d_nc_l"] is not None),0),
     "t20": ret_idx(w["px_idx"],20), "t60": ret_idx(w["px_idx"],60)} for w in wl2s]

json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved:", OUT_JSON)