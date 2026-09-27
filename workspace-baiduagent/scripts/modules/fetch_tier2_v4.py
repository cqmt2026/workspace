# -*- coding: utf-8 -*-
"""
第二梯队数据抓取 v4：一次性完成全部6个行业
"""
import sys, os, time, re, csv, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

INDUSTRY_KWS = {
    '医疗器械': ['医疗','器械','制药','生物','检验','诊断','仪器','设备','医学','医院','口腔'],
    '新材料化工': ['材料','化工','新材','塑料','塑胶','胶粘','合金','钛','镁','纤维','节能','保温','防水'],
    '机械装备汽配': ['机械','装备','模具','汽配','汽车','零部件','起重','液压','润滑','自动化','传动','机床','金属','铸造'],
    '环保检测': ['环保','检测','清洁','水处理','净化','环境','废气','废水'],
    '建筑建材': ['建材','装饰','建筑','钢结构','混凝土','保温','防水','幕墙','门窗','陶瓷'],
    '新能源充电电力': ['新能源','充电','电力','电气','光伏','储能','电池','电网'],
}

def read_sp_names():
    names = []
    with open('assets/重庆专精特新企业全名单_2275家.md', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^\d+\.\s+(.+)$', line.strip())
            if m:
                names.append(m.group(1).strip())
    return names

def classify_name(name):
    name_clean = re.sub(r'[（）\(\)\[\]【】\u300a\u300b]','',name)
    for ind, kws in INDUSTRY_KWS.items():
        for kw in kws:
            if kw in name_clean:
                return ind
    return None

def fetch_one(name, industry, session):
    try:
        params = {
            'keywords': name, 'city': '重庆',
            'offset': 1, 'page': 1, 'key': KEY, 'extensions': 'all',
        }
        r = session.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == '1' and d.get('pois'):
            item = d['pois'][0]
            return {
                '区域': item.get('adname',''),
                '机构名称': item.get('name', name),
                '地址': item.get('address',''),
                '电话': item.get('tel',''),
                '机构类别': industry,
                'adname': item.get('adname',''),
                '经度': item.get('lon',''),
                '纬度': item.get('lat',''),
                '数据来源': '高德POI+专精特新',
                '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
            }
        return None
    except:
        return None

def main():
    print("=== 第二梯队数据抓取 v4 ===")
    
    sp_names = read_sp_names()
    classified = {}
    for name in sp_names:
        ind = classify_name(name)
        if ind:
            classified.setdefault(ind, []).append(name)
    
    print(f"总专精特新: {len(sp_names)} 家")
    for ind, names in sorted(classified.items(), key=lambda x: -len(x[1])):
        print(f"  {ind}: {len(names)} 家")
    
    # 跳过机械装备汽配（已有165条）
    skip_ind = '机械装备汽配'
    
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    all_results = []
    
    # 先加载已有的机械装备汽配数据
    jxzb_path = 'data/master/机械装备汽配_sp.csv'
    if os.path.exists(jxzb_path):
        with open(jxzb_path, encoding='utf-8-sig') as f:
            existing = list(csv.DictReader(f))
        all_results.extend(existing)
        print(f"\n已加载机械装备汽配: {len(existing)} 条")
    
    import requests
    with requests.Session() as session:
        for ind, names in classified.items():
            if ind == skip_ind:
                continue
            print(f"\n--- {ind}: 开始搜索 {len(names)} 家 ---")
            batch_results = []
            matched = 0
            unmatched = 0
            
            batch_size = 20
            for i in range(0, len(names), batch_size):
                batch = names[i:i+batch_size]
                with ThreadPoolExecutor(max_workers=min(15, len(batch))) as executor:
                    futs = {executor.submit(fetch_one, name, ind, session): name for name in batch}
                    for fut in as_completed(futs):
                        result = fut.result()
                        if result:
                            batch_results.append(result)
                            matched += 1
                        else:
                            unmatched += 1
                processed = min(i+batch_size, len(names))
                print(f"  {ind}: {processed}/{len(names)}, 匹配{matched}, 未匹配{unmatched}")
            
            all_results.extend(batch_results)
            print(f"  [完成] {ind}: 匹配{matched}/{len(names)}")
    
    # 保存各行业的CSV
    by_industry = {}
    for r in all_results:
        by_industry.setdefault(r['机构类别'], []).append(r)
    
    total_saved = 0
    for ind, items in by_industry.items():
        safe_name = ind.replace('/','_').replace(' ','_')
        out_path = os.path.join('data', 'master', f'{safe_name}_sp.csv')
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        print(f"  [{ind}] {len(items)} 条 → {out_path}")
        total_saved += len(items)
    
    # 保存汇总
    master_path = os.path.join('data', 'master', 'tier2_all_sp.csv')
    with open(master_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n=== 汇总 ===")
    print(f"第二梯队总计: {total_saved} 条")
    for ind, items in sorted(by_industry.items(), key=lambda x: -len(x[1])):
        print(f"  {ind}: {len(items)} 条")

if __name__ == '__main__':
    main()
