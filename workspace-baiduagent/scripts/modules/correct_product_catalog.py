# -*- coding: utf-8 -*-
"""
修正产品目录 - 商户通和推广通属于美团医疗专属产品
"""
import sys, os, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# 修正后的产品分类
CORRECTED_PRODUCT_CATALOG = {
    '百度搜索推广': {
        'description': '搜索引擎营销，精准获客',
        'key_points': ['搜索排名', '关键词出价', '质量度', '落地页优化'],
        'target_industries': ['医疗器械', '机械装备', '新材料', '环保检测', '建筑建材'],
        'pricing': '按点击付费(CPC)，月预算3000-50000元',
        'files': ['01百度搜索推广学员手册-学员版.docx', 
                  '2.1百度搜索推广-SEM优化入门.pdf',
                  '广告产品-推广通.pptx']
    },
    '爱采购': {
        'description': 'B2B工业品采购平台',
        'key_points': ['工业品展示', '长期获客', '资质背书'],
        'target_industries': ['机械装备', '汽配', '新材料', '化工', '五金工具'],
        'pricing': '年费制，约1-3万元/年',
        'files': ['0515 爱采购产品分享.xlsx',
                  '爱采购常见样式(1).pptx']
    },
    'GEO/AI搜索': {
        'description': '生成式引擎优化，AI搜索时代新入口',
        'key_points': ['AI搜索优化', '品牌曝光', '未来流量入口'],
        'target_industries': ['所有行业'],
        'pricing': '服务费+效果付费，具体报价需确认',
        'files': ['AI搜索（GEO）产品介绍版202604.pdf',
                  'GEO.pdf',
                  'GEO产品培训材料.pptx',
                  'GEO产品销售攻略.pptx',
                  'GEO概述-20260714.pdf',
                  '智搜GEO介绍与报价2026（第四家）.pdf',
                  '第五家GEO价格.pdf',
                  '外贸快车GEO服务报价单5.20?Copy.pdf',
                  '【竞品针对话术】GEO产品销售攻略.pdf']
    },
    '百家号': {
        'description': '百度内容平台，品牌内容营销',
        'key_points': ['内容营销', '品牌曝光', 'SEO加持'],
        'target_industries': ['教育', '医疗', '企业品牌'],
        'pricing': '代运营费用+内容制作费',
        'files': ['企业百家号教育行业运营指导手册-0817.pptx']
    },
    '抖音快手': {
        'description': '短视频平台广告投放',
        'key_points': ['短视频曝光', '信息流广告', '直播带货'],
        'target_industries': ['本地生活', '消费品牌', 'B2B品牌'],
        'pricing': '按播放付费(CPM)或按行动付费(CPA)',
        'files': ['四川巨量两方【小红书抖音快手】推广信息技术服务合同（预存款、服务费）-2026版.pdf',
                  '抖音账号代运营客户信息调研表（客户填写）....docx']
    },
    '小红书': {
        'description': '种草营销，品牌心智建设',
        'key_points': ['种草营销', '女性用户', '年轻群体'],
        'target_industries': ['医美', '母婴', '教育', '消费品牌'],
        'pricing': '代运营费用+广告投放费',
        'files': ['小红书商业产品全景介绍(1)(2).pptx',
                  '小红书代运营服务清单.docx',
                  '小红书内容运营话术手册.docx',
                  '小红书代运营套餐20260416.xlsx']
    },
    '美团医疗': {
        'description': '美团医疗专属产品矩阵',
        'products': {
            '商户通': {
                'description': '美团医疗商户通，年费产品展示产品',
                'key_points': ['医疗机构信息展示', '长期曝光', '信任背书', ' patients搜索可见'],
                'target_industries': ['口腔诊所', '医美机构', '眼科医院', '男科医院', '妇科医院', '白癜风医院', '白癜风医院'],
                'pricing': '年费制，具体需确认美团政策',
                'files': ['旺铺在线升级商户通流程&常见问题.docx',
                          '年费产品-商户通介绍【FY25-20240919版】(1).pdf']
            },
            '推广通': {
                'description': '美团医疗推广通，按点击付费广告产品',
                'key_points': ['精准搜索获客', '按点击付费', '可控预算', '效果可追踪'],
                'target_industries': ['口腔诊所', '医美机构', '眼科医院', '男科医院', '妇科医院', '白癜风医院', '白癜风医院'],
                'pricing': '按点击付费(CPC)，日预算可控',
                'files': ['广告产品-推广通.pptx']
            }
        },
        'key_points': ['美团医疗专属', '本地生活服务', '患者搜索入口', '评价管理'],
        'target_industries': ['口腔诊所', '医美机构', '眼科医院', '男科医院', '妇科医院', '白癜风医院', '白癜风医院', ' Dental clinics', ' Medical aesthetics'],
        'pricing': '商户通年费 + 推广通按点击付费',
        'files': ['旺铺在线升级商户通流程&常见问题.docx',
                  '年费产品-商户通介绍【FY25-20240919版】(1).pdf',
                  '广告产品-推广通.pptx',
                  '本地会员案例-下发版.pdf']
    },
    '美团本地生活': {
        'description': '美团本地生活服务平台（非医疗）',
        'products': {
            '团购套餐': {
                'description': '餐饮/美容/家政等团购优惠',
                'key_points': ['到店消费', '价格优势', '评价管理'],
                'target_industries': ['餐饮', '美容美发', '家政', '维修保养']
            }
        },
        'key_points': ['到店消费', '团购套餐', '评价管理'],
        'target_industries': ['餐饮', '美容美发', '家政', '维修保养'],
        'pricing': '佣金制或年费制',
        'files': []
    }
}

