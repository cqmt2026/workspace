#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可悦 -> Obsidian 知识沉淀系统
每天21:30执行，收集当天Cron产出，分类写入Obsidian库
"""

import os
import json
import datetime
import re
import glob
import sys
import io

# ===== 配置 =====
OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOG_DIR = os.path.join(WORKSPACE, "logs")

CATEGORY_MAP = {
    # 小说子系统
    "Novel": ("01-小说", "小说"),
    "小说": ("01-小说", "小说"),
    # 自媒体子系统
    "Social": ("01-小说", "自媒体"),
    "自媒体": ("01-小说", "自媒体"),
    "热点": ("01-小说", "自媒体/热点素材"),
    "Hot": ("01-小说", "自媒体/热点素材"),
    "Web-Hot": ("01-小说", "自媒体/热点素材"),
    # 投资子系统
    "投资": ("03-知识", "投资"),
    "INV": ("03-知识", "投资"),
    "ML": ("03-知识", "投资"),
    "Hermes": ("03-知识", "投资"),
    # 数学动画子系统
    "Math": ("01-小说", "数学动画"),
    "数学": ("01-小说", "数学动画"),
    # 微信小程序子系统
    "WX": ("03-项目", "微信小程序"),
    "小程序": ("03-项目", "微信小程序"),
    # 系统维护
    "System": ("03-项目", "贾维斯系统"),
    "Self": ("03-项目", "贾维斯系统"),
    "LOG": ("03-项目", "贾维斯系统"),
    "P0": ("03-项目", "贾维斯系统"),
    "P1": ("03-项目", "贾维斯系统"),
    "P2": ("03-项目", "贾维斯系统"),
    "P3": ("03-项目", "贾维斯系统"),
    # 技术趋势
    "GitHub": ("03-投资", "技术"),
}

# 无匹配时的强制分配规则（防止默认进"其他"）
FALLBACK_CATEGORY = {
    "一人企业": ("03-项目", "贾维斯系统"),
    "三池模型": ("03-项目", "贾维斯系统"),
    "AI错题本": ("03-项目", "微信小程序"),
    "深度解剖": ("03-项目", "微信小程序"),
    "里昂说AI": ("03-项目", "贾维斯系统"),
    "MSTNN": ("03-知识", "投资"),
    "香农索普": ("03-知识", "投资"),
    "交易数学": ("03-知识", "投资"),
}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def classify_task(name):
    # 优先精确匹配FALLBACK_CATEGORY
    for keyword, (area, topic) in FALLBACK_CATEGORY.items():
        if keyword.lower() in name.lower():
            return area, topic
    # 再匹配CATEGORY_MAP
    for keyword, (area, topic) in CATEGORY_MAP.items():
        if keyword.lower() in name.lower():
            return area, topic
    # 都不匹配时，标记为"待分类"而非"其他"，便于人工处理
    return ("03-投资", "待分类")


def collect_today_tasks():
    today = datetime.date.today().isoformat()
    tasks = []

    if os.path.exists(LOG_DIR):
        for f in os.listdir(LOG_DIR):
            if today in f and f.endswith(".log"):
                log_path = os.path.join(LOG_DIR, f)
                task_name = f.replace(today, "").replace("_", "").replace(".log", "").strip("-_")
                tasks.append({
                    "name": task_name if task_name else "unknown",
                    "log_file": log_path,
                    "size": os.path.getsize(log_path),
                })

    hot_file = os.path.join(WORKSPACE, "out_data", "hot_topic_report.md")
    if os.path.exists(hot_file):
        tasks.append({
            "name": "Hot-Topic-Finder",
            "output_file": hot_file,
            "size": os.path.getsize(hot_file),
        })

    return tasks


def read_output_content(task):
    content = []
    log_file = task.get("log_file")
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    content.append(line.rstrip())
        except:
            pass

    out_file = task.get("output_file")
    if out_file and os.path.exists(out_file):
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                text = f.read()
                if len(text) > 2000:
                    text = text[:2000] + "\n...(截断)"
                content.append(text)
        except:
            pass

    return "\n".join(content[:80])


def write_knowledge_note(area, topic, title, content):
    topic_dir = ensure_dir(os.path.join(OBSIDIAN_VAULT, area, topic))
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:50]
    filename = datetime.date.today().isoformat() + "_" + safe_title + ".md"
    filepath = os.path.join(topic_dir, filename)

    tags = []
    if topic:
        tags.append("tag/" + topic)
    tags.append("tag/" + area.replace("-", ""))
    tag_str = ", ".join(tags)
    now_str = datetime.datetime.now().isoformat()

    md = "---\n"
    md += "created: " + now_str + "\n"
    md += "source: auto_collect\n"
    md += "tags: [" + tag_str + "]\n"
    md += "area: " + area + "\n"
    md += "topic: " + topic + "\n"
    md += "---\n\n"
    md += "# " + safe_title + "\n\n"
    md += "> 由 可悦🌸 自动采集沉淀\n\n"
    md += content + "\n\n"
    md += "---\n"
    md += "_由 可悦🌸 自动维护_\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    return filepath


def update_dataview_index():
    idx_dir = ensure_dir(os.path.join(OBSIDIAN_VAULT, "03-项目", "贾维斯系统"))
    idx_path = os.path.join(idx_dir, "Dataview索引.md")
    today = datetime.date.today().isoformat()

    md = """# 📊 Dataview 索引

