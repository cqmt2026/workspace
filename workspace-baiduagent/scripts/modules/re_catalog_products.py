# -*- coding: utf-8 -*-
"""
重新梳理产品目录 - 包含新增文件
"""
import sys, os, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data/baidu'

# 扫描所有文件
print('='*70)
print('[Product Catalog Re-Cataloging]')
print('='*70)
print(f'Scan time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

all_files = []
for root, dirs, files in os.walk(DATA_DIR):
    for f in files:
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, DATA_DIR)
        size = os.path.getsize(full_path)
        all_files.append({
            'name': f,
            'path': full_path,
            'rel_path': rel_path,
            'size': size,
            'size_mb': round(size/1024/1024, 2)
        })

print(f'\n[Step 1] Total files: {len(all_files)}')
print(f'Total size: {sum(f["size_mb"] for f in all_files):.2f} MB')

# 产品分类规则（基于文件名关键词）
def classify_product(filename):
    """根据文件名分类产品"""
    fname_lower = filename.lower()
    
    # 百度搜索推广
    if any(kw in fname_lower for kw in ['搜索推广', 'sem', '百度推广', '推广通', '竞价', '关键词']):
        return '百度搜索推广'
    
    # 爱采购
    if '爱采购' in fname_lower or 'b2b' in fname_lower:
        return '爱采购'
    
    # GEO/AI搜索
    if any(kw in fname_lower for kw in ['geo', 'ai搜索', '智搜', '生成式', 'ai智推']):
        return 'GEO/AI搜索'
    
    # 百家号
    if '百家号' in fname_lower or 'baijia' in fname_lower:
        return '百家号'
    
    # 抖音快手
    if any(kw in fname_lower for kw in ['抖音', '快手', '巨量', 'douyin', 'local push', '本地推']):
        return '抖音快手'
    
    # 小红书
    if '小红书' in fname_lower or 'xhs' in fname_lower:
        return '小红书'
    
    # 商户通（美团医疗）
    if '商户通' in fname_lower:
        return '美团医疗-商户通'
    
    # 推广通（美团医疗）
    if '推广通' in fname_lower and '广告' not in fname_lower:
        return '美团医疗-推广通'
    
    # 行业数据/开发资料
    if any(kw in fname_lower for kw in ['行业开发', '行业数据', '行业参考', '旺季预警', '同行刺激']):
        return '行业开发资料'
    
    # 话术文档
    if any(kw in fname_lower for kw in ['话术', '销售', '谈判', '一页纸']):
        return '销售话术'
    
    # 企业查询数据
    if any(kw in fname_lower for kw in ['天眼查', '爱企查', '企业查询', '导出数据', '已打']):
        return '企业查询数据'
    
    # 报价单
    if '报价' in fname_lower or '价格' in fname_lower:
        return '报价单'
    
    # 产品通关/培训
    if any(kw in fname_lower for kw in ['通关', '培训', '手册', '指南', '标准']):
        return '产品培训'
    
    # 合同/授权
    if any(kw in fname_lower for kw in ['合同', '授权', '申请']):
        return '合同授权'
    
    # 案例
    if '案例' in fname_lower:
        return '客户案例'
    
    return '其他'

# 分类所有文件
print('\n[Step 2] Classifying files...')
catalog = {}
for f in all_files:
    category = classify_product(f['name'])
    if category not in catalog:
        catalog[category] = []
    catalog[category].append(f)

# 打印分类结果
print('\n' + '='*70)
print('[Classification Results]')
print('='*70)

total_size = 0
for category, files in sorted(catalog.items(), key=lambda x: -sum(f['size_mb'] for f in x[1])):
    size_mb = sum(f['size_mb'] for f in files)
    total_size += size_mb
    print(f'\n【{category}】({len(files)}个文件, {size_mb:.2f}MB)')
    for f in files[:5]:  # 显示前5个
        print(f'  - {f["name"][:50]}... ({f["size_mb"]:.2f}MB)')
    if len(files) > 5:
        print(f'  ... 共{len(files)}个文件')

print(f'\n总文件数: {len(all_files)}')
print(f'总大小: {total_size:.2f}MB')

