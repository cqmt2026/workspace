# -*- coding: utf-8 -*-
"""
地图绘制模块 - GeoJSON加载器
职责：从DataV API下载GeoJSON，缓存到本地
"""

import os
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOJSON_DIR = os.path.join(BASE_DIR, 'data', 'cache', 'geojson')

# DataV GeoJSON API
DATAV_URL_TEMPLATE = "https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json"


class GeoJSONLoader:
    """GeoJSON加载器"""
    
    def __init__(self):
        os.makedirs(GEOJSON_DIR, exist_ok=True)
    
    def load(self, city, adcode):
        """
        加载城市GeoJSON
        
        Args:
            city: 城市名（用于文件名）
            adcode: 行政区划代码（如500000）
            
        Returns:
            dict: GeoJSON数据，或None
        """
        # 1. 检查本地缓存
        local_path = os.path.join(GEOJSON_DIR, f'{city}.geojson')
        if os.path.exists(local_path):
            logger.info(f"从缓存加载GeoJSON: {local_path}")
            with open(local_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 2. 从DataV下载
        logger.info(f"下载GeoJSON: {city}({adcode})")
        url = DATAV_URL_TEMPLATE.format(adcode=adcode)
        
        try:
            urllib.request.urlretrieve(url, local_path)
            logger.info(f"下载成功: {local_path}")
            with open(local_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"下载GeoJSON失败: {e}")
            return None
    
    def get_provinces(self):
        """
        获取中国省份GeoJSON
        
        Returns:
            list: [{name, adcode, feature}, ...]
        """
        # 检查缓存
        local_path = os.path.join(GEOJSON_DIR, 'china.geojson')
        if os.path.exists(local_path):
            logger.info(f"从缓存加载GeoJSON: {local_path}")
            with open(local_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            provinces = []
            for feature in data['features']:
                props = feature['properties']
                name = props.get('name', '')
                adcode_val = props.get('adcode', '')
                level = props.get('level', '')
                if name and level == 'province':
                    provinces.append({
                        'name': name,
                        'adcode': adcode_val,
                        'feature': feature
                    })
            logger.info(f"加载{len(provinces)}个省份")
            return provinces
        
        # 从DataV下载全国GeoJSON
        url = DATAV_URL_TEMPLATE.format(adcode='')
        try:
            urllib.request.urlretrieve(url, local_path)
            with open(local_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            provinces = []
            for feature in data['features']:
                props = feature['properties']
                name = props.get('name', '')
                adcode_val = props.get('adcode', '')
                level = props.get('level', '')
                if name and level == 'province':
                    provinces.append({
                        'name': name,
                        'adcode': adcode_val,
                        'feature': feature
                    })
            logger.info(f"加载{len(provinces)}个省份: {local_path}")
            return provinces
        except Exception as e:
            logger.error(f"下载GeoJSON失败: {e}")
            return []
    
    def get_districts(self, city, adcode):
        """
        获取区县列表
        
        Returns:
            list: [{name, adcode, feature}, ...]
        """
        data = self.load(city, adcode)
        if not data:
            return []
        
        districts = []
        for feature in data['features']:
            props = feature['properties']
            name = props.get('name', '')
            adcode_val = props.get('adcode', '')
            if name:
                districts.append({
                    'name': name,
                    'adcode': adcode_val,
                    'feature': feature
                })
        
        logger.info(f"加载{len(districts)}个区县: {city}")
        return districts


if __name__ == '__main__':
    loader = GeoJSONLoader()
    dists = loader.get_districts('重庆', '500000')
    for d in dists[:5]:
        print(f"  {d['name']} ({d['adcode']})")