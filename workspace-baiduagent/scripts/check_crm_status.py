# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all customers with their call status
cursor.execute('''
    SELECT c.id, c.name, c.industry, c.phone, c.tier, 
           MAX(cl.call_date) as last_call, cl.result as last_result
    FROM customers c
    LEFT JOIN call_logs cl ON c.id = cl.customer_id
    GROUP BY c.id
    ORDER BY 
        CASE c.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 END,
        c.industry,
        last_call DESC NULLS LAST
''')
all_customers = cursor.fetchall()
print(f'Total customers: {len(all_customers)}')

# Show recent calls - use correct column names from call_logs
cursor.execute('''
    SELECT c.name, c.industry, c.phone, cl.call_date, cl.result, cl.note
    FROM call_logs cl
    JOIN customers c ON cl.customer_id = c.id
    ORDER BY cl.call_date DESC
    LIMIT 10
''')
recent_calls = cursor.fetchall()
print('\nRecent calls:')
for row in recent_calls:
    print(f'  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}')

# Show uncontacted A-class customers
cursor.execute('''
    SELECT id, name, industry, phone, tier
    FROM customers
    WHERE tier = 'A'
    AND id NOT IN (SELECT customer_id FROM call_logs)
    ORDER BY industry
''')
uncontacted_a = cursor.fetchall()
print(f'\nUncontacted A-class customers: {len(uncontacted_a)}')
for row in uncontacted_a:
    print(f'  {row[0]} | {row[1]} | {row[2]} | {row[3]}')

# Show customers contacted in last 7 days
seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
cursor.execute('''
    SELECT DISTINCT c.id, c.name, c.industry, c.phone, c.tier, cl.call_date, cl.result
    FROM customers c
    JOIN call_logs cl ON c.id = cl.customer_id
    WHERE cl.call_date >= ?
    ORDER BY c.tier, c.industry, cl.call_date DESC
''', (seven_days_ago,))
recently_contacted = cursor.fetchall()
print(f'\nRecently contacted (last 7 days): {len(recently_contacted)}')
for row in recently_contacted:
    print(f'  {row[0]} | {row[1]} | {row[2]} | {row[3]} | Last: {row[5]} | Result: {row[6]}')

conn.close()
