# -*- coding: utf-8 -*-
"""Bark: 回调背景条件分析要点"""
import json, urllib.request

MSG = """①"涨幅大→回调深"不成立: 20条腿前期涨幅vs回撤深度相关系数r=-0.03, 深回调(≤-12%)的前期涨幅中位20% vs 浅回调19%, 无差别。深回调全部由外生冲击触发(巴西压榨/雷亚尔/原油/印度政策), 不是价格涨出来的。
②回调节奏: 牛市中平均每6~9周一次>6%回调(腿长中位39天)。当前腿(9-18低点起)才25天, 早于典型时点。
③月份分布: 9月最高发(4/20次), 10月仅1次(低发), 11-12月各2次。
④当前对照: 现价20.83, 距10-13高点仅-1.3%, 未达-6%; 本轮4月以来累计+58%但2015-16两个月+42%、全程+136%, 累计涨幅不算异常。
⑤持仓不拥挤: 净多/OI占比12.4%(51.7百分位), 远低于2016-09(38.4%)与2023-04(29.1%)顶部水平。
⑥结论: 此刻统计条件不支持"即将>6%回调"的判断。真正的风险窗口是10月底~11月: UNICA双周报(糖醇比是否回升)、ISMA印度首版、ISO QMO——既是历史深回调的触发源, 也衔接11-12月季节性高发段。若UNICA显示糖醇比回升+印度产量利空兑现, 深回调(-10%以上)概率显著上升。"""

body = json.dumps({"title": "白糖回调条件核对: 当前不符, 盯10月底-11月数据窗",
                   "body": MSG, "group": "Sugar"},
                  ensure_ascii=False).encode("utf-8")
req = urllib.request.Request("https://api.day.app/ehGL5HsAui7weuiBEQFaY6",
                             data=body, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode("utf-8"))
