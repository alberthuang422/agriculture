# -*- coding: utf-8 -*-
"""
101号研究·主分析: 价格横盘(±5%, 4-12周) + 非商业净持仓大幅变化(|Δnc_net|/OI≥阈值) 案例
前瞻: 事件终点后的 4/8/12 周收益, 对比全样本基准
输出: JSON 案例表 + CSV + 汇总统计
"""
import csv, json, math
from datetime import date, timedelta
from collections import defaultdict

ROOT = "C:/Users/Administrator/Desktop/农业"
CFTC = ROOT + "/data/cftc/results_cot/agri_cot_history_1995_2026.csv"
KC   = r"C:/Users/Administrator/Downloads/ICEUS_DLY_KC1!, 1W.csv"
CC   = r"C:/Users/Administrator/Downloads/ICEUS_DLY_CC1!, 1W.csv"
SB   = ROOT + "/data/price/sugar/sb_price_daily.csv"

START = date(2011, 1, 1)
END   = date(2026, 10, 1)
SIDE_BAND   = 0.05   # 横盘带 ±5%
L_MIN, L_MAX = 4, 12
THRESH = 0.08        # 主阈值 |Δnc_net|/OI ≥ 8%
THRESHS = [0.05, 0.08, 0.10]

def fnum(x):
    try: return float(x)
    except: return None

def to_date(s):
    return date.fromisoformat(str(s)[:10])

