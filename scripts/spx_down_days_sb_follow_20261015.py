# -*- coding: utf-8 -*-
"""
标普下跌日 → SB 是否跟跌: 分桶统计 + 回归检验 · 2026-10-15
问题: 只要标普跌(不限暴跌), 糖是否跟跌? 有无统计相关性?
口径: SPY 代理 SPX (未复权), SB=ICE原糖2号; 日收盘对收盘收益; 2011-12-23 → 2026-10-13
"""
import json
import re

import numpy as np
import pandas as pd

BASE = r"C:\Users\Administrator\Desktop\农业\data\price\spx"
SB_BASE = r"C:\Users\Administrator\Desktop\农业\data\price\sugar"

# ---------- 数据 (与 spx_crash_sugar_bull_analysis_20261015.py 同源) ----------
txt = open(f"{BASE}\\_spy_sina_raw.txt", encoding="utf-8", errors="replace").read()
rows = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
sin = pd.DataFrame(rows)[["d", "o", "h", "l", "c"]].rename(
    columns={"d": "date", "o": "open", "h": "high", "l": "low", "c": "close"})
for c in ["open", "high", "low", "close"]:
    sin[c] = pd.to_numeric(sin[c], errors="coerce")

nd = json.load(open(f"{BASE}\\_spy_nasdaq.json"))
nas = pd.DataFrame(nd["data"]["tradesTable"]["rows"])[["date", "open", "high", "low", "close"]]
nas["date"] = pd.to_datetime(nas["date"]).dt.strftime("%Y-%m-%d")
for c in ["open", "high", "low", "close"]:
    nas[c] = pd.to_numeric(nas[c].astype(str).str.replace("$", "", regex=False).str.replace(",", ""), errors="coerce")
spy = pd.concat([sin[sin["date"] < nas["date"].min()], nas]).drop_duplicates("date").sort_values("date").reset_index(drop=True)

sb1 = pd.read_csv(f"{SB_BASE}\\sb_price_daily.csv").rename(columns={"time": "date"})[["date", "close"]]
sb1["date"] = sb1["date"].astype(str).str[:10]
sb2 = pd.DataFrame(json.load(open(f"{SB_BASE}\\sb1h_daily_20261014.json")))[["date", "close"]]
sb = pd.concat([sb1[sb1["date"] < sb2["date"].min()], sb2]).drop_duplicates("date").sort_values("date").reset_index(drop=True)

spy["r"] = spy["close"].pct_change() * 100
sb["r"] = sb["close"].pct_change() * 100
m = pd.merge(spy[["date", "r"]], sb[["date", "r"]], on="date", suffixes=("_spx", "_sb")).dropna().reset_index(drop=True)

WINDOWS = [
    ("全样本", None, None),
    ("W1 2015-16", "2015-08-24", "2016-10-06"),
    ("W2 2020-21", "2020-04-28", "2021-11-18"),
    ("W3 2022-23", "2022-10-03", "2023-11-07"),
    ("W4 2026-", "2026-04-17", "2026-10-13"),
]

def ols(y, x):
    """OLS: y = a + b*x, 返回 b, t_b, R2, n"""
    n = len(x)
    xm, ym = x.mean(), y.mean()
    sxx = ((x - xm) ** 2).sum()
    b = ((x - xm) * (y - ym)).sum() / sxx
    a = ym - b * xm
    resid = y - a - b * x
    s2 = (resid ** 2).sum() / (n - 2)
    se_b = np.sqrt(s2 / sxx)
    t = b / se_b
    r2 = 1 - (resid ** 2).sum() / ((y - ym) ** 2).sum()
    return b, t, r2, n

