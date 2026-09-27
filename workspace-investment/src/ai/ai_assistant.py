# -*- coding: utf-8 -*-
"""
AI 辅助层 - 信号压缩与策略优化
AI 的作用不是告诉你买什么，而是帮你看到哪些变量正在变化
AI 辅助把模糊想法转化为明确条件
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import logging; logger = logging

class AIAssistant:
    """AI 辅助助手"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.model = self.config.get('model', 'qwen')
        self.api_endpoint = self.config.get('api_endpoint', '')
    
    def compress_signals(self, signals: Dict, df: pd.DataFrame) -> Dict:
        """
        信号压缩 - 将复杂数据压缩为可读结构
        
        Args:
            signals: 原始信号字典
            df: 价格数据
            
        Returns:
            压缩后的信号结构
        """
        compressed = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(signals, df),
            'key_changes': self._identify_key_changes(signals, df),
            'anomalies': self._detect_anomalies(signals, df),
            'actionable_insights': self._generate_insights(signals, df)
        }
        
        print(f"[AI] 信号压缩完成：发现{len(compressed['key_changes'])}个关键变化，{len(compressed['anomalies'])}个异常")
        return compressed
    
    def _generate_summary(self, signals: Dict, df: pd.DataFrame) -> str:
        """生成市场状态摘要"""
        trend = signals.get('trend', {})
        volatility = signals.get('volatility', {})
        volume = signals.get('volume', {})
        
        # 趋势描述
        trend_desc = {
            3: '强势上涨',
            2: '上涨',
            1: '震荡偏强',
            0: '震荡',
            -1: '震荡偏弱',
            -2: '下跌',
            -3: '强势下跌'
        }
        trend_text = trend_desc.get(trend.get('trend_score', 0), '未知')
        
        # 波动率描述
        vol_text = volatility.get('vol_state', '正常')
        
        # 成交量描述
        volume_text = volume.get('volume_signal', '正常')
        
        summary = f"当前市场处于{trend_text}状态，波动率{vol_text}，成交量{volume_text}。"
        
        return summary
    
    def _identify_key_changes(self, signals: Dict, df: pd.DataFrame) -> List[Dict]:
        """识别关键变化"""
        changes = []
        
        # 趋势变化
        trend = signals.get('trend', {})
        if trend.get('golden_cross'):
            changes.append({
                'type': '趋势',
                'change': '金叉',
                'description': 'MA20 上穿 MA60，形成金叉',
                'importance': '高'
            })
        elif trend.get('death_cross'):
            changes.append({
                'type': '趋势',
                'change': '死叉',
                'description': 'MA20 下穿 MA60，形成死叉',
                'importance': '高'
            })
        
        # 波动率变化
        volatility = signals.get('volatility', {})
        if volatility.get('vol_change', 0) > 0.5:
            changes.append({
                'type': '波动率',
                'change': '急剧上升',
                'description': f'波动率上升{volatility.get("vol_change", 0):.1%}',
                'importance': '高'
            })
        elif volatility.get('vol_change', 0) < -0.3:
            changes.append({
                'type': '波动率',
                'change': '压缩',
                'description': '波动率压缩，可能突破',
                'importance': '中'
            })
        
        # 成交量变化
        volume = signals.get('volume', {})
        if volume.get('volume_ratio', 1) > 2:
            changes.append({
                'type': '成交量',
                'change': '放量',
                'description': f'成交量放大{volume.get("volume_ratio", 1):.1f}倍',
                'importance': '中'
            })
        elif volume.get('volume_ratio', 1) < 0.5:
            changes.append({
                'type': '成交量',
                'change': '缩量',
                'description': '成交量萎缩',
                'importance': '中'
            })
        
        # 价格异常
        anomaly = signals.get('anomaly', {})
        if anomaly.get('new_high'):
            changes.append({
                'type': '价格',
                'change': '新高',
                'description': '创 60 日新高',
                'importance': '高'
            })
        elif anomaly.get('new_low'):
            changes.append({
                'type': '价格',
                'change': '新低',
                'description': '创 60 日新低',
                'importance': '高'
            })
        
        return changes
    
    def _detect_anomalies(self, signals: Dict, df: pd.DataFrame) -> List[Dict]:
        """检测异常"""
        anomalies = []
        
        # 极端涨跌幅
        anomaly = signals.get('anomaly', {})
        if anomaly.get('extreme_gain'):
            anomalies.append({
                'type': '极端上涨',
                'description': '涨跌幅超过 3 倍标准差',
                'action': '警惕回调'
            })
        elif anomaly.get('extreme_loss'):
            anomalies.append({
                'type': '极端下跌',
                'description': '涨跌幅超过 3 倍标准差',
                'action': '关注反弹机会'
            })
        
        # 缺口
        if anomaly.get('gap_up') and anomaly.get('gap_size', 0) > 0.05:
            anomalies.append({
                'type': '向上缺口',
                'description': f'向上缺口{anomaly.get("gap_size", 0):.1%}',
                'action': '观察缺口是否回补'
            })
        elif anomaly.get('gap_down') and abs(anomaly.get('gap_size', 0)) > 0.05:
            anomalies.append({
                'type': '向下缺口',
                'description': f'向下缺口{abs(anomaly.get("gap_size", 0)):.1%}',
                'action': '观察缺口是否回补'
            })
        
        # 布林带极端位置
        volatility = signals.get('volatility', {})
        bb_pos = volatility.get('bb_position', 0.5)
        if bb_pos > 0.95:
            anomalies.append({
                'type': '超买',
                'description': '价格接近布林带上轨',
                'action': '警惕回调'
            })
        elif bb_pos < 0.05:
            anomalies.append({
                'type': '超卖',
                'description': '价格接近布林带下轨',
                'action': '关注反弹'
            })
        
        return anomalies
    
    def _generate_insights(self, signals: Dict, df: pd.DataFrame) -> List[str]:
        """生成可操作的洞察"""
        insights = []
        
        trend = signals.get('trend', {})
        volatility = signals.get('volatility', {})
        volume = signals.get('volume', {})
        
        # 趋势 + 成交量
        if trend.get('trend_score', 0) >= 2 and volume.get('volume_signal') == '放量上涨':
            insights.append('趋势强劲且放量上涨，可考虑跟随趋势')
        
        # 趋势 + 波动率
        if trend.get('trend_score', 0) >= 2 and volatility.get('vol_signal') == '低风险':
            insights.append('趋势良好且波动率低，风险可控')
        
        # 波动率压缩
        if volatility.get('vol_state') == '波动率压缩':
            insights.append('波动率压缩，即将出现方向性突破，等待明确信号')
        
        # 量价背离
        if trend.get('trend_score', 0) >= 2 and volume.get('volume_signal') == '缩量':
            insights.append('上涨但缩量，警惕动能不足')
        
        # 高风险环境
        if volatility.get('vol_signal') == '高风险':
            insights.append('波动率急剧上升，建议降低仓位或观望')
        
        return insights
    
    def optimize_strategy_rules(self, strategy_name: str, trade_log: List[Dict]) -> Dict:
        """
        优化策略规则
        
        Args:
            strategy_name: 策略名称
            trade_log: 交易记录
            
        Returns:
            优化建议
        """
        print(f"[AI] 分析策略 {strategy_name} 的{len(trade_log)}笔交易...")
        
        # 分析盈利交易特征
        winning_trades = [t for t in trade_log if t.get('profit', 0) > 0]
        losing_trades = [t for t in trade_log if t.get('profit', 0) <= 0]
        
        # 提取特征
        winning_features = self._extract_features(winning_trades)
        losing_features = self._extract_features(losing_trades)
        
        # 生成优化建议
        recommendations = {
            'entry_conditions': self._optimize_entry_conditions(winning_features, losing_features),
            'exit_conditions': self._optimize_exit_conditions(winning_trades, losing_trades),
            'risk_management': self._optimize_risk_management(losing_trades),
            'environment_filter': self._optimize_environment_filter(winning_features, losing_features)
        }
        
        print(f"[AI] 生成{len(recommendations['entry_conditions'])}条入场优化建议")
        print(f"[AI] 生成{len(recommendations['exit_conditions'])}条出场优化建议")
        print(f"[AI] 生成{len(recommendations['risk_management'])}条风控优化建议")
        
        return recommendations
    
    def _extract_features(self, trades: List[Dict]) -> Dict:
        """提取交易特征"""
        if not trades:
            return {}
        
        features = {
            'avg_trend_score': np.mean([t.get('trend_score', 0) for t in trades]),
            'avg_volume_ratio': np.mean([t.get('volume_ratio', 1) for t in trades]),
            'volatility_distribution': {},
            'trend_distribution': {}
        }
        
        # 波动率分布
        for t in trades:
            vol = t.get('volatility', '未知')
            features['volatility_distribution'][vol] = features['volatility_distribution'].get(vol, 0) + 1
        
        # 趋势分布
        for t in trades:
            trend = t.get('market_trend', '未知')
            features['trend_distribution'][trend] = features['trend_distribution'].get(trend, 0) + 1
        
        return features
    
    def _optimize_entry_conditions(self, winning: Dict, losing: Dict) -> List[str]:
        """优化入场条件"""
        recommendations = []
        
        # 趋势评分分析
        if winning.get('avg_trend_score', 0) > losing.get('avg_trend_score', 0) + 1:
            recommendations.append(
                f"建议增加趋势过滤：trend_score >= {int(winning.get('avg_trend_score', 2))} 时入场，"
                f"当前亏损交易平均 trend_score 为{losing.get('avg_trend_score', 0):.1f}"
            )
        
        # 成交量分析
        if winning.get('avg_volume_ratio', 1) > losing.get('avg_volume_ratio', 1) + 0.5:
            recommendations.append(
                f"建议增加成交量确认：volume_ratio >= {winning.get('avg_volume_ratio', 1):.1f} 时入场，"
                f"亏损交易平均 volume_ratio 为{losing.get('avg_volume_ratio', 1):.1f}"
            )
        
        return recommendations
    
    def _optimize_exit_conditions(self, winning: List[Dict], losing: List[Dict]) -> List[str]:
        """优化出场条件"""
        recommendations = []
        
        # 分析盈利交易的持有时间
        if winning:
            avg_win_hold = np.mean([t.get('hold_days', 5) for t in winning])
            recommendations.append(f"盈利交易平均持有{avg_win_hold:.1f}天，可考虑在此时间附近设置目标止盈")
        
        # 分析亏损交易的最大亏损
        if losing:
            avg_loss = np.mean([t.get('profit_pct', 0) for t in losing])
            recommendations.append(f"亏损交易平均亏损{avg_loss:.1f}%，建议设置止损在{avg_loss * 0.8:.1f}%左右")
        
        return recommendations
    
    def _optimize_risk_management(self, losing: List[Dict]) -> List[str]:
        """优化风险管理"""
        recommendations = []
        
        if not losing:
            return recommendations
        
        # 分析大亏损
        big_losses = [t for t in losing if t.get('profit_pct', 0) < -5]
        if big_losses:
            recommendations.append(
                f"发现{len(big_losses)}笔大亏损交易 (>5%)，建议："
                f"1) 设置单笔最大亏损限制 2) 高波动时降低仓位"
            )
        
        # 分析连续亏损
        consecutive_losses = 0
        max_consecutive = 0
        for t in losing:
            if t.get('profit', 0) < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0
        
        if max_consecutive >= 3:
            recommendations.append(
                f"发现最大连续亏损{max_consecutive}次，建议连续亏损{max_consecutive}次后暂停交易"
            )
        
        return recommendations
    
    def _optimize_environment_filter(self, winning: Dict, losing: Dict) -> List[str]:
        """优化环境过滤"""
        recommendations = []
        
        # 分析最佳趋势环境
        win_trend = winning.get('trend_distribution', {})
        if win_trend:
            best_trend = max(win_trend.items(), key=lambda x: x[1])[0]
            recommendations.append(f"策略在'{best_trend}'趋势下表现最佳，建议在其他趋势中降低仓位")
        
        # 分析最佳波动环境
        win_vol = winning.get('volatility_distribution', {})
        if win_vol:
            best_vol = max(win_vol.items(), key=lambda x: x[1])[0]
            recommendations.append(f"策略在'{best_vol}'波动环境下表现最佳")
        
        return recommendations


