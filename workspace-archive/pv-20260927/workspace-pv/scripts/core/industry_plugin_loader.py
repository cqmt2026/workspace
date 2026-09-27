# -*- coding: utf-8 -*-
"""
光伏获客系统 - 行业插件加载器
通用引擎入口：读取 industry_config/<行业>/ 配置，驱动内容生成和采集
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

BASE = Path(__file__).parent.parent.parent

# 插件根目录
PLUGIN_DIR = BASE / "industry_config"


class IndustryPlugin:
    """行业插件基类"""

    def __init__(self, industry_name: str):
        self.industry = industry_name
        self.plugin_dir = PLUGIN_DIR / industry_name
        self._load()

    def _load(self):
        """加载插件配置"""
        if not self.plugin_dir.exists():
            raise FileNotFoundError(f"行业插件不存在: {self.plugin_dir}")

        # 加载关键词
        kw_path = self.plugin_dir / "keywords.json"
        if kw_path.exists():
            with open(kw_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.keywords = config.get("keywords", [])
            self.provinces = config.get("provinces", [])
        else:
            self.keywords = []
            self.provinces = []

        # 加载模板路径映射
        self.template_map = {
            "policy": "policy.md",
            "benefit": "benefit.md",
            "avoid": "avoid.md",
            "news": "news.md",
            "tech": "tech.md",
        }

        # 加载提示词路径映射
        self.prompt_map = {
            "hook": "hook.txt",
            "body": "body.txt",
            "cta": "cta.txt",
        }

        # 加载打分权重
        template_path = self.plugin_dir / "template" / "keywords.json"
        scoring_weights = {
            "has_phone": 30,
            "has_address": 20,
            "ask_price": 40,
            "ask_process": 20,
            "only_liked": 5,
        }
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                scoring_weights = json.load(f).get("scoring_weights", scoring_weights)
        self.scoring_weights = scoring_weights

    def get_template_path(self, direction: str) -> Optional[Path]:
        """获取指定方向的模板文件路径"""
        fname = self.template_map.get(direction)
        if fname:
            return self.plugin_dir / "templates" / fname
        return None

    def get_prompt_path(self, prompt_name: str) -> Optional[Path]:
        """获取指定提示词文件路径"""
        fname = self.prompt_map.get(prompt_name)
        if fname:
            return self.plugin_dir / "prompts" / fname
        return None

    def get_value_prop(self) -> str:
        """获取价值主张文案"""
        path = self.plugin_dir / "value_prop.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def calc_pv_score(self, title: str, summary: str = "") -> float:
        """计算行业相关度分数（通用逻辑，行业词库在插件里）"""
        text = f"{title} {summary}"
        score = 0.0
        for kw in self.keywords:
            if kw in text:
                score += 0.15
        for prov in self.provinces:
            if prov in text:
                score += 0.05
        return round(min(score, 1.0), 2)

    def classify_direction(self, title: str) -> str:
        """根据标题分类内容方向（通用逻辑）"""
        t = title.lower()
        # 先检查行业插件专属关键词
        for kw in self.keywords:
            if kw in t:
                # 根据关键词特征推断方向
                policy_kws = ["高考", "中考", "考研", "留学", "补习", "培训", "学区房", "义务教育", "双减", "素质教育", "职业教育", "自考", "成人教育", "专升本", "入学政策", "招生简章", "学费", "教育公平", "升学率", "重点学校", "新政", "政策", "通知", "管理办法", "意见", "标准", "规划", "细则"]
                benefit_kws = ["收益", "赚钱", "划算", "成本", "学费", "价格", "费用"]
                avoid_kws = ["注意", "警惕", "坑", "风险", "违规", "投诉", "暂停", "预警", "骗"]
                news_kws = ["装机", "GW", "并网", "中标", "采购", "投产", "业绩", "财报", "趋势", "发布", "公布"]
                if any(k in t for k in policy_kws):
                    return "policy"
                if any(k in t for k in benefit_kws):
                    return "benefit"
                if any(k in t for k in avoid_kws):
                    return "avoid"
                if any(k in t for k in news_kws):
                    return "news"
        # 通用分类逻辑
        if any(kw in t for kw in ["补贴", "政策", "通知", "管理办法", "意见", "标准", "规划", "细则"]):
            return "policy"
        if any(kw in t for kw in ["收益", "赚钱", "划算", "成本", "电价", "电费", "度电"]):
            return "benefit"
        if any(kw in t for kw in ["注意", "警惕", "坑", "风险", "违规", "投诉", "暂停", "预警"]):
            return "avoid"
        if any(kw in t for kw in ["装机", "GW", "并网", "中标", "采购", "投产", "业绩", "财报", "趋势"]):
            return "news"
        return "tech"


# 默认插件注册表（扩展时在此添加）
REGISTERED_PLUGINS = {
    "solar": "光伏行业",
    "edu": "教育行业",
}


def list_plugins() -> Dict[str, str]:
    """列出所有已注册的行业插件"""
    result = {}
    if PLUGIN_DIR.exists():
        for d in PLUGIN_DIR.iterdir():
            if d.is_dir() and d.name != "template" and (d / "keywords.json").exists():
                result[d.name] = d.name
    return result


def get_plugin(industry: str) -> Optional[IndustryPlugin]:
    """获取指定行业的插件实例"""
    if industry not in REGISTERED_PLUGINS:
        return None
    return IndustryPlugin(industry)


if __name__ == "__main__":
    print("=== Industry Plugins ===")
    plugins = list_plugins()
    for name, desc in plugins.items():
        plugin = get_plugin(name)
        print(f"\n[{name}] {desc}")
        print(f"  Keywords: {len(plugin.keywords)} terms")
        print(f"  Provinces: {len(plugin.provinces)} regions")
        tp = plugin.get_template_path("policy")
        print(f"  Template: {tp}")
