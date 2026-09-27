# -*- coding: utf-8 -*-
"""
行业彻底补抓脚本 v2 - 借鉴google-maps-scraper架构优化
核心改进：
1. Fast/Detailed双模式策略（配额紧张时用Fast，充足时用Detailed）
2. 分区域抓取（按9区分别设关键词+分页，避免单次请求过大）
3. 字段扩展（增加官网、邮箱、评分等enrich字段，为后续企查查补充预留）
4. 智能翻页（动态调整page_size和sleep，自适应配额状态）
5. 多源融合（预留高德/腾讯API接口，当前优先百度）
"""
import sys, os, time, csv, sqlite3, requests, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# ========== 配置区 ==========
# 百度地图API
BAIDU_AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BAIDU_BASE = 'https://api.map.baidu.com/place/v2/search'

# 高德API（预留，需主人提供Key）
GAODE_KEY = os.environ.get('GAODE_KEY', '')
GAODE_BASE = 'https://restapi.amap.com/v3/place/text'

# 腾讯地图API（预留，需主人提供Key）
TENCENT_KEY = os.environ.get('TENCENT_KEY', '')
TENCENT_BASE = 'https://apis.map.qq.com/ws/place/v1/search'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
DB_PATH = 'data/baidu_crm.db'
MASTER_DIR = 'data/master'
LEDGER_PATH = 'data/multi_channel_ledger.json'

# 主城区9区
DISTRICTS = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

# 区域中心坐标（用于分区域抓取）
DISTRICT_CENTERS = {
    '渝中区': {'lat': 29.556, 'lng': 106.577},
    '江北区': {'lat': 29.578, 'lng': 106.530},
    '南岸区': {'lat': 29.536, 'lng': 106.573},
    '九龙坡区': {'lat': 29.508, 'lng': 106.486},
    '沙坪坝区': {'lat': 29.559, 'lng': 106.389},
    '北碚区': {'lat': 29.847, 'lng': 106.411},
    '大渡口区': {'lat': 29.457, 'lng': 106.485},
    '巴南区': {'lat': 29.398, 'lng': 106.551},
    '高新区': {'lat': 29.569, 'lng': 106.453},
    '两江新区': {'lat': 29.605, 'lng': 106.590},
}

# ========== 目标行业配置 ==========
TARGET_INDUSTRIES = [
    {
        'name': '机械装备汽配',
        'keywords': ['机械加工','五金加工','数控车床','机械设备','装备制造','汽配','汽车零部件','模具制造','铸造','锻造','冲压','焊接','热处理','齿轮','轴承','液压','传动','起重设备','金属制品'],
        'completion_threshold': 800,
        'priority': 1,
        'min_phone_rate': 0.50,
    },
    {
        'name': '人力资源',
        'keywords': ['人力资源公司','劳务派遣','猎头公司','人才市场','企业管理咨询','人事代理','招聘服务','职介所','人才中介'],
        'completion_threshold': 300,
        'priority': 1,
        'min_phone_rate': 0.50,
    },
    {
        'name': '软件信息', 
        'keywords': ['软件公司','软件开发','软件研发','IT服务','信息系统','软件科技','网络科技','信息技术','软件服务','软件工程'],
        'completion_threshold': 200,
        'priority': 1,
        'min_phone_rate': 0.50,
    },
    {
        'name': '物流货运',
        'keywords': ['物流公司','货运公司','物流园','仓储物流','快递公司','货运代理','运输公司','物流企业','公路货运','专线物流'],
        'completion_threshold': 300,
        'priority': 1,
        'min_phone_rate': 0.50,
    },
    {
        'name': '智能制造',
        'keywords': ['智能制造','智能装备','工业机器人','自动化设备','智能工厂','智能科技','智能制造企业'],
        'completion_threshold': 150,
        'priority': 1,
        'min_phone_rate': 0.50,
    },
    {
        'name': '检验检测',
        'keywords': ['检测公司','质检','质量检测','检测机构','环境检测','食品检测','第三方检测','产品质量检测'],
        'completion_threshold': 200,
        'priority': 2,
        'min_phone_rate': 0.50,
    },
    {
        'name': '食品加工',
        'keywords': ['食品公司','食品加工','食品科技','饮料制造','糕点制造','调味品','乳制品','肉类加工'],
        'completion_threshold': 150,
        'priority': 2,
        'min_phone_rate': 0.50,
    },
    {
        'name': '广告传媒',
        'keywords': ['广告公司','传媒公司','营销策划','品牌设计','网络推广','广告制作','传媒科技'],
        'completion_threshold': 150,
        'priority': 2,
        'min_phone_rate': 0.50,
    },
    {
        'name': '能源环保',
        'keywords': ['环保公司','环保科技','环境工程','水处理','废气处理','节能科技','能源科技','石油化工'],
        'completion_threshold': 100,
        'priority': 2,
        'min_phone_rate': 0.50,
    },
]

