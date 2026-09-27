# -*- coding: utf-8 -*-
"""紧急补抓：人力资源/软件信息/物流货运"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

URGENT = {
    '人力资源': [
        '人力资源公司', '劳务派遣', '猎头公司', '人才市场',
        '企业管理咨询', '人事代理', '招聘服务', '职介所',
    ],
    '软件信息': [
        '软件公司', '软件研发', 'IT服务', '信息系统', '软件科技',
        '软件开发', '网络科技', '信息技术', '软件服务', '软件开发公司',
    ],
    '物流货运': [
        '物流公司', '货运公司', '物流园', '仓储物流', '快递公司',
        '货运代理', '运输公司', '物流企业', '公路货运', '专线物流',
    ],
}

def fetch_all_pages(kw, page_size=20, max_pages=10):
    """抓取最多max_pages页，返回所有结果"""
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
                    '机构类别': '',  # set later
                    '经度': loc.get('lng', ''),
                    '纬度': loc.get('lat', ''),
                    '数据来源': '百度地图POI',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
                new_count += 1
            print(f'    {kw} p{page}: +{new_count} new (总{len(all_results)})')
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
        print(f'  [{industry}] 累计: {len([i for i in all_items if i["机构类别"]==industry])} 条')
    
    out = os.path.join('data', 'master', 'urgent_baidu.csv')
    fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间']
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    print(f'\n总计: {len(all_items)} 条 -> {out}')
    
    # 按行业统计
    from collections import Counter
    cnt = Counter(i['机构类别'] for i in all_items)
    for ind, c in cnt.most_common():
        phone_cnt = sum(1 for i in all_items if i['机构类别']==ind and i['电话'])
        print(f'  {ind}: {c}条, 有电话{phone_cnt}条({round(phone_cnt/c*100,1)}%)')

if __name__ == '__main__':
    main()
