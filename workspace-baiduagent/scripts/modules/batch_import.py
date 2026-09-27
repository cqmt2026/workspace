# -*- coding: utf-8 -*-
"""
批量导入六大数据源名单到CRM
创建: 2026-08-29 | 作者: 小度
"""
import sqlite3
import csv
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(ROOT_DIR, 'data', 'baidu_crm.db')

# 行业名称映射（csv文件名 → CRM行业名）
INDUSTRY_MAP = {
    'kq': '口腔诊所',
    'zs': '装修装饰',
    'jp': '教培机构',
    'my': '母婴亲子',
    'ym': '医美机构',
    'cw': '宠物医院',
}

def ensure_tables():
    """确保表结构存在（幂等）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        industry TEXT,
        tier TEXT CHECK(tier IN ('A','B','C')),
        phone TEXT,
        contact TEXT,
        source TEXT,
        status TEXT CHECK(status IN ('待联系','已联系','有意向','已成交','放弃')) DEFAULT '待联系',
        last_call TEXT,
        note TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS call_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        call_date TEXT DEFAULT (date('now','localtime')),
        duration_sec INTEGER,
        result TEXT CHECK(result IN ('有效','无效','关机','拒接','有意向','需跟进')),
        next_action TEXT,
        script_version TEXT,
        note TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS industry_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        industry TEXT UNIQUE,
        search_volume TEXT,
        competitor_count TEXT,
        avg_cpc TEXT,
        key_words TEXT,
        tip TEXT,
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit()
    conn.close()

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def clean_phone(phone_str):
    """清理电话号码：保留分号分隔的多号码，每个号码提取有效数字"""
    if not phone_str:
        return ''
    phone_str = phone_str.strip()
    # 如果包含分号，保留分号分隔结构
    if ';' in phone_str:
        parts = phone_str.split(';')
        cleaned = []
        for p in parts:
            p = p.strip()
            # 提取第一个有效号码（座机或手机号）
            # 手机号: 1开头的11位; 座机: 023开头的区号+号码
            m = re.search(r'(1[3-9]\d{9}|023-?\d{7,8})', p)
            if m:
                cleaned.append(m.group(1).replace('-', ''))
        return ';'.join(cleaned) if cleaned else phone_str
    else:
        # 单号码：提取第一个有效号码
        m = re.search(r'(1[3-9]\d{9}|023-?\d{7,8})', phone_str)
        return m.group(1).replace('-', '') if m else phone_str

def import_csv(filename, industry_name, source_name):
    """导入单个CSV文件到CRM"""
    csv_path = os.path.join(ROOT_DIR, 'data', 'master', filename)
    if not os.path.exists(csv_path):
        print(f"  [SKIP] 文件不存在: {csv_path}")
        return 0, 0

    conn = get_conn()
    c = conn.cursor()

    inserted = 0
    skipped = 0
    total = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            name = row.get('机构名称', '').strip()
            phone = clean_phone(row.get('电话', ''))
            addr = row.get('地址', '').strip()
            region = row.get('区域', row.get('adname', '')).strip()
            lat = row.get('纬度', '')
            lng = row.get('经度', '')

            if not name:
                skipped += 1
                continue

            # 检查是否已存在
            c.execute("SELECT id FROM customers WHERE name=?", (name,))
            if c.fetchone():
                skipped += 1
                continue

            # 插入客户
            c.execute('''INSERT INTO customers 
                        (name, industry, tier, phone, source, status, note)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (name, industry_name, 'A', phone, source_name, '待联系',
                      f'区域:{region} | 地址:{addr[:50]} | 来源:{row.get("数据来源","")}'))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"  [{industry_name}] 共{total}家 → 新增{inserted}家 | 跳过{skipped}家")
    return inserted, skipped

def main():
    print("=" * 50)
    print("批量导入名单到CRM")
    print("=" * 50)
    ensure_tables()
    print("[OK] 数据库表结构确认")

    total_inserted = 0
    total_skipped = 0

    # 导入配置
    imports = [
        ('kq_list_chongqing_latest.csv', '口腔诊所', '高德+卫健委'),
        ('zs_list_chongqing_latest.csv', '装修装饰', '高德POI'),
        ('jp_list_chongqing_latest.csv', '教培机构', '高德+教委白名单'),
        ('my_list_chongqing_latest.csv', '母婴亲子', '高德POI'),
        ('ym_list_chongqing_latest.csv', '医美机构', '高德+卫健委'),
        ('cw_list_chongqing_latest.csv', '宠物医院', '高德POI'),
    ]

    for filename, industry, source in imports:
        ins, skip = import_csv(filename, industry, source)
        total_inserted += ins
        total_skipped += skip

    # 验证
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customers")
    total = c.fetchone()[0]
    c.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC")
    by_industry = c.fetchall()
    conn.close()

    print("\n" + "=" * 50)
    print(f"导入完成！")
    print(f"  本次新增: {total_inserted}家")
    print(f"  本次跳过: {total_skipped}家")
    print(f"  CRM客户总数: {total}家")
    print("\n分行业统计:")
    for ind, cnt in by_industry:
        print(f"  {ind}: {cnt}家")
    print("=" * 50)

if __name__ == '__main__':
    main()
