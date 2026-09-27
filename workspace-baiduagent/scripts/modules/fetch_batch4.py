# -*- coding: utf-8 -*-
"""续抓第4批 - 继续用百度补充剩余行业"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

# 继续补抓 - 针对数量不够或覆盖率低的行业
TARGETS = {
    '新材料化工': ['新材料','化工材料','塑料制品','橡胶制品','胶粘剂','钛合金','镁合金','碳纤维','节能材料','保温材料'],
    '新能源充电': ['充电桩','充电站','新能源科技','储能设备','光伏','电池制造','电力设备','电气设备'],
    '酒店餐饮': ['酒店','餐饮管理','连锁餐饮','火锅','西餐厅','中餐','宴会酒店','酒楼'],
    '文化传媒': ['文化传播','广告制作','印刷厂','包装设计','会展服务','礼仪服务'],
    '房产中介': ['房地产中介','房产经纪','中介公司','置业顾问','房屋租赁'],
    '美容美发': ['美容美发','美发店','美容院','美甲','理发'],
    '健身瑜伽': ['健身房','健身会所','瑜伽馆','游泳馆','运动健身','健身工作室'],
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
                msg = d.get('info','')
                print(f'    err: {msg}')
                return all_results, msg
            results = d.get('results', [])
            if not results:
                break
            new_count = 0
            for item in results:
                name = item.get('name', '').strip()
                if not name or name in seen:
                    continue
                area = item.get('area', '')
                if not any(x in area for x in districts):
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
            time.sleep(0.15)
            if new_count == 0:
                break
        except Exception as e:
            print(f'    error: {e}')
            break
    return all_results, ''

def main():
    all_items = []
    quota_hit = False
    for industry, kws in TARGETS.items():
        print(f'\n=== {industry} ===')
        for kw in kws:
            if quota_hit:
                break
            items, err = fetch_all_pages(kw, max_pages=6)
            if err:
                quota_hit = True
                print(f'  配额限制，停止')
                break
            for item in items:
                item['机构类别'] = industry
            all_items.extend(items)
        count = sum(1 for i in all_items if i['机构类别'] == industry)
        phone = sum(1 for i in all_items if i['机构类别'] == industry and i['电话'])
        pct = round(phone/count*100,1) if count else 0
        print(f'  [{industry}] 累计: {count}条, 电话{phone}条({pct}%)')
    
    out = os.path.join('data', 'master', 'batch4_baidu.csv')
    fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间']
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    print(f'\n总计: {len(all_items)} 条 -> {out}')
    print(f'配额状态: {"已触发限制" if quota_hit else "正常"}')

if __name__ == '__main__':
    main()