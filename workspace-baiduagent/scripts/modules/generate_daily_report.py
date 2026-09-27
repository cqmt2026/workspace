# -*- coding: utf-8 -*-
"""
百都日报生成脚本
读取CRM数据库，统计今日/昨日数据，生成日报
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'logs')

def get_tables():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [r[0] for r in cur.fetchall()]

def get_db_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    tables = get_tables()
    schema = {}
    for t in tables:
        cur.execute(f"PRAGMA table_info([{t}])")
        schema[t] = [r[1] for r in cur.fetchall()]
    return schema, tables

def count_calls_by_date(table_name, date_str, schema):
    """统计某日拨打记录"""
    if table_name not in schema or 'call_count' not in schema[table_name]:
        return 0, 0, 0, 0, 0  # 拨打数, 接通数, 有效率, 意向数, 成交数
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 检查是否有按日期统计的字段
    date_field = 'date' if 'date' in schema[table_name] else None
    
    if not date_field:
        # 尝试其他可能的日期字段
        for f in schema[table_name]:
            if 'date' in f.lower() or 'time' in f.lower() or 'day' in f.lower():
                date_field = f
                break
    
    if not date_field:
        # 没有日期字段，返回0
        return 0, 0, 0, 0, 0
    
    # 构建查询
    try:
        # 先查总拨打数
        cur.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{date_field}] = ?", (date_str,))
        total_calls = cur.fetchone()[0]
        
        # 尝试统计接通数（可能有status字段）
        if 'status' in schema[table_name]:
            cur.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{date_field}] = ? AND status IN ('answered', 'connected', '已接通')", (date_str,))
            answered = cur.fetchone()[0]
        else:
            answered = 0
        
        # 尝试统计意向数
        if 'intent' in schema[table_name]:
            cur.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{date_field}] = ? AND intent = 1", (date_str,))
            intents = cur.fetchone()[0]
        elif 'interest' in schema[table_name]:
            cur.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{date_field}] = ? AND interest_level > 0", (date_str,))
            intents = cur.fetchone()[0]
        else:
            intents = 0
        
        # 尝试统计成交数
        if 'dealed' in schema[table_name]:
            cur.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{date_field}] = ? AND dealed = 1", (date_str,))
            deals = cur.fetchone()[0]
        elif 'closed' in schema[table_name]:
            cur.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{date_field}] = ? AND closed = 1", (date_str,))
            deals = cur.fetchone()[0]
        else:
            deals = 0
        
        # 计算有效率
        effective_rate = (answered / total_calls * 100) if total_calls > 0 else 0
        
        return total_calls, answered, effective_rate, intents, deals
        
    except Exception as e:
        print(f"Error counting calls: {e}")
        return 0, 0, 0, 0, 0

def generate_daily_report():
    """生成今日日报"""
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    schema, tables = get_db_schema()
    print(f"=== 数据库表结构 ===")
    for t in tables:
        print(f"  {t}: {schema[t]}")
    
    # 查找通话记录表
    call_table = None
    for t in tables:
        if 'call' in t.lower() or 'log' in t.lower() or 'record' in t.lower():
            call_table = t
            break
    
    if not call_table:
        # 如果没有明确的通话表，尝试所有表
        call_table = tables[0] if tables else None
    
    print(f"\n=== 使用表: {call_table} ===")
    
    if call_table and call_table in schema:
        today_data = count_calls_by_date(call_table, today, schema)
        yesterday_data = count_calls_by_date(call_table, yesterday, schema)
    else:
        today_data = (0, 0, 0, 0, 0)
        yesterday_data = (0, 0, 0, 0, 0)
    
    today_calls, today_answered, today_rate, today_intents, today_deals = today_data
    yest_calls, yest_answered, yest_rate, yest_intents, yest_deals = yesterday_data
    
    # 计算变化
    calls_change = today_calls - yest_calls
    answered_change = today_answered - yest_answered
    rate_change = today_rate - yest_rate
    intents_change = today_intents - yest_intents
    deals_change = today_deals - yest_deals
    
    report = f"""# 百都销售日报 - {today.replace('-', '')}

## 一、今日数据概览

| 指标 | 今日 | 昨日 | 变化 |
|------|------|------|------|
| 拨打数 | {today_calls} | {yest_calls} | {'▲' if calls_change > 0 else '▼' if calls_change < 0 else '—'}{abs(calls_change)} |
| 接通数 | {today_answered} | {yest_answered} | {'▲' if answered_change > 0 else '▼' if answered_change < 0 else '—'}{abs(answered_change)} |
| 有效率 | {today_rate:.1f}% | {yest_rate:.1f}% | {'▲' if rate_change > 0 else '▼' if rate_change < 0 else '—'}{abs(rate_change):.1f}% |
| 意向数 | {today_intents} | {yest_intents} | {'▲' if intents_change > 0 else '▼' if intents_change < 0 else '—'}{abs(intents_change)} |
| 成交数 | {today_deals} | {yest_deals} | {'▲' if deals_change > 0 else '▼' if deals_change < 0 else '—'}{abs(deals_change)} |

## 二、数据对比分析

### 拨打量
{'提升' if calls_change > 0 else '下降' if calls_change < 0 else '持平'}{abs(calls_change)}通，{'高于' if calls_change > 0 else '低于' if calls_change < 0 else '等于'}昨日

### 接通率
{'提升' if rate_change > 0 else '下降' if rate_change < 0 else '持平'}{abs(rate_change):.1f}个百分点，{'优于' if rate_change > 0 else '劣于' if rate_change < 0 else '持平'}昨日

### 意向转化
{'增加' if intents_change > 0 else '减少' if intents_change < 0 else '持平'}{abs(intents_change)}个意向客户

### 成交情况
{'新增' if deals_change > 0 else '无' if deals_change == 0 else '减少'}{abs(deals_change)}单成交

## 三、备注

- 数据截止: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 数据来源: baidu_crm.db ({call_table})

---
_小度自动生成_
"""
    
    # 保存日报
    os.makedirs(LOGS_DIR, exist_ok=True)
    report_path = os.path.join(LOGS_DIR, f"daily_{today.replace('-', '')}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n=== 日报已生成: {report_path} ===")
    print(report)
    
    return report, report_path

if __name__ == '__main__':
    generate_daily_report()
