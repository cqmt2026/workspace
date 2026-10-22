#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setup_monitoring.py - 监控告警配置工具

功能：
1. 配置微信推送
2. 设置告警规则
3. 测试告警功能

用法：
    python setup_monitoring.py --setup      # 配置告警
    python setup_monitoring.py --test       # 测试告警
    python setup_monitoring.py --status     # 查看状态
"""

import os
import sys
import json
import urllib.request
import argparse
from datetime import datetime

BASE = r"C:\Users\Administrator\.openclaw"
CONFIG_PATH = os.path.join(BASE, "monitoring_config.json")
ENV_PATH = os.path.join(BASE, ".env")

# 告警规则
ALERT_RULES = {
    'gateway_down': {
        'enabled': True,
        'threshold': 3,  # 连续3次失败
        'message': 'Gateway服务不可用，请立即检查！'
    },
    'disk_space_low': {
        'enabled': True,
        'threshold': 90,  # 使用率超过90%
        'message': '磁盘空间不足，请及时清理！'
    },
    'cron_failure': {
        'enabled': True,
        'threshold': 5,  # 连续5次失败
        'message': '自动化任务连续失败，请检查配置！'
    },
    'memory_high': {
        'enabled': True,
        'threshold': 85,  # 内存使用超过85%
        'message': '内存使用率过高，可能影响系统性能！'
    }
}

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'wechat_webhook': '', 'alert_rules': ALERT_RULES}

def save_config(config):
    """保存配置"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def send_wechat(message):
    """发送微信消息"""
    config = load_config()
    webhook = config.get('wechat_webhook', '')
    
    if not webhook:
        print("错误: 未配置微信Webhook")
        return False
    
    try:
        data = json.dumps({
            'msgtype': 'text',
            'text': {
                'content': message
            }
        }).encode('utf-8')
        
        req = urllib.request.Request(
            webhook,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get('errcode') == 0:
            print("微信推送成功")
            return True
        else:
            print("微信推送失败:", result.get('errmsg'))
            return False
            
    except Exception as e:
        print("微信推送错误:", str(e)[:100])
        return False

def check_alerts():
    """检查告警条件"""
    import shutil
    import psutil
    
    config = load_config()
    alerts = []
    
    # 检查磁盘空间
    for drive in ['C:', 'F:']:
        if os.path.exists(drive + '\\'):
            usage = shutil.disk_usage(drive)
            used_pct = usage.used / usage.total * 100 if usage.total > 0 else 0
            if used_pct > ALERT_RULES['disk_space_low']['threshold']:
                alerts.append(f"{drive}盘空间不足: {used_pct:.1f}%")
    
    # 检查内存使用
    mem = psutil.virtual_memory()
    if mem.percent > ALERT_RULES['memory_high']['threshold']:
        alerts.append(f"内存使用率过高: {mem.percent}%")
    
    # 检查Cron失败（简化版）
    # 实际应从cron_failure_state.json读取
    
    return alerts

def setup():
    """配置告警"""
    print("=== 监控告警配置 ===")
    print()
    
    config = load_config()
    
    # 检查.env中的WECHAT_WEBHOOK
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            env_content = f.read()
        if 'WECHAT_WEBHOOK' in env_content:
            # 提取webhook URL
            for line in env_content.split('\n'):
                if line.startswith('WECHAT_WEBHOOK='):
                    config['wechat_webhook'] = line.split('=', 1)[1].strip()
                    break
    
    if config.get('wechat_webhook'):
        print("微信Webhook: 已配置")
    else:
        print("微信Webhook: 未配置")
        print("请在.env中添加: WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
    
    print()
    print("告警规则:")
    for name, rule in ALERT_RULES.items():
        status = "启用" if rule['enabled'] else "禁用"
        print(f"  {name}: {status}")
    
    print()
    print("配置已保存到:", CONFIG_PATH)
    save_config(config)

def test():
    """测试告警"""
    print("=== 测试告警 ===")
    print()
    
    config = load_config()
    webhook = config.get('wechat_webhook', '')
    
    if not webhook:
        print("错误: 未配置微信Webhook，请先运行 --setup")
        return
    
    message = f"[系统测试] 监控告警功能测试\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n状态: 正常"
    
    print("发送测试消息...")
    success = send_wechat(message)
    
    if success:
        print("告警功能正常")
    else:
        print("告警功能异常，请检查配置")

def status():
    """查看状态"""
    print("=== 监控告警状态 ===")
    print()
    
    config = load_config()
    webhook = config.get('wechat_webhook', '')
    
    print("微信Webhook:", "已配置" if webhook else "未配置")
    print()
    
    print("告警规则:")
    for name, rule in ALERT_RULES.items():
        status = "启用" if rule['enabled'] else "禁用"
        print(f"  {name}: {status} (阈值: {rule.get('threshold', 'N/A')})")
    
    print()
    
    # 检查当前告警
    alerts = check_alerts()
    if alerts:
        print("当前告警:")
        for alert in alerts:
            print(f"  [!] {alert}")
    else:
        print("当前状态: 正常")

def main():
    parser = argparse.ArgumentParser(description='监控告警配置工具')
    parser.add_argument('--setup', action='store_true', help='配置告警')
    parser.add_argument('--test', action='store_true', help='测试告警')
    parser.add_argument('--status', action='store_true', help='查看状态')
    args = parser.parse_args()
    
    if args.setup:
        setup()
    elif args.test:
        test()
    elif args.status:
        status()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
