"""快速补采K线数据 - 批量从腾讯获取"""
import sqlite3, requests, time, sys, os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB = r'F:\market_data.db'
BATCH = 100

# 获取所有股票代码
conn = sqlite3.connect(DB)
all_codes = [r[0] for r in conn.execute('SELECT DISTINCT code FROM daily_k').fetchall()]
print(f'总代码数: {len(all_codes)}')

# 确定缺失日期
missing_dates = ['2026-07-07', '2026-07-08']
for md in missing_dates:
    cnt = conn.execute("SELECT COUNT(*) FROM daily_k WHERE date=?", (md,)).fetchone()[0]
    print(f'{md}: 现有{cnt}条')

conn.close()

def db_to_tencent(code):
    if code.startswith('sh.'): return 'sh' + code[3:]
    elif code.startswith('sz.'): return 'sz' + code[3:]
    elif code.startswith('bj.'): return 'bj' + code[3:]
    return code

def parse_tencent_realtime(line):
    """解析腾讯实时行情单行"""
    if '="' not in line: return None
    try:
        parts = line.split('="')[1].strip('";\n').split('~')
        if len(parts) < 35 or not parts[3]: return None
        raw = parts[0]
        prefix_map = {'51': 'sz', '1': 'sh', '100': 'bj'}
        prefix = prefix_map.get(raw, '')
        code_num = parts[2] if len(parts) > 2 else ''
        if not code_num or len(code_num) < 6: return None
        code_db = ('sz.' if prefix == 'sz' else ('sh.' if prefix == 'sh' else 'bj.')) + code_num
        close = float(parts[3]) if parts[3] else 0
        open_p = float(parts[5]) if parts[5] else close
        high = float(parts[33]) if parts[33] else close
        low = float(parts[34]) if parts[34] else close
        vol = int(parts[6]) if parts[6] else 0
        return {'code': code_db, 'close': close, 'open': open_p, 'high': high, 'low': low, 'volume': vol}
    except: return None

# 腾讯只支持实时数据，不支持历史数据
# 改用东方财富API获取历史K线
def get_history_from_eastmoney(code, target_date):
    """从东方财富获取指定日期的K线数据"""
    import urllib.request
    import json
    
    # 转换代码格式
    if code.startswith('sh.'):
        secid = '1.' + code[3:]
    elif code.startswith('sz.'):
        secid = '0.' + code[3:]
    else:
        return None
    
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&beg={target_date.replace("-", "")}&end=20991231&lmt=1'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            klines = data.get('data', {}).get('klines', [])
            for kl in klines:
                parts = kl.split(',')
                if parts[0] == target_date:
                    return {
                        'date': target_date,
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5])
                    }
            return None
    except:
        return None

# 开始补采
saved = 0
errors = 0

for md in missing_dates:
    conn = sqlite3.connect(DB)
    existing = set(r[0] for r in conn.execute(
        "SELECT code FROM daily_k WHERE date=?", (md,)
    ).fetchall())
    missing = [c for c in all_codes if c not in existing]
    print(f'\n--- {md}: 缺失{len(missing)}只 ---')
    
    for i, code in enumerate(missing):
        result = get_history_from_eastmoney(code, md)
        if result:
            try:
                conn.execute(
                    "INSERT INTO daily_k (code, date, open, high, low, close, volume) VALUES (?,?,?,?,?,?,?)",
                    (code, md, result['open'], result['high'], result['low'], result['close'], result['volume'])
                )
                saved += 1
            except Exception as e:
                errors += 1
        else:
            errors += 1
        
        if (i + 1) % 500 == 0:
            conn.commit()
            print(f'  进度: {i+1}/{len(missing)}, 已保存{saved}')
        
        time.sleep(0.02)  # 避免限流
    
    conn.commit()
    conn.close()
    print(f'{md}: 完成 (保存{saved})')

print(f'\n总计: 处理{sum(len([c for c in all_codes if c not in set()]) for _ in missing_dates)}, 保存{saved}, 错误{errors}')

# 验证
conn = sqlite3.connect(DB)
for md in missing_dates:
    cnt = conn.execute("SELECT COUNT(*) FROM daily_k WHERE date=?", (md,)).fetchone()[0]
    print(f'  {md}: {cnt}条')
conn.close()
