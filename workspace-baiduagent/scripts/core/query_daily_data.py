#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询日报数据 - 兼容Windows PowerShell"""
import sqlite3
import sys
import json
from datetime import date, timedelta

DB_PATH = r"C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db"

def main():
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 通话记录总数
    cur.execute("SELECT COUNT(*) FROM call_logs")
    total_calls = cur.fetchone()[0]
    
    # 今日通话（call_date字段）
    cur.execute("SELECT COUNT(*) FROM call_logs WHERE date(call_date) = ?", (today_str,))
    today_calls = cur.fetchone()[0]
    
    # 昨日通话
    cur.execute("SELECT COUNT(*) FROM call_logs WHERE date(call_date) = ?", (yesterday_str,))
    yesterday_calls = cur.fetchone()[0]
    
    # 客户总数
    cur.execute("SELECT COUNT(*) FROM customers")
    total_cust = cur.fetchone()[0]
    
    # 各状态客户
    cur.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
    status_data = cur.fetchall()
    
    # Tier分布
    cur.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier")
    tier_data = cur.fetchall()
    
    # 行业Top10
    cur.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC LIMIT 10")
    top_industries = cur.fetchall()
    
    # 按日期汇总最近7天通话数据
    cur.execute("""
        SELECT date(call_date) as d, 
               COUNT(*) as total,
               SUM(CASE WHEN result='接通' THEN 1 ELSE 0 END) as connected,
               SUM(CASE WHEN result='有意向' THEN 1 ELSE 0 END) as interested,
               SUM(CASE WHEN result='成交' THEN 1 ELSE 0 END) as closed
        FROM call_logs
        GROUP BY d ORDER BY d DESC LIMIT 7
    """)
    recent_days = cur.fetchall()
    
    # 最近通话记录（使用name字段）
    cur.execute("""
        SELECT c.name, c.industry, c.phone, cl.call_date, cl.result, cl.note
        FROM call_logs cl
        JOIN customers c ON cl.customer_id = c.id
        ORDER BY cl.call_date DESC LIMIT 20
    """)
    recent_calls = cur.fetchall()
    
    conn.close()
    
    # 输出JSON格式
    result = {
        "today": today_str,
        "yesterday": yesterday_str,
        "total_calls": total_calls,
        "today_calls": today_calls,
        "yesterday_calls": yesterday_calls,
        "total_cust": total_cust,
        "status_data": [{"status": s, "count": c} for s, c in status_data],
        "tier_data": [{"tier": t, "count": c} for t, c in tier_data],
        "top_industries": [{"industry": i, "count": c} for i, c in top_industries],
        "recent_days": [{"date": d, "total": t, "connected": co, "interested": int(i), "closed": cl} for d, t, co, i, cl in recent_days],
        "recent_calls": [{"company": r[0], "industry": r[1], "phone": r[2], "time": r[3], "result": r[4], "notes": r[5]} for r in recent_calls]
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
