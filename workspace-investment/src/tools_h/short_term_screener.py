#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Short-term Stock Screener v8.0
短线选股工具 - 游资风格
标准：市值 50-300 亿、成交>3 亿、振幅>5%、涨停频率 2-3 次/月
"""

import baostock as bs
import json
from datetime import datetime, timedelta
from pathlib import Path

def get_stock_data(code, days=60):
    """获取股票数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    rs = bs.query_history_k_data_plus(
        code,
        'date,open,high,low,close,volume,amount',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    data = []
    while rs.error_msg == 'success' and rs.next():
        row = rs.get_row_data()
        if row[5]:  # 成交量不为空
            data.append({
                'date': row[0],
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': int(float(row[5])),
                'amount': float(row[6]),
            })
    
    return data

def calculate_metrics(data):
    """计算选股指标"""
    if len(data) < 20:
        return None
    
    # 市值估算（用最新收盘价*总股本，简化处理）
    latest = data[-1]
    
    # 日均成交（亿）
    avg_amount = sum(d['amount'] for d in data[-20:]) / 20 / 100000000
    
    # 日均振幅
    avg_amplitude = 0
    for d in data[-20:]:
        amplitude = (d['high'] - d['low']) / d['low'] * 100
        avg_amplitude += amplitude
    avg_amplitude /= 20
    
    # 涨停频率（简化：涨幅>9.5% 算涨停）
    limit_up_count = 0
    for d in data[-20:]:
        change = (d['close'] - d['open']) / d['open'] * 100
        if change > 9.5:
            limit_up_count += 1
    
    # 技术面（均线多头）
    closes = [d['close'] for d in data]
    ma5 = sum(closes[-5:]) / 5
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20
    
    trend_score = 0
    if closes[-1] > ma5: trend_score += 1
    if ma5 > ma10: trend_score += 1
    if ma10 > ma20: trend_score += 1
    
    return {
        'avg_amount': round(avg_amount, 2),
        'avg_amplitude': round(avg_amplitude, 2),
        'limit_up_count': limit_up_count,
        'trend_score': trend_score,
        'current_price': closes[-1],
        'ma5': round(ma5, 2),
        'ma10': round(ma10, 2),
        'ma20': round(ma20, 2),
    }

def check_criteria(metrics, market_cap):
    """检查是否符合标准"""
    if not metrics:
        return False, []
    
    reasons = []
    
    # 市值 50-300 亿
    if market_cap < 50 or market_cap > 300:
        reasons.append(f'市值{market_cap}亿 不符合 50-300 亿')
    
    # 日均成交>3 亿
    if metrics['avg_amount'] < 3:
        reasons.append(f'日均成交{metrics["avg_amount"]}亿 <3 亿')
    
    # 日均振幅>5%
    if metrics['avg_amplitude'] < 5:
        reasons.append(f'日均振幅{metrics["avg_amplitude"]}% <5%')
    
    # 涨停频率 1-5 次（放宽到 1-5 次）
    if metrics['limit_up_count'] < 1 or metrics['limit_up_count'] > 5:
        reasons.append(f'涨停{metrics["limit_up_count"]}次 不符合 1-5 次')
    
    # 技术面（至少 2 分）
    if metrics['trend_score'] < 2:
        reasons.append(f'趋势得分{metrics["trend_score"]} <2')
    
    return len(reasons) == 0, reasons

def screen_stocks():
    """筛选股票"""
    print("=" * 80)
    print("短线选股工具 v8.0 - 游资风格")
    print("=" * 80)
    print()
    print("选股标准:")
    print("  市值：50-300 亿")
    print("  日均成交：>3 亿")
    print("  日均振幅：>5%")
    print("  涨停频率：1-5 次/月")
    print("  技术面：均线多头")
    print()
    
    # 登录
    lg = bs.login()
    print(f"登录：{lg.error_msg}")
    print()
    
    # 测试股票池（小市值 + 活跃）
    test_stocks = [
        # 科技
        ('sz.002230', '科大讯飞', 150),
        ('sz.000977', '浪潮信息', 180),
        ('sz.002415', '海康威视', 200),
        ('sz.002371', '北方华创', 220),
        ('sz.002152', '广电运通', 80),
        
        # 新能源
        ('sz.002709', '天赐材料', 120),
        ('sz.002812', '恩捷股份', 150),
        ('sz.300014', '亿纬锂能', 180),
        ('sz.002460', '赣锋锂业', 200),
        ('sz.002340', '格林美', 100),
        
        # 医药
        ('sz.000538', '云南白药', 180),
        ('sh.600436', '片仔癀', 200),
        ('sz.300122', '智飞生物', 150),
        ('sh.600079', '人福医药', 80),
        ('sz.000963', '华东医药', 120),
        
        # 消费
        ('sz.002714', '牧原股份', 280),
        ('sz.000895', '双汇发展', 150),
        ('sz.002304', '洋河股份', 180),
        ('sh.600779', '水井坊', 80),
        ('sz.000799', '酒鬼酒', 100),
        
        # 金融
        ('sz.000001', '平安银行', 250),
        ('sh.600030', '中信证券', 280),
        ('sh.601688', '华泰证券', 200),
        
        # 周期
        ('sh.600547', '山东黄金', 150),
        ('sh.601899', '紫金矿业', 280),
        ('sh.600489', '中金黄金', 100),
        ('sh.600019', '宝钢股份', 180),
        
        # 其他活跃股
        ('sz.002594', '比亚迪', 280),
        ('sh.601127', '赛力斯', 180),
        ('sz.002475', '立讯精密', 200),
        ('sz.002236', '大华股份', 120),
        ('sz.002439', '启明星辰', 80),
    ]
    
    print(f"筛选股票池：{len(test_stocks)} 只")
    print()
    
    results = []
    passed = []
    
    for code, name, market_cap in test_stocks:
        data = get_stock_data(code)
        if len(data) < 20:
            continue
        
        metrics = calculate_metrics(data)
        if not metrics:
            continue
        
        is_pass, reasons = check_criteria(metrics, market_cap)
        
        result = {
            'code': code,
            'name': name,
            'market_cap': market_cap,
            'metrics': metrics,
            'pass': is_pass,
            'reasons': reasons,
        }
        results.append(result)
        
        if is_pass:
            passed.append(result)
            print(f"✅ {code} {name}: 市值{market_cap}亿 成交{metrics['avg_amount']}亿 振幅{metrics['avg_amplitude']}% 涨停{metrics['limit_up_count']}次 趋势{metrics['trend_score']}分")
        else:
            print(f"❌ {code} {name}: {', '.join(reasons)}")
    
    print()
    print("=" * 80)
    print(f"筛选结果：{len(passed)}/{len(results)} 只通过")
    print("=" * 80)
    
    if passed:
        print()
        print("✅ 符合短线选股标准:")
        for r in passed:
            m = r['metrics']
            print(f"  {r['code']} {r['name']}: 市值{r['market_cap']}亿 成交{m['avg_amount']}亿 振幅{m['avg_amplitude']}% 涨停{m['limit_up_count']}次")
    
    # 保存到文件
    pool_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'criteria': {
            'market_cap': '50-300 亿',
            'avg_amount': '>3 亿',
            'avg_amplitude': '>5%',
            'limit_up_count': '1-5 次/月',
            'trend_score': '>=2',
        },
        'total': len(results),
        'passed': len(passed),
        'stocks': passed,
    }
    
    with open('short_term_pool.json', 'w', encoding='utf-8') as f:
        json.dump(pool_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到 short_term_pool.json")
    
    bs.logout()
    return passed

if __name__ == '__main__':
    try:
        screen_stocks()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
