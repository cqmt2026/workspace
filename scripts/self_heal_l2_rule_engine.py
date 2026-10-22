#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自愈机制L2 - 异常定位规则引擎

功能：
1. 定义错误类型规则库
2. 匹配错误日志与规则
3. 输出定位结果和推荐修复方案

用法：
    python self_heal_l2_rule_engine.py "错误信息"
    python self_heal_l2_rule_engine.py --file error_log.txt
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 规则库定义
RULES = {
    "billing_error": {
        "name": "模型额度耗尽",
        "patterns": [
            r"billing error",
            r"429.*tpm|rpm limit",
            r"insufficient balance",
            r"出账失败",
            r"余额不足"
        ],
        "severity": "HIGH",
        "action": "switch_model",
        "fallback_models": ["agnes-2.0-flash", "sensenova/sensenova-6.8-flash-lite"],
        "manual_fix": "检查API密钥余额或更换模型"
    },
    "path_not_found": {
        "name": "路径不存在",
        "patterns": [
            r"FileNotFoundError",
            r"系统找不到指定的路径",
            r"path not found",
            r"No such file or directory"
        ],
        "severity": "MEDIUM",
        "action": "create_dir|restore_from_backup",
        "manual_fix": "创建缺失目录或从备份恢复"
    },
    "disk_full": {
        "name": "磁盘空间不足",
        "patterns": [
            r"No space left on device",
            r"磁盘空间不足",
            r"failed to write",
            r"write failed"
        ],
        "severity": "CRITICAL",
        "action": "cleanup_old_backups|expand_disk",
        "manual_fix": "清理旧备份文件或扩展磁盘"
    },
    "cron_delivery_error": {
        "name": "Cron投递配置错误",
        "patterns": [
            r"Channel is required",
            r"delivery.*unresolved",
            r"no configured channels",
            r"message tool target unresolved"
        ],
        "severity": "MEDIUM",
        "action": "fix_delivery_config",
        "manual_fix": "配置delivery.channel或设为none"
    },
    "state_ownership_error": {
        "name": "State所有权验证失败",
        "patterns": [
            r"state ownership.*could not be verified",
            r"Shared-state read and cleanup failed",
            r"openclaw.sqlite.*could not be verified"
        ],
        "severity": "HIGH",
        "action": "restart_gateway|fix_state_file",
        "manual_fix": "重启Gateway或修复state文件"
    },
    "encoding_error": {
        "name": "编码错误",
        "patterns": [
            r"UnicodeEncodeError",
            r"UnicodeDecodeError",
            r"GBK.*decode",
            r"UTF-8.*encode"
        ],
        "severity": "LOW",
        "action": "fix_encoding",
        "manual_fix": "使用utf-8编码读写文件"
    },
    "syntax_error": {
        "name": "Python语法错误",
        "patterns": [
            r"SyntaxError",
            r"invalid syntax",
            r"unexpected character",
            r"unterminated string"
        ],
        "severity": "MEDIUM",
        "action": "fix_syntax",
        "manual_fix": "检查语法错误并修复"
    },
    "import_error": {
        "name": "模块导入失败",
        "patterns": [
            r"ModuleNotFoundError",
            r"No module named",
            r"ImportError"
        ],
        "severity": "MEDIUM",
        "action": "install_module|fix_path",
        "manual_fix": "安装缺失模块或修正Python路径"
    },
    "permission_error": {
        "name": "权限错误",
        "patterns": [
            r"PermissionError",
            r"Access is denied",
            r"Operation not permitted"
        ],
        "severity": "HIGH",
        "action": "fix_permissions",
        "manual_fix": "检查文件权限或以管理员身份运行"
    },
    "network_error": {
        "name": "网络连接错误",
        "patterns": [
            r"ConnectionRefusedError",
            r"TimeoutError",
            r"requests.exceptions",
            r"urllib.error"
        ],
        "severity": "MEDIUM",
        "action": "check_network|retry",
        "manual_fix": "检查网络连接或API服务状态"
    },
    "cron_timeout": {
        "name": "Cron任务超时",
        "patterns": [
            r"timed out.*seconds",
            r"Run timed out",
            r"timeout.*exceeded"
        ],
        "severity": "MEDIUM",
        "action": "increase_timeout",
        "manual_fix": "增加Cron任务timeoutSeconds"
    },
    "json_parse_error": {
        "name": "JSON解析错误",
        "patterns": [
            r"JSONDecodeError",
            r"Expecting value",
            r"Invalid control character"
        ],
        "severity": "LOW",
        "action": "fix_json_format",
        "manual_fix": "检查JSON格式是否正确"
    },
    "argparse_error": {
        "name": "参数解析错误",
        "patterns": [
            r"argparse.*error",
            r"invalid choice",
            r"unrecognized arguments",
            r"unsupported format character"
        ],
        "severity": "LOW",
        "action": "fix_argparse",
        "manual_fix": "检查命令行参数格式"
    },
    "sqlite_error": {
        "name": "SQLite数据库错误",
        "patterns": [
            r"sqlite3.*Error",
            r"database is locked",
            r"no such table",
            r"database disk image is malformed"
        ],
        "severity": "HIGH",
        "action": "repair_db|restore_backup",
        "manual_fix": "修复数据库或从备份恢复"
    },
    "port_conflict": {
        "name": "端口冲突",
        "patterns": [
            r"Address already in use",
            r"port.*occupied",
            r"EADDRINUSE"
        ],
        "severity": "HIGH",
        "action": "kill_process|change_port",
        "manual_fix": "结束占用端口的进程或更换端口"
    },
    "module_version_conflict": {
        "name": "模块版本冲突",
        "patterns": [
            r"VersionConflict",
            r"version.*mismatch",
            r"requires.*different"
        ],
        "severity": "MEDIUM",
        "action": "pin_version|upgrade",
        "manual_fix": "锁定模块版本或升级依赖"
    },
    "config_invalid": {
        "name": "配置文件无效",
        "patterns": [
            r"config.*invalid",
            r"config.*not found",
            r"配置.*错误",
            r"配置.*不存在"
        ],
        "severity": "HIGH",
        "action": "restore_config|fix_config",
        "manual_fix": "从备份恢复配置文件或修复配置"
    },
    "process_dead": {
        "name": "进程异常退出",
        "patterns": [
            r"process.*terminated",
            r"process.*killed",
            r"SIGKILL",
            r"non-zero exit code"
        ],
        "severity": "HIGH",
        "action": "restart_process",
        "manual_fix": "重启进程"
    },
    "memory_leak": {
        "name": "内存不足",
        "patterns": [
            r"MemoryError",
            r"out of memory",
            r"内存不足"
        ],
        "severity": "CRITICAL",
        "action": "restart_process|reduce_load",
        "manual_fix": "重启进程或减少负载"
    }
}

