#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
热点发现 V4.0 (BrowserAct版)
- 调用 hotspot_collector_v3.py 使用BrowserAct采集头条房地产热点
- 三条规则：3天周期过滤 / 信息源评分 / 角度标签

作者：可悦
版本：V4.0
日期：2026-06-14
"""
import sys, os, json
from datetime import datetime
from pathlib import Path

# 添加 workspace-social 到路径
SOCIAL_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-social'
if SOCIAL_DIR not in sys.path:
    sys.path.insert(0, SOCIAL_DIR)

OUTPUT_FILE = os.path.expanduser(os.path.join(
    "~", ".openclaw", "workspace", "memory", "数据", "hot_topics",
    f"hot_topics_{datetime.now().strftime('%Y-%m-%d')}.json"
))
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# 导入 V3.3 采集脚本
from scripts.hotspot_collector_v3 import (
    main as collector_main,
    ba_search, dedup, save_report
)

# 导入热点适配器
from scripts.hotspot_adapter import save_for_topic_engine


def main():
    print("=" * 60)
    print("热点发现 V4.0 (BrowserAct + 三条规则)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print("")
    
    # 直接运行采集脚本
    result = collector_main()
    
    # 读取采集报告
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\热点采集') / f'hotspot_{today}.md'
    
    # 读取采集详情
    detail = []
    report_path = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\热点采集') / f'hotspot_{today}.md'
    if report_path.exists():
        content = report_path.read_text(encoding='utf-8')
        import re
        for m in re.finditer(r'^\d+\.\s*\[(.*?)\]\[(.*?)\]\s*(.+)', content, re.MULTILINE):
            detail.append({'source_label': m.group(1), 'angle': m.group(2), 'title': m.group(3).strip()})
        print(f"\n[OK] 采集报告已生成: {report_path} ({len(detail)}条)")
    else:
        print("[WARN] 采集报告未生成")

    # 保存到通用格式
    out = {
        "date": today,
        "count": result.get('total', 0),
        "real": result.get('real', 0),
        "topics": detail[:30],
        "report": result.get('report', ''),
        "suggestions": result.get('suggestions', []),
        "rules": {
            "max_age_days": 3,
            "source_priority": ["官方文件", "权威媒体", "自媒体"],
            "angle_labels": ["政策解读", "市场信号", "购房行为", "区域分析", "房企动向"]
        }
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    # 打印摘要（避免emoji编码问题）
    import sys
    for line in result.get('report', '').split('\n')[:20]:
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
    
    # 同步保存为旧格式（供 topic_engine/auto_writer 使用）
    try:
        from scripts.hotspot_adapter import load_v34_report, save_for_topic_engine
        hots = load_v34_report(today)
        if hots:
            save_for_topic_engine(hots)
    except Exception as e:
        print(f"[WARN] 适配器同步失败: {e}")
    
    print(f"\n[OK] 通用热点数据已保存: {OUTPUT_FILE}")
    # 历史记忆参考
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))
        from memory_ref import recall
        r = recall([
            ('爆款', '爆款 热点'),
            ('话题', '话题'),
            ('日志', '工作日志 自媒体'),
        ], top_k=3, max_total=4)
        if r['count'] > 0:
            print()
            print('\U0001f4d6 【历史爆款参考】')
            for m in r['results']:
                print(f"  [{m['_label']}] ({m['score']:.2f}) {m['text'][:80]}")
    except Exception as e:
        print('\U0001f4d6 【历史爆款参考】加载失败: %s' % e)
    
    return out


if __name__ == "__main__":
    main()