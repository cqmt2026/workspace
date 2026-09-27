# -*- coding: utf-8 -*-
"""
第三梯队行业数据抓取 - 百度地图地点检索API
目标：物流货运、智能制造、食品加工、家具家居、广告传媒、检验检测
数据来源：百度地图POI (place/v2/search)
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 第三梯队行业 - 每个行业多个细分关键词
INDUSTRIES = {
    '物流货运': ['物流公司','货运公司','仓储物流','冷链物流','国际物流','配送公司','快递物流','供应链'],
    '智能制造': ['智能制造','工业自动化','机器人','数控设备','精密制造','智能装备','工业互联网','物联网科技'],
    '食品加工': ['食品加工','食品公司','食品厂','饮料制造','食品科技','农产品加工','调味品','烘焙食品'],
    '家具家居': ['家具制造','家具公司','定制家具','家居建材','全屋定制','办公家具','软体家具','实木家具'],
    '广告传媒': ['广告公司','传媒公司','文化传媒','品牌策划','营销策划','广告传媒','公关公司','新媒体'],
    '检验检测': ['检验检测','检测机构','第三方检测','质检','计量检测','材料检测','环境检测','认证机构'],
    '软件信息': ['软件公司','信息技术','软件开发','大数据','人工智能','云计算','系统集成','网络安全'],
    '汽车服务': ['汽车维修','汽车美容','汽车保养','4S店','汽车配件','二手车','汽车租赁','汽修厂'],
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
                break
            page += 1
            time.sleep(0.12)
        
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
    print("=== 第三梯队数据抓取（百度地图POI） ===")
    
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