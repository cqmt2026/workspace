"""
方向2: 板块RPS分析 v1.0
===========================
计算个股RPS（相对强度）vs 市场指数

RPS计算方法：
- 个股N日涨幅 vs 指数N日涨幅
- N日可以是5/10/20/60日
- RPS = (个股涨幅 - 指数涨幅) 的排名百分位

数据来源: F:\market_data.db.daily_k
"""
import io
import sqlite3
from datetime import datetime, timedelta
import json, os

DB = r'F:\market_data.db'
OUT = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data'
os.makedirs(OUT, exist_ok=True)


def calc_stock_return(code, days=20):
    """计算个股N日收益率"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+10)).strftime('%Y-%m-%d')
    
    cur.execute("""
        SELECT date, close FROM daily_k 
        WHERE code = ? AND date >= ?
        ORDER BY date DESC
        LIMIT ?
    """, (code, start_date, days+1))
    
    rows = cur.fetchall()
    conn.close()
    
    if len(rows) < 2:
        return None
    
    # 最新收盘 vs N天前收盘
    latest_close = rows[0][1]
    old_close = rows[-1][1]
    
    if old_close == 0:
        return None
    
    return (latest_close - old_close) / old_close * 100


def calc_index_return(index_code='sh.000001', days=20):
    """计算指数N日收益率"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+10)).strftime('%Y-%m-%d')
    
    cur.execute("""
        SELECT date, close FROM daily_k 
        WHERE code = ? AND date >= ?
        ORDER BY date DESC
        LIMIT ?
    """, (index_code, start_date, days+1))
    
    rows = cur.fetchall()
    conn.close()
    
    if len(rows) < 2:
        return 0
    
    latest_close = rows[0][1]
    old_close = rows[-1][1]
    
    if old_close == 0:
        return 0
    
    return (latest_close - old_close) / old_close * 100


def calc_rps_for_all_stocks(days_list=[5, 10, 20, 60]):
    """计算所有股票的RPS"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 获取最新日期的全部股票
    cur.execute("SELECT MAX(date) FROM daily_k")
    latest_date = cur.fetchone()[0]
    
    cur.execute("""
        SELECT DISTINCT code FROM daily_k 
        WHERE date = ?
    """, (latest_date,))
    
    codes = [r[0] for r in cur.fetchall()]
    print(f"计算RPS: {latest_date}, {len(codes)}只股票...")
    
    results = []
    for code in codes:
        row_data = {'code': code}
        for days in days_list:
            ret = calc_stock_return(code, days)
            row_data[f'return_{days}d'] = ret
        if any(row_data[f'return_{d}d'] is not None for d in days_list):
            results.append(row_data)
    
    conn.close()
    
    # 计算各周期RPS排名
    for days in days_list:
        returns = [r[f'return_{days}d'] for r in results if r[f'return_{days}d'] is not None]
        if not returns:
            continue
        
        returns_sorted = sorted(returns)
        n = len(returns_sorted)
        
        for r in results:
            ret = r.get(f'return_{days}d')
            if ret is not None:
                # RPS = 排名百分位 (0-100)
                rank = returns_sorted.index(ret)
                r[f'rps_{days}d'] = round(rank / n * 100, 1)
    
    return results


def get_top_rps(rps_data, days=20, top_n=20):
    """获取RPS最强的股票"""
    field = f'rps_{days}d'
    sorted_data = sorted(rps_data, key=lambda x: x.get(field, 0) or 0, reverse=True)
    return sorted_data[:top_n]


def format_rps_report(rps_data, days=20):
    """生成RPS报告"""
    top = get_top_rps(rps_data, days, 20)
    
    print(f"\n=== RPS {days}日 Top20 ({datetime.now().strftime('%Y-%m-%d')}) ===")
    for i, item in enumerate(top, 1):
        code = item['code']
        rps = item.get(f'rps_{days}d', 0) or 0
        ret = item.get(f'return_{days}d', 0) or 0
        print(f"  {i:2d}. {code} RPS={rps:5.1f} 涨幅={ret:+6.2f}%")


def save_rps_json(rps_data, days=20):
    """保存RPS数据到JSON"""
    top = get_top_rps(rps_data, days, 50)
    
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'rps_period': f'{days}d',
        'top_stocks': top,
        'total_stocks': len(rps_data)
    }
    
    out_file = os.path.join(OUT, f'rps_{days}d_{datetime.now().strftime("%Y%m%d")}.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {out_file}")


def main():
    print("开始计算RPS...")
    
    # 计算各周期RPS
    for days in [5, 10, 20, 60]:
        rps_data = calc_rps_for_all_stocks([days])
        format_rps_report(rps_data, days)
        save_rps_json(rps_data, days)
    
    print("\n✅ RPS分析完成")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
