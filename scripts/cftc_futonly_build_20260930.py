# -*- coding: utf-8 -*-
"""从 CFTC 官方 futures-only 年度压缩包重建农产品 24 品种全史持仓序列（1986-01 ~ 2026-09-22）。
背景：本地 agri_cot_history_1995_2026.csv 实为期货+期权合并口径（已实测确认），
本脚本产出真正的 futures-only 序列：data/cftc/results_cot/agri_cot_futonly_1986_2026.csv
锚校验：糖 2015-09-01 OI 应 = 818,040（与 sugar_cftc_futonly_1986_2026.csv 一致）。
"""
import csv, glob, io, os, zipfile

LATEST = r"C:\Users\Administrator\Desktop\农业\data\cftc\latest"
OUT    = r"C:\Users\Administrator\Desktop\农业\data\cftc\results_cot\agri_cot_futonly_1986_2026.csv"

def map_market(nm):
    nm = nm.upper().strip()
    if "SPOT" in nm or "MIDAM" in nm: return None
    if nm.startswith("COTTON NO. 2"): return "棉花 2号 (ICE)"
    if nm.startswith("SUGAR NO. 11"): return "糖 11号 (ICE)"
    if nm.startswith("COFFEE C"):     return "咖啡 C (ICE)"
    if nm.startswith("COCOA"):        return "可可 (ICE)"
    if nm.startswith("FRZN CONCENTRATED ORANGE JUICE"): return "冻橙汁 (ICE)"
    if nm.startswith("ROUGH RICE"):   return "糙米 (CBOT)"
    if nm.startswith("CORN"):         return "玉米 (CBOT)"
    if nm.startswith("OATS"):         return "燕麦 (CBOT)"
    if nm.startswith("SOYBEANS"):     return "大豆 (CBOT)"
    if nm.startswith("SOYBEAN OIL"):  return "豆油 (CBOT)"
    if nm.startswith("SOYBEAN MEAL"): return "豆粕 (CBOT)"
    if nm.startswith("CANOLA"):       return "油菜籽 (ICE)"
    if nm.startswith("LIVE CATTLE"):  return "活牛 (CME)"
    if nm.startswith("FEEDER CATTLE"):return "育肥牛 (CME)"
    if nm.startswith("LEAN HOGS"):    return "瘦肉猪 (CME)"
    if nm.startswith("BUTTER") and "MERCANTILE" in nm:        return "黄油 (CME)"
    if (nm.startswith("CHEDDAR CHEESE") or nm.startswith("CHEESE")) and "MERCANTILE" in nm: return "奶酪 (CME)"
    if nm.startswith("NON FAT DRY MILK") and "MERCANTILE" in nm: return "脱脂奶粉 (CME)"
    if nm.startswith("DRY WHEY"):     return "乳清粉 (CME)"
    if nm.startswith("MILK, CLASS III") and "MERCANTILE" in nm: return "三级牛奶 (CME)"
    if nm.startswith("MILK - CHICAGO MERCANTILE"): return "三级牛奶 (CME)"
    if nm.startswith("WHEAT"):
        if "BLACK SEA" in nm or "DURUM" in nm or "WHITE" in nm: return None
        if "WHEAT-SRW" in nm or ("WHEAT " in nm and "CHICAGO" in nm):  return "小麦 SRW (CBOT)"
        if "WHEAT-HRW" in nm or "KANSAS" in nm:  return "小麦 HRW (KCBT→CBOT)"
        if "WHEAT-HRS" in nm or "MINNEAPOLIS" in nm: return "小麦 HRS (MGE→MIAX)"
    return None

out_rows = {}   # (market, date) -> row dict
n_rows = 0
zips = ["deacot1986_2016.zip"] + [f"deacot{y}.zip" for y in range(2017, 2026)] + ["deacot2026.zip"]
anchor_ok = None
for zn in zips:
    zp = os.path.join(LATEST, zn)
    z = zipfile.ZipFile(zp)
    tn = [x for x in z.namelist() if x.lower().endswith(".txt")][0]
    for r in csv.reader(io.StringIO(z.read(tn).decode("latin-1"))):
        if len(r) < 13: continue
        m = map_market(r[0])
        if not m: continue
        yy = int(r[1][:2])
        d = f"{19 if yy >= 70 else 20}{r[1][:2]}-{r[1][2:4]}-{r[1][4:]}"
        try:
            rec = {"market": m, "date": d, "oi": float(r[7]), "nc_l": float(r[8]),
                   "nc_s": float(r[9]), "nc_sp": float(r[10]),
                   "c_l": float(r[11]), "c_s": float(r[12])}
        except ValueError:
            continue
        rec["nc_net"] = rec["nc_l"] - rec["nc_s"]; rec["c_net"] = rec["c_l"] - rec["c_s"]
        out_rows[(m, d)] = rec   # 同键后者覆盖（去重）
        n_rows += 1
        if m == "糖 11号 (ICE)" and d == "2015-09-01":
            anchor_ok = (rec["oi"] == 818040.0)

print(f"原始数据行 {n_rows}，去重后 {len(out_rows)}")
print("锚校验 糖 2015-09-01 OI==818040 :", "OK" if anchor_ok else "FAIL")
assert anchor_ok, "列布局锚校验失败，停止"

rows = sorted(out_rows.values(), key=lambda x: (x["market"], x["date"]))
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["market","date","oi","nc_l","nc_s","nc_sp","c_l","c_s","nc_net","c_net"])
    w.writeheader(); w.writerows(rows)
print(f"saved -> {OUT}")

# 覆盖概览
import collections
cnt = collections.Counter(r["market"] for r in rows)
for m, n in cnt.most_common():
    ds = [r["date"] for r in rows if r["market"] == m]
    print(f"  {m:<20} {n:>5} 周  {ds[0]} ~ {ds[-1]}")
