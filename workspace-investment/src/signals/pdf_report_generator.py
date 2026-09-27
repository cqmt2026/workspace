#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 报告生成器 V1.0
自动生成 PDF 格式报告并保存到桌面
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

class PDFReportGenerator:
    """PDF 报告生成器"""
    
    def __init__(self):
        self.desktop = Path.home() / 'Desktop'
        self.reports_dir = self.desktop / 'V13.2_Reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否安装了 reportlab
        try:
            from reportlab.lib.pagesizes import A4
            self.reportlab_available = True
        except ImportError:
            self.reportlab_available = False
            print("[WARN] reportlab 未安装，将使用文本格式")
            print("[INFO] 安装命令：pip install reportlab")
    
    def generate_daily_pdf(self, report: Dict, date: Optional[str] = None) -> Path:
        """生成日报 PDF"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        filename = f'Daily_Report_{date}.pdf'
        filepath = self.reports_dir / filename
        
        print(f"\n{'='*60}")
        print(f"[PDF 日报] {date}")
        print(f"{'='*60}")
        
        if self.reportlab_available:
            self._generate_pdf_with_reportlab(filepath, report, '日报')
        else:
            filepath = self._generate_text_report(filepath.with_suffix('.txt'), report, '日报')
        
        print(f"  保存位置：{filepath}")
        print(f"  [OK] PDF 已保存到桌面")
        
        return filepath
    
    def generate_weekly_pdf(self, report: Dict, week_start: Optional[str] = None) -> Path:
        """生成周报 PDF"""
        if week_start is None:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.strftime('%Y-%m-%d')
        
        filename = f'Weekly_Report_{week_start}.pdf'
        filepath = self.reports_dir / filename
        
        print(f"\n{'='*60}")
        print(f"[PDF 周报] 周起始：{week_start}")
        print(f"{'='*60}")
        
        if self.reportlab_available:
            self._generate_pdf_with_reportlab(filepath, report, '周报')
        else:
            filepath = self._generate_text_report(filepath.with_suffix('.txt'), report, '周报')
        
        print(f"  保存位置：{filepath}")
        print(f"  [OK] PDF 已保存到桌面")
        
        return filepath
    
    def generate_monthly_pdf(self, report: Dict, month: Optional[str] = None) -> Path:
        """生成月报 PDF"""
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        filename = f'Monthly_Report_{month}.pdf'
        filepath = self.reports_dir / filename
        
        print(f"\n{'='*60}")
        print(f"[PDF 月报] 月份：{month}")
        print(f"{'='*60}")
        
        if self.reportlab_available:
            self._generate_pdf_with_reportlab(filepath, report, '月报')
        else:
            filepath = self._generate_text_report(filepath.with_suffix('.txt'), report, '月报')
        
        print(f"  保存位置：{filepath}")
        print(f"  [OK] PDF 已保存到桌面")
        
        return filepath
    
    def _generate_pdf_with_reportlab(self, filepath: Path, report: Dict, report_type: str):
        """使用 reportlab 生成 PDF"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        c = canvas.Canvas(str(filepath), pagesize=A4)
        width, height = A4
        
        # 标题
        c.setFont('Helvetica-Bold', 24)
        c.drawCentredString(width/2, height - 2*cm, f'V13.2 {report_type}报告')
        
        # 日期
        c.setFont('Helvetica', 12)
        date_str = report.get('date', report.get('week_start', report.get('month', 'N/A')))
        c.drawString(2*cm, height - 3*cm, f'日期：{date_str}')
        c.drawString(2*cm, height - 3.5*cm, f'生成时间：{report.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}')
        
        # 内容
        y = height - 5*cm
        
        # 投资组合
        if 'portfolio' in report:
            c.setFont('Helvetica-Bold', 14)
            c.drawString(2*cm, y, '投资组合')
            y -= 0.8*cm
            
            c.setFont('Helvetica', 11)
            portfolio = report['portfolio']
            
            if 'total_value' in portfolio:
                c.drawString(2.5*cm, y, f'总市值：¥{portfolio["total_value"]:,.2f}')
                y -= 0.6*cm
            
            if 'daily_change' in portfolio:
                change = portfolio['daily_change']
                change_pct = portfolio['daily_change_pct']
                c.drawString(2.5*cm, y, f'日盈亏：¥{change:,.2f} ({change_pct:+.2f}%)')
                y -= 0.6*cm
            
            if 'weekly_change' in portfolio:
                change = portfolio['weekly_change']
                change_pct = portfolio['weekly_change_pct']
                c.drawString(2.5*cm, y, f'周盈亏：¥{change:,.2f} ({change_pct:+.2f}%)')
                y -= 0.6*cm
            
            if 'monthly_change' in portfolio:
                change = portfolio['monthly_change']
                change_pct = portfolio['monthly_change_pct']
                c.drawString(2.5*cm, y, f'月盈亏：¥{change:,.2f} ({change_pct:+.2f}%)')
                y -= 0.6*cm
            
            if 'position_ratio' in portfolio:
                c.drawString(2.5*cm, y, f'仓位：{portfolio["position_ratio"]*100:.0f}%')
                y -= 0.6*cm
            
            y -= 0.5*cm
        
        # 市场概览
        if 'market_summary' in report:
            c.setFont('Helvetica-Bold', 14)
            c.drawString(2*cm, y, '市场概览')
            y -= 0.8*cm
            
            c.setFont('Helvetica', 11)
            market = report['market_summary']
            for key, value in market.items():
                c.drawString(2.5*cm, y, f'{key}: {value}')
                y -= 0.6*cm
            
            y -= 0.5*cm
        
        # 交易统计
        if 'trades_today' in report or 'trades_this_week' in report or 'trades_this_month' in report:
            c.setFont('Helvetica-Bold', 14)
            c.drawString(2*cm, y, '交易统计')
            y -= 0.8*cm
            
            c.setFont('Helvetica', 11)
            if 'trades_today' in report:
                c.drawString(2.5*cm, y, f'今日交易：{report["trades_today"]}笔')
                y -= 0.6*cm
            if 'trades_this_week' in report:
                c.drawString(2.5*cm, y, f'本周交易：{report["trades_this_week"]}笔')
                y -= 0.6*cm
            if 'trades_this_month' in report:
                c.drawString(2.5*cm, y, f'本月交易：{report["trades_this_month"]}笔')
                y -= 0.6*cm
            
            if 'win_rate' in report:
                c.drawString(2.5*cm, y, f'胜率：{report["win_rate"]*100:.0f}%')
                y -= 0.6*cm
            
            y -= 0.5*cm
        
        # 个股表现
        if 'top_performers' in report or 'best_stock' in report:
            c.setFont('Helvetica-Bold', 14)
            c.drawString(2*cm, y, '个股表现')
            y -= 0.8*cm
            
            c.setFont('Helvetica', 11)
            if 'top_performers' in report:
                for i, stock in enumerate(report['top_performers'][:3], 1):
                    c.drawString(2.5*cm, y, f'{i}. {stock["name"]} ({stock["code"]}) {stock["change_pct"]:+.1f}%')
                    y -= 0.6*cm
            
            if 'best_stock' in report:
                best = report['best_stock']
                c.drawString(2.5*cm, y, f'最佳：{best["name"]} ({best["code"]}) {best["change_pct"]:+.1f}%')
                y -= 0.6*cm
            
            y -= 0.5*cm
        
        # 备注
        if 'notes' in report:
            c.setFont('Helvetica-Bold', 14)
            c.drawString(2*cm, y, '备注')
            y -= 0.8*cm
            
            c.setFont('Helvetica', 11)
            notes = report['notes']
            # 自动换行
            max_width = width - 4*cm
            lines = self._wrap_text(c, notes, max_width)
            for line in lines:
                c.drawString(2.5*cm, y, line)
                y -= 0.6*cm
        
        # 页脚
        page_num = c.getPageNumber()
        c.setFont('Helvetica', 9)
        c.drawCentredString(width/2, 2*cm, f'第 {page_num} 页')
        c.drawString(2*cm, 2*cm, f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        c.save()
    
    def _generate_text_report(self, filepath: Path, report: Dict, report_type: str) -> Path:
        """生成文本格式报告（reportlab 不可用时）"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"V13.2 {report_type}报告\n")
            f.write(f"{'='*60}\n\n")
            
            date_str = report.get('date', report.get('week_start', report.get('month', 'N/A')))
            f.write(f"日期：{date_str}\n")
            f.write(f"生成时间：{report.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n\n")
            
            # 投资组合
            if 'portfolio' in report:
                f.write("投资组合\n")
                f.write("-"*40 + "\n")
                portfolio = report['portfolio']
                if 'total_value' in portfolio:
                    f.write(f"总市值：¥{portfolio['total_value']:,.2f}\n")
                if 'daily_change' in portfolio:
                    f.write(f"日盈亏：¥{portfolio['daily_change']:,.2f} ({portfolio['daily_change_pct']:+.2f}%)\n")
                if 'weekly_change' in portfolio:
                    f.write(f"周盈亏：¥{portfolio['weekly_change']:,.2f} ({portfolio['weekly_change_pct']:+.2f}%)\n")
                if 'monthly_change' in portfolio:
                    f.write(f"月盈亏：¥{portfolio['monthly_change']:,.2f} ({portfolio['monthly_change_pct']:+.2f}%)\n")
                if 'position_ratio' in portfolio:
                    f.write(f"仓位：{portfolio['position_ratio']*100:.0f}%\n")
                f.write("\n")
            
            # 市场概览
            if 'market_summary' in report:
                f.write("市场概览\n")
                f.write("-"*40 + "\n")
                for key, value in report['market_summary'].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            
            # 交易统计
            if 'trades_today' in report or 'trades_this_week' in report or 'trades_this_month' in report:
                f.write("交易统计\n")
                f.write("-"*40 + "\n")
                if 'trades_today' in report:
                    f.write(f"今日交易：{report['trades_today']}笔\n")
                if 'trades_this_week' in report:
                    f.write(f"本周交易：{report['trades_this_week']}笔\n")
                if 'trades_this_month' in report:
                    f.write(f"本月交易：{report['trades_this_month']}笔\n")
                if 'win_rate' in report:
                    f.write(f"胜率：{report['win_rate']*100:.0f}%\n")
                f.write("\n")
            
            # 个股表现
            if 'top_performers' in report or 'best_stock' in report:
                f.write("个股表现\n")
                f.write("-"*40 + "\n")
                if 'top_performers' in report:
                    for i, stock in enumerate(report['top_performers'][:3], 1):
                        f.write(f"{i}. {stock['name']} ({stock['code']}) {stock['change_pct']:+.1f}%\n")
                if 'best_stock' in report:
                    best = report['best_stock']
                    f.write(f"最佳：{best['name']} ({best['code']}) {best['change_pct']:+.1f}%\n")
                f.write("\n")
            
            # 备注
            if 'notes' in report:
                f.write("备注\n")
                f.write("-"*40 + "\n")
                f.write(f"{report['notes']}\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return filepath
    
    def _wrap_text(self, canvas, text: str, max_width: float) -> List[str]:
        """文本自动换行"""
        lines = []
        words = text.split()
        current_line = ''
        
        for word in words:
            test_line = current_line + ' ' + word if current_line else word
            width = canvas.stringWidth(test_line, 'Helvetica', 11)
            
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def auto_generate_all(self, report: Dict, report_type: str) -> Path:
        """自动生成所有格式报告"""
        if report_type == 'daily':
            return self.generate_daily_pdf(report)
        elif report_type == 'weekly':
            return self.generate_weekly_pdf(report)
        elif report_type == 'monthly':
            return self.generate_monthly_pdf(report)
        else:
            raise ValueError(f"未知报告类型：{report_type}")


def test_pdf_generator():
    """测试 PDF 生成器"""
    print("="*60)
    print("PDF 报告生成器测试")
    print("="*60)
    
    generator = PDFReportGenerator()
    
    # 测试日报
    daily_report = {
        'type': 'daily',
        'date': '2026-03-15',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_summary': {
            '上证指数': '3050.50 (+0.5%)',
            '深证成指': '10200.30 (+0.8%)',
            '创业板指': '2100.50 (+1.2%)'
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
    
    print("\n[测试] 生成日报 PDF...")
    daily_pdf = generator.generate_daily_pdf(daily_report)
    
    # 测试周报
    weekly_report = {
        'type': 'weekly',
        'week_start': '2026-03-11',
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
    
    print("\n[测试] 生成周报 PDF...")
    weekly_pdf = generator.generate_weekly_pdf(weekly_report)
    
    print("\n[OK] 测试完成")
    print(f"  日报：{daily_pdf}")
    print(f"  周报：{weekly_pdf}")
    
    return True


if __name__ == '__main__':
    test_pdf_generator()
