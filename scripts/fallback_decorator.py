# -*- coding: utf-8 -*-
"""
工具Fallback机制
当主工具失败时自动切换到备用方案
"""

import os
import sys
import importlib
from functools import wraps

def fallback(fallback_funcs=None):
    """Fallback装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试主函数
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e1:
                print(f"[主工具失败] {func.__name__}: {e1}")
                
                # 尝试fallback
                if fallback_funcs:
                    for i, fallback_func in enumerate(fallback_funcs):
                        try:
                            print(f"[尝试Fallback {i+1}] {fallback_func.__name__}")
                            result = fallback_func(*args, **kwargs)
                            print(f"[OK] Fallback成功: {fallback_func.__name__}")
                            return result
                        except Exception as e2:
                            print(f"[FAIL] Fallback {i+1} 失败: {e2}")
                
                # 所有尝试都失败
                raise RuntimeError(f"所有工具都失败: {e1}")
        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    def main_tool():
        # 模拟主工具失败
        raise FileNotFoundError("主工具路径不存在")
    
    def fallback_tool_1():
        # 备用方案1
        return "fallback_1_result"
    
    def fallback_tool_2():
        # 备用方案2
        return "fallback_2_result"
    
    @fallback([fallback_tool_1, fallback_tool_2])
    def my_function():
        return main_tool()
    
    try:
        result = my_function()
        print(f"结果: {result}")
    except Exception as e:
        print(f"最终失败: {e}")
