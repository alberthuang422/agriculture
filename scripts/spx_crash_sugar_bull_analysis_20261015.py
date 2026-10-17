# -*- coding: utf-8 -*-
"""
牛市期间标普(SPY代理SPX)暴跌日 × ICE原糖(SB)表现分析 · 2026-10-15

暴跌定义: SPY 当日收盘涨跌幅 <= -1 × ADR20, 其中 ADR20 = 过去20日平均日振幅 ((High-Low)/Close)
牛市窗口(日线数据可得):
  W1 2015-16 厄尔尼诺: 2015-08-24 → 2016-10-06  (10.13 → 23.90)
  W2 2020-21 拉尼娜  : 2020-04-28 → 2021-11-18  (9.05 → 20.69)  对照组
  W3 2022-23 厄尔尼诺: 2022-10-03 → 2023-11-07  (17.36 → 28.14)
  W4 2026-   厄尔尼诺: 2026-04-17 → 2026-10-13  (13.22 → 进行中)

数据源:
  SPY = 新浪美股日线(2001起) + Nasdaq API(补至2026-10-13), 未复权
  SB  = TV导出 sb_price_daily.csv(2011-12~2026-09-25) + TV websocket sb1h_daily_20261014.json(补至2026-10-13)
"""
import json
import re

import numpy as np
import pandas as pd

BASE = r"C:\Users\Administrator\Desktop\农业\data\price\sugar"

WINDOWS = [
    ("W1 2015-16 厄尔尼诺", "2015-08-24", "2016-10-06"),
    ("W2 2020-21 拉尼娜", "2020-04-28", "2021-11-18"),
    ("W3 2022-23 厄尔尼诺", "2022-10-03", "2023-11-07"),
    ("W4 2026- 厄尔尼诺(进行中)", "2026-04-17", "2026-10-13"),
]

# ---------- 1. SPY: 新浪 + Nasdaq ----------
txt = open(r"C:\Users\Administrator\Desktop\农业\data\price\spx\_spy_sina_raw.txt", encoding="utf-8", errors="replace").read()
rows = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
sin = pd.DataFrame(rows)[["d", "o", "h", "l", "c"]].rename(
    columns={"d": "date", "o": "open", "h": "high", "l": "low", "c": "close"})
for c in ["open", "high", "low", "close"]:
    sin[c] = pd.to_numeric(sin[c], errors="coerce")

nd = json.load(open(r"C:\Users\Administrator\Desktop\农业\data\price\spx\_spy_nasdaq.json"))
nas = pd.DataFrame(nd["data"]["tradesTable"]["rows"])[["date", "open", "high", "low", "close"]]
nas["date"] = pd.to_datetime(nas["date"]).dt.strftime("%Y-%m-%d")
for c in ["open", "high", "low", "close"]:
    nas[c] = pd.to_numeric(nas[c].astype(str).str.replace("$", "", regex=False).str.replace(",", ""), errors="coerce")

ov = pd.merge(sin, nas, on="date", suffixes=("_sin", "_nas"))
diffs = {c: (ov[f"{c}_sin"] - ov[f"{c}_nas"]).abs().max() for c in ["open", "high", "low", "close"]}
print(f"[SPY拼接校验] 重叠 {len(ov)} 天, 最大差: " + ", ".join(f"{k}={v:.4f}" for k, v in diffs.items()))

spy = pd.concat([sin[sin["date"] < nas["date"].min()], nas]).drop_duplicates("date").sort_values("date").reset_index(drop=True)
print(f"[SPY] {spy['date'].iloc[0]} ~ {spy['date'].iloc[-1]}, {len(spy)} 天")
spy.to_csv(r"C:\Users\Administrator\Desktop\农业\data\price\spx\spy_daily_ohlc_2001_2026.csv", index=False)

# ---------- 2. SB: TV导出 + TV websocket ----------
sb1 = pd.read_csv(f"{BASE}\\sb_price_daily.csv")
sb1 = sb1.rename(columns={"time": "date"})[["date", "open", "high", "low", "close"]]
sb1["date"] = sb1["date"].astype(str).str[:10]
for c in ["open", "high", "low", "close"]:
    sb1[c] = pd.to_numeric(sb1[c], errors="coerce")

sb2 = pd.DataFrame(json.load(open(f"{BASE}\\sb1h_daily_20261014.json")))
sb2 = sb2[["date", "open", "high", "low", "close"]]

ovsb = pd.merge(sb1, sb2, on="date", suffixes=("_tv", "_ws"))
dd = (ovsb["close_tv"] - ovsb["close_ws"]).abs().max()
print(f"[SB拼接校验] 重叠 {len(ovsb)} 天, 收盘最大差 {dd:.4f}")

sb = pd.concat([sb1[sb1["date"] < sb2["date"].min()], sb2]).drop_duplicates("date").sort_values("date").reset_index(drop=True)
print(f"[SB] {sb['date'].iloc[0]} ~ {sb['date'].iloc[-1]}, {len(sb)} 天")

# ---------- 3. 指标 ----------
spy["adr20"] = ((spy["high"] - spy["low"]) / spy["close"]).rolling(20).mean() * 100
spy["ret"] = spy["close"].pct_change() * 100
spy["ret_abs20"] = spy["ret"].abs().rolling(20).mean()
spy["crash"] = spy["ret"] <= -spy["adr20"]
spy["crash_alt"] = spy["ret"] <= -spy["ret_abs20"]  # 稳健性: ADR=平均绝对日涨跌幅

