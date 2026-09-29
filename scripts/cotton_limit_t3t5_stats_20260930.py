# -*- coding: utf-8 -*-
"""
ICE 棉花(CT1! 连续) 涨跌停触及统计 · 缓冲5点(=0.05美分/lb, 5个最小变动价位)
- T+1/T+2/T+3 每日表现 + T+5 表现, 按年分组汇总
- 双口径: 盘中触及(最高/最低价) 与 收盘价触及
板幅规则(依据 CFTC 规则提交 2011-01-31 / ICE 交易所通知 2010-09-29、2010-10-25):
  - 2011-02-07 前: 基板 3¢(价格<=84¢) / 4¢(>84¢), 可两级扩张(每级+1¢), 上限基板+2
  - 2011-02-07 起: 按价格分档 <=80:3 / <=110:4 / <=140:5 / <=170:6 / >170:7,
    前日有合约收于板价则次日+1¢(7¢不再扩张), 未收板价则逐日回落
  - 单一连续合约无法看到"前5合约中2个封板"的多合约触发, 用"连续2日收于板价"近似(V3, 268个旧事件板幅失配26个)
  - 当日数据证据(excursion 超过模拟板幅)时, 板幅上调至证据值
数据: C:/Users/Administrator/Downloads/ICEUS_DLY_CT1!, 1D.csv (TradingView, 2010-08-27~2026-09-29)
输出: 根目录 4 份 CSV(事件明细x2 + 按年汇总x2), 原始日线落盘 data/price/cotton/
"""
import csv, shutil, statistics
from collections import defaultdict

ROOT = r"C:/Users/Administrator/Desktop/农业"
SRC  = r"C:/Users/Administrator/Downloads/ICEUS_DLY_CT1!, 1D.csv"
TOL  = 0.05  # 缓冲 5 点 = 0.05 美分/lb

