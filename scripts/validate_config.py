#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_config.py - 配置验证工具

用法：
    python validate_config.py
    python validate_config.py --fix
"""
import os
import sys
import json
import datetime

BASE = r"C:\Users\Administrator\.openclaw"
CONFIG_CENTER = os.path.join(BASE, "config_center.json")

def validate():
    """验证配置完整性"""
    results = {
        'timestamp': datetime.datetime.now().isoformat(),
        'checks': {},
        'errors': [],
        'warnings': []
    }
    
    # 1. 验证核心文件
    core_files = ['openclaw.json', 'SOUL.md', 'MEMORY.md', 'AGENTS.md']
    # 实际路径可能在workspace子目录
    search_paths = [BASE, os.path.join(BASE, 'workspace')]
    for f in core_files:
        # 搜索多个可能位置
        found = False
        for search_path in search_paths:
            path = os.path.join(search_path, f)
            if os.path.exists(path):
                found = True
                break
        results['checks'][f] = 'OK' if found else 'MISSING'
        if not found:
            results['errors'].append('核心文件缺失: ' + f)
    
    # 2. 验证API密钥
    env_path = os.path.join(BASE, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
        required_keys = ['MODELSTUDIO_API_KEY']
        for key in required_keys:
            if key in env_content:
                results['checks'][key] = 'OK'
            else:
                results['checks'][key] = 'MISSING'
                results['warnings'].append('API密钥未配置: ' + key)
    else:
        results['checks']['.env'] = 'MISSING'
        results['errors'].append('.env文件不存在')
    
    # 3. 验证数据库
    db_dir = os.path.join(BASE, 'workspace', 'memory', 'supermemory_db')
    if os.path.exists(db_dir):
        dbs = [f for f in os.listdir(db_dir) if f.endswith('.db')]
        results['checks']['supermemory_db'] = 'OK (' + str(len(dbs)) + ' files)'
    else:
        results['checks']['supermemory_db'] = 'MISSING'
        results['warnings'].append('Supermemory数据库不存在')
    
    # 4. 验证Cron配置
    config_path = os.path.join(BASE, 'openclaw.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        autos = config.get('automations', {})
        results['checks']['cron_tasks'] = 'OK (' + str(len(autos)) + ' tasks)'
    else:
        results['checks']['cron_tasks'] = 'MISSING'
        results['errors'].append('openclaw.json不存在')
    
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='配置验证工具')
    parser.add_argument('--fix', action='store_true', help='自动修复问题')
    args = parser.parse_args()
    
    results = validate()
    
    # 输出结果
    print('='*50)
    print('配置验证报告')
    print('='*50)
    print()
    
    print('检查结果:')
    for check, status in results['checks'].items():
        if 'OK' in status:
            icon = 'OK'
        elif 'MISSING' in status:
            icon = 'WARN'
        else:
            icon = 'ERR'
        print('  [' + icon + '] ' + check + ': ' + status)
    
    if results['errors']:
        print()
        print('错误:')
        for e in results['errors']:
            print('  [X] ' + e)
    
    if results['warnings']:
        print()
        print('警告:')
        for w in results['warnings']:
            print('  [!] ' + w)
    
    # 保存报告
    report_dir = os.path.join(BASE, 'workspace', 'memory', '健康检查')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, 'config_validation_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print()
    print('报告已保存:', report_path)

if __name__ == '__main__':
    main()
