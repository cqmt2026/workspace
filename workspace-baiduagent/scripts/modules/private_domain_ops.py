# -*- coding: utf-8 -*-
"""
私域运营流程 - 企微管理
融合来源: agency-agents/marketing/marketing-private-domain-operator.md
功能: 客户分层、触达策略、复购激励
"""
import sqlite3
import os
from datetime import datetime, date
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def segment_customers_for_private_domain():
    """
    客户分层（RFM模型简化版）
    """
    conn = get_conn()
    c = conn.cursor()
    
    # R - Recency: 最近联系时间
    c.execute('''
        SELECT id, name, status, last_call 
        FROM customers 
        WHERE last_call IS NOT NULL AND last_call != ''
        ORDER BY last_call DESC
    ''')
    recent_customers = c.fetchall()
    
    # F - Frequency: 联系频率
    c.execute('''
        SELECT customer_id, COUNT(*) as freq
        FROM call_logs
        GROUP BY customer_id
        ORDER BY freq DESC
    ''')
    frequency_data = dict(c.fetchall())
    
    # M - Monetary: 成交金额（简化为状态）
    tier_a = []
    tier_b = []
    tier_c = []
    
    c.execute("SELECT id, name, industry FROM customers WHERE tier = 'A'")
    tier_a = c.fetchall()
    
    c.execute("SELECT id, name, industry FROM customers WHERE tier = 'B'")
    tier_b = c.fetchall()
    
    c.execute("SELECT id, name, industry FROM customers WHERE tier = 'C'")
    tier_c = c.fetchall()
    
    conn.close()
    
    return {
        'tier_a': tier_a,
        'tier_b': tier_b,
        'tier_c': tier_c,
        'recent_contacts': recent_customers[:20],
        'high_frequency': sorted(frequency_data.items(), key=lambda x: -x[1])[:20]
    }

def get_wechat_touch_strategy(customer_tier):
    """
    获取企微触达策略
    """
    strategies = {
        'A': {
            'frequency': '每周1次',
            'content_type': '行业报告+案例分享',
            'tone': '专业顾问',
            'goal': '深度信任+大额转化'
        },
        'B': {
            'frequency': '每两周1次',
            'content_type': '行业资讯+优惠政策',
            'tone': '友好专业',
            'goal': '培养意向+适度跟进'
        },
        'C': {
            'frequency': '每月1次',
            'content_type': '节日问候+品牌曝光',
            'tone': '轻松友好',
            'goal': '保持触达+等待时机'
        }
    }
    return strategies.get(customer_tier, strategies['C'])

def generate_wechat_content(customer_info, strategy):
    """
    生成微信内容
    """
    name = customer_info.get('name', '客户')
    industry = customer_info.get('industry', '行业')
    tier = customer_info.get('tier', 'C')
    
    templates = {
        'A': f"""【{industry}行业洞察】

{name}总您好，我是百都小度。

最近整理了《{industry}行业百度获客白皮书》，发现一些有趣的数据：
• {industry}行业百度搜索量同比增长XX%
• 头部客户平均获客成本降低XX%
• XX案例月增客户XX个

需要的话我发您看看，希望对您有帮助。

祝商祺！""",
        
        'B': f"""【{industry}行业动态】

{name}总您好，我是百都小度。

最近{industry}行业有几个新动态：
1. 百度推出XX新产品，适合{industry}企业
2. 同行XX已经上线，效果不错
3. 本月有优惠活动，性价比很高

感兴趣的话可以聊聊，免费帮您做个诊断。

祝好！""",
        
        'C': f"""【节日问候】

{name}总您好，我是百都小度。

{datetime.now().strftime('%m月%d日')}是XX节，祝您节日快乐！

最近我们做了很多{industry}行业的案例，有需要随时找我。

祝生意兴隆！"""
    }
    
    return templates.get(tier, templates['C'])

def generate_private_domain_plan():
    """
    生成私域运营计划
    """
    segments = segment_customers_for_private_domain()
    
    plan = f"""# 📱 私域运营计划

> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 一、客户分层概览

| 层级 | 数量 | 触达频率 | 核心目标 |
|------|------|----------|----------|
"""
    
    plan += f"| 🔴 Tier A | {len(segments['tier_a'])}家 | 每周1次 | 深度信任+大额转化 |\n"
    plan += f"| 🟡 Tier B | {len(segments['tier_b'])}家 | 每两周1次 | 培养意向+适度跟进 |\n"
    plan += f"| 🟢 Tier C | {len(segments['tier_c'])}家 | 每月1次 | 保持触达+等待时机 |\n"
    
    plan += f"""
## 二、重点客户清单（Tier A）

"""
    for i, (cid, name, industry) in enumerate(segments['tier_a'][:10], 1):
        strategy = get_wechat_touch_strategy('A')
        plan += f"{i}. **{name}** ({industry})\n"
        plan += f"   策略: {strategy['frequency']} | {strategy['content_type']}\n\n"
    
    plan += f"""
## 三、内容日历（下周）

| 日期 | 对象 | 内容类型 | 发送时间 |
|------|------|----------|----------|
| 周一 | Tier A | 行业报告 | 10:00 |
| 周三 | Tier B | 行业资讯 | 15:00 |
| 周五 | Tier C | 节日问候 | 09:00 |

## 四、执行要点

1. **内容个性化**：根据客户行业定制内容
2. **频率控制**：避免过度打扰，分层触达
3. **互动跟踪**：记录客户反馈，及时调整策略
4. **转化引导**：自然引导到电话沟通或上门拜访

---
*私域运营核心：价值先行，不急于推销*
"""
    
    return plan

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("📱 私域运营计划生成器")
    print("=" * 70)
    
    plan = generate_private_domain_plan()
    print(plan)
    
    # 保存计划
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'private_domain_plan_{datetime.now().strftime("%Y%m%d")}.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(plan)
    print(f"\n✅ 计划已保存: {output_path}")
