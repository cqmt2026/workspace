# -*- coding: utf-8 -*-
"""
光伏获客系统 - 模板引擎模块 v0.1
从行业插件读取templates/prompts，渲染内容脚本

职责：
1. 读取industry_config/<industry>/templates/目录下的模板
2. 读取prompts/目录下的提示词
3. 渲染输出结构化内容（钩子+正文+CTA）
4. 支持手动填写和AI生成两种模式
"""
import sys, os, json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.industry_plugin_loader import get_plugin


class TemplateEngine:
    """模板引擎：读取插件模板，渲染内容"""

    def __init__(self, industry: str = "solar"):
        self.plugin = get_plugin(industry)
        self.templates_dir = self.plugin.plugin_dir / "templates"
        self.prompts_dir = self.plugin.plugin_dir / "prompts"

    def load_template(self, direction: str) -> Optional[str]:
        """加载指定方向的模板"""
        fname = f"{direction}.md"
        fpath = self.templates_dir / fname
        if fpath.exists():
            return fpath.read_text(encoding="utf-8")
        return None

    def load_prompt(self, prompt_name: str) -> Optional[str]:
        """加载指定提示词"""
        fname = f"{prompt_name}.txt"
        fpath = self.prompts_dir / fname
        if fpath.exists():
            return fpath.read_text(encoding="utf-8")
        return None

    def render_template(self, direction: str, topic: Dict, policy: Dict = None) -> Dict:
        """根据模板渲染内容脚本"""
        template_text = self.load_template(direction)
        if not template_text:
            return self._fallback_render(direction, topic, policy)

        # 解析模板中的占位符
        title = topic.get("title", "")
        core = title[:28] if len(title) > 28 else title
        source = topic.get("source", "")
        province = policy.get("province", "") if policy else ""

        fname = f"{direction}.md"
        result = {
            "direction": direction,
            "source_title": title,
            "source": source,
            "template_used": fname,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        # 根据模板内容生成各部分
        if direction == "policy" and policy:
            result["hook"] = f"重磅！{core}，装光伏的前先看清楚这3点"
            result["body"] = (
                f"根据最新政策，{policy.get('title', '')[:40]}。"
                f"很多业主第一反应是观望，但真正懂行的人已经开始行动了。\n"
                f"具体怎么操作、能省多少钱，下面说清楚。\n"
                f"1. 政策要点：解读原文核心内容\n"
                f"2. 实际影响：对业主的具体影响\n"
                f"3. 操作指南：如何享受政策红利"
            )
            result["cta"] = (
                f"想了解你家能不能享受？评论区留言省份+屋顶面积，"
                f"我帮你免费测算。"
                + (f"\n如果你是{province}的朋友，这个政策可能直接关系到你的钱包。" if province else "")
            )
        elif direction == "benefit":
            result["hook"] = f"屋顶装光伏到底划不划算？算笔账给你看"
            result["body"] = (
                f"以常见的5kW-10kW屋顶光伏为例，结合当前组件价格和上网电价，"
                f"真实算一笔账：前期投入、每年发电量、回本周期、后续收益，"
                f"一次性给你讲清楚，别再被销售话术带偏。"
            )
            result["cta"] = (
                "你家适不适合装光伏？补贴能拿多少？"
                "点关注私信我，免费帮你测算当地政策 + 收益方案。"
            )
        elif direction == "avoid":
            result["hook"] = f"装光伏前必看！{core}避坑指南"
            result["body"] = (
                f"这条信息值得所有想装光伏的人注意：{core}。"
                f"我们梳理了近期业主反馈最多的几个问题，"
                f"帮你避开这些坑，做出不后悔的决策。"
            )
            result["cta"] = (
                "装光伏前先看这条视频，评论区帮你避坑。"
                "想找靠谱安装商也欢迎留言咨询。"
            )
        elif direction == "news":
            result["hook"] = f"今天光伏圈都在聊：{core}"
            result["body"] = (
                f"今天光伏圈最值得关注的就是：「{core}」。"
                f"这件事背后，是行业格局的深层变化，"
                f"对普通业主和从业者都有影响，具体往下看。"
            )
            result["cta"] = (
                "关注我，每天解读一个光伏行业大事。"
                "想了解更多？评论区留言你的问题。"
            )
        else:  # tech
            result["hook"] = f"{core}，一文讲透原理"
            result["body"] = (
                f"今天聊一个光伏人基本都遇到过的问题：「{core}」。"
                f"不讲复杂术语，用大白话给你讲明白原理，"
                f"看完你就清楚该怎么判断了。"
            )
            result["cta"] = (
                "想看更多光伏干货？关注不迷路。"
                "有问题评论区见。"
            )

        # 完整脚本
        result["full_script"] = (
            f"{result['hook']}\n\n{result['body']}\n\n{result['cta']}"
        )

        return result

    def _fallback_render(self, direction: str, topic: Dict, policy: Dict = None) -> Dict:
        """模板不存在时的兜底渲染"""
        return self.render_template(direction, topic, policy)

    def list_templates(self) -> List[str]:
        """列出可用模板"""
        if not self.templates_dir.exists():
            return []
        return [f.name for f in self.templates_dir.iterdir() if f.suffix == '.md']

    def list_prompts(self) -> List[str]:
        """列出可用提示词"""
        if not self.prompts_dir.exists():
            return []
        return [f.name for f in self.prompts_dir.iterdir() if f.suffix == '.txt']


if __name__ == "__main__":
    engine = TemplateEngine("solar")
    print("Available templates:", engine.list_templates())
    print("Available prompts:", engine.list_prompts())

    # 测试渲染
    topic = {"title": "江苏镇江2030年分布式光伏装机倍增计划", "source": "bjx"}
    result = engine.render_template("news", topic)
    print("\nRendered script:")
    print(result["full_script"])
