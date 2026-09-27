"""
批量更新DB到今日收盘数据（使用腾讯qt.gtimg.cn）
"""
import requests, sqlite3, json, time, os
from datetime import datetime, date

DB = r'F:\market_data.db'
BATCH = 80
# 自动获取最近交易日（周六/周日用周五）
def get_latest_trading_day():
    today = date.today()
    weekday = today.weekday()  # Mon=0, Sun=6
    if weekday == 5:  # 周六
        return (today - __import__('datetime').timedelta(days=1)).strftime('%Y-%m-%d')
    elif weekday == 6:  # 周日
        return (today - __import__('datetime').timedelta(days=2)).strftime('%Y-%m-%d')
    else:
        return today.strftime('%Y-%m-%d')

TODAY = get_latest_trading_day()

print(f'开始更新 | {datetime.now().strftime("%H:%M:%S")}')

# 从DB获取所有股票代码
conn = sqlite3.connect(DB)
df_codes = conn.execute('SELECT DISTINCT code FROM daily_k').fetchall()
conn.close()
all_codes = [r[0] for r in df_codes]
print(f'DB股票: {len(all_codes)}只')

def db_to_tencent(code):
    if code.startswith('sh.'): return 'sh' + code[3:]
    elif code.startswith('sz.'): return 'sz' + code[3:]
    elif code.startswith('bj.'): return 'bj' + code[3:]
    return code

def parse_tencent_kline(line):
    """解析腾讯单行，返回(code_db, open, close, high, low, volume)"""
    if '="' not in line: return None
    try:
        parts = line.split('="')[1].strip('";\n').split('~')
        if len(parts) < 35 or not parts[3]: return None
        raw = parts[0]
        # 解析市场前缀
        prefix_map = {'51': 'sz', '1': 'sh', '100': 'bj'}
        prefix = prefix_map.get(raw, '')
        code_num = parts[2] if len(parts) > 2 else ''
        if not code_num or len(code_num) < 6: return None
        code_db = ('sz.' if prefix == 'sz' else ('sh.' if prefix == 'sh' else 'bj.')) + code_num
        close = float(parts[3]) if parts[3] else 0
        prev = float(parts[4]) if parts[4] else close
        open_p = float(parts[5]) if parts[5] else close
        high = float(parts[33]) if parts[33] else close
        low = float(parts[34]) if parts[34] else close
        vol = int(parts[6]) if parts[6] else 0
        return {'code': code_db, 'open': open_p, 'close': close, 'high': high, 'low': low, 'volume': vol}
    except: return None

# 腾讯代码
tencent_codes = [db_to_tencent(c) for c in all_codes]

# 批量获取
updated = []
failed = []
total = len(tencent_codes)

for i in range(0, total, BATCH):
    batch = tencent_codes[i:i+BATCH]
    url = f'https://qt.gtimg.cn/q={",".join(batch)}'
    batch_ok = False
    for retry in range(3):
        try:
            r = requests.get(url, timeout=15)
            text = r.text.strip()
            # 检查返回是否为空或错误
            if not text or 'failed' in text.lower():
                raise Exception('Empty or error response')
            lines = text.split('\n')
            success_count = 0
            for line in lines:
                d = parse_tencent_kline(line)
                if d:
                    updated.append(d)
                    success_count += 1
            if success_count < len(batch) * 0.5:
                raise Exception(f'Only {success_count}/{len(batch)} parsed')
            batch_ok = True
            break
        except Exception as e:
            if retry < 2:
                time.sleep(2 * (retry + 1))
            else:
                failed.extend(batch)
                print(f'  Batch {i//BATCH} failed after 3 retries: {e}')
    time.sleep(0.3)
    if (i // BATCH) % 10 == 0:
        pct = i * 100 // total if total > 0 else 0
        print(f'进度: {i}/{total} ({pct}%) | 已获取: {len(updated)}')

print(f'获取成功: {len(updated)}只 | 失败: {len(failed)}只')

if not updated:
    print('无数据，更新失败')
    exit()

# 写入DB（INSERT OR REPLACE）
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 先删除今日已有记录（防止重复）
cur.execute(f"DELETE FROM daily_k WHERE date=?", (TODAY,))
print(f'删除今日旧数据: {cur.rowcount}条')

inserted = 0
for d in updated:
    try:
        cur.execute(
            f"INSERT OR REPLACE INTO daily_k (code, date, open, close, high, low, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (d['code'], TODAY, d['open'], d['close'], d['high'], d['low'], d['volume'])
        )
        inserted += 1
    except Exception as e:
        print(f'写入失败 {d["code"]}: {e}')

conn.commit()
conn.close()

print(f'写入成功: {inserted}条 | {datetime.now().strftime("%H:%M:%S")}')

# 验证
conn = sqlite3.connect(DB)
latest = conn.execute(f"SELECT code, date, close FROM daily_k WHERE date='{TODAY}' LIMIT 5").fetchall()
conn.close()
print(f'\n验证今日数据:')
for row in latest:
    print(f'  {row}')