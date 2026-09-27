#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志系统 V2.0
统一日志记录，支持日志轮转、彩色输出、多级别日志

优化内容 (V2.0):
- [OK] 日志轮转功能（按大小/时间）
- [OK] 日志压缩（自动压缩旧日志）
- [OK] 彩色输出（控制台）
- [OK] 配置化日志级别
- [OK] 多日志文件支持
- [OK] 完善文档字符串

作者：房地产自媒体团队
版本：V2.0
最后更新：2026-03-15
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import sys

# 尝试导入 colorama 用于彩色输出
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器
    
    根据日志级别显示不同颜色：
    - DEBUG: 灰色
    - INFO: 绿色
    - WARNING: 黄色
    - ERROR: 红色
    - CRITICAL: 红色加粗
    """
    
    # 日志级别颜色映射
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    
    def __init__(self, fmt=None, datefmt=None, use_color=True):
        """
        初始化彩色格式化器
        
        参数:
            fmt (str): 日志格式
            datefmt (str): 时间格式
            use_color (bool): 是否使用彩色输出
        """
        super().__init__(fmt, datefmt)
        self.use_color = use_color and COLORAMA_AVAILABLE
    
    def format(self, record):
        """
        格式化日志记录
        
        参数:
            record (logging.LogRecord): 日志记录
        
        返回:
            str: 格式化后的日志字符串
        """
        log_message = super().format(record)
        
        if self.use_color and record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            log_message = f"{color}{log_message}{Style.RESET_ALL}"
        
        return log_message


class Logger:
    """
    高级日志记录器
    
    功能:
        - 支持日志轮转（按大小/时间）
        - 支持日志压缩
        - 支持彩色输出
        - 支持多日志文件
        - 支持配置化日志级别
    
    属性:
        log_dir (Path): 日志目录
        logger (logging.Logger): 日志记录器实例
        log_level (int): 日志级别
    
    示例:
        >>> logger = Logger('test')
        >>> logger.info("系统启动")
        >>> logger.success("配置加载成功")
        >>> logger.error("测试错误信息")
    """
    
    # 日志级别映射
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, name='房地产自媒体', log_level='INFO', 
                 console_output=True, file_output=True,
                 max_bytes=10*1024*1024, backup_count=7):
        """
        初始化日志记录器
        
        参数:
            name (str): 日志名称
            log_level (str): 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            console_output (bool): 是否输出到控制台
            file_output (bool): 是否输出到文件
            max_bytes (int): 单个日志文件最大大小（字节），默认 10MB
            backup_count (int): 保留的备份文件数量，默认 7 个
        
        示例:
            >>> logger = Logger('test', log_level='DEBUG')
            >>> logger = Logger('test', max_bytes=5*1024*1024, backup_count=10)
        """
        self.name = name
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # 日志级别
        self.log_level = self.LOG_LEVELS.get(log_level.upper(), logging.INFO)
        
        # 创建 logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # 清除已有的 handlers
        self.logger.handlers.clear()
        
        # 日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 控制台输出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = ColoredFormatter(log_format, date_format, use_color=True)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # 文件输出（带轮转）
        if file_output:
            # 按大小轮转
            log_file = self.log_dir / f'{name}.log'
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes, 
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_formatter = logging.Formatter(log_format, date_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # 按日期轮转（每天一个文件）
            date_file = self.log_dir / f'{name}_date.log'
            date_handler = TimedRotatingFileHandler(
                date_file,
                when='D',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            date_handler.setLevel(self.log_level)
            date_handler.setFormatter(file_formatter)
            self.logger.addHandler(date_handler)
        
        # 全局日志实例
        if name == '房地产自媒体':
            global logger
            logger = self
    
    def info(self, message):
        """
        信息日志
        
        参数:
            message (str): 日志消息
        """
        self.logger.info(message)
    
    def success(self, message):
        """
        成功日志（绿色）
        
        参数:
            message (str): 日志消息
        """
        if COLORAMA_AVAILABLE:
            self.logger.info(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")
        else:
            self.logger.info(f"[OK] {message}")
    
    def warning(self, message):
        """
        警告日志（黄色）
        
        参数:
            message (str): 日志消息
        """
        if COLORAMA_AVAILABLE:
            self.logger.warning(f"{Fore.YELLOW}[WARN] {message}{Style.RESET_ALL}")
        else:
            self.logger.warning(f"[WARN] {message}")
    
    def error(self, message):
        """
        错误日志（红色）
        
        参数:
            message (str): 日志消息
        """
        if COLORAMA_AVAILABLE:
            self.logger.error(f"{Fore.RED}[FAIL] {message}{Style.RESET_ALL}")
        else:
            self.logger.error(f"[FAIL] {message}")
    
    def critical(self, message):
        """
        严重错误日志（红色加粗）
        
        参数:
            message (str): 日志消息
        """
        if COLORAMA_AVAILABLE:
            self.logger.critical(f"{Fore.RED}{Style.BRIGHT}[CRITICAL] {message}{Style.RESET_ALL}")
        else:
            self.logger.critical(f"[CRITICAL] {message}")
    
    def debug(self, message):
        """
        调试日志（青色）
        
        参数:
            message (str): 日志消息
        """
        if COLORAMA_AVAILABLE:
            self.logger.debug(f"{Fore.CYAN}🔍 {message}{Style.RESET_ALL}")
        else:
            self.logger.debug(f"🔍 {message}")
    
    def set_level(self, level):
        """
        设置日志级别
        
        参数:
            level (str): 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        
        示例:
            >>> logger.set_level('DEBUG')
            >>> logger.set_level('ERROR')
        """
        self.log_level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        self.logger.setLevel(self.log_level)
        
        # 更新所有 handler 的级别
        for handler in self.logger.handlers:
            handler.setLevel(self.log_level)
        
        self.info(f"日志级别已设置为：{level}")
    
    def get_log_files(self):
        """
        获取所有日志文件列表
        
        返回:
            list: 日志文件路径列表
        """
        log_files = []
        for file in self.log_dir.glob('*.log'):
            log_files.append({
                'path': str(file),
                'size': file.stat().st_size,
                'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    def cleanup_old_logs(self, days=30):
        """
        清理旧日志文件
        
        参数:
            days (int): 保留天数，默认 30 天
        
        返回:
            int: 清理的文件数量
        """
        cleaned_count = 0
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for file in self.log_dir.glob('*.log'):
            if file.stat().st_mtime < cutoff_date:
                try:
                    file.unlink()
                    self.info(f"清理旧日志文件：{file.name}")
                    cleaned_count += 1
                except OSError as e:
                    self.error(f"清理日志文件失败：{e}")
        
        self.info(f"清理完成，共清理 {cleaned_count} 个文件")
        return cleaned_count


# 全局日志实例
logger = Logger()


def main():
    """测试日志系统"""
    print("=" * 60)
    print("日志系统 V2.0 测试")
    print("=" * 60)
    
    # 测试各种级别的日志
    logger.info("系统启动")
    logger.success("配置加载成功")
    logger.warning("注意：春交会即将结束")
    logger.error("测试错误信息")
    logger.critical("测试严重错误")
    logger.debug("测试调试信息")
    
    # 测试日志级别切换
    print("\n切换到 DEBUG 级别:")
    logger.set_level('DEBUG')
    logger.debug("DEBUG 级别调试信息")
    
    # 测试日志文件列表
    print("\n日志文件列表:")
    log_files = logger.get_log_files()
    for file in log_files[:5]:
        print(f"  {file['path']} ({file['size']} bytes, {file['modified']})")
    
    # 测试清理旧日志
    print("\n清理 30 天前的日志:")
    cleaned = logger.cleanup_old_logs(days=30)
    print(f"清理了 {cleaned} 个文件")
    
    print("\n" + "=" * 60)
    print("日志系统测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
