import sqlite3, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()

# Get top 10 by industry priority with valid phone, limited to main industries
cur.execute('''
    SELECT name, industry, phone, district 
    FROM customers 
    WHERE tier='A' 
      AND phone IS NOT NULL 
      AND phone != '' 
      AND phone NOT LIKE '[]%'
      AND phone NOT LIKE '%None%'
      AND phone NOT LIKE '%空%'
      AND phone NOT LIKE '%无%'
      AND industry IN ('医疗器械','新材料化工','机械装备汽配','环保检测','建筑建材','新能源充电电力')
    ORDER BY 
        CASE industry 
            WHEN '医疗器械' THEN 1 
            WHEN '新材料化工' THEN 2 
            WHEN '机械装备汽配' THEN 3 
            WHEN '环保检测' THEN 4 
            WHEN '建筑建材' THEN 5 
            WHEN '新能源充电电力' THEN 6 
        END,
        CASE district 
            WHEN '渝北区' THEN 1 WHEN '两江新区' THEN 2 WHEN '九龙坡区' THEN 3 
            WHEN '大渡口区' THEN 4 WHEN '南岸区' THEN 5 WHEN '沙坪坝区' THEN 6
            ELSE 7 
        END
    LIMIT 10
''')
rows = cur.fetchall()
for i, r in enumerate(rows):
    print(f"{i+1}|{r[0]}|{r[1]}|{r[2]}|{r[3]}")
