# -*- coding: utf-8 -*-
"""
百度POI补抓 - 机械设备 + 新材料行业
"""
import sys
import requests
import json
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BD_MAP_KEY = '***'

def search_baidu_poi(query, page_num=0, page_size=20):
    """搜索百度POI"""
    url = 'https://api.map.baidu.com/place/v2/search'
    params = {
        'query': query,
        'region': '重庆',
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
            print(f"  API错误: {data.get('message', '未知')}")
            return []
    except Exception as e:
        print(f"  请求失败: {e}")
        return []

def parse_poi(result, industry):
    """解析POI结果"""
    name = result.get('name', '')
    tel = result.get('telephone', '')
    addr = result.get('address', '')
    area = result.get('area', '')
    location = result.get('location', {})
    lng = location.get('lng', '')
    lat = location.get('lat', '')
    
    return {
        'name': name,
        'phone': tel,
        'address': addr,
        'district': area,
        'industry': industry,
        'lng': lng,
        'lat': lat,
        'source': '百度POI补抓'
    }

def save_to_db(results):
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
    
    return inserted, updated

def fetch_industry(query_keywords, industry_name, max_pages=5):
    """抓取单个行业数据"""
    print(f"\n{'='*60}")
    print(f"📊 开始补抓: {industry_name}")
    print(f"{'='*60}")
    
    results = []
    seen_names = set()
    
    for keyword in query_keywords:
        print(f"\n搜索关键词: {keyword}")
        
        for page in range(max_pages):
            pois = search_baidu_poi(keyword, page_num=page, page_size=20)
            
            if not pois:
                break
            
            new_count = 0
            for poi in pois:
                parsed = parse_poi(poi, industry_name)
                
                # 去重
                if parsed['name'] in seen_names:
                    continue
                seen_names.add(parsed['name'])
                
                results.append(parsed)
                new_count += 1
            
            print(f"  第{page+1}页: {len(pois)}条 (新增{new_count}条)")
            
            if len(pois) < 20:
                break
    
    print(f"\n✅ {industry_name}共抓取: {len(results)}条")
    print(f"   有电话: {sum(1 for r in results if r['phone'])}条")
    print(f"   有坐标: {sum(1 for r in results if r['lat'] and r['lng'])}条")
    print(f"   有区域: {sum(1 for r in results if r['district'])}条")
    
    # 保存详细数据
    output_file = f'data/source/baidu_poi_{industry_name}_{datetime.now().strftime("%Y%m%d")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"💾 已保存: {output_file}")
    
    return results

def main():
    print('=' * 70)
    print('【百度POI补抓 - 机械设备 + 新材料】')
    print(f'执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)
    
    # 定义搜索关键词
    mechanical_keywords = [
        '重庆 机械设备',
        '重庆 机械制造',
        '重庆 金属加工',
        '重庆 精密机械',
        '重庆 机床',
        '重庆 注塑机',
        '重庆 数控机床'
    ]
    
    newmaterial_keywords = [
        '重庆 新材料',
        '重庆 化工材料',
        '重庆 复合材料',
        '重庆 环保材料',
        '重庆 塑胶材料',
        '重庆 建筑材料'
    ]
    
    # 抓取机械设备
    mechanical_results = fetch_industry(mechanical_keywords, '机械装备汽配', max_pages=5)
    
    # 抓取新材料
    newmaterial_results = fetch_industry(newmaterial_keywords, '新材料化工', max_pages=5)
    
    # 合并所有结果
    all_results = mechanical_results + newmaterial_results
    
    # 保存到数据库
    print(f"\n{'='*60}")
    print('💾 正在保存到数据库...')
    print(f"{'='*60}")
    
    inserted, updated = save_to_db(all_results)
    print(f"数据库更新: 新增 {inserted} 条, 更新 {updated} 条")
    
    # 汇总统计
    print(f"\n{'='*60}")
    print('【补抓汇总】')
    print(f"{'='*60}")
    print(f"总抓取数: {len(all_results)}")
    print(f"有电话数: {sum(1 for r in all_results if r['phone'])}")
    print(f"有坐标数: {sum(1 for r in all_results if r['lat'] and r['lng'])}")
    print(f"有区域数: {sum(1 for r in all_results if r['district'])}")
    print(f"新增入库: {inserted}条")
    print(f"更新已有: {updated}条")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
