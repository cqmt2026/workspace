#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
风险控制模块 V2.0
功能：自动止损、仓位管理、风险预警
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json

# ========== 风险配置 ==========
RISK_CONFIG = {
    'total_capital': 15000,       # 总资金
    'single_position': 0.20,      # 单笔仓位 20%
    'max_positions': 3,           # 最大持仓数
    'stop_loss': -0.03,           # 止损线 -3%
    'take_profit_1': 0.03,        # 止盈 1 +3%
    'take_profit_2': 0.05,        # 止盈 2 +5%
    'take_profit_3': 0.08,        # 止盈 3 +8%
    'daily_loss_limit': -0.05,    # 单日亏损限制 -5%
    'weekly_loss_limit': -0.10,   # 周亏损限制 -10%
    'portfolio_drawdown_limit': -0.10,   # 组合最大回撤限制 -10%
    'portfolio_drawdown_critical': -0.15, # 组合回撤临界 -15%（强制清仓）
    'consecutive_loss_limit': 3,   # 连续亏损次数限制
    'consecutive_loss_cooldown': 1, # 连亏后暂停天数
    'monthly_loss_limit': -0.15,  # 月亏损限制 -15%
    'correlation_warning': 0.7,   # 持仓平均相关系数预警
    'sector_exposure_limit': 0.4, # 同行业持仓占比上限
    'kelly_fraction': 0.5,        # 凯利公式保守系数（半凯利）
}

