# -*- coding: utf-8 -*-
import urllib.request, json
from datetime import datetime, timedelta

CODES = {
    'sz002805': '丰元股份',
    'sh600186': '莲花控股',
    'sz000833': '粤桂股份',
    'sh688556': '高测股份',
    'sz002456': '欧菲光'
}

# 1. 实时快照
qt = ','.join(CODES.keys())
url = f'https://qt.gtimg.cn/q={qt}'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
raw = resp.read().decode('gbk')

snap = {}
for line in raw.strip().split('\n'):
    if '~' not in line: continue
    p = line.split('~')
    if len(p) < 6: continue
    sym = p[2]
    if sym in CODES:
        prev = float(p[4]) if p[4] else float(p[3])
        price = float(p[3])
        snap[sym] = {
            'name': p[1], 'price': price, 'prev': prev,
            'chg_pct': round((price - prev) / prev * 100, 2) if prev else 0,
            'high': float(p[33]) if p[33] else price,
            'low': float(p[34]) if p[34] else price,
            'vol': float(p[36]) if p[36] else 0,
        }

# 2. 近30日K线（腾讯his）
beg = (datetime.now() - timedelta(days=45)).strftime('%Y%m%d')
end = datetime.now().strftime('%Y%m%d')

klines = {}
for code in CODES:
    market = '1' if code.startswith('sh') else '0'
    secid = market + code[2:]
    qurl = (f'https://qt.gtimg.cn/q={secid},d'
            f'&beg={beg}&end={end}&fields1=f1,f2,f3,f4,f5,f6'
            f'&fields2=f51,f52,f53,f54,f55,f56,f57,f58')
    try:
        r2 = urllib.request.urlopen(
            urllib.request.Request(qurl, headers={'User-Agent': 'Mozilla/5.0'}), timeout=5)
        d2 = json.loads(r2.read())
        klines[code] = d2.get('data', {}).get(code, {}).get('day', [])
    except Exception as e:
        klines[code] = []

print("=== 持仓5只实时数据 ===")
for code, name in CODES.items():
    s = snap.get(code, {})
    k = klines.get(code, [])
    print(f"\n{code} {name}")
    print(f"  实时: {s.get('price','N/A')} 昨{s.get('prev','N/A')} {s.get('chg_pct','N/A')}% 高{s.get('high','N/A')} 低{s.get('low','N/A')}")
    print(f"  近{klines.get(code,[]) and len(klines.get(code,[])}根K线")
    if klines.get(code):
        closes = [float(l[2]) for l in klines[code]]
        print(f"  近期收盘: {closes[-10:]}")
        print(f"  MA5: {sum(closes[-5:])/5:.2f}" if len(closes)>=5 else "  MA5: N/A")
        print(f"  MA10: {sum(closes[-10:])/10:.2f}" if len(closes)>=10 else "  MA10: N/A")
        print(f"  MA20: {sum(closes[-20:])/20:.2f}" if len(closes)>=20 else "  MA20: N/A")
