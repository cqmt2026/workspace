# -*- coding: utf-8 -*-
"""
行情加载器 price_loader.py
对接腾讯/东方财富实时行情，为净值计算提供价格数据
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional


class PriceLoader:
    """行情加载器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })

    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """
        获取单只股票实时价格

        Args:
            symbol: 股票代码（如 000591.SZ 或 sz000591）

        Returns:
            当前价格，失败返回None
        """
        # 转换格式：000591.SZ -> sz000591
        market_map = {'SZ': 'sz', 'SH': 'sh'}
        parts = symbol.split('.')
        if len(parts) == 2:
            code, ex = parts
            market = market_map.get(ex.upper(), ex.lower())
            qt_code = f"{market}{code}"
        else:
            qt_code = symbol.lower()

        try:
            url = f'http://qt.gtimg.cn/q={qt_code}'
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'gbk'

            if resp.status_code == 200:
                data = resp.text.strip()
                if data and '~' in data:
                    parts = data.split('~')
                    if len(parts) >= 4:
                        price_str = parts[3]
                        return float(price_str)
            return None
        except Exception:
            return None

    def get_price_map(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取股票价格

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: price} 字典
        """
        result = {}
        for sym in symbols:
            price = self.get_realtime_price(sym)
            if price:
                result[sym] = price
        return result

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票详细信息

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        market_map = {'SZ': 'sz', 'SH': 'sh'}
        parts = symbol.split('.')
        if len(parts) == 2:
            code, ex = parts
            market = market_map.get(ex.upper(), ex.lower())
            qt_code = f"{market}{code}"
        else:
            qt_code = symbol.lower()

        try:
            url = f'http://qt.gtimg.cn/q={qt_code}'
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'gbk'

            if resp.status_code == 200:
                data = resp.text.strip()
                if data and '~' in data:
                    parts = data.split('~')
                    if len(parts) >= 45:
                        return {
                            'symbol': symbol,
                            'name': parts[1],
                            'current': float(parts[3]),
                            'open': float(parts[5]),
                            'high': float(parts[33]) if len(parts) > 33 else None,
                            'low': float(parts[34]) if len(parts) > 34 else None,
                            'close_prev': float(parts[4]),  # 昨收
                            'volume': float(parts[6]) if len(parts) > 6 else None,
                            'change': float(parts[3]) - float(parts[4]) if len(parts) > 4 else None,
                            'change_pct': ((float(parts[3]) - float(parts[4])) / float(parts[4]) * 100) if len(parts) > 4 else None,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
            return None
        except Exception:
            return None


# 便捷函数
_loader = None

def get_price_loader() -> PriceLoader:
    """获取行情加载器单例"""
    global _loader
    if _loader is None:
        _loader = PriceLoader()
    return _loader


def get_realtime_price(symbol: str) -> Optional[float]:
    """获取单只股票实时价格"""
    return get_price_loader().get_realtime_price(symbol)


def get_price_map(symbols: List[str]) -> Dict[str, float]:
    """批量获取股票价格"""
    return get_price_loader().get_price_map(symbols)


# 测试
if __name__ == "__main__":
    loader = PriceLoader()

    print("=== 行情加载测试 ===\n")

    # 测试单只股票
    print("1. 单只股票价格测试")
    price = loader.get_realtime_price("000591.SZ")
    print(f"   太阳能(000591.SZ): {price}")

    print("\n2. 批量价格测试")
    symbols = ["000591.SZ", "000001.SZ", "600519.SH"]
    price_map = loader.get_price_map(symbols)
    for sym, price in price_map.items():
        print(f"   {sym}: {price}")

    print("\n3. 详细信息测试")
    info = loader.get_stock_info("000591.SZ")
    if info:
        print(f"   {info['name']}: 现价{info['current']}, 涨跌{info['change']:+.2f} ({info['change_pct']:+.2f}%)")
