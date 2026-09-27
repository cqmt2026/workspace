import sqlite3, os
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()
# Get call logs in the week
week_start = '2026-08-31'
week_end = '2026-09-06'
c.execute(f"SELECT COUNT(*) FROM call_logs WHERE call_date >= ? AND call_date <= ?", (week_start, week_end))
total_calls = c.fetchone()[0]
c.execute(f"SELECT COUNT(DISTINCT customer_id) FROM call_logs WHERE call_date >= ? AND call_date <= ?", (week_start, week_end))
distinct_customers = c.fetchone()[0]
print(f"Week calls: {total_calls}, distinct customers: {distinct_customers}")
# Get all call stats
c.execute("SELECT result, COUNT(*) FROM call_logs GROUP BY result")
print("Call results:", c.fetchall())
c.execute("SELECT call_date, COUNT(*) FROM call_logs GROUP BY call_date")
print("Calls by date:", c.fetchall())
# Customer status distribution
c.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
print("Customer status:", c.fetchall())
# Leads
c.execute("SELECT COUNT(*) FROM leads")
print("Leads count:", c.fetchone()[0])
# Top industries
c.execute("SELECT industry, COUNT(*) as cnt FROM customers GROUP BY industry ORDER BY cnt DESC LIMIT 20")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")
conn.close()
print("\nDone.")
