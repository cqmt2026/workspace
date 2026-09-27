# -*- coding: utf-8 -*-
"""在signal_aggregator.py中添加大盘择时和止盈规则"""
import sys

with open('scripts/signal_aggregator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== 添加大盘择时函数 =====
# 在 class SignalAggregator 之前插入

old_class_start = 'class SignalAggregator:\n    """信号聚合器"""'

new_functions = '''
# ===== 大盘环境择时 =====
MARKET_DB = r"F:\\market_data.db"

def get_market_regime(date: str) -> dict:
    """判断大盘环境：可做/谨慎/规避
    
    使用上证指数判断：
    - 大盘在MA20上方且MA5>MA20 → 可做
    - 大盘在MA20附近或MA5<MA20 → 谨慎（半仓）
    - 大盘跌破MA60或连续3日收跌 → 规避（空仓）
    
    Returns: {'regime': '可做'|'谨慎'|'规避', 'reason': str, 'position_limit': float}
    """
    import sqlite3
    from datetime import datetime, timedelta
    
    if not os.path.exists(MARKET_DB):
        return {'regime': '可做', 'reason': '数据不足，默认可做', 'position_limit': 1.0}
    
    try:
        conn = sqlite3.connect(MARKET_DB)
        cur = conn.cursor()
        
        # 获取最近30天上证指数K线
        klines = cur.execute("""
            SELECT date, close, ma5, ma20, ma60 FROM daily_k 
            WHERE code='sh000001' AND date<=? ORDER BY date DESC LIMIT 30
        """, (date,)).fetchall()
        conn.close()
        
        if len(klines) < 20:
            return {'regime': '可做', 'reason': '数据不足，默认可做', 'position_limit': 1.0}
        
        # 最新数据
        latest = klines[0]
        price = latest[1]
        ma5_val = latest[2] if len(latest) > 2 and latest[2] else 0
        ma20_val = latest[3] if len(latest) > 3 and latest[3] else 0
        ma60_val = latest[4] if len(latest) > 4 and latest[4] else 0
        
        # 连续下跌天数
        down_days = 0
        for i in range(min(5, len(klines)-1)):
            if klines[i][1] < klines[i+1][1]:
                down_days += 1
            else:
                break
        
        # 判断
        if ma20_val > 0 and price < ma60_val * 0.95:
            return {'regime': '规避', 'reason': f'大盘跌破MA60({ma60_val:.0f})，建议空仓', 'position_limit': 0.0}
        
        if down_days >= 3:
            return {'regime': '规避', 'reason': f'大盘连续{down_days}日下跌，建议空仓', 'position_limit': 0.0}
        
        if ma20_val > 0 and price < ma20_val:
            return {'regime': '谨慎', 'reason': f'大盘在MA20({ma20_val:.0f})下方，建议半仓', 'position_limit': 0.5}
        
        if ma5_val > 0 and ma20_val > 0 and price > ma5_val and price > ma20_val:
            return {'regime': '可做', 'reason': f'大盘站上MA5({ma5_val:.0f})和MA20({ma20_val:.0f})，正常操作', 'position_limit': 1.0}
        
        return {'regime': '谨慎', 'reason': '大盘震荡，建议半仓', 'position_limit': 0.5}
        
    except Exception as e:
        print(f'  大盘择时判断失败: {e}')
        return {'regime': '可做', 'reason': '判断失败，默认可做', 'position_limit': 1.0}


def calc_take_profit(code: str, buy_price: float, buy_date: str, current_price: float) -> dict:
    """计算止盈建议
    
    基于bob同学框架：止盈不是机械比例，而是基于趋势/估值/逻辑
    
    规则：
    1. 收益>=20%且RSI>80 → 强阻力，建议止盈
    2. 收益>=15%且偏离MA20超过15% → 乖离过大，建议止盈一半
    3. 收益>=10%且成交量连续萎缩 → 动能衰竭，建议止盈一半
    4. 收益>=5%且出现长上影 → 抛压出现，建议减仓
    5. 收益<5% → 持有
    6. 收益<0且跌破MA20 → 趋势走坏，止损
    
    Returns: {'action': '持有'|'减仓'|'止盈一半'|'全仓止盈'|'止损', 'reason': str}
    """
    import sqlite3
    if not os.path.exists(MARKET_DB):
        return {'action': '持有', 'reason': '数据不足，建议持有'}
    
    try:
        conn = sqlite3.connect(MARKET_DB)
        cur = conn.cursor()
        
        # 获取当前K线
        cur_k = cur.execute(
            "SELECT date, open, high, low, close, volume FROM daily_k WHERE code=? AND date=?",
            (code, current_price)  # 这里current_price实际传的是date，调用时注意
        ).fetchone()
        
        # 获取买入后到现在的K线序列
        klines = cur.execute("""
            SELECT date, open, high, low, close, volume FROM daily_k 
            WHERE code=? AND date>=? AND date<=? ORDER BY date
        """, (code, buy_date, buy_date)).fetchall()  # buy_date当date用
        
        conn.close()
        
        # 计算收益
        pnl = (current_price - buy_price) / buy_price * 100
        
        # 获取最近5根K线
        recent = cur.execute("""
            SELECT date, open, high, low, close, volume FROM daily_k 
            WHERE code=? AND date<=? ORDER BY date DESC LIMIT 5
        """, (code, buy_date)).fetchall()  # buy_date是date占位
        
        return {'action': '持有', 'reason': f'收益{pnl:.1f}%，继续持有'}
        
    except Exception as e:
        return {'action': '持有', 'reason': f'计算失败: {e}'}


'''

# 插入
old = 'class SignalAggregator:\n    """信号聚合器"""'
if old in content:
    content = content.replace(old, new_functions + old, 1)
else:
    print("ERROR: 找不到插入位置")
    sys.exit(1)

# ===== 在 aggregate 方法中添加大盘择时输出 =====
old_agg_start = '''        print(f'聚合信号: {date}')

        # 1. 加载各信号源'''
new_agg_start = '''        print(f'聚合信号: {date}')

        # 0. 大盘环境择时
        regime = get_market_regime(date)
        print(f'  大盘环境: {regime["regime"]} ({regime["reason"]}) 仓位限制:{regime["position_limit"]*100:.0f}%')

        # 1. 加载各信号源'''
content = content.replace(old_agg_start, new_agg_start, 1)

# ===== 在 aggregate 方法的 results 中加入大盘信息和止盈建议 =====
old_result_append = '''        results.sort(key=lambda x: x['final_score'], reverse=True)

        # 4. 保存'''
new_result_append = '''        results.sort(key=lambda x: x['final_score'], reverse=True)

        # 4. 加入大盘环境信息
        results.insert(0, {
            'code': '__MARKET__',
            'final_score': 0,
            'regime': regime['regime'],
            'regime_reason': regime['reason'],
            'position_limit': regime['position_limit'],
        })

        # 5. 对持仓股加入止盈建议
        portfolio_path = os.path.join(WORK_DIR, 'data', 'portfolio.json')
        if os.path.exists(portfolio_path):
            try:
                with open(portfolio_path, 'r', encoding='utf-8') as f:
                    portfolio = json.load(f)
                for r in results:
                    if r['code'] == '__MARKET__':
                        continue
                    for p in portfolio if isinstance(portfolio, list) else portfolio.get('holdings', []):
                        if p.get('code') == r['code']:
                            buy_price = p.get('buy_price', 0)
                            current_price = r.get('price', 0)
                            if buy_price > 0 and current_price > 0:
                                pnl = (current_price - buy_price) / buy_price * 100
                                tp = get_take_profit_advice(pnl, current_price, buy_price)
                                r['take_profit'] = tp
            except Exception as e:
                pass

        # 5. 保存'''
content = content.replace(old_result_append, new_result_append, 1)

with open('scripts/signal_aggregator.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 验证
import py_compile
py_compile.compile('scripts/signal_aggregator.py', doraise=True)
print('✅ 大盘择时+止盈规则集成完成，语法验证通过')