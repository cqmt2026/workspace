#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
30 因子量化模型
融合：技术指标 + 量价因子 + 位置因子 + 动量因子 + 基本面因子
"""

import pandas as pd
import numpy as np
from datetime import datetime

# ========== 30 因子权重 ==========
FACTOR_WEIGHTS = {
    # 技术指标（12个，23%权重）
    'ma5_trend': 0.03,
    'ma10_trend': 0.02,
    'ma20_trend': 0.02,
    'ma60_trend': 0.02,
    'macd': 0.03,
    'rsi': 0.02,
    'kdj_k': 0.02,
    'kdj_d': 0.02,
    'boll_position': 0.02,
    'cci': 0.01,
    'wr': 0.01,
    'adx': 0.01,
    
    # 量价因子（6个，10%权重）
    'volume_ratio': 0.02,
    'turnover': 0.02,
    'money_flow': 0.02,
    'price_volume': 0.015,
    'obv': 0.01,
    'vr': 0.015,
    
    # 位置因子（3个，8%权重）
    'position_60': 0.03,
    'position_250': 0.025,
    'ma_distance': 0.025,
    
    # 动量因子（3个，9%权重）
    'momentum_5': 0.035,
    'momentum_10': 0.03,
    'momentum_20': 0.025,
    
    # 基本面因子（6个，7%权重）
    'pe': 0.015,
    'pb': 0.01,
    'ps': 0.01,
    'roe': 0.015,
    'growth': 0.01,
    'debt': 0.01,
    
    # ===== 新增因子 V2.0 (2026-03-25) =====
    
    # 主力资金/筹码因子（4个，13%权重）
    'main_force': 0.04,         # 主力净流入
    'big_order': 0.035,         # 大单占比
    'chip_concentration': 0.03, # 筹码集中度
    'consecutive_inflow': 0.025,# 连续资金流入
    
    # 板块联动因子（3个，10%权重）
    'sector_rank': 0.03,        # 板块排名
    'sector_momentum': 0.04,    # 板块动量
    'relative_strength': 0.03,  # 相对强弱
    
    # 波动率因子（3个，5%权重）
    'atr': 0.02,                # ATR
    'volatility': 0.015,        # 历史波动率
    'boll_width': 0.015,        # 布林带宽
    
    # 技术形态因子（3个，5%权重）
    'ma_alignment': 0.02,       # 均线排列
    'volume_breakout': 0.02,    # 放量突破
    'support_resistance': 0.01, # 支撑压力
    
    # 情绪面因子（3个，5%权重）
    'turnover_rate': 0.02,      # 换手率
    'limit_distance': 0.015,    # 距涨停距离
    'amplitude': 0.015,         # 当日振幅
    
    # 补充因子（4个，5%权重）
    'north_flow': 0.015,        # 北向资金方向
    'gap_strength': 0.01,       # 跳空缺口强度
    'volume_ma_ratio': 0.015,   # 量能趋势（5日均量vs20日均量）
    'price_efficiency': 0.01,   # 价格效率（涨幅/振幅）
}


class Factor30Model:
    """30 因子量化模型"""
    
    def __init__(self):
        self.factor_count = 50
        self.total_weight = sum(FACTOR_WEIGHTS.values())
    
    def calculate_all_factors(self, quote, kline, fundamentals=None):
        """
        计算全部 30 个因子
        
        Args:
            quote: 实时行情
            kline: K 线数据
            fundamentals: 基本面数据（可选）
        
        Returns:
            dict: 所有因子值
        """
        factors = {}
        prices = kline['close']
        volumes = kline['volume']
        
        # ========== 技术指标（12 个）==========
        factors['ma5_trend'] = self._calc_ma_trend(prices, 5)
        factors['ma10_trend'] = self._calc_ma_trend(prices, 10)
        factors['ma20_trend'] = self._calc_ma_trend(prices, 20)
        factors['ma60_trend'] = self._calc_ma_trend(prices, 60)
        factors['macd'] = self._calc_macd(prices)
        factors['rsi'] = self._calc_rsi(prices)
        factors['kdj_k'], factors['kdj_d'] = self._calc_kdj(kline)
        factors['boll_position'] = self._calc_boll_position(prices)
        factors['cci'] = self._calc_cci(kline)
        factors['wr'] = self._calc_wr(kline)
        factors['adx'] = self._calc_adx(kline)
        
        # ========== 量价因子（6 个）==========
        factors['volume_ratio'] = self._calc_volume_ratio(volumes)
        factors['turnover'] = self._calc_turnover(quote, kline)
        factors['money_flow'] = self._calc_money_flow(kline)
        factors['price_volume'] = self._calc_price_volume(prices, volumes)
        factors['obv'] = self._calc_obv(prices, volumes)
        factors['vr'] = self._calc_vr(prices, volumes)
        
        # ========== 位置因子（3 个）==========
        factors['position_60'] = self._calc_position(prices, 60)
        factors['position_250'] = self._calc_position(prices, min(250, len(prices)))
        factors['ma_distance'] = self._calc_ma_distance(prices)
        
        # ========== 动量因子（3 个）==========
        factors['momentum_5'] = self._calc_momentum(prices, 5)
        factors['momentum_10'] = self._calc_momentum(prices, 10)
        factors['momentum_20'] = self._calc_momentum(prices, 20)
        
        # ========== 基本面因子（6 个）==========
        if fundamentals:
            factors['pe'] = self._calc_pe_score(fundamentals.get('pe', 50))
            factors['pb'] = self._calc_pb_score(fundamentals.get('pb', 5))
            factors['ps'] = self._calc_ps_score(fundamentals.get('ps', 10))
            factors['roe'] = self._calc_roe_score(fundamentals.get('roe', 10))
            factors['growth'] = self._calc_growth_score(fundamentals.get('growth', 20))
            factors['debt'] = self._calc_debt_score(fundamentals.get('debt', 50))
        
        # ========== 新增因子 V2.0 (2026-03-25) ==========
        
        # 主力资金/筹码因子（4个）
        factors['main_force'] = self._calc_main_force_ratio(quote)
        factors['big_order'] = self._calc_big_order_ratio(quote)
        factors['chip_concentration'] = self._calc_chip_concentration(kline)
        factors['consecutive_inflow'] = self._calc_consecutive_inflow(quote)
        
        # 板块联动因子（3个）
        sector = quote.get('sector', '')
        factors['sector_rank'] = self._calc_sector_rank(sector)
        factors['sector_momentum'] = self._calc_sector_momentum(sector)
        factors['relative_strength'] = self._calc_relative_strength(prices)
        
        # 波动率因子（3个）
        factors['atr'] = self._calc_atr(kline)
        factors['volatility'] = self._calc_volatility(prices)
        factors['boll_width'] = self._calc_boll_width(prices)
        
        # 技术形态因子（3个）
        factors['ma_alignment'] = self._calc_ma_alignment(prices)
        factors['volume_breakout'] = self._calc_volume_breakout(volumes)
        factors['support_resistance'] = self._calc_support_resistance(prices)
        
        # 情绪面因子（3个）
        factors['turnover_rate'] = self._calc_turnover_rate(quote)
        factors['limit_distance'] = self._calc_price_limit_distance(quote)
        factors['amplitude'] = self._calc_amp_score(kline)
        
        # 补充因子（4个）
        factors['north_flow'] = self._calc_north_flow()
        factors['gap_strength'] = self._calc_gap_strength(kline)
        factors['volume_ma_ratio'] = self._calc_volume_ma_ratio(volumes)
        factors['price_efficiency'] = self._calc_price_efficiency(kline)
        
        return factors
    
    def calculate_score(self, factors):
        """
        计算综合评分
        
        Args:
            factors: 因子值 dict
        
        Returns:
            float: 综合评分（0-100）
        """
        total_score = 0
        
        for factor_name, weight in FACTOR_WEIGHTS.items():
            if factor_name in factors:
                total_score += factors[factor_name] * weight
        
        # 归一化到 0-100
        if self.total_weight > 0:
            total_score = total_score / self.total_weight
        
        return round(total_score, 1)
    
    # ========== 技术指标计算 ==========
    def _calc_ma_trend(self, prices, period):
        """MA 趋势评分"""
        if len(prices) < period:
            return 50
        ma = prices.iloc[-period:].mean()
        current = prices.iloc[-1]
        score = 50 + (current - ma) / ma * 100
        return max(0, min(100, score))
    
    def _calc_macd(self, prices):
        """MACD 评分"""
        if len(prices) < 26 + 9:
            return 50
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        diff = ema12 - ema26
        dea = diff.ewm(span=9).mean()
        macd = (diff - dea) * 2
        
        # 金叉加分，死叉减分
        if diff.iloc[-1] > dea.iloc[-1]:
            score = 60 + min(40, macd.iloc[-1] * 10)
        else:
            score = 40 + min(40, macd.iloc[-1] * 10)
        return max(0, min(100, score))
    
    def _calc_rsi(self, prices, period=14):
        """RSI 评分"""
        if len(prices) < period + 1:
            return 50
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        
        # RSI 越低越好（超卖机会）
        if rsi_val < 30:
            return 80
        elif rsi_val < 50:
            return 60
        elif rsi_val < 70:
            return 40
        else:
            return 20
    
    def _calc_kdj(self, kline):
        """KDJ 评分"""
        if len(kline) < 9:
            return 50, 50
        low_9 = kline['low'].iloc[-9:].min()
        high_9 = kline['high'].iloc[-9:].max()
        close = kline['close'].iloc[-1]
        
        if high_9 == low_9:
            rsv = 50
        else:
            rsv = (close - low_9) / (high_9 - low_9) * 100
        
        # 简化计算
        k = rsv * 0.6 + 50 * 0.4
        d = k * 0.6 + 50 * 0.4
        
        # KDJ 越低越好
        score_k = 100 - k
        score_d = 100 - d
        return max(0, min(100, score_k)), max(0, min(100, score_d))
    
    def _calc_boll_position(self, prices, period=20, std_dev=2):
        """布林带位置评分"""
        if len(prices) < period:
            return 50
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        current = prices.iloc[-1]
        upper_val = upper.iloc[-1]
        lower_val = lower.iloc[-1]
        
        if upper_val == lower_val:
            return 50
        
        position = (current - lower_val) / (upper_val - lower_val)
        
        # 越接近下轨越好
        score = 100 - position * 80
        return max(0, min(100, score))
    
    def _calc_cci(self, kline, period=14):
        """CCI 评分"""
        if len(kline) < period:
            return 50
        tp = (kline['high'] + kline['low'] + kline['close']) / 3
        ma_tp = tp.rolling(window=period).mean()
        md = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        cci = (tp - ma_tp) / (0.015 * md.replace(0, np.nan))
        val = cci.iloc[-1]
        if np.isnan(val):
            return 50
        # CCI < -100 超卖(机会), > 100 超买(风险)
        if val < -100:
            return 85
        elif val < 0:
            return 60
        elif val < 100:
            return 45
        else:
            return 25
    
    def _calc_wr(self, kline, period=14):
        """WR(威廉指标) 评分"""
        if len(kline) < period:
            return 50
        high_n = kline['high'].iloc[-period:].max()
        low_n = kline['low'].iloc[-period:].min()
        close = kline['close'].iloc[-1]
        if high_n == low_n:
            return 50
        wr = (high_n - close) / (high_n - low_n) * 100
        # WR > 80 超卖(机会), < 20 超买(风险)
        if wr > 80:
            return 85
        elif wr > 50:
            return 60
        elif wr > 20:
            return 45
        else:
            return 25
    
    def _calc_adx(self, kline, period=14):
        """ADX(趋势强度) 评分"""
        if len(kline) < period + 1:
            return 50
        high = kline['high']
        low = kline['low']
        close = kline['close']
        # +DM / -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': (high - close.shift(1)).abs(),
            'lc': (low - close.shift(1)).abs()
        }).max(axis=1)
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr.replace(0, np.nan)
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr.replace(0, np.nan)
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(window=period).mean()
        val = adx.iloc[-1]
        if np.isnan(val):
            return 50
        # ADX > 25 有趋势, > 50 强趋势
        if val > 50:
            return 85
        elif val > 25:
            return 70
        else:
            return 40
    
    # ========== 量价因子计算 ==========
    def _calc_volume_ratio(self, volumes):
        """量比评分"""
        if len(volumes) < 5:
            return 50
        avg_vol = volumes.iloc[-5:].mean()
        current_vol = volumes.iloc[-1]
        ratio = current_vol / avg_vol if avg_vol > 0 else 1
        
        # 量比 1.5-3 最好
        if 1.5 < ratio < 3:
            return 90
        elif 1 < ratio < 1.5:
            return 70
        elif ratio > 3:
            return 50
        else:
            return 40
    
    def _calc_turnover(self, quote, kline):
        """换手率评分 - 用量比近似"""
        if len(kline) < 10:
            return 50
        vols = kline['volume']
        avg_10 = vols.iloc[-10:].mean()
        avg_5 = vols.iloc[-5:].mean()
        if avg_10 <= 0:
            return 50
        ratio = avg_5 / avg_10
        # 近5日放量=活跃
        if 1.3 < ratio < 2.5:
            return 80
        elif 1.0 < ratio < 1.3:
            return 60
        elif ratio > 2.5:
            return 45  # 过度放量
        else:
            return 35  # 缩量
    
    def _calc_money_flow(self, kline):
        """资金流向评分 - 用价量关系近似"""
        if len(kline) < 5:
            return 50
        # 近5日：价涨量增=资金流入
        flow_score = 0
        for i in range(-5, 0):
            if i - 1 < -len(kline):
                continue
            price_up = kline['close'].iloc[i] > kline['close'].iloc[i-1]
            vol_up = kline['volume'].iloc[i] > kline['volume'].iloc[i-1]
            if price_up and vol_up:
                flow_score += 20  # 价涨量增
            elif price_up and not vol_up:
                flow_score += 5   # 缩量上涨
            elif not price_up and vol_up:
                flow_score -= 15  # 放量下跌
            else:
                flow_score -= 5   # 缩量下跌
        return max(0, min(100, 50 + flow_score))
    
    def _calc_price_volume(self, prices, volumes):
        """价量背离检测评分"""
        if len(prices) < 10:
            return 50
        # 价格趋势 vs 量能趋势
        price_trend = (prices.iloc[-1] - prices.iloc[-10]) / prices.iloc[-10]
        vol_trend = (volumes.iloc[-5:].mean() - volumes.iloc[-10:-5].mean()) / volumes.iloc[-10:-5].mean() if volumes.iloc[-10:-5].mean() > 0 else 0
        # 价涨量增=健康; 价涨量缩=背离风险
        if price_trend > 0 and vol_trend > 0:
            return 80  # 健康上涨
        elif price_trend > 0 and vol_trend < -0.2:
            return 35  # 顶背离风险
        elif price_trend < 0 and vol_trend > 0.2:
            return 70  # 底部放量，可能见底
        elif price_trend < 0 and vol_trend < 0:
            return 40  # 缩量下跌
        else:
            return 55
    
    def _calc_obv(self, prices, volumes):
        """OBV(能量潮) 评分"""
        if len(prices) < 20:
            return 50
        # 计算OBV
        obv = [0]
        for i in range(1, len(prices)):
            if prices.iloc[i] > prices.iloc[i-1]:
                obv.append(obv[-1] + volumes.iloc[i])
            elif prices.iloc[i] < prices.iloc[i-1]:
                obv.append(obv[-1] - volumes.iloc[i])
            else:
                obv.append(obv[-1])
        # OBV趋势：近5日vs近20日
        obv_s = pd.Series(obv)
        obv_ma5 = obv_s.iloc[-5:].mean()
        obv_ma20 = obv_s.iloc[-20:].mean()
        if obv_ma20 == 0:
            return 50
        ratio = (obv_ma5 - obv_ma20) / abs(obv_ma20)
        if ratio > 0.1:
            return 80
        elif ratio > 0:
            return 60
        elif ratio > -0.1:
            return 40
        else:
            return 25
    
    def _calc_vr(self, prices, volumes, period=26):
        """VR(成交量比率) 评分"""
        if len(prices) < period:
            return 50
        up_vol = 0
        down_vol = 0
        for i in range(-period, 0):
            if prices.iloc[i] > prices.iloc[i-1]:
                up_vol += volumes.iloc[i]
            else:
                down_vol += volumes.iloc[i]
        if down_vol == 0:
            return 70
        vr = up_vol / down_vol * 100
        # VR 40-70 低位机会, 160-350 获利区, >450 警戒
        if vr < 40:
            return 85  # 极低位
        elif vr < 70:
            return 75
        elif vr < 160:
            return 55
        elif vr < 350:
            return 40
        else:
            return 20
    
    # ========== 位置因子计算 ==========
    def _calc_position(self, prices, period):
        """相对位置评分"""
        if len(prices) < period:
            return 50
        high = prices.iloc[-period:].max()
        low = prices.iloc[-period:].min()
        current = prices.iloc[-1]
        
        if high == low:
            return 50
        
        position = (current - low) / (high - low)
        
        # 越低越好
        score = 100 - position * 80
        return max(0, min(100, score))
    
    def _calc_ma_distance(self, prices):
        """均线偏离度评分"""
        if len(prices) < 20:
            return 50
        ma20 = prices.iloc[-20:].mean()
        current = prices.iloc[-1]
        distance = abs(current - ma20) / ma20 * 100
        
        # 偏离越小越好
        score = 100 - distance * 5
        return max(0, min(100, score))
    
    # ========== 动量因子计算 ==========
    def _calc_momentum(self, prices, period):
        """动量评分"""
        if len(prices) < period:
            return 50
        momentum = (prices.iloc[-1] - prices.iloc[-period]) / prices.iloc[-period] * 100
        
        # 适度上涨最好
        if 5 < momentum < 20:
            return 90
        elif 0 < momentum < 5:
            return 70
        elif momentum > 20:
            return 50  # 涨太多
        else:
            return 30  # 下跌
    
    # ========== 基本面因子计算 ==========
    def _calc_pe_score(self, pe):
        """PE 评分"""
        if pe < 0:
            return 30
        elif pe < 20:
            return 90
        elif pe < 30:
            return 70
        elif pe < 50:
            return 50
        else:
            return 30
    
    def _calc_pb_score(self, pb):
        """PB 评分"""
        if pb < 0:
            return 30
        elif pb < 2:
            return 90
        elif pb < 5:
            return 70
        else:
            return 50
    
    def _calc_ps_score(self, ps):
        """PS 评分"""
        if ps < 0:
            return 30
        elif ps < 5:
            return 90
        elif ps < 10:
            return 70
        else:
            return 50
    
    def _calc_roe_score(self, roe):
        """ROE 评分"""
        if roe < 0:
            return 30
        elif roe > 20:
            return 90
        elif roe > 10:
            return 70
        else:
            return 50
    
    def _calc_growth_score(self, growth):
        """增长率评分"""
        if growth < 0:
            return 30
        elif growth > 30:
            return 90
        elif growth > 15:
            return 70
        else:
            return 50
    
    def _calc_debt_score(self, debt):
        """负债率评分"""
        if debt < 30:
            return 90
        elif debt < 50:
            return 70
        elif debt < 70:
            return 50
        else:
            return 30
    
    # ========== 新增因子 V2.0 (2026-03-25) ==========
    
    # --- 主力资金/筹码因子（4个）---
    
    def _calc_main_force_ratio(self, quote):
        """主力净流入占比评分"""
        # 大单净流入/总成交额
        try:
            import requests
            code = quote.get('code', '')
            if not code:
                return 50
            secid = f'1.{code}' if code.startswith('6') else f'0.{code}'
            url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f62,f184,f66,f69,f72,f75,f78,f81,f84,f87'
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
            r = requests.get(url, headers=headers, timeout=5)
            d = r.json().get('data', {})
            if d:
                main_net = d.get('f62', 0)  # 主力净流入
                if main_net > 50000000:  # >5000万
                    return 90
                elif main_net > 10000000:  # >1000万
                    return 75
                elif main_net > 0:
                    return 60
                elif main_net > -10000000:
                    return 40
                else:
                    return 20
        except:
            pass
        return 50
    
    def _calc_big_order_ratio(self, quote):
        """大单占比评分"""
        try:
            import requests
            code = quote.get('code', '')
            if not code:
                return 50
            secid = f'1.{code}' if code.startswith('6') else f'0.{code}'
            url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f66,f69,f72,f75,f78,f81,f84,f87'
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
            r = requests.get(url, headers=headers, timeout=5)
            d = r.json().get('data', {})
            if d:
                super_big_in = d.get('f66', 0)  # 超大单流入
                big_in = d.get('f72', 0)         # 大单流入
                total_in = abs(d.get('f62', 1))   # 总流入
                if total_in > 0:
                    big_ratio = (super_big_in + big_in) / total_in * 100
                    if big_ratio > 60:
                        return 85
                    elif big_ratio > 40:
                        return 70
                    elif big_ratio > 20:
                        return 55
                    else:
                        return 35
        except:
            pass
        return 50
    
    def _calc_chip_concentration(self, kline):
        """筹码集中度评分（用价格振幅近似）"""
        if len(kline) < 10:
            return 50
        # 近10日振幅的标准差——越小说明筹码越集中
        recent = kline.iloc[-10:]
        amplitudes = (recent['high'] - recent['low']) / recent['close'] * 100
        avg_amp = amplitudes.mean()
        
        if avg_amp < 2:
            return 85  # 筹码高度集中
        elif avg_amp < 3:
            return 70
        elif avg_amp < 5:
            return 55
        elif avg_amp < 8:
            return 40
        else:
            return 25  # 筹码松散
    
    def _calc_consecutive_inflow(self, quote):
        """连续资金流入天数评分"""
        # 简化：用当天主力净流入判断
        try:
            import requests
            code = quote.get('code', '')
            if not code:
                return 50
            secid = f'1.{code}' if code.startswith('6') else f'0.{code}'
            url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f62'
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
            r = requests.get(url, headers=headers, timeout=5)
            d = r.json().get('data', {})
            if d:
                net = d.get('f62', 0)
                if net > 20000000:
                    return 80
                elif net > 0:
                    return 60
                elif net > -20000000:
                    return 40
                else:
                    return 25
        except:
            pass
        return 50
    
    # --- 板块联动因子（3个）---
    
    def _calc_sector_rank(self, sector):
        """板块排名评分"""
        try:
            from sector_tracker import BASE_WEIGHTS
            weight = BASE_WEIGHTS.get(sector, 5)
            if weight >= 12:
                return 90
            elif weight >= 8:
                return 70
            elif weight >= 5:
                return 50
            else:
                return 35
        except:
            return 50
    
    def _calc_sector_momentum(self, sector):
        """板块动量评分"""
        try:
            from eastmoney_api import EastmoneyAPI
            api = EastmoneyAPI()
            hot = api.get_hot_sectors()
            if hot:
                for s in hot:
                    if s.get('name', '') == sector:
                        chg = s.get('change', 0)
                        if chg > 3:
                            return 85
                        elif chg > 1:
                            return 70
                        elif chg > 0:
                            return 55
                        elif chg > -1:
                            return 40
                        else:
                            return 25
        except:
            pass
        return 50
    
    def _calc_relative_strength(self, prices):
        """个股相对强弱评分（vs大盘）"""
        if len(prices) < 5:
            return 50
        stock_chg = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5] * 100
        # 简化：>3%强势，<-3%弱势
        if stock_chg > 5:
            return 90
        elif stock_chg > 3:
            return 75
        elif stock_chg > 1:
            return 60
        elif stock_chg > -1:
            return 50
        elif stock_chg > -3:
            return 35
        else:
            return 20
    
    # --- 波动率因子（3个）---
    
    def _calc_atr(self, kline, period=14):
        """ATR平均真实波幅评分"""
        if len(kline) < period + 1:
            return 50
        high = kline['high']
        low = kline['low']
        close = kline['close']
        
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)
        
        atr = tr.rolling(period).mean().iloc[-1]
        atr_pct = atr / close.iloc[-1] * 100
        
        # ATR适中最好（有波动但不剧烈）
        if 2 < atr_pct < 4:
            return 80  # 适中波动
        elif 1 < atr_pct <= 2:
            return 65  # 偏低
        elif 4 <= atr_pct < 6:
            return 60  # 偏高
        elif atr_pct <= 1:
            return 40  # 太平静
        else:
            return 30  # 太剧烈
    
    def _calc_volatility(self, prices, period=20):
        """历史波动率评分"""
        if len(prices) < period:
            return 50
        returns = prices.pct_change().dropna()
        vol = returns.iloc[-period:].std() * (252 ** 0.5) * 100
        
        if 15 < vol < 35:
            return 75  # 适中
        elif 10 < vol <= 15:
            return 60
        elif 35 <= vol < 50:
            return 55
        elif vol <= 10:
            return 40
        else:
            return 30
    
    def _calc_boll_width(self, prices, period=20):
        """布林带宽评分（窄→即将突破）"""
        if len(prices) < period:
            return 50
        ma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = ma + 2 * std
        lower = ma - 2 * std
        width = ((upper - lower) / ma * 100).iloc[-1]
        
        # 带宽窄=即将变盘
        if width < 5:
            return 85  # 极窄，大概率要突破
        elif width < 10:
            return 70
        elif width < 15:
            return 55
        elif width < 25:
            return 45
        else:
            return 30  # 太宽，趋势不明
    
    # --- 技术形态因子（3个）---
    
    def _calc_ma_alignment(self, prices):
        """均线多头排列评分"""
        if len(prices) < 60:
            return 50
        ma5 = prices.iloc[-5:].mean()
        ma10 = prices.iloc[-10:].mean()
        ma20 = prices.iloc[-20:].mean()
        ma60 = prices.iloc[-60:].mean()
        
        # 多头排列：ma5>ma10>ma20>ma60
        score = 50
        if ma5 > ma10:
            score += 12
        if ma10 > ma20:
            score += 12
        if ma20 > ma60:
            score += 12
        if prices.iloc[-1] > ma5:
            score += 14
        
        return min(100, max(0, score))
    
    def _calc_volume_breakout(self, volumes):
        """放量突破评分"""
        if len(volumes) < 20:
            return 50
        avg_20 = volumes.iloc[-20:].mean()
        today_vol = volumes.iloc[-1]
        ratio = today_vol / avg_20 if avg_20 > 0 else 1
        
        if ratio > 3:
            return 90  # 巨量突破
        elif ratio > 2:
            return 80
        elif ratio > 1.5:
            return 70
        elif ratio > 1:
            return 55
        elif ratio > 0.7:
            return 40
        else:
            return 25
    
    def _calc_support_resistance(self, prices):
        """支撑压力位评分（距离支撑近=安全）"""
        if len(prices) < 20:
            return 50
        recent = prices.iloc[-20:]
        current = prices.iloc[-1]
        support = recent.min()
        resistance = recent.max()
        
        if resistance == support:
            return 50
        
        # 距离支撑的比例
        dist_to_support = (current - support) / (resistance - support)
        
        # 越接近支撑越安全
        if dist_to_support < 0.2:
            return 85  # 在支撑位附近
        elif dist_to_support < 0.4:
            return 70
        elif dist_to_support < 0.6:
            return 55
        elif dist_to_support < 0.8:
            return 40
        else:
            return 25  # 在压力位附近
    
    # --- 情绪面因子（3个）---
    
    def _calc_turnover_rate(self, quote):
        """换手率评分"""
        try:
            import requests
            code = quote.get('code', '')
            if not code:
                return 50
            secid = f'1.{code}' if code.startswith('6') else f'0.{code}'
            url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f171'
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
            r = requests.get(url, headers=headers, timeout=5)
            d = r.json().get('data', {})
            if d:
                tr = d.get('f171', 0) / 100
                # 适中换手最好
                if 3 < tr < 8:
                    return 80
                elif 1 < tr <= 3:
                    return 60
                elif 8 <= tr < 15:
                    return 55
                elif tr <= 1:
                    return 35
                else:
                    return 30
        except:
            pass
        return 50
    
    def _calc_price_limit_distance(self, quote):
        """距涨停距离评分"""
        price = quote.get('price', 0)
        pre_close = quote.get('pre_close', price)
        if pre_close <= 0:
            return 50
        change = (price - pre_close) / pre_close * 100
        limit = 20 if str(quote.get('code', '')).startswith('3') or str(quote.get('code', '')).startswith('68') else 10
        distance = limit - change
        
        if 2 < distance < 5:
            return 80  # 离涨停有空间但已经涨了不少
        elif 5 <= distance < 8:
            return 70  # 适中
        elif distance >= 8:
            return 50  # 还早
        elif 0 < distance <= 2:
            return 60  # 快涨停了
        else:
            return 40  # 已涨停或超
    
    def _calc_amp_score(self, kline):
        """当日振幅评分"""
        if kline.empty:
            return 50
        today = kline.iloc[-1]
        amp = (today['high'] - today['low']) / today['close'] * 100
        
        if 2 < amp < 5:
            return 75  # 适中活跃
        elif 1 < amp <= 2:
            return 55  # 偏弱
        elif 5 <= amp < 8:
            return 60  # 偏大
        elif amp <= 1:
            return 35  # 太弱
        else:
            return 40  # 太大
    
    # --- 补充因子（4个）---
    
    def _calc_north_flow(self):
        """北向资金方向评分"""
        try:
            import requests
            # 东财北向资金接口
            url = 'https://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f2,f3&fields2=f51,f52,f54,f56'
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
            r = requests.get(url, headers=headers, timeout=5)
            data = r.json().get('data', {})
            # s2n: 沪股通+深股通净流入
            s2n = data.get('s2n', [])
            if s2n:
                # 取最新一条
                latest = s2n[-1]
                parts = latest.split(',')
                if len(parts) >= 4:
                    net = float(parts[1]) if parts[1] != '-' else 0
                    if net > 5000000000:  # >50亿
                        return 90
                    elif net > 2000000000:
                        return 75
                    elif net > 0:
                        return 60
                    elif net > -2000000000:
                        return 40
                    else:
                        return 20
        except:
            pass
        return 50
    
    def _calc_gap_strength(self, kline):
        """跳空缺口强度评分"""
        if len(kline) < 2:
            return 50
        today = kline.iloc[-1]
        yesterday = kline.iloc[-2]
        
        # 向上跳空：今日最低 > 昨日最高
        gap_up = today['low'] - yesterday['high']
        # 向下跳空：今日最高 < 昨日最低  
        gap_down = yesterday['low'] - today['high']
        
        gap_pct = gap_up / yesterday['close'] * 100 if yesterday['close'] > 0 else 0
        
        if gap_pct > 2:
            return 85  # 强势跳空高开
        elif gap_pct > 1:
            return 75
        elif gap_pct > 0:
            return 65  # 小幅跳空
        elif gap_down > 0:
            gap_down_pct = gap_down / yesterday['close'] * 100
            if gap_down_pct > 2:
                return 20  # 跳空低开
            else:
                return 35
        else:
            return 50  # 无缺口
    
    def _calc_volume_ma_ratio(self, volumes):
        """量能趋势评分（5日均量 vs 20日均量）"""
        if len(volumes) < 20:
            return 50
        ma5_vol = volumes.iloc[-5:].mean()
        ma20_vol = volumes.iloc[-20:].mean()
        
        if ma20_vol <= 0:
            return 50
        
        ratio = ma5_vol / ma20_vol
        
        if ratio > 2.0:
            return 90  # 量能大幅放大
        elif ratio > 1.5:
            return 80
        elif ratio > 1.2:
            return 65
        elif ratio > 0.8:
            return 50  # 正常
        elif ratio > 0.5:
            return 35
        else:
            return 20  # 量能严重萎缩
    
    def _calc_price_efficiency(self, kline):
        """价格效率评分（涨幅/振幅，越接近1说明走势越干脆）"""
        if kline.empty:
            return 50
        today = kline.iloc[-1]
        change = today['close'] - kline.iloc[-2]['close'] if len(kline) >= 2 else 0
        amplitude = today['high'] - today['low']
        
        if amplitude <= 0:
            return 50
        
        efficiency = abs(change) / amplitude
        
        # 效率>0.8 说明走势干脆（不是冲高回落那种）
        if efficiency > 0.8 and change > 0:
            return 90  # 上涨且干脆
        elif efficiency > 0.6 and change > 0:
            return 75
        elif efficiency > 0.4 and change > 0:
            return 60
        elif efficiency > 0.6 and change < 0:
            return 30  # 下跌且干脆（不好）
        elif change > 0:
            return 55
        else:
            return 40


# ========== 测试 ==========
if __name__ == '__main__':
    print("="*60)
    print("30 因子量化模型测试")
    print("="*60)
    
    model = Factor30Model()
    
    # 测试数据
    prices = pd.Series([10 + i*0.1 + np.random.randn()*0.05 for i in range(60)])
    volumes = pd.Series([100000 + np.random.randn()*10000 for i in range(60)])
    highs = prices * 1.02
    lows = prices * 0.98
    
    kline = pd.DataFrame({
        'close': prices,
        'volume': volumes,
        'high': highs,
        'low': lows,
    })
    
    quote = {
        'code': 'test',
        'price': prices.iloc[-1],
        'change_pct': 2.0,
    }
    
    # 计算因子
    factors = model.calculate_all_factors(quote, kline)
    
    # 计算综合评分
    score = model.calculate_score(factors)
    
    print(f"\n综合评分：{score}")
    print(f"因子数量：{len(factors)}")
    print(f"\n前 10 大因子:")
    sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:10]
    for name, value in sorted_factors:
        print(f"  {name}: {value:.1f}")
    
    print("\n" + "="*60)
