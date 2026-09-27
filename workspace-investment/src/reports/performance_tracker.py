# -*- coding: utf-8 -*-
"""
反馈层 - 策略表现记录与分析
记录策略表现、失败原因、适用市场环境
系统必须记录策略表现，否则不会进化，只会重复犯错
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

class PerformanceTracker:
    """策略表现追踪器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.output_dir = Path(__file__).parent.parent.parent / 'outputs' / 'logs'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 表现记录
        self.performance_log = []
        self.trade_log = []
        self.environment_log = []
    
    def record_trade(self, trade: Dict, signals: Dict, market_env: Dict):
        """
        记录单笔交易
        
        Args:
            trade: 交易信息
            signals: 入场时的信号
            market_env: 市场环境
        """
        profit_pct = trade.get('profit_pct', 0)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': trade.get('order_id', len(self.trade_log) + 1),
            'symbol': trade.get('symbol', ''),
            'action': trade.get('action', ''),
            'entry_price': trade.get('price', 0),
            'exit_price': trade.get('exit_price', 0),
            'shares': trade.get('shares', 0),
            'profit': trade.get('profit', 0),
            'profit_pct': profit_pct,
            'reason': trade.get('reason', ''),
            
            # 信号记录
            'trend_score': signals.get('trend', {}).get('trend_score', 0),
            'volatility': signals.get('volatility', {}).get('vol_signal', ''),
            'volume_signal': signals.get('volume', {}).get('volume_signal', ''),
            
            # 市场环境
            'market_trend': market_env.get('trend', ''),
            'market_volatility': market_env.get('volatility', ''),
            'market_sentiment': market_env.get('sentiment', ''),
            
            # 结果分类
            'outcome': self._classify_outcome(profit_pct),
            'success': profit_pct > 0
        }
        
        self.trade_log.append(record)
        print(f"[记录] 交易 {record['trade_id']}: {record['symbol']} {record['action']} "
              f"盈亏{record['profit']:.2f} ({profit_pct:.2f}%) - {record['outcome']}")
    
    def _classify_outcome(self, profit_pct: float) -> str:
        """分类交易结果"""
        if profit_pct >= 10:
            return '大赚'
        elif profit_pct >= 3:
            return '小赚'
        elif profit_pct >= 0:
            return '持平'
        elif profit_pct >= -5:
            return '小亏'
        else:
            return '大亏'
    
    def calculate_expected_value(self, window=20):
        """
        计算期望值(EV)和盈亏比
        
        数学原理：
        E = P(win) × W(avg_win) - P(loss) × L(avg_loss)
        E > 0 → 策略有效
        E < 0 → 策略有问题
        
        Args:
            window: 滚动窗口（默认最近20笔）
        
        Returns:
            dict: {'ev': float, 'win_rate': float, 'avg_win': float, 
                   'avg_loss': float, 'win_loss_ratio': float, 'sample_size': int}
        """
        if len(self.trade_log) < 5:
            return {'ev': 0, 'win_rate': 0, 'avg_win': 0, 'avg_loss': 0,
                    'win_loss_ratio': 0, 'sample_size': len(self.trade_log),
                    'message': '样本不足（<5笔）'}
        
        recent = self.trade_log[-window:]
        winning = [t for t in recent if t['success']]
        losing = [t for t in recent if not t['success']]
        
        n_win = len(winning)
        n_loss = len(losing)
        total = n_win + n_loss
        
        win_rate = n_win / total if total > 0 else 0
        
        avg_win_pct = sum(t['profit_pct'] for t in winning) / n_win if n_win > 0 else 0
        avg_loss_pct = sum(abs(t['profit_pct']) for t in losing) / n_loss if n_loss > 0 else 0
        
        # E = P(win) × avg_win - P(loss) × avg_loss
        ev = win_rate * avg_win_pct - (1 - win_rate) * avg_loss_pct
        
        # 盈亏比
        win_loss_ratio = avg_win_pct / avg_loss_pct if avg_loss_pct > 0 else 0
        
        return {
            'ev': round(ev, 4),
            'win_rate': round(win_rate, 4),
            'avg_win': round(avg_win_pct, 2),
            'avg_loss': round(avg_loss_pct, 2),
            'win_loss_ratio': round(win_loss_ratio, 2),
            'sample_size': total,
            'message': '正常' if total >= 5 else '样本不足'
        }
        """
        记录策略整体表现
        
        Args:
            strategy_name: 策略名称
            backtest_results: 回测结果
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'strategy_name': strategy_name,
            'total_return': backtest_results.get('total_return', 0),
            'annual_return': backtest_results.get('annual_return', 0),
            'max_drawdown': backtest_results.get('max_drawdown', 0),
            'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
            'total_trades': backtest_results.get('total_trades', 0),
            'win_rate': backtest_results.get('win_rate', 0),
            'avg_profit': backtest_results.get('avg_profit', 0),
            'grade': self._grade_strategy(backtest_results)
        }
        
        self.performance_log.append(record)
        print(f"[记录] 策略 {strategy_name} 表现：收益{record['total_return']:.2f}% "
              f"胜率{record['win_rate']:.2f}% - 评级{record['grade']}")
    
    def _grade_strategy(self, results: Dict) -> str:
        """策略评级"""
        score = 0
        
        # 收益评分 (0-40 分)
        total_return = results.get('total_return', 0)
        if total_return >= 50:
            score += 40
        elif total_return >= 30:
            score += 30
        elif total_return >= 15:
            score += 20
        elif total_return >= 5:
            score += 10
        
        # 风险控制评分 (0-30 分)
        max_drawdown = results.get('max_drawdown', 0)
        if max_drawdown >= -10:
            score += 30
        elif max_drawdown >= -20:
            score += 20
        elif max_drawdown >= -30:
            score += 10
        
        # 稳定性评分 (0-30 分)
        win_rate = results.get('win_rate', 0)
        sharpe = results.get('sharpe_ratio', 0)
        if win_rate >= 60 and sharpe >= 1.5:
            score += 30
        elif win_rate >= 50 and sharpe >= 1.0:
            score += 20
        elif win_rate >= 45 and sharpe >= 0.5:
            score += 10
        
        # 评级
        if score >= 80:
            return 'S'
        elif score >= 60:
            return 'A'
        elif score >= 40:
            return 'B'
        elif score >= 20:
            return 'C'
        else:
            return 'D'
    
    def analyze_failure_reasons(self) -> Dict:
        """分析失败原因"""
        if not self.trade_log:
            return {'error': '无交易记录'}
        
        losing_trades = [t for t in self.trade_log if not t['success']]
        
        if not losing_trades:
            return {'message': '无亏损交易'}
        
        # 失败原因统计
        failure_reasons = {
            '逆势交易': 0,
            '高波动亏损': 0,
            '缩量亏损': 0,
            '信号误判': 0,
            '其他': 0
        }
        
        for trade in losing_trades:
            if trade['trend_score'] < 0 and trade['action'] == 'buy':
                failure_reasons['逆势交易'] += 1
            elif trade['volatility'] == '高风险':
                failure_reasons['高波动亏损'] += 1
            elif trade['volume_signal'] == '缩量':
                failure_reasons['缩量亏损'] += 1
            elif abs(trade['profit_pct']) > 5:
                failure_reasons['信号误判'] += 1
            else:
                failure_reasons['其他'] += 1
        
        # 按结果分类统计
        outcome_stats = {}
        for trade in losing_trades:
            outcome = trade['outcome']
            if outcome not in outcome_stats:
                outcome_stats[outcome] = {'count': 0, 'total_loss': 0}
            outcome_stats[outcome]['count'] += 1
            outcome_stats[outcome]['total_loss'] += trade['profit']
        
        return {
            'total_losing_trades': len(losing_trades),
            'failure_reasons': failure_reasons,
            'outcome_stats': outcome_stats,
            'avg_loss': np.mean([t['profit'] for t in losing_trades]),
            'max_loss': min([t['profit'] for t in losing_trades]),
            'recommendations': self._generate_failure_recommendations(failure_reasons)
        }
    
    def _generate_failure_recommendations(self, failure_reasons: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if failure_reasons['逆势交易'] > 3:
            recommendations.append('增加趋势过滤条件，避免逆势交易')
        
        if failure_reasons['高波动亏损'] > 3:
            recommendations.append('在高波动环境下降低仓位或暂停交易')
        
        if failure_reasons['缩量亏损'] > 3:
            recommendations.append('增加成交量确认条件，避免缩量交易')
        
        if failure_reasons['信号误判'] > 3:
            recommendations.append('优化信号生成逻辑，增加确认条件')
        
        return recommendations
    
    def identify_suitable_environment(self) -> Dict:
        """识别适用市场环境"""
        if not self.trade_log:
            return {'error': '无交易记录'}
        
        winning_trades = [t for t in self.trade_log if t['success']]
        
        if not winning_trades:
            return {'message': '无盈利交易'}
        
        # 统计盈利交易的市场环境
        env_stats = {
            'trend': {},
            'volatility': {},
            'sentiment': {}
        }
        
        for trade in winning_trades:
            # 趋势环境
            trend = trade['market_trend']
            env_stats['trend'][trend] = env_stats['trend'].get(trend, 0) + 1
            
            # 波动率环境
            vol = trade['market_volatility']
            env_stats['volatility'][vol] = env_stats['volatility'].get(vol, 0) + 1
            
            # 情绪环境
            sent = trade['market_sentiment']
            env_stats['sentiment'][sent] = env_stats['sentiment'].get(sent, 0) + 1
        
        # 找出最适宜的环境
        suitable_env = {
            'best_trend': max(env_stats['trend'].items(), key=lambda x: x[1])[0] if env_stats['trend'] else 'N/A',
            'best_volatility': max(env_stats['volatility'].items(), key=lambda x: x[1])[0] if env_stats['volatility'] else 'N/A',
            'best_sentiment': max(env_stats['sentiment'].items(), key=lambda x: x[1])[0] if env_stats['sentiment'] else 'N/A'
        }
        
        return {
            'suitable_environment': suitable_env,
            'environment_stats': env_stats,
            'recommendations': self._generate_environment_recommendations(suitable_env)
        }
    
    def _generate_environment_recommendations(self, env: Dict) -> List[str]:
        """生成环境适配建议"""
        recommendations = []
        
        if env['best_trend'] == '上涨':
            recommendations.append('策略适合上涨趋势，建议在下行趋势中降低仓位')
        elif env['best_trend'] == '下跌':
            recommendations.append('策略适合下跌趋势（做空），建议在上涨趋势中谨慎')
        
        if env['best_volatility'] == '正常':
            recommendations.append('策略适合正常波动环境，高波动时需谨慎')
        elif env['best_volatility'] == '高波动':
            recommendations.append('策略适合高波动环境，可捕捉大幅波动机会')
        
        return recommendations
    
    def save_logs(self):
        """保存日志到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存交易记录
        if self.trade_log:
            trade_df = pd.DataFrame(self.trade_log)
            trade_path = self.output_dir / f'trade_log_{timestamp}.csv'
            trade_df.to_csv(trade_path, index=False, encoding='utf-8-sig')
            print(f"[保存] 交易记录：{trade_path}")
        
        # 保存策略表现
        if self.performance_log:
            perf_df = pd.DataFrame(self.performance_log)
            perf_path = self.output_dir / f'strategy_performance_{timestamp}.csv'
            perf_df.to_csv(perf_path, index=False, encoding='utf-8-sig')
            print(f"[保存] 策略表现：{perf_path}")
    
    def generate_report(self) -> str:
        """生成反馈报告"""
        report = []
        report.append("=" * 70)
        report.append("策略表现反馈报告")
        report.append("=" * 70)
        report.append("")
        
        # 总体表现
        if self.performance_log:
            latest = self.performance_log[-1]
            report.append("【策略总体表现】")
            report.append(f"  策略名称：{latest['strategy_name']}")
            report.append(f"  总收益：{latest['total_return']:.2f}%")
            report.append(f"  年化收益：{latest['annual_return']:.2f}%")
            report.append(f"  最大回撤：{latest['max_drawdown']:.2f}%")
            report.append(f"  夏普比率：{latest['sharpe_ratio']:.2f}")
            report.append(f"  胜率：{latest['win_rate']:.2f}%")
            report.append(f"  评级：{latest['grade']}")
            report.append("")
        
        # 交易统计
        if self.trade_log:
            winning = [t for t in self.trade_log if t['success']]
            losing = [t for t in self.trade_log if not t['success']]
            
            report.append("【交易统计】")
            report.append(f"  总交易数：{len(self.trade_log)}")
            report.append(f"  盈利交易：{len(winning)}")
            report.append(f"  亏损交易：{len(losing)}")
            report.append(f"  平均盈利：{np.mean([t['profit'] for t in winning]):.2f}" if winning else "  平均盈利：N/A")
            report.append(f"  平均亏损：{np.mean([t['profit'] for t in losing]):.2f}" if losing else "  平均亏损：N/A")
            
            # 期望值(EV)分析
            ev_data = self.calculate_expected_value()
            report.append("")
            report.append("【期望值(EV)分析】")
            report.append(f"  样本量：{ev_data['sample_size']}笔")
            report.append(f"  胜率：{ev_data['win_rate']*100:.1f}%")
            report.append(f"  平均盈利：{ev_data['avg_win']:.2f}%")
            report.append(f"  平均亏损：{ev_data['avg_loss']:.2f}%")
            report.append(f"  盈亏比：{ev_data['win_loss_ratio']:.2f}")
            report.append(f"  期望值(EV)：{ev_data['ev']:.4f}（{'✅ 正期望，策略有效' if ev_data['ev'] > 0 else '❌ 负期望，策略有问题' if ev_data['ev'] < 0 else '⚠️ 零期望，需优化'}）")
            report.append(f"  EV判断：{'E>0 → 赚钱 > 亏钱，策略有正期望' if ev_data['ev'] > 0 else 'E<0 → 亏钱 > 赚钱，策略方向需要调整' if ev_data['ev'] < 0 else 'E≈0 → 盈亏相抵，需要优化选股'}")
            report.append("")
            
            # 失败原因分析
            failure_analysis = self.analyze_failure_reasons()
            if 'failure_reasons' in failure_analysis:
                report.append("【失败原因分析】")
                for reason, count in failure_analysis['failure_reasons'].items():
                    if count > 0:
                        report.append(f"  {reason}: {count}次")
                report.append("")
                
                if failure_analysis.get('recommendations'):
                    report.append("【改进建议】")
                    for rec in failure_analysis['recommendations']:
                        report.append(f"  - {rec}")
                    report.append("")
            
            # 适用环境
            env_analysis = self.identify_suitable_environment()
            if 'suitable_environment' in env_analysis:
                report.append("【适用市场环境】")
                env = env_analysis['suitable_environment']
                report.append(f"  最佳趋势：{env['best_trend']}")
                report.append(f"  最佳波动：{env['best_volatility']}")
                report.append(f"  最佳情绪：{env['best_sentiment']}")
                report.append("")
        
        report.append("=" * 70)
        report.append(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        
        return "\n".join(report)


# 便捷函数
def create_tracker() -> PerformanceTracker:
    """创建表现追踪器"""
    return PerformanceTracker()


# 测试
if __name__ == '__main__':
    # 创建追踪器
    tracker = create_tracker()
    
    # 模拟交易记录
    test_trades = [
        {'order_id': 1, 'symbol': '000001.SZ', 'action': 'buy', 'price': 10.5, 'exit_price': 11.2, 'shares': 1000, 'profit': 700, 'profit_pct': 6.67, 'reason': '入场信号'},
        {'order_id': 2, 'symbol': '000001.SZ', 'action': 'sell', 'price': 11.2, 'exit_price': 10.8, 'shares': 1000, 'profit': -400, 'profit_pct': -3.57, 'reason': '出场信号'},
        {'order_id': 3, 'symbol': '000001.SZ', 'action': 'buy', 'price': 10.8, 'exit_price': 11.5, 'shares': 1000, 'profit': 700, 'profit_pct': 6.48, 'reason': '入场信号'},
    ]
    
    # 模拟信号和环境
    test_signals = {
        'trend': {'trend_score': 2},
        'volatility': {'vol_signal': '正常'},
        'volume': {'volume_signal': '放量上涨'}
    }
    
    test_env = {
        'trend': '上涨',
        'volatility': '正常',
        'sentiment': 'bullish'
    }
    
    # 记录交易
    print("记录交易...")
    for trade in test_trades:
        tracker.record_trade(trade, test_signals, test_env)
    
    print()
    
    # 记录策略表现
    print("记录策略表现...")
    backtest_results = {
        'total_return': 19.97,
        'annual_return': 9.54,
        'max_drawdown': -18.81,
        'sharpe_ratio': 0.49,
        'total_trades': 17,
        'win_rate': 47.06,
        'avg_profit': 1174.54
    }
    tracker.record_strategy_performance('趋势跟踪 v1', backtest_results)
    
    print()
    
    # 生成报告
    print(tracker.generate_report())
    
    # 保存日志
    tracker.save_logs()
