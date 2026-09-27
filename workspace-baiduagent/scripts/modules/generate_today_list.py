# -*- coding: utf-8 -*-
"""生成今日拨打清单Top10"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

# 今日Top10
c.execute("""SELECT id, name, industry, phone, note FROM customers
             WHERE status='待联系'
             ORDER BY
                 CASE industry
                     WHEN '口腔诊所' THEN 1
                     WHEN '医美机构' THEN 2
                     WHEN '教培机构' THEN 3
                     WHEN '装修装饰' THEN 4
                     WHEN '宠物医院' THEN 5
                     WHEN '母婴亲子' THEN 6
                     ELSE 7 END,
                 id ASC LIMIT 10""")

print("=" * 60)
print("📞 今日拨打清单 - 2026-08-29")
print("=" * 60)
for i, r in enumerate(c.fetchall(), 1):
    cid, name, industry, phone, note = r
    # 清洗电话：分号分隔多号码保留
    if phone:
        parts = phone.split(';')
        cleaned_parts = []
        for p in parts:
            m = re.search(r'(1[3-9]\d{9}|023-?\d{7,8})', p.strip())
            if m:
                cleaned_parts.append(m.group(1).replace('-', ''))
        clean_phone = ';'.join(cleaned_parts) if cleaned_parts else (phone or '无电话')
    else:
        clean_phone = '无电话'
    # 提取区域
    region = ''
    if note:
        m = re.search(r'区域[:：]\s*([^\s|]+)', note)
        if m:
            region = m.group(1)
    print(f"\n{i}. [{industry}] {name}")
    print(f"   📍 {region} | ☎ {clean_phone}")
    if note and len(note) > 60:
        print(f"   📝 {note[:60]}...")
    else:
        print(f"   📝 {note or ''}")

# 统计
c.execute("SELECT COUNT(*) FROM customers WHERE status='待联系'")
pending = c.fetchone()[0]
c.execute("SELECT industry, COUNT(*) FROM customers WHERE status='待联系' GROUP BY industry ORDER BY COUNT(*) DESC")
by_ind = c.fetchall()
conn.close()

print("\n" + "=" * 60)
print(f"📊 CRM待联系客户总计: {pending}家")
print("分行业待联系:")
for ind, cnt in by_ind:
    print(f"  {ind}: {cnt}家")
print("=" * 60)
