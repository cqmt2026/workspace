"""回测结果定义"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats


@dataclass
class BacktestResult:
    """回测结果

    回测引擎运行完成后返回的结果对象。
    包含绩效指标、显著性检验、交易记录等。
    """
    # 基本信息
    strategy_name: str = ''
    params: Dict[str, Any] = field(default_factory=dict)
    start_date: str = ''
    end_date: str = ''
    data_version: str = ''
    config_version: str = ''

    # 核心指标
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_start: str = ''
    max_drawdown_end: str = ''
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    total_trades: int = 0
    avg_hold_days: float = 0.0

    # Alpha/Beta
    alpha: float = 0.0
    beta: float = 0.0
    information_ratio: float = 0.0

    # 详细数据
    daily_returns: Optional[pd.Series] = None
    equity_curve: Optional[pd.Series] = None
    drawdown_curve: Optional[pd.Series] = None
    trades: List[Dict] = field(default_factory=list)
    monthly_returns: Optional[pd.DataFrame] = None
    benchmark_returns: Optional[pd.Series] = None

    # 显著性检验
    significance: Dict[str, Any] = field(default_factory=dict)

    # 原始运行数据
    _run_id: str = ''
    _run_time: str = ''

    def summary(self) -> str:
        """返回文本摘要"""
        lines = [
            f"{'='*60}",
            f"  回测结果: {self.strategy_name}",
            f"  区间: {self.start_date} ~ {self.end_date}",
            f"  数据版本: {self.data_version}",
            f"{'='*60}",
            f"  总收益率:      {self.total_return:>8.2%}",
            f"  年化收益率:    {self.annual_return:>8.2%}",
            f"  夏普比率:      {self.sharpe:>8.2f}",
            f"  最大回撤:      {self.max_drawdown:>8.2%}",
            f"  胜率:          {self.win_rate:>8.2%}",
            f"  盈亏比:        {self.profit_loss_ratio:>8.2f}",
            f"  总交易次数:    {self.total_trades:>8d}",
            f"  Alpha:         {self.alpha:>8.2%}",
            f"  Beta:          {self.beta:>8.2f}",
        ]

        # 显著性检验
        if self.significance:
            sig = self.significance
            lines.extend([
                f"{'-'*60}",
                f"  显著性检验:",
                f"  夏普t检验 p值: {sig.get('sharpe_p_value', 0):.4f}",
                f"  统计显著:      {'是' if sig.get('sharpe_significant') else '否'}",
                f"  胜率二项 p值:  {sig.get('win_rate_p_value', 0):.4f}",
            ])
            if sig.get('is_luck'):
                lines.append(f"  [WARN] 结果可能是运气")

        lines.append(f"{'='*60}")
        return '\n'.join(lines)

    def save_report(self, path: str):
        """保存HTML报告

        Args:
            path: 保存路径
        """
        # 生成简化的HTML报告
        html = self._generate_html()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    def export_trades(self, path: str):
        """导出交易记录CSV

        Args:
            path: 保存路径
        """
        if not self.trades:
            return
        df = pd.DataFrame(self.trades)
        df.to_csv(path, index=False, encoding='utf-8-sig')

    def to_json(self, path: str = '') -> str:
        """导出为JSON字符串或文件

        Args:
            path: 保存路径，为空则返回JSON字符串

        Returns:
            JSON字符串
        """
        data = {
            'strategy_name': self.strategy_name,
            'params': self.params,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'data_version': self.data_version,
            'config_version': self.config_version,
            'metrics': {
                'total_return': round(self.total_return, 4),
                'annual_return': round(self.annual_return, 4),
                'sharpe': round(self.sharpe, 4),
                'sortino': round(self.sortino, 4),
                'calmar': round(self.calmar, 4),
                'max_drawdown': round(self.max_drawdown, 4),
                'win_rate': round(self.win_rate, 4),
                'profit_loss_ratio': round(self.profit_loss_ratio, 4),
                'total_trades': self.total_trades,
                'avg_hold_days': round(self.avg_hold_days, 2),
                'alpha': round(self.alpha, 4),
                'beta': round(self.beta, 4),
                'information_ratio': round(self.information_ratio, 4),
            },
            'significance': {
                k: v for k, v in self.significance.items()
                if not k.startswith('_') and isinstance(v, (str, int, float, bool))
            } if self.significance else {},
            'n_trades': len(self.trades),
        }
        import json
        result = json.dumps(data, ensure_ascii=False, indent=2)
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(result)
        return result

    def to_dict(self) -> dict:
        """导出为字典（方便对比多个回测结果）"""
        import json
        return json.loads(self.to_json())

    def _generate_html(self) -> str:
        """生成HTML报告"""
        lines = [
            '<!DOCTYPE html>',
            '<html><head><meta charset="utf-8"><title>回测报告</title>',
            '<style>body{font-family: sans-serif; margin: 20px;}',
            'table{border-collapse: collapse; width: 100%;}',
            'td,th{border: 1px solid #ddd; padding: 8px; text-align: left;}',
            'th{background-color: #f2f2f2;}</style></head><body>',
            f'<h1>回测报告: {self.strategy_name}</h1>',
            f'<p>区间: {self.start_date} ~ {self.end_date}</p>',
            '<h2>绩效指标</h2>',
            '<table>',
        ]
        metrics = [
            ('总收益率', f'{self.total_return:.2%}'),
            ('年化收益率', f'{self.annual_return:.2%}'),
            ('夏普比率', f'{self.sharpe:.2f}'),
            ('最大回撤', f'{self.max_drawdown:.2%}'),
            ('胜率', f'{self.win_rate:.2%}'),
            ('盈亏比', f'{self.profit_loss_ratio:.2f}'),
            ('总交易次数', str(self.total_trades)),
        ]
        for name, value in metrics:
            lines.append(f'<tr><td>{name}</td><td>{value}</td></tr>')

        if self.significance:
            lines.append('</table><h2>显著性检验</h2><table>')
            sig = self.significance
            lines.append(f'<tr><td>夏普t检验p值</td><td>{sig.get("sharpe_p_value", 0):.4f}</td></tr>')
            lines.append(f'<tr><td>统计显著</td><td>{"是" if sig.get("sharpe_significant") else "否"}</td></tr>')
            if sig.get('is_luck'):
                lines.append('<tr><td>⚠️ 警告</td><td>结果可能是运气</td></tr>')

        lines.append('</table></body></html>')
        return '\n'.join(lines)