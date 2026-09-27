"""基本面因子计算器

因子列表：
  - pe_ttm: 滚动市盈率
  - pb: 市净率
  - roe: 净资产收益率
  - roic: 投入资本回报率
  - earnings_yield: 收益率 (1/PE_TTM)
  - market_cap: 总市值 (亿元)
  - profit_growth_q: 净利润同比增长率 (%)

数据来源：东方财富API (HTTP)
"""
import requests
import json
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List

EM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.eastmoney.com/'
}


class FundamentalFactors:
    """基本面因子计算器"""

    # 缓存：避免重复请求
    _fin_cache: Dict[str, dict] = {}

    @staticmethod
    def _get_secid(code: str) -> str:
        """统一code为东财secid格式"""
        c = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        for prefix in ('sh', 'sz', 'bj'):
            if c.startswith(prefix) and len(c) > len(prefix) and c[len(prefix):len(prefix)+1].isdigit():
                c = c[len(prefix):]
                break
        return f'1.{c}' if c.startswith('6') or c.startswith('688') or c.startswith('689') else f'0.{c}'

    @staticmethod
    def _fetch_financials(code: str) -> dict:
        """从东财API获取基本面数据"""
        if code in FundamentalFactors._fin_cache:
            return FundamentalFactors._fin_cache[code]

        secid = FundamentalFactors._get_secid(code)
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f57,f58,f100,f116,f117,f162,f167,f168,f169,f170'

        result = {}
        try:
            resp = requests.get(url, headers=EM_HEADERS, timeout=8)
            data = resp.json()
            if data.get('data'):
                d = data['data']
                # f43=最新价, f44=最高, f45=最低, f46=今开
                # f57=股票代码, f58=股票名称
                # f100=市盈率(动态), f162=市净率
                # f116=总市值, f117=流通市值
                # f167=ROE, f168=毛利率
                # f169=净利润同比增长, f170=营业收入同比增长
                result['pe'] = d.get('f100', 0) or 0
                result['pb'] = d.get('f162', 0) or 0
                result['market_cap'] = (d.get('f116', 0) or 0) / 100000000
                result['roe'] = d.get('f167', 0) or 0
                result['profit_growth'] = d.get('f169', 0) or 0
                result['revenue_growth'] = d.get('f170', 0) or 0
                result['price'] = d.get('f43', 0) or 0
        except Exception:
            pass

        FundamentalFactors._fin_cache[code] = result
        return result

    @staticmethod
    def pe_ttm(code: str, df: pd.DataFrame = None) -> float:
        """滚动市盈率"""
        fin = FundamentalFactors._fetch_financials(code)
        pe = fin.get('pe', 0)
        return float(pe) if pe > 0 else 0.0

    @staticmethod
    def pb(code: str, df: pd.DataFrame = None) -> float:
        """市净率"""
        pb = FundamentalFactors._fetch_financials(code).get('pb', 0)
        return float(pb) if pb > 0 else 0.0

    @staticmethod
    def roe(code: str, df: pd.DataFrame = None) -> float:
        """净资产收益率 (%)"""
        roe = FundamentalFactors._fetch_financials(code).get('roe', 0)
        return float(roe)

    @staticmethod
    def roic(code: str, df: pd.DataFrame = None) -> float:
        """投入资本回报率 (近似ROE, 更精确需财报数据)

        注意：东财API没有直接提供ROIC，用ROE近似。
        精确ROIC需要从财报获取NOPAT和IC。
        """
        roe = FundamentalFactors._fetch_financials(code).get('roe', 0)
        return float(roe) * 0.8  # ROIC通常略低于ROE

    @staticmethod
    def earnings_yield(code: str, df: pd.DataFrame = None) -> float:
        """收益率 = 1/PE_TTM

        值越高越好，代表盈利性价比。
        PE=20 -> 5%, PE=10 -> 10%
        """
        pe = FundamentalFactors.pe_ttm(code, df)
        if pe <= 0:
            return 0.0
        return 1.0 / pe

    @staticmethod
    def market_cap(code: str, df: pd.DataFrame = None) -> float:
        """总市值 (亿元)"""
        cap = FundamentalFactors._fetch_financials(code).get('market_cap', 0)
        return float(cap)

    @staticmethod
    def profit_growth_q(code: str, df: pd.DataFrame = None) -> float:
        """净利润同比增长率 (%)"""
        g = FundamentalFactors._fetch_financials(code).get('profit_growth', 0)
        return float(g)

    @staticmethod
    def clear_cache():
        """清空缓存"""
        FundamentalFactors._fin_cache.clear()