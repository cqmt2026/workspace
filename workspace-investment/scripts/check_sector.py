import json, os, sqlite3

cache = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\stock_board_cache.json'
if os.path.exists(cache):
    with open(cache, encoding='utf-8') as f:
        d = json.load(f)
    print(f'Cache keys: {len(d)}')
    print(f'Sample keys: {list(d.keys())[:5]}')
else:
    print('Cache file NOT FOUND!')

rps_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\rps_history'
if os.path.exists(rps_dir):
    files = sorted([f for f in os.listdir(rps_dir) if f.startswith('RPS_board_') and f.endswith('.json')])
    print(f'RPS files: {len(files)}')
    if files:
        print(f'Latest: {files[-1]}')
        with open(os.path.join(rps_dir, files[-1]), encoding='utf-8') as f:
            data = json.load(f)
        rps_data = data.get('rps_data', [])
        print(f'RPS data entries: {len(rps_data)}')
else:
    print('RPS dir NOT FOUND!')

conn = sqlite3.connect(r'F:\market_data.db')
latest = conn.execute('SELECT MAX(date) FROM daily_k').fetchone()[0]
print(f'Latest date: {latest}')
rows = conn.execute("SELECT COUNT(*) FROM daily_k WHERE date=?", (latest,)).fetchone()
print(f'Codes on {latest}: {rows[0]}')
if isinstance(d, dict):
    board_codes = set()
    for code in d:
        v = d[code]
        if v and isinstance(v, str):
            board_codes.add(v)
    print(f'Unique boards mapped: {len(board_codes)}')
    print(f'Codes with board: {sum(1 for v in d.values() if v and isinstance(v, str))}/{len(d)}')
conn.close()
