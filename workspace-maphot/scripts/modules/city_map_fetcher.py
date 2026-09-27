# -*- coding: utf-8 -*-
"""
City Map Auto Fetcher Module
Auto-detect city province, fetch GeoJSON, generate city config
"""

import os
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOJSON_DIR = os.path.join(BASE_DIR, 'data', 'cache', 'geojson')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')

# DataV GeoJSON API
DATAV_URL_TEMPLATE = "https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json"

# China province adcode mapping
PROVINCE_ADCODES = {
    "北京": 110000, "天津": 120000, "河北": 130000, "山西": 140000,
    "内蒙古": 150000, "辽宁": 210000, "吉林": 220000, "黑龙江": 230000,
    "上海": 310000, "江苏": 320000, "浙江": 330000, "安徽": 340000,
    "福建": 350000, "江西": 360000, "山东": 370000, "河南": 410000,
    "湖北": 420000, "湖南": 430000, "广东": 440000, "广西": 450000,
    "海南": 460000, "重庆": 500000, "四川": 510000, "贵州": 520000,
    "云南": 530000, "西藏": 540000, "陕西": 610000, "甘肃": 620000,
    "青海": 630000, "宁夏": 640000, "新疆": 650000, "台湾": 710000,
    "香港": 810000, "澳门": 820000,
}

# Municipalities (adcode is city-level directly)
MUNICIPALITIES = {"北京": 110000, "天津": 120000, "上海": 310000, "重庆": 500000}

# Major city adcodes (prefecture-level)
CITY_ADCODES = {
    "深圳": 440300, "广州": 440100, "珠海": 440400, "东莞": 441900,
    "佛山": 440600, "中山": 442000, "惠州": 441300, "杭州": 330100,
    "宁波": 330200, "温州": 330300, "成都": 510100, "武汉": 420100,
    "南京": 320100, "苏州": 320500, "无锡": 320200, "西安": 610100,
    "长沙": 430100, "郑州": 410100, "济南": 370100, "青岛": 370200,
    "厦门": 350200, "福州": 350100, "合肥": 340100, "昆明": 530100,
    "沈阳": 210100, "大连": 210200, "哈尔滨": 230100, "长春": 220100,
    "南昌": 360100, "太原": 140100, "贵阳": 520100, "南宁": 450100,
    "海口": 460100, "兰州": 620100, "银川": 640100, "西宁": 630100,
    "拉萨": 540100, "乌鲁木齐": 650100,
}


