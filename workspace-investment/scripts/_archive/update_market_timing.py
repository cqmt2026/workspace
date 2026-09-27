# -*- coding: utf-8 -*-
"""替换大盘择时函数"""
import sys

with open('scripts/signal_aggregator.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('def get_market_regime')
idx2 = content.find('def calc_take_profit', idx)
if idx2 < 0:
    idx2 = content.find('def get_take_profit_advice', idx)

new_func = []
new_func.append('def get_market_regime(date: str) -> dict:\n')
new_func.append('    """判断大盘环境：可做/谨慎/规避\n')
new_func.append('\n')
new_func.append('    使用涨停家数判断市场情绪：\n')
new_func.append('    - 涨停>=30家 -> 可做（市场活跃）\n')
new_func.append('    - 涨停15-30家 -> 谨慎（半仓）\n')
new_func.append('    - 涨停<15家或连续3日递减 -> 规避（空仓）\n')
new_func.append('    """\n')
new_func.append('    import sqlite3\n')
new_func.append('    from datetime import datetime, timedelta\n')
new_func.append('\n')
new_func.append('    if not os.path.exists(MARKET_DB):\n')
new_func.append('        return {"regime": "可做", "reason": "数据不足，默认可做", "position_limit": 1.0}\n')
new_func.append('\n')
new_func.append('    try:\n')
new_func.append('        conn = sqlite3.connect(MARKET_DB)\n')
new_func.append('        cur = conn.cursor()\n')
new_func.append('        today_zt = cur.execute(\n')
new_func.append('            "SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (date,)\n')
new_func.append('        ).fetchone()[0] or 0\n')
new_func.append('        prev_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")\n')
new_func.append('        prev_zt = cur.execute(\n')
new_func.append('            "SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (prev_date,)\n')
new_func.append('        ).fetchone()[0] or 0\n')
new_func.append('        prev2_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")\n')
new_func.append('        prev2_zt = cur.execute(\n')
new_func.append('            "SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (prev2_date,)\n')
new_func.append('        ).fetchone()[0] or 0\n')
new_func.append('        conn.close()\n')
new_func.append('\n')
new_func.append('        trend_down = today_zt < prev_zt and prev_zt < prev2_zt\n')
new_func.append('\n')
new_func.append('        if today_zt >= 30:\n')
new_func.append('            return {"regime": "可做", "reason": f"涨停{today_zt}家，市场活跃", "position_limit": 1.0}\n')
new_func.append('        elif today_zt >= 15:\n')
new_func.append('            return {"regime": "谨慎", "reason": f"涨停{today_zt}家，市场一般", "position_limit": 0.5}\n')
new_func.append('        elif trend_down and today_zt < 15:\n')
new_func.append('            return {"regime": "规避", "reason": f"涨停{today_zt}家且连续递减({prev2_zt}->{prev_zt}->{today_zt})，建议空仓", "position_limit": 0.0}\n')
new_func.append('        else:\n')
new_func.append('            return {"regime": "谨慎", "reason": f"涨停仅{today_zt}家，建议半仓", "position_limit": 0.5}\n')
new_func.append('\n')
new_func.append('    except Exception as e:\n')
new_func.append('        print(f"  大盘择时判断失败: {e}")\n')
new_func.append('        return {"regime": "可做", "reason": "判断失败，默认可做", "position_limit": 1.0}\n')
new_func.append('\n')

content = content[:idx] + ''.join(new_func) + content[idx2:]

with open('scripts/signal_aggregator.py', 'w', encoding='utf-8') as f:
    f.write(content)

import py_compile
py_compile.compile('scripts/signal_aggregator.py', doraise=True)
print('替换完成，语法通过')