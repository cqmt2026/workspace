"""
持仓数据获取 - 供 holding_alert.py 和 daily_decision_report.py 共用
统一从 data/portfolio.json 读取真实持仓,不再硬编码
"""
import sys, os, json, urllib.request, sqlite3
from datetime import datetime

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB = r"F:\market_data.db"
PORTFOLIO_PATH = os.path.join(WORKSPACE, 'data', 'portfolio.json')


def _load_portfolio():
    """从 portfolio.json 读取真实持仓"""
    if not os.path.exists(PORTFOLIO_PATH):
        return []
    with open(PORTFOLIO_PATH, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('holdings', [])


def _code_to_db_code(code):
    """sh688556 -> sh.688556, sz300034 -> sz.300034
    兼容两种格式：sh688102 或 sh.688102
    """
    code = code.strip().lower()
    # 已带点格式，直接返回
    if '.' in code:
        return code
    # 前缀格式
    if code.startswith('sh'):
        return 'sh.' + code[2:]
    if code.startswith('sz'):
        return 'sz.' + code[2:]
    # 纯数字代码
    if code.startswith('6'):
        return 'sh.' + code
    return 'sz.' + code


def enrich_holdings():
    """从 portfolio.json 读取持仓,补充实时价格+MA+场景判断"""
    holdings = _load_portfolio()
    if not holdings:
        return []

    codes = [h['code'] for h in holdings]
    snap = get_realtime(codes)
    result = []

    for h in holdings:
        code = h['code']
        db_code = _code_to_db_code(code)
        rt = snap.get(code, {})
        ma5, ma10, ma20 = get_ma_levels(db_code)

        entry_price = h.get('buy_price', h.get('cost', 0))
        current_price = rt.get('price', h.get('current_price', entry_price))
        prev_price = rt.get('prev', entry_price)

        pnl = round((current_price - entry_price) * h.get('shares', 0), 2)
        pnl_pct = round((current_price - entry_price) / entry_price * 100, 2) if entry_price else 0

        chg_pct = rt.get('chg_pct', 0)

        trend = '未知'
        if ma5 and current_price:
            if current_price > ma5:
                trend = '多头'
            elif current_price < ma5 * 0.95:
                trend = '空头'
            else:
                trend = '震荡'

        # 止损线
        stop_5 = h.get('stop_loss_5', round(entry_price * 0.95, 2))
        stop_15 = h.get('stop_loss_15', round(entry_price * 0.85, 2))

        alert_price = rt.get('high', current_price)
        key_support = rt.get('low', current_price)

        signal = ''
        if current_price <= stop_5:
            signal = '🚨止损线'
        elif current_price <= stop_15:
            signal = '🔴深度止损'

        result.append({
            'code': code,
            'db_code': db_code,
            'name': h.get('name', ''),
            'cost': entry_price,
            'shares': h.get('shares', 0),
            'price': current_price,
            'prev': prev_price,
            'chg': round(chg_pct, 2),
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'turnover': rt.get('turnover', 0),
            'volume': rt.get('volume', 0),
            'high': rt.get('high', current_price),
            'low': rt.get('low', current_price),
            'stop_loss': stop_5,
            'alert_price': alert_price,
            'key_support': key_support,
            'trend': trend,
            'signal': signal,
            'logic': '',
        })

    return result


def get_ma_levels(db_code):
    """从统一接口获取MA5/MA10"""
    try:
        from scripts.data_api import DataAPI
        klines = DataAPI.get_kline(db_code, days=20)
        if len(klines) < 5:
            return None, None, None
        closes = [k['close'] for k in klines]
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10
        return round(ma5, 2), round(ma10, 2), round(ma20, 2)
    except:
        return None, None, None


def _strip_code(code):
    """sz002805 -> 002805, sh600186 -> 600186"""
    return code[2:] if len(code) > 6 else code


def get_realtime(codes):
    """腾讯实时行情"""
    qt = ','.join(codes)
    url = f'https://qt.gtimg.cn/q={qt}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=8)
    raw = resp.read().decode('gbk')
    result = {}
    for line in raw.strip().split('\n'):
        if '~' not in line:
            continue
        p = line.split('~')
        if len(p) < 40:
            continue
        sym = p[2]
        price = float(p[3]) if p[3] else 0
        prev = float(p[4]) if p[4] else price
        chg_pct = round((price - prev) / prev * 100, 2) if prev else 0
        result[sym] = {
            'price': price,
            'prev': prev,
            'chg_pct': chg_pct,
            'high': float(p[33]) if p[33] else price,
            'low': float(p[34]) if p[34] else price,
            'turnover': float(p[38]) if p[38] else 0,
            'volume': float(p[36]) if p[36] else 0,
        }
    return result


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    holdings = enrich_holdings()
    print(f"{'名称':<10}{'现价':>7}{'今日':>7}{'浮盈':>7}{'MA5':>7}{'MA10':>7}{'趋势':<6}{'场景'}")
    print("-" * 75)
    for h in holdings:
        scenarios = h.get('scenarios', [])
        print(f"{h['name']:<10}{h.get('price', 0):>7.2f}{h.get('chg', 0):>+6.1f}%{h.get('pnl', 0):>+7.2f}" 
              f"{str(h.get('ma5') or 'N/A'):>7}{str(h.get('ma10') or 'N/A'):>7}" 
              f"{h.get('trend', '未知'):<6}{', '.join(scenarios) if scenarios else '正常'}")
