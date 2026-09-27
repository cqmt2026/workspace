import json, urllib.request

def get_kline(secid, klt, count=120):
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt=1&beg=&end=20500101&lmt={count}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode('utf-8')).get('data', {}).get('klines', [])

# 厦门钨业 sh.600549 = 1.600549
# 粤电力A sz.000539 = 0.000539
data = {}
stocks = [('600549', '1', 'XMTC'), ('000539', '0', 'YDL')]

for code, mkt, name in stocks:
    daily = get_kline(f'{mkt}.{code}', 101, 120)
    data[name] = daily
    print(name + ': ' + str(len(daily)) + ' bars')
    if daily:
        first = daily[0].split(',')
        last = daily[-1].split(',')
        print('  from ' + first[0] + ' to ' + last[0])
        print('  last bar: date=' + last[0] + ' open=' + last[1] + ' close=' + last[2] + ' high=' + last[3] + ' low=' + last[4] + ' vol=' + last[5])

# Save for analysis
with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\src\tools_h\chan_analyze_data.json', 'w', encoding='utf-8') as f:
    json.dump({'XMTC': data['XMTC'], 'YDL': data['YDL']}, f, ensure_ascii=False)
print('Data saved')