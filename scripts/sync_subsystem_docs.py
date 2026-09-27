"""
sync_subsystem_docs.py - 同步主系统变动到各子系统MEMORY.md
追加今日核心变动到5个子系统
"""
import os, shutil
from datetime import datetime
import io

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
SUBS = ["workspace-novel", "workspace-investment", "workspace-social", "workspace-math", "workspace-weixin"]

ADDITION = """

---

## 🔄 系统级自动化更新（2026-06-13）

### 自动化绑定铁律（强制）
**所有自动化机制必须绑定系统，永久生效，不得因迭代丢失。**
- Cron任务 + task_logger + corrections.md + Supermemory 为系统能力的一部分
- 迭代时必须同时迁移，不得单独删除或禁用

### 日志记录机制（task_logger）
所有Cron任务通过 `run_with_log.py` 包装器执行，自动记录：
- 开始/成功/失败/超时
- 日志路径：`memory/日志/task/YYYY/MM/SYSTEM/YYYYMMDD.jsonl`
- 禁止：直接跑Python脚本不记录日志

### 新增Cron任务
| 任务 | 频率 | 作用 |
|------|------|------|
| Session-Extract-Auto | 每30分钟 | session自动提取写入Supermemory |
| Self-Learning-统一学习 | 每天21:00 | 日志审计+踩坑+知识库学习+报告 |
| LOG-日志审计-每日检查 | 每天09:05 | Cron任务日志完整性检测 |
| LOG-日志审计-晚间检查 | 每天22:00 | 当日工作结束前日志完整性检测 |
| Novel-自我学习 | 每天11:00 | 小说系统自动分类知识入库 |
| Social-自我学习 | 每天11:30 | 自媒体爆款特征学习 |
| Math-自动学习 | 每天12:00 | 数学动画数据分析教训分发专家知识库 |
| System-BackupClean-每周备份清理 | 每周日20:00 | 核心文档备份+过期清理+子系统根目录清理 |

### 今日教训（2026-06-13）
1. **批量文件操作**：大量逐文件操作时先写成脚本一次性跑，不逐条调用
2. **Supermemory**：local server运行在8642端口，fact_extract.py绕过broken的litellm chain直接写SQLite
3. **Cron任务超时**：快速失败机制已配置，LLM任务120秒/脚本60秒超时
4. **子系统根目录**：所有散落文件已归位，根目录清空

"""

def sync_one(sys):
    mem_path = os.path.join(WORKSPACE, sys, "MEMORY.md")
    if not os.path.exists(mem_path):
        print("  [skip] " + sys + "/MEMORY.md not found")
        return
    with open(mem_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 检查是否已同步
    if "自动化绑定铁律" in content:
        print("  [already] " + sys + " MEMORY.md synced")
        return
    # 追加内容
    content = content.rstrip() + ADDITION
    with open(mem_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [synced] " + sys + " MEMORY.md")

def sync_corrections(sys):
    corp_path = os.path.join(WORKSPACE, sys, "memory", "corrections.md")
    main_corp = os.path.join(WORKSPACE, "corrections.md")
    if not os.path.exists(corp_path) or not os.path.exists(main_corp):
        return
    with open(corp_path, "r", encoding="utf-8") as f:
        sub_content = f.read()
    with open(main_corp, "r", encoding="utf-8") as f:
        main_content = f.read()
    # 检查novel是否有今天的记录
    today = datetime.now().strftime("%Y-%m-%d")
    marker = f"## {today}"
    if marker in sub_content or today in sub_content:
        print("  [already] " + sys + " corrections.md synced")
        return
    # 追加主系统的今日记录（如果存在）
    if today in main_content:
        # 找到主系统今日记录并追加到子系统
        lines = main_content.split("\n")
        start_idx = None
        for i, line in enumerate(lines):
            if line.startswith(marker):
                start_idx = i
                break
        if start_idx is not None:
            # 找到结束位置
            end_idx = len(lines)
            for i in range(start_idx + 1, len(lines)):
                if lines[i].startswith("## ") and lines[i] != marker:
                    end_idx = i
                    break
            today_section = "\n".join(lines[start_idx:end_idx])
            if today_section not in sub_content:
                sub_content = sub_content.rstrip() + "\n\n" + today_section
                with open(corp_path, "w", encoding="utf-8") as f:
                    f.write(sub_content)
                print("  [synced] " + sys + " corrections.md")
                return
    print("  [skip] " + sys + " corrections.md (nothing to sync)")

if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print("[Sync Subsystem Docs] 2026-06-13")
    print("=" * 40)
    for sys in SUBS:
        sync_one(sys)
        sync_corrections(sys)
    print("\n[Done]")