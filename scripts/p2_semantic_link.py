#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2 - 语义关联：关键词跨分类关联
1. 从所有笔记中提取关键词（高频名词/概念）
2. 统计关键词在各分类中的出现频率
3. 如果一个关键词出现在 >=2 个不同分类中，建立跨分类关联
4. 生成关联图 Markdown 文件
"""
import sys
import io

import os
import re
import json
import datetime
from collections import defaultdict, Counter
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
OUTPUT_DIR = r"C:\Users\Administrator\.openclaw\workspace\out_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 金融/创作领域关键词列表（手动精选，避免通用词噪音）
DOMAIN_KEYWORDS = [
    # 投资相关
    "RPS", "MACD", "KDJ", "RSI", "MA5", "MA10", "MA20", "MA60", "MA120",
    "涨停", "跌停", "放量", "缩量", "换手率", "成交量", "成交额",
    "止损", "止盈", "仓位", "加仓", "减仓", "空仓", "满仓",
    "大盘", "板块", "概念", "题材", "龙头", "补涨", "轮动",
    "均线", "趋势", "突破", "回调", "反弹", "反转",
    "市盈率", "市净率", "流通市值", "总市值",
    "北向资金", "主力", "游资", "机构", "散户",
    "回测", "策略", "因子", "信号", "模型", "训练",
    "选股", "扫描", "监控", "预警",
    # 创作相关
    "爆款", "标题", "封面", "文案", "脚本",
    "开头", "结尾", "钩子", "悬念", "反转",
    "节奏", "结构", "框架", "模板", "公式",
    "账号", "粉丝", "播放", "点赞", "收藏",
    "算法", "推荐", "流量", "转化",
    # 数学动画
    "Manim", "场景", "镜头", "动画", "渲染",
    # 通用
    "数据", "分析", "报告", "系统", "优化",
]

STOP_CLASSIFICATIONS = ["00-日记", "03-项目"]

def extract_classification(fp, rel):
    """从文件路径推断分类"""
    for cls in STOP_CLASSIFICATIONS:
        if rel.startswith(cls):
            return None
    parts = rel.split(os.sep)
    if len(parts) >= 2:
        return parts[0] + "/" + parts[1]
    return None


def extract_keywords(content):
    """从内容中提取领域关键词"""
    found = []
    for kw in DOMAIN_KEYWORDS:
        if kw in content:
            found.append(kw)
    return found


def build_cross_classification_links():
    """建立跨分类关键词关联"""
    # kw -> set of classifications
    kw_class = defaultdict(set)
    # classification -> list of files
    class_files = defaultdict(list)

    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, OBSIDIAN_VAULT)
            cls = extract_classification(fp, rel)
            if cls is None:
                continue
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except:
                continue

            keywords = extract_keywords(content)
            class_files[cls].append((rel, keywords))
            for kw in keywords:
                kw_class[kw].add(cls)

    # 找出跨分类关键词
    cross_links = {}
    for kw, classes in kw_class.items():
        if len(classes) >= 2:
            cross_links[kw] = sorted(classes)

    return cross_links, class_files


def generate_association_map(cross_links, class_files):
    """生成关联图 Markdown"""
    lines = []
    lines.append("# P2 知识关联图 - 跨分类关键词关联")
    lines.append(f"> 由 可悦🌸 自动生成")
    lines.append(f"> 生成时间: {datetime.datetime.now().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not cross_links:
        lines.append("暂未发现跨分类关键词关联。")
        lines.append("")
        lines.append("_说明：DOMAIN_KEYWORDS 列表可能需要扩展。_")
        content = "\n".join(lines)
        outpath = os.path.join(OUTPUT_DIR, "p2_association_map.md")
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(content)
        return outpath

    # 按连接数排序
    sorted_links = sorted(cross_links.items(), key=lambda x: len(x[1]), reverse=True)

    lines.append(f"## 概览")
    lines.append(f"- 跨分类关键词: {len(cross_links)} 个")
    lines.append(f"- 涉及分类: {len(set(c for v in cross_links.values() for c in v))} 个")
    lines.append("")

    lines.append("## 关键词关联表")
    lines.append("")
    lines.append("| 关键词 | 跨分类数 | 涉及分类 |")
    lines.append("|--------|---------|---------|")
    for kw, classes in sorted_links:
        lines.append(f"| {kw} | {len(classes)} | {' / '.join(classes)} |")
    lines.append("")

    # 按分类展示
    lines.append("## 按分类查看")
    lines.append("")
    for cls in sorted(class_files.keys()):
        # 该分类下有哪些跨分类关键词
        cls_keywords = [(kw, classes) for kw, classes in sorted_links if cls in classes]
        if not cls_keywords:
            continue
        lines.append(f"### {cls}")
        lines.append(f"共 {len(class_files[cls])} 篇笔记")
        lines.append("")
        for kw, classes in cls_keywords:
            others = [c for c in classes if c != cls]
            lines.append(f"- **{kw}** → 关联到: {' / '.join(others)}")
        lines.append("")

    lines.append("---")
    lines.append("_由 P2 语义关联系统自动维护_")

    content = "\n".join(lines)
    outpath = os.path.join(OUTPUT_DIR, "p2_association_map.md")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)

    # 同时更新到 Obsidian 知识库
    obsidian_path = os.path.join(OBSIDIAN_VAULT, "03-投资", "其他", "P2_知识关联图.md")
    os.makedirs(os.path.dirname(obsidian_path), exist_ok=True)
    with open(obsidian_path, "w", encoding="utf-8") as f:
        f.write(content)

    return outpath


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    cross_links, class_files = build_cross_classification_links()
    report_path = generate_association_map(cross_links, class_files)

    print(f"P2: 扫描完成")
    print(f"P2: 跨分类关键词: {len(cross_links)} 个")
    print(f"P2: 关联图已生成: {report_path}")
    print(f"P2: 已同步到 Obsidian: 03-投资/其他/P2_知识关联图.md")

    # 输出 top 跨分类关键词
    sorted_links = sorted(cross_links.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"\nP2: Top 10 跨分类关键词:")
    for kw, classes in sorted_links[:10]:
        print(f"  {kw}: {' / '.join(classes)}")