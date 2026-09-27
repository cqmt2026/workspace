# -*- coding: utf-8 -*-
"""Generate today's call list from CRM - cross-industry balanced, phone preferred"""
import sqlite3
import sys
from datetime import date

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'

SCRIPT_TEMPLATES = {
    '医疗器械': '重庆医疗器械百度几乎无投放，医院采购第一站是百度搜供应商。专精特新企业，你们却搜不到？',
    '新材料化工': '新材料产值6200亿但百度几乎没人投广告。你们专精特新+技术实力，应该建立行业第一认知。',
    '机械装备汽配': "制造业客户找供应商第一反应是百度搜产品+厂家。你们产品这么好但百度搜不到，等于把客户拱手让人。",
    '环保检测': '政府国企招标前必百度筛供应商。你们有CMA资质但百度几乎空白，甲方第一手名单里没有你们。',
    '建筑建材': '工程公司甲方找分包供应商时先百度搜验证实力。你们百度上能搜到吗？项目靠关系还是市场化获客？',
    '新能源充电电力': '充电桩设备制造商百度搜索竞争几乎为零。新能源政策驱动先发占位成本最低。',
    '口腔诊所': '患者搜"XX区整牙/补牙"先看谁，区域词蓝海但大词被连锁占。你们在XX区能搜到吗？',
    '医美机构': '求美者决策前深度搜索比价，百度品牌搜索是信任背书关键入口。你们百度上曝光够吗？',
    '教培机构': '家长搜"XX区培训/辅导"是招生核心入口。旺季搜索暴涨你们现在区域词排名如何？',
    '软件信息': '隐形冠军也需要百度——你们客户(主机厂采购)第一件事就是百度搜供应商。',
    '人力资源': '人力资源公司百度几乎无投放，招聘端和客户端都是蓝海机会。',
    '物流货运': '物流货运B2B搜索需求大但百度上本地企业曝光极少，先发占位成本低。',
    '食品加工': '食品企业百度投放意识薄弱但采购商搜索供应商是第一动作，空白即机会。',
}

def get_script(industry):
    for key, script in SCRIPT_TEMPLATES.items():
        if key in industry:
            if key in industry or any(k in industry for k in key):
                return script
    return '贵公司百度几乎无投放，客户找供应商第一站是百度，你们空白=客户流失给竞品。'

def get_todays_list(n=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get top customers per industry, balanced across priority sectors
    # Priority industries with quota per industry
    quotas = {
        '医疗器械': 3,
        '新材料化工': 2,
        '机械装备汽配': 2,
        '环保检测': 1,
        '建筑建材': 1,
        '口腔诊所': 1,
    }
    
    result = []
    for industry, quota in quotas.items():
        cur.execute('''
            SELECT id, name, industry, tier, phone, status, district
            FROM customers
            WHERE tier = 'A' AND status IN ('待联系', '需跟进')
              AND industry = ?
            ORDER BY 
                CASE WHEN phone != '' THEN 0 ELSE 1 END,
                id ASC
            LIMIT ?
        ''', (industry, quota))
        result.extend(cur.fetchall())
    
    conn.close()
    
    # If not enough, fill from other industries
    if len(result) < n:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            SELECT id, name, industry, tier, phone, status, district
            FROM customers
            WHERE tier = 'A' AND status IN ('待联系', '需跟进')
              AND industry NOT IN ('医疗器械', '新材料化工', '机械装备汽配', '环保检测', '建筑建材', '口腔诊所')
            ORDER BY 
                CASE WHEN phone != '' THEN 0 ELSE 1 END,
                id ASC
            LIMIT ?
        ''', (n - len(result),))
        result.extend(cur.fetchall())
        conn.close()
    
    return result[:n]

if __name__ == '__main__':
    rows = get_todays_list(10)
    today = date.today().strftime('%Y-%m-%d')
    
    print(f'[今日拨打清单] 百都科技 ({today})')
    print(f'共找到 {len(rows)} 家待联系A类客户\n')
    print(f'{"序号":>4} | {"企业名称":<32} | {"行业":<12} | {"电话":<14} | 话术摘要')
    print('-' * 115)
    for i, (cid, name, industry, tier, phone, status, district) in enumerate(rows, 1):
        script = get_script(industry)
        phone_str = phone[:7] + '****' if phone and len(phone) > 7 else (phone or '-')
        name_display = name[:30] if len(name) > 30 else name
        ind_display = industry[:10] if len(industry) > 10 else industry
        print(f'{i:>4} | {name_display:<32} | {ind_display:<12} | {phone_str:<14} | {script}')
    
    print(f'\n[策略] 优先医疗器械/新材料/机械装备(Tier 1-3主战场)')
    print(f'[提醒] 拨打前30秒侦察:企查查查背景+百度搜公司名看排名+搜行业词+重庆看竞品')
    
    # Save JSON
    import json
    result = []
    for i, (cid, name, industry, tier, phone, status, district) in enumerate(rows, 1):
        result.append({
            'seq': i, 'id': cid, 'name': name, 'industry': industry,
            'phone': phone, 'district': district, 'status': status,
            'script': get_script(industry)
        })
    
    out_path = 'data/today_call_list.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'date': today, 'count': len(result), 'customers': result}, f, ensure_ascii=False, indent=2)
    print(f'\n[已保存] {out_path}')
