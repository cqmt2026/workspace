# -*- coding: utf-8 -*-
"""更新台账并生成最终执行报告"""
import json, os, sys, sqlite3, csv
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# 1. 更新multi_channel_ledger.json
LEDGER_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'
with open(LEDGER_FILE, encoding='utf-8') as f:
    ledger = json.load(f)

ledger['channels']['经信委']['status'] = '✅已覆盖'
ledger['channels']['经信委']['coverage'] = {
    'covered_industries': ['软件信息','智能制造','机械装备汽配','新材料化工','电子科技','新能源充电电力'],
    'row_count': 2556,
    'last_updated': '2026-08-29',
    'source': '2025年创新型中小企业申报+复核名单'
}
ledger['channels']['经信委']['note'] = '2025年8月公布，申报830家+复核1724家，已入库CRM'

with open(LEDGER_FILE, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)
print("✅ 台账已更新")

# 2. 读取CRM最终状态
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_tel = cur.fetchone()[0]

print(f"\n📊 CRM最终状态:")
print(f"   总客户: {total:,}家")
print(f"   有电话: {has_tel:,}家 ({has_tel*100//total}%)")

# 3. 各行业覆盖率
print(f"\n📊 各行业电话覆盖率:")
cur.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers GROUP BY industry ORDER BY has_phone*100/COUNT(*) ASC LIMIT 10
""")
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    icon = '🔴' if rate < 40 else ('🟡' if rate < 60 else '🟢')
    print(f"   {icon} {r[0]}: {r[1]}家, 有电话{r[2]}({rate}%)")

conn.close()

# 4. 生成执行总结
print("\n" + "=" * 78)
print("【2026-08-29 多渠道数据获取 - 执行总结】")
print("=" * 78)
print("""
✅ 今日已完成:
  1. 经信委创新型中小企业2,556家 → 新增1,725家入库 (CRM: 9,379→11,104)
  2. 高德POI批量抓取（12个行业，7,592家）
  3. 百度POI批量抓取（17个行业，2,022家）
  4. 卫健委名单抓取（3个行业，1,051家）
  5. 教委白名单抓取（1个行业，204家）
  6. 腾讯地图API配置+Key修复
  7. 建立32渠道统一台账管理机制

⚠️  今日受限:
  - 高德/百度/腾讯三平台配额全部耗尽（等明日0点恢复）
  - 市场监管局/药监局等动态网页需浏览器自动化

⏳  明日执行计划:
  1. 高德/百度/腾讯配额恢复 → 补抓P0/P1低覆盖率行业
  2. 市场监管局 - 检验检测/食品/广告资质名单（需浏览器）
  3. 药监局 - 医疗器械生产/经营许可证（需浏览器）
  4. 交通局 - 道路运输经营许可
  5. 住建委 - 建筑业企业资质

🔴  长期方案:
  - 企查查/天眼查专业版授权 → 解决电话覆盖率问题
  - 行业协会名录联系获取
""")
