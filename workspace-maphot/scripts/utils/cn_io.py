# -*- coding: utf-8 -*-
"""
地图热点子系统 - 中文路径读写工具
用于处理 Windows 中文路径的文件读写操作
用法：python cn_io.py <操作类型> <文件路径> [内容]
操作类型：read | write
"""

import os
import sys


def read_file(file_path):
    """读取文件内容（支持中文路径）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取失败: {e}")
        return None


def write_file(file_path, content):
    """写入文件内容（支持中文路径）"""
    try:
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python cn_io.py <read|write> <文件路径> [内容]")
        sys.exit(1)

    action = sys.argv[1]
    file_path = sys.argv[2]

    if action == 'read':
        content = read_file(file_path)
        if content:
            print(content)
    elif action == 'write':
        content = sys.argv[3] if len(sys.argv) > 3 else ''
        result = write_file(file_path, content)
        print("写入成功" if result else "写入失败")
    else:
        print(f"未知操作: {action}")
