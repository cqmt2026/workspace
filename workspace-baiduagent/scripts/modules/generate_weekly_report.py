import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()

# 本周时间范围（周一2026-09-07到周日2026-09-13）
week_start = '2026-09-07'
week_end = '2026-09-13'

print("=" * 50)
print("百都科技周报 | 2026年9月7日-13日")
print("=" * 50)

# 1. 本周拨打统计
print("\n【一、本周拨打统计】")
try:
    cur.execute("""
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN result = '有效' THEN 1 ELSE 0 END) as valid,
            SUM(CASE WHEN result = '有意向' THEN 1 ELSE 0 END) as interested,
            SUM(CASE WHEN result IS NULL OR result = '' THEN 0 ELSE 1 END) as other
        FROM call_logs
        WHERE call_date >= ? AND call_date <= ?
    """, (week_start, week_end))
    stats = cur.fetchone()
    total = stats[0] or 0
    valid = stats[1] or 0
    interested = stats[2] or 0
    
    print(f"  总拨打: {total}次")
    print(f"  有效: {valid}次")
    print(f"  有意向: {interested}次")
    
    # 成交统计
    cur.execute("SELECT COUNT(*) FROM customers WHERE status = '已成交'")
    closed = cur.fetchone()[0] or 0
    print(f"  成交: {closed}家")
except Exception as e:
    print(f"  查询失败: {e}")
    total = 0
    valid = 0
    interested = 0
    closed = 0

# 2. 行业转化对比
print("\n【二、行业转化对比】")
try:
    cur.execute("""
        SELECT 
            c.industry,
            COUNT(DISTINCT c.id) as customers,
            COUNT(cl.id) as calls
        FROM customers c
        LEFT JOIN call_logs cl ON c.id = cl.customer_id AND cl.call_date >= ? AND cl.call_date <= ?
        GROUP BY c.industry
        ORDER BY customers DESC
        LIMIT 10
    """, (week_start, week_end))
    industries = cur.fetchall()
    
    for ind in industries:
        if ind[1] > 0:
            print(f"  {ind[0]}: {ind[1]}家客户, {ind[2] or 0}次拨打")
except Exception as e:
    print(f"  查询失败: {e}")

# 3. 成交进度
print("\n【三、成交进度（vs 月目标）】")
try:
    cur.execute("SELECT COUNT(*) FROM customers WHERE status = '已成交'")
    month_closed = cur.fetchone()[0] or 0
    monthly_target = 10
    completion_rate = month_closed / monthly_target * 100
    
    print(f"  本月成交: {month_closed}家")
    print(f"  月目标: {monthly_target}家")
    print(f"  完成率: {completion_rate:.0f}%")
    
    if completion_rate >= 100:
        print("  [OK] 目标已达成！")
    elif completion_rate >= 70:
        print("  [WARN] 进度滞后，需加把劲")
    else:
        print("  [FAIL] 进度严重滞后")
except Exception as e:
    print(f"  查询失败: {e}")

# 4. 本周拨打记录
print("\n【四、本周拨打明细】")
try:
    cur.execute("""
        SELECT c.name, c.industry, cl.call_date, cl.duration_sec, cl.result
        FROM customers c
        JOIN call_logs cl ON c.id = cl.customer_id
        WHERE cl.call_date >= ?
        ORDER BY cl.call_date DESC
        LIMIT 15
    """, (week_start,))
    calls = cur.fetchall()
    
    if calls:
        for call in calls:
            date_str = call[2][:10] if call[2] else "未知"
            duration = call[3] or 0
            result = call[4] or "未记录"
            print(f"  {call[0]}({call[1]}) - {date_str} - {result} - {duration}秒")
    else:
        print("  本周暂无拨打记录")
except Exception as e:
    print(f"  查询失败: {e}")

# 5. 建议
print("\n【五、下步建议】")
if total == 0:
    print("  [WARN] 本周零拨打，需立即启动客户触达")
elif closed == 0:
    print("  [WARN] 本周无成交，需重点跟进意向客户")
    
if month_closed < 5:
    print("  [WARN] 月成交不足5家，距目标差距大，建议:")
    print("     1. 加大拨打量，目标每日15+通")
    print("     2. 重点跟进机械行业A类客户")
    print("     3. 完善话术，提升转化")

conn.close()
print("\n" + "=" * 50)
print("报告生成时间: 2026-09-13 20:00")
print("=" * 50)
