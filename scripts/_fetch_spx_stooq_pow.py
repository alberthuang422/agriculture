# -*- coding: utf-8 -*-
"""Solve stooq.com JS proof-of-work challenge (via curl) and download SPX daily CSV."""
import hashlib
import re
import subprocess
import sys
import urllib.parse

BASE = "https://stooq.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
JAR = "_stooq_cookies.txt"


def curl(args):
    cmd = ["curl", "-s", "--max-time", "60", "-A", UA, "-b", JAR, "-c", JAR, "-e", BASE + "/"] + args
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def get(url):
    return curl([url])


def post(url, data):
    return curl(["-X", "POST", "--data", urllib.parse.urlencode(data), url])


def solve_and_verify(html):
    m = re.search(r'c="([^"]+)",d=(\d+)', html)
    if not m:
        return False
    c, d = m.group(1), int(m.group(2))
    target = "0" * d
    n = 0
    while True:
        h = hashlib.sha256((c + str(n)).encode()).hexdigest()
        if h.startswith(target):
            break
        n += 1
    resp = post(BASE + "/__verify", {"c": c, "n": str(n)})
    print(f"[challenge] d={d} solved n={n}, verify resp: {resp[:80]!r}")
    return True


def download(symbol, outfile):
    url = f"{BASE}/q/d/l/?s={symbol}&i=d"
    html = get(url)
    if html.lstrip().startswith("<!DOCTYPE"):
        if not solve_and_verify(html):
            print("no challenge found but html returned")
            sys.exit(2)
        html = get(url)
    if html.lstrip().startswith("<!DOCTYPE"):
        print("still blocked after verify")
        sys.exit(3)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
    lines = html.strip().splitlines()
    print(f"{symbol}: {len(lines)-1} rows -> {outfile}")
    print("first:", lines[1])
    print("last :", lines[-1])


if __name__ == "__main__":
    download("%5Espx", "_spx_stooq_daily.csv")
