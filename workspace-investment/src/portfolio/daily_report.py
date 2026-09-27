# -*- coding: utf-8 -*-
"""
日报模块 daily_report.py
每日收盘后生成持仓报告
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from portfolio.tracker import get_tracker


def generate_daily_report(price_map: Dict[str, float],
                          output_dir: str = None) -> str:
    """
    生成日报

    Args:
        price_map: {symbol: price} 收盘价字典
        output_dir: 输出目录（默认 data/reports/）

    Returns:
        报告文件路径
    """
    tracker = get_tracker()
    report_content = tracker.get_daily_snapshot(price_map)

    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "reports"
        )

    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"daily_report_{today}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return filepath


def get_latest_report(output_dir: str = None) -> Optional[str]:
    """获取最新日报路径"""
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "reports"
        )

    if not os.path.exists(output_dir):
        return None

    files = [f for f in os.listdir(output_dir) if f.startswith("daily_report_")]
    if not files:
        return None

    files.sort(reverse=True)
    return os.path.join(output_dir, files[0])


# 测试
if __name__ == "__main__":
    # 模拟收盘价
    price_map = {
        "000591.SZ": 6.62
    }

    print("=== 日报生成测试 ===\n")

    filepath = generate_daily_report(price_map)
    print(f"日报已生成: {filepath}\n")

    # 打印内容预览
    with open(filepath, 'r', encoding='utf-8') as f:
        print(f.read())
