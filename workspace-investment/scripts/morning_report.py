# -*- coding: utf-8 -*-
"""
全方位投资早报 - 腾讯API主力（稳定），东财/DB兜底
"""
import requests, json, sys, os, sqlite3, glob, re
from datetime import datetime, date, timedelta

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB = r'F:\market_data.db'
OUT_DATA = os.path.join(WORKSPACE, 'out_data')

def fmt_chg(v):
    return f"+{v:.2f}%" if v >= 0 else f"{v:.2f}%"

def safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default

# ==================== 腾讯API（主力）====================

def tx_quote(codes):
    """腾讯批量行情查询 - 主力接口"""
    try:
        url = f'http://qt.gtimg.cn/q={codes}'
        r = requests.get(url, timeout=6,
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.qq.com'})
        results = {}
        for line in r.text.strip().split(';'):
            line = line.strip()
            if not line or 'pv_none' in line:
                continue
            parts = line.split('~')
            if len(parts) < 32:
                continue
            name = parts[1]
            price = safe_float(parts[3])
            prev_close = safe_float(parts[4])
            open_p = safe_float(parts[5])
            volume = parts[6]
            high = safe_float(parts[33]) if len(parts) > 33 else 0
            low = safe_float(parts[34]) if len(parts) > 34 else 0
            date_str = parts[30] if len(parts) > 30 else ''
            chg_pct = (price - prev_close) / prev_close * 100 if prev_close else 0
            results[parts[2]] = {
                'name': name, 'price': price, 'prev_close': prev_close,
                'open': open_p, 'high': high, 'low': low,
                'volume': volume, 'chg': round(chg_pct, 2), 'date': date_str
            }
        return results
    except Exception as e:
        print(f"[WARN] tx_quote({codes}): {e}")
        return {}

# ==================== 隔夜外盘 ====================

def get_us_markets():
    """隔夜美股 - 腾讯主力，新浪备用"""
    r = tx_quote('usDJI,usIXIC,usQQQ')
    results = {}
    mapping = {'.DJI': 'Dow Jones', '.IXIC': 'Nasdaq', 'QQQ.OQ': 'QQQ'}
    for code, info in r.items():
        for k, n in mapping.items():
            if k in code:
                results[n] = {'curr': info['price'], 'chg': info['chg']}
    if results:
        return results

    # 备用: 新浪
    try:
        r2 = requests.get('https://hq.sinajs.cn/list=gb_ixic,gb_indu,gb_sp500',
            timeout=6, headers={'Referer': 'https://finance.sina.com.cn', 'User-Agent': 'Mozilla/5.0'})
        for line in r2.text.strip().split('\n'):
            m = re.search(r'"([^"]+)"', line)
            if not m: continue
            parts = m.group(1).split(',')
            if len(parts) < 4: continue
            nmap = {'ixic': 'Nasdaq', 'indu': 'Dow Jones', 'sp500': 'S&P 500'}
            for k, n in nmap.items():
                if k in line:
                    results[n] = {'curr': safe_float(parts[1]), 'chg': safe_float(parts[3])}
        return results
    except Exception as e:
        print(f"[WARN] sina us: {e}")
    return results

# ==================== 港股 ====================

def get_hk_markets():
    """港股行情 - 腾讯"""
    r = tx_quote('hkHSI,hkHSCEI,hkHSCCI')
    results = {}
    mapping = {'HSI': '恒生指数', 'HSCEI': '国企指数', 'HSCCI': '红筹指数'}
    for code, info in r.items():
        for k, n in mapping.items():
            if k in code:
                results[n] = {'curr': info['price'], 'chg': info['chg']}
    return results

# ==================== 主要指数 ====================

def get_index_quotes():
    """A股指数 - 腾讯主力，DB兜底"""
    # 腾讯返回code不带前缀，用name做映射
    r = tx_quote('sh000001,sz399001,sz399006,sh000688,sh000300,sh000905,sh000852')
    results = []
    # 腾讯返回的key是纯数字code（如000001），我们用name匹配
    name_map = {
        '上证指数': 'sh000001', '深证成指': 'sz399001', '创业板指': 'sz399006',
        '科创50': 'sh000688', '沪深300': 'sh000300', '中证500': 'sh000905',
        '中证1000': 'sh000852',
    }
    for code, info in r.items():
        for display_name, tx_code in name_map.items():
            if display_name == info.get('name', ''):
                results.append({'name': display_name, 'curr': info['price'], 'chg': info['chg'], 'source': 'tx'})
                break
    if results:
        return results

    # DB兜底
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM daily_k WHERE code='sh.000001'")
        latest_date = cur.fetchone()[0]
        if latest_date:
            for name, code in indices:
                db_code = code[:2] + '.' + code[2:]  # sh000001 -> sh.000001
                cur.execute("SELECT close FROM daily_k WHERE code=? AND date=?", (db_code, latest_date))
                row = cur.fetchone()
                if row:
                    results.append({'name': name, 'curr': float(row[0]), 'chg': 0, 'source': 'DB'})
        conn.close()
    except Exception as e:
        print(f"[WARN] db index: {e}")
    return results

# ==================== 市场宽度 ====================

def get_market_breadth():
    """市场宽度 - 腾讯涨停价跌停价统计"""
    results = {}

    # 方法1: 腾讯全市场统计（通过板块）
    try:
        r = tx_quote('sh000001')
        # 腾讯提供总成交量和成交额，但不提供涨跌家数
        if r:
            results['total'] = '约5000只'
            results['note'] = '腾讯不提供涨跌家数统计'
    except:
        pass

    # 方法2: akshare
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is not None and len(df) > 0:
            up = int((df['涨跌幅'] > 0).sum())
            down = int((df['涨跌幅'] < 0).sum())
            flat = int((df['涨跌幅'] == 0).sum())
            total = len(df)
            zt = int((df['涨跌幅'] >= 9.5).sum())
            zd = int((df['涨跌幅'] <= -9.5).sum())
            return {'up': up, 'down': down, 'flat': flat, 'total': total, 'zt': zt, 'zd': zd}
    except Exception as e:
        print(f"[WARN] akshare breadth: {e}")

    return {'error': '所有接口均失败'}

# ==================== 板块RPS ====================

def get_sector_rps():
    """行业板块RPS - akshare"""
    try:
        import akshare as ak
        df = ak.stock_sector_spot()
        if df is not None and len(df) > 0 and '涨跌幅' in df.columns:
            df = df.sort_values('涨跌幅', ascending=False)
            top5 = [[r['板块'], r['涨跌幅']] for _, r in df.head(5).iterrows()]
            bot5 = [[r['板块'], r['涨跌幅']] for _, r in df.tail(5).iterrows()]
            return {'top': top5, 'bottom': bot5}
    except Exception as e:
        print(f"[WARN] sector rps: {e}")
    return None

# ==================== 个股RPS文件 ====================

def get_latest_rps_file():
    """获取最新RPS数据文件"""
    pattern = os.path.join(OUT_DATA, 'rps_push_*.json')
    files = glob.glob(pattern)
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

# ==================== 持仓价格 ====================

def get_position_prices(positions):
    """持仓实时价格 - 腾讯主力，DB兜底"""
    results = []

    # 腾讯批量查
    codes_str = ','.join([p['code'] for p in positions])
    tx_data = tx_quote(codes_str)

    # DB兜底
    db_prices = {}
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM daily_k WHERE code='sz.000001'")
        latest_date = cur.fetchone()[0]
        if latest_date:
            for pos in positions:
                code = pos['code']
                db_code = f"{code[:2]}.{code[2:]}"
                cur.execute("SELECT close FROM daily_k WHERE code=? AND date=?", (db_code, latest_date))
                row = cur.fetchone()
                if row:
                    db_prices[code] = float(row[0])
        conn.close()
    except:
        pass

    for pos in positions:
        code = pos['code']
        name = pos.get('name', code)
        cost = pos.get('cost', 0) or pos.get('buy_price', 0)
        curr = 0; chg = 0

        # 腾讯
        tx_code = code.replace('.', '')  # sh688556
        info = tx_data.get(tx_code)
        if info:
            curr = info['price']
            chg = info['chg']
            name = info.get('name', name)
        else:
            # 试试其他格式
            for k, v in tx_data.items():
                if code[2:] in k:
                    curr = v['price']
                    chg = v['chg']
                    name = v.get('name', name)
                    break

        # DB兜底
        if not curr and code in db_prices:
            curr = db_prices[code]

        pnl = (curr - cost) / cost * 100 if cost and curr else 0
        results.append({'name': name, 'code': code, 'curr': curr,
                        'cost': cost, 'chg': chg, 'pnl': round(pnl, 2)})
    return results

# ==================== DB辅助 ====================

def get_last_trading_day():
    """DB中最近有数据的交易日"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM daily_k WHERE code='sz.000001'")
        result = cur.fetchone()[0]
        conn.close()
        return result
    except:
        return None

def get_yesterday_zt_count():
    """最近交易日涨停家数（基于close/open>=1.095）"""
    try:
        last_day = get_last_trading_day()
        if not last_day:
            return None, last_day
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        # 涨停: 收盘/开盘 >= 1.095
        cur.execute("SELECT COUNT(*) FROM daily_k WHERE date=? AND close >= open * 1.095", (last_day,))
        count = cur.fetchone()[0] or 0
        conn.close()
        return count, last_day
    except Exception as e:
        print(f"[WARN] zt count: {e}")
        return None, None

# ==================== 快讯 ====================

def get_eastmoney_news(count=8):
    try:
        url = f'https://newsapi.eastmoney.com/kuaixun/v1/getlist_126_ajaxResult_{count}_1_.html'
        r = requests.get(url, timeout=8,
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.eastmoney.com'})
        m = re.search(r'ajaxResult=(.+)', r.text)
        if m:
            return json.loads(m.group(1)).get('LivesList', [])
    except:
        pass
    return []

def get_sina_news(count=6):
    try:
        url = f'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num={count}&versionNumber=1.2.4&encode=utf-8'
        r = requests.get(url, timeout=8)
        d = r.json()
        if d.get('result') and d['result'].get('data'):
            return d['result']['data']
    except:
        pass
    return []

# ==================== 报告生成 ====================

def generate_report():
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d %H:%M')
    weekday = ['周一','周二','周三','周四','周五','周六','周日'][now.weekday()]
    is_weekend = now.weekday() >= 5

    lines = []
    lines.append(f"投资早报 {today_str} {weekday}")
    lines.append("=" * 40)

    # === 隔夜外盘 ===
    lines.append("\n【隔夜外盘】")
    us = get_us_markets()
    if us:
        for name, data in us.items():
            lines.append(f"  {name}: {fmt_chg(data['chg'])}")
    else:
        lines.append("  暂无数据")

    # === 港股 ===
    lines.append("\n【港股】")
    hk = get_hk_markets()
    if hk:
        for name, data in hk.items():
            lines.append(f"  {name}: {fmt_chg(data['chg'])}")
    else:
        lines.append("  暂无数据")

    # === A股指数 ===
    lines.append("\n【A股指数（昨日收盘）】")
    indices = get_index_quotes()
    if indices:
        row = []
        for idx in indices:
            src = f"[{idx.get('source','实时')}]" if 'source' in idx else ""
            row.append(f"{idx['name']} {fmt_chg(idx['chg'])}")
            if len(row) == 4:
                lines.append("  " + "  ".join(row))
                row = []
        if row:
            lines.append("  " + "  ".join(row))
    else:
        lines.append("  暂无数据")

    # === 市场宽度 ===
    lines.append("\n【市场宽度】")
    breadth = get_market_breadth()
    if breadth and 'error' not in breadth:
        if breadth.get('up') is not None:
            lines.append(f"  上涨 {breadth['up']} / 下跌 {breadth['down']} / 平盘 {breadth['flat']}")
            lines.append(f"  涨停 {breadth['zt']} / 跌停 {breadth['zd']}")
        elif breadth.get('note'):
            lines.append(f"  {breadth['note']}")
    else:
        lines.append("  暂无数据（盘前未开盘）")

    # === 板块RPS ===
    lines.append("\n【板块RPS】")
    sector = get_sector_rps()
    if sector and 'error' not in sector:
        lines.append("  强势板块:")
        for name, chg in sector.get('top', [])[:3]:
            lines.append(f"    {name} {fmt_chg(chg)}")
        lines.append("  弱势板块:")
        for name, chg in sector.get('bottom', [])[:3]:
            lines.append(f"    {name} {fmt_chg(chg)}")
    else:
        lines.append("  暂无数据")

    # === 个股RPS ===
    lines.append("\n【个股RPS TOP10】")
    rps_data = get_latest_rps_file()
    if rps_data:
        rps5 = rps_data.get('rps5') or []
        rps20 = rps_data.get('rps20') or []
        if rps5 or rps20:
            lines.append("  [5日强势]")
            for i, item in enumerate(rps5[:5], 1):
                name = item.get('name', item.get('code', ''))
                code = item.get('code', '')
                chg = item.get('return_pct', 0)
                rps_val = item.get('rps', 0)
                lines.append(f"    {i}. {name}({code}) +{chg:.1f}% RPS={rps_val:.0f}")
            lines.append("  [20日强势]")
            for i, item in enumerate(rps20[:5], 1):
                name = item.get('name', item.get('code', ''))
                code = item.get('code', '')
                chg = item.get('return_pct', 0)
                rps_val = item.get('rps', 0)
                lines.append(f"    {i}. {name}({code}) +{chg:.1f}% RPS={rps_val:.0f}")
        else:
            lines.append("  RPS数据为空（16:10后生成）")
    else:
        lines.append("  暂无数据")

    # === 持仓监控 ===
    lines.append("\n【持仓监控】")
    portfolio_file = os.path.join(WORKSPACE, 'data', 'portfolio.json')
    portfolio = None
    if os.path.exists(portfolio_file):
        try:
            with open(portfolio_file, 'r', encoding='utf-8') as f:
                portfolio = json.load(f)
        except:
            pass
    if portfolio and 'holdings' in portfolio:
        positions = get_position_prices(portfolio['holdings'])
        if positions:
            for pos in positions:
                chg_sign = '+' if pos['chg'] >= 0 else ''
                pnl_sign = '+' if pos['pnl'] >= 0 else ''
                lines.append(
                    f"  {pos['name']}({pos['code']}) "
                    f"现价{pos['curr']:.2f} {chg_sign}{pos['chg']:.2f}% "
                    f"成本{pos['cost']:.2f} {pnl_sign}{pos['pnl']:.2f}%"
                )
        else:
            lines.append("  获取失败")
    else:
        lines.append("  暂无持仓数据")

    # === 涨停统计 ===
    zt_count, zt_date = get_yesterday_zt_count()
    if zt_count is not None:
        lines.append(f"\n【涨停统计 ({zt_date})】: {zt_count}家")
        if zt_count < 20:
            lines.append("  情绪低迷，谨慎开仓")
        elif zt_count > 80:
            lines.append("  情绪活跃，关注主线机会")
        else:
            lines.append("  情绪一般，正常应对")
    else:
        lines.append("\n【涨停统计】暂无数据")

    # === 快讯 ===
    lines.append("\n【快讯摘要】")
    em_news = get_eastmoney_news(5)
    sina_news = get_sina_news(5)
    news_count = 0
    for item in em_news[:4]:
        title = item.get('title', '')
        if title:
            lines.append(f"  - {title[:50]}")
            news_count += 1
    for item in sina_news[:3]:
        title = item.get('title', '')
        if title:
            lines.append(f"  - {title[:50]}")
            news_count += 1
    if news_count == 0:
        lines.append("  暂无最新快讯")

    # === 操作参考 ===
    lines.append("\n【今日操作参考】")
    signal = "待观察"
    if zt_count is not None:
        if zt_count < 20:
            lines.append("  - 市场情绪低迷，涨停家数偏少，短线降低频率")
        elif zt_count > 60:
            lines.append("  - 市场情绪活跃，涨停充足，可适当参与主线")
        else:
            lines.append("  - 市场情绪一般，精选个股为主")
    lines.append(f"  - 大盘信号: {signal}")
    top_sector = (sector.get('top', [['']*2]*3)[0][0] if sector and sector.get('top') else '暂无')
    lines.append(f"  - 重点关注: {top_sector}")

    lines.append("\n" + "=" * 40)
    result = "\n".join(lines)
    print(result)
    return result

if __name__ == '__main__':
    generate_report()