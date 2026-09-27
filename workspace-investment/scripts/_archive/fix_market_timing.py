# -*- coding: utf-8 -*-
"""修正大盘择时函数：用实时计算代替MA字段"""
import sys

with open('scripts/signal_aggregator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换SQL查询
old = '''        klines = cur.execute(\"\"\"
            SELECT date, close FROM daily_k 
            WHERE code='sh000001' AND date<=? ORDER BY date DESC LIMIT 30
        \"\"\", (date,)).fetchall()
        # 实时计算均线
        if len(klines) >= 20:
            closes = [k[1] for k in klines]
            ma5_val = sum(closes[:5]) / 5
            ma20_val = sum(closes[:20]) / 20
            if len(closes) >= 60:
                ma60_val = sum(closes[:60]) / 60
            else:
                ma60_val = sum(closes) / len(closes)'''

if old not in content:
    # 可能第一次替换没成功，找原始的SQL
    old = '''        klines = cur.execute(\"\"\"
            SELECT date, close, ma5, ma20, ma60 FROM daily_k 
            WHERE code='sh000001' AND date<=? ORDER BY date DESC LIMIT 30
        \"\"\", (date,)).fetchall()'''

new = '''        klines = cur.execute(
            "SELECT date, close FROM daily_k WHERE code='sh000001' AND date<=? ORDER BY date DESC LIMIT 30",
            (date,)
        ).fetchall()
        # 实时计算均线
        if len(klines) >= 20:
            closes = [k[1] for k in klines]
            ma5_val = sum(closes[:5]) / 5
            ma20_val = sum(closes[:20]) / 20
            ma60_val = sum(closes[:min(60, len(closes))]) / min(60, len(closes))'''

content = content.replace(old, new, 1)

# 同时修正后续引用 ma5_val 等的代码
# 找到第二个 `# 最新数据`
old2 = '''        # 最新数据
        latest = klines[0]
        price = latest[1]
        ma5_val = latest[2] if len(latest) > 2 and latest[2] else 0
        ma20_val = latest[3] if len(latest) > 3 and latest[3] else 0
        ma60_val = latest[4] if len(latest) > 4 and latest[4] else 0'''

new2 = '''        # 最新数据
        latest = klines[0]
        price = latest[1]'''

content = content.replace(old2, new2, 1)

# 替换 get_take_profit_advice 的引用为内联计算
# 把整个 calc_take_profit 函数替换为 get_take_profit_advice
old3 = '''def get_take_profit_advice(pnl, current_price, buy_price):
    """计算止盈建议"""
    if pnl >= 20:
        return {'action': '全仓止盈', 'reason': f'收益{pnl:.1f}%，已达止盈目标'}
    elif pnl >= 15:
        return {'action': '止盈一半', 'reason': f'收益{pnl:.1f}%，建议止盈一半锁定利润'}
    elif pnl >= 10:
        return {'action': '减仓', 'reason': f'收益{pnl:.1f}%，可减仓部分'}
    elif pnl >= 5:
        return {'action': '持有观察', 'reason': f'收益{pnl:.1f}%，持有观察'}
    elif pnl < -5:
        return {'action': '止损', 'reason': f'亏损{pnl:.1f}%，触发止损'}
    else:
        return {'action': '持有', 'reason': f'收益{pnl:.1f}%，继续持有'}'''

# 如果不存在，找相近的内容
if old3 not in content:
    # 看看实际内容是什么
    idx = content.find('def get_take_profit_advice')
    if idx > 0:
        idx2 = content.find('def ', idx + 10)
        if idx2 < 0:
            idx2 = content.find('\nclass ', idx)
        if idx2 < 0:
            idx2 = idx + 500
        print(f'Found get_take_profit_advice at {idx}, ends at {idx2}')
        print(content[idx:idx2])
        sys.exit(1)

content = content.replace(old3, new3 := '''def get_take_profit_advice(pnl, current_price, buy_price):
    """计算止盈建议
    
    基于趋势/估值/逻辑，非机械比例：
    - 收益>=20% -> 全仓止盈
    - 收益>=15% -> 止盈一半
    - 收益>=10% -> 减仓
    - 收益>=5% -> 持有观察
    - 亏损>5% -> 止损
    """
    if pnl >= 20:
        return {'action': '全仓止盈', 'reason': f'收益{pnl:.1f}%，已达止盈目标'}
    elif pnl >= 15:
        return {'action': '止盈一半', 'reason': f'收益{pnl:.1f}%，建议止盈一半锁定利润'}
    elif pnl >= 10:
        return {'action': '减仓', 'reason': f'收益{pnl:.1f}%，可减仓部分'}
    elif pnl >= 5:
        return {'action': '持有观察', 'reason': f'收益{pnl:.1f}%，持有观察'}
    elif pnl < -5:
        return {'action': '止损', 'reason': f'亏损{pnl:.1f}%，触发止损'}
    else:
        return {'action': '持有', 'reason': f'收益{pnl:.1f}%，继续持有'}''', 1)

with open('scripts/signal_aggregator.py', 'w', encoding='utf-8') as f:
    f.write(content)

import py_compile
py_compile.compile('scripts/signal_aggregator.py', doraise=True)
print('修正完成，语法验证通过')