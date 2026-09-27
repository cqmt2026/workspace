# -*- coding: utf-8 -*-
"""
模拟交易系统 V4.0 - 多周期缠论分析（完整版）
日线判断方向 + 60分钟找买点 + 15分钟精确入场
使用新浪财经分钟数据
"""
import urllib.request
import json
import pandas as pd
from datetime import datetime, timedelta
import os

# ========== 数据获取 ==========

def get_kline(code, market, days=500):
    """获取日K线"""
    try:
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayhfq&param={market}{code},day,,,{days},qfq'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('utf-8')
        kdata = json.loads(data.replace('kline_dayhfq=', ''))
        raw = kdata.get('data', {}).get(f'{market}{code}', {}).get('qfqday', [])
        rows = []
        for row in raw:
            if len(row) >= 5:
                rows.append({'date': row[0], 'open': float(row[1]), 'close': float(row[2]),
                             'high': float(row[3]), 'low': float(row[4])})
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

def get_sina_minute(code, market, period='60'):
    """获取新浪财经分钟K线"""
    try:
        url = f'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={market.upper()}{code}&scale={period}&ma=5&datalen=500'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('utf-8')
        kdata = json.loads(data)
        rows = []
        for row in kdata:
            rows.append({'date': row['day'], 'open': float(row['open']), 'close': float(row['close']),
                         'high': float(row['high']), 'low': float(row['low'])})
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

def get_60min(code, market):
    return get_sina_minute(code, market, '60')

def get_15min(code, market):
    return get_sina_minute(code, market, '15')

