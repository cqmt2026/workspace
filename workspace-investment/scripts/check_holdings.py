# -*- coding: utf-8 -*-
"""持仓股完整检查"""
import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'F:\market_data.db')
fd = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\factors.db'
pf_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\portfolio.json'

print('=== 持仓股实时状态 (2026-07-10 10:19) ===')
holdings = {
    'sh.688102': '斯瑞新材',
    'sh.600845': '宝信软件',
    'sz.300593': '新雷能'
}

# 读持仓JSON获取成本价
pf = json.load(open(pf_path, 'r', encoding='utf-8'))
cost_map = {}
for h in pf.get('holdings', []):
    code_db = 'sh.' + h['code'][2:] if h['code'].startswith('sh') else 'sz.' + h['code'][2:]
    cost_map[code_db] = h.get('cost_price', 0)

for code_db, name in holdings.items():
    r10 = conn.execute(
        'SELECT close FROM daily_k WHERE code=? AND date="2026-07-10"',
        (code_db,)
    ).fetchone()
    r09 = conn.execute(
        'SELECT close FROM daily_k WHERE code=? AND date="2026-07-09"',
        (code_db,)
    ).fetchone()
    r07 = conn.execute(
        'SELECT close FROM daily_k WHERE code=? AND date="2026-07-03"',
        (code_db,)
    ).fetchone()

    current_price = r10[0] if r10 else r09[0]
    prev_close = r09[0] if r09 else current_price
    base_close = r07[0] if r07 else current_price
    cost = cost_map.get(code_db, 0)

    print('\n{} ({})'.format(name, code_db))
    print('  最新价: {:.2f}'.format(current_price))
    if prev_close != current_price:
        pct_d = (current_price - prev_close) / prev_close * 100
        print('  日涨跌: {:+.2f}% (前收{:.2f})'.format(pct_d, prev_close))
    if base_close:
        pct7 = (current_price - base_close) / base_close * 100
        print('  7日涨跌: {:+.2f}% (7/3收{:.2f})'.format(pct7, base_close))
    if cost > 0:
        pct_cost = (current_price - cost) / cost * 100
        flag = '+' if pct_cost >= 0 else ''
        print('  盈亏: {:+.2f}% (成本{:.2f})'.format(pct_cost, cost))

    # 7/9最新因子
    fconn = sqlite3.connect(fd)
    factors = fconn.execute(
        'SELECT factor_name, value FROM factors WHERE code=? AND date="2026-07-09" ORDER BY factor_name',
        (code_db,)
    ).fetchall()
    factor_map = {fname: val for fname, val in factors}
    print('  关键因子(7/9):')
    for fname in ['pct_chg_1d','pct_chg_5d','ma_5','ma_20','ma_60','rsi_14','vol_ratio','atr_14','profit_ratio','macd_cross','breakout_strength']:
        if fname in factor_map:
            print('    {}: {:.2f}'.format(fname, factor_map[fname]))
    fconn.close()

conn.close()