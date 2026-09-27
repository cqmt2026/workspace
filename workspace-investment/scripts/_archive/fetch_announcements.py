"""
获取商业航天核心标的的公司公告
"""
import requests
import json
import os
from datetime import datetime

output_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\memory\L2-核心\行业研报'
os.makedirs(output_dir, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0'}

# 商业航天12只核心标的
cs_stocks = [
    ('600118', '中国卫星', 'SH'),
    ('300034', '钢研高纳', 'SZ'),
    ('300699', '光威复材', 'SZ'),
    ('300777', '中简科技', 'SZ'),
    ('688268', '华特气体', 'SH'),
    ('300394', '天孚通信', 'SZ'),
    ('688146', '中船特气', 'SH'),
    ('688239', '航宇科技', 'SH'),
    ('688510', '航亚科技', 'SH'),
    ('688281', '华秦科技', 'SH'),
    ('600893', '航发动力', 'SH'),
    ('688313', '仕佳光子', 'SH'),
]

def fetch_announcements(code, market, page_size=10):
    """获取公告（侧重重大合同/招标/业务进展）"""
    # 东方财富公告API
    ann_types = 'SHA,SZA,CYB,SZA,SHA'  # 上交所+深交所+创业板
    url = f'https://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&page_size={page_size}&page_index=1&ann_type={ann_types}&client_source=web&stock_list={code}'
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get('data') and data['data'].get('list'):
                return data['data']['list']
    except Exception as e:
        pass
    return []

def parse_announcement(ann):
    """解析公告"""
    cols = ann.get('columns', [])
    col_names = [c.get('column_name', '') for c in cols]
    col_codes = [c.get('column_code', '') for c in cols]
    
    return {
        'art_code': ann.get('art_code', ''),
        'stock_code': ann.get('stock_list', [{}])[0].get('stock_code', '') if ann.get('stock_list') else '',
        'short_name': ann.get('short_name', ''),
        'column_names': col_names,
        'display_time': ann.get('display_time', ''),
    }

# 关键词筛选
keyword_filter = ['合同', '中标', '招标', '投资', '合作', '订单', '发射', '卫星', '火箭', '公告']

print('开始获取公告...')
all_anns = []
for code, name, market in cs_stocks:
    print(f'\n[{code}] {name}...')
    anns = fetch_announcements(code, market, page_size=20)
    
    # 筛选关键词
    filtered = []
    for ann in anns:
        cols = ann.get('columns', [])
        col_names = ' '.join([c.get('column_name', '') for c in cols])
        if any(kw in col_names for kw in keyword_filter):
            filtered.append(ann)
    
    print(f'  获取{len(anns)}条公告，过滤后{len(filtered)}条相关')
    
    for ann in filtered[:5]:
        cols = ann.get('columns', [])
        col_str = ' | '.join([c.get('column_name', '') for c in cols])
        print(f'  [{ann.get("display_time", "")[:10]}] {col_str}')
    
    all_anns.extend([{**a, 'stock_code': code} for a in filtered])

print(f'\n总计相关公告: {len(all_anns)}条')

# 保存
with open(os.path.join(output_dir, '商业航天公告.json'), 'w', encoding='utf-8') as f:
    json.dump(all_anns, f, ensure_ascii=False, indent=2)

print(f'已保存到 商业航天公告.json')
