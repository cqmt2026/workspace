# -*- coding: utf-8 -*-
"""
第二梯队数据抓取 v2：从专精特新md名单中筛选目标行业企业，用高德POI获取电话/地址
目标：医疗器械、新材料化工、机械装备汽配、环保检测、建筑建材、新能源充电电力
创建: 2026-08-29 | 作者: 小度
"""
import sys, os, time, re, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 第二梯队行业关键词映射
INDUSTRY_KWS = {
    '医疗器械': ['医疗', '器械', '制药', '生物', '检验', '诊断', '仪器', '设备', '医学', '医院', '口腔'],
    '新材料化工': ['材料', '化工', '新材', '塑料', '塑胶', '胶粘', '合金', '钛', '镁', '纤维', '节能', '保温', '防水'],
    '机械装备汽配': ['机械', '装备', '模具', '汽配', '汽车', '零部件', '起重', '液压', '润滑', '自动化', '传动', '机床', '金属', '铸造'],
    '环保检测': ['环保', '检测', '清洁', '水处理', '净化', '环境', '废气', '废水', '噪声'],
    '建筑建材': ['建材', '装饰', '建筑', '钢结构', '混凝土', '保温', '防水', '幕墙', '门窗', '陶瓷'],
    '新能源充电电力': ['新能源', '充电', '电力', '电气', '光伏', '储能', '电池', '电网'],
}

def fetch_poi_by_name(name):
    """按企业名搜索高德POI，返回匹配结果"""
    params = {
        'keywords': name,
        'city': '重庆',
        'offset': 1,
        'page': 1,
        'key': KEY,
        'extensions': 'all',
    }
    try:
        r = requests.get(BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == '1' and d.get('pois'):
            return d['pois'][0]
        return None
    except:
        return None

def filter_main_urban(adname):
    """过滤主城区9区+高新区+两江新区"""
    districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
                 '北碚区','大渡口区','巴南区','高新区','两江新区']
    for d in districts:
        if d in adname:
            return True
    return False

def classify_name(name):
    """根据名称关键词判断行业"""
    name_clean = re.sub(r'[（）\(\)（〕\[\]【】\u300a\u300b]','',name)
    for ind, kws in INDUSTRY_KWS.items():
        for kw in kws:
            if kw in name_clean:
                return ind
    return None

def read_sp_names():
    """从md文件读取专精特新企业名"""
    names = []
    with open('assets/重庆专精特新企业全名单_2275家.md', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            m = re.match(r'^\d+\.\s+(.+)$', line)
            if m:
                names.append(m.group(1).strip())
    print(f"从md读取专精特新名单: {len(names)} 家")
    return names

def main():
    sp_names = read_sp_names()
    
    # 分类
    classified = {}
    unclassified = []
    for name in sp_names:
        ind = classify_name(name)
        if ind:
            classified.setdefault(ind, []).append(name)
        else:
            unclassified.append(name)
    
    print(f"\n行业分类:")
    total_t2 = 0
    for ind, names in sorted(classified.items(), key=lambda x: -len(x[1])):
        print(f"  {ind}: {len(names)} 家")
        total_t2 += len(names)
    print(f"  未分类: {len(unclassified)} 家")
    print(f"  第二梯队总计: {total_t2} 家")
    
    # 逐个搜索POI
    all_results = []
    matched = 0
    unmatched = 0
    
    for ind, names in classified.items():
        print(f"\n--- 开始抓取 {ind} ({len(names)}家) ---")
        for i, name in enumerate(names):
            item = fetch_poi_by_name(name)
            if item:
                matched += 1
                all_results.append({
                    '区域': item.get('adname',''),
                    '机构名称': item.get('name', name),
                    '地址': item.get('address',''),
                    '电话': item.get('tel',''),
                    '机构类别': ind,
                    'adname': item.get('adname',''),
                    '经度': item.get('lon',''),
                    '纬度': item.get('lat',''),
                    '数据来源': '高德POI+专精特新',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
            else:
                unmatched += 1
            if (i + 1) % 30 == 0:
                print(f"  {ind}: 进度 {i+1}/{len(names)}, 匹配{matched}, 未匹配{unmatched}")
            time.sleep(0.12)
    
    # 保存
    by_industry = {}
    for r in all_results:
        by_industry.setdefault(r['机构类别'], []).append(r)
    
    fieldnames = ['区域','机构名称','地址','电话','机构类别','adname','经度','纬度','数据来源','抓取时间']
    total_saved = 0
    for ind, items in by_industry.items():
        safe_name = ind.replace('/','_').replace(' ','_').replace('（','(').replace('）',')')
        out_path = os.path.join('data', 'master', f'{safe_name}_sp.csv')
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        print(f"  [{ind}] {len(items)} 条 → {out_path}")
        total_saved += len(items)
    
    # 汇总CSV
    master_path = os.path.join('data', 'master', 'tier2_all_sp.csv')
    with open(master_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\n汇总保存: {total_saved}/{matched} 条 → {master_path}")
    print(f"未匹配: {unmatched} 条")

if __name__ == '__main__':
    main()
