# -*- coding: utf-8 -*-
"""
CRM客户管理脚本 - 增删改查
创建: 2026-08-26 | 作者: 小度
"""
import sqlite3
import os
import sys
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def add_customer(name, industry, tier='A', phone='', contact='', source='手动添加'):
    """新增客户"""
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO customers (name, industry, tier, phone, contact, source, status, created_at, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, '待联系', ?, ?)''',
              (name, industry, tier, phone, contact, source, now, now))
    conn.commit()
    conn.close()
    print(f"✅ 新增客户: {name} ({industry}) [{tier}]")
    return c.lastrowid

def list_customers(tier=None, status=None, limit=50):
    """查询客户列表"""
    conn = get_conn()
    c = conn.cursor()
    sql = "SELECT id, name, industry, tier, phone, status, last_call FROM customers WHERE 1=1"
    params = []
    if tier:
        sql += " AND tier = ?"
        params.append(tier)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return rows

def update_status(customer_id, status, note=''):
    """更新客户状态"""
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE customers SET status=?, note=?, updated_at=? WHERE id=?",
              (status, note, now, customer_id))
    conn.commit()
    conn.close()
    print(f"✅ 客户 #{customer_id} 状态更新为: {status}")

def add_call_log(customer_id, result, duration_sec=0, next_action='', note='', script_version='v3'):
    """添加通话记录"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO call_logs (customer_id, result, duration_sec, next_action, script_version, note)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (customer_id, result, duration_sec, next_action, script_version, note))
    log_id = c.lastrowid
    conn.commit()
    conn.close()
    print(f"✅ 通话记录 #{log_id} 已保存")
    return log_id

def generate_today_list(top_n=10):
    """生成今日拨打清单"""
    conn = get_conn()
    c = conn.cursor()
    today = date.today().strftime('%Y-%m-%d')
    # 优先打Tier A，未联系或需跟进的
    c.execute('''SELECT id, name, industry, tier, phone 
                 FROM customers 
                 WHERE status IN ('待联系', '需跟进') 
                 ORDER BY 
                   CASE tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                   id DESC
                 LIMIT ?''', (top_n,))
    rows = c.fetchall()
    conn.close()
    
    print(f"\n[今日拨打清单] ({today}) - Top {top_n}:")
    print("-" * 60)
    for i, row in enumerate(rows, 1):
        cid, name, industry, tier, phone = row
        print(f"{i}. [{tier}] {name} | {industry} | 电话: {phone or '待验证'}")
    print("-" * 60)
    return rows

def generate_daily_report(today=None):
    """生成日报"""
    if not today:
        today = date.today().strftime('%Y-%m-%d')
    
    conn = get_conn()
    c = conn.cursor()
    
    # 统计数据
    c.execute("SELECT COUNT(*) FROM customers")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM customers WHERE status='待联系'")
    pending = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM customers WHERE status='已联系'")
    contacted = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM customers WHERE status='有意向'")
    interested = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM customers WHERE status='已成交'")
    deal = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM customers WHERE status='放弃'")
    given_up = c.fetchone()[0]
    
    # 今日通话
    c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=?", (today,))
    calls_today = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='有效'", (today,))
    valid_today = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='有意向'", (today,))
    interested_today = c.fetchone()[0]
    
    conn.close()
    
    report = f"""
=== 百都销售日报 {today} ===
[客户总量] {total}
   [待联系] {pending}
   [已联系] {contacted}
   [有意向] {interested}
   [已成交] {deal}
   [放弃] {given_up}

[今日拨打] {calls_today} 通
   [有效] {valid_today}
   [有意向] {interested_today}

[接通率] {valid_today/max(calls_today,1)*100:.0f}%
[转化率] {interested_today/max(calls_today,1)*100:.0f}%
============================
"""
    return report

def save_daily_report(report_text, filepath=None):
    """保存日报到日志"""
    if not filepath:
        today = date.today().strftime('%Y-%m-%d')
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'memory', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        filepath = os.path.join(log_dir, f'daily_{today}.md')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"✅ 日报已保存: {filepath}")

if __name__ == '__main__':
    print("百都CRM - 命令行工具")
    print("用法: python crm.py <命令> [参数]")
    print("命令: add/list/status/update/list_today/report")