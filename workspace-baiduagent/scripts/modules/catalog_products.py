# -*- coding: utf-8 -*-
"""
产品目录梳理脚本
整理百度旗下所有可售卖产品
"""
import sys, os, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data/baidu'

# 产品分类定义
PRODUCT_CATALOG = {
    '百度搜索推广': {
        'description': '搜索引擎营销，精准获客',
        'files': ['01百度搜索推广学员手册-学员版.docx', 
                  '2.1百度搜索推广-SEM优化入门.pdf',
                  '广告产品-推广通.pptx',
                  '年费产品-商户通介绍【FY25-20240919版】(1).pdf',
                  '百都科技公司百度推广简介.pdf'],
        'key_points': ['搜索排名', '关键词出价', '质量度', '落地页优化'],
        'target_industries': ['医疗器械', '机械装备', '新材料', '环保检测', '建筑建材']
    },
    '爱采购': {
        'description': 'B2B工业品采购平台',
        'files': ['0515 爱采购产品分享.xlsx',
                  '爱采购常见样式(1).pptx'],
        'key_points': ['工业品展示', '长期获客', '资质背书'],
        'target_industries': ['机械装备', '汽配', '新材料', '化工', '五金工具']
    },
    'GEO/AI搜索': {
        'description': '生成式引擎优化，AI搜索时代新入口',
        'files': ['AI搜索（GEO）产品介绍版202604.pdf',
                  'GEO.pdf',
                  'GEO产品培训材料.pptx',
                  'GEO产品销售攻略.pptx',
                  'GEO概述-20260714.pdf',
                  '智搜GEO介绍与报价2026（第四家）.pdf',
                  '第五家GEO价格.pdf',
                  '外贸快车GEO服务报价单5.20?Copy.pdf',
                  '【竞品针对话术】GEO产品销售攻略.pdf'],
        'key_points': ['AI搜索优化', '品牌曝光', '未来流量入口'],
        'target_industries': ['所有行业']
    },
    '百家号': {
        'description': '百度内容平台，品牌内容营销',
        'files': ['企业百家号教育行业运营指导手册-0817.pptx'],
        'key_points': ['内容营销', '品牌曝光', 'SEO加持'],
        'target_industries': ['教育', '医疗', '企业品牌']
    },
    '抖音快手': {
        'description': '短视频平台广告投放',
        'files': ['四川巨量两方【小红书抖音快手】推广信息技术服务合同（预存款、服务费）-2026版.pdf',
                  '抖音账号代运营客户信息调研表（客户填写）....docx'],
        'key_points': ['短视频曝光', '信息流广告', '直播带货'],
        'target_industries': ['本地生活', '消费品牌', 'B2B品牌']
    },
    '小红书': {
        'description': '种草营销，品牌心智建设',
        'files': ['小红书商业产品全景介绍(1)(2).pptx',
                  '小红书代运营服务清单.docx',
                  '小红书内容运营话术手册.docx',
                  '小红书代运营套餐20260416.xlsx'],
        'key_points': ['种草营销', '女性用户', '年轻群体'],
        'target_industries': ['医美', '母婴', '教育', '消费品牌']
    },
    '美团': {
        'description': '本地生活服务平台',
        'files': [],
        'key_points': ['到店消费', '团购套餐', '评价管理'],
        'target_industries': ['餐饮', '美容美发', '家政', '维修保养']
    },
    '商户通': {
        'description': '百度商户通，年费产品',
        'files': ['旺铺在线升级商户通流程&常见问题.docx'],
        'key_points': ['企业信息展示', '长期曝光', '信任背书'],
        'target_industries': ['所有本地生活企业']
    }
}

def scan_files():
    """扫描产品目录"""
    print('='*70)
    print('[Product Catalog Scanning]')
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
                'ext': os.path.splitext(f)[1].lower()
            })
    
    print(f'\n[Step 1] Scanned {len(all_files)} files')
    
    # Group by extension
    by_ext = {}
    for f in all_files:
        ext = f['ext'] or '(no extension)'
        if ext not in by_ext:
            by_ext[ext] = []
        by_ext[ext].append(f)
    
    print('\n[Step 2] Files by extension:')
    for ext, files in sorted(by_ext.items()):
        print(f'  {ext}: {len(files)} files')
    
    # Group by product category
    print('\n[Step 3] Files by product category:')
    catalog_result = {}
    for product, info in PRODUCT_CATALOG.items():
        matched = []
        for f in all_files:
            fname = f['name']
            for pf in info['files']:
                if pf.replace('.docx', '').replace('.pdf', '').replace('.xlsx', '').replace('.pptx', '') in fname.replace('.docx', '').replace('.pdf', '').replace('.xlsx', '').replace('.pptx', ''):
                    matched.append(f)
                    break
        
        # Also match by keywords
        for f in all_files:
            fname_lower = f['name'].lower()
            if product in ['百度搜索推广', '百度推广']:
                if any(kw in fname_lower for kw in ['搜索', '推广', 'sem', '百度']):
                    if f not in matched:
                        matched.append(f)
            elif product == 'GEO/AI搜索':
                if any(kw in fname_lower for kw in ['geo', 'ai搜索', '智搜', '生成式']):
                    if f not in matched:
                        matched.append(f)
            elif product == '爱采购':
                if '爱采购' in fname_lower or 'b2b' in fname_lower:
                    if f not in matched:
                        matched.append(f)
            elif product == '百家号':
                if '百家号' in fname_lower or 'baijia' in fname_lower:
                    if f not in matched:
                        matched.append(f)
            elif product == '抖音快手':
                if any(kw in fname_lower for kw in ['抖音', '快手', '巨量', 'douyin']):
                    if f not in matched:
                        matched.append(f)
            elif product == '小红书':
                if '小红书' in fname_lower or 'xhs' in fname_lower:
                    if f not in matched:
                        matched.append(f)
            elif product == '商户通':
                if '商户通' in fname_lower:
                    if f not in matched:
                        matched.append(f)
        
        catalog_result[product] = {
            'description': info['description'],
            'key_points': info['key_points'],
            'target_industries': info['target_industries'],
            'files': matched,
            'file_count': len(matched)
        }
        
        print(f'\n  {product}:')
        print(f'    描述: {info["description"]}')
        print(f'    核心要点: {", ".join(info["key_points"])}')
        print(f'    目标行业: {", ".join(info["target_industries"][:5])}')
        print(f'    文件数: {len(matched)}')
        for mf in matched[:5]:
            print(f'      - {mf["name"]}')
        if len(matched) > 5:
            print(f'      ... 共{len(matched)}个文件')
    
    # Save catalog
    output_file = 'data/product_catalog.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': len(all_files),
            'by_extension': {ext: len(files) for ext, files in by_ext.items()},
            'catalog': catalog_result
        }, f, ensure_ascii=False, indent=2)
    
    print(f'\n💾 Catalog saved: {output_file}')
    
    return catalog_result

if __name__ == '__main__':
    catalog = scan_files()
