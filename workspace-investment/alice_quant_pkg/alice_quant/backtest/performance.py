"""绩效分析 - 收益/风险/显著性检验"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Optional
from datetime import datetime

from ..core.account import Account
from ..core.result import BacktestResult


class PerformanceAnalyzer:
    """绩效分析器"""

    def analyze(self, strategy_name: str, params: dict,
                start_date: str, end_date: str,
                account: Account, trades: List[dict],
                all_dates: List[str],
                data_version: str = '') -> BacktestResult:
        """生成绩效分析报告"""
        result = BacktestResult(
            strategy_name=strategy_name,
            params=params,
            start_date=start_date,
            end_date=end_date,
            data_version=data_version,
            trades=trades,
        )

        # 计算每日收益率
        daily_returns = self._calc_daily_returns(account, all_dates)
        result.daily_returns = daily_returns
        result.equity_curve = (1 + daily_returns).cumprod()
        result.drawdown_curve = self._calc_drawdown(result.equity_curve)

        # 收益指标
        result.total_return = (1 + daily_returns).prod() - 1
        years = max(len(all_dates) / 252, 0.1)
        result.annual_return = (1 + result.total_return) ** (1 / years) - 1

        # 风险指标
        result.max_drawdown = result.drawdown_curve.min()
        if result.drawdown_curve is not None:
            dd_series = result.drawdown_curve
            if not dd_series.empty:
                min_idx = dd_series.idxmin()
                result.max_drawdown = dd_series[min_idx]

        # 风险调整收益
        excess_returns = daily_returns  # 简化：假设无风险利率为0
        if len(excess_returns) > 0 and excess_returns.std() > 0:
            result.sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()

        # 交易统计
        if trades:
            result.total_trades = len(trades)
            win_trades = [t for t in trades if t.get('profit', 0) > 0]
            result.win_rate = len(win_trades) / len(trades) if trades else 0

            profits = [abs(t.get('profit', 0)) for t in win_trades]
            losses = [abs(t.get('profit', 0)) for t in trades if t.get('profit', 0) <= 0]
            avg_profit = np.mean(profits) if profits else 0
            avg_loss = np.mean(losses) if losses else 0
            result.profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0

        # 显著性检验（默认执行）
        result.significance = self._significance_test(daily_returns, result.win_rate, result.total_trades)

        result._run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        result._run_time = datetime.now().isoformat()

        return result

    def _calc_daily_returns(self, account: Account, all_dates: List[str]) -> pd.Series:
        """计算每日收益率"""
        # 简化版：从最终结果反推
        # 真实实现需要记录每日净值
        if not all_dates:
            return pd.Series([0.0])
        n = len(all_dates)
        returns = np.random.normal(0.001, 0.02, n)  # 占位，实际从交易记录计算
        return pd.Series(returns, index=all_dates)

    def _calc_drawdown(self, equity_curve: pd.Series) -> pd.Series:
        """计算回撤曲线"""
        if equity_curve is None or equity_curve.empty:
            return pd.Series([0.0])
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown

    def _significance_test(self, daily_returns: pd.Series, win_rate: float,
                           total_trades: int) -> dict:
        """显著性检验（默认执行）"""
        result = {
            'sharpe_p_value': 1.0,
            'sharpe_significant': False,
            'win_rate_p_value': 1.0,
            'win_rate_significant': False,
            'is_luck': True,
        }

        if daily_returns is None or len(daily_returns) < 10:
            return result

        n = len(daily_returns)
        sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std() if daily_returns.std() > 0 else 0

        # 夏普标准误
        se_sharpe = np.sqrt((1 + 0.5 * sharpe**2) / n)

        # 夏普t检验
        t_stat = sharpe / se_sharpe if se_sharpe > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))

        result['sharpe_p_value'] = p_value
        result['sharpe_significant'] = p_value < 0.05

        # 胜率二项检验
        if total_trades > 0:
            from scipy.stats import binom_test
            p_win = binom_test(int(total_trades * win_rate), total_trades, 0.5)
            result['win_rate_p_value'] = p_win
            result['win_rate_significant'] = p_win < 0.05

        result['is_luck'] = not (result['sharpe_significant'] or result['win_rate_significant'])

        return result