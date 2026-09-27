# -*- coding: utf-8 -*-
"""
新浪备用行情 (Sina Fallback)
===========================
当腾讯行情接口异常时的兜底方案。

用法：
  python sina_fallback.py sh688102          # 查单只
  python sina_fallback.py --all             # 查所有持仓
  python sina_fallback.py --check           # 检查两个接口是否一致
"""
import sys, os, json, urllib.request, re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
OUT_DIR = WORK_DIR / 'out_data'
os.makedirs(OUT_DIR, exist_ok=True)


def to_sina_code(code: str) -> str:
    """转新浪代码格式：sh688102 → sh688102（一致）"""
    raw = code.replace('sh', '').replace('sz', '').replace('.', '').replace('SH', '').replace('SZ', '')
    if raw.startswith('6') or raw.startswith('68'):
        return f'sh{raw}'
    elif raw.startswith('0') or raw.startswith('3'):
        return f'sz{raw}'
    return code


def fetch_tencent(code: str) -> Optional[Dict]:
    """腾讯行情"""
    sina_code = to_sina_code(code)
    url = f'https://qt.gtimg.cn/q={sina_code}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode('gbk', errors='replace')
        parts = raw.split('~')
        if len(parts) < 6:
            return None
        return {
            'name': parts[1],
            'code': parts[2],
            'price': float(parts[3]) if parts[3] else 0,
            'yesterday': float(parts[4]) if parts[4] else 0,
            'chg_pct': float(parts[5]) if parts[5] else 0,
            'high': float(parts[33]) if len(parts) > 33 and parts[33] else 0,
            'low': float(parts[34]) if len(parts) > 34 and parts[34] else 0,
            'volume': float(parts[6]) if len(parts) > 6 and parts[6] else 0,
            'source': 'tencent',
        }
    except:
        return None


def fetch_sina(code: str) -> Optional[Dict]:
    """新浪行情"""
    sina_code = to_sina_code(code)
    url = f'https://hq.sinajs.cn/list={sina_code}'
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode('gbk', errors='replace')
        # 格式: var hq_str_sh688102="名称,开,昨收,现价,高,低,...";
        match = re.search(r'"(.*?)"', raw)
        if not match:
            return None
        parts = match.group(1).split(',')
        if len(parts) < 4:
            return None
        name = parts[0]
        price = float(parts[3]) if parts[3] else 0
        yesterday = float(parts[2]) if parts[2] else 0
        chg_pct = (price - yesterday) / yesterday * 100 if yesterday > 0 else 0
        return {
            'name': name,
            'code': code,
            'price': price,
            'yesterday': yesterday,
            'chg_pct': round(chg_pct, 2),
            'high': float(parts[4]) if len(parts) > 4 and parts[4] else 0,
            'low': float(parts[5]) if len(parts) > 5 and parts[5] else 0,
            'volume': float(parts[8]) if len(parts) > 8 and parts[8] else 0,
            'source': 'sina',
        }
    except:
        return None


def get_price(code: str, prefer: str = 'tencent') -> Optional[Dict]:
    """获取行情，支持自动回退到新浪"""
    if prefer == 'tencent':
        result = fetch_tencent(code)
        if result:
            return result
        # 回退到新浪
        result = fetch_sina(code)
        return result
    else:
        result = fetch_sina(code)
        if result:
            return result
        result = fetch_tencent(code)
        return result


def compare_sources(code: str) -> Dict:
    """对比两个数据源的一致性"""
    t = fetch_tencent(code)
    s = fetch_sina(code)

    result = {
        'code': code,
        'tencent': t,
        'sina': s,
        'match': False,
        'price_diff': 0,
    }

    if t and s:
        diff = abs(t['price'] - s['price'])
        result['price_diff'] = round(diff, 2)
        result['match'] = diff < 0.05  # 5分钱以内算一致
    elif t:
        result['note'] = '新浪不可用'
    elif s:
        result['note'] = '腾讯不可用'
    else:
        result['note'] = '两个接口均不可用'

    return result


def get_holdings() -> List[str]:
    """获取持仓代码"""
    portfolio_path = WORK_DIR / 'data' / 'portfolio.json'
    if not portfolio_path.exists():
        return []
    with open(portfolio_path, 'r', encoding='utf-8') as f:
        pf = json.load(f)
    return [h['code'] for h in pf.get('holdings', [])]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='新浪备用行情')
    parser.add_argument('code', nargs='?', help='股票代码')
    parser.add_argument('--all', action='store_true', help='查所有持仓')
    parser.add_argument('--check', action='store_true', help='对比腾讯/新浪一致性')
    args = parser.parse_args()

    if args.check and args.code:
        result = compare_sources(args.code)
        print(f'\n数据源对比 — {result["code"]}:')
        if result.get('tencent'):
            t = result['tencent']
            print(f'  腾讯: {t["name"]} {t["price"]:.2f} ({t["chg_pct"]:+.2f}%)')
        if result.get('sina'):
            s = result['sina']
            print(f'  新浪: {s["name"]} {s["price"]:.2f} ({s["chg_pct"]:+.2f}%)')
        if result.get('tencent') and result.get('sina'):
            print(f'  价差: {result["price_diff"]:.2f} | 一致: {result["match"]}')

    elif args.all or (not args.code):
        codes = get_holdings()
        if not codes:
            print('当前无持仓')
            sys.exit(0)
        print(f'\n持仓行情 ({datetime.now().strftime("%H:%M")}):')
        for code in codes:
            result = get_price(code)
            if result:
                emoji = '🟢' if result['chg_pct'] >= 0 else '🔴'
                print(f'  {emoji} {result["name"]}({code}): {result["price"]:.2f} ({result["chg_pct"]:+.2f}%) [{result["source"]}]')
            else:
                print(f'  ❌ {code}: 行情获取失败')

    elif args.code:
        result = get_price(args.code)
        if result:
            emoji = '🟢' if result['chg_pct'] >= 0 else '🔴'
            print(f'{emoji} {result["name"]}({result["code"]}): {result["price"]:.2f} ({result["chg_pct"]:+.2f}%) 高{result["high"]:.2f} 低{result["low"]:.2f} 量{result["volume"]:.0f} [{result["source"]}]')
        else:
            print(f'❌ {args.code}: 行情获取失败')