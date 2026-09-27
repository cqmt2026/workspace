# -*- coding: utf-8 -*-
"""
中国贸易朋友圈加速扩容 - 地图数据与绘制
"""
import os, sys, json
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts', 'modules'))

# ============================================================
# 中国主要贸易伙伴数据（基于公开数据整理）
# 160+ 个主要贸易伙伴，选取关键国家展示
# ============================================================

TRADE_PARTNERS = [
    # RCEP成员国（核心）
    {"name": "日本", "lon": 138.0, "lat": 36.0, "trade_billion": 3500, "group": "RCEP"},
    {"name": "韩国", "lon": 128.0, "lat": 37.0, "trade_billion": 3200, "group": "RCEP"},
    {"name": "澳大利亚", "lon": 135.0, "lat": -25.0, "trade_billion": 2500, "group": "RCEP"},
    {"name": "新西兰", "lon": 174.0, "lat": -41.0, "trade_billion": 400, "group": "RCEP"},
    {"name": "越南", "lon": 106.0, "lat": 16.0, "trade_billion": 2300, "group": "RCEP"},
    {"name": "马来西亚", "lon": 105.0, "lat": 4.0, "trade_billion": 1900, "group": "RCEP"},
    {"name": "新加坡", "lon": 104.0, "lat": 1.3, "trade_billion": 1300, "group": "RCEP"},
    {"name": "泰国", "lon": 101.0, "lat": 14.0, "trade_billion": 1400, "group": "RCEP"},
    {"name": "印尼", "lon": 118.0, "lat": -5.0, "trade_billion": 1200, "group": "RCEP"},
    {"name": "菲律宾", "lon": 122.0, "lat": 13.0, "trade_billion": 700, "group": "RCEP"},
    {"name": "柬埔寨", "lon": 105.0, "lat": 12.0, "trade_billion": 400, "group": "RCEP"},
    {"name": "老挝", "lon": 105.0, "lat": 18.0, "trade_billion": 200, "group": "RCEP"},
    {"name": "缅甸", "lon": 96.0, "lat": 20.0, "trade_billion": 250, "group": "RCEP"},
    {"name": "文莱", "lon": 115.0, "lat": 4.5, "trade_billion": 50, "group": "RCEP"},

    # 东盟（非RCEP但有自贸区）
    {"name": "印度", "lon": 78.0, "lat": 21.0, "trade_billion": 1400, "group": "东盟对话伙伴"},

    # 重要双边自贸协定伙伴
    {"name": "巴基斯坦", "lon": 69.0, "lat": 30.0, "trade_billion": 300, "group": "自贸协定"},
    {"name": "智利", "lon": -71.0, "lat": -35.0, "trade_billion": 350, "group": "自贸协定"},
    {"name": "秘鲁", "lon": -75.0, "lat": -12.0, "trade_billion": 280, "group": "自贸协定"},
    {"name": "哥斯达黎加", "lon": -84.0, "lat": 10.0, "trade_billion": 80, "group": "自贸协定"},
    {"name": "冰岛", "lon": -19.0, "lat": 65.0, "trade_billion": 30, "group": "自贸协定"},
    {"name": "瑞士", "lon": 8.0, "lat": 47.0, "trade_billion": 500, "group": "自贸协定"},
    {"name": "挪威", "lon": 10.0, "lat": 62.0, "trade_billion": 200, "group": "自贸协定"},
    {"name": "塞尔维亚", "lon": 20.0, "lat": 44.0, "trade_billion": 60, "group": "自贸协定"},
    {"name": "格鲁吉亚", "lon": 43.0, "lat": 42.0, "trade_billion": 40, "group": "自贸协定"},
    {"name": "马尔代夫", "lon": 73.0, "lat": 3.0, "trade_billion": 15, "group": "自贸协定"},

    # 重要贸易伙伴（非FTA但贸易量大）
    {"name": "美国", "lon": -98.0, "lat": 39.0, "trade_billion": 5000, "group": "重要伙伴"},
    {"name": "德国", "lon": 10.0, "lat": 51.0, "trade_billion": 2800, "group": "欧盟"},
    {"name": "荷兰", "lon": 5.0, "lat": 52.0, "trade_billion": 1000, "group": "欧盟"},
    {"name": "法国", "lon": 2.0, "lat": 47.0, "trade_billion": 900, "group": "欧盟"},
    {"name": "英国", "lon": -2.0, "lat": 54.0, "trade_billion": 900, "group": "欧盟"},
    {"name": "意大利", "lon": 12.0, "lat": 42.0, "trade_billion": 600, "group": "欧盟"},
    {"name": "俄罗斯", "lon": 50.0, "lat": 60.0, "trade_billion": 2000, "group": "重要伙伴"},
    {"name": "沙特阿拉伯", "lon": 45.0, "lat": 24.0, "trade_billion": 800, "group": "重要伙伴"},
    {"name": "阿联酋", "lon": 54.0, "lat": 24.0, "trade_billion": 1000, "group": "重要伙伴"},
    {"name": "伊朗", "lon": 53.0, "lat": 32.0, "trade_billion": 300, "group": "重要伙伴"},
    {"name": "土耳其", "lon": 35.0, "lat": 39.0, "trade_billion": 500, "group": "重要伙伴"},
    {"name": "以色列", "lon": 34.0, "lat": 31.0, "trade_billion": 250, "group": "重要伙伴"},
    {"name": "哈萨克斯坦", "lon": 68.0, "lat": 48.0, "trade_billion": 300, "group": "上合组织"},
    {"name": "乌兹别克斯坦", "lon": 64.0, "lat": 41.0, "trade_billion": 150, "group": "上合组织"},
    {"name": "巴西", "lon": -52.0, "lat": -14.0, "trade_billion": 1500, "group": "金砖国家"},
    {"name": "南非", "lon": 25.0, "lat": -29.0, "trade_billion": 400, "group": "金砖国家"},
    {"name": "埃及", "lon": 30.0, "lat": 27.0, "trade_billion": 300, "group": "重要伙伴"},
    {"name": "尼日利亚", "lon": 8.0, "lat": 9.0, "trade_billion": 200, "group": "重要伙伴"},
    {"name": "肯尼亚", "lon": 38.0, "lat": -1.0, "trade_billion": 150, "group": "重要伙伴"},
    {"name": "印尼", "lon": 118.0, "lat": -5.0, "trade_billion": 1200, "group": "重要伙伴"},
    {"name": "孟加拉国", "lon": 90.0, "lat": 24.0, "trade_billion": 200, "group": "重要伙伴"},
    {"name": "蒙古", "lon": 104.0, "lat": 46.0, "trade_billion": 100, "group": "重要伙伴"},
    {"name": "朝鲜", "lon": 127.0, "lat": 40.0, "trade_billion": 20, "group": "重要伙伴"},
    {"name": "蒙古", "lon": 104.0, "lat": 46.0, "trade_billion": 100, "group": "重要伙伴"},
]

# 去重（按名称）
seen = set()
unique_partners = []
for p in TRADE_PARTNERS:
    if p["name"] not in seen:
        seen.add(p["name"])
        unique_partners.append(p)

# 中国中心坐标
CHINA_CENTER = {"lon": 104.0, "lat": 35.0}

print(f"共 {len(unique_partners)} 个贸易伙伴")

# 保存数据
output_path = os.path.join(BASE_DIR, 'data', 'materials', 'trade_partners.json')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump({
        "partners": unique_partners,
        "china_center": CHINA_CENTER,
        "total_partners": len(unique_partners),
        "rcep_count": sum(1 for p in unique_partners if p["group"] == "RCEP"),
        "fta_count": sum(1 for p in unique_partners if p["group"] == "自贸协定"),
        "key_partner_count": sum(1 for p in unique_partners if p["group"] == "重要伙伴"),
        "eu_count": sum(1 for p in unique_partners if p["group"] == "欧盟"),
        "brics_count": sum(1 for p in unique_partners if p["group"] == "金砖国家"),
    }, f, ensure_ascii=False, indent=2)

print(f"数据已保存: {output_path}")
