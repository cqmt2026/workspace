#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自愈调度器 - 连接L2定位和L3修复，实现自动修复闭环

用法：
    python self_heal.py "错误信息"              # 定位+自动修复
    python self_heal.py "错误信息" --dry-run    # 只定位不修复
    python self_heal.py --check                 # 检查所有Cron错误并修复
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict

BASE_DIR = Path(__file__).parent
L3_DIR = BASE_DIR / "self_heal_l3_fixers"

# L2规则引擎导入
sys.path.insert(0, str(BASE_DIR))
from self_heal_l2_rule_engine import match_rule, RULES

# 错误类型到L3修复脚本的映射
FIX_SCRIPT_MAP = {
    "billing_error": "fix_model_fallback.py",
    "cron_delivery_error": "fix_cron_delivery.py",
    "state_ownership_error": "fix_gateway_state.py",
    "disk_full": "cleanup_backups.py",
    "encoding_error": "fix_encoding.py",
    "path_not_found": "fix_path.py",
    "import_error": "fix_missing_dep.py",
    "config_invalid": "fix_config.py",
}


def locate_error(error_text: str) -> Optional[Dict]:
    """L2定位错误"""
    return match_rule(error_text)


def execute_fix(rule_key: str, error_text: str = "", dry_run: bool = False) -> Dict:
    """L3执行修复"""
    fix_script = FIX_SCRIPT_MAP.get(rule_key)
    
    if not fix_script:
        return {
            "status": "SKIP",
            "message": f"无自动修复脚本 for {rule_key}，需手动处理"
        }
    
    script_path = L3_DIR / fix_script
    if not script_path.exists():
        return {
            "status": "SKIP",
            "message": f"修复脚本不存在: {fix_script}"
        }
    
    if dry_run:
        return {
            "status": "DRY_RUN",
            "message": f"将执行: {fix_script}",
            "script": fix_script
        }
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        success = result.returncode == 0
        return {
            "status": "OK" if success else "FAIL",
            "script": fix_script,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500]
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


def verify_fix(error_text: str, rule_key: str) -> dict:
    """L4验证修复结果
    
    Returns:
        dict: 验证结果，包含passed、method、detail
    """
    import urllib.request, shutil, json
    
    # 验证方法1：billing_error → 检查模型可用性
    if rule_key == "billing_error":
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:18789/health", timeout=5)
            data = json.loads(resp.read().decode('utf-8'))
            passed = data.get('status') == 'live'
            return {"passed": passed, "method": "gateway_health", "detail": str(data)}
        except Exception as e:
            return {"passed": False, "method": "gateway_health", "detail": str(e)}
    
    # 验证方法2：disk_full → 检查磁盘空间
    if rule_key == "disk_full":
        usage = shutil.disk_usage("C:")
        free_gb = usage.free / (1024**3)
        passed = free_gb > 1.0
        return {"passed": passed, "method": "disk_space", "detail": f"{free_gb:.1f}GB free"}
    
    # 验证方法3：state_ownership_error → 检查Gateway健康
    if rule_key == "state_ownership_error":
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:18789/health", timeout=5)
            passed = resp.status == 200
            return {"passed": passed, "method": "gateway_health", "detail": f"HTTP {resp.status}"}
        except Exception as e:
            return {"passed": False, "method": "gateway_health", "detail": str(e)}
    
    # 验证方法4：encoding_error → 检查脚本是否还有emoji输出
    if rule_key == "encoding_error":
        scripts_dir = Path(r"C:\Users\Administrator\.openclaw\workspace\scripts")
        emoji_files = []
        for f in scripts_dir.glob("*.py"):
            try:
                content = f.read_text(encoding='utf-8')
                if 'print("\u2705' in content or "print('\u2705" in content:
                    emoji_files.append(f.name)
            except:
                pass
        passed = len(emoji_files) == 0
        return {"passed": passed, "method": "emoji_scan", "detail": f"{len(emoji_files)} files still have emoji"}
    
    # 验证方法5：path_not_found → 检查关键目录是否存在
    if rule_key == "path_not_found":
        critical_dirs = [
            r"C:\Users\Administrator\.openclaw\workspace\logs",
            r"C:\Users\Administrator\.openclaw\workspace\memory",
            r"C:\Users\Administrator\.openclaw\workspace\scripts",
        ]
        missing = [d for d in critical_dirs if not os.path.exists(d)]
        passed = len(missing) == 0
        return {"passed": passed, "method": "dir_check", "detail": f"{len(missing)} dirs missing"}
    
    # 验证方法6：cron_delivery_error → 检查delivery配置
    if rule_key == "cron_delivery_error":
        config_file = Path(r"C:\Users\Administrator\.openclaw\openclaw.json")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            autos = config.get('automations', {})
            bad = []
            for cid, job in autos.items():
                delivery = job.get('delivery', {})
                if delivery.get('channel') and delivery.get('mode') != 'none':
                    bad.append(job.get('name', cid[:8]))
            passed = len(bad) == 0
            return {"passed": passed, "method": "config_check", "detail": f"{len(bad)} jobs with bad delivery"}
        except Exception as e:
            return {"passed": False, "method": "config_check", "detail": str(e)}
    
    # 验证方法7：config_invalid → 检查配置文件可解析
    if rule_key == "config_invalid":
        config_file = Path(r"C:\Users\Administrator\.openclaw\openclaw.json")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            has_models = bool(config.get('models'))
            has_agents = bool(config.get('agents'))
            passed = has_models and has_agents
            return {"passed": passed, "method": "json_parse", "detail": f"models={has_models}, agents={has_agents}"}
        except Exception as e:
            return {"passed": False, "method": "json_parse", "detail": str(e)}
    
    # 默认验证：重新匹配错误
    rule = match_rule(error_text)
    passed = rule is None or rule.get("rule_key") != rule_key
    return {"passed": passed, "method": "re_match", "detail": "error pattern no longer matches"}


