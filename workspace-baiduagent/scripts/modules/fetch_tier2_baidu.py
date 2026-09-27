# -*- coding: utf-8 -*-
"""
第二梯队数据抓取 - 百度地图地点检索API
目标：医疗器械、新材料化工、机械装备汽配、环保检测、建筑建材、新能源充电电力
数据来源：百度地图POI (place/v2/search)
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 第二梯队行业 - 每个行业多个细分关键词
INDUSTRIES = {
    '医疗器械': ['医疗器械','制药','生物医药','医疗设备','医用材料','检验试剂','诊断试剂','医疗器械公司'],
    '新材料化工': ['新材料','化工材料','塑料制品','塑胶制品','胶粘剂','合金材料','钛合金','镁合金','纤维材料','节能材料','保温材料','防水材料'],
    '机械装备汽配': ['机械设备','模具制造','汽车配件','汽车零部件','起重设备','液压设备','润滑设备','自动化设备','金属加工','铸造','机床设备','传动设备','智能装备'],
    '环保检测': ['环保设备','环保科技','检测公司','环境检测','水处理','空气净化','废气处理','环境工程','环境监测'],
    '建筑建材': ['建筑材料','装饰材料','钢结构','混凝土','保温材料','防水工程','幕墙工程','陶瓷','建材科技'],
    '新能源充电电力': ['充电桩','新能源科技','储能设备','光伏','电池制造','电力设备','电气设备','电网'],
}

def filter_main_urban(area):
    """过滤主城区9区+高新区+两江新区"""
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    return any(d in area for d in districts)

def fetch_poi(keyword, page_num=0, page_size=20):
    """百度地图地点检索单页"""
    params = {
        'query': keyword,
        'region': '重庆',
        'output': 'json',
        'ak': AK,
        'page_size': page_size,
        'page_num': page_num,
        'scope': 2,  # 详细信息
    }
    try:
        r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == 0:
            return d.get('results', []), d.get('total', 0)
        return [], 0
    except:
        return [], 0

def process_industry(cfg_name, keywords):
    print(f"\n{'='*50}")
    print(f"行业: {cfg_name}")
    
    all_items = []
    seen_names = set()
    
    for kw in keywords:
        print(f"  关键词: {kw}", end=' ')
        page = 0
        while True:
            results, total = fetch_poi(kw, page_num=page, page_size=20)
            if not results:
                break
            
            page_new = 0
            for item in results:
                name = item.get('name','').strip()
                if not name:
                    continue
                if name in seen_names:
                    continue
                
                area = item.get('area','')
                if not filter_main_urban(area):
                    continue
                
                seen_names.add(name)
                loc = item.get('location', {})
                all_items.append({
                    '区域': area,
                    '机构名称': name,
                    '地址': item.get('address',''),
                    '电话': item.get('telephone') or '',
                    '机构类别': cfg_name,
                    'adname': area,
                    '经度': loc.get('lng',''),
                    '纬度': loc.get('lat',''),
                    '数据来源': '百度地图POI',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
                page_new += 1
            
            # 如果当前页新增为0或已达最后一页，停止
            if not results or page >= (total // 20):
                break
            if page_new == 0:
                # 连续3页无新增则停止（避免死循环）
                break
            page += 1
            time.sleep(0.15)
        
        print(f"累计{len(all_items)}条")
    
    # 保存
    out_path = os.path.join('data', 'master', f"{cfg_name}_baidu.csv")
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    
    print(f"  [完成] {cfg_name}: {len(all_items)} 条 → {out_path}")
    return len(all_items)

def main():
    print("=== 第二梯队数据抓取（百度地图POI） ===")
    
    results = {}
    for name, keywords in INDUSTRIES.items():
        count = process_industry(name, keywords)
        results[name] = count
    
    print(f"\n{'='*50}")
    print("抓取汇总:")
    total = 0
    for name, count in results.items():
        print(f"  {name}: {count} 条")
        total += count
    print(f"  总计: {total} 条")

if __name__ == '__main__':
    main()