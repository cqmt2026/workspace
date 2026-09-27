#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Market Hot Topics Monitor v8.0
市场热点监控工具
数据源：东方财富 API（免费、实时）
"""

import requests
import json
from datetime import datetime
from pathlib import Path

class HotTopicsMonitor:
    """市场热点监控器"""
    
    def __init__(self):
        self.cache_file = Path('hot_topics_cache.json')
    
    def get_stock_rank(self):
        """
        获取个股涨幅榜（东方财富 API）
        
        返回：前 100 只股票
        """
        try:
            url = 'http://push2.eastmoney.com/api/qt/clist/get'
            params = {
                'pn': '1',
                'pz': '100',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',
                'fields': 'f12,f14,f2,f3,f5,f8,f13,f128,f136,f115,f152',
                '_': '1623833739532',
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and data['data'].get('diff'):
                    stocks = []
                    for s in data['data']['diff']:
                        stocks.append({
                            'code': s['f12'],
                            'name': s['f14'],
                            'price': s['f2'],
                            'change': s['f3'],
                            'volume': s['f5'],
                            'turnover': s['f8'],
                            'market_cap': s['f115'],
                        })
                    return stocks
        except Exception as e:
            print(f"获取涨幅榜失败：{e}")
        
        return []
    
    def get_sector_rank(self):
        """
        获取板块涨幅榜
        
        返回：前 50 个板块
        """
        try:
            url = 'http://push2.eastmoney.com/api/qt/clist/get'
            params = {
                'pn': '1',
                'pz': '50',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'm:90 t:1',
                'fields': 'f12,f14,f2,f3,f5,f8',
                '_': '1623833739532',
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and data['data'].get('diff'):
                    sectors = []
                    for s in data['data']['diff']:
                        sectors.append({
                            'code': s['f12'],
                            'name': s['f14'],
                            'change': s['f3'],
                            'volume': s['f5'],
                        })
                    return sectors
        except Exception as e:
            print(f"获取板块榜失败：{e}")
        
        return []
    
    def get_limit_up_pool(self):
        """
        获取涨停池
        
        返回：涨停股票列表
        """
        try:
            url = 'http://push2ex.eastmoney.com/getTopicZTPool'
            params = {
                'ut': '7eea3edcaed734bea9cbfc24409ed989',
                'dpt': 'wz.ztzt',
                'Pageindex': '0',
                'Pagesize': '100',
                'sort': 'fbt:asc',
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    zt_data = data['data']
                    stocks = []
                    if zt_data.get('pool'):
                        for s in zt_data['pool']:
                            stocks.append({
                                'code': s.get('zdm', ''),
                                'name': s.get('zjmc', ''),
                                'price': s.get('zxcj', 0),
                                'change': s.get('zf', 0),
                                'board_count': s.get('lban', s.get('lb', 0)),
                                'open_times': s.get('kzztcs', 0),
                                'first_time': s.get('fstime', ''),
                            })
                    return stocks, zt_data.get('ztCount', 0)
        except Exception as e:
            print(f"获取涨停池失败：{e}")
        
        return [], 0
    
    def analyze_hot_topics(self, stocks, sectors, limit_up_stocks):
        """分析热点"""
        # 统计涨停股板块分布
        sector_dist = {}
        for stock in limit_up_stocks:
            # 简化：从股票名称推断板块
            name = stock['name']
            if 'AI' in name or '智能' in name or '芯片' in name:
                sector = 'AI/芯片'
            elif '新能源' in name or '锂电' in name or '光伏' in name:
                sector = '新能源'
            elif '医药' in name or '医疗' in name:
                sector = '医药'
            elif '消费' in name or '酒' in name:
                sector = '消费'
            elif '金融' in name or '银行' in name or '券商' in name:
                sector = '金融'
            else:
                sector = '其他'
            
            sector_dist[sector] = sector_dist.get(sector, 0) + 1
        
        # 找出主流热点
        hot_sectors = sorted(sector_dist.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'limit_up_count': len(limit_up_stocks),
            'sector_distribution': sector_dist,
            'hot_sectors': hot_sectors,
            'top_sectors': sectors[:10] if sectors else [],
            'top_stocks': stocks[:20] if stocks else [],
        }
    
    def display_report(self, analysis):
        """显示热点报告"""
        print("=" * 80)
        print(f"市场热点报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)
        print()
        
        # 涨停统计
        print(f"📊 涨停统计:")
        print(f"  涨停家数：{analysis['limit_up_count']}")
        print()
        
        # 板块分布
        print(f"🔥 涨停股板块分布:")
        for sector, count in analysis['sector_distribution'].items():
            bar = '█' * count
            print(f"  {sector:<10} {count:>3} {bar}")
        print()
        
        # 主流热点
        print(f"🎯 主流热点:")
        for i, (sector, count) in enumerate(analysis['hot_sectors'], 1):
            print(f"  {i}. {sector}: {count}只涨停")
        print()
        
        # 板块涨幅榜
        print(f"📈 板块涨幅榜 TOP10:")
        for i, sector in enumerate(analysis['top_sectors'], 1):
            print(f"  {i}. {sector['name']}: {sector['change']:+.2f}%")
        print()
        
        # 个股涨幅榜
        print(f"📈 个股涨幅榜 TOP10:")
        for i, stock in enumerate(analysis['top_stocks'], 1):
            print(f"  {i}. {stock['code']} {stock['name']}: {stock['price']:.2f} ({stock['change']:+.2f}%)")
        print()
    
    def save_cache(self, analysis):
        """保存缓存"""
        cache_data = {
            'time': datetime.now().isoformat(),
            'analysis': analysis,
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def get_hot_topics(self):
        """获取热点"""
        print("获取个股涨幅榜...")
        stocks = self.get_stock_rank()
        print(f"  获取到 {len(stocks)} 只股票")
        
        print("获取板块涨幅榜...")
        sectors = self.get_sector_rank()
        print(f"  获取到 {len(sectors)} 个板块")
        
        print("获取涨停池...")
        limit_up_stocks, limit_up_count = self.get_limit_up_pool()
        print(f"  涨停家数：{limit_up_count}")
        
        print("分析热点...")
        analysis = self.analyze_hot_topics(stocks, sectors, limit_up_stocks)
        
        # 保存缓存
        self.save_cache(analysis)
        
        return analysis
    
    def show_menu(self):
        """显示菜单"""
        print("=" * 80)
        print("市场热点监控工具 v8.0")
        print("=" * 80)
        print()
        print("请选择操作:")
        print("  1. 获取最新热点")
        print("  2. 查看涨停池")
        print("  3. 查看板块涨幅榜")
        print("  4. 查看个股涨幅榜")
        print("  0. 退出")
        print()
        
        choice = input("输入选项 (0-4): ").strip()
        
        if choice == '1':
            analysis = self.get_hot_topics()
            self.display_report(analysis)
        
        elif choice == '2':
            stocks, count = self.get_limit_up_pool()
            print(f"\n涨停池：{count}只")
            for s in stocks[:20]:
                print(f"  {s['code']} {s['name']}: {s['board_count']}连板")
        
        elif choice == '3':
            sectors = self.get_sector_rank()
            print(f"\n板块涨幅榜 TOP20:")
            for i, s in enumerate(sectors[:20], 1):
                print(f"  {i}. {s['name']}: {s['change']:+.2f}%")
        
        elif choice == '4':
            stocks = self.get_stock_rank()
            print(f"\n个股涨幅榜 TOP20:")
            for i, s in enumerate(stocks[:20], 1):
                print(f"  {i}. {s['code']} {s['name']}: {s['price']:.2f} ({s['change']:+.2f}%)")
        
        return choice != '0'

def main():
    """主函数"""
    monitor = HotTopicsMonitor()
    
    while monitor.show_menu():
        input("\n按回车键继续...")
    
    print("\n再见！👋\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}\n")