def calc_indicators(df):
    if len(df) == 0 or 'close' not in df.columns:
        return df
    df = df.copy()
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['dif'] = df['ema12'] - df['ema26']
    df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
    low9 = df['low'].rolling(9, min_periods=1).min()
    high9 = df['high'].rolling(9, min_periods=1).max()
    rsv = (df['close'] - low9) / (high9 - low9) * 100
    df['k'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['d'] = df['k'].ewm(alpha=1/3, adjust=False).mean()
    df['ma5'] = df['close'].rolling(5, min_periods=1).mean()
    df['ma10'] = df['close'].rolling(10, min_periods=1).mean()
    df['ma20'] = df['close'].rolling(20, min_periods=1).mean()
    return df

# ========== 缠论分析 ==========

def find_fractals(df, n=3):
    fractals = []
    for i in range(n-1, len(df) - n + 1):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        next_k = df.iloc[i+1]
        if curr['high'] > prev['high'] and curr['high'] > next_k['high']:
            fractals.append({'idx': i, 'date': curr['date'], 'type': 'top', 'price': curr['high']})
        elif curr['low'] < prev['low'] and curr['low'] < next_k['low']:
            fractals.append({'idx': i, 'date': curr['date'], 'type': 'bottom', 'price': curr['low']})
    return fractals

def analyze_period(df):
    if len(df) == 0 or 'date' not in df.columns:
        return {'signal': 'unknown', 'last_frac': None, 'trend': 'unknown'}
    
    fractals = find_fractals(df)
    
    if len(fractals) < 2:
        return {'signal': 'unknown', 'last_frac': None, 'trend': 'unknown'}
    
    last = fractals[-1]
    prev = fractals[-2]
    
    signal = '买入机会' if last['type'] == 'bottom' else '观望'
    
    trend = '震荡'
    if last['type'] == 'bottom' and prev['type'] == 'bottom':
        trend = '上升' if last['price'] > prev['price'] else '下降'
    elif last['type'] == 'top' and prev['type'] == 'top':
        trend = '上升' if last['price'] > prev['price'] else '下降'
    
    return {
        'signal': signal,
        'last_frac': f"{last['type']}@{last['price']:.2f}",
        'last_frac_type': last['type'],
        'trend': trend
    }

def check_conditions(row):
    if row is None or len(row) == 0:
        return {'macd': False, 'ma5': False, 'kdj': False, 'duo': False}
    return {
        'macd': row['dif'] > 0 and row['dea'] > 0,
        'ma5': row['close'] > row['ma5'],
        'kdj': row['k'] < 80,
        'duo': row['ma5'] > row['ma10'] > row['ma20']
    }

# ========== 多周期分析 ==========

def multi_period_analysis(code, market):
    """多周期缠论分析"""
    result = {'daily': {}, '60min': {}, '15min': {}, 'summary': {}, 'can_buy': False, 'buy_level': 'none'}
    
    # 日线
    df_day = get_kline(code, market, 100)
    df_day = calc_indicators(df_day)
    
    if len(df_day) > 0:
        result['daily'] = analyze_period(df_day)
        row = df_day.iloc[-1]
        c = check_conditions(row)
        result['daily'].update({'price': row['close'], 'macd': c['macd'], 'ma5': c['ma5'], 'kdj': c['kdj'], 'duo': c['duo'], 'dif': row['dif'], 'k': row['k']})
    
    # 60分钟
    df_60 = get_60min(code, market)
    df_60 = calc_indicators(df_60)
    
    if len(df_60) > 0:
        result['60min'] = analyze_period(df_60)
        row = df_60.iloc[-1]
        c = check_conditions(row)
        result['60min'].update({'price': row['close'], 'macd': c['macd'], 'ma5': c['ma5'], 'kdj': c['kdj']})
    
    # 15分钟
    df_15 = get_15min(code, market)
    df_15 = calc_indicators(df_15)
    
    if len(df_15) > 0:
        result['15min'] = analyze_period(df_15)
        row = df_15.iloc[-1]
        c = check_conditions(row)
        result['15min'].update({'price': row['close'], 'macd': c['macd'], 'ma5': c['ma5'], 'kdj': c['kdj']})
    
    # 综合判断
    daily_ok = result['daily'].get('signal') == '买入机会'
    min60_ok = result['60min'].get('signal') == '买入机会'
    min15_ok = result['15min'].get('signal') == '买入机会'
    
    qizhong = sum([result['daily'].get('macd', False), result['daily'].get('ma5', False), result['daily'].get('kdj', False)])
    
    result['summary'] = {
        'daily_signal': result['daily'].get('signal', '?'),
        'daily_trend': result['daily'].get('trend', '?'),
        '60min_signal': result['60min'].get('signal', '?'),
        '15min_signal': result['15min'].get('signal', '?'),
        'qizhong': qizhong
    }
    
    if daily_ok and qizhong >= 2:
        if min15_ok:
            result['can_buy'] = True
            result['buy_level'] = '精确买入(15分)'
        elif min60_ok:
            result['can_buy'] = True
            result['buy_level'] = '60分买入'
        else:
            result['can_buy'] = True
            result['buy_level'] = '日线买入'
    else:
        result['buy_level'] = '不符合条件'
    
    return result

def print_result(result, stock):
    d = result['daily']
    m60 = result['60min']
    m15 = result['15min']
    s = result['summary']
    
    print(f'\n{'='*60}')
    print(f'股票: {stock}')
    print('='*60)
    
    print(f'\n日线:')
    print(f'  信号: {d.get("signal", "?")} | 趋势: {d.get("trend", "?")} | 分型: {d.get("last_frac", "?")}')
    print(f'  价格: {d.get("price", 0):.2f}')
    if 'macd' in d:
        print(f'  七重: MACD={"✅" if d["macd"] else "❌"} MA5={"✅" if d["ma5"] else "❌"} KDJ={"✅" if d["kdj"] else "❌"} ({s["qizhong"]}/3)')
        print(f'  多头: {"✅" if d.get("duo") else "❌"}')
    
    print(f'\n60分钟:')
    print(f'  信号: {m60.get("signal", "?")} | 分型: {m60.get("last_frac", "?")}')
    if 'price' in m60:
        print(f'  价格: {m60["price"]:.2f}')
    
    print(f'\n15分钟:')
    print(f'  信号: {m15.get("signal", "?")} | 分型: {m15.get("last_frac", "?")}')
    if 'price' in m15:
        print(f'  价格: {m15["price"]:.2f}')
    
    print(f'\n结论: {result["buy_level"]}')
    print(f'{"✅ 可以买入" if result["can_buy"] else "❌ 不宜买入"}')

def main():
    print('='*60)
    print('【模拟交易系统 V4.0 - 多周期缠论分析】')
    print('数据源: 日线=腾讯财经 | 60分钟/15分钟=新浪财经')
    print('='*60)
    
    # 测试持仓
    test_stocks = [('600549', 'sh'), ('600763', 'sh')]
    
    print('\n【持仓股票分析】')
    for stock, market in test_stocks:
        result = multi_period_analysis(stock, market)
        print_result(result, stock)
    
    # 市场机会
    print('\n\n【市场机会扫描】')
    watchlist = [('600276', 'sh'), ('600519', 'sh'), ('000001', 'sh')]
    
    opportunities = []
    for stock, market in watchlist:
        result = multi_period_analysis(stock, market)
        if result['can_buy'] and result['summary']['qizhong'] >= 2:
            opportunities.append((stock, result))
            print(f'\n✅ 买入机会: {stock} | {result["buy_level"]}')
            print(f'   日线: {result["daily"].get("signal")} | 60分: {result["60min"].get("signal")} | 15分: {result["15min"].get("signal")}')
        else:
            print(f'\n❌ {stock}: {result["buy_level"]}')
    
    # 保存报告
    output_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\src\data\reports'
    os.makedirs(output_dir, exist_ok=True)
    report_file = os.path.join(output_dir, 'multi_period_v4_2026-04-24.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('# 多周期缠论分析报告 V4.0\n\n')
        f.write('**日期**: 2026-04-24\n\n')
        f.write('## 数据源\n')
        f.write('- 日线: 腾讯财经\n')
        f.write('- 60分钟/15分钟: 新浪财经\n\n')
        f.write(f'## 机会: {len(opportunities)}个\n')
    
    print(f'\n报告已保存: {report_file}')

if __name__ == '__main__':
    main()