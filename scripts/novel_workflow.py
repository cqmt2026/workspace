# -*- coding: utf-8 -*-
"""
小说创作自动化脚本 - 集成 humanizer
功能：章节写完 → 质量检查 → 去AI味 → 归档
用法：python novel_workflow.py <章节号>
"""

import sys
import subprocess
from pathlib import Path
import io

WORKSPACE_NOVEL = Path(__file__).parent.parent / "workspace-novel"
CHAPTER_GATEKEEPER = WORKSPACE_NOVEL / "创作系统/L2-工具/02-脚本工具/chapter_gatekeeper.py"
HUMANIZER = Path(__file__).parent / "humanize_text.py"

# 章节路径
def get_chapter_path(novel_project: str, chapter_num: int) -> Path:
    """获取章节文件路径"""
    project = WORKSPACE_NOVEL / novel_project / "L4-shared" / "正文"
    for p in project.glob(f"*{chapter_num}*"):
        if p.suffix in [".md", ".txt"]:
            return p
    return None


def run_quality_check(chapter_path: Path, novel_project: str) -> bool:
    """运行质量检查"""
    print(f"\n[Step 1] 质量检查: {chapter_path.name}")
    cmd = ["python", "-X", "utf8", str(CHAPTER_GATEKEEPER), str(chapter_num)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return result.returncode == 0


def run_humanizer(chapter_path: Path) -> bool:
    """运行 humanizer 去AI味"""
    print(f"\n[Step 2] Humanizer: {chapter_path.name}")
    output = chapter_path.parent / f"{chapter_path.stem}_humanized{chapter_path.suffix}"
    cmd = ["python", "-X", "utf8", str(HUMANIZER), str(chapter_path), str(output)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        # 替换原文件
        import shutil
        shutil.move(str(output), str(chapter_path))
        print(f"  ✅ Humanizer 完成，已更新: {chapter_path.name}")
        return True
    return False


def archive_chapter(chapter_path: Path, novel_project: str):
    """归档章节 + 存入记忆"""
    print(f"\n[Step 3] 归档: {chapter_path.name}")
    import shutil, datetime
    
    # 存入supermemory
    try:
        chapter_text = chapter_path.read_text(encoding="utf-8")
        summary = chapter_text.strip()[:200].replace('\n', ' ')
        sys.path.insert(0, str(Path(__file__).parent))
        from memory_adapter import save_plot
        r = save_plot('%s - %s: %s' % (novel_project, chapter_path.stem, summary), source='novel-workflow')
        if r.get('success'):
            print('  Supermemory: 已保存章节摘要')
    except Exception as e:
        print('  Supermemory写入失败: %s' % e)
    # 角色一致性检查
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from memory_ref import recall_novel
        r = recall_novel()
        if r['count'] > 0:
            print('  [角色记忆参考]')
            for m in r['results'][:3]:
                print(f"    [{m['_label']}] ({m['score']:.2f}) {m['text'][:60]}")
    except Exception as e:
        print('  角色记忆加载失败: %s' % e)
    
    
    archive = WORKSPACE_NOVEL / novel_project / "L5-archive"
    archive.mkdir(exist_ok=True)
    dest = archive / f"{datetime.date.today().isoformat()}_{chapter_path.name}"
    shutil.copy2(str(chapter_path), str(dest))
    print(f"  ✅ 已归档: {dest.name}")


def run_workflow(novel_project: str, chapter_num: int):
    print(f"\n{'='*60}")
    print(f"小说创作自动化流程 - 第{chapter_num}章")
    print(f"{'='*60}")

    chapter_path = get_chapter_path(novel_project, chapter_num)
    if not chapter_path:
        print(f"[Error] 未找到第{chapter_num}章文件")
        return

    # Step 1: 质量检查
    if not run_quality_check(chapter_path, novel_project):
        print(f"\n❌ 质量检查未通过，停止 workflow")
        return

    # Step 2: Humanizer
    if not run_humanizer(chapter_path):
        print(f"\n⚠️ Humanizer 执行失败，继续归档")
        return

    # Step 3: 归档
    archive_chapter(chapter_path, novel_project)

    print(f"\n✅ Workflow 完成！")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import argparse
    parser = argparse.ArgumentParser(description="小说创作自动化流程")
    parser.add_argument("chapter_num", type=int, help="章节号")
    parser.add_argument("--project", default="项目一：鉴城师", help="项目名称")
    args = parser.parse_args()

    run_workflow(args.project, args.chapter_num)
