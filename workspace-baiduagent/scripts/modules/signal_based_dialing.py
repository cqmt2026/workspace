# -*- coding: utf-8 -*-
"""
信号驱动外呼策略
融合来源: agency-agents/sales/sales-outbound-strategist.md
功能: 基于购买信号的外呼策略、ICP定义、账户分层
"""
import sqlite3
import os
from datetime import datetime, date
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')

# 购买信号定义
BUYING_SIGNALS = {
    'tier1_active': {
        'name': '主动购买信号',
        'indicators': ['actively_searching', 'comparing_prices', 'requesting_quotes'],
        'weight': 1.0,
        'action': '24小时内联系'
    },
    'tier2_organizational': {
        'name': '组织变化信号',
        'indicators': ['new_management', 'funding_round', 'hiring_surge', 'ma_activity'],
        'weight': 0.7,
        'action': '72小时内联系'
    },
    'tier3_technographic': {
        'name': '技术行为信号',
        'indicators': ['website_visit', 'content_download', 'webinar_attend'],
        'weight': 0.5,
        'action': '7天内联系'
    }
}

def analyze_buying_signals(customer_id):
    """
    分析客户购买信号
    """
    conn = get_conn()
    c = conn.cursor()
    
    # 获取客户信息
    c.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
    customer = c.fetchone()
    if not customer:
        conn.close()
        return None
    
    # 获取通话记录
    c.execute('''
        SELECT result, note, call_date FROM call_logs 
        WHERE customer_id = ? ORDER BY call_date DESC LIMIT 5
    ''', (customer_id,))
    calls = c.fetchall()
    
    # 分析信号
    signals = []
    signal_score = 0
    
    # Tier 1: 主动购买信号
    for call in calls:
        note = str(call[1]) if call[1] else ''
        if '预算' in note or '报价' in note or '合同' in note:
            signals.append({'type': 'tier1', 'indicator': '预算确认', 'score': 1.0})
            signal_score += 1.0
        if '尽快' in note or '马上' in note or '本周' in note:
            signals.append({'type': 'tier1', 'indicator': '时间紧迫', 'score': 0.8})
            signal_score += 0.8
    
    # Tier 2: 组织变化（从行业推断）
    industry = customer[2]  # industry字段
    if '专精特新' in industry or '创新型' in industry:
        signals.append({'type': 'tier2', 'indicator': '政策风口', 'score': 0.5})
        signal_score += 0.5
    
    # Tier 3: 行为信号
    if customer[6] == '有意向':  # status字段
        signals.append({'type': 'tier3', 'indicator': '已表达意向', 'score': 0.6})
        signal_score += 0.6
    
    conn.close()
    
    return {
        'customer_id': customer_id,
        'customer_name': customer[1],
        'industry': customer[2],
        'tier': customer[3],
        'signal_score': signal_score,
        'signals': signals,
        'priority': 'high' if signal_score >= 1.5 else ('medium' if signal_score >= 0.8 else 'low'),
        'recommended_action': get_action_by_signal(signal_score)
    }

def get_action_by_signal(score):
    """
    根据信号分数给出行动建议
    """
    if score >= 1.5:
        return '立即联系（24小时内）- 高购买意向'
    elif score >= 0.8:
        return '优先联系（72小时内）- 中等购买意向'
    elif score >= 0.3:
        return '计划联系（1周内）- 潜在机会'
    else:
        return '纳入培育池 - 低购买信号'

def generate_signal_based_list(top_n=20):
    """
    生成信号驱动的外呼清单
    """
    conn = get_conn()
    c = conn.cursor()
    
    # 获取所有客户
    c.execute('SELECT id, name, industry, tier, status FROM customers ORDER BY id DESC')
    customers = c.fetchall()
    
    # 分析每个客户的信号
    results = []
    for customer in customers:
        signal_data = analyze_buying_signals(customer[0])
        if signal_data:
            results.append(signal_data)
    
    # 按信号分数排序
    results.sort(key=lambda x: x['signal_score'], reverse=True)
    
    # 取前N个
    top_signals = results[:top_n]
    
    conn.close()
    
    return top_signals

def get_conn():
    return sqlite3.connect(DB_PATH)

def print_signal_report():
    """
    打印信号分析报告
    """
    print("=" * 70)
    print("🎯 信号驱动外呼策略报告")
    print("=" * 70)
    
    top_signals = generate_signal_based_list(20)
    
    if not top_signals:
        print("\n⚠️ 暂无客户数据，请先导入客户信息")
        print("提示: 运行 import_targets.py 导入目标客户")
        return []
    
    top_signals = generate_signal_based_list(20)
    
    # 按优先级分组
    high_priority = [s for s in top_signals if s['priority'] == 'high']
    medium_priority = [s for s in top_signals if s['priority'] == 'medium']
    low_priority = [s for s in top_signals if s['priority'] == 'low']
    
    print(f"\n📊 分析结果（共分析{len(top_signals)}个客户）")
    print(f"  🔴 高优先级: {len(high_priority)}个 - 立即联系")
    print(f"  🟡 中优先级: {len(medium_priority)}个 - 优先联系")
    print(f"  🟢 低优先级: {len(low_priority)}个 - 纳入培育")
    
    print("\n" + "=" * 70)
    print("🔴 高优先级客户（立即联系）")
    print("=" * 70)
    for i, s in enumerate(high_priority[:10], 1):
        print(f"{i}. [{s['tier']}] {s['customer_name']} ({s['industry']})")
        print(f"   信号分: {s['signal_score']:.1f} | 行动: {s['recommended_action']}")
        if s['signals']:
            print(f"   信号: {', '.join([sig['indicator'] for sig in s['signals'][:3]])}")
        print()
    
    print("=" * 70)
    print("🟡 中优先级客户（优先联系）")
    print("=" * 70)
    for i, s in enumerate(medium_priority[:5], 1):
        print(f"{i}. [{s['tier']}] {s['customer_name']} - 信号分: {s['signal_score']:.1f}")
    
    return top_signals

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print_signal_report()
