# -*- coding: utf-8 -*-
"""
第二梯队行业数据抓取
目标：医疗器械、新材料化工、机械装备汽配、环保检测、建筑建材、新能源充电电力
数据来源：高德地图POI API（重庆主城区9区）
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'

# 定义抓取参数
INDUSTRIES = {
    'ylqy': {
        'keywords': '医疗器械',
        'category_name': '医疗器械',
        'save_name': 'ylqy_list_chongqing_latest',
        'pages': 60,  # 最多60页×500条=30000
    },
    'xincai': {
        'keywords': '新材料',
        'category_name': '新材料化工',
        'save_name': 'xc_list_chongqing_latest',
        'pages': 60,
    },
    'jxzb': {
        'keywords': '机械装备',
        'category_name': '机械装备汽配',
        'save_name': 'jxzb_list_chongqing_latest',
        'pages': 60,
    },
    'hbjc': {
        'keywords': '环保检测',
        'category_name': '环保检测',
        'save_name': 'hbjc_list_chongqing_latest',
        'pages': 60,
    },
    'jzjc': {
        'keywords': '建筑材料',
        'category_name': '建筑建材',
        'save_name': 'jzjc_list_chongqing_latest',
        'pages': 60,
    },
    'xny': {
        'keywords': '充电桩',
        'category_name': '新能源充电电力',
        'save_name': 'xny_list_chongqing_latest',
        'pages': 30,
    },
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_poi(keywords, page=1, offset=500):
    """从高德POI搜索一页数据"""
    params = {
        'keywords': keywords,
        'city': '重庆',
        'offset': offset,
        'page': page,
        'key': KEY,
        'extensions': 'all',
        'area_limit': 0,  # 不限制行政区，自己过滤
    }
    try:
        r = requests.get(BASE, params=params, timeout=15, headers=HEADERS)
        d = r.json()
        if d.get('status') == '1':
            return d
        else:
            print(f"  [ERROR] API error: {d.get('info')}")
            return None
    except Exception as e:
        print(f"  [ERROR] Request failed: {e}")
        return None

def filter_main_urban(item):
    """过滤主城区9区"""
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    adname = item.get('adname','')
    for d in districts:
        if d in adname:
            return True
    return False

def process_industry(cfg):
    """抓取一个行业的所有数据"""
    print(f"\n{'='*60}")
    print(f"开始抓取: {cfg['keywords']} ({cfg['category_name']})")
    
    all_items = []
    seen_names = set()
    
    for page in range(1, cfg['pages']+1):
        d = fetch_poi(cfg['keywords'], page=page)
        if not d or not d.get('pois'):
            if page == 1:
                print(f"  [WARN] 无数据，可能无此行业")
            break
        
        pois = d['pois']
        page_count = len(pois)
        new_count = 0
        
        for item in pois:
            name = item.get('name','').strip()
            if not name:
                continue
            # 去重
            if name in seen_names:
                continue
            seen_names.add(name)
            
            # 过滤主城区
            if not filter_main_urban(item):
                continue
            
            tel = item.get('tel','')
            addr = item.get('address','')
            adname = item.get('adname','')
            lat = item.get('lat','')
            lon = item.get('lon','')
            
            all_items.append({
                '区域': adname,
                '机构名称': name,
                '地址': addr,
                '电话': tel,
                '机构类别': cfg['category_name'],
                'adname': adname,
                '经度': lon,
                '纬度': lat,
                '数据来源': '高德POI',
                '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
            })
            new_count += 1
        
        total_so_far = len(all_items)
        print(f"  第{page}页: {page_count}条, 新增{new_count}条(主城区), 累计{total_so_far}条")
        
        # 如果没有新数据，停止
        if page_count < 10 and new_count == 0:
            print(f"  [INFO] 数据已采集完，停止")
            break
        
        time.sleep(0.3)  # 请求间隔
    
    # 保存
    out_path = os.path.join('data', 'master', f"{cfg['save_name']}.csv")
    os.makedirs('data/master', exist_ok=True)
    
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    
    print(f"  [OK] 已保存 {len(all_items)} 条 → {out_path}")
    return len(all_items)

def main():
    print("第二梯队行业数据抓取")
    print(f"关键词覆盖: {list(INDUSTRIES.values())}")
    
    results = {}
    for key, cfg in INDUSTRIES.items():
        count = process_industry(cfg)
        results[key] = count
    
    print(f"\n{'='*60}")
    print("抓取汇总:")
    total = 0
    for key, count in results.items():
        print(f"  {key}: {count} 条")
        total += count
    print(f"  总计: {total} 条")

if __name__ == '__main__':
    main()
