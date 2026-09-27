# -*- coding: utf-8 -*-
"""百度批量补抓 - 多行业扩充电话与数量"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

# 补抓行业 - 聚焦低覆盖率+高价值
TARGETS = {
    '医疗卫生': ['医院','诊所','门诊部','社区卫生服务中心','体检中心'],
    '母婴亲子': ['母婴店','早教中心','亲子乐园','月子中心','儿童摄影','游泳馆'],
    '医疗器械': ['医疗器械','医疗设备','医用材料','检验试剂','生物医药','制药'],
    '装修装饰': ['装修公司','装饰公司','装潢','室内设计','家装','工装'],
    '教育培训': ['培训机构','教育机构','培训学校','艺术培训','舞蹈培训','书法培训'],
    '能源环保': ['环保公司','环保科技','环境工程','水处理','废气处理','节能科技'],
    '法律服务': ['律师事务所','法律咨询','法务','知识产权'],
    '商贸批发': ['批发市场','商贸公司','贸易公司','供应链','供应商'],
}

def fetch_all_pages(kw, page_size=20, max_pages=10):
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
                if 'QUOTA' in str(d) or 'LIMIT' in msg or msg:
                    print(f'    [配额/错误] {msg}')
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
            if err and ('LIMIT' in err or 'QUOTA' in err.upper()):
                quota_hit = True
                print(f'  ❌ 配额可能耗尽，停止')
                break
            for item in items:
                item['机构类别'] = industry
            all_items.extend(items)
        count = sum(1 for i in all_items if i['机构类别'] == industry)
        phone = sum(1 for i in all_items if i['机构类别'] == industry and i['电话'])
        pct = round(phone/count*100,1) if count else 0
        print(f'  [{industry}] 累计: {count}条, 电话{phone}条({pct}%)')
    
    out = os.path.join('data', 'master', 'batch3_baidu.csv')
    fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间']
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)
    print(f'\n总计: {len(all_items)} 条 -> {out}')
    print(f'配额状态: {"已触发限制" if quota_hit else "正常"}')

if __name__ == '__main__':
    main()