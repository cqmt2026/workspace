#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票评分系统 V2.0
优化：技术指标 + 板块权重 + 消息面分析
"""

import pandas as pd
import numpy as np
from datetime import datetime
# 使用 Mock 数据模块替代真实 API
# from realtime_data import TencentDataAPI
from .mock_data import TencentDataAPI

# ========== 技术指标权重 ==========
TECH_WEIGHTS = {
    'trend': 0.15,      # 趋势分（MA20）- 降权，腾空间给波动率
    'momentum': 0.13,   # 动量分（5 日收益率）- 微调
    'volume': 0.10,     # 成交量分（量比）- 微调
    'macd': 0.10,       # MACD 指标 - 微调
    'rsi': 0.07,        # RSI 指标
    'boll': 0.07,       # 布林带位置
    'position': 0.06,   # 股价相对位置
    'sector': 0.05,     # 板块权重
    'relative_strength': 0.12,  # 相对强弱
    'volatility': 0.15, # 波动率（新增 2026-07-02）- 稳不是慢，是少交波动税
}

# ========== 消息面权重 ==========
NEWS_WEIGHTS = {
    'policy': 0.40,     # 政策利好
    'industry': 0.30,   # 行业利好
    'company': 0.20,    # 公司利好
    'market': 0.10,     # 市场情绪
}


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self):
        pass
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """
        计算 MACD 指标
        
        Args:
            prices: 价格序列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
        
        Returns:
            dict: MACD 指标值
        """
        if len(prices) < slow + signal:
            return {'diff': 0, 'dea': 0, 'macd': 0, 'score': 50}
        
        # 计算 EMA
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # 计算 DIFF
        diff = ema_fast - ema_slow
        
        # 计算 DEA
        dea = diff.ewm(span=signal, adjust=False).mean()
        
        # 计算 MACD 柱
        macd_bar = (diff - dea) * 2
        
        # 获取最新值
        diff_val = diff.iloc[-1]
        dea_val = dea.iloc[-1]
        macd_val = macd_bar.iloc[-1]
        
        # 计算评分（0-100）
        score = 50
        if diff_val > dea_val:  # 金叉
            score += 20
            if macd_val > 0:  # 零轴上金叉
                score += 15
        else:  # 死叉
            score -= 20
            if macd_val < 0:  # 零轴下死叉
                score -= 15
        
        score = max(0, min(100, score))
        
        return {
            'diff': diff_val,
            'dea': dea_val,
            'macd': macd_val,
            'score': score
        }
    
    def calculate_rsi(self, prices, period=14):
        """
        计算 RSI 指标
        
        Args:
            prices: 价格序列
            period: 周期
        
        Returns:
            dict: RSI 指标值
        """
        if len(prices) < period + 1:
            return {'rsi': 50, 'score': 50}
        
        # 计算涨跌幅
        delta = prices.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 计算 RS
        rs = avg_gain / avg_loss.replace(0, np.nan)
        
        # 计算 RSI
        rsi = 100 - (100 / (1 + rs))
        
        rsi_val = rsi.iloc[-1]
        
        # 计算评分（0-100）
        # RSI>70 超买，RSI<30 超卖
        # 2026-03-25优化：上涨趋势中RSI>70不应大幅扣分
        if rsi_val > 80:
            score = 45  # 极端超买，适度扣分
        elif rsi_val > 70:
            score = 55  # 超买但可能是强势延续（原30，上调）
        elif rsi_val > 50:
            score = 60 + (rsi_val - 50) * 1.0  # 强势区间加大分数（原0.8）
        elif rsi_val > 30:
            score = 40 + (rsi_val - 30) * 0.8  # 中性
        else:
            score = 70  # 超卖，机会好
        
        score = max(0, min(100, score))
        
        return {
            'rsi': rsi_val,
            'score': score
        }
    
    def calculate_boll(self, prices, period=20, std_dev=2):
        """
        计算布林带
        
        Args:
            prices: 价格序列
            period: 周期
            std_dev: 标准差倍数
        
        Returns:
            dict: 布林带指标值
        """
        if len(prices) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0, 'position': 0.5, 'score': 50}
        
        # 计算中轨
        middle = prices.rolling(window=period).mean()
        
        # 计算标准差
        std = prices.rolling(window=period).std()
        
        # 计算上下轨
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        # 获取最新值
        current_price = prices.iloc[-1]
        upper_val = upper.iloc[-1]
        middle_val = middle.iloc[-1]
        lower_val = lower.iloc[-1]
        
        # 计算价格位置（0-1）
        if upper_val == lower_val:
            position = 0.5
        else:
            position = (current_price - lower_val) / (upper_val - lower_val)
        
        # 计算评分
        # 价格在下轨附近是买入机会
        if position < 0.2:
            score = 80  # 超卖
        elif position < 0.4:
            score = 60  # 偏低
        elif position < 0.6:
            score = 50  # 中性
        elif position < 0.8:
            score = 40  # 偏高
        else:
            score = 20  # 超买
        
        return {
            'upper': upper_val,
            'middle': middle_val,
            'lower': lower_val,
            'position': position,
            'score': score
        }
    
    def calculate_position(self, prices, high_low_period=60):
        """
        计算股价相对位置（60 日高低点）
        
        Args:
            prices: 价格序列
            high_low_period: 高低点周期（默认 60 日）
        
        Returns:
            dict: 股价位置指标值
        """
        if len(prices) < high_low_period:
            return {'position': 0.5, 'score': 50, 'level': '中位'}
        
        # 获取 60 日最高/最低
        high_60 = prices.iloc[-high_low_period:].max()
        low_60 = prices.iloc[-high_low_period:].min()
        current_price = prices.iloc[-1]
        
        # 计算相对位置（0-1）
        if high_60 == low_60:
            position = 0.5
        else:
            position = (current_price - low_60) / (high_60 - low_60)
        
        # 计算评分（低位加分，高位减分）
        # 2026-03-25优化：高位不过度扣分，强势股本来就在高位
        if position < 0.2:
            score = 90  # 极低位置
            level = '低位'
        elif position < 0.3:
            score = 80  # 低位置
            level = '低位'
        elif position < 0.4:
            score = 70  # 偏低
            level = '偏低'
        elif position < 0.5:
            score = 60  # 中低位
            level = '中位'
        elif position < 0.6:
            score = 55  # 中位（原50）
            level = '中位'
        elif position < 0.7:
            score = 50  # 中高位（原40）
            level = '偏高'
        elif position < 0.8:
            score = 45  # 偏高（原30）
            level = '高位'
        else:
            score = 40  # 极高位置（原20）
            level = '高位'
        
        return {
            'position': position,
            'score': score,
            'level': level,
            'high_60': high_60,
            'low_60': low_60,
        }

    def calculate_volatility(self, prices, period=20):
        """
        计算波动率评分
        
        数学原理：(1+r)(1-r)=1-r²，波动本身消耗本金
        同等收益下，低波动组合的复利效果更好
        
        Args:
            prices: 价格序列
            period: 计算周期（默认20日）
        
        Returns:
            dict: 波动率指标值
        """
        if len(prices) < period:
            return {'volatility': 0, 'score': 50, 'level': '未知'}
        
        # 计算对数收益率
        returns = np.log(prices / prices.shift(1)).dropna()
        recent_returns = returns.iloc[-period:]
        
        # 年化波动率
        daily_vol = recent_returns.std()
        annual_vol = daily_vol * np.sqrt(252)
        
        # 波动率损耗估算：(1+r_avg)^n - product(1+r_i)
        # 近似 = -vol²/2
        vol_drag = -(annual_vol ** 2) / 2
        
        # 评分：低波动加分，高波动减分
        # A股平均年化波动率约25-30%
        if annual_vol < 0.15:
            score = 90
            level = '极低波动'
        elif annual_vol < 0.22:
            score = 80
            level = '低波动'
        elif annual_vol < 0.30:
            score = 65
            level = '中等波动'
        elif annual_vol < 0.40:
            score = 45
            level = '高波动'
        elif annual_vol < 0.55:
            score = 25
            level = '极高波动'
        else:
            score = 10
            level = '危险波动'
        
        return {
            'volatility': round(annual_vol, 4),
            'daily_vol': round(daily_vol, 4),
            'vol_drag': round(vol_drag, 4),
            'score': score,
            'level': level
        }

class NewsAnalyzer:
    """消息面分析器"""
    
    def __init__(self):
        # 简化版：预设消息评分
        # 实际应用中可接入新闻 API
        self.policy_news = {}
        self.industry_news = {}
        self.company_news = {}
    
    def analyze_policy(self, stock_code):
        """
        分析政策面
        
        Args:
            stock_code: 股票代码
        
        Returns:
            float: 政策面评分（0-100）
        """
        # 简化版：返回基础分
        # 实际应用中分析政策新闻
        return 60
    
    def analyze_industry(self, sector):
        """
        分析行业面
        
        Args:
            sector: 板块名称
        
        Returns:
            float: 行业面评分（0-100）
        """
        # 简化版：根据板块热度评分
        hot_sectors = ['半导体', '芯片', '人工智能', '新能源', '锂电池']
        if sector in hot_sectors:
            return 75
        else:
            return 55
    
    def analyze_company(self, stock_code):
        """
        分析公司面
        
        Args:
            stock_code: 股票代码
        
        Returns:
            float: 公司面评分（0-100）
        """
        # 简化版：返回基础分
        # 实际应用中分析公司公告
        return 60
    
    def analyze_market_sentiment(self):
        """
        分析市场情绪
        
        Returns:
            float: 市场情绪评分（0-100）
        """
        # 简化版：返回基础分
        # 实际应用中分析大盘、资金流向等
        return 55
    
    def get_news_score(self, stock_code, sector):
        """
        获取消息面综合评分
        
        Args:
            stock_code: 股票代码
            sector: 板块名称
        
        Returns:
            float: 消息面综合评分（0-100）
        """
        policy_score = self.analyze_policy(stock_code)
        industry_score = self.analyze_industry(sector)
        company_score = self.analyze_company(stock_code)
        market_score = self.analyze_market_sentiment()
        
        # 加权计算
        total_score = (
            policy_score * NEWS_WEIGHTS['policy'] +
            industry_score * NEWS_WEIGHTS['industry'] +
            company_score * NEWS_WEIGHTS['company'] +
            market_score * NEWS_WEIGHTS['market']
        )
        
        return total_score


class StockScorer:
    """股票综合评分器"""
    
    def __init__(self):
        self.tech_analyzer = TechnicalAnalyzer()
        self.news_analyzer = NewsAnalyzer()
    
    def calculate_score(self, quote, kline, sector='其他', dynamic_weights=None):
        """
        计算股票综合评分
        
        Args:
            quote: 实时行情
            kline: K 线数据
            sector: 所属板块
            dynamic_weights: 动态板块权重
        
        Returns:
            dict: 评分详情
        """
        prices = kline['close']
        volumes = kline['volume']
        
        # 1. 趋势分（MA20）
        ma20 = prices.iloc[-20:].mean()
        current_price = prices.iloc[-1]
        trend_score = min(100, max(0, 50 + (current_price - ma20) / ma20 * 200))
        
        # 2. 动量分（5 日收益率）
        if len(prices) >= 5:
            mom_5d = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5] * 100
            momentum_score = min(100, max(0, 50 + mom_5d * 5))
        else:
            momentum_score = 50
        
        # 3. 成交量分（量比）
        if len(volumes) >= 5:
            avg_vol = volumes.iloc[-5:].mean()
            current_vol = volumes.iloc[-1]
            vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
            volume_score = min(100, max(0, 50 + (vol_ratio - 1) * 25))
        else:
            volume_score = 50
        
        # 4. MACD 分
        macd_result = self.tech_analyzer.calculate_macd(prices)
        macd_score = macd_result['score']
        
        # 5. RSI 分
        rsi_result = self.tech_analyzer.calculate_rsi(prices)
        rsi_score = rsi_result['score']
        
        # 6. 布林带分
        boll_result = self.tech_analyzer.calculate_boll(prices)
        boll_score = boll_result['score']
        
        # 7. 股价位置分（新增）
        position_result = self.tech_analyzer.calculate_position(prices)
        position_score = position_result['score']
        
        # 8. 板块权重分
        if dynamic_weights and sector in dynamic_weights:
            sector_score = min(100, max(0, 50 + (dynamic_weights[sector] - 5) * 5))
        else:
            sector_score = 50
        
        # 9. 相对强弱分（2026-03-25新增：个股涨跌vs大盘，强于大盘加分）
        stock_chg = 0
        if len(prices) >= 2:
            stock_chg = (prices.iloc[-1] - prices.iloc[-2]) / prices.iloc[-2] * 100
        # 相对强弱：涨幅越大越好，跌的扣分
        if stock_chg > 5:
            rs_score = 90
        elif stock_chg > 3:
            rs_score = 80
        elif stock_chg > 1:
            rs_score = 65
        elif stock_chg > 0:
            rs_score = 55
        elif stock_chg > -1:
            rs_score = 45
        elif stock_chg > -3:
            rs_score = 35
        else:
            rs_score = 20
        
        # 10. 波动率分（2026-07-02新增：稳不是慢，是少交波动税）
        vol_result = self.tech_analyzer.calculate_volatility(prices)
        volatility_score = vol_result['score']
        
        # 8. 消息面分
        news_score = self.news_analyzer.get_news_score(quote.get('code', ''), sector)
        
        # 综合评分
        total_score = (
            trend_score * TECH_WEIGHTS['trend'] +
            momentum_score * TECH_WEIGHTS['momentum'] +
            volume_score * TECH_WEIGHTS['volume'] +
            macd_score * TECH_WEIGHTS['macd'] +
            rsi_score * TECH_WEIGHTS['rsi'] +
            boll_score * TECH_WEIGHTS['boll'] +
            position_score * TECH_WEIGHTS['position'] +
            sector_score * TECH_WEIGHTS['sector'] +
            rs_score * TECH_WEIGHTS['relative_strength'] +
            volatility_score * TECH_WEIGHTS['volatility']
        )
        
        # 消息面加分（最多±10 分）
        news_bonus = (news_score - 50) * 0.2
        total_score += news_bonus
        
        total_score = max(0, min(100, total_score))
        
        return {
            'total_score': round(total_score, 1),
            'trend_score': round(trend_score, 1),
            'momentum_score': round(momentum_score, 1),
            'volume_score': round(volume_score, 1),
            'macd_score': round(macd_score, 1),
            'rsi_score': round(rsi_score, 1),
            'boll_score': round(boll_score, 1),
            'position_score': round(position_score, 1),
            'position_level': position_result['level'],
            'sector_score': round(sector_score, 1),
            'rs_score': round(rs_score, 1),
            'volatility_score': round(volatility_score, 1),
            'volatility_level': vol_result['level'],
            'news_score': round(news_score, 1),
            'news_bonus': round(news_bonus, 1),
        }


# ========== 测试 ==========
if __name__ == '__main__':
    print("="*60)
    print("股票评分系统 V2.0 测试")
    print("="*60)
    
    scorer = StockScorer()
    
    # 测试数据
    test_prices = pd.Series([10 + i * 0.1 + np.random.randn() * 0.05 for i in range(60)])
    test_volumes = pd.Series([100000 + np.random.randn() * 10000 for i in range(60)])
    
    test_kline = pd.DataFrame({
        'close': test_prices,
        'volume': test_volumes
    })
    
    test_quote = {
        'code': '000001',
        'price': test_prices.iloc[-1],
        'change_pct': 2.5
    }
    
    # 计算评分
    result = scorer.calculate_score(
        quote=test_quote,
        kline=test_kline,
        sector='银行',
        dynamic_weights={'银行': 12}
    )
    
    print(f"\n综合评分：{result['total_score']}")
    print(f"趋势分：{result['trend_score']}")
    print(f"动量分：{result['momentum_score']}")
    print(f"成交量分：{result['volume_score']}")
    print(f"MACD 分：{result['macd_score']}")
    print(f"RSI 分：{result['rsi_score']}")
    print(f"布林带分：{result['boll_score']}")
    print(f"板块分：{result['sector_score']}")
    print(f"消息分：{result['news_score']}")
    print(f"消息加分：{result['news_bonus']}")
    
    print("\n" + "="*60)
