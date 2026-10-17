# -*- coding: utf-8 -*-
"""
ICE 原糖(SB1! 日线) × 郑糖主连(SR0, 新浪) 日收盘背离分析 · 2025-06-01 至今
SB 数据 = 本地 TV 导出 (2011-12~2026-09-25) 拼接 TV websocket 最新 (2026-05-21~2026-10-13)
SR0 数据 = 新浪 InnerFuturesNewService (主连日线)

背离定义（优先级从高到低）:
  D1 反向背离     : r_SB 与 r_SR 异号，且两者绝对值均 >= 0.2%
  D2 ICE大动郑糖钝化: 同向，|r_SB| >= 1.0% 且 |r_SR| < 33% * |r_SB|
  D3 郑糖独立行情 : |r_SR| >= 1.0% 且 |r_SB| < 33% * |r_SR|
  0 同步          : 其余
"""
import json, re, urllib.request
import pandas as pd

BASE = r"C:\Users\Administrator\Desktop\农业\data\price\sugar"
START = "2025-06-01"

# ---------- 1. SB: 本地 TV + 最新 TV 拼接 ----------
local = pd.read_csv(f"{BASE}\\sb_price_daily.csv")
local = local.rename(columns={local.columns[0]: "date", "close": "sb_close"})[["date", "sb_close"]]
local["sb_close"] = pd.to_numeric(local["sb_close"], errors="coerce")
local = local.dropna()

fresh = pd.DataFrame(json.load(open(f"{BASE}\\sb1h_daily_20261014.json")))
fresh = fresh[["date", "close"]].rename(columns={"close": "sb_close"})
fresh["sb_close"] = pd.to_numeric(fresh["sb_close"])

# 重叠期一致性校验
ov = pd.merge(local, fresh, on="date", suffixes=("_local", "_fresh"))
diff = (ov["sb_close_local"] - ov["sb_close_fresh"]).abs()
print(f"[SB拼接校验] 重叠 {len(ov)} 天, 最大收盘差 {diff.max():.4f}, 平均 {diff.mean():.4f}")

sb = pd.concat([
    local[local["date"] < fresh["date"].min()],
    fresh,
]).drop_duplicates("date").sort_values("date").reset_index(drop=True)
sb.to_csv(f"{BASE}\\sb_daily_spliced_20261014.csv", index=False)
print(f"[SB] {sb['date'].iloc[0]} ~ {sb['date'].iloc[-1]}, {len(sb)} 天, 最新收盘 {sb['sb_close'].iloc[-1]}")

# ---------- 2. SR0: 新浪 ----------
url = ("https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20t=/"
       "InnerFuturesNewService.getDailyKLine?symbol=SR0")
txt = urllib.request.urlopen(urllib.request.Request(
    url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "replace")
rows = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
sr = pd.DataFrame(rows).rename(columns={"d": "date", "c": "sr_close"})[["date", "sr_close"]]
sr["sr_close"] = pd.to_numeric(sr["sr_close"], errors="coerce")
sr = sr.dropna()
sr.to_csv(f"{BASE}\\sr0_daily_sina_20261014.csv", index=False)
sr = sr[sr["date"] >= START].reset_index(drop=True)
print(f"[SR0] {sr['date'].iloc[0]} ~ {sr['date'].iloc[-1]}, {len(sr)} 天, 最新收盘 {sr['sr_close'].iloc[-1]}")

# ---------- 3. merge & returns ----------
m = pd.merge(sb, sr, on="date", how="inner").sort_values("date").reset_index(drop=True)
m["r_sb"] = m["sb_close"].pct_change() * 100
m["r_sr"] = m["sr_close"].pct_change() * 100
m = m.dropna(subset=["r_sb", "r_sr"]).reset_index(drop=True)
print(f"[对齐] {len(m)} 天: {m['date'].iloc[0]} ~ {m['date'].iloc[-1]}")

# ---------- 4. classify ----------
NOISE, BIG, RATIO = 0.2, 1.0, 0.33

def classify(a, b):
    if a * b < 0 and min(abs(a), abs(b)) >= NOISE:
        return "D1_反向背离"
    if abs(a) >= BIG and abs(b) < RATIO * abs(a):
        return "D2_ICE大动郑糖钝化"
    if abs(b) >= BIG and abs(a) < RATIO * abs(b):
        return "D3_郑糖独立行情"
    return "0_同步"

m["div"] = [classify(a, b) for a, b in zip(m["r_sb"], m["r_sr"])]
m["gap_pp"] = m["r_sb"] - m["r_sr"]
m["roll20_corr"] = m["r_sb"].rolling(20).corr(m["r_sr"])

# ---------- 5. stats ----------
n = len(m)
cnt = m["div"].value_counts().to_dict()
print("\n=== 分类占比 ===")
order = ["D1_反向背离", "D2_ICE大动郑糖钝化", "D3_郑糖独立行情", "0_同步"]
for k in order:
    v = cnt.get(k, 0)
    print(f"  {k}: {v} 天 ({v/n*100:.1f}%)")
corr = m["r_sb"].corr(m["r_sr"])
print(f"全窗口 corr = {corr:.3f}; |gap|中位数 = {m['gap_pp'].abs().median():.2f}pp; |gap|>=1.5pp 天数 = {(m['gap_pp'].abs()>=1.5).sum()}")

# D2 细分：ICE 涨/跌 方向
d2 = m[m["div"] == "D2_ICE大动郑糖钝化"]
if len(d2):
    print(f"D2 细分: ICE大跌郑糖抗跌 {(d2['r_sb']<0).sum()} 天 | ICE大涨郑糖滞涨 {(d2['r_sb']>0).sum()} 天")

# 月度分布
m["ym"] = m["date"].str[:7]
monthly = m[m["div"] != "0_同步"].groupby("ym").size()
print("\n=== 背离日月度分布 ===")
print(monthly.to_string())

# 全部背离日
div_days = m[m["div"] != "0_同步"][
    ["date", "sb_close", "sr_close", "r_sb", "r_sr", "gap_pp", "div"]]
print(f"\n=== 全部背离日 ({len(div_days)} 天) ===")
print(div_days.to_string(index=False))

# 滚动相关最低段
rc = m.dropna(subset=["roll20_corr"])
print("\nroll20_corr: 当前 =", round(rc["roll20_corr"].iloc[-1], 2),
      "| 最低 =", round(rc["roll20_corr"].min(), 2), "于", rc.loc[rc["roll20_corr"].idxmin(), "date"],
      "| 最高 =", round(rc["roll20_corr"].max(), 2), "于", rc.loc[rc["roll20_corr"].idxmax(), "date"])

# ---------- 6. save ----------
out = m[["date", "sb_close", "sr_close", "r_sb", "r_sr", "gap_pp", "div", "roll20_corr"]]
out.to_csv(f"{BASE}\\sb_sr_divergence_daily.csv", index=False, encoding="utf-8-sig")
summary = {"window": [m["date"].iloc[0], m["date"].iloc[-1]], "days": n,
           "counts": {k: cnt.get(k, 0) for k in order}, "corr": round(corr, 3),
           "div_days": div_days.to_dict("records")}
json.dump(summary, open(f"{BASE}\\sb_sr_divergence_summary.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
print("\nsaved: sb_sr_divergence_daily.csv / sb_sr_divergence_summary.json")
