#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补充机械装备汽配行业缺失电话"""
import sqlite3
import os
import sys

DB = 'data/baidu_crm.db'

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # 找机械装备汽配无电话的企业
    c.execute('''SELECT id, name, address, district 
                 FROM customers 
                 WHERE industry = "机械装备汽配" 
                 AND (phone IS NULL OR phone = "")
                 LIMIT 50''')
    rows = c.fetchall()
    print(f'机械装备汽配无电话企业：{len(rows)}家')
    
    # 打印前10家
    for i, r in enumerate(rows[:10], 1):
        print(f'{i}. {r[1]} | 地址:{r[2]} | 区域:{r[3]}')
    
    conn.close()

if __name__ == '__main__':
    main()
