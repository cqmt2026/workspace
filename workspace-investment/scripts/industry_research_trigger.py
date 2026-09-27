# -*- coding: utf-8 -*-
"""
行业研报自动触发脚本
=====================
功能：
    1. 读取RPS每日预警（rps_alert_latest.json）
    2. 按优先级选择预警板块（RPS下降/异动）
    3. 调用 industry_research.py 生成研报
    4. 归档到Obsidian

用法：
    python scripts/industry_research_trigger.py

Cron: 17:00 每个交易日
"""
import io
import sys, os, json
from datetime import date
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
OUT_DIR = WORKSPACE / "out_data"
sys.path.insert(0, str(WORKSPACE / "scripts"))


def load_rps_alerts():
    """读取RPS预警"""
    alert_file = OUT_DIR / "rps_alert_latest.json"
    if not alert_file.exists():
        # 尝试旧版
        alert_file = OUT_DIR / "rps_alert_latest.json"
        if not alert_file.exists():
            print("⚠️ 未找到RPS预警文件")
            return []
    
    try:
        with open(alert_file, encoding='utf-8') as f:
            data = json.load(f)
        
        alerts = []
        if isinstance(data, list):
            alerts = data
        elif isinstance(data, dict):
            alerts = data.get('alerts', data.get('events', []))
        
        print(f"📊 RPS预警: {len(alerts)} 条")
        return alerts
    except Exception as e:
        print(f"⚠️ 读取RPS预警失败: {e}")
        return []


def load_rps_top_boards():
    """读取RPS强势板块TOP列表
    
    核心原则：仅使用今日RPS数据。
    交易日当天RPS未采集时（16:10前），返回空列表，由调用方标注"数据缺失"。
    绝不用昨日/前日/最新文件填充。
    """
    today = date.today().isoformat()
    
    # 只尝试今天的文件
    for fname in [f"RPS_daily_summary_{today}.json"]:
        fp = OUT_DIR / fname
        if fp.exists():
            try:
                with open(fp, encoding='utf-8') as f:
                    data = json.load(f)
                top = data.get('top_boards', data.get('top20', []))
                if top:
                    print(f"📈 RPS强势板块 ({today}): {len(top)} 个")
                    return top
            except:
                pass
    
    # 今日RPS不存在，返回空列表（不是用旧数据填充）
    print(f"⚠️ RPS数据缺失：今日RPS尚未采集（收盘后16:10自动生成）")
    return []


def select_trigger_boards(alerts, top_boards):
    """选择要生成研报的板块"""
    candidates = []
    seen = set()
    
    # 优先级1: RPS预警中的板块
    for a in alerts:
        name = a.get('board_name', a.get('name', ''))
        if name and name not in seen:
            reason = a.get('reason', a.get('alert_type', '预警'))
            candidates.append({'name': name, 'reason': reason, 'priority': 1})
            seen.add(name)
    
    # 优先级2: RPS强势板块TOP5（每日自动生成）
    for b in top_boards[:5]:
        name = b.get('name', b.get('board_name', ''))
        if name and name not in seen:
            candidates.append({'name': name, 'reason': 'RPS强势', 'priority': 2})
            seen.add(name)
    
    return candidates


def main():
    print("=" * 55)
    print("行业研报自动触发")
    print("=" * 55)
    
    alerts = load_rps_alerts()
    top_boards = load_rps_top_boards()
    
    candidates = select_trigger_boards(alerts, top_boards)
    
    if not candidates:
        print("📭 无候选板块，跳过行业研报生成")
        return
    
    print(f"\n🎯 候选板块 ({len(candidates)} 个):")
    for c in candidates:
        print(f"  [{c['priority']}] {c['name']} - {c['reason']}")
    
    # 只生成前2个（避免耗时过长）
    max_generate = 2
    generated = 0
    
    for c in candidates:
        if generated >= max_generate:
            break
        
        print(f"\n{'='*55}")
        print(f"🔍 生成研报: {c['name']} ({c['reason']})")
        print(f"{'='*55}")
        
        try:
            # 调用 industry_funnel 模块替代 industry_research
            from industry_funnel import run_industry_funnel
            result = run_industry_funnel(c['name'], top_n=3)
            generated += 1
            print(f"✅ 研报生成完成: {c['name']}")
        except Exception as e:
            print(f"❌ 生成失败: {c['name']} - {e}")
    
    print(f"\n{'='*55}")
    print(f"📊 本次生成: {generated} 篇行业研报")
    print(f"{'='*55}")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()