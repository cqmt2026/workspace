# -*- coding: utf-8 -*-
"""
自动报表生成器 - 日报/周报/月报
融合来源: agency-agents/specialized/sales-data-extraction-agent.md
功能: 自动从CRM提取数据，生成标准化报表
"""
import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory', 'logs')

def get_conn():
    return sqlite3.connect(DB_PATH)

def generate_daily_report(today=None):
    """
    生成日报
    """
    if not today:
        today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    
    conn = get_conn()
    c = conn.cursor()
    
    # 昨日拨打数据
    c.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN result = '有效' THEN 1 ELSE 0 END) as valid_calls,
            SUM(CASE WHEN result = '有意向' THEN 1 ELSE 0 END) as interested,
            SUM(CASE WHEN result = '关机' THEN 1 ELSE 0 END) as off,
            SUM(CASE WHEN result = '拒接' THEN 1 ELSE 0 END) as rejected,
            AVG(duration_sec) as avg_duration
        FROM call_logs 
        WHERE call_date = ?
    ''', (yesterday,))
    call_stats = c.fetchone()
    
    # 今日拨打数据（进行中）
    c.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN result = '有效' THEN 1 ELSE 0 END) as valid_calls,
            SUM(CASE WHEN result = '有意向' THEN 1 ELSE 0 END) as interested
        FROM call_logs 
        WHERE call_date = ?
    ''', (today_str,))
    today_stats = c.fetchone()
    
    # 客户状态分布
    c.execute('SELECT status, COUNT(*) FROM customers GROUP BY status')
    status_dist = dict(c.fetchall())
    
    # 行业分布（Top 5）
    c.execute('''
        SELECT industry, COUNT(*) as cnt 
        FROM customers 
        GROUP BY industry 
        ORDER BY cnt DESC 
        LIMIT 5
    ''')
    top_industries = c.fetchall()
    
    # 新增客户（今日）
    c.execute('''
        SELECT COUNT(*) FROM customers 
        WHERE created_at >= ?
    ''', (today_str + ' 00:00:00',))
    new_customers = c.fetchone()[0]
    
    conn.close()
    
    # 生成报告
    report = f"""# 📊 百都销售日报 - {today_str}

## 一、昨日拨打数据（{yesterday}）

| 指标 | 数量 |
|------|------|
| 拨打总数 | {call_stats[0] or 0} |
| 有效通话 | {call_stats[1] or 0} |
| 有意向 | {call_stats[2] or 0} |
| 关机/拒接 | {(call_stats[3] or 0) + (call_stats[4] or 0)} |
| 平均通话时长 | {call_stats[5] or 0:.0f}秒 |

## 二、今日进展（{today_str}）

| 指标 | 数量 |
|------|------|
| 已拨打 | {today_stats[0] or 0} |
| 有效通话 | {today_stats[1] or 0} |
| 有意向 | {today_stats[2] or 0} |

## 三、客户池状态

| 状态 | 数量 |
|------|------|
"""
    for status, count in status_dist.items():
        report += f"| {status} | {count} |\n"
    
    report += f"""
## 四、行业分布（Top 5）

| 行业 | 客户数 |
|------|--------|
"""
    for ind, cnt in top_industries:
        report += f"| {ind} | {cnt} |\n"
    
    report += f"""
## 五、新增客户

今日新增：**{new_customers}** 家

## 六、关键指标

- 总客户数：{sum(status_dist.values())} 家
- 待联系：{status_dist.get('待联系', 0)} 家
- 有意向：{status_dist.get('有意向', 0)} 家
- 已成交：{status_dist.get('已成交', 0)} 家

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 保存报告
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, f'daily_{today_str}.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 日报已生成: {report_path}")
    return report

def generate_weekly_report(week_start=None):
    """
    生成周报
    """
    if not week_start:
        week_start = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    conn = get_conn()
    c = conn.cursor()
    
    # 本周数据
    c.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN result = '有效' THEN 1 ELSE 0 END) as valid_calls,
            SUM(CASE WHEN result = '有意向' THEN 1 ELSE 0 END) as interested,
            SUM(CASE WHEN result = '已成交' THEN 1 ELSE 0 END) as closed,
            AVG(duration_sec) as avg_duration
        FROM call_logs 
        WHERE call_date >= ?
    ''', (week_start,))
    week_stats = c.fetchone()
    
    # 按天统计
    c.execute('''
        SELECT call_date, COUNT(*) as cnt
        FROM call_logs 
        WHERE call_date >= ?
        GROUP BY call_date
        ORDER BY call_date
    ''', (week_start,))
    daily_calls = c.fetchall()
    
    # 行业转化对比
    c.execute('''
        SELECT c.industry, 
               COUNT(DISTINCT c.id) as total,
               SUM(CASE WHEN cl.result = '有意向' THEN 1 ELSE 0 END) as interested
        FROM customers c
        LEFT JOIN call_logs cl ON c.id = cl.customer_id
        WHERE c.created_at >= ? OR cl.call_date >= ?
        GROUP BY c.industry
        ORDER BY interested DESC
        LIMIT 10
    ''', (week_start, week_start))
    industry_stats = c.fetchall()
    
    conn.close()
    
    # 生成报告
    report = f"""# 📊 百都销售周报 - {week_start}至今

## 一、本周核心数据