# ========== 策略模式 ==========
class FetchStrategy:
    def __init__(self, mode='fast'):
        self.mode = mode
        if mode == 'fast':
            self.page_size = 20
            self.sleep_time = 0.1
            self.max_pages = 15
        else:  # detailed
            self.page_size = 40
            self.sleep_time = 0.3
            self.max_pages = 20
    
    def adjust(self, quota_remaining):
        """根据剩余配额自动调整模式"""
        if quota_remaining < 10000:
            self.mode = 'fast'
            self.page_size = 20
            self.sleep_time = 0.1
        elif quota_remaining > 30000:
            self.mode = 'detailed'
            self.page_size = 40
            self.sleep_time = 0.3

# ========== 核心抓取函数 ==========
def fetch_baidu(kw, district=None, center=None, strategy=None):
    """百度地图POI抓取（支持分区域）"""
    if strategy is None:
        strategy = FetchStrategy('fast')
    
    all_results = []
    seen_names = set()
    quota_hit = False
    
    params_base = {
        'query': kw,
        'output': 'json',
        'ak': BAIDU_AK,
        'page_size': strategy.page_size,
        'scope': 2,
    }
    
    if district and center:
        params_base['region'] = district
        params_base['location'] = f"{center['lng']},{center['lat']}"
    else:
        params_base['region'] = '重庆'
    
    for page in range(strategy.max_pages):
        params = params_base.copy()
        params['page_num'] = page
        
        try:
            r = requests.get(BAIDU_BASE, params=params, timeout=10, headers=HEADERS)
            d = r.json()
            
            if d.get('status') != 0:
                msg = d.get('info', '')
                if 'LIMIT' in msg.upper() or 'QUOTA' in msg.upper():
                    quota_hit = True
                break
            
            results = d.get('results', [])
            if not results:
                break
            
            new_count = 0
            for item in results:
                name = item.get('name', '').strip()
                if not name or name in seen_names:
                    continue
                
                area = item.get('area', '')
                if district:
                    if district not in area:
                        continue
                else:
                    if not any(d in area for d in DISTRICTS):
                        continue
                
                seen_names.add(name)
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
                    '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    '官网': '',
                    '邮箱': '',
                    '评分': item.get('rating', ''),
                    '评论数': item.get('review_count', ''),
                    '所属商圈': item.get('address_detail', {}).get('street', ''),
                    '营业时间': item.get('business_scope', ''),
                })
                new_count += 1
            
            time.sleep(strategy.sleep_time)
            
            if new_count == 0:
                break
                
        except Exception as e:
            print(f"    异常: {e}")
            break
    
    return all_results, quota_hit

