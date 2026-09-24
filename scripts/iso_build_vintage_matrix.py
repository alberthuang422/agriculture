# -*- coding: utf-8 -*-
"""ISO 官方 World Sugar Balance vintage 矩阵构建（数据已从 8 期官方 PDF 手工提取核对）。
来源: data/fundamentals/sugar/iso/balance_pdfs/*.pdf 第2页全球汇总表 (千吨 tel quel)
生成:
  iso_balance_vintage_matrix.csv  - surplus/deficit vintage 矩阵
  iso_balance_raw_matrix.json     - 完整指标×vintage×market_year
"""
import csv, json, os

BASE = r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'

# 每期: (vintage, market_year列表, 各指标[production,consumption,surplus_deficit,import_demand,export_availability,end_stocks,stock_to_use])
# 数值千吨; stock_to_use 为 % 浮点; None=该期未发布
PDFS = {
 "2024-11": {
   "years": ["2024/25","2023/24","2022/23","2021/22","2020/21","2019/20","2018/19",
             "2017/18","2016/17","2015/16","2014/15","2013/14","2012/13","2011/12"],
   "production": [179069,181365,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804,163597],
   "consumption": [181582,180053,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645,157961],
   "surplus_deficit": [-2513,1312,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159,5636],
   "import_demand": [64409,69103,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781,54327],
   "export_availability": [63127,69559,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781,54327],
   "end_stocks": [96544,97775,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742,73583],
   "stock_to_use": [53.17,54.30,54.65,56.12,60.58,61.10,61.14,56.65,50.09,51.89,56.23,55.82,49.95,46.58],
 },
 "2025-02": {
   "years": ["2024/25","2023/24","2022/23","2021/22","2020/21","2019/20","2018/19",
             "2017/18","2016/17","2015/16","2014/15","2013/14","2012/13","2011/12"],
   "production": [175540,181384,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804,163597],
   "consumption": [180421,179972,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645,157961],
   "surplus_deficit": [-4881,1412,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159,5636],
   "import_demand": [63324,69119,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781,54327],
   "export_availability": [62661,69635,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781,54327],
   "end_stocks": [93597,97815,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742,73583],
   "stock_to_use": [51.88,54.35,54.65,56.12,60.58,61.10,61.14,56.65,50.09,51.89,56.23,55.82,49.95,46.58],
 },
 "2025-05": {
   "years": ["2024/25","2023/24","2022/23","2021/22","2020/21","2019/20","2018/19",
             "2017/18","2016/17","2015/16","2014/15","2013/14","2012/13","2011/12"],
   "production": [174795,181264,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804,163597],
   "consumption": [180261,179225,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645,157961],
   "surplus_deficit": [-5466,2039,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159,5636],
   "import_demand": [63133,69342,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781,54327],
   "export_availability": [63323,68713,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781,54327],
   "end_stocks": [93931,99587,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742,73583],
   "stock_to_use": [52.11,55.57,54.65,56.12,60.58,61.10,61.14,56.65,50.09,51.89,56.23,55.82,49.95,46.58],
 },
 "2025-08": {
   "years": ["2025/26","2024/25","2023/24","2022/23","2021/22","2020/21","2019/20",
             "2018/19","2017/18","2016/17","2015/16","2014/15","2013/14","2012/13"],
   "production": [180593,175174,181208,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804],
   "consumption": [180824,180053,181639,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645],
   "surplus_deficit": [-231,-4879,-431,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159],
   "import_demand": [63768,63789,70085,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781],
   "export_availability": [63890,64213,68781,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781],
   "end_stocks": [92136,92489,97792,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742],
   "stock_to_use": [None,None,None,None,None,None,None,None,None,None,None,None,None,None],
 },
 "2025-11": {
   "years": ["2025/26","2024/25","2023/24","2022/23","2021/22","2020/21","2019/20",
             "2018/19","2017/18","2016/17","2015/16","2014/15","2013/14","2012/13"],
   "production": [181767,176215,181047,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804],
   "consumption": [180142,179131,181207,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645],
   "surplus_deficit": [1625,-2916,-160,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159],
   "import_demand": [62962,64513,72078,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781],
   "export_availability": [64733,64740,70533,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781],
   "end_stocks": [95015,95161,98304,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742],
   "stock_to_use": [None,None,None,None,None,None,None,None,None,None,None,None,None,None],
 },
 "2026-02": {
   "years": ["2025/26","2024/25","2023/24","2022/23","2021/22","2020/21","2019/20",
             "2018/19","2017/18","2016/17","2015/16","2014/15","2013/14","2012/13"],
   "production": [181287,176056,181095,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804],
   "consumption": [180069,179520,181207,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645],
   "surplus_deficit": [1218,-3464,-112,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159],
   "import_demand": [63222,64731,71475,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781],
   "export_availability": [64324,64796,71521,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781],
   "end_stocks": [93300,93184,96713,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742],
   "stock_to_use": [None,None,None,None,None,None,None,None,None,None,None,None,None,None],
 },
 "2026-05": {
   "years": ["2025/26","2024/25","2023/24","2022/23","2021/22","2020/21","2019/20",
             "2018/19","2017/18","2016/17","2015/16","2014/15","2013/14","2012/13"],
   "production": [182004,175874,180954,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132,171804],
   "consumption": [179760,179070,181207,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215,163645],
   "surplus_deficit": [2244,-3196,-253,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917,8159],
   "import_demand": [63334,65147,71616,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822,60781],
   "export_availability": [64234,64816,71521,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822,60781],
   "end_stocks": [95240,93896,96761,96919,98801,102544,102950,103525,96543,86492,88362,93953,91659,81742],
   "stock_to_use": [52.98,52.44,53.40,54.65,56.12,60.58,61.10,61.14,56.65,50.09,51.89,56.23,55.82,49.95],
   "updated_end_stocks": [79360,78896,83617,83544,86209,90878,92143,93521,89609,80982,84656,91854,90266,81052],
   "updated_stock_to_use": [44.15,44.06,46.14,47.11,48.96,53.69,54.69,55.10,52.58,47.08,49.71,54.98,54.97,49.53],
 },
 "2026-08": {
   "years": ["2026/27","2025/26","2024/25","2023/24","2022/23","2021/22","2020/21",
             "2019/20","2018/19","2017/18","2016/17","2015/16","2014/15","2013/14"],
   "production": [180141,180695,174994,180954,175473,172189,168702,167866,174435,179828,169073,163825,169373,174132],
   "consumption": [180375,179551,178637,181207,177344,176066,169266,168492,169315,170420,172683,170287,167079,164215],
   "surplus_deficit": [-234,1144,-3643,-253,-1871,-3877,-564,-626,5120,9408,-3610,-6462,2294,9917],
   "import_demand": [66908,67328,67876,71616,68435,67790,64901,65768,57639,64103,66512,67814,58419,57822],
   "export_availability": [68184,67299,67876,71521,68446,67663,64858,65717,57639,63460,65442,66943,58419,57822],
   "end_stocks": [None]*14,   # Aug-2026 官方说明: 库存数据重审中, 本期不发布
   "stock_to_use": [None]*14,
 },
}

