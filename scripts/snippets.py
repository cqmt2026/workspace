#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码片段库 - 常用代码模式集合

用法：
    python snippets.py --list                    # 列出所有片段
    python snippets.py --get error_handling      # 获取片段
    python snippets.py --get file_io --verbose   # 详细查看
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional


# 代码片段定义
SNIPPETS = {
    'error_handling': {
        'name': '错误处理模式',
        'description': '分层错误处理，具体异常捕获',
        'code': '''
def safe_operation(data: Any) -> Optional[Result]:
    """安全执行操作，分层错误处理"""
    try:
        # 业务逻辑
        result = process(data)
        
        # 验证结果
        if result is None:
            raise ValueError("处理结果为空")
        
        return result
        
    except ValueError as e:
        logger.error(f"数据验证失败: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        return None
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        raise
''',
        'use_case': '所有需要错误处理的函数'
    },
    
    'file_io': {
        'name': '文件读写模式',
        'description': '安全的文件读写，支持中文路径',
        'code': '''
def read_file(filepath: str, encoding: str = 'utf-8') -> str:
    """读取文件，支持中文路径"""
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")
    
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        # 尝试其他编码
        for alt_encoding in ['gbk', 'latin-1']:
            try:
                return path.read_text(encoding=alt_encoding)
            except:
                continue
        raise
    
def write_file(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """写入文件，自动创建目录"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
''',
        'use_case': '所有文件IO操作'
    },
    
    'api_call': {
        'name': 'API调用模式',
        'description': '带重试和超时的API调用',
        'code': '''
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def api_get(url: str, params: dict = None, timeout: int = 30) -> dict:
    """带重试的GET请求"""
    session = requests.Session()
    
    # 配置重试策略
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"请求超时: {url}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP错误: {e}")
        raise
''',
        'use_case': '所有外部API调用'
    },
    
    'config_loading': {
        'name': '配置加载模式',
        'description': '多级配置加载，支持环境变量覆盖',
        'code': '''
import os
from pathlib import Path
import json

def load_config(config_path: str = None) -> dict:
    """加载配置，支持环境变量覆盖"""
    # 默认路径
    if config_path is None:
        config_path = Path(__file__).parent / 'config.json'
    
    # 加载配置文件
    config = {}
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 环境变量覆盖
    env_overrides = {
        'API_KEY': 'api.key',
        'API_URL': 'api.base_url',
        'LOG_LEVEL': 'logging.level'
    }
    
    for env_var, config_path in env_overrides.items():
        value = os.getenv(env_var)
        if value:
            set_nested(config, config_path, value)
    
    return config

def set_nested(d: dict, path: str, value):
    """设置嵌套字典值"""
    keys = path.split('.')
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
''',
        'use_case': '所有需要配置管理的脚本'
    },
    
    'logging_setup': {
        'name': '日志配置模式',
        'description': '标准化日志配置，支持文件和控制台',
        'code': '''
import logging
import sys
from pathlib import Path

def setup_logger(name: str, log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """配置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # 文件handler
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
''',
        'use_case': '所有需要日志的脚本'
    },
    
    'argparse_template': {
        'name': '命令行参数模板',
        'description': '标准化的argparse配置',
        'code': '''
import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='脚本描述',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python script.py --input data.csv --output result.json
        """
    )
    
    # 必填参数
    parser.add_argument('--input', '-i', required=True, help='输入文件')
    
    # 可选参数
    parser.add_argument('--output', '-o', help='输出文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--config', '-c', help='配置文件')
    
    # 数值参数
    parser.add_argument('--threshold', '-t', type=float, default=0.5,
                        help='阈值（默认0.5）')
    
    # 枚举参数
    parser.add_argument('--mode', '-m', choices=['fast', 'accurate'],
                        default='fast', help='运行模式')
    
    return parser.parse_args()
''',
        'use_case': '所有命令行脚本'
    },
    
    'path_handling': {
        'name': '路径处理模式',
        'description': 'Windows中文路径安全处理',
        'code': '''
from pathlib import Path
import os

# 使用Path对象处理路径
base_dir = Path(r'C:\\Users\\Administrator\\.openclaw')
config_file = base_dir / 'config.json'

# 安全的路径拼接
def safe_join(base: Path, *paths) -> Path:
    """安全拼接路径"""
    result = base
    for p in paths:
        result = result / p
    # 规范化路径
    return result.resolve()

# Windows路径处理
windows_path = r'C:\\Users\\Administrator\\.openclaw\\workspace'
path_obj = Path(windows_path)

# 检查路径
if path_obj.exists():
    print(f"路径存在: {path_obj}")
if path_obj.is_dir():
    print(f"是目录: {path_obj}")
if path_obj.is_file():
    print(f"是文件: {path_obj}")
''',
        'use_case': '所有涉及路径操作的脚本'
    },
    
    'data_validation': {
        'name': '数据验证模式',
        'description': '输入数据验证，边界全覆盖',
        'code': '''
from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: list
    warnings: list

def validate_data(data: Any, schema: dict) -> ValidationResult:
    """验证数据结构"""
    errors = []
    warnings = []
    
    # 空值检查
    if data is None:
        return ValidationResult(False, ['数据为空'], [])
    
    # 类型检查
    expected_type = schema.get('type')
    if expected_type and not isinstance(data, expected_type):
        errors.append(f"类型错误: 期望{expected_type}, 得到{type(data)}")
    
    # 字段验证
    if isinstance(data, dict):
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必填字段: {field}")
        
        # 可选字段验证
        for field, rules in schema.get('fields', {}).items():
            if field in data:
                value = data[field]
                if 'min' in rules and value < rules['min']:
                    warnings.append(f"{field}值过小: {value}")
                if 'max' in rules and value > rules['max']:
                    warnings.append(f"{field}值过大: {value}")
    
    return ValidationResult(len(errors) == 0, errors, warnings)
''',
        'use_case': '所有处理外部数据的脚本'
    }
}


def list_snippets():
    """列出所有片段"""
    print("=== 可用代码片段 ===\n")
    for key, snippet in SNIPPETS.items():
        print(f"[{key}]")
        print(f"  名称: {snippet['name']}")
        print(f"  用途: {snippet['description']}")
        print()


def get_snippet(name: str, verbose: bool = False):
    """获取片段代码"""
    if name not in SNIPPETS:
        print(f"错误: 片段'{name}'不存在")
        print("可用片段:", ', '.join(SNIPPETS.keys()))
        return
    
    snippet = SNIPPETS[name]
    print(f"\n=== {snippet['name']} ===")
    print(f"描述: {snippet['description']}")
    print(f"适用场景: {snippet['use_case']}")
    
    if verbose:
        print("\n代码:")
        print("-" * 50)
        print(snippet['code'])
        print("-" * 50)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='代码片段库')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有片段')
    parser.add_argument('--get', '-g', help='获取指定片段')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示完整代码')
    
    args = parser.parse_args()
    
    if args.list:
        list_snippets()
    elif args.get:
        get_snippet(args.get, args.verbose)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
