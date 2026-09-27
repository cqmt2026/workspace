# -*- coding: utf-8 -*-
"""
第二梯队数据抓取 v3：多线程+高德POI搜索
目标：医疗器械、新材料化工、机械装备汽配、环保检测、建筑建材、新能源充电电力
创建: 2026-08-29 | 作者: 小度
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

def filter_main_urban(adname):
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    return any(d in adname for d in districts)

def fetch_one(name, session):
    """单个企业POI搜索"""
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
                '机构类别': '',  # 由调用方设置
                'adname': item.get('adname',''),
                '经度': item.get('lon',''),
                '纬度': item.get('lat',''),
                '数据来源': '高德POI+专精特新',
                '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                'matched': True,
            }
        return {'matched': False}
    except:
        return {'matched': False}

def main():
    print("=== 第二梯队数据抓取 v3 (多线程) ===")
    
    # 1. 读取并分类专精特新名单
    sp_names = read_sp_names()
    classified = {}
    for name in sp_names:
        ind = classify_name(name)
        if ind:
            classified.setdefault(ind, []).append(name)
    
    print(f"总专精特新: {len(sp_names)} 家")
    for ind, names in sorted(classified.items(), key=lambda x: -len(x[1])):
        print(f"  {ind}: {len(names)} 家")
    
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    all_results = []
    total_matched = 0
    total_unmatched = 0
    
    # 2. 每个行业用线程池批量搜索
    with requests.Session() as session:
        for ind, names in classified.items():
            print(f"\n--- {ind}: 开始搜索 {len(names)} 家 ---")
            batch_results = []
            matched = 0
            unmatched = 0
            
            # 分批处理，每批20个并发
            batch_size = 20
            for i in range(0, len(names), batch_size):
                batch = names[i:i+batch_size]
                futures = {session: (i, name) for i, name in enumerate(batch)}
                
                # 用线程池
                with ThreadPoolExecutor(max_workers=min(15, len(batch))) as executor:
                    futs = {executor.submit(fetch_one, name, session): name for name in batch}
                    for fut in as_completed(futs):
                        result = fut.result()
                        if result['matched']:
                            result['机构类别'] = ind
                            batch_results.append(result)
                            matched += 1
                        else:
                            unmatched += 1
                
                # 进度报告
                processed = min(i+batch_size, len(names))
                print(f"  {ind}: {processed}/{len(names)}, 匹配{matched}, 未匹配{unmatched}")
            
            all_results.extend(batch_results)
            total_matched += matched
            total_unmatched += unmatched
            print(f"  [完成] {ind}: 匹配{matched}/{len(names)}")
    
    # 3. 保存
    by_industry = {}
    for r in all_results:
        by_industry.setdefault(r['机构类别'], []).append(r)
    
    os.makedirs('data/master', exist_ok=True)
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
    
    # 汇总
    master_path = os.path.join('data', 'master', 'tier2_all_sp.csv')
    with open(master_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n=== 汇总 ===")
    print(f"总匹配: {total_matched}/{total_matched+total_unmatched}")
    print(f"保存到: {master_path}")

if __name__ == '__main__':
    main()
