# -*- coding: utf-8 -*-
"""
一键净值报告脚本 portfolio_report.py
自动获取行情 + 计算净值 + 生成报告 + 相关性检查
"""

import sys
import os
from datetime import datetime

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from .price_loader import get_price_map
from .tracker import get_tracker
from .daily_report import generate_daily_report
from .weekly_report import generate_weekly_report


def check_correlation(positions, price_map, lookback_days=60):
    """
    检查持仓股票之间的相关性
    
    数学原理：
    组合方差 = Σwᵢ²σᵢ² + 2ΣΣwᵢwⱼρᵢⱼσᵢσⱼ
    ρ=1（同涨同跌）→ 买再多也只像买一只
    ρ<1 → 才有分散保护
    
    Args:
        positions: 持仓列表
        price_map: 实时价格
        lookback_days: 回顾天数
    
    Returns:
        dict: 相关性分析结果
    """
    if len(positions) < 2:
        return {
            'avg_correlation': 0,
            'level': 'normal',
            'message': '持仓少于2只，无法计算相关性'
        }
    
    try:
        # 尝试从本地数据获取历史K线
        from data_fetchers.fetch_kline import fetch_kline_data
        
        symbols = [pos['symbol'] for pos in positions]
        prices_df = None
        
        for sym in symbols:
            try:
                df = fetch_kline_data(sym, count=lookback_days)
                if df is not None and not df.empty:
                    close_col = df['close'] if 'close' in df.columns else df.iloc[:, 1]
                    if prices_df is None:
                        prices_df = pd.DataFrame({sym: close_col})
                    else:
                        prices_df[sym] = close_col
            except:
                continue
        
        if prices_df is None or prices_df.shape[1] < 2:
            return {
                'avg_correlation': 0,
                'level': 'unknown',
                'message': '无法获取足够的历史数据计算相关性'
            }
        
        # 计算收益率相关性
        returns = prices_df.pct_change().dropna()
        corr_matrix = returns.corr()
        
        # 提取上三角相关系数（不含对角线）
        corr_values = []
        sector_groups = {}
        for i, sym1 in enumerate(corr_matrix.columns):
            for j, sym2 in enumerate(corr_matrix.columns):
                if j > i:  # 上三角
                    corr_values.append(corr_matrix.iloc[i, j])
        
        avg_corr = np.mean(corr_values) if corr_values else 0
        max_corr = max(corr_values) if corr_values else 0
        min_corr = min(corr_values) if corr_values else 0
        
        # 判定等级
        if avg_corr >= 0.8:
            level = 'danger'
            message = '持仓高度同质化，基本等于买了一只'
        elif avg_corr >= 0.6:
            level = 'warning'
            message = '持仓相关性偏高，分散效果有限'
        elif avg_corr >= 0.4:
            level = 'fair'
            message = '持仓有一定分散，但仍有同涨同跌风险'
        else:
            level = 'good'
            message = '持仓分散良好，低相关保护有效'
        
        return {
            'avg_correlation': round(avg_corr, 3),
            'max_correlation': round(max_corr, 3),
            'min_correlation': round(min_corr, 3),
            'pair_count': len(corr_values),
            'level': level,
            'message': message,
            'correlation_matrix': corr_matrix.round(3).to_dict() if corr_matrix.shape[0] <= 10 else None
        }
    except ImportError:
        return {
            'avg_correlation': 0,
            'level': 'unknown',
            'message': '缺少fetch_kline模块，无法计算相关性'
        }
    except Exception as e:
        return {
            'avg_correlation': 0,
            'level': 'error',
            'message': f'相关性计算异常: {str(e)}'
        }


def generate_portfolio_report() -> dict:
    """
    生成完整组合报告

    Returns:
        报告结果字典
    """
    print("=" * 50)
    print("组合净值报告生成")
    print("=" * 50)
    print()

    # 1. 获取持仓列表
    tracker = get_tracker()
    positions = tracker.position_manager.get_all_positions()
    print(f"持仓数量: {len(positions)} 只")

    if not positions:
        print("⚠️ 零持仓，跳过行情获取")
        return {"status": "empty", "message": "零持仓"}

    # 2. 获取实时行情
    symbols = [pos["symbol"] for pos in positions]
    print(f"获取行情: {symbols}")
    price_map = get_price_map(symbols)
    print(f"成功获取: {len(price_map)} 只")
    print()

    for sym, price in price_map.items():
        print(f"  {sym}: {price:.2f}")

    print()

    # 3. 计算净值
    print("计算净值...")
    report = tracker.get_realtime_value(price_map)
    print(f"  总资产: {report['total_assets']:,.2f}")
    print(f"  累计收益: {report['total_profit']:+,.2f} ({report['profit_rate']:+.2f}%)")
    print(f"  净值: {report['nav']:.4f}")
    print()

    # 4. 相关性检查（P1-2 2026-07-02新增）
    print("检查持仓相关性...")
    corr_result = check_correlation(positions, price_map)
    print(f"  平均相关系数: {corr_result['avg_correlation']:.3f}")
    print(f"  状态: {corr_result['level']}")
    if corr_result['level'] in ('danger', 'warning'):
        print(f"  ⚠️ {corr_result['message']}")
    else:
        print(f"  ✅ {corr_result['message']}")
    print()

    # 5. 生成日报
    print("生成日报...")
    daily_path = generate_daily_report(price_map)
    print(f"  {daily_path}")

    # 6. 生成周报
    print("生成周报...")
    weekly_path = generate_weekly_report(price_map)
    print(f"  {weekly_path}")

    print()
    print("=" * 50)
    print("✅ 报告生成完成")
    print("=" * 50)

    return {
        "status": "success",
        "report": report,
        "correlation": corr_result,
        "daily_report": daily_path,
        "weekly_report": weekly_path
    }


# 命令行入口
if __name__ == "__main__":
    result = generate_portfolio_report()
    if result["status"] == "success":
        print()
        print("报告摘要:")
        print(f"  总资产: {result['report']['total_assets']:,.2f}")
        print(f"  净值: {result['report']['nav']:.4f}")
