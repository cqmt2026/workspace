#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
定时任务模板 - 通用调度器

用法：
    python scheduler.py --interval 300 --daemon
    python scheduler.py --once
    python scheduler.py --status
"""

import os
import sys
import time
import argparse
import logging
import signal
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Logger:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs", log_file: str = "scheduler.log"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_file
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            self.log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


class Task:
    """任务类"""
    
    def __init__(self, name: str, func: Callable, interval: int = 300,
                 max_retries: int = 3, on_success: Optional[Callable] = None,
                 on_failure: Optional[Callable] = None):
        """初始化任务
        
        Args:
            name: 任务名称
            func: 任务函数
            interval: 执行间隔（秒）
            max_retries: 最大重试次数
            on_success: 成功回调
            on_failure: 失败回调
        """
        self.name = name
        self.func = func
        self.interval = interval
        self.max_retries = max_retries
        self.on_success = on_success
        self.on_failure = on_failure
        
        # 状态
        self.status = TaskStatus.PENDING
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[Any] = None
        self.run_count = 0
        self.failure_count = 0
    
    def execute(self) -> bool:
        """执行任务
        
        Returns:
            bool: 是否成功
        """
        self.status = TaskStatus.RUNNING
        self.last_run = datetime.now()
        
        try:
            result = self.func()
            self.last_result = result
            self.status = TaskStatus.COMPLETED
            self.run_count += 1
            self.failure_count = 0
            
            if self.on_success:
                self.on_success(result)
            
            return True
            
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.failure_count += 1
            self.last_result = str(e)
            
            if self.on_failure:
                self.on_failure(e)
            
            return False
    
    def should_run(self) -> bool:
        """判断是否应该执行
        
        Returns:
            bool: 是否应该执行
        """
        if self.last_run is None:
            return True
        
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval
    
    def get_status(self) -> Dict:
        """获取任务状态
        
        Returns:
            dict: 状态信息
        """
        return {
            'name': self.name,
            'status': self.status.value,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_result': str(self.last_result) if self.last_result else None,
            'run_count': self.run_count,
            'failure_count': self.failure_count,
            'interval': self.interval,
        }


class Scheduler:
    """调度器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化调度器
        
        Args:
            config_path: 配置文件路径
        """
        self.tasks: List[Task] = []
        self.config_path = Path(config_path) if config_path else None
        self.running = False
        self.logger = Logger()
        
        # 加载配置
        if self.config_path and self.config_path.exists():
            self._load_config()
    
    def _load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载任务配置
            for task_config in config.get('tasks', []):
                self.add_task(
                    name=task_config['name'],
                    func=task_config['func'],
                    interval=task_config.get('interval', 300),
                    max_retries=task_config.get('max_retries', 3)
                )
            
            self.logger.info(f"加载配置完成，共{len(self.tasks)}个任务")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
    
    def add_task(self, name: str, func: Callable, interval: int = 300,
                 max_retries: int = 3, on_success: Optional[Callable] = None,
                 on_failure: Optional[Callable] = None) -> Task:
        """添加任务
        
        Args:
            name: 任务名称
            func: 任务函数
            interval: 执行间隔（秒）
            max_retries: 最大重试次数
            on_success: 成功回调
            on_failure: 失败回调
            
        Returns:
            Task: 创建的任务对象
        """
        task = Task(
            name=name,
            func=func,
            interval=interval,
            max_retries=max_retries,
            on_success=on_success,
            on_failure=on_failure
        )
        self.tasks.append(task)
        self.logger.info(f"添加任务: {name} (间隔{interval}秒)")
        return task
    
    def remove_task(self, name: str) -> bool:
        """移除任务
        
        Args:
            name: 任务名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, task in enumerate(self.tasks):
            if task.name == name:
                self.tasks.pop(i)
                self.logger.info(f"移除任务: {name}")
                return True
        return False
    
    def run_once(self) -> Dict[str, bool]:
        """执行一次所有任务
        
        Returns:
            dict: 各任务的执行结果
        """
        results = {}
        
        for task in self.tasks:
            self.logger.info(f"执行任务: {task.name}")
            success = task.execute()
            results[task.name] = success
            
            if success:
                self.logger.info(f"任务完成: {task.name}")
            else:
                self.logger.error(f"任务失败: {task.name} - {task.last_result}")
        
        return results
    
    def run_daemon(self, max_iterations: int = 0):
        """以守护进程方式运行
        
        Args:
            max_iterations: 最大迭代次数（0表示无限）
        """
        self.running = True
        self.logger.info(f"启动调度器守护进程，共{len(self.tasks)}个任务")
        
        iteration = 0
        signal_received = False
        
        def signal_handler(signum, frame):
            nonlocal signal_received
            signal_received = True
            self.logger.info("收到中断信号，准备退出...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self.running:
            try:
                # 执行所有到期的任务
                for task in self.tasks:
                    if task.should_run():
                        self.logger.info(f"执行到期任务: {task.name}")
                        success = task.execute()
                        
                        if success:
                            self.logger.info(f"任务完成: {task.name}")
                        else:
                            self.logger.error(
                                f"任务失败: {task.name} - {task.last_result}"
                            )
                
                iteration += 1
                
                # 检查是否达到最大迭代次数
                if max_iterations > 0 and iteration >= max_iterations:
                    self.logger.info(f"达到最大迭代次数{max_iterations}，退出")
                    break
                
                # 等待下一个检查周期
                self.logger.debug(f"等待60秒后再次检查...")
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"调度器运行错误: {e}")
                time.sleep(60)
        
        self.logger.info("调度器已停止")
    
    def get_status(self) -> Dict:
        """获取调度器状态
        
        Returns:
            dict: 状态信息
        """
        return {
            'running': self.running,
            'task_count': len(self.tasks),
            'tasks': [task.get_status() for task in self.tasks]
        }
    
    def save_config(self, config_path: Optional[str] = None):
        """保存配置
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path) if config_path else self.config_path
        if not path:
            self.logger.error("未指定配置文件路径")
            return
        
        config = {
            'tasks': []
        }
        
        for task in self.tasks:
            # 注意：这里不能序列化函数，只保存配置
            config['tasks'].append({
                'name': task.name,
                'interval': task.interval,
                'max_retries': task.max_retries,
            })
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"配置已保存到: {path}")


def example_task():
    """示例任务"""
    print("执行示例任务...")
    # 模拟任务逻辑
    return {"status": "success", "data": [1, 2, 3]}


def main():
    parser = argparse.ArgumentParser(
        description="定时任务调度器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scheduler.py --daemon --interval 300
  python scheduler.py --once
  python scheduler.py --status
  python scheduler.py --add "任务名" --interval 60
        """
    )
    
    parser.add_argument('--daemon', '-d', action='store_true',
                        help='以守护进程方式运行')
    parser.add_argument('--once', '-o', action='store_true',
                        help='只执行一次')
    parser.add_argument('--status', '-s', action='store_true',
                        help='显示状态')
    parser.add_argument('--interval', '-i', type=int, default=300,
                        help='执行间隔（秒，默认300）')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--add', nargs=2, metavar=('NAME', 'INTERVAL'),
                        help='添加任务（名称 间隔）')
    parser.add_argument('--max-iterations', type=int, default=0,
                        help='最大迭代次数（0表示无限）')
    
    args = parser.parse_args()
    
    # 创建调度器
    scheduler = Scheduler(args.config)
    
    # 添加示例任务（如果没有配置文件）
    if not args.config and not args.add:
        scheduler.add_task(
            name="example_task",
            func=example_task,
            interval=args.interval
        )
    
    # 处理命令行参数
    if args.status:
        status = scheduler.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    elif args.add:
        name, interval = args.add
        scheduler.add_task(name=name, func=example_task, interval=int(interval))
        if args.config:
            scheduler.save_config(args.config)
        print(f"任务已添加: {name}")
    
    elif args.daemon:
        scheduler.run_daemon(args.max_iterations)
    
    elif args.once:
        results = scheduler.run_once()
        for name, success in results.items():
            status = "成功" if success else "失败"
            print(f"{name}: {status}")
    
    else:
        # 默认守护进程模式
        scheduler.run_daemon(args.max_iterations)


if __name__ == '__main__':
    main()
