#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成日报 - 读取CRM数据库，统计今日销售数据"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '.')

TODAY = '2026-09-01'
YESTERDAY = '2026-08-31'
DB_PATH = 'data/baidu_crm.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 总览
    cur.execute('SELECT COUNT(*) as total FROM customers')
    total = cur.fetchone()['total']

    cur.execute("SELECT status, COUNT(*) as cnt FROM customers GROUP BY status ORDER BY cnt DESC")
    status_rows = cur.fetchall()
    status_dict = {r['status']: r['cnt'] for r in status_rows}

    # 有电话数
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    with_phone = cur.fetchone()[0]

    # 今日通话统计
    cur.execute("""SELECT 
        COUNT(*) as total_calls,
        SUM(CASE WHEN is_connected=1 THEN 1 ELSE 0 END) as connected,
        SUM(CASE WHEN quality='有效' THEN 1 ELSE 0 END) as valid,
        SUM(CASE WHEN is_intent=1 THEN 1 ELSE 0 END) as intent,
        SUM(CASE WHEN deal_status='已成交' THEN 1 ELSE 0 END) as closed
        FROM call_logs WHERE call_date = ?""", (TODAY,))
    stats = cur.fetchone()

    # 昨日通话统计
    cur.execute("""SELECT 
        COUNT(*) as total_calls,
        SUM(CASE WHEN is_connected=1 THEN 1 ELSE 0 END) as connected,
        SUM(CASE WHEN quality='有效' THEN 1 ELSE 0 END) as valid,
        SUM(CASE WHEN is_intent=1 THEN 1 ELSE 0 END) as intent
        FROM call_logs WHERE call_date = ?""", (YESTERDAY,))
    y_stats = cur.fetchone()

    # 今日通话明细
    cur.execute("""SELECT customer_id, phone, duration, outcome, quality, is_intent, deal_status, remark
        FROM call_logs WHERE call_date = ? ORDER BY created_at""", (TODAY,))
    detail_rows = cur.fetchall()

    # 写入结构化数据供主程序读取
    report_data = {
        'total': total,
        'with_phone': with_phone,
        'status_dict': status_dict,
        'calls_today': stats['total_calls'] or 0,
        'connected_today': stats['connected'] or 0,
        'valid_today': stats['valid'] or 0,
        'intent_today': stats['intent'] or 0,
        'closed_today': stats['closed'] or 0,
        'calls_yesterday': y_stats['total_calls'] or 0,
        'connected_yesterday': y_stats['connected'] or 0,
        'valid_yesterday': y_stats['valid'] or 0,
        'intent_yesterday': y_stats['intent'] or 0,
        'details': []
    }
    for r in detail_rows:
        report_data['details'].append({
            'customer_id': r['customer_id'],
            'phone': r['phone'],
            'duration': r['duration'],
            'outcome': r['outcome'],
            'quality': r['quality'],
            'is_intent': r['is_intent'],
            'deal_status': r['deal_status'],
            'remark': r['remark']
        })

    # 输出JSON
    print(json.dumps(report_data, ensure_ascii=False, indent=2))
    
    conn.close()

if __name__ == '__main__':
    main()
