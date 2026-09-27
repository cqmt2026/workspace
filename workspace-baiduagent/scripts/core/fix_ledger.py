import json, sys
sys.stdout.reconfigure(encoding='utf-8')

path = 'data/multi_channel_ledger.json'
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

# 更新百度POI数据量
d['channels']['百度POI']['coverage']['row_count'] = 2513
d['channels']['百度POI']['last_updated'] = '2026-08-30'

# 更新统计
d['coverage_summary']['total_rows'] = 12424
d['coverage_summary']['crm_total'] = 11615
d['coverage_summary']['today_patch'] = {
    'source': '百度POI分4批补抓',
    'rows': 511,
    'industries': ['人力资源','软件信息','物流货运','检验检测','智能制造','食品加工','广告传媒','医疗卫生','母婴亲子','医疗器械','装修装饰','教育培训','能源环保','法律服务','商贸批发','酒店餐饮','文化传媒','健身瑜伽','新能源充电'],
}
d['metadata']['last_updated'] = '2026-08-30'
d['metadata']['version'] = '1.2'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print('台账更新完成')
print(f"百度POI: {d['channels']['百度POI']['coverage']['row_count']} 条")
print(f"台账总数: {d['coverage_summary']['total_rows']}")
print(f"CRM入库: {d['coverage_summary']['crm_total']}")
print(f"今日补抓: {d['coverage_summary']['today_patch']['rows']} 条")