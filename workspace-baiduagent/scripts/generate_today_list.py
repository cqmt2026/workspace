import sqlite3
import json

conn = sqlite3.connect('C:/Users/Administrator/.openclaw/workspace/workspace-baiduagent/data/baidu_crm.db')
cursor = conn.cursor()

# 查询有电话的未联系/需跟进客户，按行业优先级排序
sql = '''
SELECT id, name, industry, tier, phone, status, last_call, note
FROM customers
WHERE (status IS NULL OR status = '' OR status = '待联系' OR status = '需跟进')
  AND phone IS NOT NULL AND phone != ''
ORDER BY 
    CASE industry
        WHEN '医疗器械' THEN 1
        WHEN '新材料化工' THEN 2
        WHEN '机械装备汽配' THEN 3
        WHEN '环保检测' THEN 4
        WHEN '建筑建材' THEN 5
        WHEN '新能源充电电力' THEN 6
        WHEN '智能制造' THEN 7
        WHEN '数控机床' THEN 8
        WHEN '精密机械' THEN 9
        WHEN '自动化设备' THEN 10
        ELSE 99
    END,
    CASE WHEN tier = 'A' THEN 1 WHEN tier = 'B' THEN 2 ELSE 3 END,
    id
LIMIT 10
'''

cursor.execute(sql)
rows = cursor.fetchall()

result = []
for r in rows:
    result.append({
        'id': r[0],
        'name': r[1],
        'industry': r[2],
        'tier': r[3],
        'phone': r[4],
        'status': r[5],
        'last_call': r[6],
        'note': r[7]
    })

print(json.dumps(result, ensure_ascii=False, indent=2))
conn.close()
