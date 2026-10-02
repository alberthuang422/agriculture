import csv, sys
base = r'C:/Users/Administrator/Desktop/农业/data/cftc/latest'
data = {}
with open(base + '/fresh_tmp/annual.txt', encoding='latin-1') as f:
    r = csv.reader(f)
    next(r)
    for row in r:
        if row[3] in ('080732', '033661') and row[2] in ('2026-09-22', '2026-09-29'):
            data.setdefault(row[3], {})[row[2]] = row
pairs = [('OI',7,7,37),('NCL',8,8,38),('NCS',9,9,39),('SPRD',10,10,40),('CL',11,11,41),('CS',12,12,42),('TL',13,13,43),('TS',14,14,44),('NRL',15,15,45),('NRS',16,16,46)]
for code in ('080732', '033661'):
    p, c = data[code]['2026-09-22'], data[code]['2026-09-29']
    out = []
    for n, i, j, k in pairs:
        diff = int(c[i]) - int(p[j])
        chg = int(c[k])
        out.append(n + ':OK' if diff == chg else n + ':MISMATCH diff=%d chg=%d' % (diff, chg))
    print(code, ' '.join(out))
