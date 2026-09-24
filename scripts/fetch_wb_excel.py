# -*- coding: utf-8 -*-
"""World Bank Pink Sheet monthly -> cotton 月度价。URL 失效则尝试多候选。"""
import urllib.request, ssl

URLS = [
    "https://thedocs.worldbank.org/en/doc/5d4336b255aaf5c72d01d3e03ad15408-0350012021/related/CMO-Historical-Data-Monthly.xlsx",
    "https://www.worldbank.org/en/research/commodity-markets",
]
for u in URLS:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        if data[:4] == b"PK\x03\x04" or b"Monthly" in data[:200000]:
            open(r"C:\Users\Administrator\Desktop\stock\data\cotton\CMO-Historical-Data-Monthly.xlsx", "wb").write(data)
            print("SAVED", u, len(data), "bytes")
            break
        else:
            print(u, "not xlsx:", data[:80])
    except Exception as e:
        print(u, "ERR", repr(e))
