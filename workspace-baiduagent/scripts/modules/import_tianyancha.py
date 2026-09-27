# -*- coding: utf-8 -*-
"""
批量导入天眼查导出Excel到CRM
"""
import sys, os, sqlite3, openpyxl
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
SOURCE_DIR = r'E:\百都文件'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=" * 70)
print("【天眼查数据批量导入】")
print("=" * 70)

# 查找所有天眼查导出文件
tianyancha_files = [f for f in os.listdir(SOURCE_DIR) if '天眼查' in f and f.endswith('.xlsx')]
print(f"\n找到{len(tianyancha_files)}个天眼查导出文件\n")

total_inserted = 0
total_skipped = 0
total_errors = 0

for idx, filename in enumerate(tianyancha_files, 1):
    filepath = os.path.join(SOURCE_DIR, filename)
    print(f"[{idx}/{len(tianyancha_files)}] {filename}")
    
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        ws = wb.active
        
        # 跳过第一行声明，从第二行开始读取表头
        headers = [cell.value for cell in ws[2]]
        print(f"  表头: {headers[:5]}...")
        
        inserted = 0
        skipped = 0
        errors = 0
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=3), start=3):
            try:
                # 提取字段
                name = row[0].value if len(row) > 0 else None  # 公司名称
                status = row[1].value if len(row) > 1 else None  # 登记状态
                legal_rep = row[2].value if len(row) > 2 else None  # 法定代表人
                capital = row[3].value if len(row) > 3 else None  # 注册资本
                unified_code = row[4].value if len(row) > 4 else None  # 统一社会信用代码
                phone = row[5].value if len(row) > 5 else None  # 有效手机号
                address = row[6].value if len(row) > 6 else None  # 最新年报地址
                
                if not name:
                    continue
                
                name = str(name).strip()
                phone = str(phone).strip() if phone else ''
                
                # 检查是否已存在
                c.execute("SELECT id FROM customers WHERE name = ?", (name,))
                if c.fetchone():
                    # 更新电话（如果有）
                    if phone:
                        c.execute("""
                            UPDATE customers 
                            SET phone = COALESCE(phone, ?),
                                source = source || '+天眼查',
                                updated_at = ?
                            WHERE name = ?
                        """, (phone, datetime.now().strftime('%Y-%m-%d %H:%M'), name))
                        if c.rowcount > 0:
                            inserted += 1
                    skipped += 1
                    continue
                
                # 插入新记录
                c.execute("""
                    INSERT INTO customers (name, industry, tier, phone, address, source, status, created_at, updated_at)
                    VALUES (?, '天眼查导出', 'A', ?, ?, '天眼查-{}'.format(?), '待联系', ?, ?)
                """, (name, phone, address, filename[:20], datetime.now(), datetime.now()))
                
                if c.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  行{row_idx}错误: {e}")
        
        conn.commit()
        total_inserted += inserted
        total_skipped += skipped
        total_errors += errors
        
        print(f"  结果: +{inserted}条, 跳过{skipped}条, 错误{errors}条")
        
    except Exception as e:
        print(f"  ❌ 文件读取失败: {e}")
        total_errors += 1

conn.close()

print(f"\n{'='*70}")
print(f"导入完成!")
print(f"  新增: {total_inserted}条")
print(f"  跳过: {total_skipped}条")
print(f"  错误: {total_errors}条")

# 统计最终状态
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM customers")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = c.fetchone()[0]
conn.close()

print(f"\nCRM最终状态:")
print(f"  总客户: {total:,}家")
print(f"  有电话: {has_phone:,}家 ({has_phone*100//total if total>0 else 0}%)")