#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
user_preferences.py - 用户偏好管理工具

功能：
1. 记录用户偏好设置
2. 自动学习用户习惯
3. 个性化响应生成

用法：
    python user_preferences.py --get style
    python user_preferences.py --set style concise
    python user_preferences.py --learn
"""

import os
import sys
import json
import datetime
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw")
PREFERENCES_FILE = BASE / "user_preferences.json"
LEARNING_LOG = BASE / "workspace" / "logs" / "preference_learning.log"

# 默认偏好
DEFAULT_PREFERENCES = {
    # 沟通风格
    "communication_style": {
        "default": "direct",  # direct/concise/detailed
        "technical": "detailed",  # 技术话题偏好
        "casual": "concise"  # 日常对话偏好
    },
    
    # 输出格式
    "output_format": {
        "default": "markdown",  # markdown/text/json
        "tables": True,  # 是否使用表格
        "code_blocks": True,  # 是否高亮代码
        "emoji": True  # 是否使用emoji
    },
    
    # 执行风格
    "execution_style": {
        "confirm_before_delete": True,  # 删除前确认
        "confirm_before_modify": True,  # 修改前确认
        "auto_execute_simple": True,  # 简单任务自动执行
        "show_progress": True  # 显示进度
    },
    
    # 技术偏好
    "tech_stack": {
        "primary_language": "python",  # 首选语言
        "shell": "powershell",  # 命令行
        "editor": "vscode",  # 编辑器
        "vcs": "git"  # 版本控制
    },
    
    # 工作习惯
    "work_habits": {
        "preferred_time": "daytime",  # daytime/evening/night
        "batch_size": "medium",  # small/medium/large
        "verification_level": "high"  # low/medium/high
    }
}

def load_preferences():
    """加载用户偏好"""
    if PREFERENCES_FILE.exists():
        try:
            with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_PREFERENCES.copy()

def save_preferences(prefs):
    """保存用户偏好"""
    with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)

def get_preference(category, key=None, default=None):
    """获取偏好设置"""
    prefs = load_preferences()
    
    if key:
        return prefs.get(category, {}).get(key, default)
    else:
        return prefs.get(category, default)

def set_preference(category, key, value):
    """设置偏好"""
    prefs = load_preferences()
    
    if category not in prefs:
        prefs[category] = {}
    
    prefs[category][key] = value
    save_preferences(prefs)
    
    # 记录学习日志
    log_learning(f"设置偏好: {category}.{key} = {value}")
    
    return True

def log_learning(message):
    """记录学习日志"""
    os.makedirs(LEARNING_LOG.parent, exist_ok=True)
    
    timestamp = datetime.datetime.now().isoformat()
    with open(LEARNING_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def learn_from_interaction(interaction_type, content):
    """从交互中学习"""
    prefs = load_preferences()
    
    # 简单规则学习
    if interaction_type == "correction":
        # 用户纠正了我，记录偏好
        log_learning(f"学习纠正: {content[:100]}")
        
    elif interaction_type == "approval":
        # 用户确认了，强化此行为
        log_learning(f"学习确认: {content[:100]}")
        
    elif interaction_type == "preference_explicit":
        # 用户明确表达了偏好
        log_learning(f"明确偏好: {content[:100]}")

def generate_response_template(topic):
    """生成个性化响应模板"""
    prefs = load_preferences()
    
    style = prefs.get("communication_style", {}).get("default", "direct")
    format_cfg = prefs.get("output_format", {})
    
    template = {
        "style": style,
        "use_tables": format_cfg.get("tables", True),
        "use_code_blocks": format_cfg.get("code_blocks", True),
        "use_emoji": format_cfg.get("emoji", True),
        "prefix": ""
    }
    
    # 根据风格调整前缀
    if style == "concise":
        template["prefix"] = "【简】"
    elif style == "detailed":
        template["prefix"] = "【详】"
    else:
        template["prefix"] = ""
    
    return template

def main():
    import argparse
    parser = argparse.ArgumentParser(description='用户偏好管理')
    parser.add_argument('--get', nargs=2, metavar=('CATEGORY', 'KEY'), help='获取偏好')
    parser.add_argument('--set', nargs=3, metavar=('CATEGORY', 'KEY', 'VALUE'), help='设置偏好')
    parser.add_argument('--learn', nargs=2, metavar=('TYPE', 'CONTENT'), help='学习交互')
    parser.add_argument('--show', action='store_true', help='显示所有偏好')
    args = parser.parse_args()
    
    if args.show:
        prefs = load_preferences()
        print(json.dumps(prefs, indent=2, ensure_ascii=False))
    
    elif args.get and len(args.get) == 2:
        value = get_preference(args.get[0], args.get[1])
        print(value if value is not None else "未设置")
    
    elif args.set and len(args.set) == 3:
        set_preference(args.set[0], args.set[1], args.set[2])
        print(f"已设置: {args.set[0]}.{args.set[1]} = {args.set[2]}")
    
    elif args.learn and len(args.learn) == 2:
        learn_from_interaction(args.learn[0], args.learn[1])
        print("已记录学习")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
