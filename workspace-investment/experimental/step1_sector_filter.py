# -*- coding: utf-8 -*-
"""
Step 1: 板块RPS筛选
====================
从现有RPS数据中，筛选出RPS>70的强势板块，
然后从这些板块中提取成分股。

数据来源：
  - out_data/rps_history/ 下的板块RPS JSON
  - efinance (实时板块成分股)
  - data/stock_board_cache.json (回退方案)

输出：
  - 强势板块列表（含RPS值）
  - 板块内成分股列表

不修改现有系统。
"""
import json, os, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
RPS_HISTORY = os.path.join(WORKSPACE, 'out_data', 'rps_history')
BOARD_CACHE = os.path.join(WORKSPACE, 'data', 'stock_board_cache.json')

def get_latest_rps():
    """获取最新一天的板块RPS数据"""
    files = sorted([f for f in os.listdir(RPS_HISTORY) if f.endswith('.json')], reverse=True)
    if not files:
        print("[Step1] 无RPS历史数据")
        return None, None
    
    latest = files[0]
    with open(os.path.join(RPS_HISTORY, latest), encoding='utf-8') as f:
        data = json.load(f)
    
    boards = data.get('boards', data.get('rps_data', []))
    date_str = latest.replace('RPS_board_', '').replace('.json', '')
    
    return boards, date_str

def get_strong_sectors(boards, rps_threshold=70, top_n=10):
    """筛选RPS>70的强势板块"""
    strong = [b for b in boards if b.get('rps_5d', 0) >= rps_threshold]
    strong.sort(key=lambda x: x.get('rps_5d', 0), reverse=True)
    
    print(f"[Step1] 强势板块 (RPS>={rps_threshold}): {len(strong)}个")
    for b in strong[:top_n]:
        name = b.get('name', b.get('code', '?'))
        rps5 = b.get('rps_5d', 0)
        rps10 = b.get('rps_10d', 0)
        print(f"  {name:20s} RPS5={rps5:.0f} RPS10={rps10:.0f}")
    
    return strong

def get_sector_stocks(board_name, cache=None):
    """
    获取板块成分股
    优先用efinance实时获取（不依赖缓存），失败时回退到缓存
    """
    # 方案1: efinance
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        try:
            import efinance as ef
            df = ef.stock.get_belong_board('000001', board_name=board_name)
            if df is not None and not df.empty and len(df) > 0:
                stocks = []
                seen_codes = set()
                for _, row in df.iterrows():
                    code = str(row.get('股票代码', '')).strip()
                    name = str(row.get('股票名称', str(code)))
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        prefix = 'sh.' if code.startswith('6') else 'sz.'
                        stocks.append({'code': prefix + code, 'name': name})
                if stocks:
                    return stocks
        except:
            pass
    
    # 方案2: 缓存回退
    if cache is None:
        cache = load_board_cache()
    stocks = []
    for code, info in cache.items():
        if isinstance(info, str):
            if board_name == info:
                stocks.append({'code': code, 'name': code})
        elif isinstance(info, dict):
            board = info.get('board', info.get('industry', ''))
            if board_name in board:
                stocks.append({'code': code, 'name': info.get('name', code)})
    return stocks

def get_stock_names(codes):
    """从DB获取股票名称"""
    import sqlite3
    conn = sqlite3.connect(r'F:\market_data.db')
    c = conn.cursor()
    names = {}
    for code in codes[:50]:
        try:
            c.execute("SELECT name FROM daily_k WHERE code LIKE ? AND name IS NOT NULL LIMIT 1", (f'%{code}',))
            row = c.fetchone()
            if row:
                names[code] = row[0]
        except:
            pass
    conn.close()
    return names

def load_board_cache():
    """加载股票→板块映射缓存"""
    if not os.path.exists(BOARD_CACHE):
        print("[Step1] 板块缓存不存在")
        return {}
    with open(BOARD_CACHE, encoding='utf-8') as f:
        return json.load(f)

def run(rps_threshold=70, top_sectors=10, verbose=True):
    """执行Step1"""
    if verbose:
        print("=" * 60)
        print("Step 1: 板块RPS筛选")
        print("=" * 60)
    
    boards, date_str = get_latest_rps()
    if not boards:
        return []
    
    strong = get_strong_sectors(boards, rps_threshold, top_sectors)
    cache = load_board_cache()
    
    # 提取所有强势板块的成分股（efinance优先，缓存回退）
    all_stocks = []
    failed_boards = []
    matched_count = 0
    for b in strong:
        name = b.get('name', b.get('code', ''))
        stocks = get_sector_stocks(name, cache)
        if stocks:
            matched_count += 1
            for s in stocks:
                s['sector'] = name
                s['sector_rps'] = b.get('rps_5d', 0)
            all_stocks.extend(stocks)
        else:
            failed_boards.append(name)
    
    if verbose:
        print(f"[Step1] 强势板块: {len(strong)}个, 获取成分股成功: {matched_count}个")
        if failed_boards:
            print(f"  获取失败的板块: {failed_boards}")
        print(f"\n[Step1] 成分股总计: {len(all_stocks)}只")
    
    # 去重
    seen = {}
    for s in all_stocks:
        code = s['code']
        if code not in seen or s['sector_rps'] > seen[code]['sector_rps']:
            seen[code] = s
    
    unique_stocks = list(seen.values())
    unique_stocks.sort(key=lambda x: x['sector_rps'], reverse=True)
    
    if verbose:
        print(f"[Step1] 去重后: {len(unique_stocks)}只")
        for s in unique_stocks[:10]:
            print(f"  {s.get('name','?'):10s}({s['code']}) 板块:{s['sector']} RPS:{s['sector_rps']:.0f}")
    
    return {
        'date': date_str,
        'threshold': rps_threshold,
        'strong_sectors': [{'name': b.get('name','?'), 'rps_5d': b.get('rps_5d',0)} for b in strong],
        'candidates': unique_stocks,
        'total_raw': len(all_stocks),
        'total_unique': len(unique_stocks)
    }

if __name__ == '__main__':
    result = run()
    print(f"\n[Step1] 完成: {result['total_unique']}只候选股来自{len(result['strong_sectors'])}个强势板块")