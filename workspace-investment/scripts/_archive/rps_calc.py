# -*- coding: utf-8 -*-
"""
RPS分析 - 使用正确的数据库路径 F:\market_data.db
"""
import sqlite3, os, json, csv
from datetime import datetime
from typing import List, Dict

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB = r'F:\market_data.db'
STOCK_LIST_CSV = os.path.join(WORK_DIR, 'data', 'stock_list_clean.csv')
OUT_DIR = os.path.join(WORK_DIR, 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)

MIN_PRICE = 3.0
MAX_PRICE = 300.0

# 加载股票名称映射
def load_name_map():
    name_map = {}
    for enc in ['gbk', 'gb2312', 'latin1']:
        try:
            with open(STOCK_LIST_CSV, encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_map[row['code']] = row['name']
            break
        except:
            continue
    return name_map

def get_latest_date(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(date) FROM daily_k")
    return cur.fetchone()[0]

def calc_rps_for_period(conn, stocks, latest_date, period, name_map):
    """计算指定周期的RPS"""
    cur = conn.cursor()
    results = []
    
    # 获取period+1个交易日
    cur.execute("""
        SELECT DISTINCT date FROM daily_k 
        ORDER BY date DESC LIMIT ?
    """, (period + 1,))
    dates = [r[0] for r in cur.fetchall()]
    
    if len(dates) < period + 1:
        print(f"  警告: 仅有{len(dates)}个交易日，不足以计算{period}日RPS")
        return results
    
    for code, _ in stocks:
        # 获取period天的收盘价
        closes = []
        valid = True
        for d in dates[:period]:
            cur.execute("SELECT close FROM daily_k WHERE code=? AND date=?", (code, d))
            row = cur.fetchone()
            if row is None:
                valid = False
                break
            closes.append(row[0])
        
        if not valid or len(closes) < period:
            continue
        
        # 获取基准日价格
        cur.execute("SELECT close FROM daily_k WHERE code=? AND date=?", (code, dates[period]))
        base_row = cur.fetchone()
        if not base_row or base_row[0] <= 0:
            continue
        
        base_price = base_row[0]
        avg_recent = sum(closes) / period
        pct = (avg_recent / base_price - 1) * 100
        
        # 获取现价
        cur.execute("SELECT close FROM daily_k WHERE code=? AND date=?", (code, latest_date))
        price_row = cur.fetchone()
        price = price_row[0] if price_row else None
        
        name = name_map.get(code, code)
        
        results.append({
            'code': code,
            'name': name,
            'rps': round(pct, 2),
            'price': price
        })
    
    results.sort(key=lambda x: x['rps'], reverse=True)
    return results

print(f"[RPS] Start {datetime.now()}")

name_map = load_name_map()
print(f"已加载{len(name_map)}只股票名称")

conn = sqlite3.connect(DB)
cur = conn.cursor()

latest_date = get_latest_date(conn)
print(f"最新交易日: {latest_date}")

# 获取符合条件的股票
cur.execute("""
    SELECT code, close FROM daily_k 
    WHERE date=? AND close >= ? AND close <= ?
""", (latest_date, MIN_PRICE, MAX_PRICE))
stocks = [(r[0], r[1]) for r in cur.fetchall()]
print(f"符合条件的股票数: {len(stocks)}")

print("计算5日RPS...")
rps5 = calc_rps_for_period(conn, stocks, latest_date, 5, name_map)
print(f"  有效结果: {len(rps5)}")

print("计算20日RPS...")
rps20 = calc_rps_for_period(conn, stocks, latest_date, 20, name_map)
print(f"  有效结果: {len(rps20)}")

conn.close()

top10_rps5 = rps5[:10]
top10_rps20 = rps20[:10]

print("\n========== RPS5 Top10 ==========")
for i, s in enumerate(top10_rps5, 1):
    print(f"{i}. {s['code']} {s['name']} RPS5={s['rps']}% 现价={s['price']}")

print("\n========== RPS20 Top10 ==========")
for i, s in enumerate(top10_rps20, 1):
    print(f"{i}. {s['code']} {s['name']} RPS20={s['rps']}% 现价={s['price']}")

output = {
    'latest_date': latest_date,
    'rps5_top10': top10_rps5,
    'rps20_top10': top10_rps20,
    'rps5_all': rps5[:50],
    'rps20_all': rps20[:50]
}
out_path = os.path.join(OUT_DIR, 'rps_top10.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存: {out_path}")