ROWS = ["production","consumption","surplus_deficit","import_demand","export_availability","end_stocks","stock_to_use"]
CN = {"production":"Production(kt)","consumption":"Consumption(kt)","surplus_deficit":"Surplus/Deficit(kt)",
      "import_demand":"Import demand(kt)","export_availability":"Export availability(kt)",
      "end_stocks":"End stocks(kt)","stock_to_use":"Stocks/Consumption(%)"}

# 1) surplus/deficit vintage 矩阵 CSV
all_years_sorted = ["2011/12","2012/13","2013/14","2014/15","2015/16","2016/17","2017/18","2018/19",
                    "2019/20","2020/21","2021/22","2022/23","2023/24","2024/25","2025/26","2026/27"]
vintage_order = ["2024-11","2025-02","2025-05","2025-08","2025-11","2026-02","2026-05","2026-08"]

def get(vintage, year, metric):
    d = PDFS[vintage]
    if year not in d["years"] or metric not in d:
        return None
    idx = d["years"].index(year)
    if len(d[metric]) <= idx:
        return None
    return d[metric][idx]

# 矩阵 CSV: 行=market_year, 列=vintage
mpath = os.path.join(BASE, "iso_balance_vintage_matrix.csv")
with open(mpath, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["market_year"] + vintage_order + ["unit", "note"])
    notes = {
        "2015/16": "缺口起点(连续6年缺口之1)",
        "2017/18": "过剩峰值",
        "2021/22": "ISO 2024年起回溯修订, 从旧口径-2655kt扩至-3877kt",
        "2022/23": "ISO 2024年起回溯修订, 从旧口径+310kt翻转为-1871kt",
        "2023/24": "跨年份大幅修订: +2039(May-25) → -253(Aug-26)",
        "2024/25": "缺口头一年内多次修订: -4879→-2916→-3464→-3196→-3643",
        "2025/26": "本季5个vintage: 首版-231 → 11月+1625 → 2月+1218 → 5月+2244 → 8月+1144",
        "2026/27": "首版(2026-08)",
    }
    for y in all_years_sorted:
        row = [y]
        for v in vintage_order:
            sd = get(v, y, "surplus_deficit")
            row.append("" if sd is None else sd)
        row.append("kt (tel quel)")
        row.append(notes.get(y, ""))
        w.writerow(row)