# 日志目录
LOG_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\logs")
FIX_LOG_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\memory\日志\修复日志")


def match_rule(error_text: str) -> Optional[Dict]:
    """匹配错误规则
    
    Args:
        error_text: 错误信息
        
    Returns:
        匹配的规则字典，未匹配返回None
    """
    error_lower = error_text.lower()
    
    for rule_key, rule in RULES.items():
        for pattern in rule["patterns"]:
            if re.search(pattern, error_lower, re.IGNORECASE):
                return {
                    "rule_key": rule_key,
                    "name": rule["name"],
                    "severity": rule["severity"],
                    "action": rule["action"],
                    "fallback_models": rule.get("fallback_models", []),
                    "manual_fix": rule["manual_fix"]
                }
    
    return None


def analyze_log_file(filepath: str) -> List[Dict]:
    """分析日志文件中的错误
    
    Args:
        filepath: 日志文件路径
        
    Returns:
        错误列表，每项包含位置、错误信息、匹配规则
    """
    results = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # 检测错误关键字
            if any(kw in line.lower() for kw in ['error', 'exception', 'traceback', 'failed']):
                # 提取错误信息（取前后5行上下文）
                start = max(0, i - 6)
                end = min(len(lines), i + 5)
                context = ''.join(lines[start:end])
                
                # 匹配规则
                rule = match_rule(line)
                
                results.append({
                    "line": i,
                    "text": line.strip()[:200],
                    "context": context[:500],
                    "rule": rule
                })
                
    except Exception as e:
        print(f"读取日志文件失败: {e}", file=sys.stderr)
    
    return results


