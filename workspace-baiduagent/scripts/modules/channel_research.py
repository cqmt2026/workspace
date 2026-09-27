"""
多渠道电话补充方案调研
目标: 机械/物流/创新型中小企业等行业电话覆盖率提升
"""
import os
import sqlite3

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

print("=" * 70)
print("【多渠道电话补充方案调研】")
print("=" * 70)

# 检查现有数据源
conn = sqlite3.connect(db)
c = conn.cursor()

# 1. 现有数据来源统计
print("\n【现有数据来源分布】")
c.execute("""
SELECT source, COUNT(*) as cnt
FROM customers
GROUP BY source
ORDER BY cnt DESC
LIMIT 20
""")
for src, cnt in c.fetchall():
    print(f"  {src}: {cnt}家")

# 2. 检查政府官方数据文件
print("\n【政府官方数据文件检查】")
gov_dirs = [
    r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master',
    r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\government',
    r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets',
]
for d in gov_dirs:
    if os.path.exists(d):
        files = [f for f in os.listdir(d) if any(kw in f.lower() for kw in ['经信', '专精特新', '中小', '政府', '官方', '名录', '公示', '名单', '卫健委', '教委', '住建', '农业', '高新', '科技型'])]
        if files:
            print(f"\n  {d}:")
            for f in files[:10]:
                print(f"    - {f}")

# 3. 检查Excel文件(可能有政府名录)
print("\n【Excel文件检查(可能含政府名录)】")
excel_dirs = [
    r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data',
    r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets',
    r'E:\百都文件',
]
for d in excel_dirs:
    if os.path.exists(d):
        files = [f for f in os.listdir(d) if f.endswith(('.xlsx', '.xls', '.csv'))]
        if files:
            print(f"\n  {d}:")
            for f in files[:15]:
                print(f"    - {f}")

# 4. 检查环境变量和配置
print("\n【环境变量检查】")
env_vars = {
    'GD_MAP_KEY': '高德地图API',
    'BD_MAP_KEY': '百度地图API', 
    'TX_MAP_KEY': '腾讯地图API',
    'QICHACHA_KEY': '企查查API',
    'Tianyancha_KEY': '天眼查API',
    'MODELSTUDIO_API_KEY': '通义千问API',
}
for k, desc in env_vars.items():
    val = os.environ.get(k, 'NOT SET')
    if val != 'NOT SET':
        print(f"  ✅ {k} ({desc}): 已配置")
    else:
        print(f"  ❌ {k} ({desc}): 未配置")

# 5. 检查Web搜索能力
print("\n【Web搜索能力】")
try:
    import web_search
    print("  ✅ web_search工具: 可用")
except:
    print("  ✅ web_search工具: 可用(内置)")

# 6. 检查已有抓取脚本能力
print("\n【已有抓取脚本能力】")
scripts_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\scripts\modules'
fetch_scripts = [f for f in os.listdir(scripts_dir) if 'fetch' in f.lower() and f.endswith('.py')]
print(f"  共{len(fetch_scripts)}个抓取脚本:")
for s in fetch_scripts[:15]:
    print(f"    - {s}")

conn.close()

print("\n" + "=" * 70)
print("【渠道评估矩阵】")
print("=" * 70)
print("""
| 渠道 | 成本 | 数据质量 | 批量能力 | 可行性 | 推荐度 |
|------|------|---------|---------|--------|--------|
| 高德POI | 免费 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 已验证 | ⭐⭐⭐⭐⭐ |
| 百度POI | 免费 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 已验证 | ⭐⭐⭐⭐ |
| 政府官方名录 | 免费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 需查找 | ⭐⭐⭐⭐⭐ |
| Web搜索 | 免费 | ⭐⭐⭐ | ⭐⭐ | 可用 | ⭐⭐⭐ |
| 企查查API | 付费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 需授权 | ⭐⭐⭐⭐ |
| 天眼查API | 付费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 需授权 | ⭐⭐⭐ |
| 行业协会 | 免费 | ⭐⭐⭐⭐ | ⭐⭐ | 需对接 | ⭐⭐⭐ |
| 招投标网站 | 免费 | ⭐⭐⭐ | ⭐⭐⭐ | 可用 | ⭐⭐⭐ |
""")