# 2) 完整 raw matrix JSON
raw = {}
for v in vintage_order:
    d = PDFS[v]
    raw[v] = {"market_years": d["years"]}
    for m in ROWS:
        raw[v][m] = d.get(m, [])
        raw[v]["_note_" + m] = CN[m]
rpath = os.path.join(BASE, "iso_balance_raw_matrix.json")
with open(rpath, "w", encoding="utf-8") as f:
    json.dump(raw, f, ensure_ascii=False, indent=1)

# 3) 与现有 iso_qmo_vintage.json 合并: 更新 historical_final_series 为最新官方(2026-08)口径, 并追加 vintage 表
jpath = os.path.join(BASE, "iso_qmo_vintage.json")
with open(jpath, encoding="utf-8") as f:
    jd = json.load(f)

jd["official_balance_pdfs"] = {
    "path": "balance_pdfs/",
    "public": True,
    "files": ["world_sugar_balance_november_2024.pdf","world_sugar_balance_february_2025.pdf",
              "world_sugar_balance_may_2025.pdf","world_sugar_balance_august_2025.pdf",
              "world_sugar_balance_november_2025.pdf","world_sugar_balance_february_2026.pdf",
              "world_sugar_balance_may_2026.pdf","world_sugar_balance_august_2026.pdf",
              "world_sugar_balance_november_2023.pdf"],
    "note": "ISO 官网 /content/memo/ 路径公开可下载(年度报表由各期 QMO 同期发布)。购买版World Sugar Balance为£170/期, 但官方 memo PDF 免费。",
    "stock_discontinuity": "Aug-2026 起 ISO 正在进行全球库存数据的全面重审, 该期不发布库存/库消比, 修订结果将于2026年鉴与Nov-2026 QMO发布。",
}

# 用最新官方值(2026-08 版, 缺失补 2026-05)更新最终序列
final = {}
for y in all_years_sorted:
    p = get("2026-08", y, "production")
    c = get("2026-08", y, "consumption")
    sd = get("2026-08", y, "surplus_deficit")
    es = get("2026-08", y, "end_stocks")
    stu = get("2026-08", y, "stock_to_use")
    if p is None and y in ["2011/12","2012/13"]:  # Aug-2026 从2013/14开始
        p = get("2026-02", y, "production"); c = get("2026-02", y, "consumption")
        sd = get("2026-02", y, "surplus_deficit"); es = get("2026-02", y, "end_stocks"); stu = get("2026-02", y, "stock_to_use")
    final[y] = {
        "production_mt": None if p is None else round(p/1000, 3),
        "consumption_mt": None if c is None else round(c/1000, 3),
        "balance_mt": None if sd is None else round(sd/1000, 3),
        "end_stocks_mt": None if es is None else round(es/1000, 3),
        "stock_to_use_pct": stu,
    }

jd["historical_final_series_2010_2026_mt"] = [
    {"market_year": y,
     "production": final[y]["production_mt"],
     "consumption": final[y]["consumption_mt"],
     "balance": final[y]["balance_mt"],
     "end_stocks": final[y]["end_stocks_mt"],
     "stock_to_use_pct": final[y]["stock_to_use_pct"],
     "caliber": "latest official (2026-08, 库存空缺)"
               if y in ["2026/27","2025/26","2024/25"] and final[y]["end_stocks_mt"] is None
               else "latest official (2026-08)"}
    for y in all_years_sorted
]

# 追加官方 vintage 细节块(平衡表/生产/消费矩阵)
jd["official_vintage_matrix"] = {
    "surplus_deficit_kt": {y: {v: get(v,y,"surplus_deficit") for v in vintage_order} for y in all_years_sorted},
}
with open(jpath, "w", encoding="utf-8") as f:
    json.dump(jd, f, ensure_ascii=False, indent=2)

print("matrix csv:", mpath)
print("raw json:", rpath)
print("merged json:", jpath)
print("\n--- 2025/26 官方 revision 链 (kt) ---")
for v in vintage_order:
    print(v, get(v,"2025/26","surplus_deficit"))
print("\n--- 2024/25 官方 revision 链 (kt) ---")
for v in vintage_order:
    print(v, get(v,"2024/25","surplus_deficit"))