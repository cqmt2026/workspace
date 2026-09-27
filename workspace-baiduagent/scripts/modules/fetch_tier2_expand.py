# -*- coding: utf-8 -*-
"""
第二梯队数据抓取 v5：扩展关键词批量抓取高德POI
目标行业全量抓取（不限专精特新名单）
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, csv, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

KEY = '3f85cf…bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 每个行业定义多个细分关键词，覆盖更多企业
INDUSTRIES = {
    '医疗器械': {
        'keywords': ['医疗器械','制药','生物制药','医疗器械公司','检验设备','诊断仪器','医疗仪器','医用材料','生物医药'],
        'category': '医疗器械',
        'pages': 30,
    },
    '新材料化工': {
        'keywords': ['新材料','化工材料','塑料制品','塑胶制品','胶粘剂','合金材料','钛合金','镁合金','纤维材料','节能材料'],
        'category': '新材料化工',
        'pages': 30,
    },
    '机械装备汽配': {
        'keywords': ['机械设备','模具','汽车配件','汽车零部件','起重设备','液压设备','润滑设备','自动化设备','金属加工','铸造'],
        'category': '机械装备汽配',
        'pages': 40,
    },
    '环保检测': {
        'keywords': ['环保设备','检测公司','清洁用品','水处理设备','环境工程','空气净化','废气处理','环境监测'],
        'category': '环保检测',
        'pages': 30,
    },
    '建筑建材': {
        'keywords': ['建筑材料','装饰材料','钢结构','混凝土','保温材料','防水工程','幕墙工程','陶瓷建材'],
        'category': '建筑建材',
        'pages': 30,
    },
    '新能源充电电力': {
        'keywords': ['充电桩','新能源科技','电力设备','电气设备','光伏发电','储能设备','电池制造','电网设备'],
        'category': '新能源充电电力',
        'pages': 30,
    },
}

def fetch_poi(keyword, page, offset=500):
    params = {
        'keywords': keyword, 'city': '重庆',
        'offset': offset, 'page': page,
        'key': KEY, 'extensions': 'all', 'area_limit': 0,
    }
    try:
        r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == '1':
            return d.get('pois', [])
        return []
    except:
        return []

def filter_main_urban(adname):
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    return any(d in adname for d in districts)

def process_industry(cfg):
    print(f"\n{'='*50}")
    print(f"行业: {cfg['category']}")
    print(f"关键词: {cfg['keywords']}")
    
    all_items = []
    seen_names = set()
    total_found = 0
    
    for kw in cfg['keywords']:
        print(f"\n  关键词: {kw}")
        for page in range(1, cfg['pages']+1):
            pois = fetch_poi(kw, page)
            if not pois:
                break
            
            page_new = 0
            for item in pois:
                name = item.get('name','').strip()
                if not name:
                    continue
                if name in seen_names:
                    continue
                seen_names.add(name)
                
                adname = item.get('adname','')
                if not filter_main_urban(adname):
                    continue
                
                tel = item.get('tel','')
                all_items.append({
                    '区域': adname,
                    '机构名称': name,
                    '地址': item.get('address',''),
                    '电话': tel,
                    '机构类别': cfg['category'],
                    'adname': adname,
                    '经度': item.get('lon',''),
                    '纬度': item.get('lat',''),
                    '数据来源': '高德POI',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
                page_new += 1
                total_found += 1
            
            print(f"    第{page}页: {len(pois)}条, 新增{page_new}条(主城), 累计{total_found}条")
            if len(pois) < 10:
                break
            time.sleep(0.2)
    
    # 保存
    out_path = os.path.join('data', 'master', f"{cfg['category']}_expand.csv")
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    
    print(f"\n  [完成] {cfg['category']}: {len(all_items)} 条 → {out_path}")
    return len(all_items)

def main():
    print("=== 第二梯队数据扩展抓取 ===")
    
    results = {}
    for key, cfg in INDUSTRIES.items():
        count = process_industry(cfg)
        results[key] = count
    
    print(f"\n{'='*50}")
    print("抓取汇总:")
    total = 0
    for key, count in results.items():
        print(f"  {key}: {count} 条")
        total += count
    print(f"  总计: {total} 条")

if __name__ == '__main__':
    main()
