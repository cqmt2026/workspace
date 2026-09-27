# -*- coding: utf-8 -*-
"""从腾讯批量补采缺失的K线数据（7/1, 7/7, 7/8）"""
import sqlite3, urllib.request, re, time, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r'F:\market_data.db'
conn = sqlite3.connect(DB)

# 1. 确定需要补采的日期和代码
missing_dates = ['2026-07-01', '2026-07-07', '2026-07-08']
all_codes = [r[0] for r in conn.execute("SELECT DISTINCT code FROM daily_k ORDER BY code").fetchall()]
print(f'总代码数: {len(all_codes)}')

# 2. 对每个缺失日期，找哪些代码需要补采
def get_missing_codes(date):
    existing = set(r[0] for r in conn.execute(
        "SELECT code FROM daily_k WHERE date=?", (date,)
    ).fetchall())
    return [c for c in all_codes if c not in existing]

for md in missing_dates:
    mc = get_missing_codes(md)
    print(f'  {md}: 缺失{len(mc)}只')

# 3. 用腾讯实时接口批量获取数据
# 腾讯接口格式: https://qt.gtimg.cn/q=sh600845,sz300593,...
# 但我们需要历史数据，用另一个接口

# 方案：用update_today_kline.py的逻辑，但它只能查最近交易日
# 我们需要查特定日期的历史数据

# 尝试腾讯历史K线接口（不同格式）
def get_history_kline(tencent_code, date_target):
    """从腾讯获取指定日期的历史K线"""
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_code},day,30,qfq'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.qq.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode('utf-8')
            # 解析格式: v_sh600845=["sh600845","数据名",["daydata":["20260709,19.25,20.36,18.66,20.19,470211,..."]]]
            pattern = r'"(\d{8}),([\d.]+),([\d.]+),([\d.]+),([\d.]+),([\d.]+)'
            matches = re.findall(pattern, text)
            if not matches:
                return None
            
            target = date_target.replace('-', '')
            for m in matches:
                if m[0] == target:
                    return {
                        'date': date_target,
                        'open': float(m[1]),
                        'high': float(m[2]),
                        'low': float(m[3]),
                        'close': float(m[4]),
                        'volume': float(m[5]),
                    }
            return None
    except:
        return None

# 4. 测试单只股票
test_code = 'sh600845'
for md in missing_dates:
    result = get_history_kline(test_code, md)
    print(f'测试 {test_code} {md}: {result}')

print('\n开始批量补采...')
total = 0
saved = 0
errors = 0

# 遍历每个缺失日期
for md in missing_dates:
    mc = get_missing_codes(md)
    if not mc:
        print(f'\n{md}: 无需补采')
        continue
    
    print(f'\n--- {md} (缺失{len(mc)}只) ---')
    for i, code_db in enumerate(mc):
        # 转换为腾讯代码格式
        if code_db.startswith('sh.'):
            tc = 'sh' + code_db[3:]
        elif code_db.startswith('sz.'):
            tc = 'sz' + code_db[3:]
        elif code_db.startswith('bj.'):
            tc = 'bj' + code_db[3:]
        else:
            tc = code_db
        
        result = get_history_kline(tc, md)
        if result:
            try:
                conn.execute(
                    "INSERT INTO daily_k (code, date, open, high, low, close, volume) VALUES (?,?,?,?,?,?,?)",
                    (code_db, md, result['open'], result['high'], result['low'], result['close'], result['volume'])
                )
                saved += 1
            except Exception as e:
                errors += 1
        else:
            errors += 1
        
        total += 1
        if total % 500 == 0:
            conn.commit()
            print(f'  进度: {total}, 已保存{saved}')
        
        time.sleep(0.01)  # 避免限流
    
    conn.commit()
    print(f'  {md}: 完成 (保存{saved})')

print(f'\n总计: 处理{total}, 保存{saved}, 错误{errors}')

# 5. 验证
print('\n=== 补采后验证 ===')
for md in missing_dates:
    cnt = conn.execute("SELECT COUNT(*) FROM daily_k WHERE date=?", (md,)).fetchone()[0]
    print(f'  {md}: {cnt}条')

conn.close()