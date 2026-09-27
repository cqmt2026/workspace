#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成今日拨打清单 - 基于实际CRM数据"""
import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'baidu_crm.db')

# 行业优先级映射（根据实际数据调整）
INDUSTRY_PRIORITY = {
    '医疗器械': 1,
    '新材料化工': 2,
    '机械装备汽配': 3,
    '环保检测': 4,
    '建筑建材': 5,
    '新能源充电电力': 6,
    '智能制造': 7,
    '数控机床': 8,
    '精密机械': 9,
    '自动化设备': 10,
    '液压设备': 11,
    '工程机械': 12,
}

# 各行业话术模板
INDUSTRY_SCRIPTS = {
    '医疗器械': """您是重庆医疗器械领域最有实力的企业之一，但百度搜'重庆医疗器械''重庆IVD'，前十页都没有你们。这意味着你们的客户在找供应商时，第一个看到的是竞争对手或者聚合平台。你们现在主要靠什么渠道获客？展会、代理商，还是老客户介绍？""",
    
    '新材料化工': """新材料行业百度基本是空白，你们专精特新资质+技术实力，完全可以在百度上建立行业第一的认知。下游客户（汽车/电子/建筑厂）找供应商时，第一站就是百度搜'[材料]+供应商'。你们现在线上获客有在做吗？""",
    
    '机械装备汽配': """制造业企业客户找供应商，第一反应是百度搜。你们产品这么好，但百度上搜不到，等于把客户拱手让给竞争对手。重庆机械企业801家，但百度投放的不到10%，这是蓝海机会。你们现在订单主要怎么来？""",
    
    '环保检测': """环保检测企业的主要客户是政府/国企，他们招标前一定会百度搜供应商名录。你们现在百度上几乎是空白的，这是最大的获客机会。有CMA/CNAS资质对招标很重要。""",
    
    '建筑建材': """建筑工程B2B，百度搜索量大但投放少。甲方找分包/供应商时，会先百度验证实力。你们现在百度上能搜到吗？项目主要靠关系还是也有市场化获客？""",
    
    '新能源充电电力': """充电桩设备制造商，百度竞争极少。重庆新能源政策驱动，你们是技术领先的企业，应该在线上建立品牌优势。下游客户找供应商第一站就是百度。""",
    
    '智能制造': """工业4.0时代，智能制造企业应该在线上建立技术品牌形象。百度搜'重庆智能制造''重庆自动化设备'，你们排第几？客户找供应商第一站就是百度。""",
    
    '数控机床': """精密制造企业，客户找供应商第一件事就是百度搜'重庆数控机床''数控加工中心'。你们现在能搜到自己吗？竞品已经在投了。""",
    
    '精密机械': """精密加工是企业名片，但百度上搜'重庆精密加工'，你们排第几？这直接影响客户对你们技术实力的第一印象。""",
    
    '自动化设备': """自动化设备厂商，客户找供应商第一站就是百度。你们的产品这么好，但百度上几乎看不到，等于把客户让给外地竞品。""",
}

def get_today_list(limit=10):
    """生成今日拨打清单"""
    
    if not os.path.exists(DB_PATH):
        print(f"错误：CRM数据库不存在：{DB_PATH}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询待联系/需跟进的客户，按行业优先级和Tier排序
    query = """
        SELECT id, name, industry, phone, contact, status, tier, note
        FROM customers 
        WHERE status IN ('待联系', '需跟进')
        ORDER BY 
            CASE 
                WHEN industry = '医疗器械' THEN 1
                WHEN industry = '新材料化工' THEN 2
                WHEN industry = '机械装备汽配' THEN 3
                WHEN industry = '环保检测' THEN 4
                WHEN industry = '建筑建材' THEN 5
                WHEN industry = '新能源充电电力' THEN 6
                WHEN industry = '智能制造' THEN 7
                WHEN industry = '数控机床' THEN 8
                WHEN industry = '精密机械' THEN 9
                WHEN industry = '自动化设备' THEN 10
                WHEN industry = '液压设备' THEN 11
                WHEN industry = '工程机械' THEN 12
                ELSE 99
            END,
            CASE tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
            id ASC
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    customers = cursor.fetchall()
    conn.close()
    
    # 生成清单
    result = []
    for idx, cust in enumerate(customers, 1):
        cust_id, company, industry, phone, contact, status, tier, notes = cust
        
        # 获取话术
        script = INDUSTRY_SCRIPTS.get(industry, INDUSTRY_SCRIPTS.get('机械装备汽配', ''))
        
        result.append({
            '序号': idx,
            '企业': company,
            '行业': industry,
            '电话': phone or '暂无',
            '联系人': contact or '待定',
            '状态': status,
            'Tier': tier,
            '话术摘要': script[:60] + '...' if len(script) > 60 else script
        })
    
    return result

def print_list(result):
    """打印清单"""
    if not result:
        print("暂无未联系/待跟进客户")
        return
    
    print("=" * 80)
    print(f"百都科技·今日拨打清单")
    print(f"日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"共 {len(result)} 家客户")
    print("=" * 80)
    print()
    
    for item in result:
        print(f"【{item['序号']}】{item['企业']}")
        print(f"    行业：{item['行业']} | Tier：{item['Tier']} | 状态：{item['状态']}")
        print(f"    电话：{item['电话']} | 联系人：{item['联系人']}")
        print(f"    话术：{item['话术摘要']}")
        print("-" * 80)

def save_list(result, output_path=None):
    """保存清单到文件"""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', f'明日拨打名单_{datetime.now().strftime("%Y-%m-%d")}.md')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    weekday_map = ['周一','周二','周三','周四','周五','周六','周日']
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 百都科技·今日拨打清单\n\n")
        f.write(f"**日期**: {datetime.now().strftime('%Y-%m-%d')} ({weekday_map[datetime.now().weekday()]})\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%H:%M')}\n")
        f.write(f"**客户数**: {len(result)}家\n\n")
        f.write("---\n\n")
        f.write("| 序号 | 企业 | 行业 | Tier | 电话 | 联系人 | 状态 |\n")
        f.write("|------|------|------|------|------|--------|------|\n")
        
        for item in result:
            f.write(f"| {item['序号']} | {item['企业']} | {item['行业']} | {item['Tier']} | {item['电话']} | {item['联系人']} | {item['状态']} |\n")
        
        f.write("\n---\n\n")
        f.write("## 话术参考\n\n")
        
        # 按行业分组话术
        for item in result:
            industry = item['行业']
            script = INDUSTRY_SCRIPTS.get(industry, '')
            if script:
                f.write(f"### {industry}\n\n")
                f.write(f"> {script}\n\n")
    
    print(f"清单已保存至：{output_path}")
    return output_path

if __name__ == '__main__':
    result = get_today_list(limit=10)
    print_list(result)
    
    # 自动保存到assets目录
    output = save_list(result)
    print(f"\n完成！")
