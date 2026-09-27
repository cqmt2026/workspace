# -*- coding: utf-8 -*-
"""
缠论 + 实时行情 完整持仓分析
厦门钨业(600549.SH) + 粤电力A(000539.SZ)
"""
import baostock as bs
import urllib.request
import ssl
from datetime import datetime, timedelta

# === 实时行情 ===
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

positions = [
    {'code': '600549', 'name': '厦门钨业', 'shares': 900, 'cost': 63.20, 'market': 'sh'},
    {'code': '000539', 'name': '粤电力A', 'shares': 2800, 'cost': 6.16, 'market': 'sz'},
]

syms = 'sh600549,sz000539'
url = 'https://qt.gtimg.cn/q=' + syms
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req, context=ctx, timeout=10)
data = r.read().decode('gbk')
lines = [l for l in data.strip().split('\n') if l]

# 解析实时数据
realtime = {}
for pos in positions:
    sym = pos['market'] + pos['code']
    for line in lines:
        if sym in line:
            f = line.split('~')
            cur = float(f[3])
            prev = float(f[4])
            open_p = float(f[5])
            vol = int(float(f[6])) if f[6] else 0
            high = float(f[33]) if len(f) > 33 and f[33] else 0
            low = float(f[34]) if len(f) > 34 and f[34] else 0
            realtime[pos['code']] = {
                'name': pos['name'],
                'cur': cur,
                'prev': prev,
                'open': open_p,
                'high': high,
                'low': low,
                'vol': vol,
                'change': cur - prev,
                'pct': (cur - prev) / prev * 100 if prev else 0,
            }
            break

# === Baostock K线 ===
lg = bs.login()
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

def get_kline(code_baostock):
    rs = bs.query_history_k_data_plus(
        code_baostock,
        'date,open,high,low,close,volume',
        start_date=start_date, end_date=end_date,
        frequency='d', adjustflag='2'
    )
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    return data

def calc_ma(closes, period):
    result = []
    for i in range(len(closes)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(closes[i-period+1:i+1]) / period)
    return result

def find_fenxing(klines):
    """识别顶底分型"""
    fractals = []
    for i in range(1, len(klines) - 1):
        prev, curr, nxt = klines[i-1], klines[i], klines[i+1]
        ch, cl = float(curr[2]), float(curr[3])
        ph, pl = float(prev[2]), float(prev[3])
        nh, nl = float(nxt[2]), float(nxt[3])
        if ch > ph and ch > nh and cl > pl and cl > nl:
            fractals.append({'i': i, 'type': 'top', 'date': curr[0], 'high': ch, 'low': cl})
        elif ch < ph and ch < nh and cl < pl and cl < nl:
            fractals.append({'i': i, 'type': 'bottom', 'date': curr[0], 'high': ch, 'low': cl})
    return fractals

