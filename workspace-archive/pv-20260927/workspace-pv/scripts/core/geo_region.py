# -*- coding: utf-8 -*-
"""
光伏获客系统 - GEO区域数据注入模块 v0.1
轻量级GEO：基于31省份的光照/电价/补贴数据，生成区域化内容
"""
import sys, os, json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase


# 九箭新能源在重庆，服务半径辐射川渝贵
# 评分逻辑：服务半径（base_score） + 光照×电价（eco_score）
# base_score: 重庆100, 四川90, 贵州80, 周边省份递减
HIGH_POTENTIAL_PROVINCES = [
    {"province": "重庆", "sunshine": 2.5, "elec": 0.55, "subsidy": 0.0, "base_score": 100, "score": 100},
    {"province": "四川", "sunshine": 2.8, "elec": 0.54, "subsidy": 0.02, "base_score": 90, "score": 90},
    {"province": "贵州", "sunshine": 3.0, "elec": 0.50, "subsidy": 0.03, "base_score": 80, "score": 80},
    {"province": "云南", "sunshine": 4.0, "elec": 0.42, "subsidy": 0.05, "base_score": 70, "score": 70},
    {"province": "湖北", "sunshine": 3.2, "elec": 0.58, "subsidy": 0.0, "base_score": 60, "score": 65},
    {"province": "湖南", "sunshine": 3.0, "elec": 0.60, "subsidy": 0.0, "base_score": 55, "score": 62},
    {"province": "陕西", "sunshine": 3.8, "elec": 0.50, "subsidy": 0.0, "base_score": 50, "score": 58},
    {"province": "广东", "sunshine": 3.5, "elec": 0.65, "subsidy": 0.0, "base_score": 40, "score": 55},
    {"province": "广西", "sunshine": 3.5, "elec": 0.50, "subsidy": 0.0, "base_score": 45, "score": 52},
    {"province": "浙江", "sunshine": 3.2, "elec": 0.62, "subsidy": 0.0, "base_score": 30, "score": 48},
    {"province": "江苏", "sunshine": 3.4, "elec": 0.58, "subsidy": 0.0, "base_score": 30, "score": 46},
    {"province": "山东", "sunshine": 4.0, "elec": 0.55, "subsidy": 0.0, "base_score": 30, "score": 44},
    {"province": "安徽", "sunshine": 3.6, "elec": 0.58, "subsidy": 0.05, "base_score": 35, "score": 42},
    {"province": "福建", "sunshine": 3.3, "elec": 0.60, "subsidy": 0.0, "base_score": 30, "score": 40},
    {"province": "河南", "sunshine": 3.8, "elec": 0.56, "subsidy": 0.0, "base_score": 30, "score": 38},
    {"province": "河北", "sunshine": 4.2, "elec": 0.52, "subsidy": 0.0, "base_score": 25, "score": 36},
    {"province": "江西", "sunshine": 3.3, "elec": 0.56, "subsidy": 0.0, "base_score": 30, "score": 34},
    {"province": "山西", "sunshine": 4.0, "elec": 0.48, "subsidy": 0.0, "base_score": 25, "score": 32},
    {"province": "辽宁", "sunshine": 3.6, "elec": 0.50, "subsidy": 0.0, "base_score": 25, "score": 30},
    {"province": "内蒙古", "sunshine": 4.5, "elec": 0.45, "subsidy": 0.02, "base_score": 20, "score": 28},
    {"province": "甘肃", "sunshine": 4.5, "elec": 0.40, "subsidy": 0.0, "base_score": 20, "score": 26},
    {"province": "宁夏", "sunshine": 4.5, "elec": 0.42, "subsidy": 0.0, "base_score": 20, "score": 24},
    {"province": "新疆", "sunshine": 4.8, "elec": 0.35, "subsidy": 0.01, "base_score": 15, "score": 22},
    {"province": "青海", "sunshine": 5.0, "elec": 0.38, "subsidy": 0.0, "base_score": 15, "score": 20},
    {"province": "西藏", "sunshine": 5.5, "elec": 0.30, "subsidy": 0.05, "base_score": 15, "score": 18},
    {"province": "天津", "sunshine": 3.5, "elec": 0.55, "subsidy": 0.0, "base_score": 20, "score": 16},
    {"province": "海南", "sunshine": 4.5, "elec": 0.60, "subsidy": 0.02, "base_score": 15, "score": 14},
    {"province": "上海", "sunshine": 3.0, "elec": 0.62, "subsidy": 0.0, "base_score": 15, "score": 12},
    {"province": "北京", "sunshine": 3.5, "elec": 0.55, "subsidy": 0.0, "base_score": 15, "score": 10},
    {"province": "黑龙江", "sunshine": 3.2, "elec": 0.48, "subsidy": 0.0, "base_score": 15, "score": 8},
    {"province": "吉林", "sunshine": 3.4, "elec": 0.48, "subsidy": 0.0, "base_score": 15, "score": 6},
]


