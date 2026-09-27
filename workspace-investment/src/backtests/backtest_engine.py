# -*- coding: utf-8 -*-
"""
回测引擎层
任何策略如果不能被回测或模拟验证，都不属于生产系统
真正的策略工厂必须能回答：如果过去运行这个规则，会发生什么
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging; logger = logging

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = []
    
    def reset(self):
        """重置回测状态"""
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(self, df: pd.DataFrame, strategy, signals_list: List[Dict]) -> Dict:
        """
        运行回测
        
        Args:
            df: 价格数据
            strategy: 策略实例
            signals_list: 信号列表（每天一个信号）
            
        Returns:
            回测结果字典
        """
        self.reset()
        
        print(f"开始回测，初始资金：{self.initial_capital}")
        
        for i, (idx, row) in enumerate(df.iterrows()):
            current_price = row['close']
            signals = signals_list[i] if i < len(signals_list) else {}
            
            # 记录权益曲线
            equity = self.capital + self.position * current_price
            self.equity_curve.append({
                'date': idx,
                'equity': equity,
                'capital': self.capital,
                'position': self.position,
            })
            
            # 检查是否持有仓位
            if self.position > 0:
                # 检查止损
                if strategy.check_stop_loss(current_price):
                    self._close_position(current_price, '止损')
                    continue
                
                # 检查止盈
                if strategy.check_take_profit(current_price):
                    self._close_position(current_price, '止盈')
                    continue
                
                # 检查出场条件
                if strategy.check_exit_condition(signals, current_price):
                    self._close_position(current_price, '出场信号')
                    continue
                
                # 检查策略失效
                if strategy.check_strategy_invalid(signals):
                    self._close_position(current_price, '策略失效')
                    continue
            else:
                # 检查入场条件
                if strategy.check_entry_condition(signals):
                    self._open_position(current_price, '入场信号')
        
        # 如果最后还有仓位，平仓
        if self.position > 0 and len(df) > 0:
            final_price = df['close'].iloc[-1]
            self._close_position(final_price, '回测结束')
        
        # 计算回测结果
        return self._calculate_results()
    
    def _open_position(self, price: float, reason: str):
        """开仓"""
        if self.position > 0:
            return
        
        # 计算可买数量（全仓）
        shares = int(self.capital * 0.95 / price)  # 留 5% 现金
        
        if shares > 0:
            cost = shares * price
            self.capital -= cost
            self.position = shares
            self.entry_price = price
            
            print(f"{reason}: 买入{shares}股 @ {price}, 花费{cost}")
            
            self.trades.append({
                'type': 'buy',
                'date': pd.Timestamp.now(),
                'price': price,
                'shares': shares,
                'reason': reason,
            })
    
    def _close_position(self, price: float, reason: str):
        """平仓"""
        if self.position <= 0:
            return
        
        revenue = self.position * price
        self.capital += revenue
        
        profit = revenue - self.position * self.entry_price
        profit_pct = profit / (self.position * self.entry_price) * 100
        
        print(f"{reason}: 卖出{self.position}股 @ {price}, 盈亏{profit:.2f} ({profit_pct:.2f}%)")
        
        self.trades.append({
            'type': 'sell',
            'date': pd.Timestamp.now(),
            'price': price,
            'shares': self.position,
            'profit': profit,
            'profit_pct': profit_pct,
            'reason': reason,
        })
        
        self.position = 0
        self.entry_price = 0
    
    def _calculate_results(self) -> Dict:
        """计算回测结果"""
        if not self.equity_curve:
            return {'error': '无回测数据'}
        
        equity_df = pd.DataFrame(self.equity_curve)
        
        # 总收益
        total_return = (equity_df['equity'].iloc[-1] - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益
        days = (equity_df['date'].iloc[-1] - equity_df['date'].iloc[0]).days
        if days > 0:
            annual_return = (1 + total_return / 100) ** (365 / days) - 1
        else:
            annual_return = 0
        
        # 最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # 夏普比率
        returns = equity_df['equity'].pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe = 0
        
        # 交易统计
        buy_trades = [t for t in self.trades if t['type'] == 'buy']
        sell_trades = [t for t in self.trades if t['type'] == 'sell']
        
        total_trades = len(sell_trades)
        winning_trades = len([t for t in sell_trades if t.get('profit', 0) > 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        avg_profit = np.mean([t.get('profit', 0) for t in sell_trades]) if sell_trades else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': equity_df['equity'].iloc[-1],
            'total_return': total_return,
            'annual_return': annual_return * 100,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'num_buy_trades': len(buy_trades),
            'num_sell_trades': len(sell_trades),
            'equity_curve': equity_df,
            'trades': self.trades,
        }


# 测试
if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from loaders.data_loader import get_loader
    from signals.signal_generator import SignalGenerator
    from strategies.strategy_definition import StrategyFactory
    
    # 加载数据
    loader = get_loader('A')
    df = loader.load_market_data('000001.SZ', '2023-01-01', '2024-12-31')
    
    if not df.empty:
        # 生成信号
        generator = SignalGenerator({})
        signals_list = []
        for i in range(len(df)):
            signals = generator.generate_all_signals(df.iloc[:i+1])
            signals_list.append(signals)
        
        # 创建策略
        factory = StrategyFactory({})
        strategy = factory.create_strategy('trend', '趋势跟踪 v1')
        
        # 运行回测
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(df, strategy, signals_list)
        
        print("\n=== 回测结果 ===")
        print(f"初始资金：{results['initial_capital']:,.0f}")
        print(f"最终资金：{results['final_capital']:,.0f}")
        print(f"总收益：{results['total_return']:.2f}%")
        print(f"年化收益：{results['annual_return']:.2f}%")
        print(f"最大回撤：{results['max_drawdown']:.2f}%")
        print(f"夏普比率：{results['sharpe_ratio']:.2f}")
        print(f"交易次数：{results['total_trades']}")
        print(f"胜率：{results['win_rate']:.2f}%")
        print(f"平均盈亏：{results['avg_profit']:.2f}")
