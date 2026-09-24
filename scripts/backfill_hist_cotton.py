# -*- coding: utf-8 -*-
"""补全分国历史：1980-2023 逐年 /country/all 扫取（带重试+退避）"""
import json, ssl, urllib.request, time, os

KEY = "DxRVr66dGKqS1pItPj1sUXl1PLgmu3CmUPZCJsPL"
CC = "2631000"
OUT = r"C:\Users\Administrator\Desktop\stock\data\cotton\raw"
ok, fail = 0, []
for y in range(1980, 2024):
    path = f"/commodity/{CC}/country/all/year/{y}"
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://api.fas.usda.gov/api/psd" + path,
                                         headers={"X-Api-Key": KEY})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
            if isinstance(d, list) and d:
                json.dump(d, open(os.path.join(OUT, f"all_{y}.json"), "w"), ensure_ascii=False)
                ok += 1
                print(y, len(d), flush=True)
            else:
                print(y, "EMPTY", str(d)[:80], flush=True)
                fail.append(y)
            break
        except Exception as e:
            wait = 3 * (attempt + 1)
            print(y, "retry", attempt, repr(e)[:100], f"wait {wait}s", flush=True)
            time.sleep(wait)
    else:
        fail.append(y)
    time.sleep(0.4)
print("DONE ok:", ok, "fail:", fail)
