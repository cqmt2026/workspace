# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
tiers = ['医疗器械','新材料化工','机械装备汽配','环保检测','建筑建材','新能源充电电力']
print('=== 第二梯队CRM统计 ===')
total = 0
with_phone = 0
for t in tiers:
    cur.execute("SELECT COUNT(*) FROM customers WHERE industry=?", (t,))
    cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers WHERE industry=? AND phone != ''", (t,))
    phone_cnt = cur.fetchone()[0]
    total += cnt
    with_phone += phone_cnt
    pct = phone_cnt/cnt*100 if cnt > 0 else 0
    print(f'{t}: {cnt}家, 有电话{phone_cnt}家 ({pct:.0f}%)')
print(f'\n总计: {total}家, 有电话{with_phone}家 ({with_phone/total*100:.0f}%)')