class CityMapAutoFetcher:
    """City map auto fetcher"""
    
    def __init__(self):
        os.makedirs(GEOJSON_DIR, exist_ok=True)
        os.makedirs(CONFIG_DIR, exist_ok=True)
    
    def get_city_adcode(self, city_name):
        """
        Get city adcode by name
        
        Args:
            city_name: City name (e.g. "深圳", "广州")
            
        Returns:
            int: adcode, or None
        """
        # 1. Preset mapping
        if city_name in CITY_ADCODES:
            return CITY_ADCODES[city_name]
        
        # 2. Municipalities
        if city_name in MUNICIPALITIES:
            return MUNICIPALITIES[city_name]
        
        # 3. Search from province GeoJSON
        province_name = self._guess_province(city_name)
        if not province_name:
            logger.warning(f"Cannot determine province for {city_name}")
            return None
        
        province_adcode = PROVINCE_ADCODES.get(province_name)
        if not province_adcode:
            return None
        
        province_data = self._load_geojson(province_name, province_adcode)
        if not province_data:
            return None
        
        for feature in province_data['features']:
            props = feature['properties']
            geo_name = props.get('name', '')
            # GeoJSON中城市名带"市"后缀，需要模糊匹配
            if geo_name == city_name or geo_name == city_name + '市':
                if props.get('level') == 'city':
                    return int(props['adcode'])
        
        logger.warning(f"City {city_name} not found in {province_name}")
        return None
    
    def _guess_province(self, city_name):
        """
        Guess province by city name
        
        Args:
            city_name: City name
            
        Returns:
            str: Province name, or None
        """
        city_to_province = {
            # Guangdong
            "深圳": "广东", "广州": "广东", "珠海": "广东", "东莞": "广东",
            "佛山": "广东", "中山": "广东", "惠州": "广东", "汕头": "广东",
            "韶关": "广东", "湛江": "广东", "肇庆": "广东", "江门": "广东",
            "茂名": "广东", "梅州": "广东", "汕尾": "广东", "河源": "广东",
            "阳江": "广东", "清远": "广东", "潮州": "广东", "揭阳": "广东",
            "云浮": "广东",
            # Zhejiang
            "杭州": "浙江", "宁波": "浙江", "温州": "浙江", "嘉兴": "浙江",
            "湖州": "浙江", "绍兴": "浙江", "金华": "浙江", "衢州": "浙江",
            "舟山": "浙江", "台州": "浙江", "丽水": "浙江",
            # Jiangsu
            "南京": "江苏", "苏州": "江苏", "无锡": "江苏", "常州": "江苏",
            "徐州": "江苏", "南通": "江苏", "连云港": "江苏", "淮安": "江苏",
            "盐城": "江苏", "扬州": "江苏", "镇江": "江苏", "泰州": "江苏",
            "宿迁": "江苏",
            # Sichuan
            "成都": "四川", "绵阳": "四川", "德阳": "四川", "宜宾": "四川",
            "南充": "四川", "泸州": "四川", "自贡": "四川",
            # Hubei
            "武汉": "湖北", "襄阳": "湖北", "宜昌": "湖北", "荆州": "湖北",
            # Shaanxi
            "西安": "陕西", "咸阳": "陕西", "宝鸡": "陕西",
            # Hunan
            "长沙": "湖南", "株洲": "湖南", "湘潭": "湖南", "衡阳": "湖南",
            # Henan
            "郑州": "河南", "洛阳": "河南", "开封": "河南", "南阳": "河南",
            # Shandong
            "济南": "山东", "青岛": "山东", "烟台": "山东", "潍坊": "山东",
            "临沂": "山东", "淄博": "山东", "济宁": "山东",
            # Fujian
            "厦门": "福建", "福州": "福建", "泉州": "福建", "漳州": "福建",
            # Anhui
            "合肥": "安徽", "芜湖": "安徽", "马鞍山": "安徽", "蚌埠": "安徽",
            # Yunnan
            "昆明": "云南", "大理": "云南", "丽江": "云南",
            # Liaoning
            "沈阳": "辽宁", "大连": "辽宁", "鞍山": "辽宁",
            # Heilongjiang
            "哈尔滨": "黑龙江", "大庆": "黑龙江",
            # Jilin
            "长春": "吉林", "吉林": "吉林",
            # Jiangxi
            "南昌": "江西", "九江": "江西", "赣州": "江西",
            # Shanxi
            "太原": "山西", "大同": "山西",
            # Guizhou
            "贵阳": "贵州", "遵义": "贵州",
            # Guangxi
            "南宁": "广西", "桂林": "广西", "北海": "广西",
            # Hainan
            "海口": "海南", "三亚": "海南",
            # Gansu
            "兰州": "甘肃", "天水": "甘肃",
            # Ningxia
            "银川": "宁夏",
            # Qinghai
            "西宁": "青海",
            # Tibet
            "拉萨": "西藏",
            # Xinjiang
            "乌鲁木齐": "新疆",
            # Municipalities
            "北京": "北京", "上海": "上海", "天津": "天津", "重庆": "重庆",
            "香港": "香港", "澳门": "澳门",
        }
        return city_to_province.get(city_name)
    
    def _load_geojson(self, name, adcode):
        """
        Load GeoJSON (cache first)
        
        Args:
            name: Place name
            adcode: Adcode
            
        Returns:
            dict: GeoJSON data
        """
        local_path = os.path.join(GEOJSON_DIR, f'{name}.geojson')
        
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        url = DATAV_URL_TEMPLATE.format(adcode=adcode)
        try:
            logger.info(f"Downloading GeoJSON: {name}({adcode})")
            urllib.request.urlretrieve(url, local_path)
            with open(local_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def get_districts(self, city_name, adcode=None):
        """
        Get city districts list
        
        Args:
            city_name: City name
            adcode: Optional adcode
            
        Returns:
            list: [{name, adcode, feature}, ...]
        """
        if not adcode:
            adcode = self.get_city_adcode(city_name)
        if not adcode:
            return []
        
        data = self._load_geojson(city_name, adcode)
        if not data:
            return []
        
        districts = []
        for feature in data['features']:
            props = feature['properties']
            name = props.get('name', '')
            adcode_val = props.get('adcode', '')
            level = props.get('level', '')
            if name and level == 'district':
                districts.append({
                    'name': name,
                    'adcode': adcode_val,
                    'feature': feature
                })
        
        logger.info(f"Got {len(districts)} districts for {city_name}")
        return districts
    
    def auto_generate_city_config(self, city_name):
        """
        Auto generate city config JSON
        
        Args:
            city_name: City name
            
        Returns:
            dict: City config, or None
        """
        adcode = self.get_city_adcode(city_name)
        if not adcode:
            return None
        
        districts = self.get_districts(city_name, adcode)
        if not districts:
            return None
        
        config = {
            "city": city_name,
            "year": "2026",
            "total_gdp": "待获取",
            "gdp_rank": "待获取",
            "area": "待获取",
            "population": "待获取",
            "districts": [
                {
                    "name": d['name'],
                    "gdp": "待获取",
                    "gdp_raw": 0,
                    "per_gdp": "待获取",
                    "pct": "待获取",
                    "desc": "待填写",
                    "tag": "待填写"
                }
                for d in districts
            ],
            "opt_a": "待填写",
            "opt_b": "待填写",
            "opt_c": "待填写",
            "adcode": adcode
        }
        
        config_path = os.path.join(CONFIG_DIR, f'city_{city_name}.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Auto-generated city config: {config_path}")
        return config


if __name__ == '__main__':
    fetcher = CityMapAutoFetcher()
    
    print('=== 深圳区县 ===')
    dists = fetcher.get_districts('深圳')
    for d in dists[:5]:
        print(f'  {d["name"]} ({d["adcode"]})')
    
    print('\n=== 广州自动配置 ===')
    config = fetcher.auto_generate_city_config('广州')
    if config:
        print(f'  adcode: {config.get("adcode")}')
        print(f'  区县数: {len(config["districts"])}')
        print(f'  前3区: {[d["name"] for d in config["districts"][:3]]}')
    else:
        print('  失败')
    
    print('\n=== 成都自动配置 ===')
    config = fetcher.auto_generate_city_config('成都')
    if config:
        print(f'  adcode: {config.get("adcode")}')
        print(f'  区县数: {len(config["districts"])}')
        print(f'  前3区: {[d["name"] for d in config["districts"][:3]]}')
    else:
        print('  失败')