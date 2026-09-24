# -*- coding: utf-8 -*-
"""构建 ISO 全球食糖平衡表年度序列 2010/11-2026/27.
数据来源：
  2010/11-2023/24: ISO 官方 World Sugar Balance PDF (Nov-2023) —— 千吨原值, 转百万吨
  2024/25: ISO QMO (Feb-2026, ChiniMandi 完整表) 
  2025/26: ISO QMO (Aug-2026 HEADLINES 最新) + Feb-2026 细节
  2026/27: ISO QMO (Aug-2026 首版)
"""
import csv, os, json

base = r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'

# (market_year, production_kt, consumption_kt, balance_kt, imports_kt, exports_kt, end_stocks_kt, stock_to_use_pct, source, note)
official = [
    ("2010/11", 156177, 153147,  3030,  53942,  53948,  67947, 44.37, "ISO balance PDF Nov-2023", ""),
    ("2011/12", 163597, 157961,  5636,  54327,  54327,  73583, 46.58, "ISO balance PDF Nov-2023", ""),
    ("2012/13", 171804, 163645,  8159,  60781,  60781,  81742, 49.95, "ISO balance PDF Nov-2023", ""),
    ("2013/14", 174132, 164215,  9917,  57822,  57822,  91659, 55.82, "ISO balance PDF Nov-2023", ""),
    ("2014/15", 169373, 167079,  2294,  58419,  58419,  93953, 56.23, "ISO balance PDF Nov-2023", ""),
    ("2015/16", 163825, 170287, -6462,  67814,  66943,  88362, 51.89, "ISO balance PDF Nov-2023", "连续第六年缺口起点(官方口径)"),
    ("2016/17", 169073, 172683, -3610,  66512,  65442,  86492, 50.09, "ISO balance PDF Nov-2023", ""),
    ("2017/18", 179828, 170420,  9408,  64103,  63460,  96543, 56.65, "ISO balance PDF Nov-2023", "过剩周期峰值"),
    ("2018/19", 174435, 169315,  5120,  57639,  57639, 103525, 61.14, "ISO balance PDF Nov-2023", ""),
    ("2019/20", 167866, 168492,  -626,  65768,  65717, 102950, 61.10, "ISO balance PDF Nov-2023", "过剩结束, 转缺口"),
    ("2020/21", 168702, 169266,  -564,  64901,  64858, 102544, 60.58, "ISO balance PDF Nov-2023", "疫情年, 消费受抑"),
    ("2021/22", 172189, 174844, -2655,  67790,  67663, 100023, 57.21, "ISO balance PDF Nov-2023", ""),
    ("2022/23", 178328, 178018,   310,  66068,  65695, 100706, 56.57, "ISO balance PDF Nov-2023", ""),
    ("2023/24", 179887, 180222,  -335,  65058,  64760, 100669, 55.86, "ISO balance PDF Nov-2023", "消费后经 QMO 上修至 181.2Mt 附近(见 notes)"),
]

# 2023/24 消费口径修订: ChiniMandi(Feb-2026 QMO) 引 181.207 Mt
# 2024/25: QMO Feb-2026 完整表 (ChiniMandi)
# 2025/26: QMO Aug-2026 HEADLINES (balance +1.1, cons 179.6); 产量取 Feb-2026 最新公开 181.287
recent = [
    ("2024/25", 176.056, 179.520, -3.464, 64.731, 64.796, 93.184, 51.91,
     "ISO QMO Feb-2026 (latest full table)",
     "缺口由 Nov-25 的 2.916 上修至 3.464 (美国消费上修)；May-26 收窄至 3.196"),
    ("2025/26", 181.287, 179.600,  1.100,  63.222, 64.324, 93.300, None,
     "ISO QMO Aug-2026 HEADLINES + Feb-2026",
     "平衡/消费为 Aug-26 最新(过剩由 May 2.244 腰斩至 1.1)；产量为 Feb-26 最新公开 181.287；库消比双口径: 旧 51.81% / 修订 44.15%(May-26 起)"),
    ("2026/27", None,   180.400, -0.200,  None,   None,   None,   None,
     "ISO QMO Aug-2026 首版预估",
     "首版即缺口 0.2Mt; 巴西以外产量预计 -4.4Mt(欧盟/泰国/中美洲); 贸易盈余 1.3Mt; 厄尔尼诺为主要风险"),
]

rows = []
for my, p, c, b, i, e, s, r, src, note in official:
    rows.append({
        "market_year": my, "production_mt": round(p/1000, 3), "consumption_mt": round(c/1000, 3),
        "balance_mt": round(b/1000, 3), "import_demand_mt": round(i/1000, 3),
        "export_availability_mt": round(e/1000, 3), "end_stocks_mt": round(s/1000, 3),
        "stock_to_use_pct": r, "source": src, "notes": note,
    })
for my, p, c, b, i, e, s, r, src, note in recent:
    rows.append({
        "market_year": my, "production_mt": p, "consumption_mt": c,
        "balance_mt": b, "import_demand_mt": i,
        "export_availability_mt": e, "end_stocks_mt": s,
        "stock_to_use_pct": r, "source": src, "notes": note,
    })

cols = ["market_year","production_mt","consumption_mt","balance_mt","import_demand_mt",
        "export_availability_mt","end_stocks_mt","stock_to_use_pct","source","notes"]
out_csv = os.path.join(base, "iso_world_balance_2010_2026.csv")
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)

# 同步补充 JSON (历史序列块)
jpath = os.path.join(base, "iso_qmo_vintage.json")
with open(jpath, encoding="utf-8") as f:
    d = json.load(f)
d["historical_final_series_2010_2026_mt"] = [
    {"market_year": r["market_year"], "production": r["production_mt"],
     "consumption": r["consumption_mt"], "balance": r["balance_mt"],
     "end_stocks": r["end_stocks_mt"], "stock_to_use_pct": r["stock_to_use_pct"]}
    for r in rows
]
with open(jpath, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print("rows:", len(rows))
print("csv:", out_csv, os.path.getsize(out_csv), "bytes")
print("json updated:", os.path.getsize(jpath), "bytes")
for r in rows:
    if r["market_year"] in ("2015/16","2019/20","2023/24","2024/25","2025/26","2026/27"):
        print(r["market_year"], "balance", r["balance_mt"], "| P", r["production_mt"], "| C", r["consumption_mt"])