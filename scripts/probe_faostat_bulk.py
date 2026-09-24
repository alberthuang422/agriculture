# -*- coding: utf-8 -*-
"""探测 FAOSTAT 各下载通道可达性"""
import urllib.request, ssl, time

ctx = ssl.create_default_context()
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

URLS = [
    ("fenix bulk zip (Production_Crops_E_All_Data)",
     "https://fenixservices.fao.org/faostat/static/bulkdownloads/datasets_E/datasets/Production_Crops_E_All_Data.zip"),
    ("fenix bulk 根目录",
     "https://fenixservices.fao.org/faostat/static/bulkdownloads/datasets_E/datasets/"),
    ("bulk.uni-fao.org Production_Crops_E_All_Data.zip",
     "https://bulk.uni-fao.org/production/crops/Production_Crops_E_All_Data.zip"),
    ("bulk.uni-fao.org 根目录",
     "https://bulk.uni-fao.org/production/crops/"),
    ("fenix 域名根",
     "https://fenixservices.fao.org/"),
    ("FAOSTAT 主站 API 域名 fenixservices 是否可用",
     "https://fenixservices.fao.org/faostat/api/v1/en/definitions/elements/1001"),
]

for name, url in URLS:
    try:
        req = urllib.request.Request(url, headers=HDRS)
        # 只读 header 不下载 body（zip 会很大）
        with urllib.request.urlopen(req, timeout=25, context=ctx) as resp:
            info = dict(resp.headers)
            ct = info.get("Content-Type", "")
            cl = info.get("Content-Length", "?")
            print(f"[OK]   {name}: HTTP {resp.status} type={ct} len={cl}", flush=True)
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}", flush=True)
    time.sleep(1)