# L5自主学习：修复日志自动分析
LEARNING_LOG = Path(r"C:\Users\Administrator\.openclaw\workspace\memory\自愈学习日志.json")

def learn_from_fix(rule_key: str, error_text: str, fix_result: dict, verify_result: dict):
    """L5自主学习：记录修复结果，积累经验"""
    from datetime import datetime
    
    # 加载历史学习记录
    history = []
    if LEARNING_LOG.exists():
        try:
            history = json.loads(LEARNING_LOG.read_text(encoding='utf-8'))
        except:
            history = []
    
    # 记录本次修复
    entry = {
        "timestamp": datetime.now().isoformat(),
        "rule_key": rule_key,
        "error": error_text[:200],
        "fix_script": fix_result.get("script", ""),
        "fix_status": fix_result.get("status", ""),
        "verify_passed": verify_result.get("passed", False),
        "verify_method": verify_result.get("method", ""),
    }
    history.append(entry)
    
    # 只保留最近100条
    if len(history) > 100:
        history = history[-100:]
    
    # 保存
    LEARNING_LOG.parent.mkdir(parents=True, exist_ok=True)
    LEARNING_LOG.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')
    
    # 统计成功率
    same_rule_fixes = [h for h in history if h["rule_key"] == rule_key]
    if same_rule_fixes:
        success_rate = sum(1 for h in same_rule_fixes if h["verify_passed"]) / len(same_rule_fixes)
        print(f"  [L5学习] {rule_key} 历史成功率: {success_rate*100:.0f}% ({len(same_rule_fixes)}次)")
        
        # 如果成功率低于50%，建议人工介入
        if success_rate < 0.5 and len(same_rule_fixes) >= 3:
            print(f"  [L5学习] ⚠️ {rule_key} 成功率低于50%，建议人工检查")


