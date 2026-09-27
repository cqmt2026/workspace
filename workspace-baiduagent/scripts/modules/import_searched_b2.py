# -*- coding: utf-8 -*-
"""
批量导入第二批实测客户到CRM
创建: 2026-08-26 | 作者: 小度
"""
import os
import sys
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT_DIR, 'scripts', 'core'))
import sqlite3

DB_PATH = os.path.join(ROOT_DIR, 'scripts', 'data', 'baidu_crm.db')
NAME_FILE = os.path.join(ROOT_DIR, 'assets', '百度实测客户名单_2026-08-26_b2.md')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
imported = 0
skipped = 0

with open(NAME_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

current_section = ''
for line in lines:
    line = line.strip()
    if '🌿 环保检测' in line:
        current_section = '环保检测'
        continue
    elif '🏗️ 机械起重设备' in line or '🏗️' in line:
        current_section = '机械装备'
        continue
    elif '🏥 医疗器械补充' in line:
        current_section = '医疗器械'
        continue
    elif '🏠 装修公司' in line or '🏠本地服务' in line:
        current_section = '本地服务'
        continue
    elif '📚 教育培训' in line:
        current_section = '教育培训'
        continue
    elif '🦷 医美齿科' in line:
        current_section = '医美齿科'
        continue
    
    if line.startswith('|') and len(line) > 5 and '序号' not in line:
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 3:
            name = re.sub(r'\*+', '', parts[1]).strip()
            phone_raw = parts[2] if len(parts) > 2 else ''
            phones = re.findall(r'1[3-9]\d{9}|0[1-9]\d{7,10}', phone_raw)
            phone = phones[0] if phones else ''
            
            if name and len(name) > 3:
                try:
                    c.execute("SELECT id FROM customers WHERE name=?", (name,))
                    if c.fetchone():
                        skipped += 1
                        continue
                    c.execute('''INSERT INTO customers (name, industry, tier, phone, source, status)
                                 VALUES (?, ?, 'A', ?, '百度搜索实测b2', '待联系')''',
                              (name, current_section, phone))
                    print(f"[OK] {name} | {current_section} | {phone or '待验证'}")
                    imported += 1
                except Exception as e:
                    print(f"[ERR] {name}: {e}")

conn.commit()
conn.close()
print(f"\n[总结] 导入 {imported} 家，跳过 {skipped} 家（已存在）")