> 由 可悦🌸 自动生成，提供 Obsidian 知识库的 Dataview 查询入口。
> 最后更新: """ + today + """

---

## 📝 最近知识笔记
```dataview
TABLE file.mtime AS 修改时间
FROM "03-投资"
SORT file.mtime DESC
LIMIT 20
```

---

## 📈 投资研究
```dataview
TABLE file.mtime AS 修改时间
FROM "03-知识"
SORT file.mtime DESC
LIMIT 20
```

---

## 📂 项目进展
```dataview
TABLE file.mtime AS 修改时间
FROM "03-项目"
SORT file.mtime DESC
LIMIT 20
```

---

## 📅 最近日记
```dataview
TABLE file.mtime AS 修改时间
FROM "00-日记"
SORT file.mtime DESC
LIMIT 10
```

---

## 🔍 按标签查询
- 科技趋势：`#tag/科技`
- 互联网观察：`#tag/互联网`
- 行业洞察：`#tag/行业`
- 投资研究：`#tag/投资`
- 系统维护：`#tag/系统`

---
_由 可悦🌸 自动维护_
"""

    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(md)

    return idx_path


def main():
    print("可悦知识沉淀 - " + datetime.datetime.now().isoformat())
    print("Obsidian库: " + OBSIDIAN_VAULT)
    print()

    print("收集当天Cron产出...")
    tasks = collect_today_tasks()
    print("  找到 " + str(len(tasks)) + " 个任务产出")

    written = []
    for task in tasks:
        area, topic = classify_task(task["name"])
        content = read_output_content(task)
        if not content.strip():
            continue
        filepath = write_knowledge_note(area, topic, task["name"], content)
        written.append(filepath)
        print("  + " + os.path.basename(filepath) + " -> " + area + "/" + topic)

    print()
    print("从Supermemory召回今日记忆...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))
        from memory_adapter import search
        # 召回各领域今日记忆
        sm_count = 0
        for domain_name in ['novel', 'investment', 'social', 'system']:
            r = search('', top_k=10, domain=domain_name)
            if r['count'] > 0:
                note_content = '# Supermemory今日记忆\n\n来源: ' + domain_name + '\n\n'
                for m in r['results'][:5]:
                    note_content += '- [' + m.get('category','') + '] ' + m['text'][:100] + '\n'
                filepath = write_knowledge_note('系统', '记忆', 'Supermemory-' + domain_name, note_content)
                if filepath:
                    written.append(filepath)
                    sm_count += 1
        print('  + Supermemory: ' + str(sm_count) + ' 篇记忆笔记')
    except Exception as e:
        print('  [WARN] Supermemory召回失败: ' + str(e))

    print()
    print("更新Dataview索引...")
    idx = update_dataview_index()
    print("  + " + idx)

    print()
    print("今日知识沉淀完成")
    print("写入 " + str(len(written)) + " 篇笔记")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()