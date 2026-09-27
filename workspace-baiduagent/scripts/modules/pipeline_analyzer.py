# -*- coding: utf-8 -*-
"""
Pipeline分析师 - 销售管道健康诊断
融合来源: agency-agents/sales/sales-pipeline-analyst.md
功能: Pipeline速度分析、覆盖率诊断、交易健康评分、预测模型
"""
import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')

# MEDDPICC评分框架
MEDDPICC_FIELDS = ['M- Metrics', 'E- Economic Buyer', 'D- Decision Criteria', 
                   'D- Decision Process', 'P- Paper Process', 'I- Implicated Pain',
                   'C- Champion', 'C- Competition']

def get_conn():
    return sqlite3.connect(DB_PATH)

def calculate_pipeline_velocity():
    """
    Pipeline速度分析
    Pipeline Velocity = (Qualified Opportunities × Average Deal Size × Win Rate) / Sales Cycle Length
    """
    conn = get_conn()
    c = conn.cursor()
    
    # 获取近期成交客户（用于计算转化率）
    c.execute('''
        SELECT COUNT(*) FROM call_logs 
        WHERE result IN ('有意向', '有效')
        AND call_date >= date('now', '-30 days')
    ''')
    opportunities_30d = c.fetchone()[0]
    
    # 获取平均客单价（基于历史通话记录估算）
    avg_deal_size = 5000  # 默认值
    
    # 计算转化率
    c.execute('SELECT COUNT(*) FROM call_logs WHERE call_date >= date(\'now\', \'-30 days\')')
    total_calls = c.fetchone()[0]
    win_rate = opportunities_30d / total_calls if total_calls > 0 else 0.15
    
    # 计算销售周期（天）- 基于通话记录估算
    c.execute('''
        SELECT AVG(julianday(last_call) - julianday(created_at))
        FROM customers 
        WHERE status = '已成交'
        AND last_call IS NOT NULL
    ''')
    result = c.fetchone()[0]
    sales_cycle = result if result else 30  # 默认30天
    
    # 计算Pipeline速度
    velocity = (opportunities_30d * avg_deal_size * win_rate) / 30 if sales_cycle > 0 else 0
    
    conn.close()
    
    return {
        'qualified_opportunities': opportunities_30d,
        'average_deal_size': avg_deal_size,
        'win_rate': win_rate,
        'sales_cycle_days': sales_cycle,
        'pipeline_velocity': velocity,
        'period': '30天'
    }

def analyze_pipeline_coverage():
    """
    Pipeline覆盖率分析
    Target coverage: 成熟业务3x，成长期4-5x
    """
    conn = get_conn()
    c = conn.cursor()
    
    # 当前Pipeline状态分布
    c.execute('''
        SELECT status, COUNT(*) 
        FROM customers 
        GROUP BY status
    ''')
    status_dist = dict(c.fetchall())
    
    # 计算有希望的商机（Tier A/B + 有意向状态）
    c.execute('''
        SELECT COUNT(*) FROM customers 
        WHERE tier IN ('A', 'B') 
        AND status IN ('有意向', '需跟进', '已报价', '已成交')
    ''')
    qualified_pipeline = c.fetchone()[0]
    
    # 计算目标收入（基于客户数量和平均客单价）
    monthly_target = qualified_pipeline * 3000  # 假设月目标3000元/客户
    
    # 覆盖率 = Pipeline价值 / 目标收入
    pipeline_value = qualified_pipeline * 5000  # 假设平均5000元
    coverage_ratio = pipeline_value / monthly_target if monthly_target > 0 else 0
    
    # 质量调整覆盖率（考虑状态）
    hot_leads = status_dist.get('有意向', 0)
    warm_leads = status_dist.get('需跟进', 0)
    cold_leads = status_dist.get('待联系', 0)
    
    quality_adjusted = (hot_leads * 1.0 + warm_leads * 0.5 + cold_leads * 0.1) / max(qualified_pipeline, 1)
    
    conn.close()
    
    return {
        'qualified_pipeline': qualified_pipeline,
        'monthly_target': monthly_target,
        'pipeline_value': pipeline_value,
        'coverage_ratio': coverage_ratio,
        'target_coverage': 4.0,  # 成长期目标
        'quality_adjusted': quality_adjusted,
        'status_distribution': status_dist
    }

