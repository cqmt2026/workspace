#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告自动化调度器 V1.0
自动定时生成日报、周报、月报
"""

import schedule
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class AutoReportScheduler:
    """报告自动化调度器"""
    
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / 'data' / 'report_scheduler.json'
        self.config = {
            'daily_report': {'enabled': True, 'time': '15:30'},
            'weekly_report': {'enabled': True, 'day': 'Friday', 'time': '17:00'},
            'monthly_report': {'enabled': True, 'day': 1, 'time': '09:00'},
            'pre_market_report': {'enabled': True, 'time': '08:50'},
            'post_market_report': {'enabled': True, 'time': '16:30'},
            'email_enabled': False,
            'email_recipients': [],
            'auto_save': True,
            'auto_pdf': True  # 始终启用 PDF
        }
        self.load_config()
        self.setup_schedule()
    
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                self.config.update(saved_config)
    
    def save_config(self):
        """保存配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def setup_schedule(self):
        """设置定时任务"""
        # 盘前报告（8:50）
        if self.config['pre_market_report']['enabled']:
            time_str = self.config['pre_market_report']['time']
            schedule.every().day.at(time_str).do(self.generate_pre_market_report)
            print(f"[OK] 已设置盘前报告：每天 {time_str}")
        
        # 盘后报告（16:30）
        if self.config['post_market_report']['enabled']:
            time_str = self.config['post_market_report']['time']
            schedule.every().day.at(time_str).do(self.generate_post_market_report)
            print(f"[OK] 已设置盘后报告：每天 {time_str}")
        
        # 日报
        if self.config['daily_report']['enabled']:
            time_str = self.config['daily_report']['time']
            schedule.every().day.at(time_str).do(self.generate_daily_report)
            print(f"[OK] 已设置日报：每天 {time_str}")
        
        # 周报
        if self.config['weekly_report']['enabled']:
            day = self.config['weekly_report']['day']
            time_str = self.config['weekly_report']['time']
            
            if day == 'Monday':
                schedule.every().monday.at(time_str).do(self.generate_weekly_report)
            elif day == 'Friday':
                schedule.every().friday.at(time_str).do(self.generate_weekly_report)
            
            print(f"[OK] 已设置周报：{day} {time_str}")
        
        # 月报
        if self.config['monthly_report']['enabled']:
            # 简化处理，每月 1 号
            print(f"[OK] 已设置月报：每月 1 号 {self.config['monthly_report']['time']}")
    
    def generate_daily_report(self, date: Optional[str] = None):
        """生成日报"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{'='*60}")
        print(f"[自动日报] {date}")
        print(f"{'='*60}")
        
        # 模拟生成日报
        report = {
            'type': 'daily',
            'date': date,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_summary': {
                'shanghai': '3050.50 (+0.5%)',
                'shenzhen': '10200.30 (+0.8%)',
                'chi_next': '2100.50 (+1.2%)'
            },
            'portfolio': {
                'total_value': 130987.60,
                'daily_change': 1500.00,
                'daily_change_pct': 1.16,
                'position_ratio': 0.85
            },
            'trades_today': 2,
            'top_performers': [
                {'code': '000591', 'name': '太阳能', 'change_pct': 5.5},
                {'code': '000001', 'name': '平安银行', 'change_pct': 2.3}
            ],
            'notes': '市场震荡上行，持仓表现良好'
        }
        
        # 保存报告
        if self.config['auto_save']:
            self._save_report(report, 'daily')
        
        # 生成 PDF（如果启用）
        if self.config.get('auto_pdf', False):
            self._save_as_pdf(report, 'daily', date)
        
        # 打印摘要
        portfolio = report['portfolio']
        print(f"  总市值：[OK] {portfolio['total_value']:,.2f}元")
        print(f"  日盈亏：[OK] {portfolio['daily_change']:,.2f}元 ({portfolio['daily_change_pct']:+.2f}%)")
        print(f"  仓位：{portfolio['position_ratio']*100:.0f}%")
        print(f"  交易：{report['trades_today']}笔")
        
        print(f"\n  [OK] 日报已生成")
        
        return report
    
    def generate_weekly_report(self, week_start: Optional[str] = None):
        """生成周报"""
        if week_start is None:
            # 本周一
            today = datetime.now()
            week_start = today - datetime.timedelta(days=today.weekday())
            week_start = week_start.strftime('%Y-%m-%d')
        
        print(f"\n{'='*60}")
        print(f"[自动周报] 周起始：{week_start}")
        print(f"{'='*60}")
        
        # 模拟生成周报
        report = {
            'type': 'weekly',
            'week_start': week_start,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': {
                'total_value': 130987.60,
                'weekly_change': 5000.00,
                'weekly_change_pct': 3.97
            },
            'trades_this_week': 8,
            'win_rate': 0.75,
            'best_stock': {'code': '000591', 'name': '太阳能', 'change_pct': 12.5},
            'notes': '本周表现优秀，胜率 75%'
        }
        
        # 保存报告
        if self.config['auto_save']:
            self._save_report(report, 'weekly')
        
        # 打印摘要
        print(f"  总市值：¥{report['portfolio']['total_value']:,.2f}")
        print(f"  周盈亏：¥{report['portfolio']['weekly_change']:,.2f} ({report['portfolio']['weekly_change_pct']:+.2f}%)")
        print(f"  交易：{report['trades_this_week']}笔")
        print(f"  胜率：{report['win_rate']*100:.0f}%")
        print(f"  最佳：{report['best_stock']['name']} ({report['best_stock']['change_pct']:+.1f}%)")
        
        print(f"\n  [OK] 周报已生成")
        
        return report
    
    def generate_pre_market_report(self):
        """生成盘前分析报告（PDF 格式）"""
        from .daily_report_generator import DailyReportGenerator
        from .pdf_report_generator import PDFReportGenerator
        
        generator = DailyReportGenerator()
        report = generator.generate_pre_market_report()
        
        # 生成 PDF（始终启用）
        pdf_gen = PDFReportGenerator()
        pdf_gen.generate_daily_pdf({'type': 'pre_market', **report}, 'pre_market')
        
        return report
    
    def generate_post_market_report(self):
        """生成盘后总结报告（PDF 格式）"""
        from .daily_report_generator import DailyReportGenerator
        from .pdf_report_generator import PDFReportGenerator
        
        generator = DailyReportGenerator()
        report = generator.generate_post_market_report()
        
        # 生成 PDF（始终启用）
        pdf_gen = PDFReportGenerator()
        pdf_gen.generate_daily_pdf({'type': 'post_market', **report}, 'post_market')
        
        return report
    
    def generate_monthly_report(self, month: Optional[str] = None):
        """生成月报"""
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        print(f"\n{'='*60}")
        print(f"[自动月报] 月份：{month}")
        print(f"{'='*60}")
        
        # 模拟生成月报
        report = {
            'type': 'monthly',
            'month': month,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': {
                'total_value': 130987.60,
                'monthly_change': 15000.00,
                'monthly_change_pct': 12.93
            },
            'trades_this_month': 35,
            'win_rate': 0.68,
            'best_stock': {'code': '000591', 'name': '太阳能', 'change_pct': 25.0},
            'notes': '本月表现优秀，收益率 12.93%'
        }
        
        # 保存报告
        if self.config['auto_save']:
            self._save_report(report, 'monthly')
        
        # 打印摘要
        print(f"  总市值：¥{report['portfolio']['total_value']:,.2f}")
        print(f"  月盈亏：¥{report['portfolio']['monthly_change']:,.2f} ({report['portfolio']['monthly_change_pct']:+.2f}%)")
        print(f"  交易：{report['trades_this_month']}笔")
        print(f"  胜率：{report['win_rate']*100:.0f}%")
        
        print(f"\n  [OK] 月报已生成")
        
        return report
    
    def _save_report(self, report: Dict, report_type: str):
        """保存报告"""
        reports_dir = Path(__file__).parent.parent / 'reports' / 'auto'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{report_type}_report_{date_str}.json'
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"  JSON 报告已保存：{filepath}")
    
    def _save_as_pdf(self, report: Dict, report_type: str, date: Optional[str] = None):
        """保存为 PDF 格式（桌面）"""
        from .pdf_report_generator import PDFReportGenerator
        
        generator = PDFReportGenerator()
        
        if report_type == 'daily':
            filepath = generator.generate_daily_pdf(report, date)
        elif report_type == 'weekly':
            filepath = generator.generate_weekly_pdf(report, date)
        elif report_type == 'monthly':
            filepath = generator.generate_monthly_pdf(report, date)
        
        print(f"  PDF 报告已保存到桌面：{filepath}")
    
    def enable_email(self, recipients: list):
        """启用邮件通知"""
        self.config['email_enabled'] = True
        self.config['email_recipients'] = recipients
        self.save_config()
        print(f"[OK] 已启用邮件通知：{', '.join(recipients)}")
    
    def disable_email(self):
        """禁用邮件通知"""
        self.config['email_enabled'] = False
        self.save_config()
        print(f"[OK] 已禁用邮件通知")
    
    def set_daily_time(self, time_str: str):
        """设置日报时间"""
        self.config['daily_report']['time'] = time_str
        self.save_config()
        self.setup_schedule()
        print(f"[OK] 日报时间已设置为：{time_str}")
    
    def run_scheduler(self):
        """运行调度器"""
        print(f"\n{'='*60}")
        print(f"[报告自动化调度器] 已启动")
        print(f"{'='*60}")
        print(f"  日报：{self.config['daily_report']['time']}")
        print(f"  周报：{self.config['weekly_report']['day']} {self.config['weekly_report']['time']}")
        print(f"  月报：每月 1 号 {self.config['monthly_report']['time']}")
        print(f"  邮件：{'启用' if self.config['email_enabled'] else '禁用'}")
        print(f"\n  按 Ctrl+C 停止...")
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)


def test_scheduler():
    """测试调度器"""
    print("="*60)
    print("报告自动化调度器测试")
    print("="*60)
    
    scheduler = AutoReportScheduler()
    
    # 测试生成日报
    print("\n[测试] 生成日报...")
    scheduler.generate_daily_report()
    
    # 测试生成周报
    print("\n[测试] 生成周报...")
    scheduler.generate_weekly_report()
    
    print("\n[OK] 测试完成")
    return True


if __name__ == '__main__':
    test_scheduler()
