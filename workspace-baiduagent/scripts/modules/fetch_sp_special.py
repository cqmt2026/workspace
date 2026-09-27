# -*- coding: utf-8 -*-
"""
第二梯队增强：用专精特新名单中的企业名去高德POI搜索获取电话/地址
目标：医疗器械、新材料化工、机械装备汽配、环保检测、建筑建材、新能源充电电力
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_poi_by_name(name, city='重庆'):
    """按企业名搜索高德POI"""
    params = {
        'keywords': name,
        'city': city,
        'offset': 1,
        'page': 1,
        'key': KEY,
        'extensions': 'all',
        'area_limit': 0,
    }
    try:
        r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == '1' and d.get('pois'):
            return d['pois'][0]
        return None
    except:
        return None

def filter_main_urban(item):
    """过滤主城区9区"""
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    adname = item.get('adname','')
    for d in districts:
        if d in adname:
            return True
    return False

def get_industry_from_sp(name, industry_keywords):
    """根据名称关键词判断行业"""
    for kw, ind in industry_keywords:
        if kw in name:
            return ind
    return '专精特新综合'

def main():
    # 第二梯队关键词
    industry_map = [
        ('医疗','医疗器械'), ('器械','医疗器械'), ('制药','医疗器械'),
        ('生物','医疗器械'), ('检验','医疗器械'), ('诊断','医疗器械'),
        ('仪器','医疗器械'), ('设备','医疗器械'),
        ('材料','新材料化工'), ('化工','新材料化工'), ('新材','新材料化工'),
        ('塑料','新材料化工'), ('塑胶','新材料化工'), ('胶粘','新材料化工'),
        ('合金','新材料化工'), ('钛','新材料化工'), ('镁','新材料化工'),
        ('纤维','新材料化工'), ('节能','新材料化工'),
        ('机械','机械装备汽配'), ('装备','机械装备汽配'), ('模具','机械装备汽配'),
        ('汽配','机械装备汽配'), ('汽车','机械装备汽配'), ('零部件','机械装备汽配'),
        ('起重','机械装备汽配'), ('液压','机械装备汽配'), ('润滑','机械装备汽配'),
        ('智能装备','机械装备汽配'), ('自动化','机械装备汽配'),
        ('环保','环保检测'), ('检测','环保检测'), ('清洁','环保检测'),
        ('水处理','环保检测'), ('净化','环保检测'),
        ('建材','建筑建材'), ('装饰','建筑建材'), ('建筑','建筑建材'),
        ('钢结构','建筑建材'), ('混凝土','建筑建材'), ('保温','建筑建材'),
        ('新能源','新能源充电电力'), ('充电','新能源充电电力'),
        ('电力','新能源充电电力'), ('电气','新能源充电电力'),
    ]

    # 读取专精特新名单
    sp_path = 'data/master/zs_list_chongqing_latest.csv'
    sp_names = []
    with open(sp_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('机构名称','').strip()
            if name and len(name) > 3:
                sp_names.append(name)
    print(f"专精特新名单共 {len(sp_names)} 家")

    # 筛选第二梯队相关的企业
    tier2_names = []
    for name in sp_names:
        ind = get_industry_from_sp(name, industry_map)
        if ind != '专精特新综合':
            tier2_names.append((name, ind))
    print(f"第二梯队相关: {len(tier2_names)} 家")

    # 抓取POI
    results = []
    matched = 0
    unmatched = 0
    errors = 0

    for i, (name, industry) in enumerate(tier2_names):
        item = fetch_poi_by_name(name)
        if item and filter_main_urban(item):
            matched += 1
            results.append({
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
            })
        elif item:
            # 非主城区也记录（标注）
            matched += 1
            results.append({
                '区域': item.get('adname',''),
                '机构名称': item.get('name', name),
                '地址': item.get('address',''),
                '电话': item.get('tel',''),
                '机构类别': industry,
                'adname': item.get('adname',''),
                '经度': item.get('lon',''),
                '纬度': item.get('lat',''),
                '数据来源': '高德POI+专精特新(非主城)',
                '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
            })
        else:
            unmatched += 1
        errors += 0

        if (i + 1) % 50 == 0:
            print(f"  进度 {i+1}/{len(tier2_names)}, 匹配{matched}, 未匹配{unmatched}")

        time.sleep(0.15)  # 控制频率

    # 按行业分类保存
    by_industry = {}
    for r in results:
        ind = r['机构类别']
        by_industry.setdefault(ind, []).append(r)

    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
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

    print(f"\n汇总: 匹配{matched}/{len(tier2_names)}, 未匹配{unmatched}, 保存{total_saved}条")

if __name__ == '__main__':
    main()
