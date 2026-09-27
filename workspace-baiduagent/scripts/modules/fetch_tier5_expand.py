# -*- coding: utf-8 -*-
"""
第五梯队：扩展抓取 - 用更宽泛关键词+区县不限
目标：财税、法律、人力资源、电子科技、商贸批发等百度POI覆盖不足的行业
策略：放宽区域限制+换关键词
"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 放宽区域限制 - 不过滤主城9区，全部重庆数据
def fetch_poi_all(keyword, page_num=0, page_size=20):
    params = {
        'query': keyword,
        'region': '重庆',
        'output': 'json',
        'ak': AK,
        'page_size': page_size,
        'page_num': page_num,
        'scope': 2,
    }
    try:
        r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == 0:
            return d.get('results', []), d.get('total', 0)
        return [], 0
    except:
        return [], 0

INDUSTRIES = {
    '财税服务': ['会计', '财务', '税务师', '代理记账', '审计'],
    '法律服务': ['律师', '法务', '知识产权', '公证处'],
    '人力资源': ['人力资源公司', '劳务派遣', '猎头公司', '人才市场'],
    '电子科技': ['电子', '半导体', '光电', '芯片', '微电子'],
    '商贸批发': ['贸易', '批发', '进出口', '供应链'],
    '物流仓储': ['仓储', '仓库', '物流园', '货运站'],
}

def process_industry(cfg_name, keywords, filter_main=True):
    print(f"\n{'='*50}")
    print(f"行业: {cfg_name}")
    
    all_items = []
    seen_names = set()
    
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    
    for kw in keywords:
        print(f"  关键词: {kw}", end=' ')
        page = 0
        stop_cnt = 0
        while True:
            results, total = fetch_poi_all(kw, page_num=page, page_size=20)
            if not results:
                break
            
            page_new = 0
            for item in results:
                name = item.get('name','').strip()
                if not name or name in seen_names:
                    continue
                area = item.get('area','')
                if filter_main and not any(d in area for d in districts):
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
                    '数据来源': '百度地图POI(全域)',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
                page_new += 1
            
            if not results or page >= (total // 20):
                break
            if page_new == 0:
                stop_cnt += 1
                if stop_cnt >= 3:
                    break
            else:
                stop_cnt = 0
            page += 1
            time.sleep(0.12)
        
        print(f"累计{len(all_items)}条")
    
    out_path = os.path.join('data', 'master', f"{cfg_name}_baidu.csv")
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    
    print(f"  [完成] {cfg_name}: {len(all_items)} 条")
    return len(all_items)

def main():
    print("=== 第五梯队：扩展抓取（放宽区域限制） ===")
    results = {}
    for name, keywords in INDUSTRIES.items():
        count = process_industry(name, keywords, filter_main=False)
        results[name] = count
    print(f"\n总计: {sum(results.values())} 条")

if __name__ == '__main__':
    main()