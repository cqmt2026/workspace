# -*- coding: utf-8 -*-
import urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

positions = [
    {'code': '600549', 'name': '厦门钨业', 'shares': 900, 'avg_cost': 63.20, 'market': 'sh'},
    {'code': '000539', 'name': '粤电力A', 'shares': 2800, 'avg_cost': 6.16, 'market': 'sz'},
]

syms = 'sh600549,sz000539'
url = 'https://qt.gtimg.cn/q=' + syms
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req, context=ctx, timeout=10)
data = r.read().decode('gbk')

lines = [l for l in data.strip().split('\n') if l]

print('=' * 55)
print('  持仓股 - 详细行情分析')
print('=' * 55)

for pos in positions:
    sym = pos['market'] + pos['code']
    for line in lines:
        if sym in line:
            f = line.split('~')
            cur = float(f[3])
            prev = float(f[4])
            open_p = float(f[5])
            vol_str = f[6] if len(f) > 6 else '0'
            vol = int(float(vol_str)) if vol_str else 0
            high = float(f[33]) if len(f) > 33 and f[33] else 0
            low = float(f[34]) if len(f) > 34 and f[34] else 0
            change = cur - prev
            pct = change / prev * 100
            cost = pos['avg_cost']
            profit = (cur - cost) / cost * 100
            near_high = (cur - high) / high * 100 if high else 0
            from_open = (cur - open_p) / open_p * 100 if open_p else 0
            market_cap = cur * pos['shares']

            print()
            print('%s (%s)' % (pos['name'], sym))
            print('-' * 45)
            print('  现价:    %.2f' % cur)
            print('  涨跌:    %+.2f (%+.2f%%)' % (change, pct))
            print('  今开:    %.2f  (相比开盘 %+.2f%%)' % (open_p, from_open))
            print('  最高:    %.2f  (距高点 %+.2f%%)' % (high, near_high))
            print('  最低:    %.2f' % low)
            print('  成交量:  %d 手' % vol)
            print()
            print('  持仓:    %d股  成本: %.2f' % (pos['shares'], cost))
            print('  浮盈:    %+.2f (%+.2f%%)' % ((cur-cost)*pos['shares'], profit))
            print('  市值:    %.2f' % market_cap)

            # 简单信号
            signals = []
            if pct > 5:
                signals.append('强势上涨')
            elif pct > 2:
                signals.append('温和上涨')
            elif pct > 0:
                signals.append('小幅上涨')
            elif pct > -2:
                signals.append('小幅下跌')
            else:
                signals.append('大幅下跌')

            if near_high > -2:
                signals.append('接近日内高点')
            elif near_high < -5:
                signals.append('回调较深')

            if from_open > 2:
                signals.append('低开高走')
            elif from_open < -2:
                signals.append('高开低走')

            print('  信号:    %s' % ' / '.join(signals))
            break

print()
print('=' * 55)