# -*- coding: utf-8 -*-
"""报告100 周更 2026-10-13 报告日（糖/棉，幂等脚本，串行单遍改写）"""
import io, sys

P = r"C:\Users\Administrator\Desktop\农业\reports\100_CFTC四窗联动图_白糖棉花Tab版\cftc持仓.html"
t = io.open(P, encoding="utf-8").read()

if '2026-10-13", "close": 21.11' in t and "418594" in t:
    print("ALREADY UPDATED"); sys.exit(0)

def append_series(text, varname, entry_json):
    """在 var <name> = {"series":[...]};} 行尾 ]}; 前插入一条"""
    i = text.index("var " + varname + " =")
    j = text.index("]};", i)
    return text[:j] + "," + entry_json + text[j:]

# ---- 1. DATA_SUGAR 追加 2026-10-13 ----
t = append_series(t, "DATA_SUGAR",
    '{"date": "2026-10-13", "close": 21.11, "nc_net": 226974, "nc_l": 418594, "nc_s": 191620, "oi": 1179144}')

# ---- 2. DATA_COTTON 追加 2026-10-13 ----
t = append_series(t, "DATA_COTTON",
    '{"date":"2026-10-13","close":80.0,"nc_net":94307,"nc_l":128518,"nc_s":34211,"oi":395640}')

# ---- 3. COT_SNAP sb ----
old_sb = """  sb: {
    date: '2026-10-06', unit: '112,000 POUNDS', code: '080732',
    oi: 1158944, chg_oi: 59768, totalTraders: 295,
    vals: [406286, 189011, 198079, 448754, 726098, 1053119, 1113188, 105825, 45756],
    chg:  [45360,  -3473,   18721,   -9540,   44883,   54541,   60131,   5227,   -363],
    traders: [127, 62, 94, 77, 80, 249, 195]
  },"""
new_sb = """  sb: {
    date: '2026-10-13', unit: '112,000 POUNDS', code: '080732',
    oi: 1179144, chg_oi: 20200, totalTraders: 301,
    vals: [418594, 191620, 202786, 453716, 740906, 1075096, 1135312, 104048, 43832],
    chg:  [12308,   2609,   4707,   4962,  14808,   21977,   22124,  -1777,  -1924],
    traders: [144, 53, 91, 76, 78, 255, 191]
  },"""
assert old_sb in t, "sb block not found"
t = t.replace(old_sb, new_sb, 1)

# ---- 4. COT_SNAP ct ----
old_ct = """  ct: {
    date: '2026-10-06', unit: '50,000 POUNDS', code: '033661',
    oi: 382230, chg_oi: -7264, totalTraders: 343,
    vals: [128343, 31985, 69181, 168574, 272079, 366098, 373245, 16132, 8985],
    chg:  [-4296,  -4041,  -5992,   3638,   2702,   -6650,  -7331,    -614,    67],
    traders: [169, 67, 116, 72, 77, 290, 221]
  }"""
new_ct = """  ct: {
    date: '2026-10-13', unit: '50,000 POUNDS', code: '033661',
    oi: 395640, chg_oi: 13410, totalTraders: 342,
    vals: [128518, 34211, 77146, 173636, 275082, 379300, 386439, 16340, 9201],
    chg:  [175, 2226, 7965, 5062, 3003, 13202, 13194, 208, 216],
    traders: [167, 69, 116, 78, 81, 291, 228]
  }"""
assert old_ct in t, "ct block not found"
t = t.replace(old_ct, new_ct, 1)

# ---- 5. meta / note ----
old = "数据窗口 2011-12 ~ 2026-10 · 772 个 CFTC 报告周"
assert old in t; t = t.replace(old, "数据窗口 2011-12 ~ 2026-10 · 773 个 CFTC 报告周", 1)

old = "数据窗口 2009-01-06 ~ 2026-10-06 · 927 个 CFTC 报告周"
assert old in t; t = t.replace(old, "数据窗口 2009-01-06 ~ 2026-10-13 · 928 个 CFTC 报告周", 1)

old = "最新（2026-10-06）：净多 9.6 万手、OI 38.2 万手，均处多年高位区。"
assert old in t; t = t.replace(old, "最新（2026-10-13）：净多 9.4 万手、OI 39.6 万手，均处多年高位区。", 1)

io.open(P, "w", encoding="utf-8", newline="").write(t)
print("UPDATED OK")
