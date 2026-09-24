# -*- coding: utf-8 -*-
"""
批量下载 ISO World Sugar Balance memo 早期期次（当年发布视角），标准库实现（无第三方依赖）
- 官方公开路径: https://www.isosugar.org/content/memo/world_sugar_balance_<month>_<year>.pdf
- 双源回退: www.isosugar.org -> archive.isosugar.org
- 归档目录: balance_pdfs/historical/world_sugar_balance_<month>_<year>.pdf
- 目标期次: 2015-02 ~ 2024-08（每季 2/5/8/11 月）
已下载的 8 期（nov2024~aug2026）在主目录 balance_pdfs/ 下，此处跳过（nov2024 起）。
"""
import os
import sys
import time
import ssl
import urllib.request

# 数据输出目录固定指向 data/fundamentals/sugar/iso/balance_pdfs/historical（脚本位于 scripts/ 下）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "fundamentals", "sugar", "iso")
OUT_DIR = os.path.join(DATA_DIR, "balance_pdfs", "historical")
os.makedirs(OUT_DIR, exist_ok=True)

# archive.isosugar.org 证书 hostname 不匹配（证书只覆盖 www），禁用证书校验以允许抓取
_SSL_CTX = ssl._create_unverified_context()

MONTHS = ["february", "may", "august", "november"]
YEARS = list(range(2015, 2025))  # 2015 ~ 2024

HOSTS = [
    "https://www.isosugar.org/content/memo/",
    "https://archive.isosugar.org/content/memo/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}


def try_download(url, timeout=40, unverified=False):
    req = urllib.request.Request(url, headers=HEADERS)
    kwargs = {"timeout": timeout}
    if unverified:
        kwargs["context"] = _SSL_CTX
    with urllib.request.urlopen(req, **kwargs) as resp:
        data = resp.read()
        return resp.status, data


results = []
for year in YEARS:
    for month in MONTHS:
        # 已下载的 8 期: nov2024 之后全部已有（2025、2026）
        if (year == 2024 and month == "november") or year >= 2025:
            continue
        fname = f"world_sugar_balance_{month}_{year}.pdf"
        fpath = os.path.join(OUT_DIR, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 100000:
            results.append((fname, "SKIP(exists)", fpath))
            continue
        ok = False
        last_err = ""
        for i, host in enumerate(HOSTS):
            url = host + fname
            try:
                status, data = try_download(url, unverified=(i > 0))
                if status == 200 and len(data) > 100000 and data[:5] == b"%PDF-":
                    with open(fpath, "wb") as f:
                        f.write(data)
                    results.append((fname, f"OK {len(data)}", host))
                    ok = True
                    break
                else:
                    last_err = f"{host} -> HTTP {status} size {len(data)}"
            except Exception as e:
                last_err = f"{host} -> ERR {type(e).__name__}: {e}"
        if not ok:
            results.append((fname, f"FAIL {last_err}", "-"))
        time.sleep(0.4)

ok_n = sum(1 for _, s, _ in results if s.startswith("OK"))
skip_n = sum(1 for _, s, _ in results if s.startswith("SKIP"))
fail_n = sum(1 for _, s, _ in results if s.startswith("FAIL"))
print(f"TOTAL {len(results)}  OK {ok_n}  SKIP {skip_n}  FAIL {fail_n}")
print("--- FAIL list ---")
for fname, status, _ in results:
    if status.startswith("FAIL"):
        print(f"  {fname}  {status}")
print("--- OK list ---")
for fname, status, host in results:
    if status.startswith("OK"):
        print(f"  {fname} ({status.split()[1]} bytes) <- {host}")

with open(os.path.join(OUT_DIR, "_download_log.csv"), "w", encoding="utf-8") as f:
    f.write("file,status,source\n")
    for fname, status, host in results:
        f.write(f"{fname},{status},{host}\n")
print("log written:", os.path.join(OUT_DIR, "_download_log.csv"))