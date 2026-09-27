#!/usr/bin/env python3
"""逐一核查所有数据源接口 - 无emoji版本"""
import urllib.request, json, re, sys

def check(name, func):
    print(f'\n=== {name} ===')
    try:
        result = func()
        if result:
            for line in result:
                print(f'  [OK] {line}')
        else:
            print('  (空结果)')
    except Exception as e:
        print(f'  [FAIL] {e}')

# 1. A股指数
def check_indices():
    r = urllib.request.urlopen('http://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688,sh000300,sh000905,sh000852', timeout=5).read().decode('gbk')
    lines = []
    for l in r.split(';'):
        l = l.strip()
        if not l or 'pv_none' in l:
            continue
        parts = l.split('~')
        if len(parts) >= 32:
            name = parts[1]
            price = parts[3]
            prev = parts[4]
            open_p = parts[5]
            high = parts[33]
            low = parts[34]
            volume = parts[6]
            date = parts[30]
            try: pct = (float(price)-float(prev))/float(prev)*100
            except: pct = 0
            lines.append(f'{name}: {price} ({pct:+.2f}%) 开盘{open_p} 高{high} 低{low} [{date}]')
    return lines

# 2. 外盘美股
def check_us():
    r = urllib.request.urlopen('http://qt.gtimg.cn/q=usDJI,usIXIC,usQQQ', timeout=5).read().decode('gbk')
    lines = []
    for l in r.split(';'):
        l = l.strip()
        if not l or 'pv_none' in l:
            continue
        parts = l.split('~')
        if len(parts) >= 32:
            name = parts[1]
            price = parts[3]
            prev = parts[4]
            date = parts[30]
            try: pct = (float(price)-float(prev))/float(prev)*100
            except: pct = 0
            lines.append(f'{name}: {price} ({pct:+.2f}%) [{date}]')
    return lines

# 3. 港股
def check_hk():
    r = urllib.request.urlopen('http://qt.gtimg.cn/q=hkHSI,hkHSCEI,hkHSCCI', timeout=5).read().decode('gbk')
    lines = []
    for l in r.split(';'):
        l = l.strip()
        if not l or 'pv_none' in l:
            continue
        parts = l.split('~')
        if len(parts) >= 32:
            name = parts[1]
            price = parts[3]
            prev = parts[4]
            try: pct = (float(price)-float(prev))/float(prev)*100
            except: pct = 0
            lines.append(f'{name}: {price} ({pct:+.2f}%)')
    return lines

# 4. A50期货
def check_a50():
    lines = []
    try:
        req = urllib.request.Request('https://hq.sinajs.cn/list=cn_A50', headers={'Referer':'https://finance.sina.com.cn'})
        r = urllib.request.urlopen(req, timeout=5).read().decode('gbk')
        m = re.search(r'"([^"]+)"', r)
        if m:
            parts = m.group(1).split(',')
            if len(parts) >= 2:
                lines.append(f'新浪A50: {parts[0]} {parts[1]}')
        else:
            lines.append(f'原始: {r[:150]}')
    except Exception as e:
        lines.append(f'[FAIL] 新浪A50: {e}')
    for code in ['CN00918', 'CN00Y03', 'CN00Y04']:
        try:
            r = urllib.request.urlopen(f'http://qt.gtimg.cn/q={code}', timeout=3).read().decode('gbk')
            lines.append(f'腾讯{code}: {r[:120]}')
        except:
            pass
    return lines

# 5. 商品期货
def check_futures():
    lines = []
    codes = 'CZCE301,CZCE303,CZCE305,CZCE307,DCE2501,DCE2505,SHFE2501,SHFE2502'
    r = urllib.request.urlopen(f'http://qt.gtimg.cn/q={codes}', timeout=5).read().decode('gbk')
    for l in r.split(';'):
        l = l.strip()
        if not l or 'pv_none' in l:
            continue
        parts = l.split('~')
        if len(parts) >= 32:
            name = parts[1]
            price = parts[3]
            prev = parts[4]
            try: pct = (float(price)-float(prev))/float(prev)*100
            except: pct = 0
            lines.append(f'{name}: {price} ({pct:+.2f}%)')
        elif len(parts) >= 5:
            lines.append(f'[WARN] {parts[1]}: {parts[3]} (字段不足)')
    return lines

# 6. 东财push2
def check_eastmoney_push2():
    lines = []
    indices = [
        ('上证指数', '1.000001'),
        ('深证成指', '1.399001'),
        ('创业板指', '0.399006'),
        ('沪深300', '1.000300'),
        ('中证500', '1.000905'),
    ]
    for name, secid in indices:
        try:
            url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f2,f3,f4'
            r = urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
            d = json.loads(r)
            if d.get('data') and d['data'].get('f2'):
                lines.append(f'{name}: {d["data"]["f2"]} (涨幅{d["data"].get("f3",0)})')
            else:
                lines.append(f'[FAIL] {name}: 返回{d}')
        except Exception as e:
            lines.append(f'[FAIL] {name}: {e.__class__.__name__} {e}')
    return lines