class GeoRegionData:
    """GEO区域数据引擎"""
    
    def __init__(self):
        self.db = PVDatabase()
        self._ensure_data()
    
    def _ensure_data(self):
        """确保region_data表有基础数据"""
        cur = self.db.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM region_data")
        if cur.fetchone()[0] == 0:
            self._seed_region_data()
    
    def _seed_region_data(self):
        """注入省份基础数据"""
        from core.database import init_db
        init_db()
        cur = self.db.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        for p in HIGH_POTENTIAL_PROVINCES:
            cur.execute("""
                INSERT OR IGNORE INTO region_data
                (province, city, avg_sunshine, residential_electricity, subsidy_local, data_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p["province"], None, p["sunshine"], p["elec"], p["subsidy"], today))
        self.db.conn.commit()
        print(f"[GEO] Seeded {len(HIGH_POTENTIAL_PROVINCES)} provinces")
    
    def get_high_potential_regions(self, top_n: int = 10) -> List[Dict]:
        """获取光伏投资潜力最高的省份"""
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT province, avg_sunshine, residential_electricity, subsidy_local
            FROM region_data
            WHERE avg_sunshine > 0
            ORDER BY avg_sunshine * residential_electricity DESC
            LIMIT ?
        """, (top_n,))
        return [dict(r) for r in cur.fetchall()]
    
    def get_province_score(self, province: str) -> int:
        """获取省份评分"""
        for p in HIGH_POTENTIAL_PROVINCES:
            if p["province"] == province:
                return p["score"]
        return 0
    
    def localize_content(self, content: Dict, province: str) -> Dict:
        """将通用内容本地化到指定省份"""
        localized = dict(content)
        for p in HIGH_POTENTIAL_PROVINCES:
            if p["province"] == province:
                # 替换电价数据
                if "{price}" in localized.get("body", ""):
                    localized["body"] = localized["body"].replace("{price}", str(p["elec"]))
                if "{total}" in localized.get("body", ""):
                    total_invest = round(5 * p["elec"] * 1000, 0)
                    localized["body"] = localized["body"].replace("{total}", str(int(total_invest)))
                if "{years}" in localized.get("body", ""):
                    years = round(5 * p["elec"] * 1000 / (p["sunshine"] * 365 * 5 * 0.4), 1)
                    localized["body"] = localized["body"].replace("{years}", str(years))
                # 添加省份标签
                localized["province"] = province
                localized["geo_score"] = p["score"]
                break
        return localized
    
    def get_geo_tag(self, province: str) -> str:
        """生成GEO标签"""
        score = self.get_province_score(province)
        if score >= 80:
            return "[核心区]"
        elif score >= 60:
            return "[辐射区]"
        elif score >= 40:
            return "[扩展区]"
        return "[机会区]"
    
    def get_daily_geo_report(self) -> str:
        """生成GEO日报"""
        high = self.get_high_potential_regions(5)
        lines = []
        lines.append("📊 光伏GEO日报 — 高潜力区域排名")
        lines.append("=" * 40)
        for i, r in enumerate(high, 1):
            tag = self.get_geo_tag(r["province"])
            lines.append(f"  {i}. {r['province']}  | 日照{r['avg_sunshine']}h  | 电价¥{r['residential_electricity']}/度  {tag}")
        lines.append("\n建议：优先投放Top5省份的区域化内容")
        return "\n".join(lines)


if __name__ == "__main__":
    geo = GeoRegionData()
    print(geo.get_daily_geo_report())
    geo.db.close()