#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六维选股工具 v7.0
功能：自动计算六维评分，筛选高胜率股票
六维：政策 + 题材 + 情绪 + 量价 + 技术 (缠论) + 周期
"""

import baostock as bs
import sys
import io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ==================== 1. 数据获取 ====================

def get_stock_data(code, start_date='2025-01-01', end_date='2026-03-08'):
    """获取股票 K 线数据"""
    rs = bs.query_history_k_data_plus(
        code,
        'date,open,high,low,close,volume,amount',
        start_date=start_date,
        end_date=end_date
    )
    
    data = []
    while rs.error_msg == 'success' and rs.next():
        row = rs.get_row_data()
        # 跳过无效数据
        if not row[5] or not row[6]:
            continue
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

# ==================== 2. 六维评分系统 ====================

def score_policy(code, name, sector=None):
    """
    政策维评分（20 分）
    
    优化版：支持板块参数
    """
    policy_support = {
        'AI': 20, '人工智能': 20, '芯片': 18, '半导体': 18, '算力': 19,
        '新能源': 16, '光伏': 16, '风电': 16, '锂电池': 16,
        '医药': 14, '创新药': 14, '医疗器械': 14,
        '券商': 12, '银行': 10, '保险': 10,
        '房地产': 6, '基建': 8, '建材': 8,
        '消费': 12, '白酒': 12, '家电': 10,
        '军工': 14, '航天': 14,
        '农业': 10, '养殖': 10,
    }
    
    # 优先使用板块信息
    if sector:
        for keyword, score in policy_support.items():
            if keyword in sector:
                return score
    
    # 从股票名匹配
    for keyword, score in policy_support.items():
        if keyword in name:
            return score
    
    return 10  # 默认分

def score_topic(code, name, sector=None):
    """
    题材维评分（15 分）
    
    优化版：支持板块参数
    """
    hot_topics = {
        'AI': 15, '人工智能': 15, '算力': 14, '大模型': 14, 'CPO': 14,
        '芯片': 13, '半导体': 13, '光刻机': 13, '先进封装': 13,
        '新能源': 12, '锂电池': 12, '固态电池': 12, '光伏': 12,
        '机器人': 11, '无人机': 11, '自动驾驶': 11,
        '医药': 10, '疫苗': 10, '创新药': 10,
        '低空经济': 13, '商业航天': 12,
        '华为': 13, '小米': 11, '苹果': 11,
    }
    
    if sector:
        for keyword, score in hot_topics.items():
            if keyword in sector:
                return score
    
    for keyword, score in hot_topics.items():
        if keyword in name:
            return score
    
    return 7  # 默认分

def score_sentiment(data, market_sentiment=None):
    """
    情绪维评分（15 分）
    
    优化版：使用市场情绪数据
    """
    if market_sentiment:
        # 使用真实情绪数据
        from sentiment_tool import sentiment_to_score
        return sentiment_to_score(market_sentiment['stage'])
    
    # 降级方案：用 5 日涨幅估算
    if len(data) < 20:
        return 7
    
    closes = [d['close'] for d in data]
    change_5d = ((closes[-1] / closes[-5]) - 1) * 100 if len(closes) >= 5 else 0
    
    if change_5d > 15:
        return 7   # 高潮期（减仓）
    elif change_5d > 5:
        return 10  # 发酵期
    elif change_5d > 0:
        return 13  # 启动期（最佳）
    elif change_5d > -5:
        return 7   # 震荡
    else:
        return 4   # 衰退期

def score_volume_price(data):
    """
    量价维评分（15 分）
    根据量价关系判断
    """
    if len(data) < 10:
        return 7
    
    closes = [d['close'] for d in data]
    volumes = [d['volume'] for d in data]
    
    # 今日涨跌
    today_change = ((closes[-1] / closes[-2]) - 1) * 100 if len(closes) >= 2 else 0
    
    # 量比
    avg_vol_5 = sum(volumes[-5:]) / 5
    vol_ratio = volumes[-1] / avg_vol_5 if avg_vol_5 > 0 else 1
    
    # 量价评分
    if today_change > 3 and vol_ratio > 1.5:
        return 14  # 放量上涨
    elif today_change > 0 and vol_ratio > 1.0:
        return 12  # 温和放量上涨
    elif today_change > 0 and vol_ratio < 1.0:
        return 9   # 缩量上涨
    elif today_change < 0 and vol_ratio < 1.0:
        return 7   # 缩量下跌
    elif today_change < 0 and vol_ratio > 1.5:
        return 4   # 放量下跌
    else:
        return 7   # 其他

def score_technical(data, code=None):
    """
    技术维评分（25 分）
    
    优化版：整合缠论分析
    """
    # 尝试使用缠论分析（如果可用）
    if code:
        try:
            from chan_analysis import analyze_chan_full
            result = analyze_chan_full(code, '', start_date='2025-01-01', end_date='2026-03-08')
            if result and result.get('last_segment'):
                seg_type = result['last_segment']['type']
                if seg_type == 'up':
                    return 22  # 缠论向上线段
                else:
                    return 15  # 缠论向下线段
        except:
            pass  # 缠论分析失败，降级到均线
    
    # 降级方案：均线系统
    if len(data) < 20:
        return 10
    
    closes = [d['close'] for d in data]
    ma5 = sum(closes[-5:]) / 5
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20
    current = closes[-1]
    
    if current > ma5 > ma10 > ma20:
        return 22
    elif current > ma5 > ma10:
        return 18
    elif current > ma5:
        return 15
    elif current > ma10:
        return 12
    elif current > ma20:
        return 10
    else:
        return 6

def score_cycle(data):
    """
    周期维评分（10 分）
    多周期共振评分
    """
    if len(data) < 60:
        return 5
    
    closes = [d['close'] for d in data]
    
    # 日线趋势
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    daily_trend = 1 if closes[-1] > ma5 > ma20 else 0
    
    # 周线趋势（简化：用 20 日线代替）
    weekly_trend = 1 if ma5 > ma20 else 0
    
    # 月线趋势（简化：用 60 日线代替）
    if len(closes) >= 60:
        ma60 = sum(closes[-60:]) / 60
        monthly_trend = 1 if closes[-1] > ma60 else 0
    else:
        monthly_trend = 0
    
    # 周期评分
    if monthly_trend and weekly_trend and daily_trend:
        return 10  # 三线共振
    elif weekly_trend and daily_trend:
        return 7   # 周线 + 日线
    elif daily_trend:
        return 4   # 仅日线
    else:
        return 2   # 无共振

# ==================== 3. 综合评分 ====================

def calculate_total_score(code, name, data):
    """计算六维综合评分"""
    scores = {
        'policy': score_policy(code, name),
        'topic': score_topic(code, name),
        'sentiment': score_sentiment(data),
        'volume_price': score_volume_price(data),
        'technical': score_technical(data),
        'cycle': score_cycle(data),
    }
    
    total = sum(scores.values())
    
    return {
        'code': code,
        'name': name,
        'scores': scores,
        'total': total,
        'level': get_level(total),
    }

def get_level(total):
    """根据总分确定等级"""
    if total > 85:
        return '黄金买点'
    elif total > 70:
        return '白银买点'
    elif total > 55:
        return '青铜买点'
    else:
        return '观望'

# ==================== 4. 主程序 ====================

def select_stocks():
    """执行六维选股"""
    print("=" * 80)
    print("六维选股工具 v7.0")
    print("=" * 80)
    print(f"筛选日期：{datetime.now().strftime('%Y-%m-%d')}")
    print(f"六维：政策 + 题材 + 情绪 + 量价 + 技术 + 周期")
    print()
    
    # 登录
    lg = bs.login()
    print(f"登录：{lg.error_msg}")
    
    # 测试股票池（各板块代表性股票）
    test_stocks = [
        # AI/科技
        ('sh.601138', '工业富联'),
        ('sh.688981', '中芯国际'),
        ('sz.002230', '科大讯飞'),
        ('sz.000977', '浪潮信息'),
        ('sh.603019', '中科曙光'),
        ('sh.688111', '金山办公'),
        
        # 新能源
        ('sz.300750', '宁德时代'),
        ('sz.002594', '比亚迪'),
        ('sh.601012', '隆基绿能'),
        ('sh.601127', '赛力斯'),
        
        # 消费
        ('sh.600519', '贵州茅台'),
        ('sz.000858', '五粮液'),
        ('sh.600276', '恒瑞医药'),
        ('sz.002714', '牧原股份'),
        
        # 金融
        ('sh.600036', '招商银行'),
        ('sh.601318', '中国平安'),
        ('sz.000001', '平安银行'),
        ('sh.600030', '中信证券'),
        
        # 其他
        ('sz.002415', '海康威视'),
        ('sz.002475', '立讯精密'),
        ('sz.000333', '美的集团'),
        ('sh.600900', '长江电力'),
    ]
    
    print(f"\n筛选股票池：{len(test_stocks)} 只")
    print()
    
    results = []
    
    for code, name in test_stocks:
        # 获取数据
        data = get_stock_data(code)
        
        if len(data) < 20:
            continue
        
        # 计算评分
        result = calculate_total_score(code, name, data)
        results.append(result)
        
        # 打印结果
        level_tag = '🥇' if result['level'] == '黄金买点' else '🥈' if result['level'] == '白银买点' else '🥉' if result['level'] == '青铜买点' else '❌'
        print(f"{level_tag} {code} {name}: {result['total']}分 ({result['level']})")
        print(f"   政策:{result['scores']['policy']:>2} 题材:{result['scores']['topic']:>2} 情绪:{result['scores']['sentiment']:>2} 量价:{result['scores']['volume_price']:>2} 技术:{result['scores']['technical']:>2} 周期:{result['scores']['cycle']:>2}")
    
    # 排序
    results.sort(key=lambda x: x['total'], reverse=True)
    
    # 总结
    print(f"\n{'='*80}")
    print("筛选结果:")
    print(f"{'='*80}")
    
    golden = [r for r in results if r['level'] == '黄金买点']
    silver = [r for r in results if r['level'] == '白银买点']
    bronze = [r for r in results if r['level'] == '青铜买点']
    
    print(f"黄金买点：{len(golden)} 只")
    print(f"白银买点：{len(silver)} 只")
    print(f"青铜买点：{len(bronze)} 只")
    print(f"观望：{len(results) - len(golden) - len(silver) - len(bronze)} 只")
    
    if golden:
        print(f"\n🥇 黄金买点股票:")
        for r in golden[:5]:
            print(f"  {r['code']} {r['name']}: {r['total']}分")
    
    if silver:
        print(f"\n🥈 白银买点股票:")
        for r in silver[:5]:
            print(f"  {r['code']} {r['name']}: {r['total']}分")
    
    bs.logout()
    
    return results

if __name__ == '__main__':
    results = select_stocks()
