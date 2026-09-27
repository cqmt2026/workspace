# -*- coding: utf-8 -*-
"""生成今日数据获取阶段性汇报"""
import sqlite3, csv, os, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
SOURCE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source'

print("=" * 70)
print("【百都系统数据获取阶段性汇报】")
print(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 70)

# 1. CRM总览
print("\n📊 一、CRM数据库总览")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
print(f"   总客户数: {total:,}家")

cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = cur.fetchone()[0]
print(f"   有电话: {has_phone:,}家 ({has_phone*100//total}%)")

cur.execute("SELECT COUNT(*) FROM customers WHERE status='待联系'")
pending = cur.fetchone()[0]
print(f"   待联系: {pending:,}家")

# 2. 行业分布
print("\n📊 二、行业分布")
cur.execute('''
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers GROUP BY industry ORDER BY total DESC
''')
print(f"   {'行业':<12} {'总数':>6} {'有电话':>8} {'覆盖率':>8}")
print("   " + "-" * 40)
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    print(f"   {r[0]:<12} {r[1]:>6} {r[2]:>8} {rate:>5}%")

# 3. 数据来源分析
print("\n📊 三、数据来源分析")
cur.execute('''
    SELECT source, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers GROUP BY source ORDER BY total DESC
''')
print(f"   {'来源':<20} {'总数':>6} {'有电话':>8} {'覆盖率':>8}")
print("   " + "-" * 50)
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    print(f"   {r[0]:<20} {r[1]:>6} {r[2]:>8} {rate:>5}%")

conn.close()

# 4. Master文件统计
print("\n📊 四、Master数据文件统计")
print(f"   目录: {MASTER_DIR}")
total_rows = 0
baidu_count = 0
amap_count = 0
other_count = 0
for f in sorted(os.listdir(MASTER_DIR)):
    if not f.endswith('.csv'):
        continue
    fpath = os.path.join(MASTER_DIR, f)
    with open(fpath, encoding='utf-8-sig') as fh:
        rows = sum(1 for _ in fh) - 1
    total_rows += rows
    if 'baidu' in f:
        baidu_count += rows
    elif 'amap' in f or '高德' in f:
        amap_count += rows
    else:
        other_count += rows

print(f"   总行数: {total_rows:,}行")
print(f"   百度源: {baidu_count:,}行")
print(f"   高德源: {amap_count:,}行")
print(f"   其他源: {other_count:,}行")

# 5. Source目录统计
print("\n📊 五、Source原始数据统计")
for subdir in ['amap', 'tencent', 'weijkw', 'gxq']:
    subpath = os.path.join(SOURCE_DIR, subdir)
    if not os.path.exists(subpath):
        continue
    files = [f for f in os.listdir(subpath) if f.endswith('.csv')]
    count = len(files)
    total_size = sum(os.path.getsize(os.path.join(subpath, f)) for f in files)
    print(f"   {subdir}/: {count}个文件, {total_size//1024}KB")

# 6. 今日工作亮点
print("\n🌟 六、今日工作亮点")
print("   ✅ 完成CRM数据库初始化（9,379家客户）")
print("   ✅ 高德POI数据批量抓取（第一+第二梯队）")
print("   ✅ 百度POI数据批量抓取（第二+第三梯队）")
print("   ✅ 官方名单多渠道验证（卫健委/教育局/住建委）")
print("   ✅ 腾讯地图API配置成功（域名白名单+IP授权）")
print("   ✅ 建立数据管理规范（master/source/temp目录结构）")

# 7. 遇到的问题
print("\n⚠️ 七、遇到的问题")
print("   ❌ 高德/百度/腾讯三平台今日配额全部耗尽")
print("   ❌ 腾讯批量脚本Key被截断导致0数据入库")
print("   ⚠️ 低覆盖率行业需补充电话（软件/智能制造/物流）")

# 8. 明日计划
print("\n📋 八、明日计划（配额恢复后）")
print("   1. 高德text/around接口恢复 → 批量补抓低覆盖率行业")
print("   2. 百度接口恢复 → 补充第二梯队数据")
print("   3. 腾讯接口恢复 → 重新运行修复后的批量脚本")
print("   4. 低覆盖率行业电话补充（企查查手动查询）")
print("   5. 开始首批电话拨打（优先口腔+医美高价值行业）")

# 9. 长期建议
print("\n💡 九、长期建议")
print("   📌 引入企查查专业版（¥2,000-5,000/年）")
print("      - 解决电话覆盖率问题")
print("      - 批量筛选+导出功能")
print("      - API实时查询验证")
print("   📌 考虑地图API企业版（配额提升10倍）")
print("   📌 建立月度增量更新机制")

print("\n" + "=" * 70)
print("汇报完毕 | 小度 | 2026-08-29")
print("=" * 70)