def score_deal_health(customer_id):
    """
    交易健康评分（MEDDPICC框架）
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
        SELECT result, note, call_date, duration_sec 
        FROM call_logs 
        WHERE customer_id = ? 
        ORDER BY call_date DESC
        LIMIT 5
    ''', (customer_id,))
    calls = c.fetchall()
    
    # MEDDPICC评分（简化版）
    score = 0
    max_score = 8
    details = []
    
    # M - Metrics: 客户是否量化了价值
    if calls and any('预算' in str(c[2]) or '费用' in str(c[2]) for c in calls if c[2]):
        score += 1
        details.append('M-Metrics: 已量化价值')
    else:
        details.append('M-Metrics: ⚠️ 未量化价值')
    
    # E - Economic Buyer: 是否找到决策人
    if customer[5]:  # contact字段
        score += 1
        details.append('E-Economic Buyer: 已识别联系人')
    else:
        details.append('E-Economic Buyer: ⚠️ 未找到决策人')
    
    # D - Decision Criteria: 通话记录中的决策标准
    if calls and any('对比' in str(c[2]) or '标准' in str(c[2]) or '条件' in str(c[2]) for c in calls if c[2]):
        score += 1
        details.append('D-Decision Criteria: 已明确标准')
    else:
        details.append('D-Decision Criteria: ⚠️ 未明确决策标准')
    
    # D - Decision Process: 决策流程
    if calls and any('流程' in str(c[2]) or '审批' in str(c[2]) or '时间' in str(c[2]) for c in calls if c[2]):
        score += 1
        details.append('D-Decision Process: 已了解流程')
    else:
        details.append('D-Decision Process: ⚠️ 未了解决策流程')
    
    # P - Paper Process: 合同/法律流程
    if customer[7] and '合同' in str(customer[7]):
        score += 1
        details.append('P-Paper Process: 已启动合同流程')
    else:
        details.append('P-Paper Process: ⚠️ 未启动合同流程')
    
    # I - Implicated Pain: 痛点量化
    if calls and any('损失' in str(c[2]) or '影响' in str(c[2]) or '成本' in str(c[2]) for c in calls if c[2]):
        score += 1
        details.append('I-Implicated Pain: 痛点已量化')
    else:
        details.append('I-Implicated Pain: ⚠️ 痛点未量化')
    
    # C - Champion: 内部支持者
    if calls and any('支持' in str(c[2]) or '推荐' in str(c[2]) or '同意' in str(c[2]) for c in calls if c[2]):
        score += 1
        details.append('C-Champion: 有内部支持者')
    else:
        details.append('C-Champion: ⚠️ 未找到内部支持者')
    
    # C - Competition: 竞争情况
    if calls and any('竞品' in str(c[2]) or '竞争' in str(c[2]) or '对比' in str(c[2]) for c in calls if c[2]):
        score += 1
        details.append('C-Competition: 已了解竞争情况')
    else:
        details.append('C-Competition: ⚠️ 未了解竞争情况')
    
    conn.close()
    
    return {
        'customer_id': customer_id,
        'customer_name': customer[1],
        'meddpicc_score': score,
        'max_score': max_score,
        'health_level': '健康' if score >= 6 else ('需关注' if score >= 4 else '高风险'),
        'details': details,
        'recent_calls': len(calls)
    }

def generate_pipeline_health_report():
    """
    生成Pipeline健康报告
    """
    velocity = calculate_pipeline_velocity()
    coverage = analyze_pipeline_coverage()
    
    # 获取高风险交易
    conn = get_conn()
    c = conn.cursor()
    
    # 找出停滞超过14天的意向客户
    c.execute('''
        SELECT id, name, status, updated_at 
        FROM customers 
        WHERE status IN ('有意向', '需跟进', '已报价')
        AND updated_at < date('now', '-14 days')
        ORDER BY updated_at ASC
        LIMIT 10
    ''')
    stalled_deals = c.fetchall()
    
    # 计算本周/本月转化漏斗
    c.execute('''
        SELECT 
            SUM(CASE WHEN status = '待联系' THEN 1 ELSE 0 END) as new_leads,
            SUM(CASE WHEN status IN ('需跟进', '有意向') THEN 1 ELSE 0 END) as active_deals,
            SUM(CASE WHEN status = '已成交' THEN 1 ELSE 0 END) as closed_won,
            SUM(CASE WHEN result = '有意向' THEN 1 ELSE 0 END) as calls_interested
        FROM customers c
        LEFT JOIN call_logs cl ON c.id = cl.customer_id
        WHERE c.created_at >= date('now', '-30 days')
        OR cl.call_date >= date('now', '-30 days')
    ''')
    funnel = c.fetchone()
    
    conn.close()
    
    report = {
        'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'velocity_metrics': velocity,
        'coverage_analysis': coverage,
        'stalled_deals': [
            {'id': d[0], 'name': d[1], 'status': d[2], 'last_updated': d[3]}
            for d in stalled_deals
        ],
        'funnel_summary': {
            'new_leads_30d': funnel[0] or 0,
            'active_deals': funnel[1] or 0,
            'closed_won_30d': funnel[2] or 0,
            'interested_from_calls': funnel[3] or 0
        },
        'recommendations': []
    }
    
    # 生成建议
    if coverage['coverage_ratio'] < coverage['target_coverage']:
        report['recommendations'].append(
            f"⚠️ Pipeline覆盖率不足（当前{coverage['coverage_ratio']:.1f}x，目标{coverage['target_coverage']}x）"
        )
    if len(stalled_deals) > 0:
        report['recommendations'].append(
            f"🔴 发现{len(stalled_deals)}个停滞超过14天的交易，需立即介入"
        )
    if velocity['win_rate'] < 0.15:
        report['recommendations'].append(
            f"📉 转化率偏低（{velocity['win_rate']:.1%}），建议优化话术或客户筛选"
        )
    
    return report

def forecast_revenue(period_days=30):
    """
    收入预测（基于历史转化率）
    """
    conn = get_conn()
    c = conn.cursor()
    
    # 获取近期通话数据
    c.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN result IN ('有意向', '有效') THEN 1 ELSE 0 END) as interested
        FROM call_logs 
        WHERE call_date >= date('now', '-{:d} days')
    '''.format(period_days))
    recent = c.fetchone()
    
    # 当前Pipeline中的高概率交易
    c.execute('''
        SELECT COUNT(*) FROM customers 
        WHERE status IN ('有意向', '需跟进', '已报价')
        AND updated_at >= date('now', '-7 days')
    ''')
    hot_deals = c.fetchone()[0]
    
    conn.close()
    
    # 预测
    commit = hot_deals * 3000  # 假设平均3000元
    best_case = commit + (recent[1] or 0) * 1000  # 加意向客户转化
    upside = best_case + (recent[0] or 0) * 500  # 加历史转化率
    
    return {
        'commit': commit,
        'commit_confidence': '>90%',
        'best_case': best_case,
        'best_case_confidence': '>60%',
        'upside': upside,
        'upside_confidence': '<60%',
        'method': '历史转化率+Pipeline状态加权'
    }

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("Pipeline健康诊断报告")
    print("=" * 60)
    
    report = generate_pipeline_health_report()
    
    print(f"\n📅 报告日期: {report['report_date']}")
    
    print("\n【Pipeline速度指标】")
    v = report['velocity_metrics']
    print(f"  qualified opportunities (30天): {v['qualified_opportunities']}")
    print(f"  平均客单价: {v['average_deal_size']:.0f}元")
    print(f"  转化率: {v['win_rate']:.1%}")
    print(f"  销售周期: {v['sales_cycle_days']:.1f}天")
    print(f"  Pipeline速度: {v['pipeline_velocity']:.0f}元/天")
    
    print("\n【覆盖率分析】")
    cov = report['coverage_analysis']
    print(f"  合格Pipeline: {cov['qualified_pipeline']}家")
    print(f"  Pipeline价值: {cov['pipeline_value']:.0f}元")
    print(f"  当前覆盖率: {cov['coverage_ratio']:.1f}x (目标: {cov['target_coverage']}x)")
    print(f"  质量调整系数: {cov['quality_adjusted']:.2f}")
    
    print("\n【停滞交易预警】")
    if report['stalled_deals']:
        for deal in report['stalled_deals'][:5]:
            print(f"  🔴 #{deal['id']} {deal['name']} - 最后更新: {deal['last_updated']}")
    else:
        print("  ✅ 无停滞交易")
    
    print("\n【收入预测】")
    forecast = forecast_revenue()
    print(f"  Commit (>90%): {forecast['commit']:.0f}元")
    print(f"  Best Case (>60%): {forecast['best_case']:.0f}元")
    print(f"  Upside (<60%): {forecast['upside']:.0f}元")
    
    print("\n【建议】")
    for rec in report['recommendations']:
        print(f"  → {rec}")
    
    print("\n" + "=" * 60)
