# -*- coding: utf-8 -*-
"""
百度POI补抓脚本
按行业优先级补抓电话和坐标数据
"""
import sys
import os
import json
import time
import requests
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# 百度地图API Key
BD_MAP_KEY = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'

# 补抓行业配置（按优先级排序）
INDUSTRY_CONFIG = [
    {'name': '创新型中小企业', 'query': '重庆 创新型中小企业', 'priority': 'P0', 'target_count': 200},
    {'name': '人力资源', 'query': '重庆 人力资源公司', 'priority': 'P0', 'target_count': 150},
    {'name': '物流货运', 'query': '重庆 物流公司', 'priority': 'P0', 'target_count': 200},
    {'name': '软件信息', 'query': '重庆 软件开发', 'priority': 'P1', 'target_count': 150},
    {'name': '智能制造', 'query': '重庆 智能制造', 'priority': 'P1', 'target_count': 100},
    {'name': '检验检测', 'query': '重庆 检测公司', 'priority': 'P1', 'target_count': 100},
    {'name': '医疗器械', 'query': '重庆 医疗器械', 'priority': 'P1', 'target_count': 200},
    {'name': '环保检测', 'query': '重庆 环保检测', 'priority': 'P2', 'target_count': 100},
    {'name': '新材料化工', 'query': '重庆 新材料', 'priority': 'P2', 'target_count': 150},
    {'name': '机械装备汽配', 'query': '重庆 机械设备', 'priority': 'P2', 'target_count': 200},
]

# 重庆主城区坐标和半径
CHONGQING_CENTER = {'lat': 29.563017, 'lng': 106.551557}
CHONGQING_RADIUS = 50000  # 50公里半径覆盖主城区

