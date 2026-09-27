"""绩效分析 - 收益/风险/显著性检验

从交易记录真实计算每日收益率，不再使用随机数占位。
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Optional, Dict, Any
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
        """生成绩效分析报告

        从交易记录真实计算每日收益率，不再使用随机数占位。

        Args:
            strategy_name: 策略名称
            params: 策略参数
            start_date: 开始日期
            end_date: 结束日期
            account: 最终账户状态
            trades: 交易记录列表
            all_dates: 所有交易日
            data_version: 数据版本

        Returns:
            BacktestResult
        """
        result = BacktestResult(
            strategy_name=strategy_name,
            params=params,
            start_date=start_date,
            end_date=end_date,
            data_version=data_version,
            trades=trades,
        )

        # 从交易记录计算每日净值
        daily_returns = self._calc_daily_returns(trades, all_dates, account.initial_capital)
        result.daily_returns = daily_returns
        result.equity_curve = (1 + daily_returns).cumprod()
        result.drawdown_curve = self._calc_drawdown(result.equity_curve)

        # 收益指标
        result.total_return = account.total_return()
        years = max(len(all_dates) / 252, 0.1)
        result.annual_return = (1 + result.total_return) ** (1 / years) - 1

        # 风险指标
        if result.drawdown_curve is not None and not result.drawdown_curve.empty:
            result.max_drawdown = result.drawdown_curve.min()

        # 风险调整收益
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            result.sharpe = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
            downside = daily_returns[daily_returns < 0]
            if len(downside) > 0 and downside.std() > 0:
                result.sortino = np.sqrt(252) * daily_returns.mean() / downside.std()

        # Calmar比率
        if result.max_drawdown != 0:
            result.calmar = result.annual_return / abs(result.max_drawdown)

        # 交易统计
        if trades:
            result.total_trades = len(trades)
            # 只对卖出交易算胜率（买入交易profit=0）
            sell_trades = [t for t in trades if t.get('direction') == 'sell']
            win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
            result.win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0

            profits = [t.get('profit', 0) for t in win_trades]
            losses = [t.get('profit', 0) for t in sell_trades if t.get('profit', 0) <= 0]
            avg_profit = np.mean(profits) if profits else 0
            avg_loss = abs(np.mean(losses)) if losses else 0
            result.profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0

        # 显著性检验
        result.significance = self._significance_test(daily_returns, result.win_rate, result.total_trades)

        result._run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        result._run_time = datetime.now().isoformat()

        return result

    def _calc_daily_returns(self, trades: List[dict], all_dates: List[str],
                           initial_capital: float) -> pd.Series:
        """从交易记录计算每日收益率

        方法：
        - 从初始资金开始
        - 每天记录账户净值变化
        - 有交易的日子：根据成交记录计算当日盈亏
        - 无交易的日子：收益率=0

        Args:
            trades: 交易记录
            all_dates: 所有交易日
            initial_capital: 初始资金

        Returns:
            pd.Series index=日期, values=日收益率
        """
        if not trades:
            return pd.Series(np.zeros(len(all_dates)), index=all_dates)

        # 按日期分组交易
        trade_by_date: Dict[str, List[dict]] = {}
        for t in trades:
            d = t.get('date', '')
            if d not in trade_by_date:
                trade_by_date[d] = []
            trade_by_date[d].append(t)

        # 模拟每日净值
        cash = initial_capital
        positions: Dict[str, dict] = {}  # {code: {volume, cost, last_price}}
        daily_returns = []

        for date in all_dates:
            prev_value = cash + sum(
                p['volume'] * p.get('last_price', p['cost'])
                for p in positions.values()
            )

            # 处理当日交易
            day_trades = trade_by_date.get(date, [])
            for t in day_trades:
                code = t.get('code', '')
                direction = t.get('direction', '')
                price = t.get('price', 0)
                volume = t.get('volume', 0)
                commission = t.get('commission', 0)
                tax = t.get('tax', 0)

                if direction == 'buy':
                    cost = price * volume + commission + tax
                    if cost <= cash:
                        cash -= cost
                        if code in positions:
                            p = positions[code]
                            total_vol = p['volume'] + volume
                            total_cost = p['volume'] * p['cost'] + price * volume
                            p['volume'] = total_vol
                            p['cost'] = total_cost / total_vol
                        else:
                            positions[code] = {'volume': volume, 'cost': price, 'last_price': price}
                elif direction == 'sell':
                    revenue = price * volume - commission - tax
                    cash += revenue
                    if code in positions:
                        p = positions[code]
                        p['volume'] -= volume
                        if p['volume'] <= 0:
                            del positions[code]

            # 更新持仓市值
            for code, p in positions.items():
                # 用当天交易价格更新，无交易则维持前值
                for t in day_trades:
                    if t.get('code') == code and t.get('direction') == 'buy':
                        p['last_price'] = t.get('price', p['last_price'])

            current_value = cash + sum(
                p['volume'] * p.get('last_price', p['cost'])
                for p in positions.values()
            )

            # 日收益率
            if prev_value > 0:
                daily_return = (current_value - prev_value) / prev_value
            else:
                daily_return = 0.0
            daily_returns.append(daily_return)

        return pd.Series(daily_returns, index=all_dates)

    def _calc_drawdown(self, equity_curve: pd.Series) -> pd.Series:
        """计算回撤曲线"""
        if equity_curve is None or equity_curve.empty:
            return pd.Series([0.0])
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown

    def _significance_test(self, daily_returns: pd.Series, win_rate: float,
                           total_trades: int) -> dict:
        """显著性检验

        默认执行夏普比率t检验和胜率二项检验。

        Returns:
            dict: 显著性检验结果
        """
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
        daily_std = daily_returns.std()
        if daily_std <= 0:
            return result

        sharpe = np.sqrt(252) * daily_returns.mean() / daily_std
        se_sharpe = np.sqrt((1 + 0.5 * sharpe**2) / n)
        t_stat = sharpe / se_sharpe if se_sharpe > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))

        result['sharpe'] = sharpe
        result['sharpe_p_value'] = p_value
        result['sharpe_significant'] = p_value < 0.05

        # 胜率二项检验
        if total_trades > 0:
            from scipy.stats import binomtest
            p_win = binomtest(int(total_trades * win_rate), total_trades, 0.5).pvalue
            result['win_rate_p_value'] = p_win
            result['win_rate_significant'] = p_win < 0.05

        result['is_luck'] = not (result['sharpe_significant'] or result['win_rate_significant'])

        return result

    def plot_equity_curve(self, result: BacktestResult, save_path: str = None):
        """绘制净值曲线图

        Args:
            result: 回测结果
            save_path: 保存路径，不传则显示
        """
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # 净值曲线
        ax1 = axes[0]
        equity = result.equity_curve
        if equity is not None:
            ax1.plot(equity.index, equity.values, label='策略净值', color='#1f77b4', linewidth=1.5)
            ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
            ax1.set_ylabel('净值')
            ax1.set_title(f'回测净值曲线 - {result.strategy_name}')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # 回撤曲线
        ax2 = axes[1]
        dd = result.drawdown_curve
        if dd is not None:
            ax2.fill_between(dd.index, 0, dd.values, color='red', alpha=0.3)
            ax2.plot(dd.index, dd.values, color='red', linewidth=1)
            ax2.set_ylabel('回撤')
            ax2.set_title(f'最大回撤: {result.max_drawdown:.2%}')
            ax2.grid(True, alpha=0.3)

        # 月度收益热力图
        ax3 = axes[2]
        if result.daily_returns is not None:
            monthly = result.daily_returns.copy()
            monthly.index = pd.to_datetime(monthly.index)
            monthly_ret = monthly.groupby([monthly.index.year, monthly.index.month]).sum()
            monthly_ret = monthly_ret.unstack(level=0)
            if not monthly_ret.empty:
                im = ax3.imshow(monthly_ret.values, cmap='RdYlGn', aspect='auto', vmin=-0.1, vmax=0.1)
                ax3.set_xticks(range(len(monthly_ret.columns)))
                ax3.set_xticklabels(monthly_ret.columns)
                ax3.set_yticks(range(len(monthly_ret.index)))
                ax3.set_yticklabels([f'{m}月' for m in monthly_ret.index])
                ax3.set_title('月度收益')
                plt.colorbar(im, ax=ax3, format='%.0f%%')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f'图表已保存: {save_path}')
        else:
            plt.show()

    def generate_full_report(self, result: BacktestResult, output_dir: str = 'reports'):
        """生成完整报告（HTML + 图表 + CSV）

        Args:
            result: 回测结果
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 1. HTML报告
        html_path = os.path.join(output_dir, f'{result.strategy_name}_report.html')
        result.save_report(html_path)

        # 2. 图表
        chart_path = os.path.join(output_dir, f'{result.strategy_name}_chart.png')
        self.plot_equity_curve(result, chart_path)

        # 3. 交易记录
        csv_path = os.path.join(output_dir, f'{result.strategy_name}_trades.csv')
        result.export_trades(csv_path)

        print(f'报告已生成: {output_dir}/')
        print(f'  - HTML: {os.path.basename(html_path)}')
        print(f'  - 图表: {os.path.basename(chart_path)}')
        print(f'  - CSV:  {os.path.basename(csv_path)}')