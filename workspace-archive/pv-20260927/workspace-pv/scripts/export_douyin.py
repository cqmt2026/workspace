# -*- coding: utf-8 -*-
"""导出A级内容为抖音发布格式"""
import json, os, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
content_dir = BASE / "data" / "output" / "llm_generated"
output_dir = BASE / "data" / "output" / "douyin_ready"
output_dir.mkdir(parents=True, exist_ok=True)

# 加载生成的内容
json_file = content_dir / "llm_generated_20260820.json"
with open(json_file, "r", encoding="utf-8") as f:
    contents = json.load(f)

# 筛选A级（正文>=100字且无占位符）
a_level = []
for c in contents:
    body_len = len(c.get("body",""))
    has_placeholder = any(x in c.get("hook","") + c.get("body","") + c.get("cta","") for x in ["测试", "占位符", "{title"])
    has_number_or_q = bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))
    if body_len >= 100 and not has_placeholder and has_number_or_q:
        a_level.append(c)

print(f"共 {len(contents)} 条，A级 {len(a_level)} 条可发布")

# 抖音格式：标题(30字内)+正文+话题标签
topics_map = {
    "policy": ["#光伏政策", "#屋顶光伏", "#分布式光伏", "#光伏补贴"],
    "news": ["#光伏新闻", "#行业趋势", "#光伏装机", "#新能源"],
    "tech": ["#光伏技术", "#太阳能发电", "#光伏科普", "#组件选择"],
    "benefit": ["#光伏收益", "#光伏发电", "#投资回报", "#省钱攻略"],
    "avoid": ["#光伏避坑", "#光伏安装", "#业主必看", "#光伏陷阱"],
}

for i, c in enumerate(a_level):
    direction = c.get("direction", "news")
    tags = topics_map.get(direction, topics_map["news"])

    # 抖音标题：从钩子截取30字内
    hook = c["hook"]
    if len(hook) > 30:
        # 找最近的句号/逗号截断
        for sep in ["。", ".", "，", ",", "！", "!", "？", "?"]:
            idx = hook.find(sep)
            if 20 <= idx <= 30:
                hook = hook[:idx]
                break
        else:
            hook = hook[:28] + "..."

    # 抖音正文：钩子+正文+CTA，控制总长度
    body = c["body"]
    cta = c["cta"]
    full_text = f"{hook}\n\n{body}\n\n{cta}"

    # 话题标签追加到正文末尾
    tag_text = " " + " ".join(tags)
    full_text += tag_text

    # 追踪ID
    tid = c.get("tracking_id", f"DY_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # 保存为纯文本（方便复制）
    md_file = output_dir / f"{tid}.txt"
    md_file.write_text(full_text, encoding="utf-8")

    # 同时保存结构化JSON
    print(f"[{i+1}] {tid}")
    print(f"    标题: {hook[:30]}...")
    print(f"    正文: {len(full_text)} 字")
    print(f"    标签: {', '.join(tags)}")
    print(f"    保存: {md_file.name}")
    print()

# 保存汇总清单
summary_file = output_dir / "发布清单.txt"
summary_lines = []
summary_lines.append("=" * 50)
summary_lines.append("光伏获客 - 抖音发布清单")
summary_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
summary_lines.append(f"共 {len(a_level)} 条内容")
summary_lines.append("=" * 50)
summary_lines.append("")

for i, c in enumerate(a_level):
    tid = c.get("tracking_id", f"DY_{i+1}")
    direction = c.get("direction", "news")
    summary_lines.append(f"【{i+1}】{tid}")
    summary_lines.append(f"  方向: {direction}")
    summary_lines.append(f"  标题: {c['hook'][:40]}...")
    summary_lines.append(f"  正文: {len(c['body'])}字")
    summary_lines.append(f"  CTA: {c['cta'][:40]}...")
    summary_lines.append("")

summary_file.write_text("\n".join(summary_lines), encoding="utf-8")
print(f"清单已保存: {summary_file}")
print(f"\n文件目录: {output_dir}/")
print("每条内容可直接复制粘贴到抖音发布器")
