# -*- coding: utf-8 -*-
"""
data_source.py - 数据源降级工具
当 push2.eastmoney.com 失败时，自动降级到备选数据源

用法:
    from src.data_source import fetch_realtime, fetch_capital_flow
    data = fetch_realtime('sh.600519')  # 自动降级
"""
import ssl, json, time, urllib.request
from typing import Optional, List, Dict, Any

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.eastmoney.com/',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}


# ─────────────────────────────────────────────
# 核心降级请求函数
# ─────────────────────────────────────────────
def fetch_with_fallback(
    primary_url: str,
    fallback_urls: List[str],
    headers: dict = None,
    timeout: int = 10,
    fields: Optional[str] = None,
) -> Optional[str]:
    """
    尝试 primary_url，失败后依次尝试 fallback_urls。
    返回第一个成功的数据（str），全部失败返回 None。
    """
    if headers is None:
        headers = HEADERS

    urls = [primary_url] + fallback_urls
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                data = r.read().decode('utf-8', errors='replace')
                if data and len(data) > 10:
                    return data
        except Exception:
            pass
    return None


# ─────────────────────────────────────────────
# 实时行情（个股）
# 数据源：东方财富 push2（主）→ 腾讯 qt.gtimg.cn（备）
# 返回: dict 或 None
# ─────────────────────────────────────────────
def fetch_realtime(code: str) -> Optional[Dict[str, Any]]:
    """
    获取个股实时行情（5档+最新价+涨跌停状态等）
    
    参数:
        code: 格式 'sh.600519' 或 'sz.002456'
    
    返回:
        {'code': 'sh.600519', 'name': '贵州茅台', 'price': 1215.0, 
         'change_pct': -1.5, 'volume': 1234567, 'amount': 9876543210,
         'high': 1230.0, 'low': 1200.0, 'open': 1220.0,
         'bid1': ..., 'ask1': ..., ...}
        失败返回 None
    """
    # 解析市场代码
    m = code[:2]
    num = code[3:]
    if m == 'sh':
        secid = f'1.{num}'
        tencent_market = f'sh{num}'
    elif m == 'sz':
        secid = f'0.{num}'
        tencent_market = f'sz{num}'
    elif m == 'bj':
        secid = f'0.{num}'
        tencent_market = f'bj{num}'
    else:
        return None

    # 东财 push2 实时行情接口
    primary_url = (
        f'https://push2.eastmoney.com/api/qt/stock/get'
        f'?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f169,f170'
        f'&ut=fa5fd1943c7b386f172d6893dbfba10b'
    )

    # 腾讯实时行情（备选）
    fallback_url = f'https://qt.gtimg.cn/q={tencent_market}'

    # 尝试东财
    data = fetch_with_fallback(primary_url, [], timeout=8)
    
    # 东财失败，降级腾讯
    if data is None:
        data = fetch_with_fallback(fallback_url, [], timeout=8)
        if data is None:
            return None
        return _parse_tencent_realtime(data, code)

    try:
        obj = json.loads(data)
        fields = obj.get('data', {})
        if not fields:
            return None
        return _parse_eastmoney_realtime(fields, code)
    except:
        # JSON 解析失败，降级腾讯
        data2 = fetch_with_fallback(fallback_url, [], timeout=8)
        if data2:
            return _parse_tencent_realtime(data2, code)
        return None


def _parse_eastmoney_realtime(fields: dict, code: str) -> Dict[str, Any]:
    """解析东财 push2 实时行情"""
    return {
        'code': code,
        'name': fields.get('f58', ''),
        'price': fields.get('f43', 0) / 100 if fields.get('f43') else 0,
        'change_pct': fields.get('f170', 0) / 100 if fields.get('f170') else 0,
        'change': fields.get('f169', 0) / 100 if fields.get('f169') else 0,
        'open': fields.get('f46', 0) / 100 if fields.get('f46') else 0,
        'high': fields.get('f44', 0) / 100 if fields.get('f44') else 0,
        'low': fields.get('f45', 0) / 100 if fields.get('f45') else 0,
        'volume': fields.get('f47', 0),  # 成交量（股）
        'amount': fields.get('f48', 0),  # 成交额（元）
        'bid1': fields.get('f50', 0) / 100 if fields.get('f50') else 0,
        'ask1': fields.get('f51', 0) / 100 if fields.get('f51') else 0,
        'up_limit': fields.get('f169', 0) / 100 if fields.get('f169') else 0,  # 涨停价
        'down_limit': 0,
    }


def _parse_tencent_realtime(raw: str, code: str) -> Optional[Dict[str, Any]]:
    """解析腾讯 qt.gtimg.cn 实时行情"""
    try:
        # 格式: v_sh600519="1~name~code~price~change_pct~volume~..."
        if '="' not in raw:
            return None
        line = raw.split('="')[1].strip('";\n')
        parts = line.split('~')
        if len(parts) < 40:
            return None
        price = float(parts[3]) if parts[3] else 0
        yesterday_close = float(parts[4]) if parts[4] else price
        change = price - yesterday_close
        change_pct = (change / yesterday_close * 100) if yesterday_close else 0
        return {
            'code': code,
            'name': parts[1] if len(parts) > 1 else '',
            'price': price,
            'change_pct': change_pct,
            'change': change,
            'open': float(parts[5]) if parts[5] else price,
            'high': float(parts[33]) if parts[33] else price,
            'low': float(parts[34]) if parts[34] else price,
            'volume': int(parts[6]) if parts[6] else 0,
            'amount': float(parts[37]) if parts[37] else 0,
            'bid1': float(parts[9]) if len(parts) > 9 and parts[9] else price,
            'ask1': float(parts[19]) if len(parts) > 19 and parts[19] else price,
        }
    except:
        return None


