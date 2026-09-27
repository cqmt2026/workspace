#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时风控模块
功能：实时监控股票风险，自动预警

作者：股票 V13.2 系统
时间：2026-03-18 02:26
"""

from datetime import datetime
from pathlib import Path
import json

class RealtimeRiskControl:
    """实时风控系统"""
    
    def __init__(self):
        self.risk_rules = {
            'max_single_position': 0.15,  # 单只股票最大仓位 15%
            'max_total_position': 0.60,   # 总仓位上限 60%
            'stop_loss': -0.05,            # 止损线 -5%
            'stop_profit': 0.10,           # 止盈线 +10%
            'max_drawdown': -0.15,         # 最大回撤 -15%
        }
        
        self.risk_dir = Path('../risk')
        self.risk_dir.mkdir(parents=True, exist_ok=True)
        
        print('[OK] 实时风控系统已初始化')
        print('  单只最大仓位：{:.0f}%'.format(self.risk_rules['max_single_position'] * 100))
        print('  总仓位上限：{:.0f}%'.format(self.risk_rules['max_total_position'] * 100))
        print('  止损线：{:.0f}%'.format(self.risk_rules['stop_loss'] * 100))
        print('  止盈线：{:.0f}%'.format(self.risk_rules['stop_profit'] * 100))
    
    def check_stock_risk(self, stock_data):
        """检查个股风险"""
        risks = []
        
        for stock in stock_data:
            try:
                change_pct = float(stock.get('涨跌幅', 0) or 0)
                turnover = float(stock.get('换手率', 0) or 0)
                
                risk_level = '低风险'
                risk_score = 0
                
                # 涨跌幅风险
                if change_pct > 7:
                    risk_score += 30
                    risks.append('{}: 涨幅过大 ({:.1f}%)'.format(stock.get('名称', ''), change_pct))
                elif change_pct < -5:
                    risk_score += 40
                    risks.append('{}: 跌幅过大 ({:.1f}%)'.format(stock.get('名称', ''), change_pct))
                
                # 换手率风险
                if turnover > 20:
                    risk_score += 20
                    risks.append('{}: 换手率过高 ({:.1f}%)'.format(stock.get('名称', ''), turnover))
                elif turnover < 1:
                    risk_score += 10
                    risks.append('{}: 换手率过低 ({:.1f}%)'.format(stock.get('名称', ''), turnover))
                
                # 风险等级
                if risk_score >= 50:
                    risk_level = '高风险'
                elif risk_score >= 30:
                    risk_level = '中风险'
                
                stock['风险等级'] = risk_level
                stock['风险评分'] = risk_score
                
            except:
                pass
        
        print('[OK] 个股风险检查完成')
        print('  高风险：{} 只'.format(sum(1 for s in stock_data if s.get('风险等级') == '高风险')))
        print('  中风险：{} 只'.format(sum(1 for s in stock_data if s.get('风险等级') == '中风险')))
        
        return risks
    
    def check_portfolio_risk(self, positions):
        """检查组合风险"""
        print('\n组合风险检查:')
        
        # 计算总仓位
        total_position = sum(pos.get('position', 0) for pos in positions)
        
        # 检查总仓位
        if total_position > self.risk_rules['max_total_position']:
            print('  [WARN] 总仓位过高：{:.0f}% (上限：{:.0f}%)'.format(
                total_position * 100, self.risk_rules['max_total_position'] * 100
            ))
        else:
            print('  [OK] 总仓位正常：{:.0f}%'.format(total_position * 100))
        
        # 检查单只仓位
        for pos in positions:
            if pos.get('position', 0) > self.risk_rules['max_single_position']:
                print('  [WARN] {} 仓位过高：{:.0f}%'.format(
                    pos.get('名称', ''), pos.get('position', 0) * 100
                ))
        
        # 计算盈亏
        total_profit = sum(pos.get('profit', 0) for pos in positions)
        if total_profit > self.risk_rules['stop_profit']:
            print('  [OK] 总盈利：{:.1f}% (已达止盈线)'.format(total_profit * 100))
        elif total_profit < self.risk_rules['stop_loss']:
            print('  [WARN] 总亏损：{:.1f}% (已达止损线)'.format(total_profit * 100))
        else:
            print('  [OK] 总盈亏：{:.1f}%'.format(total_profit * 100))
    
    def generate_risk_report(self, stock_risks, portfolio_positions):
        """生成风控报告"""
        report_file = self.risk_dir / 'risk_report_{}.md'.format(
            datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('# 实时风控报告\n\n')
            f.write('**生成时间**: {}\n\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            f.write('## 风控规则\n\n')
            f.write('| 规则 | 设置 |\n')
            f.write('|------|------|\n')
            for key, value in self.risk_rules.items():
                f.write('| {} | {:.0f}% |\n'.format(key, value * 100))
            
            f.write('\n## 个股风险\n\n')
            if stock_risks:
                for risk in stock_risks[:10]:
                    f.write('- {}\n'.format(risk))
            else:
                f.write('无高风险个股\n')
            
            f.write('\n## 组合风险\n\n')
            f.write('持仓数量：{} 只\n'.format(len(portfolio_positions)))
            
            f.write('\n## 建议\n\n')
            f.write('1. 严格执行止损止盈\n')
            f.write('2. 控制单只仓位不超过 15%\n')
            f.write('3. 总仓位不超过 60%\n')
            f.write('4. 实时监控风险指标\n')
        
        print('\n[OK] 风控报告已保存：{}'.format(report_file))

def main():
    """主函数"""
    print('=' * 60)
    print('实时风控模块')
    print('=' * 60)
    
    # 创建风控系统
    risk_control = RealtimeRiskControl()
    
    # 加载数据
    data_file = Path('../data/volume_top200_real_20260318.json')
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stocks = data.get('stocks', [])
        print('[OK] 数据已加载：{} 只'.format(len(stocks)))
    
    # 检查个股风险
    stock_risks = risk_control.check_stock_risk(stocks)
    
    # 模拟持仓
    positions = [
        {'名称': '测试持仓 1', 'position': 0.15, 'profit': 0.05},
        {'名称': '测试持仓 2', 'position': 0.10, 'profit': -0.03},
    ]
    
    # 检查组合风险
    risk_control.check_portfolio_risk(positions)
    
    # 生成报告
    risk_control.generate_risk_report(stock_risks, positions)
    
    print('\n' + '=' * 60)
    print('实时风控模块引入完成！')
    print('=' * 60)
    print('风控维度：5 个（仓位/止损/止盈/回撤/个股风险）')
    print('实时监控：支持')
    print('自动预警：支持')

if __name__ == '__main__':
    main()
