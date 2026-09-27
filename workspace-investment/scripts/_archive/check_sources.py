#!/usr/bin/env python3
"""检查数据源状态"""
import io
import os, json, datetime, sqlite3

def load_json(path):
    for enc in ['utf-8', 'gbk', 'utf-8-sig', 'latin1']:
        try:
            with open(path, encoding=enc) as f:
                return json.load(f)
        except:
            continue
    return None

def main():
    results = {}

    # 1. 核心K线库
    db_path = r'F:\market_data.db'
    results['market_db'] = {}
    results['market_db']['exists'] = os.path.exists(db_path)
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / 1024 / 1024
        results['market_db']['size_mb'] = round(size_mb, 1)
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        results['market_db']['tables'] = {}
        for t in tables:
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM [{t[0]}]').fetchone()[0]
                results['market_db']['tables'][t[0]] = count
            except:
                pass
        try:
            latest = conn.execute('SELECT MAX(trade_date) FROM daily_kline').fetchone()[0]
            results['market_db']['latest_date'] = latest
        except Exception as e:
            results['market_db']['latest_date_error'] = str(e)
        conn.close()

    # 2. 因子库
    factor_path = r'data/factors.db'
    results['factor_db'] = {}
    results['factor_db']['exists'] = os.path.exists(factor_path)
    if os.path.exists(factor_path):
        conn = sqlite3.connect(factor_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        results['factor_db']['tables'] = {}
        for t in tables:
            count = conn.execute(f'SELECT COUNT(*) FROM [{t[0]}]').fetchone()[0]
            results['factor_db']['tables'][t[0]] = count
        conn.close()

    # 3. 持仓
    port_path = r'data/portfolio.json'
    results['portfolio'] = {}
    if os.path.exists(port_path):
        port = load_json(port_path)
        if port:
            if isinstance(port, list):
                results['portfolio']['positions'] = len(port)
                for p in port[:3]:
                    results['portfolio']['first_3'] = results.get('portfolio', {}).get('first_3', [])
                    if 'first_3' not in results['portfolio']:
                        results['portfolio']['first_3'] = []
                    results['portfolio']['first_3'].append(p)
            else:
                results['portfolio']['data'] = port
    else:
        results['portfolio']['status'] = 'MISSING'

    # 4. 股票池
    pool_path = r'config/stock_pool.json'
    results['stock_pool'] = {}
    if os.path.exists(pool_path):
        pool = load_json(pool_path)
        if pool:
            if isinstance(pool, list):
                results['stock_pool']['count'] = len(pool)
                results['stock_pool']['first_3'] = pool[:3]
            elif isinstance(pool, dict):
                results['stock_pool']['count'] = len(pool)
                results['stock_pool']['keys'] = list(pool.keys())[:5]
    else:
        results['stock_pool']['status'] = 'MISSING'

    # 5. 交易历史
    hist_path = r'data/trade_history.json'
    results['trade_history'] = {}
    if os.path.exists(hist_path):
        hist = load_json(hist_path)
        if hist:
            if isinstance(hist, list):
                results['trade_history']['count'] = len(hist)
            elif isinstance(hist, dict):
                results['trade_history']['count'] = len(hist)
    else:
        results['trade_history']['status'] = 'MISSING'

    # 6. out_data最新文件
    out_path = r'out_data'
    results['out_data'] = {}
    if os.path.exists(out_path):
        files = [f for f in os.listdir(out_path) if os.path.isfile(os.path.join(out_path, f))]
        results['out_data']['file_count'] = len(files)
        files.sort(key=lambda f: os.path.getmtime(os.path.join(out_path, f)), reverse=True)
        latest = []
        for f in files[:15]:
            mtime = os.path.getmtime(os.path.join(out_path, f))
            dt = datetime.datetime.fromtimestamp(mtime)
            sz = os.path.getsize(os.path.join(out_path, f))
            latest.append({'file': f, 'size_kb': round(sz/1024, 1), 'modified': dt.strftime('%m-%d %H:%M')})
        results['out_data']['latest_files'] = latest

    # 7. 板块缓存
    board_path = r'data/stock_board_cache.json'
    results['board_cache'] = {}
    if os.path.exists(board_path):
        sz = os.path.getsize(board_path) / 1024 / 1024
        results['board_cache']['size_mb'] = round(sz, 1)
        bc = load_json(board_path)
        if bc:
            results['board_cache']['count'] = len(bc)
    else:
        results['board_cache']['status'] = 'MISSING'

    print(json.dumps(results, ensure_ascii=False, indent=2))

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()