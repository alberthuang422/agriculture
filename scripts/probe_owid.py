# -*- coding: utf-8 -*-
"""探测 OWID 甘蔗数据 CSV 通道"""
import urllib.request, ssl, time

ctx = ssl.create_default_context()
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

CANDIDATES = [
    "sugar-cane-production",
    "sugar-cane-yield",
    "sugar-cane-yields",
    "sugar-cane-area",
    "sugar-cane-area-harvested",
    "sugar-cane",
]

for slug in CANDIDATES:
    url = f"https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full&useColumnShortNames=true"
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            first = raw.splitlines()[:8]
            print(f"[OK] {slug}: HTTP {resp.status} lines~{raw.count(chr(10))}")
            for ln in first:
                print("    |", ln[:160])
    except Exception as e:
        print(f"[FAIL] {slug}: {type(e).__name__}: {e}", flush=True)
    time.sleep(0.8)