def print_catalog():
    """打印产品目录"""
    print('='*70)
    print('[Corrected Product Catalog]')
    print('='*70)
    print(f'Update time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70)
    
    for product, info in CORRECTED_PRODUCT_CATALOG.items():
        print(f'\n【{product}】')
        print(f'  描述: {info["description"]}')
        print(f'  核心卖点: {", ".join(info["key_points"])}')
        print(f'  目标行业: {", ".join(info["target_industries"][:5])}')
        
        if 'pricing' in info:
            print(f'  定价: {info["pricing"]}')
        
        if 'products' in info:
            print(f'  子产品:')
            for sub_product, sub_info in info['products'].items():
                print(f'    - {sub_product}: {sub_info["description"]}')
                print(f'      核心卖点: {", ".join(sub_info["key_points"])}')
                print(f'      目标行业: {", ".join(sub_info["target_industries"][:3])}')
        
        print(f'  文件数: {len(info.get("files", []))}')
    
    # Save corrected catalog
    output_file = 'data/product_catalog_corrected.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(CORRECTED_PRODUCT_CATALOG, f, ensure_ascii=False, indent=2)
    print(f'\n💾 Corrected catalog saved: {output_file}')
    
    # Update MEMORY.md
    print('\n[Step 2] Updating MEMORY.md...')
    memory_file = 'MEMORY.md'
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add product catalog section
    product_section = '''
---

## 📦 产品目录（已修正）

### 百度系产品
| 产品 | 类型 | 目标行业 | 定价模式 |
|------|------|---------|---------|
| 百度搜索推广 | CPC广告 | 医疗/机械/新材料/环保 | 按点击付费 |
| 爱采购 | B2B平台 | 机械/汽配/新材料 | 年费制 |
| GEO/AI搜索 | 搜索优化 | 所有行业 | 服务费+效果付费 |
| 百家号 | 内容平台 | 教育/医疗/企业品牌 | 代运营费 |
| 抖音快手 | 短视频广告 | 本地生活/消费品牌 | CPM/CPA |
| 小红书 | 种草营销 | 医美/母婴/教育 | 代运营+广告费 |

### 美团系产品
| 产品 | 类型 | 目标行业 | 定价模式 |
|------|------|---------|---------|
| **商户通** | 年费展示 | 口腔/医美/眼科/男科/妇科 | 年费制 |
| **推广通** | CPC广告 | 口腔/医美/眼科/男科/妇科 | 按点击付费 |
| 团购套餐 | 到店优惠 | 餐饮/美容/家政 | 佣金制 |

> ⚠️ **重要更正**：商户通和推广通是**美团医疗专属产品**，不是百度产品！
> 目标行业：口腔诊所、医美机构、眼科医院、男科医院、妇科医院、白癜风医院

---
'''
    
    # Insert before the last section
    if '## 📦 产品目录' not in content:
        content = content.replace('## 🔗 跨系统引用', product_section + '\n## 🔗 跨系统引用')
    
    with open(memory_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('  MEMORY.md updated')

if __name__ == '__main__':
    print_catalog()
