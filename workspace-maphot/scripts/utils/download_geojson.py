# -*- coding: utf-8 -*-
"""下载高精度GeoJSON"""
import urllib.request, json, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_dir = os.path.join(BASE_DIR, 'data', 'cache', 'geojson')
os.makedirs(out_dir, exist_ok=True)

urls = [
    'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json',
    'https://geo.datav.aliyun.com/areas_v3/bound/100000.json',
]

for url in urls:
    print('尝试:', url)
    try:
        req = urllib.request.urlopen(url, timeout=30)
        data = json.loads(req.read().decode('utf-8'))
        out_path = os.path.join(out_dir, 'china_full.geojson')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        sz = os.path.getsize(out_path) // 1024
        print('下载完成: {}KB, 特征数: {}'.format(sz, len(data.get('features', []))))
        break
    except Exception as e:
        print('失败:', e)
else:
    print('所有URL均失败')
    # 检查现有文件
    print('使用现有文件:', os.path.exists(os.path.join(out_dir, 'china_full.geojson')))