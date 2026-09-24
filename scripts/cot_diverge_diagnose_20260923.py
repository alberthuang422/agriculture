# -*- coding: utf-8 -*-
"""
101号研究·诊断阶段: 价格横盘(±5%) + 非商业净持仓 4-12周大幅变化 案例检测
- CFTC 持仓: data/cftc/results_cot/agri_cot_history_1995_2026.csv (周度, 周二快照)
- 价格: 咖啡/可可 = 用户提供的 TradingView 周线; 白糖 = sb_price_daily.csv 聚合周线
- 周对齐: 以 CFTC 报告日(周二)所在周为锚, 价格取该周周五收盘(周bar close)

输出: 诊断 JSON — 各品种横盘窗口计数 / 仓位变化分布 / 初步案例数量
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

# ---------- helpers ----------
def fnum(x):
    try: return float(x)
    except: return None

def to_date(s):
    return date.fromisoformat(str(s)[:10])

# ---------- 1. CFTC 持仓: 按品种取 nc_net 周序列 ----------
cftc = defaultdict(list)   # market -> [(date, oi, nc_l, nc_s, nc_net)]
with open(CFTC, encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        m = r["market"]
        if m not in ("咖啡 C (ICE)", "可可 (ICE)", "糖 11号 (ICE)"):
            continue
        d = to_date(r["date"])
        cftc[m].append((d, fnum(r["oi"]), fnum(r["nc_l"]), fnum(r["nc_s"]), fnum(r["nc_net"])))
for m in cftc:
    cftc[m].sort()

# ---------- 2. 价格: 周线 {周一: close} ----------
def load_tv_weekly(path):
    """TradingView 周线: time=周一, close=周五收盘"""
    out = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            d = to_date(r["time"])
            out.append((d, fnum(r["close"])))
    out.sort()
    return out

def load_daily_weekly(path):
    """日线 -> 周线: 按自然周取最后交易日 close, time=该周周一"""
    rows = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows.append((to_date(r["time"]), fnum(r["close"])))
    rows.sort()
    # 周一分桶
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

# ---------- 3. 统一周网格: 以 CFTC 周二为锚, 价格取 <= 周二 最近的周bar close ----------
# 注意: TradingView 周bar time=周一, 即 CFTC 周二所在周的周一开始那一根bar的close(周五)
def align(market):
    """返回 [{date: CFTC周二, close: 对应周收盘, oi, nc_l, nc_s, nc_net}]"""
    pxs = dict(px[market])
    out = []
    for d, oi, nl, ns, nnet in cftc[market]:
        monday = d - timedelta(days=1)          # CFTC 周二 -> 所在周周一
        # 该周bar: 周一 key; 若缺(假期), 向前取最近 bar
        key = monday
        while key not in pxs and key >= date(2000,1,1):
            key -= timedelta(days=7)
        if key not in pxs:
            continue
        out.append({"date": d, "close": pxs[key], "oi": oi,
                    "nc_l": nl, "nc_s": ns, "nc_net": nnet})
    return out

aligned = {m: align(m) for m in cftc}
for m, s in aligned.items():
    print(f"[{m}] 对齐后周数: {len(s)}  范围: {s[0]['date']} ~ {s[-1]['date']}")

# ---------- 4. 诊断: 横盘窗口 + 仓位变化分布 ----------
def is_sideways(closes, L):
    """窗口 [0..L]: 所有点相对起点 |Δ|<=5%"""
    p0 = closes[0]
    if p0 is None or p0 <= 0:
        return False
    return all(abs(c/p0 - 1) <= 0.05 for c in closes)

diag = {}
for m, s in aligned.items():
    # 限 2011 起
    idxs = [i for i, r in enumerate(s) if START <= r["date"] <= END]
    n = len(s)
    nclose = [r["close"] for r in s]
    nnet = [r["nc_net"] for r in s]
    oi = [r["oi"] for r in s]

    side_count = defaultdict(int)
    dnet_dist = defaultdict(list)   # L -> list of |Δnc_net|
    dnet_pct_oi = defaultdict(list) # L -> list of |Δ|/OI
    for L in range(4, 13):
        for i in idxs:
            if i + L >= n:
                continue
            cl = nclose[i:i+L+1]
            if not is_sideways(cl, L):
                continue
            side_count[L] += 1
            dn = nnet[i+L] - nnet[i]
            oim = sum(oi[i:i+L+1]) / (L+1)
            dnet_dist[L].append(abs(dn))
            dnet_pct_oi[L].append(abs(dn)/oim if oim else 0)

    diag[m] = {
        "weeks": len([i for i in idxs]),
        "sideways_by_L": dict(side_count),
        "tot_frames": sum(side_count.values()),
        "dnet_pct_by_L": {
            str(L): {
                "p50": round(sorted(v)[len(v)//2], 0) if v else None,
                "p90": round(sorted(v)[int(len(v)*0.9)] if v else 0, 0) if v else None,
                "n": len(v),
            } for L, v in dnet_dist.items()
        },
        "dnet_oi_pct_by_L": {
            str(L): {
                "p50": round(sorted(v)[len(v)//2], 4) if v else None,
                "p90": round(sorted(v)[int(len(v)*0.9)] if v else 0, 4) if v else None,
                "n": len(v),
            } for L, v in dnet_pct_oi.items()
        },
    }

out = ROOT + "/data/cftc/results_cot/diverge_diag_20260923.json"
with open(out, "w", encoding="utf-8") as fh:
    json.dump(diag, fh, ensure_ascii=False, indent=1, default=str)
print("saved:", out)
print(json.dumps(diag, ensure_ascii=False, indent=1, default=str))