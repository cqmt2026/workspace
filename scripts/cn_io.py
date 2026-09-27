# -*- coding: utf-8 -*-
"""
中文路径读写工具
解决 Windows 中文路径编码问题

用法:
    from scripts.cn_io import read_file, write_file, list_files
    
    # 读取中文路径文件
    content = read_file(r'C:\中文路径\文件.md')
    
    # 写入文件
    result = write_file(r'C:\中文路径\文件.md', content)
    
    # 列出目录文件（正确处理中文）
    files = list_files(r'C:\中文路径\目录')
"""
import os
import sys
from pathlib import Path
import io

def read_file(file_path):
    """
    读取中文路径文件
    
    Args:
        file_path: 文件路径（支持中文）
    
    Returns:
        文件内容字符串
    """
    # 使用 pathlib 处理中文路径
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def write_file(file_path, content):
    """
    写入中文路径文件
    
    Args:
        file_path: 文件路径（支持中文）
        content: 文件内容
    
    Returns:
        dict: {'success': True, 'path': 路径，'size': 大小}
    """
    # 使用 pathlib 处理中文路径
    path = Path(file_path)
    
    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 验证写入
    size = path.stat().st_size
    
    return {
        'success': True,
        'path': str(path),
        'size': size,
        'preview': content[:50] + '...' if len(content) > 50 else content
    }

def list_files(dir_path, pattern='*.md'):
    """
    列出目录文件（正确处理中文）
    
    Args:
        dir_path: 目录路径（支持中文）
        pattern: 文件匹配模式
    
    Returns:
        list: 文件名列表
    """
    # 使用 pathlib 处理中文路径
    path = Path(dir_path)
    
    if not path.exists():
        raise FileNotFoundError(f"目录不存在：{dir_path}")
    
    files = []
    for f in path.glob(pattern):
        # 返回原始 Unicode 文件名
        files.append(f.name)
    
    return sorted(files)

def get_real_filename(file_path):
    """
    获取中文路径的真实文件名（避免编码问题）
    
    Args:
        file_path: 文件路径
    
    Returns:
        真实文件名（Unicode 原始）
    """
    path = Path(file_path)
    return path.name

if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    # 测试
    print("cn_io.py 中文路径工具已加载")
    print(f"Python 版本：{sys.version}")
    print(f"文件系统编码：{sys.getfilesystemencoding()}")