def analyze_fix_logs() -> Dict:
    """分析修复日志，统计错误模式
    
    Returns:
        统计结果
    """
    if not FIX_LOG_DIR.exists():
        return {"total": 0, "by_system": {}, "by_severity": {}}
    
    logs = list(FIX_LOG_DIR.glob("fix_*.md"))
    stats = {
        "total": len(logs),
        "by_system": {},
        "by_severity": {},
        "recent": []
    }
    
    for log in logs:
        # 从文件名提取子系统
        match = re.search(r'fix_\d{8}_(\w+)_', log.name)
        system = match.group(1) if match else "unknown"
        stats["by_system"][system] = stats["by_system"].get(system, 0) + 1
        
        # 读取内容提取严重度
        try:
            content = log.read_text(encoding='utf-8', errors='ignore')
            if 'P0' in content or 'critical' in content.lower():
                stats["by_severity"]["P0/Critical"] = stats["by_severity"].get("P0/Critical", 0) + 1
            elif 'P1' in content or 'high' in content.lower():
                stats["by_severity"]["P1/High"] = stats["by_severity"].get("P1/High", 0) + 1
            elif 'P2' in content or 'medium' in content.lower():
                stats["by_severity"]["P2/Medium"] = stats["by_severity"].get("P2/Medium", 0) + 1
            else:
                stats["by_severity"]["P3/Low"] = stats["by_severity"].get("P3/Low", 0) + 1
        except:
            pass
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="自愈机制L2 - 异常定位规则引擎")
    parser.add_argument("error", nargs="?", help="错误信息（直接输入或从文件读取）")
    parser.add_argument("--file", "-f", help="日志文件路径")
    parser.add_argument("--analyze-fix-logs", action="store_true", help="分析修复日志统计")
    parser.add_argument("--output", "-o", help="输出JSON文件路径")
    
    args = parser.parse_args()
    
    # 分析修复日志统计
    if args.analyze_fix_logs:
        stats = analyze_fix_logs()
        print("=" * 50)
        print("修复日志统计分析")
        print("=" * 50)
        print(f"总修复记录: {stats['total']}条")
        print()
        print("按子系统分布:")
        for system, count in sorted(stats['by_system'].items(), key=lambda x: -x[1]):
            print(f"  {system}: {count}条")
        print()
        print("按严重度分布:")
        for severity, count in sorted(stats['by_severity'].items()):
            print(f"  {severity}: {count}条")
        return
    
    # 分析日志文件
    if args.file:
        results = analyze_log_file(args.file)
        if not results:
            print("未检测到错误")
            return
        
        print(f"发现 {len(results)} 个错误:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"[{i}] 行{result['line']}: {result['text']}")
            if result['rule']:
                rule = result['rule']
                print(f"    匹配规则: {rule['name']} (严重度: {rule['severity']})")
                print(f"    建议操作: {rule['action']}")
                print(f"    手动修复: {rule['manual_fix']}")
            print()
        
        # 输出JSON
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {output_path}")
        
        return
    
    # 直接输入错误信息
    if args.error:
        rule = match_rule(args.error)
        if rule:
            print("=" * 50)
            print("错误定位结果")
            print("=" * 50)
            print(f"错误信息: {args.error[:100]}...")
            print()
            print(f"匹配规则: {rule['name']}")
            print(f"严重度: {rule['severity']}")
            print(f"建议操作: {rule['action']}")
            if rule.get('fallback_models'):
                print(f"推荐备用模型: {', '.join(rule['fallback_models'])}")
            print(f"手动修复: {rule['manual_fix']}")
        else:
            print(f"未匹配到已知规则: {args.error[:100]}...")
        return
    
    # 无参数：显示帮助
    parser.print_help()


if __name__ == '__main__':
    main()
