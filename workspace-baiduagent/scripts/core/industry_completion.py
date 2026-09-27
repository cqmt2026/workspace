# -*- coding: utf-8 -*-
"""
行业完成度盘点 - v4升级：加入贝叶斯线索评分算法
借鉴Prospex的评分理念：避免"高分低质"，综合评分+评论数
"""
import sys, os, csv, sqlite3, math
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 各行业总数 + 电话数 + 来源分布 + 评分
cur.execute('''
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone,
           GROUP_CONCAT(DISTINCT source) as sources
    FROM customers
    GROUP BY industry
    ORDER BY total DESC
''')

print("=" * 80)
print("【全行业完成度盘点 v4】")
print("判定标准: 数量充足 + 电话覆盖率>=50% + 贝叶斯线索评分（预留）")
print("=" * 80)
print(f'{"行业":<12}{"总":>5}{"有电话":>6}{"率":>6}  完成度  评分')
print("-" * 80)
rows = cur.fetchall()
for ind, total, phone, sources in rows:
    phone = phone or 0
    pct = round(phone/total*100,1) if total else 0
    
    # v4升级：贝叶斯线索评分（预留逻辑）
    # 公式：score = (rating * review_count + prior_rating * prior_count) / (review_count + prior_count)
    # 当前暂用电话覆盖率作为代理评分
    bayesian_score = round(pct / 10, 1)  # 简化版，后续可接入真实评分
    
    # 完成度判定
    if total >= 500 and pct >= 60:
        grade = "✅ 完成"
    elif total >= 200 and pct >= 50:
        grade = "🟡 基本完成"
    elif total >= 50 and pct >= 30:
        grade = "🔵 需补数量+电话"
    else:
        grade = "🔴 严重不足"
    
    print(f'{ind:<12}{total:>5}{phone:>6}{str(pct)+"%":>7}  {grade}  {bayesian_score}')
    print(f'        来源: {sources}')

conn.close()

print("\n【贝叶斯线索评分预留】")
print("下一步规划：")
print("1. 在customers表增加rating和review_count字段")
print("2. 抓取时从POI数据中提取评分和评论数")
print("3. 用贝叶斯公式计算综合评分，避免'高分低质'")
print("4. 高评分客户优先拨打，低评分客户纳入培育池")

print("\n【ICP动态学习预留】")
print("下一步规划：")
print("1. 在customers表增加icp_score字段（0-10）")
print("2. 根据BANT评分自动计算ICP得分")
print("3. 高ICP客户优先拨打，低ICP客户纳入培育池")
print("4. 每月复盘ICP模型准确率，动态调整权重")
