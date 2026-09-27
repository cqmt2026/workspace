# -*- coding: utf-8 -*-
"""百度紧急补抓 - 剩余低覆盖率行业"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

URGENT = {
    '检验检测': ['检测公司','质检','质量检测','检测机构','环境检测','食品检测'],
    '智能制造': ['智能制造','智能装备','工业机器人','自动化设备','智能工厂'],
    '食品加工': ['食品公司','食品加工','食品科技','饮料制造','糕点制造','调味品'],
    '广告传媒': ['广告公司','传媒公司','营销策划','品牌设计','网络推广'],
}

def fetch_all_pages(kw, page_size=20, max_pages=8):
    all_results = []
    seen = set()
    for page in range(max_pages):
        params = {
            'query': kw, 'region': '重庆', 'output': 'json',
            'ak': AK, 'page_size': page_size, 'page_num': page, 'scope': 2,
        }
        try:
            r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
            d = r.json()
            if d.get('status') != 0:
                print(f'    err: {d.get("info")}')
                break
            results = d.get('results', [])
            if not results:
                break
            new_count = 0
            for item in results:
                name = item.get('name', '').strip()
                if not name or name in seen:
                    continue
                area = item.get('area', '')
                if not any(d in area for d in districts):
                    continue
                seen.add(name)
                loc = item.get('location', {})
                all_results.append({
                    '区域': area,
                    '机构名称': name,
                    '地址': item.get('address', ''),
                    '电话': item.get('telephone') or '',
                    '机构类别': '',
                    '经度': loc.get('lng', ''),
                    '纬度': loc.get('lat', ''),
                    '数据来源': '百度地图POI',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
                new_count += 1
            print(f'    {kw} p{page}: +{new_count} (总{len(all_results)})')
            time.sleep(0.12)
            if new_count == 0:
                break
        except Exception as e:
            print(f'    error: {e}')
            break
    return all_results

def main():
    all_items = []
    for industry, kws in URGENT.items():
        print(f'\n=== {industry} ===')
        for kw in kws:
            items = fetch_all_pages(kw, max_pages=5)
            for item in items:
                item['机构类别'] = industry
            all_items.extend(items)
        count = sum(1 for i in all_items if i['机构类别'] == industry)
        phone_count = sum(1 for i in all_items if i['机构类别'] == industry and i['电话'])
        pct = round(phone_count/count*100,1) if count > 0 else 0
        print(f'  [{industry}] 累计: {count}条, 有电话{phone_count}条({pct}%)')
    
    out = os.path.join('data', 'master', 'urgent_batch2_baidu.csv')
    fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间']
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    print(f'\n总计: {len(all_items)} 条 -> {out}')
    
    from collections import Counter
    cnt = Counter(i['机构类别'] for i in all_items)
    for ind, c in cnt.most_common():
        pc = sum(1 for i in all_items if i['机构类别']==ind and i['电话'])
        print(f'  {ind}: {c}条, 电话{pc}条({round(pc/c*100,1)}%)')

if __name__ == '__main__':
    main()
