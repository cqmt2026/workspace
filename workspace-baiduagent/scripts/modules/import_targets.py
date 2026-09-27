# -*- coding: utf-8 -*-
"""
快速导入脚本 - 将现有名单批量导入CRM
创建: 2026-08-26 | 作者: 小度
"""
import sqlite3
import os
import sys

# 直接导入crm模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location('crm', os.path.join(os.path.dirname(__file__), '..', 'core', 'crm.py'))
crm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crm)
get_conn = crm.get_conn

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')

def import_from_target_pool():
    """从中小客户目标池导入A类客户"""
    pool_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', '中小客户目标池_2026-08-26.md')
    conn = get_conn()
    c = conn.cursor()
    
    imported = 0
    with open(pool_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_industry = ''
    in_target = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('### 🥇 Tier 1'):
            current_industry = '医疗器械'
            in_target = True
            continue
        elif line.startswith('### 🥈 Tier 2'):
            current_industry = '新材料化工'
            in_target = True
            continue
        elif line.startswith('### 🥉 Tier 3'):
            current_industry = '机械装备'
            in_target = True
            continue
        elif line.startswith('### 🏅 Tier 4'):
            current_industry = '环保检测'
            in_target = True
            continue
        elif line.startswith('### ⚡ Tier 5'):
            current_industry = '新能源充电'
            in_target = True
            continue
        elif line.startswith('| **序号**'):
            continue  # 跳过表头
        elif line.startswith('|') and len(line) > 2 and in_target:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 2:
                name = parts[1].replace('**', '')
                phone = parts[2] if len(parts) > 2 else ''
                if name and len(name) > 3:
                    try:
                        c.execute("SELECT id FROM customers WHERE name=?", (name,))
                        if not c.fetchone():
                            c.execute('''INSERT INTO customers (name, industry, tier, phone, source, status)
                                         VALUES (?, ?, 'A', ?, '目标池导入', '待联系')''',
                                      (name, current_industry, phone))
                            imported += 1
                    except Exception as e:
                        print(f"  [WARN] {name}: {e}")
        elif not line.startswith('|') and not line.startswith('#') and line != '':
            in_target = False
    
    conn.commit()
    conn.close()
    print(f"[OK] 从目标池导入 {imported} 家A类客户")
    return imported

if __name__ == '__main__':
    import_from_target_pool()