#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
风控小助手 V1.0
风险控制和止损止盈
"""

from datetime import datetime
from pathlib import Path
import json

class RiskControlAssistant:
    """风控小助手"""
    
    def __init__(self):
        self.risk_file = Path(__file__).parent.parent / 'data' / 'risk_settings.json'
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        if self.risk_file.exists():
            with open(self.risk_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
    
    def save_settings(self):
        """保存设置"""
        self.risk_file.parent.mkdir(exist_ok=True)
        with open(self.risk_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    def set_stop_loss(self, stock_code, stop_loss_pct=-5.0):
        """设置止损"""
        self.settings[stock_code] = {
            'stop_loss_pct': stop_loss_pct,
            'stop_profit_pct': self.settings.get(stock_code, {}).get('stop_profit_pct', 10.0),
            'updated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_settings()
        return True
    
    def set_stop_profit(self, stock_code, stop_profit_pct=10.0):
        """设置止盈"""
        if stock_code not in self.settings:
            self.settings[stock_code] = {'stop_loss_pct': -5.0}
        self.settings[stock_code]['stop_profit_pct'] = stop_profit_pct
        self.settings[stock_code]['updated_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_settings()
        return True
    
    def check_risk(self, stock_code, profit_pct):
        """检查风险"""
        if stock_code not in self.settings:
            return {'status': 'normal', 'message': '无风控设置'}
        
        setting = self.settings[stock_code]
        
        if profit_pct <= setting['stop_loss_pct']:
            return {
                'status': 'stop_loss',
                'message': f'触发止损（{profit_pct:.1f}% <= {setting["stop_loss_pct"]:.1f}%）',
                'action': 'sell'
            }
        elif profit_pct >= setting['stop_profit_pct']:
            return {
                'status': 'stop_profit',
                'message': f'触发止盈（{profit_pct:.1f}% >= {setting["stop_profit_pct"]:.1f}%）',
                'action': 'sell'
            }
        else:
            return {
                'status': 'normal',
                'message': f'正常（{profit_pct:.1f}%）',
                'action': 'hold'
            }
    
    def get_warnings(self):
        """获取风控预警"""
        warnings = []
        for stock_code, setting in self.settings.items():
            warnings.append({
                'code': stock_code,
                'stop_loss': setting['stop_loss_pct'],
                'stop_profit': setting['stop_profit_pct']
            })
        return warnings
    
    def set_position_limit(self, stock_code, max_position, max_percent):
        """设置仓位限制"""
        if stock_code not in self.settings:
            self.settings[stock_code] = {'stop_loss_pct': -5.0, 'stop_profit_pct': 10.0}
        
        self.settings[stock_code]['max_position'] = max_position
        self.settings[stock_code]['max_percent'] = max_percent
        self.settings[stock_code]['updated_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_settings()
        
        print(f"[OK] 已设置 {stock_code} 仓位限制：最大{max_position}股，最大{max_percent}%")
        return True
    
    def calculate_var(self, portfolio_returns, confidence=0.95):
        """计算 VaR（风险价值）"""
        import statistics
        
        if not portfolio_returns or len(portfolio_returns) < 10:
            return {'var': 0, 'confidence': confidence, 'note': '数据不足'}
        
        # 历史模拟法计算 VaR
        sorted_returns = sorted(portfolio_returns)
        var_index = int((1 - confidence) * len(sorted_returns))
        var = abs(sorted_returns[var_index]) if var_index < len(sorted_returns) else 0
        
        # 计算条件 VaR（CVaR）
        cvar = abs(sum(sorted_returns[:var_index+1]) / (var_index+1)) if var_index >= 0 else 0
        
        result = {
            'var_95': var * 100,
            'cvar_95': cvar * 100,
            'confidence': confidence,
            'samples': len(portfolio_returns),
            'interpretation': f'有{confidence*100:.0f}%的把握，单日最大损失不超过{var*100:.2f}%'
        }
        
        print(f"[VaR] {confidence*100:.0f}%置信度：{var*100:.2f}%")
        print(f"[CVaR] 条件 VaR: {cvar*100:.2f}%")
        
        return result
    
    def calculate_max_drawdown(self, portfolio_values):
        """计算最大回撤"""
        if not portfolio_values or len(portfolio_values) < 2:
            return {'max_drawdown': 0, 'note': '数据不足'}
        
        peak = portfolio_values[0]
        max_drawdown = 0
        max_drawdown_period = {'start': 0, 'end': 0}
        
        for i, value in enumerate(portfolio_values):
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_period['end'] = i
        
        result = {
            'max_drawdown': max_drawdown * 100,
            'max_drawdown_pct': f'{max_drawdown*100:.2f}%',
            'interpretation': f'历史最大回撤{max_drawdown*100:.2f}%'
        }
        
        print(f"[最大回撤] {max_drawdown*100:.2f}%")
        
        return result
    
    def calculate_portfolio_beta(self, portfolio_returns, market_returns):
        """计算组合 Beta"""
        import statistics
        
        if not portfolio_returns or not market_returns:
            return {'beta': 1.0, 'note': '数据不足'}
        
        # 确保数据长度一致
        min_len = min(len(portfolio_returns), len(market_returns))
        port_ret = portfolio_returns[:min_len]
        mkt_ret = market_returns[:min_len]
        
        # 计算协方差和方差
        mean_port = sum(port_ret) / len(port_ret)
        mean_mkt = sum(mkt_ret) / len(mkt_ret)
        
        covariance = sum((p - mean_port) * (m - mean_mkt) for p, m in zip(port_ret, mkt_ret)) / len(port_ret)
        variance_mkt = sum((m - mean_mkt) ** 2 for m in mkt_ret) / len(mkt_ret)
        
        beta = covariance / variance_mkt if variance_mkt > 0 else 1.0
        
        result = {
            'beta': beta,
            'interpretation': 'Beta>1: 波动大于市场; Beta<1: 波动小于市场'
        }
        
        print(f"[Beta] {beta:.2f}")
        if beta > 1.2:
            print(f"  [提示] 组合波动大于市场，风险较高")
        elif beta < 0.8:
            print(f"  [提示] 组合波动小于市场，风险较低")
        
        return result
    
    def calculate_sharpe_ratio(self, portfolio_returns, risk_free_rate=0.03):
        """计算夏普比率"""
        import statistics
        
        if not portfolio_returns or len(portfolio_returns) < 10:
            return {'sharpe': 0, 'note': '数据不足'}
        
        # 年化收益
        avg_return = sum(portfolio_returns) / len(portfolio_returns)
        annual_return = avg_return * 252
        
        # 年化波动率
        std_return = statistics.stdev(portfolio_returns)
        annual_std = std_return * (252 ** 0.5)
        
        # 夏普比率
        sharpe = (annual_return - risk_free_rate) / annual_std if annual_std > 0 else 0
        
        result = {
            'sharpe_ratio': sharpe,
            'annual_return': annual_return * 100,
            'annual_volatility': annual_std * 100,
            'interpretation': 'Sharpe>1: 良好; Sharpe>2: 优秀'
        }
        
        print(f"[夏普比率] {sharpe:.2f}")
        if sharpe > 2:
            print(f"  [优秀] 风险收益比优秀")
        elif sharpe > 1:
            print(f"  [良好] 风险收益比良好")
        elif sharpe > 0:
            print(f"  [一般] 风险收益比一般")
        else:
            print(f"  [警告] 风险收益比为负")
        
        return result
    
    def risk_warning(self, portfolio, threshold=0.8):
        """风险预警"""
        warnings = []
        
        # 检查仓位
        total_value = sum(p.get('market_value', 0) for p in portfolio)
        for p in portfolio:
            weight = p.get('market_value', 0) / total_value if total_value > 0 else 0
            if weight > threshold:
                warnings.append({
                    'type': 'concentration',
                    'code': p['code'],
                    'weight': weight * 100,
                    'message': f"{p['code']} 仓位过重 ({weight*100:.1f}%)"
                })
        
        # 检查亏损
        for p in portfolio:
            profit_pct = p.get('profit_pct', 0)
            if profit_pct < -10:
                warnings.append({
                    'type': 'loss',
                    'code': p['code'],
                    'loss': profit_pct,
                    'message': f"{p['code']} 亏损超过 10% ({profit_pct:.1f}%)"
                })
        
        if warnings:
            print(f"\n[风险预警] 发现{len(warnings)}个风险:")
            for w in warnings:
                print(f"  ⚠️ {w['message']}")
        else:
            print(f"\n[风险预警] 暂无风险")
        
        return warnings
    
    def correlation_warning(self, portfolio):
        """相关性预警（简化版）"""
        if len(portfolio) < 2:
            return {'warning': False}
        
        # 检查行业集中度
        sectors = {}
        for p in portfolio:
            sector = p.get('sector', 'unknown')
            sectors[sector] = sectors.get(sector, 0) + p.get('market_value', 0)
        
        total = sum(sectors.values())
        warnings = []
        
        for sector, value in sectors.items():
            weight = value / total if total > 0 else 0
            if weight > 0.5:
                warnings.append(f"行业集中度过高：{sector} 占比{weight*100:.1f}%")
        
        if warnings:
            print(f"\n[相关性预警]")
            for w in warnings:
                print(f"  ⚠️ {w}")
            return {'warning': True, 'warnings': warnings}
        else:
            print(f"\n[相关性预警] 行业分散良好")
            return {'warning': False}
    
    def liquidity_warning(self, portfolio):
        """流动性预警"""
        warnings = []
        
        for p in portfolio:
            volume = p.get('volume', 0)
            market_value = p.get('market_value', 0)
            
            # 简化的流动性检查
            if volume < 10000 and market_value > 50000:
                warnings.append({
                    'code': p['code'],
                    'volume': volume,
                    'message': f"{p['code']} 成交量过低，流动性风险"
                })
        
        if warnings:
            print(f"\n[流动性预警] 发现{len(warnings)}个流动性风险:")
            for w in warnings:
                print(f"  ⚠️ {w['code']}: {w['message']}")
        else:
            print(f"\n[流动性预警] 流动性良好")
        
        return warnings

def main():
    """主函数"""
    risk = RiskControlAssistant()
    
    print("=" * 60)
    print("风控小助手 V1.0")
    print("=" * 60)
    
    risk.set_stop_loss('300975', stop_loss_pct=-5.0)
    risk.set_stop_profit('300975', stop_profit_pct=10.0)
    
    print(f"\n风控设置:")
    warnings = risk.get_warnings()
    for warning in warnings:
        print(f"  {warning['code']}: 止损{warning['stop_loss']:.1f}%, 止盈{warning['stop_profit']:.1f}%")
    
    print(f"\n风险检查:")
    test_profits = [-6.0, -3.0, 5.0, 12.0]
    for profit in test_profits:
        result = risk.check_risk('300975', profit)
        print(f"  盈亏{profit:+.1f}%: {result['status']} - {result['message']}")

if __name__ == '__main__':
    main()
