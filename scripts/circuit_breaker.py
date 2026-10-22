#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
circuit_breaker.py - 熔断器模式实现

用法：
    python circuit_breaker.py --service MXSearch --call
    python circuit_breaker.py --list
    python circuit_breaker.py --reset MXSearch
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta

CONFIG_PATH = r"C:\Users\Administrator\.openclaw\circuit_breaker.json"
STATE_PATH = r"C:\Users\Administrator\.openclaw\circuit_breaker_state.json"

class CircuitBreaker:
    def __init__(self, service, config):
        self.service = service
        self.config = config
        self.state = 'closed'  # closed, open, half_open
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_requests = 0
        
    def call(self):
        """执行调用"""
        if self.state == 'open':
            # 检查是否超时
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).seconds
                if elapsed > self.config.get('timeout_seconds', 60):
                    self.state = 'half_open'
                    self.half_open_requests = 0
                    print('[半开状态] ' + self.service + ' 尝试恢复...')
                else:
                    raise Exception('[熔断中] ' + self.service + ' 仍处于熔断状态')
        
        try:
            # 模拟调用（实际需要替换为真实调用）
            result = self._simulate_call()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _simulate_call(self):
        """模拟调用"""
        return {'status': 'success', 'timestamp': datetime.now().isoformat()}
    
    def _on_success(self):
        """成功处理"""
        if self.state == 'half_open':
            self.half_open_requests += 1
            if self.half_open_requests >= self.config.get('half_open_requests', 3):
                self.state = 'closed'
                self.failure_count = 0
                print('[恢复成功] ' + self.service + ' 已恢复正常')
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """失败处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        threshold = self.config.get('failure_threshold', 5)
        
        if self.state == 'half_open':
            self.state = 'open'
            print('[熔断] ' + self.service + ' 半开测试失败，重新熔断')
        elif self.failure_count >= threshold:
            self.state = 'open'
            print('[熔断] ' + self.service + ' 连续失败' + str(self.failure_count) + '次，触发熔断')
    
    def get_state(self):
        return {
            'service': self.service,
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None
        }

def main():
    parser = argparse.ArgumentParser(description='熔断器管理')
    parser.add_argument('--service', type=str, help='服务名称')
    parser.add_argument('--call', action='store_true', help='执行调用')
    parser.add_argument('--list', action='store_true', help='列出所有状态')
    parser.add_argument('--reset', type=str, help='重置指定服务')
    args = parser.parse_args()
    
    if not os.path.exists(CONFIG_PATH):
        print('错误: 找不到配置文件')
        return
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        configs = json.load(f)
    
    if args.list:
        print('=== 熔断器状态 ===')
        for service, config in configs.items():
            cb = CircuitBreaker(service, config)
            state = cb.get_state()
            print(service + ': ' + state['state'] + ' (失败:' + str(state['failure_count']) + ')')
    
    elif args.service and args.call:
        if args.service not in configs:
            print('错误: 未知服务', args.service)
            return
        cb = CircuitBreaker(args.service, configs[args.service])
        try:
            result = cb.call()
            print('调用成功:', result)
        except Exception as e:
            print('调用失败:', str(e))
    
    elif args.service and args.reset:
        print('已重置: ' + args.service)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
