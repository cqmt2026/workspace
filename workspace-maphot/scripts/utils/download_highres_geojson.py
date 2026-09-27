# -*- coding: utf-8 -*-
"""下载高精度GeoJSON - simplemaps.com"""
import urllib.request, json, os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_dir = os.path.join(BASE_DIR, 'data', 'cache', 'geojson')
os.makedirs(out_dir, exist_ok=True)

# simplemaps 提供的中国省级边界GeoJSON（admin level 1, 7.5MB）
url = 'https://simplemaps.com/static/geojson/country/cn/1/1/1.geojson'

print('下载中...')
try:
    req = urllib.request.urlopen(url, timeout=60)
    data = json.loads(req.read().decode('utf-8'))
    out_path = os.path.join(out_dir, 'china_simplemaps.geojson')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    sz = os.path.getsize(out_path) // 1024
    features = data.get('features', [])
    print('下载完成: {}KB, {}个特征'.format(sz, len(features)))
    # 查看第一个特征的结构
    if features:
        feat = features[0]
        props = feat.get('properties', {})
        print('属性字段:', list(props.keys()))
        print('name字段:', props.get('name', ''))
        # 检查坐标点数量
        geom = feat.get('geometry', {})
        coords = str(geom.get('coordinates', ''))
        print('坐标长度:', len(coords))
except Exception as e:
    print('失败:', e)
    # 备用：从GitHub xyanmi/MapData下载
    print('尝试备用源...')
    try:
        url2 = 'https://raw.githubusercontent.com/xyanmi/MapData/main/provinces.cn.geojson'
        req = urllib.request.urlopen(url2, timeout=60)
        data = json.loads(req.read().decode('utf-8'))
        out_path = os.path.join(out_dir, 'china_xyanmi.geojson')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        sz = os.path.getsize(out_path) // 1024
        features = data.get('features', [])
        print('备用源下载完成: {}KB, {}个特征'.format(sz, len(features)))
    except Exception as e2:
        print('备用源也失败:', e2)