# ─────────────────────────────────────────────
# 批量实时行情（多只股票）
# 数据源：东财 push2 批量接口（主）→ 腾讯（备）
# 返回: {code: {...}} dict
# ─────────────────────────────────────────────
def fetch_batch_realtime(codes: List[str], timeout: int = 12) -> Dict[str, Dict[str, Any]]:
    """
    批量获取多只股票实时行情。
    自动降级：东财 → 腾讯逐只查询。
    """
    result = {}
    
    if not codes:
        return result

    # 东财批量接口（单次最多约200只，这里用全部codes拼一个请求）
    secids = []
    for code in codes:
        m, n = code[:2], code[3:]
        if m == 'sh':
            secids.append(f'1.{n}')
        elif m == 'sz':
            secids.append(f'0.{n}')
        elif m == 'bj':
            secids.append(f'0.{n}')
    
    primary_url = (
        f'https://push2.eastmoney.com/api/qt/clist/get'
        f'?pn=1&pz=500&po=1&np=1&ut=fa5fd1943c7b386f172d6893dbfba10b'
        f'&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23,m:0+t:80+s:2048'
        f'&fields=f12,f13,f14,f3,f43,f170'
    )
    
    data = fetch_with_fallback(primary_url, [], timeout=timeout)
    
    if data:
        try:
            obj = json.loads(data)
            stocks = obj.get('data', {}).get('diff', [])
            for s in stocks:
                code_num = s.get('f12', '')
                market = 'sh' if str(s.get('f13', '')) == '1' else 'sz'
                code_full = f'{market}.{code_num}'
                result[code_full] = {
                    'code': code_full,
                    'name': s.get('f14', ''),
                    'price': s.get('f43', 0) / 100 if s.get('f43') else 0,
                    'change_pct': s.get('f170', 0) / 100 if s.get('f170') else 0,
                }
            return result
        except:
            pass
    
    # 东财失败，降级腾讯逐只查询（并发限制每批50只）
    BATCH = 50
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def fetch_one(code):
        r = fetch_realtime(code)
        return code, r if r else {}
    
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_one, code): code for code in codes}
        for future in as_completed(futures):
            code, data = future.result()
            if data:
                result[code] = data
    
    return result


# ─────────────────────────────────────────────
# 资金流向（东方财富 f62）
# 主：push2.eastmoney.com → 备：无（资金流没有好的备选，返回None）
# ─────────────────────────────────────────────
def fetch_capital_flow(secid: str) -> Optional[Dict[str, Any]]:
    """
    获取个股资金流向（5日/10日/20日主力净流入）
    secid格式: '1.600519' 或 '0.002456'
    """
    primary_url = (
        f'https://push2.eastmoney.com/api/qt/stock/get'
        f'?secid={secid}&fields=f62,f184&ut=fa5fd1943c7b386f172d6893dbfba10b'
    )
    data = fetch_with_fallback(primary_url, [], timeout=8)
    if data:
        try:
            obj = json.loads(data)
            fields = obj.get('data', {})
            if fields:
                return {
                    'main_net_inflow_5d': fields.get('f62', 0),  # 5日主力净流入
                    'main_net_inflow_10d': fields.get('f184', 0),
                }
        except:
            pass
    return None


# ─────────────────────────────────────────────
# 融资融券数据（东方财富 f47/f48）
# ─────────────────────────────────────────────
def fetch_margin_data(secid: str) -> Optional[Dict[str, Any]]:
    """
    获取融资融券数据
    """
    primary_url = (
        f'https://push2.eastmoney.com/api/qt/stock/get'
        f'?secid={secid}&fields=f47,f48&ut=fa5fd1943c7b386f172d6893dbfba10b'
    )
    data = fetch_with_fallback(primary_url, [], timeout=8)
    if data:
        try:
            obj = json.loads(data)
            fields = obj.get('data', {})
            if fields:
                return {
                    'margin_balance': fields.get('f47', 0),  # 融资余额
                    'short_balance': fields.get('f48', 0),   # 融券余额
                }
        except:
            pass
    return None


# ─────────────────────────────────────────────
# 健康检查：测试主数据源连通性
# 返回: (push2_ok: bool, tencent_ok: bool)
# ─────────────────────────────────────────────
def health_check() -> tuple:
    test_secid = '1.600519'
    primary_url = (
        f'https://push2.eastmoney.com/api/qt/stock/get'
        f'?secid={test_secid}&fields=f43,f58'
    )
    fallback_url = 'https://qt.gtimg.cn/q=sh600519'
    
    push2_ok = fetch_with_fallback(primary_url, [], timeout=6) is not None
    tencent_ok = fetch_with_fallback(fallback_url, [], timeout=6) is not None
    
    return push2_ok, tencent_ok


if __name__ == '__main__':
    print('数据源健康检查...')
    push2_ok, tencent_ok = health_check()
    print(f'  东财 push2: {"✅ 正常" if push2_ok else "❌ 失败"}')
    print(f'  腾讯 qt.gtimg: {"✅ 正常" if tencent_ok else "❌ 失败"}')
    
    # 测试单只股票
    print('\n测试 fetch_realtime("sh.600519"):')
    r = fetch_realtime('sh.600519')
    if r:
        print(f'  名称: {r["name"]}')
        print(f'  现价: {r["price"]}')
        print(f'  涨跌%: {r["change_pct"]:.2f}%')
    else:
        print('  ❌ 获取失败')