# ---------- 1. CFTC ----------
cftc = defaultdict(list)
with open(CFTC, encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        m = r["market"]
        if m not in ("咖啡 C (ICE)", "可可 (ICE)", "糖 11号 (ICE)"):
            continue
        cftc[m].append((to_date(r["date"]), fnum(r["oi"]), fnum(r["nc_l"]),
                        fnum(r["nc_s"]), fnum(r["nc_net"])))
for m in cftc:
    cftc[m].sort()

# ---------- 2. 价格 ----------
def load_tv_weekly(path):
    out = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            out.append((to_date(r["time"]), fnum(r["close"])))
    out.sort(); return out

def load_daily_weekly(path):
    rows = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows.append((to_date(r["time"]), fnum(r["close"])))
    rows.sort()
    wk = {}
    for d, c in rows:
        monday = d - timedelta(days=d.weekday())
        if monday not in wk or d > wk[monday][0]:
            wk[monday] = (d, c)
    return [(k, v[1]) for k, v in sorted(wk.items())]

px = {
    "咖啡 C (ICE)": load_tv_weekly(KC),
    "可可 (ICE)":   load_tv_weekly(CC),
    "糖 11号 (ICE)": load_daily_weekly(SB),
}

# ---------- 3. 对齐: 每个 CFTC 周二 -> 所在周 bar close(周五) ----------
def align(market):
    pxs = dict(px[market])
    out = []
    for d, oi, nl, ns, nnet in cftc[market]:
        monday = d - timedelta(days=1)
        key = monday
        while key not in pxs and key >= date(2000,1,1):
            key -= timedelta(days=7)
        if key not in pxs:
            continue
        out.append({"date": d, "close": pxs[key], "oi": oi,
                    "nc_l": nl, "nc_s": ns, "nc_net": nnet})
    return out

aligned = {m: align(m) for m in cftc}

# ---------- 4. 事件检测 ----------
def detect(market, thr):
    s = aligned[market]
    n = len(s)
    nclose = [r["close"] for r in s]
    nnet   = [r["nc_net"] for r in s]
    oi     = [r["oi"] for r in s]

    # 候选: (i, L, score) 横盘窗口 [i, i+L] 内所有点相对起点 ±5%, L∈[4,12]
    cands = []
    for i in range(n):
        if not (START <= s[i]["date"] <= END):
            continue
        p0 = nclose[i]
        if p0 is None or p0 <= 0:
            continue
        # 向前扩展直到破带
        j = i
        while j < n and j - i <= L_MAX:
            if abs(nclose[j]/p0 - 1) > SIDE_BAND:
                break
            L = j - i
            if L >= L_MIN:
                dn = nnet[j] - nnet[i]
                if dn is None: break
                oim = sum(oi[i:j+1]) / (L+1)
                if oim and abs(dn)/oim >= thr:
                    cands.append({"i": i, "L": L, "j": j,
                                  "dn": dn, "oi_avg": oim,
                                  "score": abs(dn)/oim})
            j += 1
    # 贪心去重: 按 score 降序, 窗口重叠则跳过
    cands.sort(key=lambda c: (-c["score"], -c["L"]))
    evs = []
    used = [False]*n
    for c in cands:
        if any(used[k] for k in range(c["i"], c["j"]+1)):
            continue
        for k in range(c["i"], c["j"]+1):
            used[k] = True
        evs.append(c)
    evs.sort(key=lambda c: s[c["i"]]["date"])

    # 组装事件详情
    events = []
    for c in evs:
        i, j = c["i"], c["j"]
        L = c["L"]
        # 横盘带价格统计
        band_closes = nclose[i:j+1]
        p0 = band_closes[0]
        hi = max((p/p0-1)*100 for p in band_closes)
        lo = min((p/p0-1)*100 for p in band_closes)
        # 前瞻: 从 j (终点) 起 4/8/12 周
        fwd = {}
        for k in (4, 8, 12):
            if j + k < n:
                fwd[k] = (nclose[j+k]/nclose[j] - 1)*100
            else:
                fwd[k] = None
        ev = {
            "market": market,
            "start": str(s[i]["date"]),     # 横盘带起点 CFTC 周二
            "end":   str(s[j]["date"]),
            "L": L,
            "close0": round(p0, 2),
            "close_end": round(nclose[j], 2),
            "band_hi_pct": round(hi, 2),
            "band_lo_pct": round(lo, 2),
            "d_nc_net": int(c["dn"]),
            "d_nc_net_pct_oi": round(c["score"]*100, 2),
            "nc_net_end": int(nnet[j]),
            "oi_avg": int(c["oi_avg"]),
            "dir": "增仓" if c["dn"] > 0 else "减仓",
            "fwd4": fwd[4], "fwd8": fwd[8], "fwd12": fwd[12],
        }
        events.append(ev)
    return events

events = {t: {} for t in THRESHS}
for t in THRESHS:
    for m in aligned:
        events[t][m] = detect(m, t)

# ---------- 5. 基准: 全样本 4/8/12 周收益分布 ----------
def base_stats(market):
    s = aligned[market]
    n = len(s)
    nclose = [r["close"] for r in s]
    out = {}
    for k in (4, 8, 12):
        rets = []
        for i in range(0, n-k):
            p0 = nclose[i]
            if p0 and p0 > 0:
                rets.append((nclose[i+k]/p0 - 1)*100)
        rets.sort()
        out[k] = {"n": len(rets), "med": round(rets[len(rets)//2], 2),
                  "p25": round(rets[int(len(rets)*0.25)], 2),
                  "p75": round(rets[int(len(rets)*0.75)], 2),
                  "p10": round(rets[int(len(rets)*0.10)], 2),
                  "p90": round(rets[int(len(rets)*0.90)], 2),
                  "pos_pct": round(100*sum(1 for x in rets if x>0)/len(rets), 1)}
    return out

base = {m: base_stats(m) for m in aligned}

# ---------- 6. 汇总 ----------
summary = {}
for t in THRESHS:
    summary[t] = {"tot": 0}
    stats_by_m = {}
    for m in aligned:
        evs = events[t][m]
        stats_by_m[m] = {
            "n": len(evs),
            "n_add": sum(1 for e in evs if e["dir"]=="增仓"),
            "n_cut": sum(1 for e in evs if e["dir"]=="减仓"),
        }
        # 前瞻均值/中位
        for k in (4,8,12):
            vals = [e[f"fwd{k}"] for e in evs if e[f"fwd{k}"] is not None]
            pos = sum(1 for v in vals if v>0)
            stats_by_m[m][f"fwd{k}"] = {
                "n": len(vals),
                "med": round(sorted(vals)[len(vals)//2], 2) if vals else None,
                "mean": round(sum(vals)/len(vals), 2) if vals else None,
                "pos_pct": round(100*pos/len(vals), 1) if vals else None,
            }
        summary[t]["tot"] += len(evs)
    summary[t]["by_market"] = stats_by_m

# 保存
out_json = ROOT + "/data/cftc/results_cot/diverge_events_20260923.json"
out_csv  = ROOT + "/data/cftc/results_cot/diverge_events_20260923.csv"
payload = {"events": events, "base": base, "summary": summary,
           "params": {"band": SIDE_BAND, "L": [L_MIN, L_MAX], "thresh": THRESHS}}
with open(out_json, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=1)

with open(out_csv, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["threshold","market","start","end","L","close0","close_end",
                "band_hi_pct","band_lo_pct","d_nc_net","d_nc_net_pct_oi",
                "nc_net_end","oi_avg","dir","fwd4","fwd8","fwd12"])
    for t in THRESHS:
        for m in aligned:
            for e in events[t][m]:
                w.writerow([t, m, e["start"], e["end"], e["L"], e["close0"],
                            e["close_end"], e["band_hi_pct"], e["band_lo_pct"],
                            e["d_nc_net"], e["d_nc_net_pct_oi"], e["nc_net_end"],
                            e["oi_avg"], e["dir"], e["fwd4"], e["fwd8"], e["fwd12"]])
print("saved:", out_json)
print("saved:", out_csv)
print(json.dumps(summary, ensure_ascii=False, indent=1))
print("\n--- 基准(全样本任意周买入) 4/8/12周 ---")
print(json.dumps(base, ensure_ascii=False, indent=1))