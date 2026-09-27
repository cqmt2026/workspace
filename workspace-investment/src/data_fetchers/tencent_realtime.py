# -*- coding: utf-8 -*-
"""
腾讯财经实时数据获取
API: http://qt.gtimg.cn/q=sh600519
"""

import requests
import json
from pathlib import Path
from datetime import datetime

class TencentDataFetcher:
    """腾讯财经数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        
        self.output_dir = Path(__file__).parent.parent / 'outputs'
        self.reports_dir = self.output_dir / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_stock(self, code):
        """获取单只股票实时行情"""
        try:
            url = f'http://qt.gtimg.cn/q={code}'
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'gbk'
            
            if resp.status_code == 200:
                data = resp.text.strip()
                if data:
                    parts = data.split('~')
                    if len(parts) >= 30:
                        return {
                            'code': code,
                            'name': parts[1],
                            'current': float(parts[3]),
                            'open': float(parts[5]),
                            'high': float(parts[33]) if len(parts) > 33 else None,
                            'low': float(parts[34]) if len(parts) > 34 else None,
                            'volume': float(parts[6]) if len(parts) > 6 else None,
                            'turnover': float(parts[37]) if len(parts) > 37 else None,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
            return None
        except Exception as e:
            print(f'获取失败 {code}: ' + str(e))
            return None
    
    def fetch_stocks(self, codes):
        """批量获取股票行情"""
        print(f'获取 {len(codes)} 只股票数据...')
        
        results = []
        for code in codes:
            data = self.fetch_stock(code)
            if data:
                results.append(data)
                print(f'  OK {data["name"]} ({code}): {data["current"]}元')
        
        return results
    
    def fetch_index(self):
        """获取大盘指数"""
        print('获取大盘指数...')
        
        indices = {
            'sh000001': '上证指数',
            'sz399001': '深证成指',
            'sz399006': '创业板指',
            'sh000688': '科创 50',
        }
        
        results = []
        for code, name in indices.items():
            data = self.fetch_stock(code)
            if data:
                results.append(data)
                print(f'  OK {name}: {data["current"]}点')
        
        return results
    
    def fetch_stock_pool(self):
        """获取股票池数据"""
        print('获取股票池数据...')
        
        stock_pool_file = Path(__file__).parent.parent / 'config' / 'stock_pool.json'
        
        if stock_pool_file.exists():
            with open(stock_pool_file, 'r', encoding='utf-8') as f:
                pool = json.load(f)
            
            # 收集所有股票代码
            codes = []
            for category in ['focus', 'observation', 'core', 'reserve']:
                for stock in pool.get(category, []):
                    code = stock.get('code', '')
                    if code:
                        # 添加市场前缀
                        if code.startswith('6'):
                            code = f'sh{code}'
                        elif code.startswith('3') or code.startswith('0'):
                            code = f'sz{code}'
                        codes.append(code)
            
            print(f'  股票池：{len(codes)} 只')
            return self.fetch_stocks(codes[:20])  # 限制前 20 只测试
        else:
            print('  WARN 股票池配置文件不存在')
            return []
    
    def generate_report(self, data):
        """生成实时数据报告"""
        print('生成报告...')
        
        today = datetime.now().strftime('%Y-%m-%d')
        report_path = self.reports_dir / f'tencent_realtime_{today}.md'
        
        content = f"""# 腾讯财经实时数据 - {today}

**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据来源**: 腾讯财经 API  
**状态**: 实时获取

---

## 📊 大盘指数

| 指数 | 当前价 | 开盘 | 最高 | 最低 |
|------|--------|------|------|------|
"""
        
        # 添加指数数据
        indices = [d for d in data if d['code'].startswith('sh000') or d['code'].startswith('sz399')]
        for idx in indices:
            content += f"| {idx['name']} | {idx['current']} | {idx['open']} | {idx.get('high', '-')} | {idx.get('low', '-')} |\n"
        
        content += f"""
---

## 📈 个股行情

| 代码 | 名称 | 当前价 | 开盘 | 最高 | 最低 | 成交量 |
|------|------|--------|------|------|------|--------|
"""
        
        # 添加个股数据
        stocks = [d for d in data if not (d['code'].startswith('sh000') or d['code'].startswith('sz399'))]
        for stock in stocks:
            content += f"| {stock['code']} | {stock['name']} | {stock['current']} | {stock['open']} | {stock.get('high', '-')} | {stock.get('low', '-')} | {stock.get('volume', '-')} |\n"
        
        content += f"""
---

## 💡 数据说明

- **数据来源**: 腾讯财经 (http://qt.gtimg.cn/)
- **更新时间**: 交易日 9:30-15:00 实时更新
- **延迟**: 可能有 15 分钟延迟

---

_报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'  报告已保存：{report_path}')
        return report_path
    
    def fetch_all(self):
        """获取全部数据"""
        print('='*60)
        print('腾讯财经实时数据获取')
        print('='*60)
        print()
        
        data = []
        
        # 1. 获取大盘指数
        print('[1] 大盘指数...')
        indices = self.fetch_index()
        data.extend(indices)
        print()
        
        # 2. 获取股票池数据
        print('[2] 股票池...')
        stocks = self.fetch_stock_pool()
        data.extend(stocks)
        print()
        
        # 3. 生成报告
        print('[3] 生成报告...')
        report_path = self.generate_report(data)
        
        print()
        print('='*60)
        print('数据获取完成！')
        print('='*60)
        
        return data, report_path


if __name__ == '__main__':
    fetcher = TencentDataFetcher()
    fetcher.fetch_all()