def search_baidu_poi(query, city='重庆', radius=50000, location=None, page_num=0, page_size=20):
    """搜索百度POI"""
    if not location:
        location = f"{CHONGQING_CENTER['lng']},{CHONGQING_CENTER['lat']}"
    
    url = 'https://api.map.baidu.com/place/v2/search'
    params = {
        'query': query,
        'region': city,
        'output': 'json',
        'ak': BD_MAP_KEY,
        'page_size': page_size,
        'page_num': page_num,
        'scope': 2,
        'region_fix': 1
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('status') == 0:
            return data.get('results', [])
        else:
            print(f"  ⚠️ API错误: {data.get('message', '未知错误')}")
            return []
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return []

def parse_poi_result(result):
    """解析POI结果"""
    try:
        name = result.get('name', '')
        tel = result.get('telephone', '')
        addr = result.get('address', '')
        area = result.get('area', '')
        city = result.get('city', '')
        
        # 解析经纬度
        location = result.get('location', {})
        lng = location.get('lng', '')
        lat = location.get('lat', '')
        
        # 提取区域（从地址中）
        district = ''
        if addr:
            # 简单提取区域
            districts = ['渝中区', '江北区', '沙坪坝区', '九龙坡区', '南岸区', 
                        '渝北区', '北碚区', '大渡口区', '巴南区', '重庆高新区',
                        '两江新区']
            for d in districts:
                if d in addr:
                    district = d.replace('重庆', '').replace('市', '')
                    break
        
        return {
            'name': name,
            'phone': tel,
            'address': addr,
            'district': district,
            'industry': '',  # 由调用者填充
            'lng': lng,
            'lat': lat,
            'source': '百度POI补抓',
            'tier': ''  # 后续分配
        }
    except Exception as e:
        print(f"  ❌ 解析错误: {e}")
        return None

def get_industry_from_query(query):
    """从查询词中提取行业名称"""
    # 简单映射
    query_map = {
        '创新型中小企业': '创新型中小企业',
        '人力资源': '人力资源',
        '物流': '物流货运',
        '软件开发': '软件信息',
        '智能制造': '智能制造',
        '检测': '检验检测',
        '医疗器械': '医疗器械',
        '环保检测': '环保检测',
        '新材料': '新材料化工',
        '机械设备': '机械装备汽配',
    }
    
    for key, industry in query_map.items():
        if key in query:
            return industry
    return '其他'

def fetch_industry(industry_config, existing_phones=None):
    """抓取单个行业数据"""
    print(f"\n{'='*60}")
    print(f"📊 开始补抓: {industry_config['name']} (优先级: {industry_config['priority']})")
    print(f"   目标数量: {industry_config['target_count']}")
    print(f"{'='*60}")
    
    results = []
    page_num = 0
    max_pages = 10  # 最多抓取10页（200条）
    
    while len(results) < industry_config['target_count'] and page_num < max_pages:
        print(f"  正在抓取第 {page_num + 1} 页...")
        
        pois = search_baidu_poi(
            industry_config['query'],
            page_num=page_num,
            page_size=20
        )
        
        if not pois:
            print(f"  ⚠️ 无更多数据，停止抓取")
            break
        
        for poi in pois:
            if len(results) >= industry_config['target_count']:
                break
            
            parsed = parse_poi_result(poi)
            if parsed:
                parsed['industry'] = get_industry_from_query(industry_config['query'])
                
                # 过滤掉已有电话的数据（如果提供）
                if existing_phones:
                    if parsed['phone'] in existing_phones:
                        continue
                
                results.append(parsed)
        
        page_num += 1
        time.sleep(0.5)  # 避免请求过快
    
    print(f"  ✅ 抓取完成: 共 {len(results)} 条")
    return results

def save_to_db(results, industry_name):
    """保存数据到数据库"""
    conn = sqlite3.connect('data/baidu_crm.db')
    c = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for r in results:
        # 检查是否已存在
        c.execute('SELECT id FROM customers WHERE name = ?', (r['name'],))
        existing = c.fetchone()
        
        if existing:
            # 更新现有记录
            c.execute('''
                UPDATE customers 
                SET phone = ?, district = ?, lat = ?, lng = ?, 
                    source = ?, updated_at = ?
                WHERE id = ?
            ''', (
                r['phone'], r['district'], r['lat'], r['lng'],
                r['source'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                existing[0]
            ))
            updated += 1
        else:
            # 插入新记录
            c.execute('''
                INSERT INTO customers 
                (name, industry, tier, phone, contact, source, status, 
                 address, district, lat, lng, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, '待联系', ?, ?, ?, ?, ?, ?, ?)
            ''', (
                r['name'], r['industry'], '', r['phone'], '', r['source'],
                r['address'], r['district'], r['lat'], r['lng'], '',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            inserted += 1
    
    conn.commit()
    conn.close()
    
    print(f"  💾 数据库更新: 新增 {inserted} 条, 更新 {updated} 条")
    return inserted, updated

def main():
    print('=' * 70)
    print('【百度POI补抓工具】')
    print(f'执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)
    
    # 获取现有电话列表（用于去重）
    conn = sqlite3.connect('data/baidu_crm.db')
    c = conn.cursor()
    c.execute('SELECT phone FROM customers WHERE phone IS NOT NULL AND phone != ""')
    existing_phones = set(row[0] for row in c.fetchall())
    conn.close()
    print(f"📊 现有有电话客户: {len(existing_phones)} 条")
    
    # 选择要抓取的行业
    # 默认抓取P0行业（创新型中小企业）
    target_industries = [ind for ind in INDUSTRY_CONFIG if ind['priority'] == 'P0']
    
    if not target_industries:
        print("❌ 未找到P0行业配置")
        return
    
    print(f"\n🎯 本次补抓行业: {[ind['name'] for ind in target_industries]}")
    
    # 执行补抓
    all_results = []
    for ind_config in target_industries:
        results = fetch_industry(ind_config, existing_phones)
        all_results.extend(results)
        
        # 保存到数据库
        if results:
            save_to_db(results, ind_config['name'])
        
        # 保存详细数据
        output_file = f'data/source/baidu_poi_{ind_config["name"]}_{datetime.now().strftime("%Y%m%d")}.json'
        os.makedirs('data/source', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  💾 详细数据已保存: {output_file}")
    
    # 汇总统计
    print(f"\n{'='*60}")
    print('【补抓汇总】')
    print(f'  总抓取数: {len(all_results)}')
    print(f'  有电话数: {sum(1 for r in all_results if r["phone"])}')
    print(f'  有坐标数: {sum(1 for r in all_results if r["lat"] and r["lng"])}')
    print(f'  有区域数: {sum(1 for r in all_results if r["district"])}')
    print(f'{'='*60}')

if __name__ == '__main__':
    main()
