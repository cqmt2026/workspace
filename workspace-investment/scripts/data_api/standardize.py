# -*- coding: utf-8 -*-
"""
数据标准化工具 — 统一所有数据格式

核心原则：
  1. 股票代码：统一使用 sh.xxxxxx / sz.xxxxxx / bj.xxxxxx 格式
  2. 日期：统一使用 YYYY-MM-DD 格式
  3. 数值：统一使用 float，None 表示缺失
  4. 文件名：统一使用 YYYY-MM-DD 日期格式

用法:
    from scripts.data_api.standardize import normalize_code, normalize_date, ...
"""
import re
from typing import Optional


# ──────────────────────────────────────────────
# 股票代码标准化
# ──────────────────────────────────────────────

def normalize_code(code: str) -> str:
    """
    将任意格式的股票代码转为 sh.xxxxxx / sz.xxxxxx / bj.xxxxxx 格式

    输入: '000004' / 'sz000004' / 'SZ000004' / 'sz.000004' / '000004.SZ' / '600001'
    输出: 'sz.000004' / 'sh.600001'

    规则:
      - 6/9开头 → sh（上海）
      - 0/3开头 → sz（深圳）
      - 4开头   → bj（北交所）
      - 已带前缀 → 保持不变
    """
    if not code:
        return code

    # 去除空格
    code = code.strip()

    # 已带前缀格式 (sh.600001, sz.000001, bj.400001)
    if re.match(r'^(sh|sz|bj)\.\d{6}$', code, re.IGNORECASE):
        return code.lower()

    # 带前缀无点格式 (sh600001, sz000001)
    if re.match(r'^(sh|sz|bj)\d{6}$', code, re.IGNORECASE):
        prefix = code[:2].lower()
        digits = code[2:]
        return f'{prefix}.{digits}'

    # 后缀格式 (000001.SZ, 600001.SH)
    if re.match(r'^\d{6}\.(SH|SZ|BJ)$', code, re.IGNORECASE):
        digits = code[:6]
        prefix = code[7:].lower()
        return f'{prefix}.{digits}'

    # 纯数字格式
    if re.match(r'^\d{6}$', code):
        if code.startswith('6') or code.startswith('9'):
            return f'sh.{code}'
        elif code.startswith('0') or code.startswith('3'):
            return f'sz.{code}'
        elif code.startswith('4') or code.startswith('8'):
            return f'bj.{code}'

    # 无法识别，原样返回
    return code


def strip_code_prefix(code: str) -> str:
    """去掉前缀，返回纯数字代码"""
    m = re.match(r'^(sh|sz|bj)[\.]?(\d{6})$', code, re.IGNORECASE)
    if m:
        return m.group(2)
    return code


def code_to_tengxun(code: str) -> str:
    """转为腾讯API格式 (无点无前缀)"""
    return strip_code_prefix(code)


def code_to_db(code: str) -> str:
    """转为DB中存储的格式 (sh.xxxxxx)"""
    return normalize_code(code)


# ──────────────────────────────────────────────
# 日期标准化
# ──────────────────────────────────────────────

def normalize_date(date_val) -> str:
    """
    将任意格式的日期转为 YYYY-MM-DD 格式

    输入: '20260713' / '2026-07-13' / datetime(2026,7,13) / date(2026,7,13)
    输出: '2026-07-13'
    """
    if not date_val:
        return ''

    # 已经是字符串
    if isinstance(date_val, str):
        d = date_val.strip()
        # 2026-07-13 格式
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            return d
        # 20260713 格式
        if re.match(r'^\d{8}$', d):
            return f'{d[:4]}-{d[4:6]}-{d[6:8]}'
        # 2026/07/13 格式
        if re.match(r'^\d{4}/\d{2}/\d{2}$', d):
            return d.replace('/', '-')
        return d

    # datetime 或 date 对象
    if hasattr(date_val, 'strftime'):
        return date_val.strftime('%Y-%m-%d')

    return str(date_val)


def compact_date(date_val) -> str:
    """转为 YYYYMMDD 紧凑格式"""
    return normalize_date(date_val).replace('-', '')


# ──────────────────────────────────────────────
# 文件名标准化
# ──────────────────────────────────────────────

def normalize_filename(basename: str, date_val) -> str:
    """
    统一文件名中的日期格式为 YYYY-MM-DD

    输入: ('RPS_board_{}.json', '20260713')
    输出: 'RPS_board_2026-07-13.json'
    """
    date_str = normalize_date(date_val)
    return basename.replace('{}', date_str)


# ──────────────────────────────────────────────
# 数值标准化
# ──────────────────────────────────────────────

def safe_float(val, default: Optional[float] = None) -> Optional[float]:
    """安全转float，失败返回默认值"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default: Optional[int] = None) -> Optional[int]:
    """安全转int，失败返回默认值"""
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default