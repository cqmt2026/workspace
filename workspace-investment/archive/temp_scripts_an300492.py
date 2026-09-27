"""300492 分析"""
import json, urllib.request

def get_kline(secid, klt, fqt=0, beg='', count=500):
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt={fqt}&beg={beg}&end=20500101&lmt={count}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode('utf-8')).get('data', {}).get('klines', [])

def get_rt(secid):
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58,f43,f44,f45,f46,f47,f48,f50'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode('utf-8')).get('data', {})

def ema(prices, n):
    k = 2/(n+1)
    r = [prices[0]]
    for p in prices[1:]: r.append(p*k + r[-1]*(1-k))
    return r

def macd(closes):
    e12, e26 = ema(closes, 12), ema(closes, 26)
    dif = [e12[i]-e26[i] for i in range(len(closes))]
    dea = ema(dif, 9)
    return dif, dea, [(dif[i]-dea[i])*2 for i in range(len(dif))]

def kdj(closes, n=9):
    k_list, d_list = [50]*n, [50]*n
    k, d = 50, 50
    for i, price in enumerate(closes[n:]):
        idx = i + n
        lows, highs = closes[idx-n:idx], closes[idx-n:idx]
        lm, hm = min(lows), max(highs)
        rsv = (price-lm)/(hm-lm)*100 if hm>lm else 50
        k = 2/3*k + 1/3*rsv
        d = 2/3*d + 1/3*k
        k_list.append(k); d_list.append(d)
    return k_list, d_list, [3*k_list[i]-2*d_list[i] for i in range(len(k_list))]

stock = '300492'
secid = '0.' + stock
rt = get_rt(secid)
daily = get_kline(secid, 101, 0, '', 200)
min60 = get_kline(secid, 5, 0, '20260301', 2000)

closes = [float(k.split(',')[2]) for k in daily]
dates = [k.split(',')[0] for k in daily]
highs = [float(k.split(',')[3]) for k in daily]
lows = [float(k.split(',')[4]) for k in daily]

cur = closes[-1]
prev = closes[-2]
ma5 = sum(closes[-5:])/5
ma10 = sum(closes[-10:])/10
ma20 = sum(closes[-20:])/20
ma60 = sum(closes[-60:])/60
dif, dea, hist = macd(closes)
k_l, d_l, j_l = kdj(closes)

name = rt.get('f58', 'N/A')
price = rt.get('f43', 'N/A')
chg_rt = rt.get('f48', 'N/A')
high_rt = rt.get('f44', 'N/A')
low_rt = rt.get('f45', 'N/A')
open_rt = rt.get('f46', 'N/A')

print('='*50)
print(stock, name)
print('='*50)
print('现价:', price, ' 涨跌幅:', chg_rt, '%')
print('今开:', open_rt, ' 最高:', high_rt, ' 最低:', low_rt)
print()
print('日线:', len(daily), '条 (', dates[0], '->', dates[-1], ')')
print('60分钟:', len(min60), '条')
print()
print('均线: MA5=%.2f MA10=%.2f MA20=%.2f MA60=%.2f' % (ma5, ma10, ma20, ma60))
print('最新:', cur, ' 昨收:', prev, ' 涨幅:%.2f%%' % ((cur-prev)/prev*100))
print()
print('MACD: DIF=%.4f DEA=%.4f MACD柱=%.4f' % (dif[-1], dea[-1], hist[-1]))
if dif[-1] > 0 and hist[-1] > 0:
    print('MACD状态: 金叉区域，红柱')
elif dif[-1] < 0 and hist[-1] < 0:
    print('MACD状态: 绿柱区域')
else:
    print('MACD状态: 即将金叉' if dif[-1] < 0 and hist[-1] > 0 else 'MACD状态: 即将死叉')
print()
print('KDJ: K=%.2f D=%.2f J=%.2f' % (k_l[-1], d_l[-1], j_l[-1]))
if k_l[-1] > 80:
    print('KDJ状态: 超买')
elif k_l[-1] < 20:
    print('KDJ状态: 超卖')
else:
    print('KDJ状态: 中性区域')
print()
print('10日高:%.2f 10日低:%.2f' % (max(highs[-10:]), min(lows[-10:])))
print('20日高:%.2f 20日低:%.2f' % (max(highs[-20:]), min(lows[-20:])))
print()
# 综合评分
score = 0
if cur > ma20: score += 1
if ma5 > ma10: score += 1
if dif[-1] > 0: score += 1
if hist[-1] > 0: score += 1
if k_l[-1] > 50: score += 1
if k_l[-1] < 80: score += 1
result = '偏多' if score >= 5 else '偏空' if score <= 2 else '中性'
print('综合评分:', score, '/6 -', result)
print()
# 均线多头/空头
if ma5 > ma10 > ma20:
    print('均线排列: 多头排列')
elif ma5 < ma10 < ma20:
    print('均线排列: 空头排列')
else:
    print('均线排列: 混乱')
print()
# 60分钟
if min60:
    m60_c = [float(k.split(',')[2]) for k in min60]
    m60_d = [k.split(',')[0] for k in min60]
    print('60分钟最近5根:')
    for i in range(5):
        idx = -5 + i
        if abs(idx) <= len(m60_c):
            c = m60_c[idx]
            dt = m60_d[idx]
            prev_c = m60_c[idx-1] if idx-1 >= -len(m60_c) else c
            chg = (c - prev_c) / prev_c * 100 if prev_c != 0 else 0
            print('  ', dt, '%.2f' % c, '(%.1f%%)' % chg)