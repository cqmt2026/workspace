#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六维选股工具 v8.0 - 扩大测试版
测试股票池：50 只（各板块代表性股票）
"""

import baostock as bs
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 导入六维选股功能
from six_dim_screener import get_stock_data, calculate_total_score, get_level

def select_stocks_extended():
    """扩大测试版 - 50 只股票"""
    print("=" * 80)
    print("六维选股工具 v8.0 - 扩大测试")
    print("=" * 80)
    print(f"筛选日期：{datetime.now().strftime('%Y-%m-%d')}")
    print(f"测试股票池：50 只")
    print()
    
    # 登录
    lg = bs.login()
    print(f"登录：{lg.error_msg}")
    
    # 扩大股票池（50 只）
    test_stocks = [
        # AI/科技 (10)
        ('sh.601138', '工业富联'),
        ('sh.688981', '中芯国际'),
        ('sz.002230', '科大讯飞'),
        ('sz.000977', '浪潮信息'),
        ('sh.603019', '中科曙光'),
        ('sh.688111', '金山办公'),
        ('sz.002415', '海康威视'),
        ('sz.002236', '大华股份'),
        ('sz.002439', '启明星辰'),
        ('sh.600570', '恒生电子'),
        
        # 新能源 (10)
        ('sz.300750', '宁德时代'),
        ('sz.002594', '比亚迪'),
        ('sh.601012', '隆基绿能'),
        ('sh.601127', '赛力斯'),
        ('sz.002709', '天赐材料'),
        ('sz.002812', '恩捷股份'),
        ('sz.300014', '亿纬锂能'),
        ('sh.600438', '通威股份'),
        ('sz.002460', '赣锋锂业'),
        ('sz.002340', '格林美'),
        
        # 消费 (10)
        ('sh.600519', '贵州茅台'),
        ('sz.000858', '五粮液'),
        ('sz.000568', '泸州老窖'),
        ('sh.600809', '山西汾酒'),
        ('sz.002714', '牧原股份'),
        ('sz.000895', '双汇发展'),
        ('sz.000333', '美的集团'),
        ('sh.600690', '海尔智家'),
        ('sz.000651', '格力电器'),
        ('sh.601888', '中国中免'),
        
        # 医药 (5)
        ('sh.600276', '恒瑞医药'),
        ('sz.300760', '迈瑞医疗'),
        ('sz.000538', '云南白药'),
        ('sh.600436', '片仔癀'),
        ('sz.300122', '智飞生物'),
        
        # 金融 (5)
        ('sh.600036', '招商银行'),
        ('sh.601318', '中国平安'),
        ('sz.000001', '平安银行'),
        ('sh.600030', '中信证券'),
        ('sh.601688', '华泰证券'),
        
        # 周期/其他 (10)
        ('sh.600900', '长江电力'),
        ('sh.601088', '中国神华'),
        ('sh.600028', '中国石化'),
        ('sh.601857', '中国石油'),
        ('sh.601398', '工商银行'),
        ('sh.601939', '建设银行'),
        ('sh.600048', '保利发展'),
        ('sz.000002', '万科 A'),
        ('sh.600547', '山东黄金'),
        ('sh.601899', '紫金矿业'),
    ]
    
    print(f"\n筛选股票池：{len(test_stocks)} 只")
    print()
    
    results = []
    
    for code, name in test_stocks:
        # 获取数据
        data = get_stock_data(code)
        
        if len(data) < 20:
            continue
        
        # 计算评分
        result = calculate_total_score(code, name, data)
        results.append(result)
    
    # 排序
    results.sort(key=lambda x: x['total'], reverse=True)
    
    # 打印结果
    print(f"\n{'='*80}")
    print("筛选结果:")
    print(f"{'='*80}")
    
    golden = [r for r in results if r['level'] == '黄金买点']
    silver = [r for r in results if r['level'] == '白银买点']
    bronze = [r for r in results if r['level'] == '青铜买点']
    wait = [r for r in results if r['level'] == '观望']
    
    print(f"黄金买点：{len(golden)} 只")
    print(f"白银买点：{len(silver)} 只")
    print(f"青铜买点：{len(bronze)} 只")
    print(f"观望：{len(wait)} 只")
    
    if golden:
        print(f"\n🥇 黄金买点股票:")
        for r in golden[:10]:
            print(f"  {r['code']} {r['name']}: {r['total']}分 (政{r['scores']['policy']} 题{r['scores']['topic']} 情{r['scores']['sentiment']} 量{r['scores']['volume_price']} 技{r['scores']['technical']} 周{r['scores']['cycle']})")
    
    if silver:
        print(f"\n🥈 白银买点股票:")
        for r in silver[:10]:
            print(f"  {r['code']} {r['name']}: {r['total']}分 (政{r['scores']['policy']} 题{r['scores']['topic']} 情{r['scores']['sentiment']} 量{r['scores']['volume_price']} 技{r['scores']['technical']} 周{r['scores']['cycle']})")
    
    if bronze:
        print(f"\n🥉 青铜买点股票:")
        for r in bronze[:10]:
            print(f"  {r['code']} {r['name']}: {r['total']}分")
    
    # 板块分析
    print(f"\n{'='*80}")
    print("板块分析:")
    print(f"{'='*80}")
    
    sectors = {
        'AI/科技': ['工业富联', '中芯国际', '科大讯飞', '浪潮信息', '中科曙光', '金山办公', '海康威视', '大华股份', '启明星辰', '恒生电子'],
        '新能源': ['宁德时代', '比亚迪', '隆基绿能', '赛力斯', '天赐材料', '恩捷股份', '亿纬锂能', '通威股份', '赣锋锂业', '格林美'],
        '消费': ['贵州茅台', '五粮液', '泸州老窖', '山西汾酒', '牧原股份', '双汇发展', '美的集团', '海尔智家', '格力电器', '中国中免'],
        '医药': ['恒瑞医药', '迈瑞医疗', '云南白药', '片仔癀', '智飞生物'],
        '金融': ['招商银行', '中国平安', '平安银行', '中信证券', '华泰证券'],
        '周期': ['长江电力', '中国神华', '中国石化', '中国石油', '工商银行', '建设银行', '保利发展', '万科 A', '山东黄金', '紫金矿业'],
    }
    
    for sector, names in sectors.items():
        sector_results = [r for r in results if r['name'] in names]
        if sector_results:
            avg_score = sum(r['total'] for r in sector_results) / len(sector_results)
            max_score = max(r['total'] for r in sector_results)
            min_score = min(r['total'] for r in sector_results)
            print(f"{sector}: 平均{avg_score:.1f}分 最高{max_score}分 最低{min_score}分")
    
    bs.logout()
    
    return results

if __name__ == '__main__':
    results = select_stocks_extended()
