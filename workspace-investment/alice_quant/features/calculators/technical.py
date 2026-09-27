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

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """能量潮 OBV - 量价配合/背离检测

        返回OBV标准化值（z-score），正值=量价配合，负值=背离
        """
        change = close.diff()
        direction = pd.Series(np.where(change > 0, 1, np.where(change < 0, -1, 0)), index=close.index)
        obv_values = (direction * volume).cumsum()
        # z-score标准化
        mean = obv_values.mean()
        std = obv_values.std()
        if std > 0:
            return (obv_values - mean) / std
        return pd.Series(0.0, index=close.index)

    @staticmethod
    def wr(close: pd.Series, high: pd.Series, low: pd.Series, window: int = 14) -> pd.Series:
        """威廉指标 W%R - 超买超卖（与RSI互补）

        W%R = (最高价 - 收盘价) / (最高价 - 最低价) * -100
        范围: -100 ~ 0
        超卖: < -80, 超买: > -20
        """
        highest = high.rolling(window=window).max()
        lowest = low.rolling(window=window).min()
        wr_val = (highest - close) / (highest - lowest).replace(0, np.nan) * -100
        return wr_val

    @staticmethod
    def cci(close: pd.Series, high: pd.Series, low: pd.Series, window: int = 20) -> pd.Series:
        """商品通道指标 CCI - 价格偏离检测

        CCI = (TP - MA(TP)) / (0.015 * 平均偏差)
        TP = (高+低+收)/3
        >100: 超买, < -100: 超卖
        """
        tp = (high + low + close) / 3
        ma = tp.rolling(window=window).mean()
        md = tp.rolling(window=window).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        cci_val = (tp - ma) / (0.015 * md.replace(0, np.nan))
        return cci_val

    @staticmethod
    def vwap(close: pd.Series, volume: pd.Series, window: int = 5) -> pd.Series:
        """成交量加权均价 VWAP

        VWAP = 累计(价格*成交量) / 累计(成交量)
        股价在VWAP上方 = 多头，下方 = 空头
        """
        pv = close * volume
        return pv.rolling(window=window).sum() / volume.rolling(window=window).sum().replace(0, np.nan)

    @staticmethod
    def volatility(close: pd.Series, window: int = 20) -> pd.Series:
        """波动率 - 日收益率标准差

        高波动=风险大但机会多，低波动=横盘
        """
        returns = close.pct_change()
        return returns.rolling(window=window).std() * 100