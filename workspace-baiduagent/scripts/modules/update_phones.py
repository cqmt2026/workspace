# -*- coding: utf-8 -*-
"""
补充已知客户电话 - 从目标池/蓝海名单中已确认的电话，更新到CRM
创建: 2026-08-26 | 作者: 小度
"""
import os
import sys

# 加载crm
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location('crm', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'core', 'crm.py'))
crm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crm)

# 已知电话映射（来源：中小客户目标池 + 蓝海名单，已核实）
KNOWN_PHONES = {
    '中元汇吉生物技术': '023-68959999',
    '山外山医疗': '023-68605247',
    '海扶医院': '023-67886660',
    '再升科技': '023-67183329',
    '数引网': '023-63660666',
    '云翼智航': '19332234194',
    '特永建筑': '138-8335-6656',
    '壹木和科技': '1333-035-9876',
    '重庆特永建筑': '138-8335-6656',
    '重庆壹木和科技': '1333-035-9876',
}

def update_phones():
    conn = crm.get_conn()
    c = conn.cursor()
    updated = 0
    for name, phone in KNOWN_PHONES.items():
        c.execute("UPDATE customers SET phone=? WHERE name=? AND (phone IS NULL OR phone='' OR phone='-')", (phone, name))
        if c.rowcount > 0:
            print(f"[OK] {name} 补电话: {phone}")
            updated += 1
        else:
            # 可能名字不完全匹配，模糊找
            c.execute("SELECT id, name, phone FROM customers WHERE name LIKE ?", (f'%{name[:4]}%',))
            rows = c.fetchall()
            for rid, rname, rphone in rows:
                if not rphone or rphone == '-' or rphone == '':
                    c.execute("UPDATE customers SET phone=? WHERE id=?", (phone, rid))
                    print(f"[OK] {rname}(#{rid}) 补电话: {phone}")
                    updated += 1
    conn.commit()
    conn.close()
    print(f"[DONE] 共补充 {updated} 条电话")

if __name__ == '__main__':
    update_phones()