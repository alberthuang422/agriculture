import hashlib, re, subprocess, sys

base = 'https://stooq.com'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
JAR = r'C:/Users/Administrator/Desktop/农业/data/cftc/latest/_stooq_cookies.txt'
url = base + '/q/d/l/?s=sb.f&d1=20260922&d2=20261002&i=d'

def curl(args):
    return subprocess.run(['curl', '-sL', '-A', UA, '-b', JAR, '-c', JAR] + args,
                          capture_output=True, text=True).stdout

html = curl([url])
if 'Date,Open,High,Low,Close' in html:
    print(html)
    sys.exit(0)
m = re.search(r'const c="([^"]+)",d=(\d+)', html)
if not m:
    print('NO_CHALLENGE', html[:300])
    sys.exit(1)
c, d = m.group(1), int(m.group(2))
n = 0
while not hashlib.sha256((c + str(n)).encode()).hexdigest().startswith('0' * d):
    n += 1
print('solved n =', n, file=sys.stderr)
curl(['-X', 'POST', base + '/__verify', '--data', 'c=' + c + '&n=' + str(n)])
html = curl([url])
print(html if 'Date,Open' in html else 'STILL_BLOCKED: ' + html[:300])
