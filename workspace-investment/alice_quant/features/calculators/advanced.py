"""动量加速度因子 + 筹码分布因子 + 板块联动因子"""
import pandas as pd
import numpy as np


class MomentumFactors:
    """动量加速度因子"""

    @staticmethod
    def macd_dif(close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """MACD快慢线差值"""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        return ema_fast - ema_slow

    @staticmethod
    def macd_signal(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """MACD信号线"""
        dif = MomentumFactors.macd_dif(close, fast, slow)
        return dif.ewm(span=signal, adjust=False).mean()

    @staticmethod
    def macd_bar(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """MACD柱状图 (DIF - DEA) * 2"""
        dif = MomentumFactors.macd_dif(close, fast, slow)
        dea = dif.ewm(span=signal, adjust=False).mean()
        return 2 * (dif - dea)

    @staticmethod
    def macd_cross(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """MACD金叉/死叉信号

        1 = 金叉（DIF上穿DEA）
        -1 = 死叉（DIF下穿DEA）
        0 = 无
        """
        dif = MomentumFactors.macd_dif(close, fast, slow)
        dea = dif.ewm(span=signal, adjust=False).mean()
        cross = pd.Series(0, index=close.index)
        cross[(dif.shift(1) <= dea.shift(1)) & (dif > dea)] = 1
        cross[(dif.shift(1) >= dea.shift(1)) & (dif < dea)] = -1
        return cross

    @staticmethod
    def rsi_slope(rsi: pd.Series, window: int = 3) -> pd.Series:
        """RSI斜率（连续N日RSI变化方向）

        正值=RSI上升，负值=RSI下降
        """
        return rsi.diff(window)

    @staticmethod
    def rsi_momentum(rsi: pd.Series, window: int = 5) -> pd.Series:
        """RSI动量（RSI加速度）

        正值=RSI上升加速，负值=RSI上升减速
        """
        slope = rsi.diff(1)
        return slope.diff(window - 1)

    @staticmethod
    def acceleration(close: pd.Series, short_window: int = 5, long_window: int = 10) -> pd.Series:
        """涨速比 = 短周期涨幅 / 长周期涨幅

        > 1 = 加速上涨
        < 1 = 减速上涨
        < 0 = 下跌加速
        """
        short_ret = close.pct_change(short_window)
        long_ret = close.pct_change(long_window)
        # 避免除0，long_ret接近0时返回0
        result = pd.Series(np.where(abs(long_ret) > 0.001, short_ret / long_ret, 0), index=close.index)
        return result

    @staticmethod
    def breakout_strength(close: pd.Series, high: pd.Series, window: int = 20) -> pd.Series:
        """突破强度 = 当前价格 / 过去N日最高价

        > 0.95 = 接近突破
        > 1.0 = 创新高
        """
        highest = high.rolling(window=window).max().shift(1)  # 前N日最高
        return close / highest.replace(0, np.nan)

    @staticmethod
    def macd_second_peak(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """MACD红绿柱二次放大/缩短信号

        2 = 红柱二次放大（洗盘结束，新一轮上涨启动）
        -2 = 绿柱二次放大（反弹结束，新一轮下跌开始）
        1 = 红柱持续缩短（多头衰减）
        -1 = 绿柱持续缩短（空头衰减）
        0 = 无信号
        """
        bar = MomentumFactors.macd_bar(close, fast, slow, signal)
        bar_diff = bar.diff(1)
        direction = pd.Series(0, index=close.index)
        direction[bar_diff > 0] = 1
        direction[bar_diff < 0] = -1
        signal_out = pd.Series(0, index=close.index)

        n = len(bar)
        for i in range(8, n):
            if bar.iloc[i] > 0 and direction.iloc[i] == 1:
                prev5 = direction.iloc[i-5:i]
                if (prev5 == -1).any():
                    if bar.iloc[i] > bar.iloc[i-5:i].max() * 1.005:
                        signal_out.iloc[i] = 2
                        continue
            if bar.iloc[i] < 0 and direction.iloc[i] == -1:
                prev5 = direction.iloc[i-5:i]
                if (prev5 == 1).any():
                    if bar.iloc[i] < bar.iloc[i-5:i].min() * 0.995:
                        signal_out.iloc[i] = -2
                        continue
            if bar.iloc[i] > 0 and direction.iloc[i] == -1 and (direction.iloc[i-3:i] == -1).all():
                signal_out.iloc[i] = 1
            elif bar.iloc[i] < 0 and direction.iloc[i] == 1 and (direction.iloc[i-3:i] == 1).all():
                signal_out.iloc[i] = -1
        return signal_out

class ChipFactors:
    """筹码分布因子（从K线估算）"""

    @staticmethod
    def avg_cost(close: pd.Series, volume: pd.Series, window: int = 60) -> pd.Series:
        """平均持仓成本 = 加权平均价（成交量加权）

        60日成交量加权均价 = 近似主力成本
        """
        pv = close * volume
        return pv.rolling(window=window).sum() / volume.rolling(window=window).sum().replace(0, np.nan)

    @staticmethod
    def profit_ratio(close: pd.Series, avg_cost: pd.Series) -> pd.Series:
        """获利盘比例 = (收盘价 - 平均成本) / 平均成本

        正值=获利盘，负值=套牢盘
        """
        return (close - avg_cost) / avg_cost.replace(0, np.nan) * 100

    @staticmethod
    def concentration(close: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
        """筹码集中度 = 近期成交量变异系数

        变异系数越小 = 成交量越均匀 = 筹码越集中
        变异系数突然变小 = 筹码集中信号
        """
        mean_v = volume.rolling(window=window).mean()
        std_v = volume.rolling(window=window).std()
        cv = std_v / mean_v.replace(0, np.nan)
        # 反向：cv越小 = 越集中
        return 1 - cv

    @staticmethod
    def support_level(close: pd.Series, window: int = 20) -> pd.Series:
        """支撑位 = 过去N日最低价附近

        收盘价接近支撑位 = 可能有反弹
        """
        lowest = close.rolling(window=window).min()
        return (close - lowest) / lowest.replace(0, np.nan) * 100

    @staticmethod
    def resistance_level(close: pd.Series, high: pd.Series, window: int = 20) -> pd.Series:
        """压力位 = 过去N日最高价附近

        收盘价接近压力位 = 可能有回调
        """
        highest = high.rolling(window=window).max()
        return (highest - close) / close.replace(0, np.nan) * 100


class SectorFactors:
    """板块联动因子"""

    @staticmethod
    def sector_dispersion(codes_in_sector: list, close_map: dict, date: str) -> float:
        """板块内涨幅离散度

        越小=板块效应越强，越大=个股分化
        """
        returns = []
        for code in codes_in_sector:
            if code in close_map and date in close_map[code]:
                returns.append(close_map[code][date])
        if len(returns) < 5:
            return 0
        return float(np.std(returns))

    @staticmethod
    def leader_premium(code_return: float, sector_median_return: float) -> float:
        """龙头溢价 = 个股涨幅 - 板块中位数涨幅

        正数=跑赢板块，负数=跑输板块
        """
        if sector_median_return == 0:
            return 0
        return code_return - sector_median_return

    @staticmethod
    def rotation_speed(current_top_sectors: list, prev_top_sectors: list) -> float:
        """板块轮动速度 = 当前领涨板块 vs 前一日领涨板块的重叠度

        0=完全轮动（新板块），1=完全不变
        """
        if not current_top_sectors or not prev_top_sectors:
            return 0
        overlap = len(set(current_top_sectors) & set(prev_top_sectors))
        return overlap / max(len(current_top_sectors), len(prev_top_sectors))