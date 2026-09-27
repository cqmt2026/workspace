# -*- coding: utf-8 -*-
"""获取大盘和板块数据"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import akshare as ak

print("=" * 50)
print("【大盘指数】")
print("=" * 50)

# 获取主要指数行情
indices = [
    ('sh000001', '上证指数'),
    ('sz399001', '深证成指'),
    ('sz399006', '创业板指'),
    ('sh000300', '沪深300'),
    ('sh000016', '上证50'),
]

for code, name in indices:
    try:
        df = ak.stock_zh_index_spot_em(symbol=code)
        if not df.empty:
            row = df[df['代码'] == code]
            if not row.empty:
                idx = row.iloc[0]
                print(f"{name}: {idx['最新价']} 涨跌={idx['涨跌额']} 涨跌幅={idx['涨跌幅']}%")
    except Exception as e:
        pass

print()
print("=" * 50)
print("【板块涨跌Top5】")
print("=" * 50)

try:
    df = ak.stock_board_industry_name_em()
    top = df.nlargest(5, '涨跌幅')
    bot = df.nsmallest(5, '涨跌幅')
    
    print("涨幅榜:")
    for _, r in top.iterrows():
        print(f"  {r['板块名称']}: {r['涨跌幅']}%")
    
    print("跌幅榜:")
    for _, r in bot.iterrows():
        print(f"  {r['板块名称']}: {r['涨跌幅']}%")
except Exception as e:
    print(f"板块数据获取失败: {e}")

print()
print("=" * 50)
print("【北向资金】")
print("=" * 50)

try:
    df = ak.stock_hsgt_hist_em(symbol='北向')
    if not df.empty:
        latest = df.iloc[-1]
        print(f"最新日期: {latest['日期']}")
        print(f"北向净流入: {latest['北向净流入']}亿元")
except Exception as e:
    print(f"北向资金获取失败: {e}")
