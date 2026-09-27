# -*- coding: utf-8 -*-
"""
光伏获客系统 - 素材整合模块 v0.1
从L2数据层提取结构化素材，为L3内容层提供输入

职责：
1. 从hot_topics筛选今日PV相关热点
2. 从policies提取相关政策素材
3. 从competitors提取竞品内容参考
4. 从region_data提取区域数据
5. 整合为结构化素材包（素材库）
"""
import sys, os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase


class MaterialLib:
    """素材库：整合L2各数据源的可用素材"""

    def __init__(self):
        self.db = PVDatabase()

    def get_today_hot_topics(self, limit: int = 10) -> List[Dict]:
        """获取今日PV相关热点话题"""
        return self.db.get_today_pv_topics(limit)

    def get_latest_policies(self, limit: int = 5) -> List[Dict]:
        """获取最新政策"""
        return self.db.get_latest_policies(limit)

    def get_competitors(self, platform: str = None) -> List[Dict]:
        """获取竞品账号列表"""
        if platform:
            cur = self.db.conn.cursor()
            cur.execute("SELECT * FROM competitors WHERE platform=? ORDER BY followers DESC", (platform,))
            return [dict(r) for r in cur.fetchall()]
        return self.db.get_all_competitors()

    def get_region_data(self, province: str = None) -> List[Dict]:
        """获取区域数据"""
        if province:
            cur = self.db.conn.cursor()
            cur.execute("SELECT * FROM region_data WHERE province=? ORDER BY avg_sunshine DESC", (province,))
            return [dict(r) for r in cur.fetchall()]
        return self.db.get_all_region_data()

    def build_material_pack(self, date: str = None) -> Dict:
        """构建今日素材包"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        pack = {
            "date": date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "hot_topics": self.get_today_hot_topics(10),
            "policies": self.get_latest_policies(5),
            "competitors": self.get_competitors(),
            "region_data": self.get_region_data(),
            "metadata": {
                "total_pv_topics": len(self.get_today_hot_topics(20)),
                "total_policies": len(self.get_latest_policies(10)),
                "total_competitors": len(self.get_competitors()),
                "total_regions": len(self.get_region_data()),
            }
        }
        return pack

    def filter_by_direction(self, direction: str, limit: int = 5) -> List[Dict]:
        """按内容方向筛选素材"""
        # 从热点中筛选
        topics = self.get_today_hot_topics(20)
        from core.industry_plugin_loader import get_plugin
        plugin = get_plugin('solar')
        filtered = []
        for t in topics:
            if plugin.classify_direction(t['title']) == direction:
                filtered.append(t)
            if len(filtered) >= limit:
                break
        return filtered

    def export_material_pack(self, pack: Dict = None, filename: str = None) -> Path:
        """导出素材包到文件"""
        if pack is None:
            pack = self.build_material_pack()

        output_dir = BASE / "data" / "output"
        output_dir.mkdir(exist_ok=True)
        if filename is None:
            filename = f"material_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        filepath = output_dir / filename

        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(pack, f, ensure_ascii=False, indent=2)

        return filepath


if __name__ == "__main__":
    ml = MaterialLib()
    pack = ml.build_material_pack()
    path = ml.export_material_pack(pack)
    print(f"Material pack exported to: {path}")
    print(f"  Hot topics: {len(pack['hot_topics'])}")
    print(f"  Policies: {len(pack['policies'])}")
    print(f"  Competitors: {len(pack['competitors'])}")
    print(f"  Regions: {len(pack['region_data'])}")
