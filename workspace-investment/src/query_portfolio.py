# -*- coding: utf-8 -*-
import urllib.request
import ssl

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
print('  投资组合 - 实时行情')
print('=' * 55)

total_cost = 0
total_market = 0

for pos in positions:
    sym = pos['market'] + pos['code']
    for line in lines:
        if sym in line:
            fields = line.split('~')
            cur_price = float(fields[3])
            yesterday_close = float(fields[4])
            change = cur_price - yesterday_close
            change_pct = (change / yesterday_close) * 100

            market_value = cur_price * pos['shares']
            cost_total = pos['avg_cost'] * pos['shares']
            profit = market_value - cost_total
            profit_pct = (profit / cost_total) * 100
            total_cost += cost_total
            total_market += market_value

            symbol = '▲' if change >= 0 else '▼'
            print()
            print('%s (%s)' % (pos['name'], pos['code']))
            print('  现价: %.2f  涨跌: %s%.2f (%.2f%%)' % (cur_price, symbol, abs(change), change_pct))
            print('  持仓: %d股  成本: %.2f' % (pos['shares'], pos['avg_cost']))
            print('  市值: %.2f  盈亏: %+.2f (%.2f%%)' % (market_value, profit, profit_pct))
            break

total_profit = total_market - total_cost
total_profit_pct = (total_profit / total_cost) * 100

print()
print('-' * 55)
print('  组合总计')
print('  总成本: %.2f' % total_cost)
print('  总市值: %.2f' % total_market)
print('  总盈亏: %+.2f (%.2f%%)' % (total_profit, total_profit_pct))
print('=' * 55)
print('  数据时间: %s' % fields[30])