# 风险等级
RISK_LEVELS = {
    'low': {'name': '低风险', 'color': '[GREEN]'},
    'medium': {'name': '中风险', 'color': '[YELLOW]'},
    'high': {'name': '高风险', 'color': '[ORANGE]'},
    'extreme': {'name': '极高风险', 'color': '[RED]'},
}


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config=None):
        self.config = config or RISK_CONFIG
        self.positions = []
        self.history = []
        self.daily_pnl = 0
        self.weekly_pnl = 0
        self.monthly_pnl = 0
        self.peak_value = 0
        self.current_value = 0
        self.consecutive_losses = 0
        self.max_drawdown = 0
        self.original_capital = self.config['total_capital']
        self.trade_results = []  # 最近20笔交易结果（用于EV计算）
    
    def add_position(self, stock):
        """
        添加持仓
        
        Args:
            stock: 股票信息（dict）
        
        Returns:
            bool: 是否成功添加
        """
        # 检查最大持仓数
        if len(self.positions) >= self.config['max_positions']:
            print(f"已达最大持仓数：{self.config['max_positions']}")
            return False
        
        # 检查可用资金
        used_capital = sum(p.get('value', 0) for p in self.positions)
        available = self.config['total_capital'] * self.config['single_position']
        
        if used_capital + stock.get('value', 0) > available * self.config['max_positions']:
            print("可用资金不足")
            return False
        
        # 添加持仓
        position = {
            'code': stock['code'],
            'name': stock.get('name', ''),
            'price': stock['price'],
            'shares': stock.get('shares', 0),
            'value': stock.get('value', 0),
            'stop_loss': stock.get('stop_loss', stock['price'] * 0.97),
            'take_profit': stock.get('take_profit', stock['price'] * 1.08),
            'push_time': stock.get('push_time', ''),
            'status': 'holding',
        }
        
        self.positions.append(position)
        print(f"添加持仓：{stock['code']} {stock.get('name', '')}")
        return True
    
    def check_stop_loss(self, current_prices, open_prices=None):
        """
        检查止损（含开盘跳空处理）
        
        P2-1 2026-07-02新增：开盘跌幅 > 3% 直接止损
        数学原理：亏得越深，回本越难。跳空低开等反弹可能亏更多
        
        Args:
            current_prices: 当前价格 dict {code: price}
            open_prices: 开盘价 dict {code: open_price}（可选）
        
        Returns:
            list: 需要止损的股票列表
        """
        stop_loss_list = []
        
        for pos in self.positions:
            code = pos['code']
            if code not in current_prices:
                continue
            
            current_price = current_prices[code]
            buy_price = pos['price']
            stop_loss_price = pos['stop_loss']
            
            # 常规止损检查
            if current_price <= stop_loss_price:
                stop_loss_list.append({
                    'code': code,
                    'name': pos['name'],
                    'current_price': current_price,
                    'stop_loss_price': stop_loss_price,
                    'loss_pct': (current_price - buy_price) / buy_price * 100,
                    'reason': '常规止损',
                    'action': '市价单卖出'
                })
                continue
            
            # 开盘跳空检查（P2-1 2026-07-02新增）
            # 策略论据提到"-5%止损有时失效，因为开盘跳空低开"
            if open_prices and code in open_prices:
                open_price = open_prices[code]
                gap_pct = (open_price - buy_price) / buy_price * 100
                
                # 开盘跌幅 > 3%，集合竞价直接挂单卖出
                if gap_pct <= -3:
                    stop_loss_list.append({
                        'code': code,
                        'name': pos['name'],
                        'current_price': open_price,
                        'stop_loss_price': stop_loss_price,
                        'loss_pct': gap_pct,
                        'reason': f'开盘跳空{gap_pct:.1f}%',
                        'action': '集合竞价直接卖出，不等盘中反弹'
                    })
        
        return stop_loss_list
    
    def check_take_profit(self, current_prices):
        """
        检查止盈
        
        Args:
            current_prices: 当前价格 dict {code: price}
        
        Returns:
            dict: 止盈信号 {code: level}
        """
        take_profit_signals = {}
        
        for pos in self.positions:
            code = pos['code']
            if code not in current_prices:
                continue
            
            current_price = current_prices[code]
            buy_price = pos['price']
            profit_pct = (current_price - buy_price) / buy_price
            
            # 判断止盈级别
            if profit_pct >= self.config['take_profit_3']:
                take_profit_signals[code] = 'tp3'
            elif profit_pct >= self.config['take_profit_2']:
                take_profit_signals[code] = 'tp2'
            elif profit_pct >= self.config['take_profit_1']:
                take_profit_signals[code] = 'tp1'
        
        return take_profit_signals
    
    def calculate_daily_pnl(self, current_prices):
        """
        计算当日盈亏，同时更新组合峰值和回撤
        
        Args:
            current_prices: 当前价格 dict {code: price}
        
        Returns:
            float: 当日盈亏比例
        """
        total_value = 0
        total_cost = 0
        
        for pos in self.positions:
            code = pos['code']
            if code not in current_prices:
                continue
            
            current_price = current_prices[code]
            total_value += current_price * pos['shares']
            total_cost += pos['price'] * pos['shares']
        
        if total_cost == 0:
            return 0
        
        self.daily_pnl = (total_value - total_cost) / total_cost
        self.current_value = total_value
        
        # 更新组合峰值
        if self.current_value > self.peak_value:
            self.peak_value = self.current_value
        
        # 计算当前回撤
        if self.peak_value > 0:
            current_drawdown = (self.current_value - self.peak_value) / self.peak_value
            self.max_drawdown = min(self.max_drawdown, current_drawdown)
        
        return self.daily_pnl
    
    def check_portfolio_drawdown(self):
        """
        检查组合最大回撤
        
        Returns:
            dict: 回撤状态 {'level': str, 'drawdown': float, 'action': str}
        """
        if self.peak_value <= 0:
            return {'level': 'normal', 'drawdown': 0, 'action': '无操作'}
        
        current_drawdown = self.max_drawdown
        
        if current_drawdown <= self.config['portfolio_drawdown_critical']:
            return {
                'level': 'critical',
                'drawdown': current_drawdown,
                'action': '强制清仓，休息3天'
            }
        elif current_drawdown <= self.config['portfolio_drawdown_limit']:
            return {
                'level': 'warning',
                'drawdown': current_drawdown,
                'action': '强制减仓至50%，暂停开新仓'
            }
        elif current_drawdown <= self.config['portfolio_drawdown_limit'] * 0.7:
            return {
                'level': 'alert',
                'drawdown': current_drawdown,
                'action': '预警，评估持仓'
            }
        
        return {'level': 'normal', 'drawdown': current_drawdown, 'action': '正常'}

    def check_consecutive_losses(self):
        """
        检查连续亏损，触发熔断
        
        Returns:
            dict: 熔断状态 {'triggered': bool, 'count': int, 'action': str}
        """
        if self.consecutive_losses >= 5:
            return {
                'triggered': True,
                'count': self.consecutive_losses,
                'action': f'连续{self.consecutive_losses}笔亏损，暂停交易3天，全面检查策略'
            }
        elif self.consecutive_losses >= self.config['consecutive_loss_limit']:
            return {
                'triggered': True,
                'count': self.consecutive_losses,
                'action': f'连续{self.consecutive_losses}笔亏损，暂停交易1天，复盘'
            }
        
        return {'triggered': False, 'count': self.consecutive_losses, 'action': '正常'}

    def calculate_kelly_position(self, win_rate, avg_win, avg_loss):
        """
        凯利公式计算最优仓位
        
        Args:
            win_rate: 胜率 (0-1)
            avg_win: 平均盈利率 (正数)
            avg_loss: 平均亏损率 (正数)
        
        Returns:
            float: 建议仓位比例
        """
        if avg_loss <= 0:
            return self.config['single_position']
        
        # 盈亏比
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1
        
        # 凯利公式：f* = (p*b - q) / b = p - q/b
        # p=胜率, q=1-p, b=盈亏比
        b = win_loss_ratio
        p = win_rate
        q = 1 - p
        
        kelly_f = (p * b - q) / b if b > 0 else 0
        
        # 使用半凯利（更保守）
        safe_f = max(0, kelly_f * self.config['kelly_fraction'])
        
        # 不超过配置的单笔上限
        return min(safe_f, self.config['single_position'])

    def check_risk_level(self):
        """
        检查风险等级（增强版）
        
        Returns:
            str: 风险等级
        """
        # 检查组合回撤
        drawdown_status = self.check_portfolio_drawdown()
        if drawdown_status['level'] == 'critical':
            return 'extreme'
        
        # 检查连续亏损
        consecutive_status = self.check_consecutive_losses()
        if consecutive_status['count'] >= 5:
            return 'extreme'
        
        # 检查单日亏损
        if self.daily_pnl <= self.config['daily_loss_limit']:
            return 'extreme'
        
        # 检查周亏损
        if self.weekly_pnl <= self.config['weekly_loss_limit']:
            return 'extreme'
        
        # 检查月亏损
        if self.monthly_pnl <= self.config['monthly_loss_limit']:
            return 'extreme'
        
        # 检查连续亏损预警
        if consecutive_status['triggered']:
            return 'high'
        
        # 检查组合回撤预警
        if drawdown_status['level'] == 'warning':
            return 'high'
        
        # 检查持仓集中度
        if len(self.positions) >= self.config['max_positions']:
            return 'high'
        
        # 检查盈亏情况
        if self.daily_pnl < -0.02:
            return 'medium'
        elif self.daily_pnl > 0.05:
            return 'low'
        
        return 'medium'
    
    def get_risk_warning(self):
        """
        获取风险预警（增强版）
        
        Returns:
            list: 预警信息列表
        """
        warnings = []
        risk_level = self.check_risk_level()
        
        # 风险等级预警
        if risk_level == 'extreme':
            warnings.append({
                'level': '🔴 极高',
                'message': '触及止损线，建议立即减仓！',
                'action': '立即减仓至 1 只或空仓'
            })
        elif risk_level == 'high':
            warnings.append({
                'level': '🟠 高',
                'message': '风险较高，谨慎开新仓！',
                'action': '暂停开新仓，等待风险释放'
            })
        
        # 组合回撤预警
        drawdown_status = self.check_portfolio_drawdown()
        if drawdown_status['level'] == 'critical':
            warnings.append({
                'level': '🔴 极高',
                'message': f'组合回撤 {drawdown_status["drawdown"]*100:.1f}%，触及强制清仓线！',
                'action': drawdown_status['action']
            })
        elif drawdown_status['level'] == 'warning':
            warnings.append({
                'level': '🟠 高',
                'message': f'组合回撤 {drawdown_status["drawdown"]*100:.1f}%，触及预警线',
                'action': drawdown_status['action']
            })
        elif drawdown_status['level'] == 'alert':
            warnings.append({
                'level': '🟡 中',
                'message': f'组合回撤 {drawdown_status["drawdown"]*100:.1f}%，接近预警',
                'action': drawdown_status['action']
            })
        
        # 连续亏损预警
        consecutive_status = self.check_consecutive_losses()
        if consecutive_status['triggered']:
            warnings.append({
                'level': '🔴 极高' if consecutive_status['count'] >= 5 else '🟠 高',
                'message': f'连续 {consecutive_status["count"]} 笔亏损！',
                'action': consecutive_status['action']
            })
        
        # 单日亏损预警
        if self.daily_pnl <= -0.03:
            warnings.append({
                'level': '🟡 中',
                'message': f'单日亏损 {self.daily_pnl*100:.1f}%，注意风险！',
                'action': '考虑止损部分持仓'
            })
        
        # 持仓集中度预警
        if len(self.positions) >= self.config['max_positions']:
            warnings.append({
                'level': '🟡 中',
                'message': f'已达最大持仓数 {self.config["max_positions"]}只',
                'action': '暂停开新仓'
            })
        
        return warnings
    
    def print_report(self):
        """打印风险报告"""
        print("\n" + "="*80)
        print("风险控制报告")
        print("="*80)
        print(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # 基本配置
        print(f"\n风险配置:")
        print(f"  总资金：{self.config['total_capital']}元")
        print(f"  单笔仓位：{self.config['single_position']*100:.0f}%")
        print(f"  最大持仓：{self.config['max_positions']}只")
        print(f"  止损线：{self.config['stop_loss']*100:.0f}%")
        print(f"  组合回撤预警：{self.config['portfolio_drawdown_limit']*100:.0f}% / 强制清仓：{self.config['portfolio_drawdown_critical']*100:.0f}%")
        print(f"  连续亏损熔断：{self.config['consecutive_loss_limit']}笔 / 深度熔断：5笔")
        print(f"  月亏损限制：{self.config['monthly_loss_limit']*100:.0f}%")
        print(f"  凯利系数：{self.config['kelly_fraction']*100:.0f}%")
        print(f"  止盈线：+{self.config['take_profit_1']*100:.0f}% / +{self.config['take_profit_2']*100:.0f}% / +{self.config['take_profit_3']*100:.0f}%")
        
        # 当前持仓
        print(f"\n当前持仓 ({len(self.positions)}只):")
        for pos in self.positions:
            print(f"  {pos['code']} {pos['name']}")
            print(f"    价格：{pos['price']}元  数量：{pos['shares']}股  价值：{pos['value']}元")
            print(f"    止损：{pos['stop_loss']}元  止盈：{pos['take_profit']}元")
        
        # 风险等级
        risk_level = self.check_risk_level()
        risk_info = RISK_LEVELS.get(risk_level, {})
        print(f"\n风险等级：{risk_info.get('color', '')} {risk_info.get('name', risk_level)}")
        
        # 盈亏情况
        print(f"\n盈亏情况:")
        print(f"  当日盈亏：{self.daily_pnl*100:+.2f}%")
        print(f"  本周盈亏：{self.weekly_pnl*100:+.2f}%")
        print(f"  本月盈亏：{self.monthly_pnl*100:+.2f}%")
        
        # 组合回撤状态
        drawdown_status = self.check_portfolio_drawdown()
        print(f"\n组合回撤:")
        print(f"  当前回撤：{drawdown_status['drawdown']*100:.2f}%")
        print(f"  状态：{drawdown_status['level']}")
        if drawdown_status['level'] != 'normal':
            print(f"  建议：{drawdown_status['action']}")
        
        # 连续亏损状态
        consecutive_status = self.check_consecutive_losses()
        print(f"\n连续亏损:")
        print(f"  当前连续：{consecutive_status['count']}笔")
        if consecutive_status['triggered']:
            print(f"  ⚠️ 已触发熔断！{consecutive_status['action']}")
        else:
            print(f"  状态：正常")
        
        # 风险预警
        warnings = self.get_risk_warning()
        if warnings:
            print(f"\n风险预警:")
            for w in warnings:
                print(f"  {w['level']} {w['message']}")
                print(f"     建议：{w['action']}")
        else:
            print(f"\n风险预警：无")
        
        print("="*80)


def main():
    """主函数"""
    print("="*80)
    print("风险控制模块 V2.0")
    print("="*80)
    
    # 创建风险管理器
    risk_mgr = RiskManager()
    
    # 测试添加持仓
    test_stocks = [
        {'code': '600032', 'name': '浙江新能', 'price': 11.41, 'shares': 200, 'value': 2282},
        {'code': '600026', 'name': '中远海能', 'price': 25.57, 'shares': 100, 'value': 2557},
    ]
    
    for stock in test_stocks:
        risk_mgr.add_position(stock)
    
    # 打印报告
    risk_mgr.print_report()


if __name__ == '__main__':
    main()
