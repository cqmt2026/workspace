# -*- coding: utf-8 -*-
"""
自媒体工作流自动化脚本 - 集成 skill 能力
功能:热点采集 → 调研 → 创作 → 去AI味 → 发布
用法:python social_workflow.py full       # 完整流程
      python social_workflow.py research <话题>  # 深度调研
      python social_workflow.py humanize <文章文件>  # 去AI味
"""

import subprocess
import sys
from pathlib import Path
import io

HUMANIZER = Path(__file__).parent / "humanize_text.py"
SOCIAL_SCRIPTS = Path(__file__).parent.parent / "workspace-social" / "scripts"


def step_research(topic: str) -> bool:
    """深度调研(集成 deep-research-pro skill)"""
    print(f"\n[Step 1] 深度调研: {topic}")
    print("  → 调用 deep-research-pro skill")
    print("  → 使用 DuckDuckGo 多源搜索")
    print("  → 输出带引用的调研报告")
    # Skill 自动触发,这里只需提示
    print(f"  ✅ 调研完成(skill会在对话中自动激活)")
    return True


def step_title_optimize(title: str) -> bool:
    """标题优化(集成 marketing-psychology skill)"""
    print(f"\n[Step 2] 标题优化: {title}")
    print("  → 调用 marketing-psychology skill")
    print("  → 行为科学角度分析钩子力")
    print("  → 输出优化建议")
    print(f"  ✅ 优化完成(skill会在对话中自动激活)")
    return True


def step_humanize(article_path: str) -> bool:
    """文章去AI味(集成 humanizer-zh skill)"""
    print(f"\n[Step 3] Humanizer: {article_path}")
    cmd = ["python", "-X", "utf8", str(HUMANIZER), article_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    return result.returncode == 0


def step_publish(platform: str = "baijiahao") -> bool:
    """发布到平台"""
    print(f"\n[Step 4] 发布: {platform}")
    print("  → 发布前需主人确认")
    return True


def run_full_workflow(topic: str, article_file: str = None):
    print(f"\n{'='*60}")
    print(f"自媒体工作流自动化")
    print(f"{'='*60}")
    
    # 存入supermemory
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))
        from memory_adapter import save_topic
        save_topic('自媒体调研: %s' % topic, source='social-workflow')
        print('  [Supermemory] 已保存话题')
    except Exception as e:
        print('  [Supermemory] 写入失败: %s' % e)
    
    # Step 1: 调研
    step_research(topic)

    # Step 2: 标题优化(如果提供了标题)
    title = input("输入标题(用于优化,可跳过直接回车):").strip()
    if title:
        step_title_optimize(title)

    # Step 3: Humanizer
    if article_file:
        step_humanize(article_file)
    else:
        print("\n[Step 3] Humanizer: 请手动提供文章路径")
        print("  用法: python social_workflow.py humanize <文章文件>")

    print(f"\n✅ 工作流完成")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import argparse
    parser = argparse.ArgumentParser(description="自媒体工作流自动化")
    parser.add_argument("action", choices=["full", "research", "humanize", "stats"],
                        help="full=完整流程, research=深度调研, humanize=去AI味, stats=统计")
    parser.add_argument("--topic", "-t", help="调研话题")
    parser.add_argument("--file", "-f", help="文章文件路径")
    args = parser.parse_args()

    if args.action == "full":
        topic = args.topic or input("输入话题:").strip()
        run_full_workflow(topic, args.file)
    elif args.action == "research":
        topic = args.topic or input("输入调研话题:").strip()
        step_research(topic)
    elif args.action == "humanize":
        if not args.file:
            print("[Error] 需要提供文件路径: --file <文章文件>")
        else:
            step_humanize(args.file)
    elif args.action == "stats":
        print("[统计] 暂无数据")
