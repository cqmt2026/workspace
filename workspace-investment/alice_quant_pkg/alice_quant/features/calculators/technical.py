"""技术因子计算器"""
import pandas as pd
import numpy as np


class TechnicalFactors:
    """价量技术因子"""

    @staticmethod
    def ma(close: pd.Series, window: int = 5) -> pd.Series:
        """移动平均线"""
        return close.rolling(window=window).mean()

    @staticmethod
    def ema(close: pd.Series, window: int = 12) -> pd.Series:
        """指数移动平均线"""
        return close.ewm(span=window, adjust=False).mean()

    @staticmethod
    def rsi(close: pd.Series, window: int = 14) -> pd.Series:
        """相对强弱指标 RSI"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD指标"""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd_bar = 2 * (dif - dea)
        return pd.DataFrame({'dif': dif, 'dea': dea, 'macd': macd_bar})

    @staticmethod
    def bollinger(close: pd.Series, window: int = 20, num_std: int = 2) -> pd.DataFrame:
        """布林带"""
        ma = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        upper = ma + num_std * std
        lower = ma - num_std * std
        return pd.DataFrame({'ma': ma, 'upper': upper, 'lower': lower})

    @staticmethod
    def volume_ratio(volume: pd.Series, window: int = 5) -> pd.Series:
        """量比 = 当日成交量 / 5日均量"""
        avg_volume = volume.rolling(window=window).mean()
        return volume / avg_volume.replace(0, np.nan)

    @staticmethod
    def turnover_rate(volume: pd.Series, close: pd.Series,
                     total_shares: float = 1e9) -> pd.Series:
        """换手率 = 成交量 / 流通股本（简化版）"""
        return volume / total_shares * 100

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """平均真实波幅 ATR"""
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift()),
            'lc': abs(low - close.shift())
        }).max(axis=1)
        return tr.rolling(window=window).mean()

    @staticmethod
    def pct_change(close: pd.Series, periods: int = 1) -> pd.Series:
        """涨跌幅"""
        return close.pct_change(periods=periods) * 100