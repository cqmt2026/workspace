"""600549 + 688399 完整分析"""
import json, urllib.request

def get_kline(secid, klt, fqt=0, beg='', count=500):
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt={fqt}&beg={beg}&end=20500101&lmt={count}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('utf-8')
    return json.loads(raw).get('data', {}).get('klines', [])

def get_realtime(secid):
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58,f43,f44,f45,f46,f47,f48,f50,f57,f58,f60'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
    resp = urllib.request.urlopen(req, timeout=10)
    d = json.loads(resp.read().decode('utf-8')).get('data', {})
    return d

def ema(prices, n):
    k = 2/(n+1)
    result = [prices[0]]
    for p in prices[1:]:
        result.append(p * k + result[-1] * (1-k))
    return result

def macd(closes):
    e12 = ema(closes, 12)
    e26 = ema(closes, 26)
    dif = [e12[i] - e26[i] for i in range(len(closes))]
    dea = ema(dif, 9)
    return dif, dea, [(dif[i]-dea[i])*2 for i in range(len(dif))]

def kdj(closes, n=9):
    k_list, d_list = [50]*n, [50]*n
    k, d = 50, 50
    for i, price in enumerate(closes[n:]):
        i += n
        lows = closes[i-n:i]
        highs = closes[i-n:i]
        low_min, high_max = min(lows), max(highs)
        rsv = (price - low_min) / (high_max - low_min) * 100 if high_max > low_min else 50
        k = 2/3*k + 1/3*rsv
        d = 2/3*d + 1/3*k
        k_list.append(k)
        d_list.append(d)
    j_list = [3*k_list[i]-2*d_list[i] for i in range(len(k_list))]
    return k_list, d_list, j_list

def analyze(stock, name):
    print(f'\n{"="*55}')
    print(f'{name} ({stock})')
    print(f'{"="*55}')
    
    # 实时行情
    secid = f'1.{stock}' if stock.startswith('6') else f'0.{stock}'
    rt = get_realtime(secid)
    print(f'名称: {rt.get("f58","N/A")}')
    print(f'现价: {rt.get("f43","N/A")}')
    print(f'涨跌幅: {rt.get("f48","N/A")}%')
    print(f'今开: {rt.get("f46","N/A")}  最高: {rt.get("f44","N/A")}  最低: {rt.get("f45","N/A")}')
    print(f'成交量: {rt.get("f47","N/A")}手')
    
    # K线数据
    daily_kl = get_kline(secid, 101, 0, '', 200)
    min60_kl = get_kline(secid, 5, 0, '20260301', 2000)
    
    if not daily_kl:
        print('无日线数据')
        return
    
    closes_d = [float(k.split(',')[2]) for k in daily_kl]
    dates_d = [k.split(',')[0] for k in daily_kl]
    highs_d = [float(k.split(',')[3]) for k in daily_kl]
    lows_d = [float(k.split(',')[4]) for k in daily_kl]
    
    print(f'\n日线: {len(daily_kl)}条 ({dates_d[0]} -> {dates_d[-1]})')
    print(f'60分钟: {len(min60_kl)}条')
    
    # MA
    ma5 = sum(closes_d[-5:])/5
    ma10 = sum(closes_d[-10:])/10
    ma20 = sum(closes_d[-20:])/20
    ma60 = sum(closes_d[-60:])/60
    cur = closes_d[-1]
    prev = closes_d[-2]
    chg = (cur-prev)/prev*100
    
    print(f'\n--- 均线 ---')
    print(f'MA5: {ma5:.2f}  MA10: {ma10:.2f}  MA20: {ma20:.2f}  MA60: {ma60:.2f}')
    print(f'最新: {cur:.2f}  昨收: {prev:.2f}  涨幅: {chg:+.2f}%')
    
    # 多头排列
    if ma5 > ma10 > ma20:
        print('均线: 多头排列 ✅')
    elif ma5 < ma10 < ma20:
        print('均线: 空头排列 ❌')
    else:
        print('均线: 混乱')
    
    # MACD
    dif, dea, hist = macd(closes_d)
    print(f'\n--- MACD ---')
    print(f'DIF: {dif[-1]:.4f}  DEA: {dea[-1]:.4f}  MACD柱: {hist[-1]:.4f}')
    if dif[-1] > 0 and hist[-1] > 0:
        print('MACD: 金叉区域，红柱 ✅')
    elif dif[-1] > 0 and hist[-1] < 0:
        print('MACD: 绿柱收窄 ⚠️')
    elif dif[-1] < 0 and hist[-1] < 0:
        print('MACD: 绿柱区域 ❌')
    else:
        print('MACD: 即将金叉 ⚠️')
    
    # KDJ
    k_list, d_list, j_list = kdj(closes_d)
    print(f'\n--- KDJ(9) ---')
    print(f'K: {k_list[-1]:.2f}  D: {d_list[-1]:.2f}  J: {j_list[-1]:.2f}')
    if k_list[-1] > 80:
        print('KDJ: 超买 ⚠️')
    elif k_list[-1] < 20:
        print('KDJ: 超卖 ✅')
    else:
        print('KDJ: 中性区域')
    
    # 近期支撑压力
    high10 = max(highs_d[-10:])
    low10 = min(lows_d[-10:])
    high20 = max(highs_d[-20:])
    low20 = min(lows_d[-20:])
    print(f'\n--- 关键价位 ---')
    print(f'10日高: {high10:.2f}  10日低: {low10:.2f}')
    print(f'20日高: {high20:.2f}  20日低: {low20:.2f}')
    print(f'当前: {cur:.2f}  距10日高: {(high10-cur)/cur*100:.1f}%  距10日低: {(cur-low10)/low10*100:.1f}%')
    
    # 60分钟缠论笔
    if min60_kl:
        closes_m60 = [float(k.split(',')[2]) for k in min60_kl]
        dates_m60 = [k.split(',')[0] for k in min60_kl]
        print(f'\n--- 60分钟近期 ---')
        print(f'最新: {closes_m60[-1]:.2f}  ({dates_m60[-1]})')
        # 最近5根60分钟
        for i in range(-5, 0):
            if abs(i) <= len(closes_m60):
                dt = dates_m60[i] if i >= -len(dates_m60) else ''
                c = closes_m60[i] if i >= -len(closes_m60) else 0
                h = float(min60_kl[i].split(',')[3]) if i >= -len(min60_kl) else 0
                l = float(min60_kl[i].split(',')[4]) if i >= -len(min60_kl) else 0
                chg_m = (closes_m60[i]-closes_m60[i-1])/closes_m60[i-1]*100 if i < -1 else 0
                print(f'  {dt} 收:{c:.2f} 高:{h:.2f} 低:{l:.2f} 幅:{chg_m:+.1f}%')
    
    # 综合评分
    score = 0
    if cur > ma20: score += 1
    if ma5 > ma10: score += 1
    if dif[-1] > 0: score += 1
    if hist[-1] > 0: score += 1
    if k_list[-1] > 50: score += 1
    if k_list[-1] < 80: score += 1
    print(f'\n综合评分: {score}/6')
    if score >= 5:
        print('总体: 偏多 ✅')
    elif score <= 2:
        print('总体: 偏空 ❌')
    else:
        print('总体: 中性 ⚠️')

# 同时分析两只
analyze('600549', '600549 厦门钨业')
analyze('688399', '688399 硕世生物')