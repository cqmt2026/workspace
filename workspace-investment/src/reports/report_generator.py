# -*- coding: utf-8 -*-
"""
excel-xlsx + minimax-xlsx Skill 集成
报告生成：策略报告/绩效分析/数据报表
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging; logger = logging

class ReportGenerator:
    """报告生成 Skill"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.output_dir = Path(__file__).parent.parent.parent / 'outputs' / 'reports'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_strategy_report(self, backtest_results: Dict, output_filename: str = None) -> str:
        """
        生成策略报告
        
        Args:
            backtest_results: 回测结果
            output_filename: 输出文件名
            
        Returns:
            输出文件路径
        """
        print("生成策略报告")
        
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'strategy_report_{timestamp}.xlsx'
        
        output_path = self.output_dir / output_filename
        
        # 创建 Excel 报告
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 1. 绩效指标
            metrics_df = pd.DataFrame({
                '指标': ['初始资金', '最终资金', '总收益', '年化收益', '最大回撤', '夏普比率', '交易次数', '胜率'],
                '数值': [
                    backtest_results.get('initial_capital', 0),
                    backtest_results.get('final_capital', 0),
                    f"{backtest_results.get('total_return', 0):.2f}%",
                    f"{backtest_results.get('annual_return', 0):.2f}%",
                    f"{backtest_results.get('max_drawdown', 0):.2f}%",
                    f"{backtest_results.get('sharpe_ratio', 0):.2f}",
                    backtest_results.get('total_trades', 0),
                    f"{backtest_results.get('win_rate', 0):.2f}%"
                ]
            })
            metrics_df.to_excel(writer, sheet_name='绩效指标', index=False)
            
            # 2. 交易记录
            if 'trades' in backtest_results:
                trades_df = pd.DataFrame(backtest_results['trades'])
                if not trades_df.empty:
                    trades_df.to_excel(writer, sheet_name='交易记录', index=False)
            
            # 3. 权益曲线
            if 'equity_curve' in backtest_results:
                equity_df = backtest_results['equity_curve']
                if isinstance(equity_df, pd.DataFrame):
                    equity_df.to_excel(writer, sheet_name='权益曲线', index=False)
            
            # 4. 月度收益
            if 'equity_curve' in backtest_results and isinstance(backtest_results['equity_curve'], pd.DataFrame):
                monthly_returns = self._calculate_monthly_returns(backtest_results['equity_curve'])
                monthly_returns.to_excel(writer, sheet_name='月度收益', index=False)
        
        print(f"报告已生成：{output_path}")
        return str(output_path)
    
    def _calculate_monthly_returns(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """计算月度收益"""
        if 'date' not in equity_df.columns or 'equity' not in equity_df.columns:
            return pd.DataFrame()
        
        equity_df = equity_df.copy()
        equity_df['date'] = pd.to_datetime(equity_df['date'])
        equity_df['month'] = equity_df['date'].dt.to_period('M')
        
        monthly = equity_df.groupby('month')['equity'].agg(['first', 'last'])
        monthly['return'] = (monthly['last'] - monthly['first']) / monthly['first'] * 100
        monthly = monthly.reset_index()
        monthly['month'] = monthly['month'].astype(str)
        
        return monthly[['month', 'return']]
    
    def generate_portfolio_report(self, positions: List[Dict], output_filename: str = None) -> str:
        """
        生成持仓报告
        
        Args:
            positions: 持仓列表
            output_filename: 输出文件名
            
        Returns:
            输出文件路径
        """
        print("生成持仓报告")
        
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'portfolio_report_{timestamp}.xlsx'
        
        output_path = self.output_dir / output_filename
        
        # 创建持仓 DataFrame
        df = pd.DataFrame(positions)
        
        # 计算盈亏
        if 'entry_price' in df.columns and 'current_price' in df.columns:
            df['profit'] = (df['current_price'] - df['entry_price']) * df['shares']
            df['profit_pct'] = (df['current_price'] - df['entry_price']) / df['entry_price'] * 100
        
        # 保存到 Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='持仓明细', index=False)
            
            # 汇总统计
            summary = pd.DataFrame({
                '指标': ['持仓数量', '总市值', '总盈亏', '平均盈亏率'],
                '数值': [
                    len(df),
                    f"{(df['current_price'] * df['shares']).sum():,.0f}" if 'current_price' in df.columns else 'N/A',
                    f"{df['profit'].sum():,.0f}" if 'profit' in df.columns else 'N/A',
                    f"{df['profit_pct'].mean():.2f}%" if 'profit_pct' in df.columns else 'N/A'
                ]
            })
            summary.to_excel(writer, sheet_name='汇总统计', index=False)
        
        print(f"持仓报告已生成：{output_path}")
        return str(output_path)
    
    def generate_risk_report(self, risk_metrics: Dict, output_filename: str = None) -> str:
        """
        生成风险报告
        
        Args:
            risk_metrics: 风险指标
            output_filename: 输出文件名
            
        Returns:
            输出文件路径
        """
        print("生成风险报告")
        
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'risk_report_{timestamp}.xlsx'
        
        output_path = self.output_dir / output_filename
        
        # 创建风险报告 DataFrame
        risk_df = pd.DataFrame({
            '风险指标': list(risk_metrics.keys()),
            '数值': [f"{v:.4f}" if isinstance(v, float) else str(v) for v in risk_metrics.values()]
        })
        
        # 保存到 Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            risk_df.to_excel(writer, sheet_name='风险指标', index=False)
        
        print(f"风险报告已生成：{output_path}")
        return str(output_path)


# 便捷函数
def generate_strategy_report(backtest_results: Dict, output_filename: str = None) -> str:
    """生成策略报告（便捷函数）"""
    generator = ReportGenerator()
    return generator.generate_strategy_report(backtest_results, output_filename)

def generate_portfolio_report(positions: List[Dict], output_filename: str = None) -> str:
    """生成持仓报告（便捷函数）"""
    generator = ReportGenerator()
    return generator.generate_portfolio_report(positions, output_filename)

def generate_risk_report(risk_metrics: Dict, output_filename: str = None) -> str:
    """生成风险报告（便捷函数）"""
    generator = ReportGenerator()
    return generator.generate_risk_report(risk_metrics, output_filename)


# 测试
if __name__ == '__main__':
    # 模拟回测结果
    backtest_results = {
        'initial_capital': 100000,
        'final_capital': 125000,
        'total_return': 25.0,
        'annual_return': 30.5,
        'max_drawdown': -12.3,
        'sharpe_ratio': 1.5,
        'total_trades': 50,
        'winning_trades': 30,
        'win_rate': 60.0,
        'trades': [
            {'date': '2024-01-01', 'symbol': '000001.SZ', 'action': 'buy', 'price': 10.5, 'shares': 1000},
            {'date': '2024-01-10', 'symbol': '000001.SZ', 'action': 'sell', 'price': 11.2, 'shares': 1000, 'profit': 700}
        ],
        'equity_curve': pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'equity': np.linspace(100000, 125000, 30) + np.random.normal(0, 1000, 30)
        })
    }
    
    # 测试策略报告生成
    report_path = generate_strategy_report(backtest_results)
    print(f"\n=== 策略报告生成 ===")
    print(f"报告路径：{report_path}")
    
    # 测试持仓报告生成
    positions = [
        {'code': '000001.SZ', 'name': '平安银行', 'shares': 1000, 'entry_price': 10.5, 'current_price': 11.2},
        {'code': '600519.SH', 'name': '贵州茅台', 'shares': 100, 'entry_price': 1800, 'current_price': 1850}
    ]
    report_path = generate_portfolio_report(positions)
    print(f"\n=== 持仓报告生成 ===")
    print(f"报告路径：{report_path}")
    
    # 测试风险报告生成
    risk_metrics = {
        'volatility': 0.25,
        'var_95': -0.03,
        'max_drawdown': -0.15,
        'beta': 1.2
    }
    report_path = generate_risk_report(risk_metrics)
    print(f"\n=== 风险报告生成 ===")
    print(f"报告路径：{report_path}")
