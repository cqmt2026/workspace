# -*- coding: utf-8 -*-
"""策略参数优化 - 网格搜索最优参数"""
import requests, json, math, os
from itertools import product

# 尾盘策略参数空间
PARAM_SPACE = {
    'price_min': [3, 4, 5],         # 股价下限
    'price_max': [100, 150, 200],   # 股价上限
    'chg_min': [0.5, 1.0, 1.5],     # 涨幅下限%
    'chg_max': [5.0, 6.5, 8.0],     # 涨幅上限%
    'vol_ratio_min': [1.0, 1.05],  # 量比下限
    'vol_ratio_max': [1.5, 1.8, 2.0],  # 量比上限
    'match_thresh': [3, 4],         # 满足条件数
}

def get_kline_full(code, market):
    """获取完整日K线"""
    secid = f'{market}.{code}'
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&ut=fa5fd1943c7b386f172d6893dbfba10b&klt=101&fqt=1&secid={secid}&beg=0&end=20500101'
    try:
        r = requests.get(url, timeout=10)
        d = r.json()
        if d.get('data') and d['data'].get('klines'):
            klines = []
            for kl in d['data']['klines']:
                p = kl.split(',')
                klines.append({
                    'date': p[0], 'open': float(p[1]), 'high': float(p[2]),
                    'low': float(p[3]), 'close': float(p[4]), 'vol': float(p[5])
                })
            return klines
    except:
        pass
    return None

def simulate_trade(klines, params):
    """模拟交易"""
    if not klines or len(klines) < 20:
        return None
    
    trades = []
    for i in range(5, len(klines)-1):
        today = klines[i]
        tomorrow = klines[i+1]
        
        price = today['close']
        chg_pct = (today['close'] - today['open']) / today['open'] * 100
        vol_ratio = 1.0  # simplified
        
        # 简化条件检查
        c1 = params['price_min'] <= price <= params['price_max']
        c2 = params['chg_min'] <= chg_pct <= params['chg_max']
        c3 = params['vol_ratio_min'] <= vol_ratio <= params['vol_ratio_max']
        
        # 简化均线多头(MA5>MA10)
        if i >= 10:
            ma5 = sum(k['close'] for k in klines[i-5:i]) / 5
            ma10 = sum(k['close'] for k in klines[i-10:i]) / 10
            c4 = ma5 > ma10
        else:
            c4 = False
        
        match_count = sum([c1, c2, c3, c4])
        
        if match_count >= params['match_thresh']:
            # 买入 tomorrow 开盘价
            buy_price = tomorrow['open']
            # 持有N天后卖出(简化:持有1天)
            if i+2 < len(klines):
                sell_price = klines[i+2]['close']
                profit_pct = (sell_price - buy_price) / buy_price * 100
                trades.append(profit_pct)
    
    if not trades:
        return {'count': 0, 'win_rate': 0, 'avg_profit': 0}
    
    win_count = sum(1 for p in trades if p > 0)
    return {
        'count': len(trades),
        'win_rate': win_count / len(trades) * 100,
        'avg_profit': sum(trades) / len(trades),
        'total_profit': sum(trades),
        'max_profit': max(trades),
        'max_loss': min(trades),
    }

def optimize_params(sample_codes=[('000001', 0), ('600036', 1), ('600519', 1)]):
    """网格搜索最优参数"""
    print('开始策略参数优化...')
    print('加载K线数据...')
    
    all_klines = {}
    for code, mkt in sample_codes:
        kl = get_kline_full(code, mkt)
        if kl:
            all_klines[(code, mkt)] = kl
            print(f'  {code}: {len(kl)}条K线')
    
    if len(all_klines) < 2:
        return {'error': '数据不足'}
    
    # 生成参数组合
    keys = list(PARAM_SPACE.keys())
    values = list(PARAM_SPACE.values())
    combinations = list(product(*values))
    
    print(f'共{len(combinations)}种参数组合')
    best_result = None
    best_params = None
    
    for i, combo in enumerate(combinations[:50]):  # 限制前50个组合
        params = dict(zip(keys, combo))
        
        all_results = []
        for (code, mkt), klines in all_klines.items():
            result = simulate_trade(klines, params)
            if result and result['count'] >= 5:  # 至少5笔交易
                all_results.append(result)
        
        if not all_results:
            continue
        
        # 汇总
        total_trades = sum(r['count'] for r in all_results)
        avg_win_rate = sum(r['win_rate'] for r in all_results) / len(all_results)
        avg_profit = sum(r['avg_profit'] for r in all_results) / len(all_results)
        
        # 综合评分: 考虑胜率 + 收益 + 交易次数
        score = avg_win_rate * 0.4 + avg_profit * 10 * 0.3 + min(total_trades/100, 1) * 0.3
        
        if best_result is None or score > best_result:
            best_result = score
            best_params = params
            best_stats = {
                'win_rate': round(avg_win_rate, 1),
                'avg_profit': round(avg_profit, 3),
                'total_trades': total_trades,
                'score': round(score, 2)
            }
        
        if (i+1) % 10 == 0:
            print(f'  进度: {i+1}/{min(50, len(combinations))}')
    
    return {
        'best_params': best_params,
        'best_stats': best_stats,
        'tested': min(50, len(combinations))
    }

if __name__ == '__main__':
    print('='*60)
    print('策略参数优化 - 网格搜索')
    print('='*60)
    
    result = optimize_params()
    if 'error' in result:
        print(f'错误: {result["error"]}')
    else:
        print(f'\n最优参数: {result["best_params"]}')
        print(f'测试统计: {result["best_stats"]}')
        print(f'综合评分: {result["best_stats"]["score"]}')