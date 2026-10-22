#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gateway_ha.py - Gateway高可用管理工具

功能：
1. 监控主Gateway状态
2. 自动故障切换
3. 健康检查
4. 状态报告

用法：
    python gateway_ha.py status          # 查看状态
    python gateway_ha.py check           # 执行健康检查
    python gateway_ha.py switch          # 手动切换
    python gateway_ha.py --daemon        # 守护进程模式
"""

import os
import sys
import json
import time
import socket
import urllib.request
import argparse
from datetime import datetime

# 配置
CONFIG_PATH = r"C:\Users\Administrator\.openclaw\gateway_ha.json"
STATE_PATH = r"C:\Users\Administrator\.openclaw\gateway_state.json"
LOG_PATH = r"C:\Users\Administrator\.openclaw\workspace\logs\gateway_ha.log"

# Gateway配置
GATEWAY_CONFIG = {
    'primary': {
        'host': '127.0.0.1',
        'port': 18789,
        'health_path': '/health',
        'timeout': 5
    },
    'standby': {
        'host': '127.0.0.1',
        'port': 18790,
        'health_path': '/health',
        'timeout': 5
    },
    'check_interval': 30,  # 检查间隔（秒）
    'fail_threshold': 3,   # 连续失败次数触发切换
    'notification': {
        'wechat': False,     # 暂不启用微信推送
        'log': True
    }
}

def log(message):
    """写入日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def check_gateway(host, port, timeout=5):
    """检查Gateway健康状态"""
    try:
        url = f"http://{host}:{port}/health"
        req = urllib.request.Request(url, headers={'User-Agent': 'GatewayHA/1.0'})
        resp = urllib.request.urlopen(req, timeout=timeout)
        if resp.status == 200:
            return {'status': 'healthy', 'code': resp.status}
        else:
            return {'status': 'unhealthy', 'code': resp.status}
    except Exception as e:
        return {'status': 'error', 'error': str(e)[:100]}

def load_state():
    """加载状态"""
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'active_gateway': 'primary',
        'consecutive_failures': 0,
        'last_check': None,
        'last_switch': None,
        'switch_count': 0
    }

def save_state(state):
    """保存状态"""
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_status():
    """获取当前状态"""
    state = load_state()
    active = state.get('active_gateway', 'primary')
    
    # 检查两个Gateway
    primary_status = check_gateway(
        GATEWAY_CONFIG['primary']['host'],
        GATEWAY_CONFIG['primary']['port'],
        GATEWAY_CONFIG['primary']['timeout']
    )
    standby_status = check_gateway(
        GATEWAY_CONFIG['standby']['host'],
        GATEWAY_CONFIG['standby']['port'],
        GATEWAY_CONFIG['standby']['timeout']
    )
    
    return {
        'timestamp': datetime.now().isoformat(),
        'active_gateway': active,
        'primary': {
            'address': f"{GATEWAY_CONFIG['primary']['host']}:{GATEWAY_CONFIG['primary']['port']}",
            'status': primary_status['status']
        },
        'standby': {
            'address': f"{GATEWAY_CONFIG['standby']['host']}:{GATEWAY_CONFIG['standby']['port']}",
            'status': standby_status['status']
        },
        'state': state
    }

def do_check():
    """执行健康检查"""
    state = load_state()
    active = state.get('active_gateway', 'primary')
    
    # 检查当前活跃Gateway
    config = GATEWAY_CONFIG[active]
    result = check_gateway(config['host'], config['port'], config['timeout'])
    
    if result['status'] == 'healthy':
        state['consecutive_failures'] = 0
        log(f"{active} Gateway健康")
    else:
        state['consecutive_failures'] += 1
        log(f"{active} Gateway失败: {result.get('error', 'unknown')}")
        
        # 检查是否达到切换阈值
        if state['consecutive_failures'] >= GATEWAY_CONFIG['fail_threshold']:
            log(f"连续失败{state['consecutive_failures']}次，准备切换...")
            do_switch(active)
    
    state['last_check'] = datetime.now().isoformat()
    save_state(state)
    return result

def do_switch(from_gateway):
    """执行切换"""
    state = load_state()
    
    # 确定新的活跃Gateway
    new_active = 'standby' if from_gateway == 'primary' else 'primary'
    
    log(f"切换到 {new_active} Gateway")
    
    # 检查新Gateway健康
    config = GATEWAY_CONFIG[new_active]
    result = check_gateway(config['host'], config['port'], config['timeout'])
    
    if result['status'] == 'healthy':
        state['active_gateway'] = new_active
        state['last_switch'] = datetime.now().isoformat()
        state['switch_count'] = state.get('switch_count', 0) + 1
        state['consecutive_failures'] = 0
        save_state(state)
        log(f"切换成功，当前活跃: {new_active}")
        return True
    else:
        log(f"切换失败: {result.get('error', 'unknown')}")
        return False

def run_daemon():
    """守护进程模式"""
    log("启动Gateway高可用守护进程")
    
    while True:
        try:
            do_check()
            time.sleep(GATEWAY_CONFIG['check_interval'])
        except KeyboardInterrupt:
            log("收到中断信号，退出")
            break
        except Exception as e:
            log(f"守护进程错误: {e}")
            time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description='Gateway高可用管理')
    parser.add_argument('command', choices=['status', 'check', 'switch', 'daemon'], 
                       nargs='?', help='命令')
    parser.add_argument('--from', dest='from_gateway', choices=['primary', 'standby'],
                       help='从哪个Gateway切换')
    args = parser.parse_args()
    
    command = args.command or 'status'
    
    if command == 'status':
        status = get_status()
        print("="*60)
        print("Gateway高可用状态")
        print("="*60)
        print()
        print(f"当前活跃: {status['active_gateway']}")
        print()
        print("Primary Gateway:")
        print(f"  地址: {status['primary']['address']}")
        print(f"  状态: {status['primary']['status']}")
        print()
        print("Standby Gateway:")
        print(f"  地址: {status['standby']['address']}")
        print(f"  状态: {status['standby']['status']}")
        print()
        print(f"连续失败: {status['state'].get('consecutive_failures', 0)}")
        print(f"切换次数: {status['state'].get('switch_count', 0)}")
        
    elif command == 'check':
        result = do_check()
        print("健康检查:", result['status'])
        if result['status'] != 'healthy':
            print("错误:", result.get('error', 'unknown'))
            
    elif command == 'switch':
        from_gw = args.from_gateway or 'primary'
        if do_switch(from_gw):
            print("切换成功")
        else:
            print("切换失败")
            
    elif command == 'daemon':
        run_daemon()

if __name__ == '__main__':
    main()
