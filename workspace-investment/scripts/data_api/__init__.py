# -*- coding: utf-8 -*-
"""
统一数据接口层 — 封装所有外部数据源

设计原则：
  1. 所有数据通过此模块获取，不直接调用API
  2. 统一返回格式：code=标准化格式，date=YYYY-MM-DD
  3. 降级策略统一：RAISE(关键) / SKIP(非关键)，不允许旧数据填充
  4. 每次调用记录日志

用法:
    from scripts.data_api import DataAPI
    api = DataAPI()
    price = api.get_realtime('sh688102')
    kline = api.get_kline('sz300750', days=60)
"""
import os, sys, json, sqlite3, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from .standardize import normalize_code, normalize_date, compact_date

# 路径常量
DB_PATH = r'F:\market_data.db'
FACTORS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'factors.db')

# 日志
_log_events = []


def _log(source: str, action: str, detail: str = ''):
    """记录数据访问事件"""
    _log_events.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': source,
        'action': action,
        'detail': detail,
    })
    # 只保留最近200条
    if len(_log_events) > 200:
        _log_events[:] = _log_events[-200:]


class DataAPI:
    """统一数据接口"""

    # ── 实时行情 ──────────────────────────────

    @staticmethod
    def get_realtime(codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取实时行情（腾讯API）

        返回: {code: {'price': float, 'chg_pct': float, 'volume': float, 'amount': float}}
        """
        if isinstance(codes, str):
            codes = [codes]

        # 标准化code为腾讯API格式（sh600001 / sz300001）
        tengxun_codes = []
        # code_map: tx_code(如sh688556) -> std_code(如sh.688556)
        # 同时也建一个纯数字映射: 688556 -> sh.688556
        code_map = {}
        code_map_digits = {}
        import re
        for c in codes:
            std = normalize_code(c)
            # 从 sh.600001 提取 sh600001（腾讯API需要前缀）
            m = re.match(r'^([a-z]+)\.(\d{6})$', std)
            if m:
                tx_code = m.group(1) + m.group(2)
                digits = m.group(2)
            else:
                tx_code = std
                digits = std
            tengxun_codes.append(tx_code)
            code_map[tx_code] = std
            code_map_digits[digits] = std

        try:
            url = f'https://qt.gtimg.cn/q={",".join(tengxun_codes)}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=8)
            raw = resp.read().decode('gbk')

            result = {}
            for line in raw.strip().split('\n'):
                if '~' not in line:
                    continue
                p = line.split('~')
                if len(p) < 5:
                    continue
                # 腾讯返回格式: v_sh688556=...~
                # p[2]是代码（纯数字），用code_map_digits还原标准格式
                digits = p[2]
                std_code = code_map_digits.get(digits, digits)
                price = float(p[3]) if p[3] else 0
                prev_close = float(p[4]) if p[4] else price
                chg_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
                result[std_code] = {
                    'price': price,
                    'chg_pct': chg_pct,
                    'volume': float(p[6]) if len(p) > 6 and p[6] else 0,
                    'amount': float(p[37]) if len(p) > 37 and p[37] else 0,
                    'name': p[1] if len(p) > 1 else '',
                    'open': float(p[5]) if len(p) > 5 and p[5] else 0,
                    'high': float(p[33]) if len(p) > 33 and p[33] else 0,
                    'low': float(p[34]) if len(p) > 34 and p[34] else 0,
                    'prev_close': prev_close,
                }
            _log('tencent', 'get_realtime', f'{len(codes)}只, {len(result)}只有效')
            return result
        except Exception as e:
            _log('tencent', 'get_realtime_error', str(e))
            raise  # RAISE — 关键数据源

    @staticmethod
    def get_index(index_code: str) -> Optional[Dict[str, Any]]:
        """
        获取指数行情

        输入: 'sh000001' / 'sz399967' 等（不带点）
        返回: {'price': float, 'chg_pct': float, 'name': str}
        """
        try:
            url = f'https://qt.gtimg.cn/q={index_code}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=8)
            raw = resp.read().decode('gbk')

            for line in raw.strip().split('\n'):
                if '~' not in line:
                    continue
                p = line.split('~')
                if len(p) < 5:
                    continue
                price = float(p[3]) if p[3] else 0
                prev = float(p[4]) if p[4] else price
                chg = round((price - prev) / prev * 100, 2) if prev else 0
                return {
                    'price': price,
                    'chg_pct': chg,
                    'name': p[1] if len(p) > 1 else '',
                    'prev_close': prev,
                }
            return None
        except Exception as e:
            _log('tencent', 'get_index_error', str(e))
            return None  # SKIP — 非关键

    # ── K线数据 ───────────────────────────────

    @staticmethod
    def get_kline(code: str, days: int = 60, end_date: str = None) -> List[Dict]:
        """
        从DB获取K线数据

        返回: [{'date': str, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': float}, ...]
        """
        std_code = normalize_code(code)
        if not os.path.exists(DB_PATH):
            _log('db', 'get_kline_error', f'DB不存在: {DB_PATH}')
            return []

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        if end_date:
            rows = c.execute(
                "SELECT date, open, high, low, close, volume FROM daily_k "
                "WHERE code=? AND date<=? ORDER BY date DESC LIMIT ?",
                (std_code, end_date, days)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT date, open, high, low, close, volume FROM daily_k "
                "WHERE code=? ORDER BY date DESC LIMIT ?",
                (std_code, days)
            ).fetchall()

        conn.close()

        def _sf(v):
            if isinstance(v, str):
                v = v.strip()
            try:
                return float(v) if v else 0.0
            except (ValueError, TypeError):
                return 0.0

        result = []
        for r in reversed(rows):
            result.append({
                'date': r[0],
                'open': _sf(r[1]),
                'high': _sf(r[2]),
                'low': _sf(r[3]),
                'close': _sf(r[4]),
                'volume': _sf(r[5]),
            })
        return result

    @staticmethod
    def get_trading_dates(count: int = 120, end_date: str = None) -> List[str]:
        """获取最近的交易日列表"""
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if end_date:
            rows = c.execute(
                "SELECT DISTINCT date FROM daily_k WHERE date<=? ORDER BY date DESC LIMIT ?",
                (end_date, count)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT DISTINCT date FROM daily_k ORDER BY date DESC LIMIT ?",
                (count,)
            ).fetchall()
        conn.close()
        return [r[0] for r in reversed(rows)]

    @staticmethod
    def get_last_trading_day() -> Optional[str]:
        """获取最近一个交易日"""
        dates = DataAPI.get_trading_dates(count=1)
        return dates[-1] if dates else None

    @staticmethod
    def get_prev_trading_day(date_str: str) -> Optional[str]:
        """获取指定日期之前的交易日"""
        dates = DataAPI.get_trading_dates(count=120, end_date=date_str)
        if len(dates) >= 2:
            return dates[-2]
        return None

    # ── 涨停数据 ──────────────────────────────

    @staticmethod
    def get_zt_stocks(trade_date: str) -> List[Dict]:
        """获取某日涨停股票列表"""
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 兼容两种日期格式
        rows = c.execute(
            "SELECT code, name FROM daily_zt WHERE trade_date=? OR trade_date=?",
            (trade_date, trade_date.replace('-', ''))
        ).fetchall()
        conn.close()
        return [{'code': normalize_code(r[0]), 'name': r[1]} for r in rows]

    # ── 涨停K线 ──────────────────────────────

    @staticmethod
    def get_zt_kline(trade_date: str) -> List[Dict]:
        """获取某日涨停K线"""
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        rows = c.execute(
            "SELECT code, name, date, open, high, low, close, volume FROM zt_kline WHERE trade_date=?",
            (trade_date,)
        ).fetchall()
        conn.close()
        return [{'code': r[0], 'name': r[1], 'date': r[2],
                 'open': r[3], 'high': r[4], 'low': r[5], 'close': r[6], 'volume': r[7]} for r in rows]

    # ── 因子数据 ──────────────────────────────

    @staticmethod
    def get_factors(date_str: str) -> Optional[Dict[str, Dict[str, float]]]:
        """获取某日因子值"""
        if not os.path.exists(FACTORS_DB):
            return None
        conn = sqlite3.connect(FACTORS_DB)
        c = conn.cursor()
        try:
            rows = c.execute(
                "SELECT code, factor_name, value FROM factors WHERE date=?",
                (date_str,)
            ).fetchall()
            conn.close()
            result = {}
            for code, fname, value in rows:
                if code not in result:
                    result[code] = {}
                result[code][fname] = value
            return result
        except:
            conn.close()
            return None

    # ── 板块RPS ──────────────────────────────

    @staticmethod
    def get_board_rps(trade_date: str, rps_dir: str) -> Optional[List[Dict]]:
        """获取板块RPS数据（仅今日）"""
        import glob
        date_str = normalize_date(trade_date)
        compact = date_str.replace('-', '')

        # 搜两种格式
        patterns = [
            os.path.join(rps_dir, f'RPS_board_{compact}.json'),
            os.path.join(rps_dir, f'RPS_board_{date_str}.json'),
        ]
        for p in patterns:
            if os.path.exists(p):
                with open(p, encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('rps_data', data.get('data', []))
        return None  # SKIP — 不返回旧数据

    # ── 日志 ──────────────────────────────────

    @staticmethod
    def get_log() -> List[Dict]:
        return list(_log_events)

    @staticmethod
    def clear_log():
        _log_events.clear()


# ── MX搜索 ──────────────────────────────────

# MX搜索脚本路径
MX_SEARCH_SCRIPT = r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-search\mx_search.py'

def get_mx_apikey() -> Optional[str]:
    """获取MX_APIKEY"""
    key = os.environ.get('MX_APIKEY')
    if not key:
        # 尝试从配置文件读取
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'mx_api.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, encoding='utf-8') as f:
                    config = json.load(f)
                key = config.get('api_key')
            except:
                pass
    return key


def mx_search(query: str, timeout: int = 25) -> Optional[str]:
    """
    MX搜索接口

    用法:
        from scripts.data_api import mx_search
        result = mx_search("斯瑞新材 公告")
        if result:
            print(result)
    """
    import subprocess
    key = get_mx_apikey()
    if not key:
        _log('mx_search', 'skip', 'MX_APIKEY未设置')
        return None
    if not os.path.exists(MX_SEARCH_SCRIPT):
        _log('mx_search', 'skip', f'mx_search.py不存在: {MX_SEARCH_SCRIPT}')
        return None
    env = os.environ.copy()
    env['MX_APIKEY'] = key
    try:
        r = subprocess.run(
            [sys.executable, MX_SEARCH_SCRIPT, query],
            env=env, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        _log('mx_search', 'ok', f'query="{query[:50]}..."')
        return r.stdout
    except Exception as e:
        _log('mx_search', 'error', str(e))
        return None


# ── 万得MCP ──────────────────────────────────

WIND_MCP_CLI = r'C:\Users\Administrator\.agents\skills\wind-mcp-skill\scripts\cli.mjs'


def _wind_call(action: str, target: str, params_json: str) -> Optional[Dict]:
    """调用万得MCP CLI"""
    import subprocess, json
    if not os.path.exists(WIND_MCP_CLI):
        _log('wind_mcp', 'skip', 'cli.mjs不存在')
        return None
    try:
        cmd = ['node', WIND_MCP_CLI, 'call', action, target, params_json]
        proc = subprocess.run(cmd, capture_output=True, timeout=15,
                              encoding='utf-8', errors='replace')
        result = json.loads(proc.stdout)
        if not result.get('isError') and result.get('content'):
            text = result['content'][0]['text']
            data = json.loads(text)
            _log('wind_mcp', 'ok', f'{action}.{target}')
            return data
        return None
    except Exception as e:
        _log('wind_mcp', 'error', str(e))
        return None


def wind_stock_kline(windcode: str, begin_date: str, end_date: str) -> Optional[List[Dict]]:
    """获取万得个股K线"""
    import json
    params = json.dumps({"windcode": windcode, "begin_date": begin_date, "end_date": end_date})
    data = _wind_call('index_data', 'get_index_kline', params)
    if data and data.get('data') and data['data'].get('rows'):
        return data['data']['rows']
    return None


def wind_index_kline(windcode: str, begin_date: str, end_date: str) -> Optional[List[Dict]]:
    """获取万得指数K线"""
    import json
    params = json.dumps({"windcode": windcode, "begin_date": begin_date, "end_date": end_date})
    data = _wind_call('index_data', 'get_index_kline', params)
    if data and data.get('data') and data['data'].get('rows'):
        return data['data']['rows']
    return None


def wind_fundamentals(windcode: str) -> Optional[Dict]:
    """获取万得基本面数据"""
    import json
    params = json.dumps({"windcode": windcode})
    data = _wind_call('stock_data', 'get_stock_basicinfo', params)
    return data


def wind_news(query: str, count: int = 5) -> Optional[List[Dict]]:
    """获取万得新闻"""
    import json
    params = json.dumps({"query": query, "count": count})
    data = _wind_call('financial_docs', 'get_financial_news', params)
    if data and data.get('data') and data['data'].get('rows'):
        return data['data']['rows']
    return None


# ── 东方财富 ──────────────────────────────────

def eastmoney_secid(code: str) -> str:
    """转为东方财富secid格式 (1.600001 / 0.000001)"""
    std = normalize_code(code)
    digits = std.split('.')[1]
    prefix = '1' if std.startswith('sh') else '0'
    return f'{prefix}.{digits}'


def eastmoney_realtime(codes: List[str]) -> Optional[Dict[str, Dict]]:
    """
    东方财富实时行情（备用数据源）
    返回: {code: {'price': float, 'chg_pct': float}}
    """
    if isinstance(codes, str):
        codes = [codes]
    secids = ','.join(eastmoney_secid(c) for c in codes)
    try:
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secids={secids}&fields=f43,f170,f171,f167'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode('utf-8'))
        result = {}
        if data.get('data'):
            for item in data['data'] if isinstance(data['data'], list) else [data['data']]:
                std_code = normalize_code(str(item.get('code', '')))
                result[std_code] = {
                    'price': float(item.get('f43', 0)),
                    'chg_pct': float(item.get('f170', 0)),
                }
        _log('eastmoney', 'realtime', f'{len(codes)}只, {len(result)}只有效')
        return result
    except Exception as e:
        _log('eastmoney', 'realtime_error', str(e))
        return None


def eastmoney_money_flow(secid: str) -> Optional[Dict]:
    """东方财富资金流向"""
    try:
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secids={secid}&fields=f62,f184,f66,f69,f72,f75,f78,f81,f84,f87'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode('utf-8'))
        return data.get('data')
    except Exception as e:
        _log('eastmoney', 'money_flow_error', str(e))
        return None


def eastmoney_announcements(code: str, days: int = 30) -> Optional[List[Dict]]:
    """
    东方财富公告
    
    主源：np-anotice-stock.eastmoney.com
    """
    import urllib.parse
    std = normalize_code(code)
    digits = std.split('.')[1]
    market = '1' if std.startswith('sh') else '0'
    end = datetime.now().strftime('%Y-%m-%d')
    from datetime import timedelta
    start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    try:
        url = (f'https://np-anotice-stock.eastmoney.com/api/security/ann?'
               f'sr=-1&page_size=20&page_index=1&ann_type=A&'
               f'stock_list={market}_{digits}&'
               f'begin_time={start}&end_time={end}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        notices = data.get('data', {}).get('list', [])
        _log('eastmoney', 'announcements', f'{code}: {len(notices)}条')
        return notices
    except Exception as e:
        _log('eastmoney', 'announcements_error', str(e))
        return None


# ── 新浪财经（备用数据源）──────────────────────

def sina_realtime(code: str) -> Optional[Dict]:
    """
    新浪实时行情（腾讯挂了时的备用）
    
    用法:
        data = sina_realtime('sh688102')
        if data:
            print(data['price'], data['chg_pct'])
    """
    try:
        url = f'https://hq.sinajs.cn/list={code}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
                                                     'Referer': 'https://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('gbk')
        if '=' in raw and '"' in raw:
            p = raw.split('"')[1].split(',')
            if len(p) >= 30:
                price = float(p[3]) if p[3] else 0
                prev = float(p[2]) if p[2] else price
                chg = round((price - prev) / prev * 100, 2) if prev else 0
                return {
                    'price': price,
                    'chg_pct': chg,
                    'name': p[0],
                    'open': float(p[1]) if p[1] else 0,
                    'volume': float(p[8]) if p[8] else 0,
                    'amount': float(p[9]) if p[9] else 0,
                }
        return None
    except Exception as e:
        _log('sina', 'realtime_error', str(e))
        return None


# ── 金十快讯 ──────────────────────────────────

def jin10_flash(max_items: int = 50) -> Optional[List[Dict]]:
    """
    金十实时快讯
    
    返回: [{'time': str, 'content': str, 'type': str}, ...]
    """
    import time as time_module
    ts = int(time_module.time() * 1000)
    try:
        url = f'https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=1&max_time=&_={ts}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.jin10.com/',
        })
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode('utf-8'))
        items = data.get('data', [])[:max_items]
        result = []
        for item in items:
            result.append({
                'time': item.get('time', ''),
                'content': item.get('data', {}).get('content', item.get('content', '')),
                'type': item.get('data', {}).get('type', '') if 'data' in item else '',
            })
        _log('jin10', 'flash', f'{len(result)}条')
        return result
    except Exception as e:
        _log('jin10', 'flash_error', str(e))
        return None


def jin10_search_keyword(keyword: str) -> Optional[List[Dict]]:
    """金十搜索关键词"""
    import time as time_module
    ts = int(time_module.time() * 1000)
    try:
        url = f'https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=1&max_time=&_={ts}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.jin10.com/',
        })
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode('utf-8'))
        items = data.get('data', [])
        result = []
        for item in items:
            content = item.get('data', {}).get('content', item.get('content', ''))
            if keyword in content:
                result.append({
                    'time': item.get('time', ''),
                    'content': content,
                })
        _log('jin10', 'search', f'keyword="{keyword}", {len(result)}条')
        return result
    except Exception as e:
        _log('jin10', 'search_error', str(e))
        return None