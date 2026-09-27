# -*- coding: utf-8 -*-
"""第二梯队扩展抓取v6：覆盖重庆全域+细分类关键词"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 细分关键词 - 每个行业多个搜索词
INDUSTRIES = {
    '医疗器械': ['医疗器械','制药企业','生物制药','医疗器械公司','检验设备','诊断仪器','医疗仪器','医用材料','生物医药企业'],
    '新材料化工': ['新材料','化工企业','塑料制品','塑胶制品','胶粘剂','合金材料','钛合金','镁合金','纤维材料','节能材料','保温材料'],
    '机械装备汽配': ['机械设备','模具制造','汽车配件','汽车零部件','起重设备','液压设备','润滑设备','自动化设备','金属加工','铸造企业','机床设备','传动设备'],
    '环保检测': ['环保设备','检测公司','清洁用品','水处理设备','环境工程','空气净化','废气处理','环境监测'],
    '建筑建材': ['建筑材料','装饰材料','钢结构','混凝土','保温材料','防水工程','幕墙工程','陶瓷建材','建材公司'],
    '新能源充电电力': ['充电桩','新能源科技','电力设备','电气设备','光伏发电','储能设备','电池制造','电网设备','电气公司'],
}

def fetch_all_poi(keyword, max_pages=50):
    """获取关键词所有POI数据（不限区域）"""
    all_pois = []
    for page in range(1, max_pages+1):
        params = {
            'keywords': keyword, 'city': '重庆',
            'offset': 500, 'page': page,
            'key': KEY, 'extensions': 'all', 'area_limit': 0,
        }
        try:
            r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
            d = r.json()
            if d.get('status') != '1' or not d.get('pois'):
                break
            all_pois.extend(d['pois'])
            if len(d['pois']) < 50:
                break
            time.sleep(0.15)
        except:
            break
    return all_pois

def main():
    print("=== 第二梯队扩展抓取（重庆全域） ===")
    
    all_results = []
    seen_names = set()
    
    for industry, keywords in INDUSTRIES.items():
        print(f"\n--- {industry} ---")
        industry_results = []
        
        for kw in keywords:
            print(f"  关键词: {kw}", end=' ')
            pois = fetch_all_poi(kw, max_pages=30)
            print(f"获取{len(pois)}条")
            
            for item in pois:
                name = item.get('name','').strip()
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                
                tel = item.get('tel','')
                industry_results.append({
                    '区域': item.get('adname',''),
                    '机构名称': name,
                    '地址': item.get('address',''),
                    '电话': tel,
                    '机构类别': industry,
                    'adname': item.get('adname',''),
                    '经度': item.get('lon',''),
                    '纬度': item.get('lat',''),
                    '数据来源': '高德POI(全域)',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
        
        print(f"  [{industry}] 去重后: {len(industry_results)} 条")
        all_results.extend(industry_results)
    
    # 保存
    os.makedirs('data/master', exist_ok=True)
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    
    # 按行业保存
    from collections import defaultdict
    by_industry = defaultdict(list)
    for r in all_results:
        by_industry[r['机构类别']].append(r)
    
    total_saved = 0
    for ind, items in by_industry.items():
        safe_name = ind.replace('/','_').replace(' ','_')
        out_path = os.path.join('data', 'master', f'{safe_name}_full.csv')
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        print(f"  [{ind}] {len(items)} 条 → {out_path}")
        total_saved += len(items)
    
    # 汇总
    master_path = os.path.join('data', 'master', 'tier2_full.csv')
    with open(master_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n=== 汇总 ===")
    print(f"第二梯队总计: {total_saved} 条")
    print(f"总去重企业: {len(seen_names)} 家")

if __name__ == '__main__':
    main()
