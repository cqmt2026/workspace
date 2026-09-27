# -*- coding: utf-8 -*-
"""
多渠道补充：用百度POI把专精特新缺口企业逐个搜索补电话
目标：把1768家未入库专精特新企业匹配上百度地图数据
创建: 2026-08-29
"""
import sys, os, time, re, csv, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BASE = 'https://api.map.baidu.com/place/v2/search'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

INDUSTRY_KWS = {
    '医疗器械': ['医疗','器械','制药','生物','医学','医药'],
    '新材料化工': ['材料','化工','新材','塑料','塑胶','合金','钛','镁','纤维'],
    '机械装备汽配': ['机械','装备','模具','汽配','汽车零','零部件','起重','液压','机床','金属','铸造','自动化'],
    '环保检测': ['环保','检测','清洁','水处理','净化','环境'],
    '建筑建材': ['建材','装饰','建筑','钢结构','混凝土','保温','幕墙'],
    '新能源充电电力': ['新能源','充电','电力','电气','光伏','储能','电池'],
    '软件IT': ['软件','科技','信息','大数据','人工智能','互联网','智能','数字'],
    '食品加工': ['食品','饮料','粮油','农产品','乳业','酿造'],
    '包装印刷': ['印刷','包装','印务'],
    '物流货运': ['物流','仓储','供应链','货运'],
    '电气设备': ['电气','电子','电器','仪器','仪表','机电'],
}

def classify(name):
    for ind, kws in INDUSTRY_KWS.items():
        for kw in kws:
            if kw in name:
                return ind
    return None

def read_all_names():
    names = []
    with open('assets/重庆专精特新企业全名单_2275家.md', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^\d+\.\s+(.+)$', line.strip())
            if m:
                names.append(m.group(1).strip())
    return names

def get_covered():
    import sqlite3
    conn = sqlite3.connect('data/baidu_crm.db')
    cur = conn.cursor()
    covered = set()
    cur.execute("SELECT name FROM customers")
    for (name,) in cur.fetchall():
        covered.add(name)
    conn.close()
    return covered

def fetch_one(name, session):
    try:
        clean = re.sub(r'[（）\(\)\[\]【】]', '', name)
        params = {
            'query': clean, 'region': '重庆', 'output': 'json',
            'ak': AK, 'page_size': 1, 'page_num': 0, 'scope': 2,
        }
        r = session.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == 0 and d.get('results'):
            item = d['results'][0]
            loc = item.get('location', {})
            return {
                '区域': item.get('area',''),
                '机构名称': item.get('name', name),
                '地址': item.get('address',''),
                '电话': item.get('telephone') or '',
                '机构类别': '',  # 由调用方填
                'adname': item.get('area',''),
                '经度': loc.get('lng',''),
                '纬度': loc.get('lat',''),
                '数据来源': '百度POI+专精特新',
                '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                'matched': True,
            }
        return {'matched': False, 'name': name}
    except:
        return {'matched': False, 'name': name}

def main():
    print("=== 专精特新缺口企业多渠道补充 ===")
    names = read_all_names()
    covered = get_covered()
    gap = [n for n in names if n not in covered]
    print(f"缺口企业: {len(gap)}家")
    
    # 分类
    classified = {}
    for n in gap:
        ind = classify(n)
        if ind:
            classified.setdefault(ind, []).append(n)
    
    print("缺口按行业:")
    for ind, lst in sorted(classified.items(), key=lambda x: -len(x[1])):
        print(f"  {ind}: {len(lst)}家")
    
    all_results = []
    matched = 0
    unmatched = 0
    
    with requests.Session() as session:
        for ind, names_list in classified.items():
            print(f"\n--- {ind}: {len(names_list)}家 ---")
            batch_results = []
            # 线程池
            with ThreadPoolExecutor(max_workers=12) as executor:
                futs = {executor.submit(fetch_one, name, session): name for name in names_list}
                for fut in as_completed(futs):
                    result = fut.result()
                    if result['matched']:
                        result['机构类别'] = ind
                        batch_results.append(result)
                        matched += 1
                    else:
                        unmatched += 1
            
            all_results.extend(batch_results)
            print(f"  [{ind}] 匹配{len(batch_results)}/{len(names_list)}")
    
    # 保存
    os.makedirs('data/master', exist_ok=True)
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    out_path = 'data/master/专精特新缺口补充_baidu.csv'
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n=== 汇总 ===")
    print(f"匹配成功: {matched}家, 未匹配: {unmatched}家")
    print(f"保存: {out_path}")

if __name__ == '__main__':
    main()