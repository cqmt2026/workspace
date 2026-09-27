#!/usr/bin/env python3
"""生成每日50家源头厂家拨打清单"""
import sqlite3
import os
import json
import sys
from datetime import datetime, timedelta

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
OUTPUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets'

# 排除关键词：批发商、贸易商、代理商、加工部、门店等
EXCLUDE_KEYWORDS = [
    '批发', '超市', '商行', '经销', '代理', '贸易', '供应站', 
    '零售', '门店', '经营部', '供销', '加工部', '加工厂', '店',
    '中心', '服务部', '工作室', '营业部'
]

# 优先关键词：源头厂家特征
PRIORITY_KEYWORDS = [
    '制造', '生产', '有限', '股份', '技术', '科技', '实业',
    '机械', '设备', '仪器', '仪表', '电子', '电气', '材料',
    '化工', '环保', '检测', '生物', '医药', '医疗'
]

def exclude_pattern():
    """生成SQL排除条件"""
    conditions = [f"name NOT LIKE '%{kw}%'" for kw in EXCLUDE_KEYWORDS]
    return ' AND '.join(conditions)

def priority_pattern():
    """生成SQL优先条件"""
    conditions = [f"name LIKE '%{kw}%'" for kw in PRIORITY_KEYWORDS]
    return ' OR '.join(conditions)

