#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史回测引擎 V2.0
功能：
  1. 基于历史K线的策略回测（真正的历史模拟）
  2. 基于历史推送文件的实盘回测（原有功能）
  3. 多维度绩效分析 + 报告生成
数据源：腾讯财经K线API
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import glob
import time

sys.path.insert(0, str(Path(__file__).parent))

from realtime_data import TencentDataAPI
from advanced_scorer import StockScorer
from stock_pool_200 import STOCK_POOL_200, CORE_STOCKS
from sector_tracker import STOCK_SECTOR_MAP, BASE_WEIGHTS
from market_filter import SectorBlacklist
from trading_config import TRADING_CONFIG

# ========== 配置 ==========
REPORT_DIR = Path(__file__).parent.parent / 'reports'
REPORT_DIR.mkdir(exist_ok=True)

BACKTEST_CONFIG = dict(TRADING_CONFIG)  # 从统一配置读取


class HistoricalBacktest:
    """
    历史K线回测引擎
    用历史数据模拟评分->选股->买入->持有->卖出的完整流程
    """

    def __init__(self, config=None):
        self.config = config or BACKTEST_CONFIG
        self.api = TencentDataAPI()
        self.scorer = StockScorer()
        self.trades = []          # 所有交易记录
        self.daily_equity = []    # 每日净值
        self.positions = {}       # 当前持仓 {code: {entry_price, entry_date, shares, cost}}

    def fetch_kline_pool(self, stock_codes, days=120):
        """
        批量拉取股票池历史K线

        Args:
            stock_codes: 股票代码列表
            days: K线天数(需要额外天数做指标计算)

        Returns:
            dict: {code: DataFrame}
        """
        print(f"\n拉取K线数据: {len(stock_codes)}只, {days}天...")
        klines = {}
        success = 0
        fail = 0

        for i, code in enumerate(stock_codes):
            try:
                df = self.api.get_kline_data(code, period='d', count=days)
                if df is not None and not df.empty and len(df) >= 30:
                    klines[code] = df
                    success += 1
                else:
                    fail += 1
            except Exception:
                fail += 1

            # 进度
            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(stock_codes)} (成功:{success} 失败:{fail})")
            time.sleep(0.05)  # 控频

        print(f"  K线获取完成: {success}只成功, {fail}只失败")
        return klines

    def score_on_date(self, klines, target_idx, dynamic_weights=None):
        """
        在指定日期对所有股票评分

        Args:
            klines: {code: DataFrame} 全量K线
            target_idx: 目标日期在K线中的索引位置
            dynamic_weights: 板块权重

        Returns:
            list: [(code, score, price, sector), ...] 按分数降序
        """
        results = []
        weights = dynamic_weights or BASE_WEIGHTS

        for code, df in klines.items():
            if target_idx >= len(df) or target_idx < 60:
                continue

            # 截取到target_idx为止的历史数据（模拟当天只能看到当天及之前的数据）
            hist = df.iloc[:target_idx + 1].copy()
            if len(hist) < 30:
                continue

            price = hist['close'].iloc[-1]
            if price < 5 or price > 200:
                continue

            sector = STOCK_SECTOR_MAP.get(code, '其他')

            # 构造 quote（模拟当日行情）
            prev_close = hist['close'].iloc[-2] if len(hist) >= 2 else price
            change_pct = (price - prev_close) / prev_close * 100

            quote = {
                'code': code,
                'name': '',
                'price': price,
                'change_pct': change_pct,
                'volume': hist['volume'].iloc[-1],
                'amount': 0,
            }

            try:
                score_result = self.scorer.calculate_score(
                    quote=quote,
                    kline=hist,
                    sector=sector,
                    dynamic_weights=weights,
                )
                score = score_result['total_score']
                if score >= self.config['morning_threshold']:
                    # 额外过滤：趋势+动量确认
                    # 1. MA5 > MA20（短期趋势向上）
                    closes = hist['close']
                    ma5 = closes.iloc[-5:].mean()
                    ma20 = closes.iloc[-20:].mean()
                    if ma5 < ma20:
                        continue  # 短期趋势向下，跳过
                    
                    # 2. 近2日不能连续下跌
                    if len(closes) >= 3:
                        if closes.iloc[-1] < closes.iloc[-2] < closes.iloc[-3]:
                            continue  # 连续3日下跌，跳过
                    
                    # 3. RSI不能超买(>75)
                    if score_result.get('rsi_score', 50) < 30:
                        continue  # RSI评分太低=超买
                    
                    results.append((code, score, price, sector))
            except Exception:
                continue

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def simulate_trading(self, klines, start_offset=60, end_offset=None):
        """
        模拟交易

        Args:
            klines: {code: DataFrame}
            start_offset: 从第几根K线开始交易（前面用于指标计算）
            end_offset: 结束位置（None=到最后）

        Returns:
            dict: 回测结果
        """
        if not klines:
            print("[ERROR] 无K线数据")
            return {}

        # 确定回测区间
        max_len = max(len(df) for df in klines.values())
        if end_offset is None:
            end_offset = max_len - 1

        capital = self.config['initial_capital']
        self.positions = {}
        self.trades = []
        self.daily_equity = []

        print(f"\n模拟交易: 第{start_offset}天 -> 第{end_offset}天 (共{end_offset - start_offset}个交易日)")
        print(f"初始资金: {capital:.0f}元")

        for day_idx in range(start_offset, end_offset + 1):
            # ---- 1. 检查持仓止损/止盈/到期 ----
            codes_to_sell = []
            for code, pos in self.positions.items():
                if code not in klines or day_idx >= len(klines[code]):
                    continue
                row = klines[code].iloc[day_idx]
                current_price = row['close']
                day_low = row['low'] if 'low' in row.index else current_price
                day_high = row['high'] if 'high' in row.index else current_price
                entry_price = pos['entry_price']
                
                # 用盘中最低价判断止损（更真实）
                pnl_low = (day_low - entry_price) / entry_price
                # 用盘中最高价判断止盈
                pnl_high = (day_high - entry_price) / entry_price
                # 收盘价用于计算实际盈亏
                pnl_close = (current_price - entry_price) / entry_price

                sell_reason = None
                sell_price_override = None
                
                if pnl_low <= self.config['stop_loss']:
                    sell_reason = '止损'
                    # 止损价格用止损线而非收盘价
                    sell_price_override = entry_price * (1 + self.config['stop_loss'])
                elif pnl_high >= self.config['take_profit_3']:
                    sell_reason = '止盈3(+8%)'
                    sell_price_override = entry_price * (1 + self.config['take_profit_3'])
                elif pnl_high >= self.config['take_profit_2']:
                    sell_reason = '止盈2(+5%)'
                    sell_price_override = entry_price * (1 + self.config['take_profit_2'])
                elif pnl_high >= self.config['take_profit_1']:
                    sell_reason = '止盈1(+3%)'
                    sell_price_override = entry_price * (1 + self.config['take_profit_1'])
                elif day_idx - pos['entry_idx'] >= self.config['hold_days']:
                    sell_reason = '到期'
                    sell_reason = '止损'
                elif pnl_pct >= self.config['take_profit_3']:
                    sell_reason = '止盈3(+8%)'
                elif pnl_pct >= self.config['take_profit_2']:
                    sell_reason = '止盈2(+5%)'
                elif pnl_pct >= self.config['take_profit_1']:
                    sell_reason = '止盈1(+3%)'
                elif day_idx - pos['entry_idx'] >= self.config['hold_days']:
                    sell_reason = '到期'

                if sell_reason:
                    actual_sell = sell_price_override if sell_price_override else current_price
                    actual_pnl = (actual_sell - entry_price) / entry_price
                    codes_to_sell.append((code, actual_sell, sell_reason, actual_pnl))

            # 执行卖出
            for code, sell_price, reason, pnl_pct in codes_to_sell:
                pos = self.positions.pop(code)
                sell_price_adj = sell_price * (1 - self.config['slippage'])
                proceeds = pos['shares'] * sell_price_adj
                commission = proceeds * self.config['commission']
                stamp = proceeds * self.config['stamp_tax']
                net = proceeds - commission - stamp
                capital += net

                profit = net - pos['cost']
                self.trades.append({
                    'code': code,
                    'sector': pos.get('sector', ''),
                    'entry_price': pos['entry_price'],
                    'entry_idx': pos['entry_idx'],
                    'exit_price': round(sell_price, 2),
                    'exit_idx': day_idx,
                    'shares': pos['shares'],
                    'cost': round(pos['cost'], 2),
                    'proceeds': round(net, 2),
                    'profit': round(profit, 2),
                    'profit_pct': round(pnl_pct * 100, 2),
                    'reason': reason,
                    'hold_days': day_idx - pos['entry_idx'],
                })

            # ---- 2. 选股+买入（信号产生在当天收盘，次日开盘买入） ----
            if len(self.positions) < self.config['max_positions']:
                candidates = self.score_on_date(klines, day_idx)
                # 取前5个候选，但实际在次日(day_idx+1)开盘买入
                for code, score, price, sector in candidates[:5]:
                    if code in self.positions:
                        continue
                    if len(self.positions) >= self.config['max_positions']:
                        break

                    # 次日开盘价买入（更真实）
                    next_idx = day_idx + 1
                    if code not in klines or next_idx >= len(klines[code]):
                        continue
                    next_row = klines[code].iloc[next_idx]
                    if 'open' in next_row.index and next_row['open'] > 0:
                        buy_price = next_row['open'] * (1 + self.config['slippage'])
                    else:
                        buy_price = price * (1 + self.config['slippage'])
                    
                    alloc = capital * self.config['single_position']
                    shares = int(alloc / buy_price / 100) * 100
                    if shares < 100:
                        continue
                    cost = shares * buy_price
                    commission = cost * self.config['commission']
                    total_cost = cost + commission

                    if total_cost > capital:
                        continue

                    capital -= total_cost
                    self.positions[code] = {
                        'entry_price': round(buy_price, 2),
                        'entry_idx': day_idx,
                        'shares': shares,
                        'cost': round(total_cost, 2),
                        'sector': sector,
                    }

            # ---- 3. 计算当日总权益 ----
            position_value = 0
            for code, pos in self.positions.items():
                if code in klines and day_idx < len(klines[code]):
                    current_price = klines[code]['close'].iloc[day_idx]
                    position_value += pos['shares'] * current_price

            equity = capital + position_value

            # 获取日期
            date_str = ''
            for df in klines.values():
                if day_idx < len(df) and 'date' in df.columns:
                    date_str = str(df['date'].iloc[day_idx])
                    break

            self.daily_equity.append({
                'idx': day_idx,
                'date': date_str,
                'capital': round(capital, 2),
                'position_value': round(position_value, 2),
                'equity': round(equity, 2),
                'positions': len(self.positions),
            })

        # 清仓剩余持仓
        for code, pos in list(self.positions.items()):
            if code in klines and end_offset < len(klines[code]):
                sell_price = klines[code]['close'].iloc[end_offset]
                pnl_pct = (sell_price - pos['entry_price']) / pos['entry_price']
                proceeds = pos['shares'] * sell_price
                commission = proceeds * self.config['commission']
                stamp = proceeds * self.config['stamp_tax']
                net = proceeds - commission - stamp
                profit = net - pos['cost']
                capital += net

                self.trades.append({
                    'code': code,
                    'sector': pos.get('sector', ''),
                    'entry_price': pos['entry_price'],
                    'entry_idx': pos['entry_idx'],
                    'exit_price': round(sell_price, 2),
                    'exit_idx': end_offset,
                    'shares': pos['shares'],
                    'cost': round(pos['cost'], 2),
                    'proceeds': round(net, 2),
                    'profit': round(profit, 2),
                    'profit_pct': round(pnl_pct * 100, 2),
                    'reason': '清仓',
                    'hold_days': end_offset - pos['entry_idx'],
                })

        self.positions = {}
        print(f"\n交易完成: {len(self.trades)}笔交易")

    def analyze(self):
        """分析回测结果"""
        if not self.trades:
            return {'error': '无交易记录'}

        profits = [t['profit_pct'] for t in self.trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]

        # 基本指标
        total_trades = len(self.trades)
        win_count = len(wins)
        win_rate = win_count / total_trades * 100 if total_trades > 0 else 0
        avg_profit = np.mean(profits) if profits else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0

        # 净值曲线
        equities = [e['equity'] for e in self.daily_equity]
        initial = self.config['initial_capital']
        final = equities[-1] if equities else initial
        total_return = (final - initial) / initial * 100

        # 最大回撤
        max_drawdown = 0
        peak = initial
        max_dd_start = max_dd_end = 0
        for i, eq in enumerate(equities):
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_drawdown:
                max_drawdown = dd
                max_dd_end = i

        # 年化收益
        trading_days = len(equities)
        annual_return = total_return / trading_days * 252 if trading_days > 0 else 0

        # 日收益率序列
        daily_returns = []
        for i in range(1, len(equities)):
            ret = (equities[i] - equities[i-1]) / equities[i-1]
            daily_returns.append(ret)

        # 夏普比率 (无风险利率2%年化)
        if daily_returns and np.std(daily_returns) > 0:
            rf_daily = 0.02 / 252
            sharpe = (np.mean(daily_returns) - rf_daily) / np.std(daily_returns) * np.sqrt(252)
        else:
            sharpe = 0

        # 按板块分析
        sector_stats = {}
        for t in self.trades:
            sector = t.get('sector', '其他')
            if sector not in sector_stats:
                sector_stats[sector] = {'count': 0, 'win': 0, 'profits': []}
            sector_stats[sector]['count'] += 1
            sector_stats[sector]['profits'].append(t['profit_pct'])
            if t['profit_pct'] > 0:
                sector_stats[sector]['win'] += 1

        sector_summary = {}
        for sector, s in sector_stats.items():
            sector_summary[sector] = {
                'count': s['count'],
                'win_rate': round(s['win'] / s['count'] * 100, 1) if s['count'] > 0 else 0,
                'avg_profit': round(np.mean(s['profits']), 2),
                'total_profit': round(sum(s['profits']), 2),
            }

        # 按卖出原因分析
        reason_stats = {}
        for t in self.trades:
            reason = t['reason']
            if reason not in reason_stats:
                reason_stats[reason] = {'count': 0, 'profits': []}
            reason_stats[reason]['count'] += 1
            reason_stats[reason]['profits'].append(t['profit_pct'])

        reason_summary = {}
        for reason, s in reason_stats.items():
            reason_summary[reason] = {
                'count': s['count'],
                'avg_profit': round(np.mean(s['profits']), 2),
            }

        # 日期范围
        dates = [e['date'] for e in self.daily_equity if e['date']]
        date_start = dates[0] if dates else ''
        date_end = dates[-1] if dates else ''

        return {
            'date_range': f'{date_start} ~ {date_end}',
            'trading_days': trading_days,
            'total_trades': total_trades,
            'win_count': win_count,
            'loss_count': total_trades - win_count,
            'win_rate': round(win_rate, 1),
            'avg_profit': round(avg_profit, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_profit': round(max_profit, 2),
            'max_loss': round(max_loss, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'INF',
            'initial_capital': initial,
            'final_capital': round(final, 2),
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'sector_summary': sector_summary,
            'reason_summary': reason_summary,
        }

    def generate_report(self, analysis):
        """生成Markdown回测报告"""
        if 'error' in analysis:
            return f"# 回测报告\n\n错误: {analysis['error']}"

        # 评级
        def grade(val, thresholds):
            for label, low, high in thresholds:
                if low <= val < high:
                    return label
            return thresholds[-1][0]

        ret_grade = grade(analysis['total_return'],
            [('D', -999, 0), ('C', 0, 5), ('B', 5, 15), ('A', 15, 30), ('S', 30, 999)])
        wr_grade = grade(analysis['win_rate'],
            [('D', 0, 40), ('C', 40, 50), ('B', 50, 60), ('A', 60, 70), ('S', 70, 100)])
        dd_grade = grade(analysis['max_drawdown'],
            [('S', 0, 5), ('A', 5, 10), ('B', 10, 15), ('C', 15, 20), ('D', 20, 999)])
        sp_grade = grade(analysis['sharpe_ratio'],
            [('D', -999, 0.5), ('C', 0.5, 1), ('B', 1, 1.5), ('A', 1.5, 2), ('S', 2, 999)])

        report = f"""# V14.0 历史回测报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**回测区间**: {analysis['date_range']}
**交易天数**: {analysis['trading_days']}天
**交易笔数**: {analysis['total_trades']}笔

---

## 核心指标

| 指标 | 数值 | 评级 |
|------|------|------|
| **总收益率** | {analysis['total_return']:.2f}% | {ret_grade} |
| **年化收益** | {analysis['annual_return']:.2f}% | {ret_grade} |
| **胜率** | {analysis['win_rate']:.1f}% | {wr_grade} |
| **最大回撤** | {analysis['max_drawdown']:.2f}% | {dd_grade} |
| **夏普比率** | {analysis['sharpe_ratio']:.2f} | {sp_grade} |
| **盈亏比** | {analysis['profit_factor']} | - |

## 资金变化

| 项目 | 数值 |
|------|------|
| 初始资金 | {analysis['initial_capital']:,.0f}元 |
| 最终资金 | {analysis['final_capital']:,.0f}元 |
| 盈亏 | {analysis['final_capital'] - analysis['initial_capital']:+,.0f}元 |

## 交易统计

| 项目 | 数值 |
|------|------|
| 总交易 | {analysis['total_trades']}笔 |
| 盈利 | {analysis['win_count']}笔 |
| 亏损 | {analysis['loss_count']}笔 |
| 平均收益 | {analysis['avg_profit']:.2f}% |
| 平均盈利 | {analysis['avg_win']:.2f}% |
| 平均亏损 | {analysis['avg_loss']:.2f}% |
| 最大单笔盈利 | {analysis['max_profit']:.2f}% |
| 最大单笔亏损 | {analysis['max_loss']:.2f}% |

## 板块分析

| 板块 | 交易数 | 胜率 | 平均收益 |
|------|--------|------|----------|
"""
        sorted_sectors = sorted(analysis['sector_summary'].items(),
                                key=lambda x: x[1]['avg_profit'], reverse=True)
        for sector, stats in sorted_sectors:
            report += f"| {sector} | {stats['count']} | {stats['win_rate']:.1f}% | {stats['avg_profit']:+.2f}% |\n"

        report += f"""
## 卖出原因

| 原因 | 次数 | 平均收益 |
|------|------|----------|
"""
        for reason, stats in sorted(analysis['reason_summary'].items(),
                                     key=lambda x: x[1]['count'], reverse=True):
            report += f"| {reason} | {stats['count']} | {stats['avg_profit']:+.2f}% |\n"

        report += f"""
---

## 综合评级: {ret_grade}{wr_grade}{dd_grade}{sp_grade}

**收益{ret_grade} | 胜率{wr_grade} | 回撤{dd_grade} | 夏普{sp_grade}**

---
*V14.0 历史回测引擎 V2.0*
"""
        return report

    def save_results(self, analysis, report):
        """保存回测结果"""
        ts = datetime.now().strftime('%Y%m%d_%H%M')

        # Markdown报告
        md_file = REPORT_DIR / f'backtest_history_{ts}.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(report)

        # JSON结果
        json_file = REPORT_DIR / f'backtest_history_{ts}.json'
        result = {
            'time': datetime.now().isoformat(),
            'config': self.config,
            'analysis': analysis,
            'trades': self.trades[-50:],  # 最近50笔
            'equity_sample': self.daily_equity[-30:],  # 最近30天净值
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  报告: {md_file.name}")
        print(f"  JSON: {json_file.name}")
        return md_file, json_file

    def run(self, stock_codes=None, days=90, pool_size=50):
        """
        运行历史回测

        Args:
            stock_codes: 股票列表（默认用核心股+随机抽样）
            days: 回测K线天数
            pool_size: 回测股票数量

        Returns:
            dict: 回测分析结果
        """
        print("=" * 60)
        print(f"V14.0 历史回测引擎 V2.0")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 选择回测股票
        if stock_codes is None:
            # 用核心股 + 从完整池子里抽样
            pool = list(CORE_STOCKS)
            if pool_size > len(pool):
                remaining = [c for c in STOCK_POOL_200 if c not in pool]
                np.random.seed(42)
                need = min(pool_size - len(pool), len(remaining))
                if need > 0:
                    extra = list(np.random.choice(remaining, need, replace=False))
                    pool.extend(extra)
            stock_codes = pool[:pool_size]

        print(f"回测股票: {len(stock_codes)}只")
        print(f"K线天数: {days}天")
        print(f"配置: 资金{self.config['initial_capital']}, 仓位{self.config['single_position']*100:.0f}%, "
              f"最多{self.config['max_positions']}仓, 止损{self.config['stop_loss']*100:.0f}%")

        # 1. 拉取K线
        klines = self.fetch_kline_pool(stock_codes, days=days)
        if not klines:
            print("[ERROR] 无法获取K线数据")
            return {'error': '无K线数据'}

        # 2. 模拟交易 (前60天用于指标计算，后面是真正回测区间)
        self.simulate_trading(klines, start_offset=60)

        # 3. 分析
        analysis = self.analyze()
        if 'error' in analysis:
            print(f"[ERROR] {analysis['error']}")
            return analysis

        # 4. 打印摘要
        print(f"\n{'='*60}")
        print("回测结果摘要")
        print(f"{'='*60}")
        print(f"  回测区间: {analysis['date_range']}")
        print(f"  交易天数: {analysis['trading_days']}天")
        print(f"  交易笔数: {analysis['total_trades']}笔")
        print(f"  总收益率: {analysis['total_return']:+.2f}%")
        print(f"  年化收益: {analysis['annual_return']:+.2f}%")
        print(f"  胜率:     {analysis['win_rate']:.1f}%")
        print(f"  最大回撤: {analysis['max_drawdown']:.2f}%")
        print(f"  夏普比率: {analysis['sharpe_ratio']:.2f}")
        print(f"  盈亏比:   {analysis['profit_factor']}")
        print(f"  资金变化: {analysis['initial_capital']:,.0f} -> {analysis['final_capital']:,.0f}")

        # 5. 生成报告
        report = self.generate_report(analysis)
        self.save_results(analysis, report)

        return analysis


# ======== 兼容旧接口: 基于推送文件的回测 ========

class SignalBacktest:
    """基于历史推送文件的回测（保留原有功能）"""

    def __init__(self):
        self.data_dir = Path(__file__).parent / 'track_result_v2'
        self.signal_dir = Path(__file__).parent

    def load_historical_signals(self, days=30):
        signals = []
        today = datetime.now()
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')
            pattern = f'signal_*_{date_str}_*.json'
            files = glob.glob(str(self.signal_dir / pattern))
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for signal in data.get('signals', []):
                        signal['push_date'] = date_str
                        signal['push_mode'] = data.get('mode', 'unknown')
                        signals.append(signal)
                except Exception:
                    pass
        return signals

    def load_historical_tracks(self, days=30):
        tracks = []
        today = datetime.now()
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')
            track_file = self.data_dir / f'track_report_{date_str}.json'
            if track_file.exists():
                try:
                    with open(track_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['track_date'] = date_str
                    tracks.append(data)
                except Exception:
                    pass
        return tracks

    def run_backtest(self, days=30):
        signals = self.load_historical_signals(days)
        tracks = self.load_historical_tracks(days)
        print(f"推送文件回测: {len(signals)}条信号, {len(tracks)}天数据")
        return {'signals': len(signals), 'tracks': len(tracks)}


# ======== 统一入口 ========

class BacktestEngine:
    """统一回测入口（兼容V14主系统调用）"""

    def __init__(self):
        self.historical = HistoricalBacktest()
        self.signal = SignalBacktest()

    def run_backtest(self, mode='history', days=90, pool_size=50, stock_codes=None):
        """
        运行回测

        Args:
            mode: 'history'=历史K线回测, 'signal'=推送文件回测
            days: 回测天数
            pool_size: 回测股票数
            stock_codes: 指定股票列表
        """
        if mode == 'history':
            return self.historical.run(stock_codes=stock_codes, days=days, pool_size=pool_size)
        else:
            return self.signal.run_backtest(days=days)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='V14.0 历史回测引擎')
    parser.add_argument('--mode', default='history', choices=['history', 'signal'],
                        help='回测模式: history=K线回测, signal=推送文件回测')
    parser.add_argument('--days', type=int, default=90, help='K线天数(默认90)')
    parser.add_argument('--pool', type=int, default=50, help='回测股票数(默认50)')
    args = parser.parse_args()

    engine = BacktestEngine()
    engine.run_backtest(mode=args.mode, days=args.days, pool_size=args.pool)


if __name__ == '__main__':
    main()
