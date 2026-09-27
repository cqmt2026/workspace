# -*- coding: utf-8 -*-
"""
ROI计算模块 - 借鉴Google lightweight_mmm理念
功能：
1. 简化版归因逻辑（首次点击+末次点击）
2. 渠道效果对比表生成
3. 预算优化建议
"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'

def calculate_roi(budget, cpc, click_rate, conversion_rate, avg_order_value):
    """
    计算ROI（投资回报率）
    
    参数：
    - budget: 月度预算（元）
    - cpc: 平均点击成本（元）
    - click_rate: 点击率（%）
    - conversion_rate: 转化率（%）
    - avg_order_value: 平均订单金额（元）
    
    返回：
    - roi: ROI百分比
    - leads: 线索数量
    - conversions: 成交数量
    - revenue: 营收
    """
    clicks = budget / cpc if cpc > 0 else 0
    leads = clicks * (click_rate / 100)
    conversions = leads * (conversion_rate / 100)
    revenue = conversions * avg_order_value
    roi = ((revenue - budget) / budget) * 100 if budget > 0 else 0
    
    return {
        'budget': budget,
        'cpc': cpc,
        'clicks': round(clicks, 0),
        'leads': round(leads, 1),
        'conversions': round(conversions, 2),
        'revenue': round(revenue, 2),
        'roi': round(roi, 1),
        'calc_date': datetime.now().strftime('%Y-%m-%d')
    }

def attribution_analysis(contacts, calls):
    """
    归因分析（简化版：首次接触+最终转化）
    
    参数：
    - contacts: 客户列表（含来源）
    - calls: 通话记录列表
    
    返回：
    - attribution: 各渠道贡献分析
    """
    # 统计各渠道线索数
    channel_leads = {}
    for c in contacts:
        source = c.get('source', '未知')
        channel_leads[source] = channel_leads.get(source, 0) + 1
    
    # 统计各渠道转化数（有电话+有跟进记录）
    channel_conversions = {}
    for call in calls:
        source = call.get('source', '未知')
        if call.get('result') in ['有意向', '已成交']:
            channel_conversions[source] = channel_conversions.get(source, 0) + 1
    
    # 计算转化率
    attribution = {}
    for channel in channel_leads:
        leads = channel_leads[channel]
        conversions = channel_conversions.get(channel, 0)
        conversion_rate = (conversions / leads * 100) if leads > 0 else 0
        
        attribution[channel] = {
            'leads': leads,
            'conversions': conversions,
            'conversion_rate': round(conversion_rate, 1),
            'attribution_type': '首次接触' if leads > conversions else '最终转化'
        }
    
    return attribution

def generate_channel_comparison(customers, call_logs):
    """
    生成渠道效果对比表
    
    参数：
    - customers: 客户列表
    - call_logs: 通话记录列表
    
    返回：
    - comparison: 渠道对比数据
    """
    # 按来源分组统计
    sources = {}
    
    # 统计客户数
    for c in customers:
        src = c.get('source', '未知')
        if src not in sources:
            sources[src] = {'customers': 0, 'calls': 0, 'converted': 0, 'total_budget': 0}
        sources[src]['customers'] += 1
    
    # 统计通话和转化
    for call in call_logs:
        # 需要从通话记录关联到客户来源
        # 这里简化处理
        pass
    
    # 计算关键指标
    comparison = {}
    for src, data in sources.items():
        # 假设平均预算3000元/客户
        avg_budget = 3000
        total_budget = data['customers'] * avg_budget
        
        comparison[src] = {
            'customer_count': data['customers'],
            'total_potential_budget': total_budget,
            'avg_budget_per_customer': avg_budget,
            'conversion_rate': '待补充',
            'recommendation': _get_recommendation(data['customers'])
        }
    
    return comparison

def _get_recommendation(customer_count):
    """根据客户数量给出建议"""
    if customer_count >= 100:
        return '重点投入'
    elif customer_count >= 50:
        return '持续关注'
    elif customer_count >= 20:
        return '适量投放'
    else:
        return '测试阶段'

def calculate_budget_optimization(current_budget, roi_history):
    """
    预算优化建议
    
    参数：
    - current_budget: 当前预算
    - roi_history: ROI历史数据列表
    
    返回：
    - optimization: 优化建议
    """
    if not roi_history:
        return {
            'current_budget': current_budget,
            'suggested_budget': current_budget,
            'expected_roi': '暂无数据',
            'recommendation': '先收集3个月投放数据'
        }
    
    # 计算平均ROI
    avg_roi = sum([r.get('roi', 0) for r in roi_history]) / len(roi_history)
    
    # 根据ROI给出建议
    if avg_roi > 200:
        suggested_budget = current_budget * 1.5
        recommendation = 'ROI优秀，建议增加50%预算'
    elif avg_roi > 100:
        suggested_budget = current_budget * 1.2
        recommendation = 'ROI良好，建议增加20%预算'
    elif avg_roi > 0:
        suggested_budget = current_budget
        recommendation = 'ROI正常，保持当前预算'
    else:
        suggested_budget = current_budget * 0.8
        recommendation = 'ROI为负，建议减少20%预算并优化策略'
    
    return {
        'current_budget': current_budget,
        'suggested_budget': round(suggested_budget, 0),
        'avg_roi': round(avg_roi, 1),
        'recommendation': recommendation
    }

def generate_proposal_template(industry, company_name, budget=5000):
    """
    生成提案模板（含ROI计算）
    
    参数：
    - industry: 行业
    - company_name: 公司名称
    - budget: 建议预算
    
    返回：
    - proposal: 提案数据
    """
    # 行业基准数据（需要持续更新）
    industry_benchmarks = {
        '机械制造': {'cpc': 8, 'click_rate': 3.5, 'conversion_rate': 2.5, 'avg_order': 50000},
        '医疗器械': {'cpc': 15, 'click_rate': 2.8, 'conversion_rate': 3.2, 'avg_order': 100000},
        '新材料': {'cpc': 6, 'click_rate': 4.0, 'conversion_rate': 2.0, 'avg_order': 30000},
        '本地生活': {'cpc': 5, 'click_rate': 5.0, 'conversion_rate': 4.0, 'avg_order': 5000},
    }
    
    # 获取行业基准或默认值
    benchmark = industry_benchmarks.get(industry, {
        'cpc': 8,
        'click_rate': 3.0,
        'conversion_rate': 2.5,
        'avg_order': 20000
    })
    
    # 计算ROI
    roi_data = calculate_roi(
        budget=budget,
        cpc=benchmark['cpc'],
        click_rate=benchmark['click_rate'],
        conversion_rate=benchmark['conversion_rate'],
        avg_order_value=benchmark['avg_order']
    )
    
    # 生成提案
    proposal = {
        'company': company_name,
        'industry': industry,
        'budget': budget,
        'roi_calculation': roi_data,
        'benchmark': benchmark,
        'recommendation': _get_strategy_recommendation(roi_data['roi']),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    return proposal

def _get_strategy_recommendation(roi):
    """根据ROI给出策略建议"""
    if roi >= 300:
        return '高效投放，建议加大预算'
    elif roi >= 200:
        return '表现良好，可适度增加预算'
    elif roi >= 100:
        return '收支平衡，建议优化关键词'
    elif roi >= 0:
        return '略有亏损，建议调整策略'
    else:
        return '亏损严重，建议重新评估投放必要性'

def export_roi_report(proposal, output_path=None):
    """导出ROI报告"""
    if output_path is None:
        output_path = f"data/roi_report_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(proposal, f, ensure_ascii=False, indent=2)
    
    return output_path

if __name__ == '__main__':
    # 测试示例
    print("="*60)
    print("【ROI计算模块测试】")
    print("="*60)
    
    # 测试1：ROI计算
    print("\n▶ 测试1：ROI计算")
    roi_result = calculate_roi(
        budget=5000,
        cpc=8,
        click_rate=3.5,
        conversion_rate=2.5,
        avg_order_value=50000
    )
    print(f"  预算: {roi_result['budget']}元")
    print(f"  点击: {roi_result['clicks']}次")
    print(f"  线索: {roi_result['leads']}个")
    print(f"  成交: {roi_result['conversions']}单")
    print(f"  营收: {roi_result['revenue']}元")
    print(f"  ROI: {roi_result['roi']}%")
    
    # 测试2：提案生成
    print("\n▶ 测试2：提案生成")
    proposal = generate_proposal_template(
        industry='机械制造',
        company_name='重庆XX机械公司',
        budget=5000
    )
    print(f"  公司: {proposal['company']}")
    print(f"  行业: {proposal['industry']}")
    print(f"  建议预算: {proposal['budget']}元/月")
    print(f"  预期ROI: {proposal['roi_calculation']['roi']}%")
    print(f"  策略建议: {proposal['recommendation']}")
    
    # 测试3：导出报告
    print("\n▶ 测试3：导出报告")
    report_path = export_roi_report(proposal)
    print(f"  报告已保存: {report_path}")
    
    print("\n" + "="*60)
    print("【测试完成】")
    print("="*60)
