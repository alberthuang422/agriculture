# -*- coding: utf-8 -*-
"""CDP 实测: 100号四窗图 反转按钮功能验证
流程: 起临时http服务 -> 无头Chrome -> 打开页面 -> 点击#btnFlip前后读yAxis[2].inverse状态
"""
import json, os, subprocess, sys, time, threading, urllib.request, websocket

REPORTS = r"C:\Users\Administrator\Desktop\农业\reports"
URL = "http://127.0.0.1:8771/100_%E7%99%BD%E7%B3%96CFTC%E4%BB%B7%E6%A0%BC%E5%A4%9A%E7%A9%BA%E5%87%80%E5%9B%9B%E7%AA%97%E5%9B%BE/index.html"

# ---------- 1. HTTP 服务 ----------
import http.server, socketserver
os.chdir(REPORTS)
srv = None
def serve():
    global srv
    H = http.server.SimpleHTTPRequestHandler
    srv = socketserver.TCPServer(("127.0.0.1", 8771), H)
    srv.serve_forever()
threading.Thread(target=serve, daemon=True).start()
time.sleep(0.8)
print("[1] HTTP server on :8771")

# ---------- 2. 无头 Chrome ----------
CHROME = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
user_dir = r"C:\Users\Administrator\Desktop\农业\.tmp_chrome_cdp"
import shutil
shutil.rmtree(user_dir, ignore_errors=True)
proc = subprocess.Popen([
    CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=9223", "--remote-allow-origins=*",
    f"--user-data-dir={user_dir}",
    "--window-size=1400,900", "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    # 等待调试端口
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:9223/json/version", timeout=1)
            break
        except Exception:
            time.sleep(0.4)
    else:
        print("[2] CDP port not up"); sys.exit(1)
    print("[2] headless Chrome up on :9223")

    # ---------- 3. 建 target ----------
    req = urllib.request.Request("http://127.0.0.1:9223/json/new", data=b"{}",
                                 headers={"Content-Type":"application/json"}, method="PUT")
    target = json.load(urllib.request.urlopen(req, timeout=5))
    ws_url = target["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url, timeout=15)
    mid = 0
    def send(method, params=None):
        global mid
        mid += 1
        ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid:
                return msg
    def ev_eval(expr):
        r = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    # ---------- 4. 打开页面 ----------
    send("Page.enable")
    send("Runtime.enable")
    send("Page.navigate", {"url": URL})
    time.sleep(5)  # 等 echarts CDN 加载

    # 页面已加载?
    title = ev_eval("document.title")
    print("[3] page title:", title)
    btn = ev_eval("!!document.getElementById('btnFlip')")
    print("[4] btnFlip exists:", btn)
    hasChart = ev_eval("typeof echarts !== 'undefined' && echarts.getInstanceByDom(document.getElementById('chart')) !== undefined")
    print("[5] echarts instance:", hasChart)

    # 读取当前 yAxis[2] inverse (点击前)
    inv0 = ev_eval("echarts.getInstanceByDom(document.getElementById('chart')).getOption().yAxis[2].inverse")
    print("[6] yAxis[2].inverse BEFORE click:", inv0)

    # ---------- 5. 点击按钮 ----------
    clicked = ev_eval("document.getElementById('btnFlip').click(); 'clicked'")
    time.sleep(1.2)
    inv1 = ev_eval("echarts.getInstanceByDom(document.getElementById('chart')).getOption().yAxis[2].inverse")
    btnText = ev_eval("document.getElementById('btnFlip').textContent")
    tip = ev_eval("(document.getElementById('flipTip')||{}).textContent || ''")
    print("[7] AFTER click -> inverse:", inv1, "| btn:", btnText, "| tip:", tip[:40])

    # ---------- 6. 再点一次恢复 ----------
    ev_eval("document.getElementById('btnFlip').click(); 'x'")
    time.sleep(1.2)
    inv2 = ev_eval("echarts.getInstanceByDom(document.getElementById('chart')).getOption().yAxis[2].inverse")
    print("[8] AFTER 2nd click -> inverse:", inv2)

    ok = (inv0 in (False, None)) and (inv1 is True) and (inv2 in (False, None)) and btn and hasChart
    print("\nRESULT:", "PASS ✅ 按钮翻转功能正常" if ok else "FAIL ❌")
    ws.close()
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except Exception: proc.kill()
    time.sleep(0.5)
    shutil.rmtree(user_dir, ignore_errors=True)
print("[done]")