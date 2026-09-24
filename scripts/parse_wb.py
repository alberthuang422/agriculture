# -*- coding: utf-8 -*-
"""解析 WB pink sheet monthly：定位 Cotton 列并导出月度序列"""
import openpyxl, json

F = r"C:\Users\Administrator\Desktop\stock\data\cotton\CMO-Historical-Data-Monthly.xlsx"
wb = openpyxl.load_workbook(F, data_only=True)
print(wb.sheetnames)
sh = wb[wb.sheetnames[0]]
# 找列头
coords = []
for row in sh.iter_rows(min_row=1, max_row=10):
    for c in row:
        v = c.value
        if isinstance(v, str) and ("otton" in v or "February" in v or "January" in v):
            coords.append((c.row, c.column, v))
print("HEADERS:", coords[:20])
sh2 = wb["Monthly Prices"]
# 列头结构：第一行表的年份跨度，真正列名多在 3-7 行；宽搜 40 行
for row in sh2.iter_rows(min_row=1, max_row=40):
    for c in row:
        v = c.value
        if isinstance(v, str) and "otton" in v:
            print("COTTON at", c.row, c.column, v)
# 月份列
for row in sh2.iter_rows(min_row=1, max_row=40, min_col=1, max_col=3):
    for c in row:
        if c.value is not None:
            print((c.row, c.column), repr(c.value))