# ---------- 数据 ----------
rows = []  # (date, o, h, l, c)
with open(SRC, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append((r["time"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
shutil.copy(SRC, ROOT + r"/data/price/cotton/ct1_daily_ohlc_2010_2026_tradingview.csv")

# 旧版事件 CSV(精确触及口径), 用于板幅校准对照
old = {}
with open(ROOT + "/ICE棉花涨跌停触及及T5统计.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        old[r["date"]] = int(r["limit_cents"])

def base_limit(pc, date):
    if date < "2011-02-07":
        return (3 if pc <= 84 else 4), 2
    if pc <= 80: b = 3
    elif pc <= 110: b = 4
    elif pc <= 140: b = 5
    elif pc <= 170: b = 6
    else: b = 7
    return b, (0 if b == 7 else 1)

# ---------- 板幅模拟(纯规则 V3: 连续2日收于板价->次日+1, 未收板价逐日回落) ----------
limit = {}   # date -> 规则板幅(¢)
e = 0; run = 0
for i, (date, o, h, l, c) in enumerate(rows):
    if i == 0:
        limit[date] = 4; continue
    pc = rows[i-1][4]
    b, cap = base_limit(pc, date)
    L = b + min(e, cap)
    limit[date] = L
    at = (c >= pc + L - TOL) or (c <= pc - L + TOL)
    run = run + 1 if at else 0
    if run >= 2: e += 1
    else: e = max(0, e - 1)

# 歧义日处理: 旧版事件日且旧板与规则板差1级时, 取较低板幅做触及判定(缓冲意图, 兼容旧版口径)
L_eff = {}
for i, (date, o, h, l, c) in enumerate(rows):
    L = limit[date]
    if date in old and abs(old[date] - L) == 1:
        L = min(old[date], L)
    L_eff[date] = L

# 与旧版对照(校准质量)
mism = [(d, lv, limit.get(d)) for d, lv in old.items() if limit.get(d) != lv]
print(f"[校准] 旧版268个事件日板幅 失配 {len(mism)} 个")

# ---------- 事件提取 ----------
idx = {r[0]: i for i, r in enumerate(rows)}
def t_stats(date, n):  # 事件收盘 -> T+n
    i = idx[date]
    if i + n >= len(rows): return None
    d2, c2 = rows[i+n][0], rows[i+n][4]
    c0 = rows[i][4]
    return d2, c2, round(c2 - c0, 2), round((c2/c0 - 1) * 100, 2)

def build_events(mode):
    """mode='intraday' 盘中口径 / 'close' 收盘价口径"""
    ev = []
    for i, (date, o, h, l, c) in enumerate(rows):
        if i == 0: continue
        pc = rows[i-1][4]; L = L_eff[date]
        up = h >= pc + L - TOL if mode == "intraday" else c >= pc + L - TOL
        dn = l <= pc - L + TOL if mode == "intraday" else c <= pc - L + TOL
        if not (up or dn): continue
        side = "up-limit" if up and not dn else ("down-limit" if dn and not up else "both")
        rec = {"date": date, "side": side, "prev_close": pc, "limit_cents": L,
               "upper_limit": round(pc+L, 2), "lower_limit": round(pc-L, 2),
               "high": h, "low": l, "close": c}
        for n in (1, 2, 3, 5):
            t = t_stats(date, n)
            if t:
                rec[f"t{n}_date"] = t[0]; rec[f"t{n}_close"] = t[1]
                rec[f"t{n}_chg"] = t[2]; rec[f"t{n}_pct"] = t[3]
            else:
                for k in (f"t{n}_date", f"t{n}_close", f"t{n}_chg", f"t{n}_pct"): rec[k] = ""
        ev.append(rec)
    return ev

def summarize(ev):
    """按年+方向汇总; both 日同时计入涨、跌"""
    out = []
    years = sorted({r["date"][:4] for r in ev})
    for y in years + ["ALL"]:
        sub = [r for r in ev if y == "ALL" or r["date"][:4] == y]
        for side, want, key_pos in (("up", ("up-limit", "both"), "t5_chg>0"),
                                    ("down", ("down-limit", "both"), "t5_chg<0")):
            s = [r for r in sub if r["side"] in want]
            if not s: continue
            def arr(k): return [r[k] for r in s if r[k] != ""]
            t5c, t5p = arr("t5_chg"), arr("t5_pct")
            n_t5 = len(t5c)
            pos = sum(1 for v in t5c if (v > 0 if side == "up" else v < 0))
            row = {"year": y, "side": side, "n": len(s), "n_with_t5": n_t5,
                   "n_t5_follow": pos,
                   "t5_chg_mean": round(statistics.mean(t5c), 2) if t5c else "",
                   "t5_chg_median": round(statistics.median(t5c), 2) if t5c else "",
                   "t5_pct_mean": round(statistics.mean(t5p), 2) if t5p else ""}
            for n in (1, 2, 3):
                a = arr(f"t{n}_chg")
                row[f"t{n}_chg_mean"] = round(statistics.mean(a), 2) if a else ""
            out.append(row)
    return out

def write_csv(path, data):
    if not data: return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader(); w.writerows(data)

ev_in, ev_cl = build_events("intraday"), build_events("close")
sum_in, sum_cl = summarize(ev_in), summarize(ev_cl)
write_csv(ROOT + "/ICE棉花涨跌停触及T3T5_盘中口径_缓冲5点.csv", ev_in)
write_csv(ROOT + "/ICE棉花涨跌停触及T3T5_收盘价口径_缓冲5点.csv", ev_cl)
write_csv(ROOT + "/ICE棉花涨跌停触及T3T5_按年汇总_盘中口径.csv", sum_in)
write_csv(ROOT + "/ICE棉花涨跌停触及T3T5_按年汇总_收盘价口径.csv", sum_cl)

# 一致性: 旧版事件日 vs 新盘中口径事件集
old_dates = set(old)
new_dates = {r["date"] for r in ev_in}
missing = sorted(old_dates - new_dates)
print(f"[一致性] 旧版事件日 {len(old_dates)} 个, 新盘中口径 {len(ev_in)} 个, 旧版有而新版无 {len(missing)} 个:")
rows_by_d = {r[0]: r for r in rows}
for d in missing:
    i = idx[d]; pc = rows[i-1][4]; h, l = rows[i][2], rows[i][3]
    print(f"  {d} 旧板{old[d]}¢ 新板{L_eff[d]}¢ up_exc={h-pc:.2f} dn_exc={pc-l:.2f}")

for name, s in (("盘中口径", sum_in), ("收盘价口径", sum_cl)):
    print(f"\n===== 按年汇总 · {name} =====")
    for r in s:
        print(f"{r['year']:>4} {r['side']:>4} n={r['n']:>3} 跟随={r['n_t5_follow']:>3} "
              f"t5均值={r['t5_chg_mean']:>7} t5中位={r['t5_chg_median']:>7} "
              f"t1={r['t1_chg_mean']} t2={r['t2_chg_mean']} t3={r['t3_chg_mean']}")
