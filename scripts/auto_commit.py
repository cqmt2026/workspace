#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
auto_commit.py - 自动Git提交工具

功能：
1. 检查工作区变更
2. 自动add和commit
3. 生成提交消息
4. 记录提交日志

用法：
    python auto_commit.py              # 自动提交所有变更
    python auto_commit.py --dry-run   # 预览变更不提交
    python auto_commit.py --message "自定义消息"
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw")
LOG_FILE = BASE / "workspace" / "logs" / "auto_commit.log"

def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=cwd or str(BASE)
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, '', str(e)

def get_git_status():
    """获取Git状态"""
    code, stdout, stderr = run_cmd('git status --short')
    if code != 0:
        return None
    return stdout.strip()

def get_git_diff():
    """获取变更摘要"""
    code, stdout, stderr = run_cmd('git diff --stat')
    if code != 0:
        return ''
    return stdout.strip()

def auto_commit(dry_run=False, custom_message=None):
    """自动提交"""
    # 检查是否有变更
    status = get_git_status()
    if not status:
        print('Git错误: 无法获取状态')
        return False
    
    if not status:
        print('工作区干净，无变更需要提交')
        return True
    
    # 生成提交消息
    if custom_message:
        message = custom_message
    else:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        message = f'chore: 自动备份 ({timestamp})'
    
    print(f'准备提交: {message}')
    print(f'变更文件数: {len([l for l in status.split(chr(10)) if l.strip()])}')
    
    if dry_run:
        print('[DRY RUN] 跳过实际提交')
        print('变更预览:')
        for line in status.split('\n')[:20]:
            if line.strip():
                print('  ' + line)
        return True
    
    # 添加所有变更
    code, stdout, stderr = run_cmd('git add .')
    if code != 0:
        print(f'git add 失败: {stderr}')
        return False
    
    # 提交
    code, stdout, stderr = run_cmd(f'git commit -m "{message}"')
    if code != 0:
        print(f'git commit 失败: {stderr}')
        return False
    
    # 记录日志
    log_entry = f'[{datetime.datetime.now().isoformat()}] {message}\n'
    log_entry += f'  变更文件数: {len([l for l in status.split(chr(10)) if l.strip()])}\n'
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(f'提交成功: {message}')
    print(f'日志已保存: {LOG_FILE}')
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='自动Git提交工具')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    parser.add_argument('--message', type=str, help='自定义提交消息')
    args = parser.parse_args()
    
    print('='*50)
    print('自动Git提交工具')
    print('='*50)
    print()
    
    success = auto_commit(args.dry_run, args.message)
    
    if success:
        print()
        print('完成')
    else:
        print()
        print('失败')
        sys.exit(1)

if __name__ == '__main__':
    main()