# 便捷函数
def create_ai_assistant(config: Dict = None) -> AIAssistant:
    """创建 AI 助手"""
    return AIAssistant(config or {})


# 测试
if __name__ == '__main__':
    # 创建 AI 助手
    ai = create_ai_assistant()
    
    # 测试信号压缩
    print("=" * 70)
    print("AI 信号压缩测试")
    print("=" * 70)
    print()
    
    test_signals = {
        'trend': {'trend_score': 2, 'golden_cross': True},
        'volatility': {'vol_state': '正常', 'vol_change': 0.1},
        'volume': {'volume_signal': '放量上涨', 'volume_ratio': 2.5},
        'anomaly': {'new_high': False, 'extreme_gain': False}
    }
    
    # 生成测试数据
    dates = pd.date_range('2024-01-01', periods=252)
    df = pd.DataFrame({
        'close': np.linspace(10, 15, 252) + np.random.normal(0, 0.5, 252),
        'volume': np.random.uniform(1000000, 5000000, 252)
    }, index=dates)
    
    compressed = ai.compress_signals(test_signals, df)
    
    print("\n压缩结果:")
    print(f"摘要：{compressed['summary']}")
    print(f"\n关键变化 ({len(compressed['key_changes'])}个):")
    for change in compressed['key_changes']:
        print(f"  [{change['importance']}] {change['type']}: {change['change']} - {change['description']}")
    
    print(f"\n异常检测 ({len(compressed['anomalies'])}个):")
    for anomaly in compressed['anomalies']:
        print(f"  {anomaly['type']}: {anomaly['description']} - 建议：{anomaly['action']}")
    
    print(f"\n可操作洞察 ({len(compressed['actionable_insights'])}条):")
    for insight in compressed['actionable_insights']:
        print(f"  - {insight}")
    
    print()
    print()
    print("=" * 70)
    print("AI 策略优化测试")
    print("=" * 70)
    print()
    
    # 测试策略优化
    test_trade_log = [
        {'profit': 700, 'profit_pct': 6.67, 'trend_score': 2, 'volume_ratio': 1.5, 'volatility': '正常', 'market_trend': '上涨'},
        {'profit': -400, 'profit_pct': -3.57, 'trend_score': -1, 'volume_ratio': 0.8, 'volatility': '高风险', 'market_trend': '下跌'},
        {'profit': 1200, 'profit_pct': 10.5, 'trend_score': 3, 'volume_ratio': 2.0, 'volatility': '正常', 'market_trend': '上涨'},
    ]
    
    recommendations = ai.optimize_strategy_rules('趋势跟踪 v1', test_trade_log)
    
    print("\n优化建议:")
    print("\n【入场条件优化】")
    for rec in recommendations['entry_conditions']:
        print(f"  - {rec}")
    
    print("\n【出场条件优化】")
    for rec in recommendations['exit_conditions']:
        print(f"  - {rec}")
    
    print("\n【风险管理优化】")
    for rec in recommendations['risk_management']:
        print(f"  - {rec}")
    
    print("\n【环境过滤优化】")
    for rec in recommendations['environment_filter']:
        print(f"  - {rec}")