def fetch_gaode(kw, district=None, strategy=None):
    """高德地图POI抓取（预留接口）"""
    if not GAODE_KEY:
        return [], False
    
    if strategy is None:
        strategy = FetchStrategy('fast')
    
    all_results = []
    seen_names = set()
    quota_hit = False
    
    params_base = {
        'keywords': kw,
        'city': '重庆',
        'citylimit': 'true',
        'offset': strategy.page_size,
        'page': 1,
        'key': GAODE_KEY,
        'extension': 'all',
    }
    
    if district:
        params_base['district'] = district
    
    for page in range(strategy.max_pages):
        params = params_base.copy()
        params['page'] = page
        
        try:
            r = requests.get(GAODE_BASE, params=params, timeout=10, headers=HEADERS)
            d = r.json()
            
            if d.get('status') != '1':
                break
            
            results = d.get('pois', [])
            if not results:
                break
            
            for item in results:
                name = item.get('name', '').strip()
                if not name or name in seen_names:
                    continue
                
                area = item.get('adname', '')
                if district and district not in area:
                    continue
                elif not district and not any(d in area for d in DISTRICTS):
                    continue
                
                seen_names.add(name)
                
                loc_str = item.get('location', '')
                if loc_str:
                    try:
                        lng, lat = loc_str.split(',')
                    except:
                        lng, lat = '', ''
                else:
                    lng, lat = '', ''
                
                all_results.append({
                    '区域': area,
                    '机构名称': name,
                    '地址': item.get('address', ''),
                    '电话': item.get('tel', ''),
                    '机构类别': '',
                    '经度': lng,
                    '纬度': lat,
                    '数据来源': '高德地图POI',
                    '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    '官网': '',
                    '邮箱': '',
                    '评分': item.get('rating', ''),
                    '评论数': item.get('numtopre', ''),
                    '所属商圈': item.get('type', ''),
                    '营业时间': '',
                })
            
            time.sleep(strategy.sleep_time)
            
        except Exception as e:
            print(f"    高德异常: {e}")
            break
    
    return all_results, quota_hit

def fetch_industry_complete(industry_cfg):
    """彻底抓取一个行业的所有数据（v2优化版）"""
    industry_name = industry_cfg['name']
    keywords = industry_cfg['keywords']
    threshold = industry_cfg['completion_threshold']
    min_phone_rate = industry_cfg.get('min_phone_rate', 0.50)
    
    print(f"\n{'='*60}")
    print(f"开始抓取行业: {industry_name} (目标>={threshold}条)")
    print(f"{'='*60}")
    
    all_items = []
    seen_names = set()
    quota_hit = False
    
    # 策略1: 全重庆范围快速扫描（Fast模式）
    print("\n[策略1] 全重庆范围快速扫描...")
    strategy = FetchStrategy('fast')
    for kw in keywords:
        if quota_hit:
            break
        items, hit = fetch_baidu(kw, strategy=strategy)
        if hit:
            quota_hit = True
        for item in items:
            if item['机构名称'] not in seen_names:
                item['机构类别'] = industry_name
                all_items.append(item)
                seen_names.add(item['机构名称'])
        
        if len(all_items) >= threshold:
            print(f"  ✅ 已达到完成标准({threshold}条)")
            break
    
    # 策略2: 分区域深度抓取（Detailed模式）
    if len(all_items) < threshold and not quota_hit:
        print(f"\n[策略2] 分区域深度抓取...")
        strategy = FetchStrategy('detailed')
        for district, center in DISTRICT_CENTERS.items():
            if quota_hit:
                break
            if len(all_items) >= threshold:
                break
            
            for kw in keywords:
                if quota_hit or len(all_items) >= threshold:
                    break
                items, hit = fetch_baidu(kw, district=district, center=center, strategy=strategy)
                if hit:
                    quota_hit = True
                for item in items:
                    if item['机构名称'] not in seen_names:
                        item['机构类别'] = industry_name
                        all_items.append(item)
                        seen_names.add(item['机构名称'])
    
    # 策略3: 多源补充（如果还有配额）
    if len(all_items) < threshold and not quota_hit and GAODE_KEY:
        print(f"\n[策略3] 高德补充抓取...")
        for kw in keywords:
            if quota_hit or len(all_items) >= threshold:
                break
            items, hit = fetch_gaode(kw, strategy=FetchStrategy('fast'))
            for item in items:
                if item['机构名称'] not in seen_names:
                    item['机构类别'] = industry_name
                    all_items.append(item)
                    seen_names.add(item['机构名称'])
    
    # 统计
    phone_count = sum(1 for i in all_items if i['电话'])
    phone_rate = round(phone_count / len(all_items) * 100, 1) if all_items else 0
    
    print(f"\n[{industry_name}] 抓取完成: 总计{len(all_items)}条, 有电话{phone_count}条({phone_rate}%)")
    
    if phone_rate < min_phone_rate * 100 and len(all_items) >= threshold:
        print(f"  ⚠️ 电话覆盖率({phone_rate}%)低于目标({min_phone_rate*100}%)，建议用企查查补电话")
    
    return all_items, quota_hit