print("=" * 100)
print("一、标普涨跌幅分桶 → SB 同日表现 (全样本 2011-12 ~ 2026-10, n=%d)" % len(m))
print("=" * 100)
buckets = [
    ("标普大跌 ≤-2%", lambda x: x <= -2),
    ("标普跌 -2% ~ -1%", lambda x: (x > -2) & (x <= -1)),
    ("标普跌 -1% ~ -0.3%", lambda x: (x > -1) & (x <= -0.3)),
    ("标普微跌 -0.3% ~ 0", lambda x: (x > -0.3) & (x < 0)),
    ("标普上涨 >0", lambda x: x > 0),
]
rows_out = []
for name, cond in buckets:
    sub = m[cond(m["r_spx"])]
    rows_out.append({
        "桶": name, "n": len(sub),
        "SB均值%": sub["r_sb"].mean(), "SB中位%": sub["r_sb"].median(),
        "SB上涨占比": (sub["r_sb"] > 0).mean(), "SB下跌占比": (sub["r_sb"] < 0).mean(),
        "SPY均值%": sub["r_spx"].mean(),
    })
bt = pd.DataFrame(rows_out)
print(bt.round(2).to_string(index=False))

# 条件概率链: P(SB跌 | SPY跌, 幅度递增)
print("\n条件概率: P(SB当日下跌 | 标普下跌幅度)")
for thr in [-0.3, -0.5, -1.0, -1.5, -2.0, -3.0]:
    sub = m[m["r_spx"] <= thr]
    print(f"  SPY ≤ {thr}%: n={len(sub):4d}  P(SB跌)={100*(sub['r_sb']<0).mean():.1f}%  SB均 {sub['r_sb'].mean():+.2f}%  SB中位 {sub['r_sb'].median():+.2f}%")

# 同样的桶在四个牛市窗口内
print("\n" + "=" * 100)
print("二、牛市窗口内: 标普跌日 SB 是否跟跌")
print("=" * 100)
for wname, w0, w1 in WINDOWS[1:]:
    w = m[(m["date"] >= w0) & (m["date"] <= w1)]
    dn = w[w["r_spx"] < 0]
    up = w[w["r_spx"] > 0]
    print(f"\n[{wname}] 交易日 {len(w)}: 标普跌日 n={len(dn)} | SB跌日均 {dn['r_sb'].mean():+.2f}%, 中位 {dn['r_sb'].median():+.2f}%, P(SB跌)={100*(dn['r_sb']<0).mean():.0f}% | 标普涨日 SB均 {up['r_sb'].mean():+.2f}%")

# 回归: SB = a + b * SPY
print("\n" + "=" * 100)
print("三、OLS 回归: SB日收益 = a + b × SPY日收益")
print("=" * 100)
print(f"{'样本':<14}{'b(斜率)':>10}{'t值':>8}{'R²':>8}{'n':>7}")
for wname, w0, w1 in WINDOWS:
    w = m if w0 is None else m[(m["date"] >= w0) & (m["date"] <= w1)]
    b, t, r2, n = ols(w["r_sb"].values, w["r_spx"].values)
    print(f"{wname:<14}{b:>10.3f}{t:>8.1f}{r2:>8.3f}{n:>7}")

# Welch t 检验: 标普跌日 vs 涨日 SB 均值差
from math import sqrt
def welch(a, b_):
    ma, mb = a.mean(), b_.mean()
    va, vb = a.var(ddof=1), b_.var(ddof=1)
    t = (ma - mb) / sqrt(va / len(a) + vb / len(b_))
    return t

dn = m[m["r_spx"] < 0]["r_sb"]; up = m[m["r_spx"] > 0]["r_sb"]
print(f"\n四、全样本 Welch t 检验: 标普跌日SB均 {dn.mean():+.3f}% vs 涨日 {up.mean():+.3f}%, 差 {dn.mean()-up.mean():+.3f}pct, t={welch(dn, up):+.2f}")
for wname, w0, w1 in WINDOWS[1:]:
    w = m[(m["date"] >= w0) & (m["date"] <= w1)]
    d = w[w["r_spx"] < 0]["r_sb"]; u = w[w["r_spx"] > 0]["r_sb"]
    print(f"  {wname}: 跌日 {d.mean():+.3f}% vs 涨日 {u.mean():+.3f}%, t={welch(d, u):+.2f}")