def query_source_manufacturers(limit=100):
    """查询源头厂家"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    exclude = exclude_pattern()
    priority = priority_pattern()
    
    # 机械装备汽配
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '机械装备汽配' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    mechanical = cur.fetchall()
    
    # 医疗器械
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '医疗器械' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    medical = cur.fetchall()
    
    # 新材料化工
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '新材料化工' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    new_materials = cur.fetchall()
    
    # 环保检测
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '环保检测' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    environmental = cur.fetchall()
    
    # 自动化设备
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '自动化设备' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    automation = cur.fetchall()
    
    # 液压设备
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '液压设备' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    hydraulic = cur.fetchall()
    
    # 智能制造
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '智能制造' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    smart_manufacturing = cur.fetchall()
    
    # 精密机械
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '精密机械' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    precision = cur.fetchall()
    
    # 数控机床
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '数控机床' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    cnc = cur.fetchall()
    
    # 模具
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = '模具' AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {exclude}
        ORDER BY 
            CASE WHEN ({priority}) THEN 0 ELSE 1 END,
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (limit,))
    molds = cur.fetchall()
    
    conn.close()
    
    return {
        'mechanical': mechanical,
        'medical': medical,
        'new_materials': new_materials,
        'environmental': environmental,
        'automation': automation,
        'hydraulic': hydraulic,
        'smart_manufacturing': smart_manufacturing,
        'precision': precision,
        'cnc': cnc,
        'molds': molds
    }

def generate_daily_list(industries_data, day_number, date_str):
    """生成每日50家清单"""
    lines = []
    lines.append(f"# GEO突破 - Day {day_number} 拨打清单（{date_str}）")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 执行日期：{date_str}")
    lines.append(f"> 主题：机械装备类源头厂家（已排除批发商、加工部、门店）")
    lines.append(f"> 目标：50家源头厂家")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 统计各行业发展
    lines.append("## 📊 今日行业分布")
    lines.append("")
    lines.append("| 序号 | 公司名称 | 行业 | 电话 | 区域 |")
    lines.append("|------|---------|------|------|------|")
    
    all_customers = []
    
    # 按行业分配数量（机械20家、医疗10家、新材料8家、环保5家、其他7家）
    distribution = [
        ('mechanical', 20),
        ('medical', 10),
        ('new_materials', 8),
        ('environmental', 5),
        ('automation', 4),
        ('hydraulic', 3),
        ('smart_manufacturing', 2),
        ('precision', 2),
        ('cnc', 1),
    ]
    
    row_num = 1
    for industry_key, count in distribution:
        if industry_key in industries_data:
            customers = industries_data[industry_key][:count]
            for name, ind, phone, tier, district in customers:
                d = district if district else '未知'
                phone_clean = phone.replace('(', '').replace(')', '').replace('-', '')[:15]
                lines.append(f"| {row_num:2} | {name[:30]:<30} | {ind[:10]:<10} | {phone_clean:<15} | {d:<8} |")
                all_customers.append({
                    'seq': row_num,
                    'name': name,
                    'industry': ind,
                    'phone': phone,
                    'district': d
                })
                row_num += 1
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 今日目标")
    lines.append("")
    lines.append("| 指标 | 目标值 |")
    lines.append("|------|--------|")
    lines.append("| 拨打量 | 50通 |")
    lines.append("| 接通率 | >60% |")
    lines.append("| 意向数 | ≥5个 |")
    lines.append("| 拜访邀约 | ≥2个 |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 💬 开场白模板（机械类）")
    lines.append("")
    lines.append("```")
    lines.append('"您好，请问是[公司名]吗？我是百都科技的小度，做重庆中小企业获客增长的。')
    lines.append("")
    lines.append("打电话前我先在豆包上搜了一下——发现搜\'[产品]+重庆\'，AI回答里推荐的都是外地公司或者聚合平台，咱们本地厂家几乎没有曝光。")
    lines.append("")
    lines.append("但你们下游客户找供应商时，第一件事就是搜这个。这意味着什么？你的潜在采购商正在被AI引导去别家。")
    lines.append("")
    lines.append("冒昧问一下——你们现在主要靠什么渠道接客户？")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📝 通话记录模板")
    lines.append("")
    lines.append("```")
    lines.append("【通话记录】")
    lines.append(f"日期：{date_str}")
    lines.append("客户名称：")
    lines.append("行业：")
    lines.append("电话：")
    lines.append("BANT评分：B__ A__ N__ T__（总分__）")
    lines.append("Lead等级：🔥Hot / 🟡Warm / 🟢Cold")
    lines.append("核心痛点：")
    lines.append("当前获客方式：")
    lines.append("预算线索：")
    lines.append("决策人：是否可直接拍板？")
    lines.append('GEO可见度：豆包搜索"XX"的结果如何？')
    lines.append("下一步行动：□上门拜访 □微信发方案 □3天后跟进 □纳入培育池")
    lines.append("跟进时间：")
    lines.append("备注：")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ⏰ 今日节奏")
    lines.append("")
    lines.append("```")
    lines.append("09:00-09:30  完成10家侦察（企查查+百度+豆包）")
    lines.append("09:30-10:30  拨打第1-10家")
    lines.append("10:30-11:00  完成10家侦察")
    lines.append("11:00-12:00  拨打第11-20家")
    lines.append("14:00-15:00  完成10家侦察")
    lines.append("15:00-16:00  拨打第21-30家")
    lines.append("16:00-17:00  完成10家侦察")
    lines.append("17:00-18:00  拨打第31-40家 + 复盘")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"_清单生成：小度 | {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append(f"_执行日期：{date_str}_")
    
    return '\n'.join(lines), all_customers

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    # 查询源头厂家
    print("正在查询源头厂家数据库...")
    industries_data = query_source_manufacturers(limit=100)
    
    # 统计各行业发展
    print("\n【各行业源头厂家数量】")
    total = 0
    for key, data in industries_data.items():
        print(f"  {key}: {len(data)} 家")
        total += len(data)
    print(f"\n总计: {total} 家源头厂家")
    
    # 生成5天清单
    start_date = datetime(2026, 9, 14)
    
    for day in range(1, 6):
        current_date = start_date + timedelta(days=day-1)
        date_str = current_date.strftime('%Y-%m-%d')
        
        print(f"\n正在生成 Day {day} ({date_str}) 清单...")
        content, customers = generate_daily_list(industries_data, day, date_str)
        
        # 保存到文件
        output_path = os.path.join(OUTPUT_DIR, f'GEO突破_Day{day}_50家清单_{date_str}.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ 已保存: {output_path}")
        print(f"  📊 客户数: {len(customers)} 家")
    
    print("\n✅ 全部完成！")

if __name__ == '__main__':
    main()
