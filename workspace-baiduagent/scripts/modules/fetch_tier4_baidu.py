# -*- coding: utf-8 -*-
"""
第四梯队行业数据抓取 - 百度地图地点检索API
数据来源：百度地图POI (place/v2/search)
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

INDUSTRIES = {
    '财税服务': ['财务公司','会计服务','税务师事务所','代理记账','财税咨询','会计师事务所'],
    '法律服务': ['律师事务所','法律咨询','法务公司','知识产权'],
    '人力资源': ['人力资源','劳务派遣','猎头','人才招聘','企业管理咨询'],
    '电子科技': ['电子科技','半导体','集成电路','电子元件','电子产品制造','光电科技'],
    '医疗健康': ['体检中心','健康管理','康复医疗','养老机构','月子中心','康养'],
    '酒店餐饮': ['酒店','餐饮管理','连锁餐饮','火锅','西餐厅','中餐','宴会酒店'],
    '教育培训补充': ['职业培训','技能培训','驾校','成人教育','在线教育','学历教育'],
    '机械设备补充': ['工业设备','包装机械','食品机械','制药机械','印刷设备'],
    '能源环保补充': ['石油化工','天然气','煤炭','能源科技','节能科技'],
    '商贸批发': ['批发市场','商贸公司','贸易公司','进出口','供应链管理'],
}

def filter_main_urban(area):
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    return any(d in area for d in districts)

def fetch_poi(keyword, page_num=0, page_size=20):
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

def process_industry(cfg_name, keywords):
    print(f"\n{'='*50}")
    print(f"行业: {cfg_name}")
    
    all_items = []
    seen_names = set()
    
    for kw in keywords:
        print(f"  关键词: {kw}", end=' ')
        page = 0
        stop_cnt = 0
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
    
    print(f"  [完成] {cfg_name}: {len(all_items)} 条 → {out_path}")
    return len(all_items)

def main():
    print("=== 第四梯队数据抓取（百度地图POI） ===")
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