def get_healing_stats() -> dict:
    """获取自愈统计数据"""
    if not LEARNING_LOG.exists():
        return {"total": 0, "success_rate": 0, "by_rule": {}}
    
    history = json.loads(LEARNING_LOG.read_text(encoding='utf-8'))
    
    total = len(history)
    success = sum(1 for h in history if h.get("verify_passed"))
    
    by_rule = {}
    for h in history:
        rk = h.get("rule_key", "unknown")
        if rk not in by_rule:
            by_rule[rk] = {"total": 0, "success": 0}
        by_rule[rk]["total"] += 1
        if h.get("verify_passed"):
            by_rule[rk]["success"] += 1
    
    # 计算每类成功率
    for rk, stats in by_rule.items():
        stats["rate"] = round(stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
    
    return {
        "total": total,
        "success_rate": round(success / total * 100) if total > 0 else 0,
        "by_rule": by_rule
    }


def self_heal(error_text: str, dry_run: bool = False) -> Dict:
    """完整自愈流程：定位→修复→验证"""
    print("=" * 50)
    print("自愈流程启动")
    print("=" * 50)
    
    # Step 1: L2定位
    print("\n[1] L2定位错误...")
    rule = locate_error(error_text)
    
    if not rule:
        print("  未匹配到已知规则，需人工处理")
        print(f"  错误信息: {error_text[:100]}")
        return {"status": "NO_MATCH", "error": error_text[:200]}
    
    print(f"  匹配规则: {rule['name']}")
    print(f"  严重度: {rule['severity']}")
    print(f"  建议操作: {rule['action']}")
    
    # Step 2: L3修复
    print("\n[2] L3执行修复...")
    fix_result = execute_fix(rule["rule_key"], error_text, dry_run)
    
    if fix_result["status"] == "SKIP":
        print(f"  跳过: {fix_result['message']}")
        print(f"  手动修复建议: {rule['manual_fix']}")
        return {"status": "SKIP", "rule": rule, "fix": fix_result}
    
    if fix_result["status"] == "DRY_RUN":
        print(f"  模拟运行: {fix_result['message']}")
        return {"status": "DRY_RUN", "rule": rule, "fix": fix_result}
    
    if fix_result["status"] == "OK":
        print(f"  修复脚本执行成功: {fix_result['script']}")
    else:
        print(f"  修复脚本执行失败: {fix_result.get('stderr', '')[:100]}")
        print(f"  手动修复建议: {rule['manual_fix']}")
        return {"status": "FAIL", "rule": rule, "fix": fix_result}
    
    # Step 3: L4验证
    print("\n[3] L4验证修复结果...")
    verify_result = verify_fix(error_text, rule["rule_key"])
    passed = verify_result.get("passed", False)
    
    print(f"  验证方法: {verify_result.get('method', '')}")
    print(f"  结果: {'通过' if passed else '失败'} ({verify_result.get('detail', '')})")
    
    # Step 4: L5学习
    print("\n[4] L5学习：记录修复经验...")
    learn_from_fix(rule["rule_key"], error_text, fix_result, verify_result)
    
    if passed:
        print("  验证通过，修复成功")
        return {"status": "OK", "rule": rule, "fix": fix_result, "verify": verify_result}
    else:
        print("  验证失败，可能需要手动检查")
        return {"status": "OK_BUT_UNVERIFIED", "rule": rule, "fix": fix_result, "verify": verify_result}


def show_stats():
    """显示自愈统计"""
    stats = get_healing_stats()
    print("=" * 50)
    print("自愈机制统计")
    print("=" * 50)
    print(f"总修复次数: {stats['total']}")
    print(f"整体成功率: {stats['success_rate']}%")
    print()
    if stats['by_rule']:
        print("各错误类型:")
        for rk, info in sorted(stats['by_rule'].items(), key=lambda x: -x[1]['total']):
            print(f"  - {rk}: {info['total']}次, 成功率{info['rate']}%")


def check_cron_errors() -> list:
    """检查所有Cron任务的错误"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            # 尝试非JSON模式
            result = subprocess.run(
                ["openclaw", "cron", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # 简单解析文本输出找error
            errors = []
            for line in result.stdout.split('\n'):
                if 'error' in line.lower():
                    errors.append(line.strip())
            return errors
        
        data = json.loads(result.stdout)
        jobs = data.get("jobs", data) if isinstance(data, dict) else data
        errors = []
        for job in jobs:
            state = job.get("state", {})
            status = state.get("lastRunStatus", "")
            if "error" in str(status).lower():
                errors.append({
                    "name": job.get("name", ""),
                    "error": state.get("lastRunError", "")[:200]
                })
        return errors
    except Exception as e:
        print(f"检查Cron错误失败: {e}")
        return []


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="自愈调度器")
    parser.add_argument("error", nargs="?", help="错误信息")
    parser.add_argument("--dry-run", action="store_true", help="只定位不修复")
    parser.add_argument("--check", action="store_true", help="检查所有Cron错误并自愈")
    parser.add_argument("--stats", action="store_true", help="显示自愈统计")
    
    args = parser.parse_args()
    
    # 显示统计
    if args.stats:
        show_stats()
        return
    
    if args.check:
        # 检查所有Cron错误
        print("检查Cron任务错误...")
        errors = check_cron_errors()
        
        if not errors:
            print("  无错误")
            return
        
        print(f"  发现 {len(errors)} 个错误:")
        for err in errors:
            print(f"  - {err.get('name', '')}: {err.get('error', '')[:80]}")
            # 尝试自愈
            result = self_heal(err.get("error", ""), dry_run=args.dry_run)
            print()
        
        return
    
    if args.error:
        result = self_heal(args.error, dry_run=args.dry_run)
        print()
        print("=" * 50)
        print(f"自愈结果: {result['status']}")
        print("=" * 50)
        return
    
    parser.print_help()


if __name__ == '__main__':
    main()
