# -*- coding: utf-8 -*-
"""生成机械行业明日拨打名单"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date, timedelta

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
output_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\明日拨打名单_2026-09-07_机械行业.md'

conn = sqlite3.connect(db_path)
c = conn.cursor()

today = date.today()
tomorrow = today + timedelta(days=1)

# 查询机械行业客户（修正字段名）
c.execute("""
    SELECT id, name, industry, tier, phone, source, last_call
    FROM customers
    WHERE industry LIKE '%%机械%%'
      AND phone IS NOT NULL
      AND phone != ''
      AND phone NOT LIKE '%%无%%'
    ORDER BY
        CASE tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END,
        id DESC
    LIMIT 30
""")
customers = c.fetchall()

print(f'机械行业客户总数: {len(customers)}')
print(f'生成时间: {today.strftime("%Y-%m-%d %H:%M")}')

# 生成MD文件
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f'''# 百都科技·明日拨打名单（机械行业）

**日期**: {tomorrow.strftime("%Y-%m-%d")}（周一）
**生成时间**: {today.strftime("%Y-%m-%d %H:%M")}
**行业**: 机械装备/汽配/五金工具/仪器仪表
**目标**: Top{len(customers)}家优先拨打

---

## 一、核心话术要点

**开场白（30秒）**：
```
"您好，我是百都科技小度。我们在做重庆机械企业的百度获客调研，
发现你们在'[行业词]'搜索上几乎没有品牌曝光，
等于把线上客户让给了外地竞品。
想了解一下你们现在的获客渠道，方便简单聊2分钟吗？"
```

**产品推荐组合**：
- 首选：百度搜索推广（3000-5000元测试）
- 次选：爱采购B2B平台（6980元/年起）
- 补充：GEO/AI搜索（4000-12800元/季）

**关键数据锚点**：
- 重庆机械企业801家，百度投放竞争几乎为零
- 单台设备产值数万~数百万元，客单价高
- 下游客户找供应商，百度是第一入口

---

## 二、Top{len(customers)}拨打清单

| 序号 | 企业 | 细分行业 | Tier | 电话 | 话术要点 |
|------|------|---------|------|------|---------|
''')

    for i, cust in enumerate(customers, 1):
        cid, name, industry, tier, phone, source, last_call = cust
        # 生成行业词
        industry_word = industry.replace('机械', '').replace('设备', '').strip() or '机械'
        search_term = f"重庆{industry_word}"
        
        # 话术建议
        script_hint = f"搜索词：'{search_term}'，竞品曝光弱"
        
        f.write(f"| {i} | {name[:25]} | {industry[:15]} | {tier} | {phone} | {script_hint} |\n")

    f.write('''
---

## 三、拨打策略

### 3.1 优先级排序
1. **Tier A客户**（20-30分钟/个）：详细侦察+完整SPIN+BANT评估
2. **Tier B客户**（10-15分钟/个）：快速侦察+核心痛点挖掘
3. **Tier C客户**（5-10分钟/个）：简短介绍+加微信发资料

### 3.2 时间分配
| 时间段 | 动作 | 目标 |
|--------|------|------|
| 9:00-9:30 | 侦察Top10（企查查+百度搜） | 准备话术锚点 |
| 9:30-11:30 | 第一批电话 | 10-15通 |
| 11:30-12:00 | 录入CRM+记录反馈 | 即时同步 |
| 14:00-16:00 | 第二批电话 | 10-15通 |
| 16:00-17:00 | 意向客户跟进 | 加微信5个+ |
| 17:00-17:30 | 复盘总结+日报生成 | 自动报表 |

### 3.3 每通电话必做
- [ ] 记录通话结果（接通/未接通/忙/拒接）
- [ ] 记录BANT评分（预算/权限/需求/时间表）
- [ ] 记录客户原话（用于话术优化）
- [ ] 意向客户当天加微信

---

## 四、关键提醒

1. **拨打前侦察**：搜公司名看百度现状，搜行业词看竞品投放
2. **立即录入**：每通电话后**立即**录入call_logs表
3. **跟进时机**：意向客户**当天**加微信，24小时内二次触达
4. **异议记录**：收集客户异议，明日复盘优化话术

---

_由小度生成 | 2026-09-06 | 机械行业专用_
''')

conn.close()
print(f'\n已生成名单文件: {output_path}')
print(f'共{len(customers)}家机械行业客户，明日优先拨打')
