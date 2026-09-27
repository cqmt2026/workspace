#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动为未分类客户分配层级"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

# 分层规则（基于行业价值）
TIER_RULES = {
    # A类：高价值行业
    '口腔诊所': 'A',
    '医美机构': 'A',
    '宠物医院': 'A',
    '医疗器械': 'A',
    '教培机构': 'A',
    '装修装饰': 'A',
    '机械装备汽配': 'A',
    '新材料化工': 'A',
    '环保检测': 'A',
    '建筑建材': 'A',
    '新能源充电电力': 'A',
    
    # B类：中等价值
    '母婴亲子': 'B',
    '酒店餐饮': 'B',
    '汽车服务': 'B',
    '家具家居': 'B',
    '文化传媒': 'B',
    '健身瑜伽': 'B',
    '物流货运': 'B',
    '人力资源': 'B',
    '软件信息': 'B',
    '智能制造': 'B',
    '检验检测': 'B',
    '食品加工': 'B',
    '电子科技': 'B',
    '能源环保补充': 'B',
    '教育培训补充': 'B',
    
    # 其他默认B类
}

def assign_tiers():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 获取所有未分类客户
    cur.execute("SELECT id, industry FROM customers WHERE tier IS NULL")
    unclassified = cur.fetchall()
    
    print(f"共{len(unclassified)}家未分类客户")
    
    assigned = 0
    skipped = 0
    for cust_id, industry in unclassified:
        tier = TIER_RULES.get(industry, 'B')  # 默认B类
        cur.execute("UPDATE customers SET tier=? WHERE id=?", (tier, cust_id))
        assigned += cur.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"分配完成: {assigned}家")
    
    # 验证
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier")
    print("\n分层结果:")
    for r in cur.fetchall():
        print(f"  {r[0] or '未分类'}: {r[1]}家")
    
    cur.execute("SELECT COUNT(*) FROM customers WHERE tier IS NULL")
    remaining = cur.fetchone()[0]
    print(f"\n剩余未分类: {remaining}家")
    conn.close()

if __name__ == '__main__':
    assign_tiers()
