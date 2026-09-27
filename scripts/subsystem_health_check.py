#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子系统健康检查脚本
检查各子系统的：Cron状态、脚本完整性、数据产出、商业化指标
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace")
SUBSYSTEMS = {
    "investment": {
        "path": WORKSPACE / "workspace-investment",
        "scripts": ["collect_daily_zt_kline.py", "daily_analysis.py", "holding_alert.py", "morning_brief.py", "rps_push.py"],
        "cron_prefix": "INV-",
        "commercial_metric": "策略盈亏/回测表现"
    },
    "maphot": {
        "path": WORKSPACE / "workspace-maphot",
        "scripts": ["pipeline.py", "选题采集_v3.py", "脚本生成_v3.py", "地图绘制_v5.py", "配音生成_v2.py", "视频合成_v2.py"],
        "script_dirs": ["scripts/core", "scripts"],
        "cron_prefix": "MapHot-",
        "commercial_metric": "视频发布数量/播放量"
    },
    "novel": {
        "path": WORKSPACE / "workspace-novel",
        "scripts": ["novel_write_flow.py", "batch_write.py", "auto_write_daily.py"],
        "cron_prefix": None,
        "commercial_metric": "番茄连载收入/读者数"
    },
    "social": {
        "path": WORKSPACE / "workspace-social",
        "scripts": ["social_writing_workflow.py", "hotspot_collector_v3.py", "viral_analyzer.py"],
        "cron_prefix": None,
        "commercial_metric": "播放量/涨粉趋势"
    },
    "pv": {
        "path": WORKSPACE / "workspace-pv",
        "scripts": ["run.py", "run_full.py", "publish_toutiao.py"],
        "cron_prefix": "PV-",
        "commercial_metric": "内容发布量/阅读量"
    },
    "baidu": {
        "path": Path(r"C:\Users\Administrator\.openclaw\workspace-baiduagent"),
        "scripts": ["analyze_agents.py"],
        "cron_prefix": "Baidu-",
        "commercial_metric": "客户转化率"
    },
    "math": {
        "path": WORKSPACE / "workspace-math",
        "scripts": [],
        "cron_prefix": "Math-",
        "commercial_metric": "视频播放量"
    },
    "weixin": {
        "path": WORKSPACE / "workspace-weixin",
        "scripts": ["update_knowledge.py", "sync_corrections.py"],
        "cron_prefix": "WX-",
        "commercial_metric": "小程序用户数"
    }
}

def check_cron_status(prefix):
    """检查指定前缀的Cron状态"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.split('\n')
        errors = []
        oks = []
        for line in lines:
            if prefix and prefix not in line:
                continue
            if 'error' in line:
                errors.append(line.strip())
            elif 'ok' in line and 'skill-collection' not in line:
                oks.append(line.strip())
        return {"errors": len(errors), "oks": len(oks), "error_details": errors[:3]}
    except Exception as e:
        return {"error": str(e)}

def check_scripts_exist(subsystem):
    """检查子系统脚本完整性"""
    path = SUBSYSTEMS[subsystem]["path"]
    scripts = SUBSYSTEMS[subsystem]["scripts"]
    search_dirs = SUBSYSTEMS[subsystem].get("script_dirs", ["scripts"])
    missing = []
    found = []
    for script in scripts:
        found_it = False
        for dir_name in search_dirs:
            full_path = path / dir_name / script
            if full_path.exists():
                found.append(script)
                found_it = True
                break
        if not found_it:
            missing.append(script)
    return {"found": len(found), "missing": len(missing), "missing_list": missing}

def check_data_output(subsystem):
    """检查子系统数据产出"""
    base = SUBSYSTEMS[subsystem]["path"]
    outputs = []
    
    # Check common output directories
    for dir_name in ["data", "outputs", "output", "logs"]:
        dir_path = base / dir_name
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            if files:
                newest = max(files, key=lambda f: f.stat().st_mtime)
                delta = datetime.now() - datetime.fromtimestamp(newest.stat().st_mtime)
                hours_ago = delta.total_seconds() / 3600
                outputs.append(f"{dir_name}/{newest.name} ({hours_ago:.1f}h ago)")
    
    return outputs[:3]  # Return top 3

def main():
    print(f"{'='*60}")
    print(f"子系统健康检查 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    results = {}
    for name, config in SUBSYSTEMS.items():
        print(f"【{name}】")
        
        # Cron status
        cron = check_cron_status(config["cron_prefix"])
        print(f"  Cron: {cron.get('oks', 0)} OK, {cron.get('errors', 0)} Error")
        
        # Scripts
        scripts = check_scripts_exist(name)
        print(f"  脚本: {scripts['found']} found, {scripts['missing']} missing")
        if scripts['missing_list']:
            print(f"    缺失: {', '.join(scripts['missing_list'][:3])}")
        
        # Data output
        outputs = check_data_output(name)
        if outputs:
            print(f"  产出: {outputs[-1]}")
        
        # Commercial metric
        print(f"  商业化: {config['commercial_metric']}")
        print()
        
        results[name] = {
            "cron": cron,
            "scripts": scripts,
            "outputs": outputs
        }
    
    # Summary
    print(f"{'='*60}")
    print("汇总:")
    total_cron_errors = sum(r['cron'].get('errors', 0) for r in results.values())
    total_script_missing = sum(r['scripts'].get('missing', 0) for r in results.values())
    print(f"  Cron错误总数: {total_cron_errors}")
    print(f"  缺失脚本总数: {total_script_missing}")
    print(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    main()