# 产品目录定义（修正版）
PRODUCT_CATALOG = {
    '百度搜索推广': {
        'description': '搜索引擎营销，精准获客',
        'key_points': ['搜索排名', '关键词出价', '质量度', '落地页优化'],
        'target_industries': ['医疗器械', '机械装备', '新材料', '环保检测', '建筑建材'],
        'pricing': '按点击付费(CPC)，月预算3000-50000元',
        'file_count': len(catalog.get('百度搜索推广', []))
    },
    '爱采购': {
        'description': 'B2B工业品采购平台',
        'key_points': ['工业品展示', '长期获客', '资质背书'],
        'target_industries': ['机械装备', '汽配', '新材料', '化工', '五金工具'],
        'pricing': '年费制，约1-3万元/年',
        'file_count': len(catalog.get('爱采购', []))
    },
    'GEO/AI搜索': {
        'description': '生成式引擎优化，AI搜索时代新入口',
        'key_points': ['AI搜索优化', '品牌曝光', '未来流量入口'],
        'target_industries': ['所有行业'],
        'pricing': '服务费+效果付费',
        'file_count': len(catalog.get('GEO/AI搜索', []))
    },
    '百家号': {
        'description': '百度内容平台，品牌内容营销',
        'key_points': ['内容营销', '品牌曝光', 'SEO加持'],
        'target_industries': ['教育', '医疗', '企业品牌'],
        'pricing': '代运营费用+内容制作费',
        'file_count': len(catalog.get('百家号', []))
    },
    '抖音快手': {
        'description': '短视频平台广告投放',
        'key_points': ['短视频曝光', '信息流广告', '直播带货'],
        'target_industries': ['本地生活', '消费品牌', 'B2B品牌'],
        'pricing': '按播放付费(CPM)或按行动付费(CPA)',
        'file_count': len(catalog.get('抖音快手', []))
    },
    '小红书': {
        'description': '种草营销，品牌心智建设',
        'key_points': ['种草营销', '女性用户', '年轻群体'],
        'target_industries': ['医美', '母婴', '教育', '消费品牌'],
        'pricing': '代运营费用+广告投放费',
        'file_count': len(catalog.get('小红书', []))
    },
    '美团医疗-商户通': {
        'description': '美团医疗商户通，年费产品展示产品',
        'key_points': ['医疗机构信息展示', '长期曝光', '信任背书', '患者搜索可见'],
        'target_industries': ['口腔诊所', '医美机构', '眼科医院', '男科医院', '妇科医院'],
        'pricing': '年费制',
        'file_count': len(catalog.get('美团医疗-商户通', []))
    },
    '美团医疗-推广通': {
        'description': '美团医疗推广通，按点击付费广告产品',
        'key_points': ['精准搜索获客', '按点击付费', '可控预算', '效果可追踪'],
        'target_industries': ['口腔诊所', '医美机构', '眼科医院', '男科医院', '妇科医院'],
        'pricing': '按点击付费(CPC)',
        'file_count': len(catalog.get('美团医疗-推广通', []))
    },
    '行业开发资料': {
        'description': '行业数据、开发背景、旺季预警等参考资料',
        'key_points': ['行业数据', '竞品分析', '旺季预警'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('行业开发资料', []))
    },
    '销售话术': {
        'description': '销售话术、谈判技巧、一页纸等资料',
        'key_points': ['开场白', 'SPIN提问', '异议处理', '促单技巧'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('销售话术', []))
    },
    '企业查询数据': {
        'description': '天眼查/爱企查导出的企业数据',
        'key_points': ['企业工商信息', '联系方式', '经营范围'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('企业查询数据', []))
    },
    '报价单': {
        'description': '各产品报价单、价格表',
        'key_points': ['产品定价', '套餐方案', '优惠政策'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('报价单', []))
    },
    '产品培训': {
        'description': '产品培训材料、通关卡片、操作指南',
        'key_points': ['产品知识', '操作规范', '销售技巧'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('产品培训', []))
    },
    '合同授权': {
        'description': '客户合同、授权文件、申请表',
        'key_points': ['合同签订', '授权流程', '资质申请'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('合同授权', []))
    },
    '客户案例': {
        'description': '成功案例、客户反馈、效果展示',
        'key_points': ['案例分享', '效果数据', '客户证言'],
        'target_industries': ['所有行业'],
        'file_count': len(catalog.get('客户案例', []))
    },
    '其他': {
        'description': '未分类文件',
        'file_count': len(catalog.get('其他', []))
    }
}

# 保存产品目录
output_file = 'data/product_catalog_v2.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_files': len(all_files),
        'total_size_mb': round(total_size, 2),
        'catalog': PRODUCT_CATALOG,
        'file_details': {cat: [f['name'] for f in files] for cat, files in catalog.items()}
    }, f, ensure_ascii=False, indent=2)

print(f'\n💾 Product catalog saved: {output_file}')

# 打印详细分类
print('\n' + '='*70)
print('[Detailed Classification]')
print('='*70)

for category, info in PRODUCT_CATALOG.items():
    files = catalog.get(category, [])
    if files:
        print(f'\n【{category}】- {len(files)}个文件')
        for f in files:
            print(f'  - {f["name"][:60]}... ({f["size_mb"]:.2f}MB)')
