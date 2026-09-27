"""补采缺失的K线数据 - 使用东方财富API"""
import sqlite3, urllib.request, json, time, sys, os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB = r'F:\market_data.db'
conn = sqlite3.connect(DB)

# 获取所有股票代码
all_codes = [r[0] for r in conn.execute('SELECT DISTINCT code FROM daily_k').fetchall()]
print(f'总代码数: {len(all_codes)}')

# 确定缺失日期
missing_dates = ['2026-07-07', '2026-07-08']
for md in missing_dates:
    cnt = conn.execute('SELECT COUNT(*) FROM daily_k WHERE date=?', (md,)).fetchone()[0]
    print(f'{md}: 现有{cnt}条，缺失{len(all_codes)-cnt}只')

conn.close()

def get_history(code, target_date):
    """从东方财富获取指定日期的K线数据"""
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
    except Exception as e:
        return None

# 开始补采
saved = 0
errors = 0

for md in missing_dates:
    conn = sqlite3.connect(DB)
    existing = set(r[0] for r in conn.execute(
        'SELECT code FROM daily_k WHERE date=?', (md,)
    ).fetchall())
    missing = [c for c in all_codes if c not in existing]
    print(f'\n--- {md}: 缺失{len(missing)}只 ---')
    
    for i, code in enumerate(missing):
        result = get_history(code, md)
        if result:
            try:
                conn.execute(
                    'INSERT INTO daily_k (code, date, open, high, low, close, volume) VALUES (?,?,?,?,?,?,?)',
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

print(f'\n总计: 保存{saved}, 错误{errors}')

# 验证
conn = sqlite3.connect(DB)
for md in missing_dates:
    cnt = conn.execute('SELECT COUNT(*) FROM daily_k WHERE date=?', (md,)).fetchone()[0]
    print(f'  {md}: {cnt}条')
conn.close()
