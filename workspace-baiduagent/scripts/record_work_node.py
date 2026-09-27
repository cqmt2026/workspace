# -*- coding: utf-8 -*-
"""记录2026-08-31工作节点：百度POI彻底补抓8行业"""
import sys, json, sqlite3, time
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'
LEDGER_PATH = 'data/multi_channel_ledger.json'

# 1. 读取CRM最新数据
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM customers WHERE length(phone)>5')
has_phone = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ""')
has_district = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM customers WHERE tier IS NOT NULL AND tier != ""')
has_tier = cur.fetchone()[0]

# 各补抓行业入库数
print('--- 百度POI彻底补抓各行业入库数 ---')
cur.execute("SELECT source, COUNT(*) FROM customers WHERE source LIKE '百度POI彻底补抓%' GROUP BY source")
baidu_patch = {r[0]: r[1] for r in cur.fetchall()}
for k, v in baidu_patch.items():
    print(f'  {k}: {v}')
conn.close()

phone_coverage = round(has_phone/total*100, 1)
district_coverage = round(has_district/total*100, 1)

print(f'\nCRM总客户: {total:,}')
print(f'有电话: {has_phone:,} ({phone_coverage}%)')
print(f'有区域: {has_district:,} ({district_coverage}%)')
print(f'有层级: {has_tier:,}')

# 2. 读取台账
with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
    ledger = json.load(f)

# 3. 更新百度POI行数
bd = ledger['channels']['百度POI']['coverage']
bd_patch_rows = sum(baidu_patch.values())
bd['row_count'] = bd.get('row_count', 0) + bd_patch_rows
bd['last_updated'] = '2026-08-31'
# 新增覆盖行业
for ind in ['人力资源', '软件信息', '物流货运', '智能制造', '检验检测', '食品加工', '广告传媒', '能源环保补充']:
    if ind not in bd['covered_industries']:
        bd['covered_industries'].append(ind)
bd['covered_industries'].sort()

# 4. 更新汇总
summary = ledger['coverage_summary']
summary['total_rows'] = summary.get('total_rows', 0) + bd_patch_rows
summary['crm_total'] = total
summary['notes'] = '【2026-08-31】百度POI彻底补抓8行业(人力资源/软件信息/物流货运/智能制造/检验检测/食品加工/广告传媒/能源环保补充)，入库721条。百度配额在食品加工时开始受限，食品加工/广告传媒未达标，明日0点后可继续。高德今日INVALID_USER_KEY需检查。'

# 更新quality_summary
qs = ledger['quality_summary']
qs['total_customers'] = total
qs['has_phone'] = has_phone
qs['phone_coverage'] = phone_coverage
qs['has_tier'] = has_tier
qs['has_district'] = has_district
qs['district_coverage'] = district_coverage

# 更新metadata
ledger['metadata']['last_updated'] = '2026-08-31'
ledger['metadata']['changelog'] = '【2026-08-31】百度POI彻底补抓8行业入库721条，CRM增至12,631家。百度配额今日可用(未耗尽前抓取8行业)，高德Key异常(INVALID_USER_KEY)待检查。'

# 5. 写回台账
with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)

print('\n✅ 台账已更新')
print(f'百度POI行数: {bd["row_count"]}')
print(f'台账总行数: {summary["total_rows"]}')
