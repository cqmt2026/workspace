# -*- coding: utf-8 -*-
"""
周报模块 weekly_report.py
每周生成持仓总结报告
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from portfolio.tracker import get_tracker
from portfolio.transactions import get_manager as get_tx_manager


def generate_weekly_report(price_map: Dict[str, float],
                          output_dir: str = None) -> str:
    """
    生成周报

    Args:
        price_map: {symbol: price} 周末收盘价字典
        output_dir: 输出目录

    Returns:
        报告文件路径
    """
    tracker = get_tracker()
    tx_manager = get_tx_manager()

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    report = tracker.get_realtime_value(price_map)

    # 获取本周交易
    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = week_end.strftime("%Y-%m-%d")
    week_tx = tx_manager.get_transactions(
        start_date=week_start_str,
        end_date=week_end_str
    )

    # 生成报告
    lines = []
    lines.append(f"# 组合周报 · {week_start_str} ~ {week_end_str}")
    lines.append("")
    lines.append(f"**生成时间**: {today.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 1. 本周概况
    lines.append("## 📊 本周概况")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 周初净值 | （待对接历史数据） |")
    lines.append(f"| 周末净值 | {report['nav']:.4f} |")
    lines.append(f"| 本周收益 | {report['total_profit']:+,.2f} 元 |")
    lines.append(f"| 持仓市值 | {report['total_value']:,.2f} 元 |")
    lines.append(f"| 持仓数量 | {report['position_count']} 只 |")
    lines.append("")

    # 2. 持仓明细
    lines.append("## 📋 持仓明细")
    lines.append("")
    if report["positions"]:
        lines.append("| 股票 | 持仓 | 成本 | 现价 | 盈亏 | 收益率 |")
        lines.append("|------|------|------|------|------|--------|")
        for p in report["positions"]:
            lines.append(f"| {p['name']} | {p['quantity']} | {p['cost']:.2f} | {p['current_price']:.2f} | {p['profit']:+,.2f} | {p['profit_rate']:+.2f}% |")
    else:
        lines.append("*零持仓，继续观察*")
    lines.append("")

    # 3. 本周交易
    lines.append("## 📝 本周交易")
    lines.append("")
    if week_tx:
        lines.append("| 日期 | 股票 | 方向 | 数量 | 价格 |")
        lines.append("|------|------|------|------|------|")
        for tx in week_tx:
            lines.append(f"| {tx['date']} | {tx['name']} | {tx['direction']} | {tx['quantity']} | {tx['price']:.2f} |")
    else:
        lines.append("*本周无交易*")
    lines.append("")

    # 4. 下周关注
    lines.append("## 🔭 下周关注")
    lines.append("")
    lines.append("- （待主人填写）")
    lines.append("")

    lines.append("---")
    lines.append(f"*由 可悦🌸 生成于 {today.strftime('%Y-%m-%d %H:%M')}*")

    report_content = "\n".join(lines)

    # 保存
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "reports"
        )

    os.makedirs(output_dir, exist_ok=True)
    filename = f"weekly_report_{today.strftime('%Y%m%d')}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return filepath


# 测试
if __name__ == "__main__":
    price_map = {}

    print("=== 周报生成测试 ===\n")

    filepath = generate_weekly_report(price_map)
    print(f"周报已生成: {filepath}\n")

    with open(filepath, 'r', encoding='utf-8') as f:
        print(f.read())