sb["ret"] = sb["close"].pct_change() * 100
sb["fwd1"] = sb["close"].shift(-1) / sb["close"] * 100 - 100
sb["fwd5"] = sb["close"].shift(-5) / sb["close"] * 100 - 100
sb["fwd20"] = sb["close"].shift(-20) / sb["close"] * 100 - 100
spy["fwd5"] = spy["close"].shift(-5) / spy["close"] * 100 - 100
spy["fwd20"] = spy["close"].shift(-20) / spy["close"] * 100 - 100

m = pd.merge(spy, sb, on="date", suffixes=("_spx", "_sb"), how="inner").sort_values("date").reset_index(drop=True)
print(f"[对齐] {len(m)} 天: {m['date'].iloc[0]} ~ {m['date'].iloc[-1]}")

# ---------- 4. 分窗口统计 ----------
detail_frames = []
for wname, w0, w1 in WINDOWS:
    w = m[(m["date"] >= w0) & (m["date"] <= w1)].reset_index(drop=True)
    cw = w[w["crash"]].copy()
    n_all, n_crash = len(w), int(w["crash"].sum())
    n_alt = int(w["crash_alt"].sum())
    print(f"\n===== {wname}  ({w0} → {w1})  交易日 {n_all} =====")
    print(f"暴跌日(ADR口径): {n_crash} 天 ({n_crash/n_all:.1%})   [稳健性: 平均绝对涨跌幅口径 {n_alt} 天]")
    if n_crash:
        cols = ["date", "ret_spx", "adr20", "ret_sb", "fwd1", "fwd5_sb", "fwd20_sb", "fwd20_spx"]
        view = cw[cols].rename(columns={
            "ret_spx": "SPY日%", "adr20": "ADR20%", "ret_sb": "SB同日%",
            "fwd1": "SB+1d%", "fwd5_sb": "SB+5d%", "fwd20_sb": "SB+20d%", "fwd20_spx": "SPY+20d%"})
        view = view.round(2)
        print(view.to_string(index=False))
        detail_frames.append(cw.assign(window=wname))
        base_all = w
        print(f"  SB暴跌日: 同日均 {cw['ret_sb'].mean():+.2f}% / 中位 {cw['ret_sb'].median():+.2f}% / 上涨占比 {(cw['ret_sb']>0).mean():.0%}")
        print(f"  SB后续  : +5d 均 {cw['fwd5_sb'].mean():+.2f}% (样本n={cw['fwd5_sb'].notna().sum()}) | +20d 均 {cw['fwd20_sb'].mean():+.2f}% (n={cw['fwd20_sb'].notna().sum()})")
        nb = base_all[~base_all["crash"]]
        print(f"  非暴跌日 SB 同日均 {nb['ret_sb'].mean():+.2f}% (对照, n={len(nb)})")

if detail_frames:
    det = pd.concat(detail_frames, ignore_index=True)
    det.to_csv(f"{BASE}\\bull_spx_crash_days_detail_20261015.csv", index=False)
    print(f"\n[明细已存] bull_spx_crash_days_detail_20261015.csv ({len(det)} 行)")

# ---------- 5. 汇总(四个窗口合并) ----------
print("\n===== 汇总: 四窗口合并, 暴雨日 vs 非暴跌日 =====")
for wname, w0, w1 in WINDOWS:
    w = m[(m["date"] >= w0) & (m["date"] <= w1)]
    print(f"  {wname}: 暴跌{int(w['crash'].sum())}/{len(w)}天", end="")
    cw = w[w["crash"]]
    if len(cw):
        print(f" | 暴雨日SB+20d均 {cw['fwd20_sb'].mean():+.2f}%", end="")
    print()

pooled_crash = m[m["crash"] & (m["date"] >= "2015-08-24")]
pooled_rest = m[(~m["crash"]) & (m["date"] >= "2015-08-24")]
print(f"\n全样本暴跌日 SB 同日: 均 {pooled_crash['ret_sb'].mean():+.2f}%, 中位 {pooled_crash['ret_sb'].median():+.2f}%, 上涨占比 {(pooled_crash['ret_sb']>0).mean():.0%}")
print(f"全样本非暴跌日 SB 同日: 均 {pooled_rest['ret_sb'].mean():+.2f}%")
print(f"全样本暴跌日 SB +5d: 均 {pooled_crash['fwd5_sb'].mean():+.2f}% (n={pooled_crash['fwd5_sb'].notna().sum()})")
print(f"全样本暴跌日 SB +20d: 均 {pooled_crash['fwd20_sb'].mean():+.2f}% (n={pooled_crash['fwd20_sb'].notna().sum()})")
print(f"全样本暴跌日 SPY +20d: 均 {pooled_crash['fwd20_spx'].mean():+.2f}%")

# 暴雨日 SPY 与 SB 同日相关性(牛市窗口内)
for wname, w0, w1 in WINDOWS:
    w = m[(m["date"] >= w0) & (m["date"] <= w1)]
    if len(w) > 30:
        corr = w[["ret_spx", "ret_sb"]].corr().iloc[0, 1]
        print(f"  {wname}: SPY×SB 同日收益相关系数 {corr:+.2f}")
