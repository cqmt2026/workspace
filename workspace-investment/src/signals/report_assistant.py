#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成小助手 V1.0
生成日报、周报、月报
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

class ReportAssistant:
    """报告生成小助手"""
    
    def __init__(self):
        self.report_dir = Path(__file__).parent.parent / 'reports'
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_report(self, portfolio, trades, date=None):
        """生成日报"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"[生成日报] 日期：{date}")
        
        # 计算当日盈亏
        total_value = sum(p.get('market_value', 0) for p in portfolio)
        total_profit = sum(p.get('profit', 0) for p in portfolio)
        total_profit_pct = (total_profit / (total_value - total_profit)) * 100 if total_value > total_profit else 0
        
        # 交易统计
        buy_count = sum(1 for t in trades if t.get('action') == 'buy')
        sell_count = sum(1 for t in trades if t.get('action') == 'sell')
        
        report = {
            'type': 'daily',
            'date': date,
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': {
                'total_value': total_value,
                'total_profit': total_profit,
                'total_profit_pct': total_profit_pct,
                'holding_count': len(portfolio)
            },
            'trades': {
                'total': len(trades),
                'buy_count': buy_count,
                'sell_count': sell_count
            },
            'holdings': portfolio,
            'trade_details': trades
        }
        
        # 保存报告
        filename = f'daily_report_{date}.json'
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"  总市值：[OK] {total_value:,.0f}元")
        print(f"  总盈亏：[OK] {total_profit:,.0f}元 ({total_profit_pct:+.1f}%)")
        print(f"  交易次数：{len(trades)}")
        print(f"  报告已保存：{filepath}")
        
        return report
    
    def generate_weekly_report(self, portfolio, trades, week_start=None):
        """生成周报"""
        if week_start is None:
            # 本周一
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.strftime('%Y-%m-%d')
        
        print(f"[生成周报] 周起始：{week_start}")
        
        # 周统计
        total_value = sum(p.get('market_value', 0) for p in portfolio)
        total_profit = sum(p.get('profit', 0) for p in portfolio)
        
        # 周交易统计
        week_trades = [t for t in trades if t.get('date', '') >= week_start]
        week_profit = sum(t.get('profit', 0) for t in week_trades if t.get('action') == 'sell')
        
        report = {
            'type': 'weekly',
            'week_start': week_start,
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': {
                'total_value': total_value,
                'total_profit': total_profit,
                'holding_count': len(portfolio)
            },
            'trades': {
                'total': len(week_trades),
                'profit': week_profit
            }
        }
        
        # 保存报告
        filename = f'weekly_report_{week_start}.json'
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"  总市值：¥{total_value:,.0f}")
        print(f"  周盈利：¥{week_profit:,.0f}")
        print(f"  报告已保存：{filepath}")
        
        return report
    
    def generate_monthly_report(self, portfolio, trades, month=None):
        """生成月报"""
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        print(f"[生成月报] 月份：{month}")
        
        # 月统计
        total_value = sum(p.get('market_value', 0) for p in portfolio)
        total_profit = sum(p.get('profit', 0) for p in portfolio)
        
        # 月交易统计
        month_trades = [t for t in trades if t.get('date', '').startswith(month)]
        month_profit = sum(t.get('profit', 0) for t in month_trades if t.get('action') == 'sell')
        
        report = {
            'type': 'monthly',
            'month': month,
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': {
                'total_value': total_value,
                'total_profit': total_profit,
                'holding_count': len(portfolio)
            },
            'trades': {
                'total': len(month_trades),
                'profit': month_profit
            }
        }
        
        # 保存报告
        filename = f'monthly_report_{month}.json'
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"  总市值：¥{total_value:,.0f}")
        print(f"  月盈利：¥{month_profit:,.0f}")
        print(f"  报告已保存：{filepath}")
        
        return report
    
    def list_reports(self, report_type='all'):
        """列出报告"""
        reports = []
        for f in self.report_dir.glob('*.json'):
            if report_type == 'all' or report_type in f.name:
                reports.append(f.name)
        return reports
    
    def schedule_auto_daily(self, time_str='15:30'):
        """设置自动日报"""
        from .auto_report_scheduler import AutoReportScheduler
        scheduler = AutoReportScheduler()
        scheduler.set_daily_time(time_str)
        print(f"[OK] 已设置自动日报：每天 {time_str}")
    
    def schedule_auto_weekly(self, day='Friday', time_str='17:00'):
        """设置自动周报"""
        from .auto_report_scheduler import AutoReportScheduler
        scheduler = AutoReportScheduler()
        scheduler.config['weekly_report']['day'] = day
        scheduler.config['weekly_report']['time'] = time_str
        scheduler.save_config()
        print(f"[OK] 已设置自动周报：{day} {time_str}")
    
    def export_to_pdf(self, report, filename=None):
        """导出 PDF 格式（简化版）"""
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        filepath = self.report_dir / filename
        
        # 简化版：保存为文本
        with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
            f.write(f"报告类型：{report.get('type', 'N/A')}\n")
            f.write(f"生成时间：{report.get('generated_time', 'N/A')}\n")
            f.write(f"\n内容:\n{json.dumps(report, ensure_ascii=False, indent=2)}")
        
        print(f"[OK] 报告已导出：{filepath.with_suffix('.txt')}")
        print(f"  注：完整 PDF 功能需要安装 reportlab 库")
        
        return filepath.with_suffix('.txt')
    
    def send_to_email(self, report, recipients, subject=None):
        """邮件发送报告（简化版）"""
        if subject is None:
            subject = f"V13.2 {report.get('type', '报告')} - {datetime.now().strftime('%Y-%m-%d')}"
        
        print(f"[邮件发送]")
        print(f"  收件人：{', '.join(recipients)}")
        print(f"  主题：{subject}")
        print(f"  内容：{report.get('type', '报告')}")
        print(f"\n  注：完整邮件功能需要配置 SMTP 服务器")
        
        return {'status': 'simulated', 'recipients': recipients, 'subject': subject}
    
    def save_as_pdf(self, report, report_type='daily', date=None):
        """保存为 PDF 格式（自动保存到桌面）"""
        from .pdf_report_generator import PDFReportGenerator
        
        generator = PDFReportGenerator()
        
        if report_type == 'daily':
            return generator.generate_daily_pdf(report, date)
        elif report_type == 'weekly':
            return generator.generate_weekly_pdf(report, date)
        elif report_type == 'monthly':
            return generator.generate_monthly_pdf(report, date)
        else:
            raise ValueError(f"未知报告类型：{report_type}")


def test_report():
    """测试报告生成"""
    print("="*60)
    print("报告生成小助手测试")
    print("="*60)
    
    report = ReportAssistant()
    
    # 模拟数据
    portfolio = [
        {'code': '000001', 'name': '平安银行', 'market_value': 11000, 'profit': 500},
        {'code': '600000', 'name': '浦发银行', 'market_value': 8300, 'profit': -200}
    ]
    
    trades = [
        {'action': 'buy', 'code': '000001', 'date': '2026-03-14', 'price': 10.50},
        {'action': 'sell', 'code': '600000', 'date': '2026-03-14', 'price': 8.30, 'profit': -200}
    ]
    
    # 生成日报
    print("\n[生成日报]")
    daily = report.generate_daily_report(portfolio, trades)
    
    # 生成周报
    print("\n[生成周报]")
    weekly = report.generate_weekly_report(portfolio, trades)
    
    print("\n[OK] 测试完成")
    return True


if __name__ == '__main__':
    test_report()