# 7. 东财市场宽度
def check_breadth():
    lines = []
    try:
        url = ('https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=1&po=1&np=1'
               '&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3'
               '&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3')
        r = urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
        m = re.search(r'jQuery\((.+)\)', r)
        if m:
            d = json.loads(m.group(1))
            total = d.get('data', {}).get('total', 0)
            lines.append(f'东财市场宽度: 全市场约{total}只')
        else:
            lines.append(f'[FAIL] 东财宽度: 解析失败')
    except Exception as e:
        lines.append(f'[FAIL] 东财宽度: {e.__class__.__name__} {e}')
    return lines

# 8. akshare板块
def check_akshare_sector():
    lines = []
    try:
        import akshare as ak
        df = ak.stock_sector_spot()
        if df is not None and len(df) > 0:
            df_sorted = df.sort_values('涨跌幅', ascending=False)
            top3 = df_sorted.head(3)
            bot3 = df_sorted.tail(3)
            for _, r in top3.iterrows():
                lines.append(f'强势: {r["板块"]} {r["涨跌幅"]:+.2f}%')
            for _, r in bot3.iterrows():
                lines.append(f'弱势: {r["板块"]} {r["涨跌幅"]:+.2f}%')
        else:
            lines.append('[FAIL] akshare板块: 空结果')
    except Exception as e:
        lines.append(f'[FAIL] akshare板块: {e.__class__.__name__} {e}')
    return lines

# 9. 快讯
def check_news():
    lines = []
    try:
        url = 'https://newsapi.eastmoney.com/kuaixun/v1/getlist_126_ajaxResult_5_1_.html'
        r = urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
        m = re.search(r'ajaxResult=(.+)', r)
        if m:
            d = json.loads(m.group(1))
            for item in d.get('LivesList', [])[:3]:
                lines.append(f'东财: {item.get("title","")[:50]}')
        else:
            lines.append('[FAIL] 东财快讯: 解析失败')
    except Exception as e:
        lines.append(f'[FAIL] 东财快讯: {e}')
    try:
        url = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=3&versionNumber=1.2.4&encode=utf-8'
        r = urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
        d = json.loads(r)
        if d.get('result') and d['result'].get('data'):
            for item in d['result']['data'][:3]:
                lines.append(f'新浪: {item.get("title","")[:50]}')
        else:
            lines.append('[FAIL] 新浪快讯: 空结果')
    except Exception as e:
        lines.append(f'[FAIL] 新浪快讯: {e}')
    return lines

# 10. DB涨停
def check_zt():
    lines = []
    try:
        import sqlite3
        conn = sqlite3.connect(r'F:\market_data.db')
        cols = conn.execute('PRAGMA table_info(daily_k)').fetchall()
        col_names = [c[1] for c in cols]
        lines.append(f'字段: {col_names}')
        latest = conn.execute('SELECT MAX(date) FROM daily_k').fetchone()[0]
        lines.append(f'最新日期: {latest}')
        if 'prev_close' in col_names:
            zt = conn.execute('SELECT COUNT(*) FROM daily_k WHERE date=? AND close/prev_close >= 1.095', (latest,)).fetchone()[0]
            lines.append(f'涨停({latest}): {zt}家')
        elif 'pct_chg' in col_names:
            zt = conn.execute('SELECT COUNT(*) FROM daily_k WHERE date=? AND pct_chg >= 9.5', (latest,)).fetchone()[0]
            lines.append(f'涨停({latest}): {zt}家')
        else:
            lines.append(f'字段无prev_close/pct_chg, 查close/open:')
            sample = conn.execute('SELECT code,close,open,high,low,date FROM daily_k WHERE date=? LIMIT 3', (latest,)).fetchall()
            for row in sample:
                lines.append(f'  {row}')
        conn.close()
    except Exception as e:
        lines.append(f'[FAIL] DB涨停: {e}')
    return lines

# 11. A股期指
def check_csi_futures():
    lines = []
    codes = 'IF0,IC0,IH0,IM0'
    r = urllib.request.urlopen(f'http://qt.gtimg.cn/q={codes}', timeout=5).read().decode('gbk')
    for l in r.split(';'):
        l = l.strip()
        if not l or 'pv_none' in l:
            continue
        parts = l.split('~')
        if len(parts) >= 32:
            name = parts[1]
            price = parts[3]
            prev = parts[4]
            try: pct = (float(price)-float(prev))/float(prev)*100
            except: pct = 0
            lines.append(f'{name}: {price} ({pct:+.2f}%)')
    if not lines:
        lines.append('[WARN] 腾讯A股期货无数据')
    return lines


print('=' * 60)
print(f'数据源核查报告 - {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}')
print('=' * 60)

check('1. A股指数 (腾讯qt.gtimg.cn)', check_indices)
check('2. 外盘美股 (腾讯)', check_us)
check('3. 港股 (腾讯)', check_hk)
check('4. A50期货', check_a50)
check('5. 商品期货 (腾讯)', check_futures)
check('6. 东财push2行情', check_eastmoney_push2)
check('7. 东财市场宽度', check_breadth)
check('8. 板块RPS (akshare)', check_akshare_sector)
check('9. 快讯 (东财+新浪)', check_news)
check('10. DB涨停统计', check_zt)
check('11. A股期指 (腾讯)', check_csi_futures)