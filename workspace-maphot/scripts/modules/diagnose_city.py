# -*- coding: utf-8 -*-
"""诊断城市查找问题"""
import sys, os, logging, json
logging.basicConfig(level=logging.WARNING)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from city_map_fetcher import CityMapAutoFetcher, PROVINCE_ADCODES, GEOJSON_DIR

f = CityMapAutoFetcher()

# 测试常州：下载江苏GeoJSON，看看里面有什么
print("=== 下载江苏GeoJSON ===")
province_data = f._load_geojson("江苏", 320000)
if province_data:
    features = province_data['features']
    print(f"江苏GeoJSON特征数: {len(features)}")
    # 看看前5个城市的level
    for feat in features[:5]:
        props = feat['properties']
        print(f'  name={props.get("name")}, level={props.get("level")}, adcode={props.get("adcode")}')
    
    # 搜索常州
    for feat in features:
        props = feat['properties']
        if '常州' in props.get('name', ''):
            print(f'  找到常州: name={props.get("name")}, level={props.get("level")}, adcode={props.get("adcode")}')

# 测试海南（三亚）
print("\n=== 下载海南GeoJSON ===")
hainan_data = f._load_geojson("海南", 460000)
if hainan_data:
    for feat in hainan_data['features']:
        props = feat['properties']
        if '三亚' in props.get('name', ''):
            print(f'  找到三亚: name={props.get("name")}, level={props.get("level")}, adcode={props.get("adcode")}')

# 看看省份GeoJSON的level值都有什么
print("\n=== 江苏GeoJSON level值 ===")
levels = set()
for feat in features:
    levels.add(feat['properties'].get('level', 'N/A'))
print(f'  levels: {levels}')