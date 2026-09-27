# -*- coding: utf-8 -*-
"""更新台账JSON - 记录今日补抓成果"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

ledger_path = 'data/multi_channel_ledger.json'
with open(ledger_path, 'r', encoding='utf-8') as f:
    ledger = json.load(f)

# 更新百度POI
ledger['channels']['百度POI']['coverage']['row_count'] = 2513
ledger['channels']['百度POI']['coverage']['last_updated'] = '2026-08-30'
ledger['channels']['百度POI']['last_updated'] = '2026-08-30'

# 更新统计
ledger['coverage_summary']['total_rows'] = 12424
ledger['coverage_summary']['crm_total'] = 11615
ledger['coverage_summary']['today_patch'] = {
    'source': '百度POI分4批补抓',
    'rows': 511,
    'industries': ['人力资源','软件信息','物流货运','检验检测','智能制造','食品加工','广告传媒','医疗卫生','母婴亲子','医疗器械','装修装饰','教育培训','能源环保','法律服务','商贸批发','酒店餐饮','文化传媒','健身瑜伽','新能源充电'],
    'phone_coverage_before': '25-40%',
    'phone_coverage_after': '30-97%'
}
ledger['metadata']['last_updated'] = '2026-08-30'
ledger['metadata']['version'] = '1.2'

with open(ledger_path, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)

print('台账已更新 ✅')