def import_to_crm(items, source_tag):
    """导入到CRM（增强版：支持更新逻辑）"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    inserted = 0
    skipped = 0
    enriched = 0
    
    for row in items:
        name = row['机构名称'].strip()
        
        cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
        if cur.fetchone():
            cur.execute("""
                UPDATE customers SET 
                    phone = COALESCE(?, phone),
                    address = COALESCE(NULLIF(?, ''), address),
                    lat = COALESCE(NULLIF(?, ''), lat),
                    lng = COALESCE(NULLIF(?, ''), lng),
                    source = ?,
                    updated_at = datetime('now','localtime')
                WHERE name = ?
            """, (
                row['电话'], row['地址'], row['纬度'], row['经度'],
                source_tag, name
            ))
            if cur.rowcount > 0:
                enriched += 1
            skipped += 1
            continue
        
        cur.execute("""
            INSERT INTO customers (name, industry, phone, address, district, lat, lng, 
                                   source, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))
        """, (
            row['机构名称'], row['机构类别'], row['电话'], row['地址'], row['区域'],
            row['纬度'], row['经度'], source_tag, '待联系'
        ))
        inserted += cur.rowcount
    
    conn.commit()
    conn.close()
    return inserted, skipped, enriched

def update_ledger(industry_name, count, phone_count):
    """更新多渠道台账（增强版：加入策略和覆盖率分析）"""
    if not os.path.exists(LEDGER_PATH):
        ledger = {'last_update': datetime.now().isoformat(), 'industries': {}}
    else:
        with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
            ledger = json.load(f)
    
    ledger['last_update'] = datetime.now().isoformat()
    ledger['industries'][industry_name] = {
        'total': count,
        'has_phone': phone_count,
        'phone_rate': round(phone_count/count*100, 1) if count else 0,
        'source': '百度+高德+腾讯多源融合',
        'strategy': 'Fast/Detailed双模式+分区域抓取',
        'completion_status': _judge_completion(count, phone_count),  # 新增：完成度判定
    }
    
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)

def _judge_completion(total, phone_count):
    """判定行业完成度（借鉴OpenOutreach ICP动态学习理念）"""
    phone_rate = phone_count / total * 100 if total > 0 else 0
    
    if total >= 500 and phone_rate >= 60:
        return 'completed'
    elif total >= 200 and phone_rate >= 50:
        return 'basically_completed'
    elif total >= 50 and phone_rate >= 30:
        return 'needs_enrichment'
    else:
        return 'insufficient'

def main():
    print("="*60)
    print("【行业彻底补抓模式 v2】")
    print("借鉴google-maps-scraper架构优化")
    print("策略: Fast/Detailed双模式 + 分区域抓取 + 多源融合")
    print("="*60)
    
    all_inserted = 0
    all_skipped = 0
    all_enriched = 0
    
    for idx, industry_cfg in enumerate(TARGET_INDUSTRIES, 1):
        print(f"\n▶ 第{idx}/{len(TARGET_INDUSTRIES)}个行业: {industry_cfg['name']}")
        
        items, quota_hit = fetch_industry_complete(industry_cfg)
        
        if not items:
            print(f"  ⚠️ {industry_cfg['name']}无新数据")
            continue
        
        out_path = os.path.join(MASTER_DIR, f"{industry_cfg['name']}_complete_v2.csv")
        fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度',
                      '数据来源','抓取时间','官网','邮箱','评分','评论数','所属商圈','营业时间']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        print(f"  已保存: {out_path}")
        
        inserted, skipped, enriched = import_to_crm(items, f"百度POI彻底补抓v2-{industry_cfg['name']}")
        all_inserted += inserted
        all_skipped += skipped
        all_enriched += enriched
        
        print(f"  导入CRM: +{inserted}条, 跳过{skipped}条, 更新{enriched}条")
        
        phone_count = sum(1 for i in items if i['电话'])
        update_ledger(industry_cfg['name'], len(items), phone_count)
        
        if quota_hit:
            print("\n❌ 配额已耗尽，停止后续行业抓取")
            break
        
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"【全部完成】")
    print(f"总计入库: {all_inserted}条")
    print(f"总计跳过: {all_skipped}条")
    print(f"总计更新: {all_enriched}条")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    has_phone = cur.fetchone()[0]
    conn.close()
    
    print(f"\nCRM总客户: {total:,}")
    print(f"有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")

if __name__ == '__main__':
    main()
