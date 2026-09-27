# -*- coding: utf-8 -*-
"""
advanced_scorer 使用示例
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

print('=' * 70)
print('advanced_scorer 使用示例')
print('=' * 70)
print()

# 1. 导入模块
print('[1/5] 导入模块...')
print()

from src.ai.advanced_scorer import StockScorer
from src.ai.simple_scorer import SimpleStockScorer
from src.strategies.multi_strategies import MultiStrategyFactory
from src.signals.signal_generator import SignalGenerator

print('[OK] 导入模块')
print()

# 2. 准备数据
print('[2/5] 准备数据...')
print()

dates = pd.date_range('2024-01-01', periods=120, freq='D')
dates = dates[dates.weekday < 5]

np.random.seed(42)
base_price = 10
returns = np.random.normal(0.0005, 0.02, len(dates))
close = base_price * (1 + returns).cumprod()

df = pd.DataFrame({
    'open': close * (1 + np.random.uniform(-0.01, 0.01, len(close))),
    'high': close * (1 + np.random.uniform(0, 0.02, len(close))),
    'low': close * (1 - np.random.uniform(0, 0.02, len(close))),
    'close': close,
    'volume': np.random.uniform(1000000, 5000000, len(close)),
    'amount': np.random.uniform(10000000, 50000000, len(close))
}, index=dates)

quote = {
    'code': '000001.SZ',
    'price': df['close'].iloc[-1],
    'change': df['close'].pct_change().iloc[-1] * 100,
    'volume': df['volume'].iloc[-1],
    'amount': df['amount'].iloc[-1]
}

print('[OK] 生成数据')
print('     股票：000001.SZ')
print('     价格:', round(quote['price'], 2))
print('     涨跌:', round(quote['change'], 2), '%')
print()

# 3. advanced_scorer 评分
print('[3/5] advanced_scorer 评分...')
print()

scorer = StockScorer()
score = scorer.calculate_score(quote, df, sector='金融')

print('[OK] 评分完成')
print()
print('===== 评分结果 =====')
print()
print('综合得分:', round(score['total_score'], 1))
print('消息面加分:', round(score['news_bonus'], 1))
print()
print('技术面:')
print('  趋势分:', round(score['trend_score'], 1))
print('  动量分:', round(score['momentum_score'], 1))
print('  成交量分:', round(score['volume_score'], 1))
print('  MACD 分:', score['macd_score'])
print('  RSI 分:', round(score['rsi_score'], 1))
print('  布林带分:', score['boll_score'])
print('  位置分:', score['position_score'], '(' + score['position_level'] + ')')
print('  板块分:', score['sector_score'])
print('  相对强弱:', round(score['rs_score'], 1))
print()

# 评级
total = score['total_score']
if total >= 70:
    rating = '强烈推荐'
elif total >= 60:
    rating = '推荐'
elif total >= 50:
    rating = '中性'
elif total >= 40:
    rating = '谨慎'
else:
    rating = '不推荐'

print('综合评级:', rating)
print()

# 4. 对比简化版
print('[4/5] 对比简化版...')
print()

simple_scorer = SimpleStockScorer()
simple_score = simple_scorer.score_stock('000001.SZ', df)

print('评分对比:')
print('  advanced:', round(score['total_score'], 1), '分')
print('  simple:  ', round(simple_score['total'], 1), '分 (' + simple_score['rating'] + ')')

diff = abs(score['total_score'] - simple_score['total'])
print('  差异:', round(diff, 1), '分')
print()

# 5. 策略整合
print('[5/5] 策略整合...')
print()

factory = MultiStrategyFactory()
generator = SignalGenerator({})
signals = generator.generate_all_signals(df)
strategy = factory.create_strategy('trend', '趋势跟踪 v1')

print('综合决策:')
print('  advanced 评分:', round(score['total_score'], 1))
print('  趋势信号:', signals.get('trend', {}).get('trend', 'N/A'))
print('  入场条件:', strategy.check_entry_condition(signals))
print()

if score['total_score'] >= 60 and strategy.check_entry_condition(signals):
    print('  决策：可以入场')
    print('  理由：评分>=60 且策略信号确认')
elif score['total_score'] >= 50:
    print('  决策：观望')
    print('  理由：评分中性，等待明确信号')
else:
    print('  决策：不推荐')
    print('  理由：评分<50，风险较高')

print()
print('=' * 70)
print('使用完成!')
print('=' * 70)