| 指标 | 数值 |
|------|------|
| 总拨打数 | {week_stats[0] or 0} |
| 有效通话 | {week_stats[1] or 0} |
| 有意向 | {week_stats[2] or 0} |
| 成交数 | {week_stats[3] or 0} |
| 平均通话时长 | {week_stats[4] or 0:.0f}秒 |
| 接通率 | {(week_stats[1] or 0) / max(week_stats[0] or 1, 1) * 100:.1f}% |
| 意向率 | {(week_stats[2] or 0) / max(week_stats[1] or 1, 1) * 100:.1f}% |

## 二、每日拨打趋势

| 日期 | 拨打数 |
|------|--------|
"""
    for day, cnt in daily_calls:
        report += f"| {day} | {cnt} |\n"
    
    report += f"""
## 三、行业转化对比（Top 10）

| 行业 | 总客户 | 有意向 | 转化率 |
|------|--------|--------|--------|
"""
    for ind, total, interested in industry_stats:
        rate = interested / max(total, 1) * 100
        report += f"| {ind} | {total} | {interested} | {rate:.1f}% |\n"
    
    report += f"""
## 四、关键洞察

1. **拨打量分析**：本周共拨打{week_stats[0] or 0}通，{'达标' if (week_stats[0] or 0) >= 50 else '未达标'}（目标50通）
2. **意向质量**：{week_stats[2] or 0}个有意向客户，{'质量较好' if (week_stats[2] or 0) >= 5 else '需提升'}
3. **行业表现**：{'/'.join([ind for ind, _, _ in industry_stats[:3]])}行业意向最多

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, f'weekly_{week_start}.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 周报已生成: {report_path}")
    return report

def generate_monthly_report(month=None):
    """
    生成月报
    """
    if not month:
        month = date.today().strftime('%Y-%m')
    
    conn = get_conn()
    c = conn.cursor()
    
    # 本月数据
    c.execute('''
        SELECT 
            COUNT(DISTINCT customer_id) as callers,
            COUNT(*) as total_calls,
            SUM(CASE WHEN result = '有效' THEN 1 ELSE 0 END) as valid,
            SUM(CASE WHEN result = '有意向' THEN 1 ELSE 0 END) as interested,
            SUM(CASE WHEN result = '已成交' THEN 1 ELSE 0 END) as closed,
            SUM(duration_sec) as total_duration
        FROM call_logs 
        WHERE call_date LIKE ?
    ''', (month + '%',))
    month_stats = c.fetchone()
    
    # 客户增长
    c.execute('''
        SELECT COUNT(*) FROM customers 
        WHERE created_at LIKE ?
    ''', (month + '%',))
    new_customers = c.fetchone()[0]
    
    # 状态变化
    c.execute('''
        SELECT 
            SUM(CASE WHEN status = '已成交' THEN 1 ELSE 0 END) as won,
            SUM(CASE WHEN status = '放弃' THEN 1 ELSE 0 END) as lost,
            SUM(CASE WHEN status IN ('有意向', '需跟进') THEN 1 ELSE 0 END) as active
        FROM customers 
        WHERE updated_at LIKE ?
    ''', (month + '%',))
    status_change = c.fetchone()
    
    conn.close()
    
    # 生成报告
    report = f"""# 📊 百都销售月报 - {month}

## 一、月度核心指标

| 指标 | 数值 | 目标 | 达成率 |
|------|------|------|--------|
| 总拨打数 | {month_stats[1] or 0} | 150 | {(month_stats[1] or 0)/150*100:.1f}% |
| 有效通话 | {month_stats[2] or 0} | 50 | {(month_stats[2] or 0)/50*100:.1f}% |
| 意向客户 | {month_stats[3] or 0} | 15 | {(month_stats[3] or 0)/15*100:.1f}% |
| 成交客户 | {month_stats[4] or 0} | 3 | {(month_stats[4] or 0)/3*100:.1f}% |
| 新增客户 | {new_customers} | - | - |

## 二、转化漏斗

```
拨打 {month_stats[1] or 0} → 有效 {month_stats[2] or 0} → 意向 {month_stats[3] or 0} → 成交 {month_stats[4] or 0}
接通率: {(month_stats[2] or 0)/max(month_stats[1] or 1, 1)*100:.1f}%    意向率: {(month_stats[3] or 0)/max(month_stats[2] or 1, 1)*100:.1f}%    成交率: {(month_stats[4] or 0)/max(month_stats[3] or 1, 1)*100:.1f}%
```

## 三、客户状态变化

| 变化类型 | 数量 |
|----------|------|
| 新增成交 | {status_change[0] or 0} |
| 流失放弃 | {status_change[1] or 0} |
| 活跃跟进 | {status_change[2] or 0} |

## 四、关键洞察

1. **拨打效率**：日均拨打{(month_stats[1] or 0)/30:.1f}通
2. **转化质量**：意向率{(month_stats[3] or 0)/max(month_stats[2] or 1, 1)*100:.1f}%，{'高于预期' if (month_stats[3] or 0)/max(month_stats[2] or 1, 1) > 0.3 else '需提升'}
3. **成交转化**：成交率{(month_stats[4] or 0)/max(month_stats[3] or 1, 1)*100:.1f}%

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, f'monthly_{month}.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 月报已生成: {report_path}")
    return report

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("自动生成报表")
    print("=" * 60)
    
    # 生成日报
    generate_daily_report()
    
    # 生成周报
    generate_weekly_report()
    
    # 生成月报
    generate_monthly_report()
    
    print("\n✅ 所有报表生成完成")