def full_analysis(pos, rt):
    """综合缠论 + 实时"""
    bao_code = 'sh.' + pos['code'] if pos['market'] == 'sh' else 'sz.' + pos['code']
    klines = get_kline(bao_code)
    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]

    fractals = find_fenxing(klines)
    tops = [f for f in fractals if f['type'] == 'top']
    bottoms = [f for f in fractals if f['type'] == 'bottom']

    # 最近N日
    N = 20
    recent_c = closes[-N:]
    recent_h = highs[-N:]
    recent_l = lows[-N:]
    cur_price = rt['cur']

    ma5 = calc_ma(closes, 5)
    ma10 = calc_ma(closes, 10)
    ma20 = calc_ma(closes, 20)
    ma60 = calc_ma(closes, 60)

    m5 = ma5[-1] if ma5[-1] else 0
    m10 = ma10[-1] if ma10[-1] else 0
    m20 = ma20[-1] if ma20[-1] else 0
    m60 = ma60[-1] if len(ma60) > 0 and ma60[-1] else 0

    # 缠论笔分析
    # 找最近一个完整上下上或下上下
    last_top = tops[-1] if tops else None
    last_bottom = bottoms[-1] if bottoms else None

    # 计算距离关键位
    dist_high20 = (cur_price - max(recent_h)) / max(recent_h) * 100 if max(recent_h) else 0
    dist_low20 = (cur_price - min(recent_l)) / min(recent_l) * 100 if min(recent_l) else 0
    dist_cost = (cur_price - pos['cost']) / pos['cost'] * 100

    # 支撑压力
    resistances = sorted([h for h in recent_h if h > cur_price])[:3]
    supports = sorted([l for l in recent_l if l < cur_price], reverse=True)[:3]

    # 信号判断
    signals = []
    actions = []

    # 1. 均线判断
    if m5 > m10 > m20:
        trend = '上升'
        signals.append(('均线多头', '上升趋势'))
    elif m5 < m10 < m20:
        trend = '下降'
        signals.append(('均线空头', '下降趋势'))
    else:
        trend = '震荡'
        signals.append(('均线混乱', '方向不明'))

    # 2. 乖离
    if dist_cost > 15:
        actions.append('偏离成本15%以上，注意止盈')
    elif dist_cost > 10:
        actions.append('成本乖离大，建议分批止盈')

    # 3. 压力
    if resistances and resistances[0]:
        r_near = resistances[0]
        dist_r = (r_near - cur_price) / cur_price * 100
        if dist_r < 3:
            actions.append('接近压力位 %.2f，建议观察' % r_near)

    # 4. 电力特殊判断（今日涨10%，疑似涨停）
    if rt['pct'] > 9.5:
        signals.append(('今日强势', '疑似涨停'))
        if high > 0 and abs(cur_price - high) / high < 0.5:
            actions.append('价格封住涨停板，可继续持有')
        else:
            actions.append('未封板，警惕开板，可考虑部分止盈')
    elif rt['pct'] > 5:
        signals.append(('今日大涨', '强势上涨'))

    # 5. 厦门钨业特殊
    if pos['code'] == '600549':
        if cur_price > m5 > m10:
            signals.append(('多头排列', '各周期均线向上'))
        if dist_cost < 3:
            actions.append('仍在成本附近，趋势未破，继续持有')

    return {
        'cur': cur_price,
        'prev_close': rt['prev'],
        'open': rt['open'],
        'high': rt['high'] if rt['high'] > 0 else max(recent_h),
        'low': rt['low'] if rt['low'] > 0 else min(recent_l),
        'change': rt['change'],
        'pct': rt['pct'],
        'vol': rt['vol'],
        'ma5': round(m5, 2),
        'ma10': round(m10, 2),
        'ma20': round(m20, 2),
        'ma60': round(m60, 2) if m60 else None,
        'trend': trend,
        'dist_cost': round(dist_cost, 2),
        'dist_high20': round(dist_high20, 2),
        'supports': [round(s, 2) for s in supports],
        'resistances': [round(r, 2) for r in resistances],
        'signals': signals,
        'actions': actions,
        'fenxing': {
            'total': len(fractals),
            'last_top': tops[-1] if tops else None,
            'last_bottom': bottoms[-1] if bottoms else None,
        }
    }

# === 输出 ===
print('=' * 60)
print('  持仓完整分析 - 实时行情 + 缠论结构')
print('  更新时间: %s' % datetime.now().strftime('%Y-%m-%d %H:%M'))
print('=' * 60)

for pos in positions:
    rt = realtime[pos['code']]
    res = full_analysis(pos, rt)
    profit = (res['cur'] - pos['cost']) * pos['shares']

    print()
    print('=' * 60)
    print('  %s (%s)' % (pos['name'], pos['code']))
    print('  持仓: %d股  成本: %.2f  浮盈: %+.0f (%+.2f%%)' % (
        pos['shares'], pos['cost'], profit, res['dist_cost']))
    print('-' * 60)
    print()
    print('  【实时行情】')
    print('  现价:    %.2f  (%+.2f %+.2f%%)' % (
        res['cur'], res['change'], res['pct']))
    print('  今开:    %.2f  最高: %.2f  最低: %.2f' % (
        res['open'], res['high'], res['low']))
    print('  成交量:  %d手' % res['vol'])
    print()
    print('  【均线】')
    print('  MA5:  %.2f  MA10: %.2f  MA20: %.2f' % (
        res['ma5'], res['ma10'], res['ma20']))
    if res['ma60']:
        print('  MA60: %.2f' % res['ma60'])
    print()
    print('  【关键位】')
    if res['supports']:
        print('  支撑: %s' % ' / '.join([str(s) for s in res['supports']]))
    if res['resistances']:
        print('  压力: %s' % ' / '.join([str(r) for r in res['resistances']]))
    print('  20日高点: %.2f (距今价 %+.2f%%)' % (max([float(k[2]) for k in get_kline(
        'sh.'+pos['code'] if pos['market']=='sh' else 'sz.'+pos['code'])][-20:]), res['dist_high20']))
    print()
    print('  【缠论结构】')
    print('  分型: %d个  趋势: %s' % (res['fenxing']['total'], res['trend']))
    fx = res['fenxing']
    print('  最近顶分型: %s (%.2f)' % (
        fx['last_top']['date'], fx['last_top']['high']) if fx['last_top'] else '  无顶分型')
    print('  最近底分型: %s (%.2f)' % (
        fx['last_bottom']['date'], fx['last_bottom']['low']) if fx['last_bottom'] else '  无底分型')
    print()
    print('  【信号】')
    for sig, desc in res['signals']:
        print('  %s - %s' % (sig, desc))
    print()
    print('  【操作建议】')
    if res['actions']:
        for a in res['actions']:
            print('  - %s' % a)
    else:
        print('  - 继续持有，等待信号')

bs.logout()
print()
print('=' * 60)