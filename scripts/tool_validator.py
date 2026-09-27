# -*- coding: utf-8 -*-
"""
工具调用验证层
在调用外部工具前验证依赖和路径
"""

import os
import sys
import importlib
from functools import wraps

def validate_path(path):
    """验证路径是否存在"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")
    return True

def validate_module(module_name):
    """验证模块是否可导入"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        raise ImportError(f"模块不可用: {module_name}, {e}")

def tool_validator(func):
    """工具调用验证装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 前置验证
        print(f"[验证] 调用 {func.__name__}...")
        
        # 检查常见路径
        common_paths = [
            r"F:\market_data.db",
            r"C:\Users\Administrator\.openclaw\workspace",
        ]
        
        for path in common_paths:
            try:
                validate_path(path)
                print(f"  ✅ 路径验证通过: {path}")
            except FileNotFoundError:
                print(f"  ⚠️ 路径不存在: {path}")
        
        # 检查常见模块
        common_modules = [
            "sqlite3",
            "requests",
            "json",
        ]
        
        for module in common_modules:
            try:
                validate_module(module)
                print(f"  ✅ 模块可用: {module}")
            except ImportError:
                print(f"  ❌ 模块缺失: {module}")
        
        # 执行原函数
        try:
            result = func(*args, **kwargs)
            print(f"  ✅ {func.__name__} 执行成功")
            return result
        except Exception as e:
            print(f"  ❌ {func.__name__} 执行失败: {e}")
            raise
    
    return wrapper

# 使用示例
if __name__ == "__main__":
    @tool_validator
    def test_function():
        print("  执行测试功能")
        return "success"
    
    test_function()
