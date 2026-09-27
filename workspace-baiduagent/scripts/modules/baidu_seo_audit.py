# -*- coding: utf-8 -*-
"""
百度SEO审计工具 - GEO产品技术支持
融合来源: agency-agents/marketing/marketing-baidu-seo-specialist.md
功能: 百度SEO诊断、GEO优化建议、关键词策略
"""
import os
import json
from datetime import datetime

def baidu_seo_audit(company_name, industry):
    """
    百度SEO审计（简化版）
    """
    audit = {
        'company': company_name,
        'industry': industry,
        'audit_date': datetime.now().strftime('%Y-%m-%d'),
        'checklist': {
            'icp_filing': {
                'status': 'unknown',
                'importance': 'critical',
                'note': 'ICP备案是百度排名基础，无备案网站会被降权'
            },
            'baidu_index': {
                'status': 'unknown',
                'importance': 'high',
                'note': '使用site:命令检查收录情况'
            },
            'mobile_optimization': {
                'status': 'unknown',
                'importance': 'high',
                'note': '百度移动搜索占80%+，需适配'
            },
            'content_quality': {
                'status': 'unknown',
                'importance': 'medium',
                'note': '原创内容占比>80%，避免重复内容'
            },
            'page_speed': {
                'status': 'unknown',
                'importance': 'medium',
                'note': '移动端加载时间<2秒'
            },
            'structured_data': {
                'status': 'unknown',
                'importance': 'low',
                'note': 'JSON-LD结构化数据增强展现'
            }
        },
        'geography_keywords': [],
        'recommendations': []
    }
    
    # 基于行业的关键词建议
    keyword_mapping = {
        '口腔': ['重庆口腔', '重庆牙齿矫正', '重庆种植牙', '重庆洗牙', '重庆牙科医院'],
        '医美': ['重庆医美', '重庆整形', '重庆隆鼻', '重庆双眼皮', '重庆医美医院'],
        '机械': ['重庆机械', '重庆机床', '重庆机械设备', '重庆机械制造', '重庆机械厂家'],
        '建材': ['重庆建材', '重庆装修公司', '重庆建材市场', '重庆装饰材料'],
        '医疗': ['重庆医院', '重庆体检', '重庆男科医院', '重庆妇科医院', '重庆骨科医院'],
        '教培': ['重庆培训', '重庆教育', '重庆奥数', '重庆美术培训', '重庆英语培训']
    }
    
    for key, kws in keyword_mapping.items():
        if key in industry:
            audit['geography_keywords'] = kws
            break
    
    # 生成建议
    if not audit['geography_keywords']:
        audit['recommendations'].append('建议针对行业核心词做百度SEO优化')
    
    audit['recommendations'].extend([
        '建立百度站长平台账号，提交sitemap',
        '创建百度百科词条增强权威性',
        '在百度知道、百度贴吧布局行业问答',
        '发布百度经验文章提升品牌曝光'
    ])
    
    return audit

def geo_optimization_guide(industry):
    """
    GEO优化指南
    """
    guide = {
        'industry': industry,
        'goal': '让AI搜索（DeepSeek/豆包/Kimi等）推荐贵司',
        'steps': [
            {
                'step': 1,
                'action': '创建结构化企业文档',
                'detail': '在官网/公众号发布详细介绍，包含：企业全称、成立时间、主营产品、服务内容、联系方式',
                'priority': 'high'
            },
            {
                'step': 2,
                'action': '发布权威媒体文章',
                'detail': '在36氪、钛媒体、澎湃新闻等平台发布企业新闻，增加权威背书',
                'priority': 'high'
            },
            {
                'step': 3,
                'action': '创建知识型内容',
                'detail': '在知乎、小红书、公众号发布行业知识文章，建立专业形象',
                'priority': 'medium'
            },
            {
                'step': 4,
                'action': '百度百科/维基百科词条',
                'detail': '创建企业词条，包含完整的企业信息和权威引用',
                'priority': 'medium'
            },
            {
                'step': 5,
                'action': '监测AI推荐情况',
                'detail': '定期用DeepSeek/豆包搜索品牌词，检查是否被推荐',
                'priority': 'low'
            }
        ],
        'tools': [
            '百度指数（关键词热度）',
            '5118（关键词挖掘）',
            '站长工具（收录监测）',
            'ChatGPT/DeepSeek（效果验证）'
        ]
    }
    
    return guide

def generate_seo_report(company_name, industry):
    """
    生成SEO审计报告
    """
    audit = baidu_seo_audit(company_name, industry)
    geo_guide = geo_optimization_guide(industry)
    
    report = f"""# 🔍 {company_name} SEO审计与GEO优化报告

> 生成时间：{audit['audit_date']}
> 行业：{industry}

---

## 一、百度SEO基础审计

| 检查项 | 状态 | 重要性 | 说明 |
|--------|------|--------|------|
"""
    for item, data in audit['checklist'].items():
        report += f"| {item} | {data['status']} | {data['importance']} | {data['note']} |\n"
    
    report += f"""
## 二、关键词策略

{" **推荐关键词**：" + "、".join(audit['geography_keywords']) if audit['geography_keywords'] else " **暂无关键词数据**，建议补充行业关键词研究"}

## 三、GEO优化指南

### 目标
让AI搜索（DeepSeek/豆包/Kimi/元宝/文心一言/通义千问）推荐贵司

### 优化步骤

"""
    for step in geo_guide['steps']:
        priority_icon = '🔴' if step['priority'] == 'high' else ('🟡' if step['priority'] == 'medium' else '🟢')
        report += f"""#### {priority_icon} 步骤{step['step']}: {step['action']}
- **行动**：{step['detail']}
- **优先级**：{step['priority']}

"""
    
    report += f"""### 推荐工具
- {', '.join(geo_guide['tools'])}

---

## 四、下一步行动

"""
    for rec in audit['recommendations']:
        report += f"- [ ] {rec}\n"
    
    report += f"""
---
*本报告由百都GEO优化工具生成*
"""
    
    return report

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) >= 3:
        company = sys.argv[1]
        industry = sys.argv[2]
    else:
        company = '测试企业'
        industry = '口腔医疗'
    
    report = generate_seo_report(company, industry)
    print(report)
    
    # 保存报告
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'seo_report_{datetime.now().strftime("%Y%m%d")}.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ 报告已保存: {output_path}")
