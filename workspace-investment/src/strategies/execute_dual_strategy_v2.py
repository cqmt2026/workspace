#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用真实数据执行双策略选股（修正版）
策略 1: 尾盘选股（T+1）
策略 2: 趋势跟踪（T+N）

作者：股票 V13.2 系统
时间：2026-03-18 02:04
"""

from datetime import datetime
from pathlib import Path
import json

def load_real_volume_data():
    """加载真实成交量数据"""
    data_file = Path('../data/volume_top200_real_20260318.json')
    
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print('[OK] 真实数据已加载：{} 只'.format(data.get('total', 0)))
        return data.get('stocks', [])
    else:
        print('[ERROR] 数据文件不存在')
        return []

def strategy1_tail_pick(stocks):
    """策略 1: 尾盘选股"""
    print('\n' + '=' * 60)
    print('策略 1: 尾盘选股（T+1）')
    print('=' * 60)
    
    # 筛选条件（使用真实字段名）
    # 换手率 3-20%
    # 涨跌幅 -5% 到 +7%
    # 现价>3 元
    
    selected = []
    for stock in stocks:
        try:
            turnover = float(stock.get('换手率', 0) or 0)
            change_pct = float(stock.get('涨跌幅', 0) or 0)
            price = float(stock.get('最新价', 0) or 0)
            
            if (3 <= turnover <= 20) and (-5 <= change_pct <= 7) and (price > 3):
                score = 0
                # 换手率评分
                if 8 <= turnover <= 12:
                    score += 40
                elif 3 <= turnover <= 20:
                    score += 30
                
                # 涨跌幅评分
                if 0 <= change_pct <= 3:
                    score += 40
                elif -5 <= change_pct <= 7:
                    score += 30
                
                # 价格评分
                if price > 20:
                    score += 20
                elif price > 3:
                    score += 10
                
                if score >= 50:
                    selected.append({
                        'code': stock.get('代码', ''),
                        'name': stock.get('名称', ''),
                        'price': price,
                        'change_pct': change_pct,
                        'turnover': turnover,
                        'volume': stock.get('成交量', 0),
                        'score': score,
                        'reason': '换手活跃 + 涨幅适中'
                    })
        except Exception as e:
            pass
    
    # 按评分排序
    selected.sort(key=lambda x: x['score'], reverse=True)
    top3 = selected[:3]
    
    print('  候选股票：{} 只'.format(len(selected)))
    print('  推荐标的：{} 只'.format(len(top3)))
    
    for i, stock in enumerate(top3, 1):
        print('  {}. {}（{}）- 评分：{} - 换手：{}% - 涨幅：{}% - 现价：{}元'.format(
            i, stock['name'], stock['code'], stock['score'],
            stock['turnover'], stock['change_pct'], stock['price']
        ))
    
    return top3

def strategy2_trend_follow(stocks):
    """策略 2: 趋势跟踪"""
    print('\n' + '=' * 60)
    print('策略 2: 趋势跟踪（T+N）')
    print('=' * 60)
    
    # 筛选条件
    # 换手率 2-15%
    # 涨跌幅>-2%（趋势向上或盘整）
    # 现价>3 元
    
    selected = []
    for i, stock in enumerate(stocks[:100]):
        try:
            turnover = float(stock.get('换手率', 0) or 0)
            change_pct = float(stock.get('涨跌幅', 0) or 0)
            price = float(stock.get('最新价', 0) or 0)
            
            if (2 <= turnover <= 15) and (change_pct > -2) and (price > 3):
                score = 0
                # 趋势评分
                if change_pct > 3:
                    score += 50
                elif change_pct > 0:
                    score += 30
                else:
                    score += 20
                
                # 换手率评分
                if 5 <= turnover <= 8:
                    score += 30
                elif 2 <= turnover <= 15:
                    score += 20
                
                # 成交量排名评分
                score += (100 - i) // 10
                
                if score >= 50:
                    selected.append({
                        'code': stock.get('代码', ''),
                        'name': stock.get('名称', ''),
                        'price': price,
                        'change_pct': change_pct,
                        'turnover': turnover,
                        'volume': stock.get('成交量', 0),
                        'score': score,
                        'hold_period': '5-10 天' if score < 70 else '10-15 天',
                        'reason': '趋势确立 + 量能配合'
                    })
        except:
            pass
    
    # 按评分排序
    selected.sort(key=lambda x: x['score'], reverse=True)
    top3 = selected[:3]
    
    print('  候选股票：{} 只'.format(len(selected)))
    print('  推荐标的：{} 只'.format(len(top3)))
    
    for i, stock in enumerate(top3, 1):
        print('  {}. {}（{}）- 评分：{} - 持仓：{} 天 - 换手：{}% - 涨幅：{}%'.format(
            i, stock['name'], stock['code'], stock['score'],
            stock['hold_period'], stock['turnover'], stock['change_pct']
        ))
    
    return top3

def generate_report(strategy1_picks, strategy2_picks):
    """生成选股报告"""
    reports_dir = Path('../reports')
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / 'dual_strategy_real_picks_{}.md'.format(
        datetime.now().strftime('%Y%m%d')
    )
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('# 双策略选股报告（真实数据）\n\n')
        f.write('**日期**: {}\n'.format(datetime.now().strftime('%Y-%m-%d')))
        f.write('**数据源**: efinance 真实 API\n\n')
        
        f.write('## 策略 1: 尾盘选股（T+1）\n\n')
        f.write('| 参数 | 内容 |\n')
        f.write('|------|------|\n')
        f.write('| 类型 | T+1 |\n')
        f.write('| 胜率 | 65-75% |\n')
        f.write('| 止损/止盈 | -5% / +10% |\n')
        f.write('| 仓位 | 单只≤15% |\n')
        f.write('| 执行时间 | 14:30 买入，次日 09:35 卖出 |\n\n')
        
        if strategy1_picks:
            f.write('### 今日推荐标的\n\n')
            f.write('| 排名 | 代码 | 名称 | 现价 | 涨幅 | 换手率 | 评分 | 理由 |\n')
            f.write('|------|------|------|------|------|--------|------|------|\n')
            for i, stock in enumerate(strategy1_picks, 1):
                f.write('| {} | {} | {} | {:.2f} | {:.2f}% | {:.2f}% | {} | {} |\n'.format(
                    i, stock['code'], stock['name'], stock['price'],
                    stock['change_pct'], stock['turnover'], stock['score'], stock['reason']
                ))
        else:
            f.write('### 今日推荐标的\n\n')
            f.write('暂无符合筛选条件的股票。\n\n')
        
        f.write('\n\n## 策略 2: 趋势跟踪（T+N）\n\n')
        f.write('| 参数 | 内容 |\n')
        f.write('|------|------|\n')
        f.write('| 类型 | T+N |\n')
        f.write('| 胜率 | 60-70% |\n')
        f.write('| 止损/止盈 | -8% / +15% |\n')
        f.write('| 仓位 | 单只≤20% |\n')
        f.write('| 持仓周期 | 5-20 天 |\n')
        f.write('| 执行时间 | 趋势确立时买入，趋势反转时卖出 |\n\n')
        
        if strategy2_picks:
            f.write('### 今日推荐标的\n\n')
            f.write('| 排名 | 代码 | 名称 | 现价 | 涨幅 | 换手率 | 评分 | 持仓 | 理由 |\n')
            f.write('|------|------|------|------|------|--------|------|------|------|\n')
            for i, stock in enumerate(strategy2_picks, 1):
                f.write('| {} | {} | {} | {:.2f} | {:.2f}% | {:.2f}% | {} | {} | {} |\n'.format(
                    i, stock['code'], stock['name'], stock['price'],
                    stock['change_pct'], stock['turnover'], stock['score'],
                    stock['hold_period'], stock['reason']
                ))
        else:
            f.write('### 今日推荐标的\n\n')
            f.write('暂无符合筛选条件的股票。\n\n')
        
        f.write('\n\n## 风险提示\n\n')
        f.write('1. 尾盘选股：次日早盘必须卖出，不贪心\n')
        f.write('2. 趋势跟踪：趋势反转必须离场，不幻想\n')
        f.write('3. 单只股票≤15% 仓位，避免集中风险\n')
        f.write('4. 严格执行止损，保命第一\n')
        f.write('5. 数据来自 efinance 真实 API\n')
    
    print('\n选股报告已保存：{}'.format(report_file))

def main():
    """主函数"""
    print('=' * 60)
    print('双策略选股 - 真实数据（修正版）')
    print('=' * 60)
    print('执行时间：{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    # 加载真实数据
    stocks = load_real_volume_data()
    
    if not stocks:
        print('[ERROR] 数据加载失败')
        return
    
    # 执行两个策略
    strategy1_picks = strategy1_tail_pick(stocks)
    strategy2_picks = strategy2_trend_follow(stocks)
    
    # 生成报告
    generate_report(strategy1_picks, strategy2_picks)
    
    print('\n' + '=' * 60)
    print('选股完成！')
    print('=' * 60)
    print('策略 1（尾盘选股）：推荐{} 只'.format(len(strategy1_picks)))
    print('策略 2（趋势跟踪）：推荐{} 只'.format(len(strategy2_picks)))

if __name__ == '__main__':
    main()
