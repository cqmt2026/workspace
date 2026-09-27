# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime

df = pd.read_excel(r'C:\Users\Administrator\Desktop\近三月.xlsx')

trades = []

# Group by stock, process FIFO
stocks = df.groupby('证券代码')

for code, group in stocks:
    name = group['证券名称'].iloc[0]
    group = group.sort_values('成交日期')
    buy_fifo = []  # [{date, qty, price}]

    for _, row in group.iterrows():
        date = row['成交日期']
        direction = row['委托方向']
        qty = row['成交数量']
        price = row['成交均价']
        fees = row['佣金'] + row['其他费用'] + (row['印花税'] if '印花税' in row else 0) + (row['过户费'] if '过户费' in row else 0)

        if direction == '证券买入':
            buy_date_val = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
            buy_fifo.append({'date': buy_date_val, 'qty': qty, 'price': price})
        elif direction == '证券卖出' and buy_fifo:
            sell_qty = qty
            total_proceeds = sell_qty * price
            total_cost = 0
            last_buy_date = None
            first_buy_date = None
            last_buy_date_str = None
            first_buy_date_str = None

            while sell_qty > 0 and buy_fifo:
                b = buy_fifo[0]
                match_qty = min(sell_qty, b['qty'])
                total_cost += match_qty * b['price']
                last_buy_date_str = b['date']
                if first_buy_date_str is None:
                    first_buy_date_str = b['date']
                sell_qty -= match_qty
                b['qty'] -= match_qty
                if b['qty'] <= 0:
                    buy_fifo.pop(0)

            sell_date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
            net_proceeds = total_proceeds - fees
            pnl = net_proceeds - total_cost
            pnl_pct = pnl / total_cost * 100 if total_cost else 0
            if last_buy_date_str:
                d1 = datetime.strptime(sell_date_str, '%Y-%m-%d')
                d2 = datetime.strptime(last_buy_date_str, '%Y-%m-%d')
                holding_days = (d1 - d2).days
            else:
                holding_days = 0

            trades.append({
                'name': name,
                'code': code,
                'sell_date': sell_date_str,
                'buy_date': first_buy_date_str if first_buy_date_str else '',
                'qty': qty,
                'cost': round(total_cost, 2),
                'proceeds': round(net_proceeds, 2),
                'pnl': round(pnl, 2),
                'pnl_pct': round(pnl_pct, 2),
                'holding_days': holding_days,
            })

# === Summary ===
print('=' * 60)
print('  近三月交易记录分析')
print('=' * 60)
print()

# Table
print('%-8s %-6s %5s %8s %8s %8s %7s %5s' % ('股票', '代码', '数量', '成本', '卖出额', '盈亏', '收益率', '持仓天'))
print('-' * 60)
for t in trades:
    sign = '+' if t['pnl'] >= 0 else ''
    print('%-8s %-6s %5d %8.2f %8.2f %8.2f %7.2f%% %5d' % (
        t['name'][:8], t['code'], t['qty'], t['cost'], t['proceeds'],
        t['pnl'], t['pnl_pct'], t['holding_days']))

print('-' * 60)
wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] <= 0]
total_pnl = sum(t['pnl'] for t in trades)
total_cost = sum(t['cost'] for t in trades)
print('%-8s %-6s %5s %8.2f %8s %8.2f' % ('', '', '', total_cost, '', total_pnl))
print()

print('=' * 60)
print('  汇总统计')
print('=' * 60)
print()
print('  交易次数:  %d' % len(trades))
print('  盈利次数:  %d (%d%%)' % (len(wins), len(wins)*100//max(len(trades),1)))
print('  亏损次数:  %d (%d%%)' % (len(losses), len(losses)*100//max(len(trades),1)))
print()
print('  总盈亏:    %+.2f 元' % total_pnl)
print('  总收益率:  %+.2f%%' % (total_pnl/total_cost*100 if total_cost else 0))
print()

if trades:
    avg_holding = sum(t['holding_days'] for t in trades) / len(trades)
    print('  平均持仓:  %.1f 天' % avg_holding)
    min_t = min(trades, key=lambda x: x['holding_days'])
    max_t = max(trades, key=lambda x: x['holding_days'])
    print('  最短持仓:  %d 天 (%s)' % (min_t['holding_days'], min_t['name']))
    print('  最长持仓:  %d 天 (%s)' % (max_t['holding_days'], max_t['name']))
    print()

if wins:
    best = max(wins, key=lambda x: x['pnl'])
    worst = min(wins, key=lambda x: x['pnl_pct'])
    print('  最大盈利:  %+.2f (%s, %+.2f%%)' % (best['pnl'], best['name'], best['pnl_pct']))
    print('  最大盈幅:  %+.2f%% (%s)' % (best['pnl_pct'], best['name']))
if losses:
    worst = min(losses, key=lambda x: x['pnl'])
    print('  最大亏损:  %+.2f (%s, %+.2f%%)' % (worst['pnl'], worst['name'], worst['pnl_pct']))

print()
print('=' * 60)

# === Pattern Analysis ===
print('  模式识别')
print('=' * 60)
print()

# Day trades
day_trades = [t for t in trades if t['holding_days'] == 0]
print('  日内交易(当天卖): %d次 (%d%%)' % (
    len(day_trades), len(day_trades)*100//max(len(trades),1)))
for t in day_trades:
    print('    %s %s: %+.2f%%' % (t['sell_date'], t['name'], t['pnl_pct']))

print()

# Short term (< 3 days)
short = [t for t in trades if 1 <= t['holding_days'] <= 2]
print('  短线(1-2天): %d次' % len(short))
for t in short:
    print('    %s %s(%s): %+.2f%% (%d天)' % (
        t['sell_date'], t['name'], t['code'], t['pnl_pct'], t['holding_days']))

print()

# Sector exposure
sectors = {}
# Known sectors from current portfolio or we can try to map
for t in trades:
    # simple pattern: check code prefix
    sectors.setdefault(t['name'], []).append(t)

print('  个股盈亏:')
for name, ts in sectors.items():
    total = sum(t['pnl'] for t in ts)
    pct = total / sum(t['cost'] for t in ts) * 100
    print('    %s: %+.2f (%+.2f%%)' % (name, total, pct))

print()
print('=' * 60)