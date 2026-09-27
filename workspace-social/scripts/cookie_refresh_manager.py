#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cookie 有效期检测 + 自动刷新管理器 (Plan A)

功能:
1. 解析 Cookie 提取过期时间（或试探性请求检测是否失效）
2. 每次采集前检查 Cookie 有效性
3. Cookie 即将过期（<3 天）时自动预警 + 自动触发刷新流程
4. 利用百家号/头条号的登录机制尝试自动刷新

作者：自媒体自动化团队
版本：V1.0
创建时间：2026-04-11
"""

import io
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# 配置目录
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / 'config'
LOG_DIR = SCRIPT_DIR.parent / 'data' / 'cookie_logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)


class CookieRefreshManager:
    """Cookie 有效期检测 + 自动刷新管理器"""
    
    def __init__(self):
        self.baijiahao_config_file = CONFIG_DIR / 'baijiahao_accounts.json'
        self.toutiao_config_file = CONFIG_DIR / 'toutiao_accounts.json'
        self.log_file = LOG_DIR / f'cookie_check_{datetime.now().strftime("%Y%m%d")}.log'
        
        # 过期预警阈值（天数）
        self.warning_threshold_days = 3
        # 请求超时时间
        self.request_timeout = 10
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        self.log(f"Cookie 刷新管理器 V1.0 初始化完成")
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        # 使用 UTF-8 编码输出，避免 Windows 控制台编码问题
        print(log_entry.encode('utf-8').decode('utf-8', errors='replace'))
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def load_config(self, platform: str) -> Optional[Dict]:
        """加载平台配置"""
        config_file = self.baijiahao_config_file if platform == 'baijiahao' else self.toutiao_config_file
        
        if not config_file.exists():
            self.log(f"未找到配置文件：{config_file}")
            return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config
    
    def save_config(self, platform: str, config: Dict):
        """保存平台配置"""
        config_file = self.baijiahao_config_file if platform == 'baijiahao' else self.toutiao_config_file
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.log(f"{platform} 配置文件已更新")
    
    def parse_cookie_expiry(self, cookie_str: str) -> Dict[str, datetime]:
        """
        解析 Cookie 字符串，提取过期时间信息
        
        注意：大多数 Cookie 不直接包含过期时间，需要通过试探性请求检测
        
        Returns:
            包含 Cookie 键值对和推测过期时间的字典
        """
        expiry_info = {}
        
        # 尝试从 Cookie 中提取过期时间相关的字段
        # 头条号的 sid_guard 包含时间戳信息
        for item in cookie_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 检查是否包含时间戳
                if 'guard' in key.lower() or 'expire' in key.lower():
                    # 尝试提取时间戳（例如：Sun, 07-Jun-2026 02:11:54 GMT）
                    timestamp_match = re.search(r'\|(\d+)\|', value)
                    if timestamp_match:
                        try:
                            ts = int(timestamp_match.group(1))
                            expiry = datetime.fromtimestamp(ts)
                            expiry_info[key] = expiry
                            self.log(f"从 {key} 提取到过期时间：{expiry}")
                        except:
                            pass
        
        return expiry_info
    
    def test_cookie_validity(self, platform: str, cookie: str) -> Tuple[bool, str]:
        """
        通过试探性请求测试 Cookie 是否有效
        
        Returns:
            (是否有效，状态消息)
        """
        self.session.headers.update({'Cookie': cookie})
        
        if platform == 'baijiahao':
            # 测试百家号 API
            test_url = "https://baijiahao.baidu.com/u/api/article/getlist"
            params = {'page': 1, 'page_size': 1}
            
            try:
                response = self.session.get(test_url, params=params, timeout=self.request_timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('errno') == 0:
                        return True, "Cookie 有效"
                    elif data.get('errno') == 1001 or 'login' in str(data.get('errmsg', '')).lower():
                        return False, "Cookie 已失效（需要登录）"
                    else:
                        return False, f"API 返回错误：{data.get('errmsg', 'Unknown')}"
                else:
                    return False, f"HTTP {response.status_code}"
                    
            except requests.exceptions.RequestException as e:
                return False, f"请求失败：{str(e)}"
            except json.JSONDecodeError:
                return False, "响应格式错误"
        
        elif platform == 'toutiao':
            # 测试头条号 API
            test_url = "https://mp.toutiao.com/profile_v4/index"
            
            try:
                response = self.session.get(test_url, timeout=self.request_timeout, allow_redirects=False)
                
                # 如果返回 200 且没有重定向到登录页，说明 Cookie 有效
                if response.status_code == 200:
                    return True, "Cookie 有效"
                elif response.status_code in [302, 301]:
                    location = response.headers.get('Location', '')
                    if 'login' in location.lower():
                        return False, "Cookie 已失效（重定向到登录页）"
                    return True, "Cookie 有效"
                else:
                    return False, f"HTTP {response.status_code}"
                    
            except requests.exceptions.RequestException as e:
                return False, f"请求失败：{str(e)}"
        
        return False, "未知平台"
    
    def check_all_cookies(self) -> Dict[str, Dict]:
        """
        检查所有平台的 Cookie 状态
        
        Returns:
            各平台 Cookie 状态报告
        """
        self.log("=" * 60)
        self.log("开始检查所有平台 Cookie 状态")
        self.log("=" * 60)
        
        results = {}
        
        for platform in ['baijiahao', 'toutiao']:
            self.log(f"\n检查 {platform}...")
            
            config = self.load_config(platform)
            if not config:
                results[platform] = {'status': 'error', 'message': '配置文件不存在'}
                continue
            
            accounts = config.get('accounts', [])
            if not accounts:
                results[platform] = {'status': 'error', 'message': '账号配置为空'}
                continue
            
            platform_results = []
            
            for i, account in enumerate(accounts):
                account_name = account.get('name', f'账号{i+1}')
                cookie = account['credentials'].get('cookie', '')
                
                if not cookie:
                    platform_results.append({
                        'name': account_name,
                        'status': 'error',
                        'message': 'Cookie 为空'
                    })
                    continue
                
                # 测试 Cookie 有效性
                is_valid, message = self.test_cookie_validity(platform, cookie)
                
                # 解析过期时间
                expiry_info = self.parse_cookie_expiry(cookie)
                
                # 判断是否需要刷新
                needs_refresh = False
                warning_message = None
                
                if not is_valid:
                    needs_refresh = True
                    warning_message = "Cookie 已失效，需要立即刷新"
                elif expiry_info:
                    # 检查是否有即将过期的 Cookie
                    for key, expiry in expiry_info.items():
                        days_left = (expiry - datetime.now()).days
                        if days_left < self.warning_threshold_days:
                            needs_refresh = True
                            warning_message = f"Cookie 即将过期（剩余{days_left}天）"
                            break
                
                platform_results.append({
                    'name': account_name,
                    'status': 'valid' if is_valid else 'invalid',
                    'needs_refresh': needs_refresh,
                    'message': message if not warning_message else warning_message,
                    'expiry_info': {k: v.isoformat() for k, v in expiry_info.items()}
                })
                
                self.log(f"  {account_name}: {message}")
                if warning_message:
                    self.log(f"  [WARNING] {warning_message}")
            
            results[platform] = {
                'status': 'ok',
                'accounts': platform_results,
                'needs_action': any(acc.get('needs_refresh', False) for acc in platform_results)
            }
        
        self.log("\n" + "=" * 60)
        self.log("Cookie 检查完成")
        self.log("=" * 60)
        
        return results
    
    def trigger_auto_refresh(self, platform: str):
        """
        触发自动刷新流程（调用 Plan B）
        
        注意：这需要账号密码配置，目前仅作为接口预留
        """
        self.log(f"触发 {platform} 自动刷新流程...")
        
        # 检查 Plan B 脚本是否存在
        auto_login_script = SCRIPT_DIR / 'auto_login_for_cookies.py'
        
        if not auto_login_script.exists():
            self.log("❌ 自动登录脚本不存在，无法触发刷新")
            return False
        
        # 调用 Plan B 脚本
        import subprocess
        
        try:
            result = subprocess.run(
                ['python', str(auto_login_script), '--platform', platform],
                capture_output=True,
                text=True,
                timeout=300  # 5 分钟超时
            )
            
            if result.returncode == 0:
                self.log(f"[OK] {platform} 自动刷新成功")
                return True
            else:
                self.log(f"[ERROR] {platform} 自动刷新失败：{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("[ERROR] 自动刷新超时（>5 分钟）")
            return False
        except Exception as e:
            self.log(f"[ERROR] 自动刷新异常：{str(e)}")
            return False
    
    def run_full_check(self, auto_refresh: bool = True) -> Dict:
        """
        运行完整检查流程
        
        Args:
            auto_refresh: 是否自动触发刷新
        
        Returns:
            检查报告
        """
        self.log("开始运行完整 Cookie 检查流程")
        
        # 检查所有 Cookie
        results = self.check_all_cookies()
        
        # 如果需要，自动触发刷新
        if auto_refresh:
            for platform in ['baijiahao', 'toutiao']:
                if results.get(platform, {}).get('needs_action', False):
                    self.log(f"\n{platform} 需要刷新，触发自动刷新流程...")
                    self.trigger_auto_refresh(platform)
        
        # 生成报告
        report = {
            'check_time': datetime.now().isoformat(),
            'platforms': results,
            'summary': {
                'total_platforms': len(results),
                'platforms_needing_refresh': sum(
                    1 for r in results.values() if r.get('needs_action', False)
                )
            }
        }
        
        # 保存报告
        report_file = LOG_DIR / f'cookie_check_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"\n检查报告已保存：{report_file}")
        
        return report


def main():
    """主函数 - 可被 cron 调用"""
    import sys
    
    # 命令行参数
    auto_refresh = True
    if len(sys.argv) > 1 and sys.argv[1] == '--no-refresh':
        auto_refresh = False
    
    manager = CookieRefreshManager()
    report = manager.run_full_check(auto_refresh=auto_refresh)
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("Cookie 检查摘要")
    print("=" * 60)
    print(f"检查时间：{report['check_time']}")
    print(f"检查平台数：{report['summary']['total_platforms']}")
    print(f"需要刷新：{report['summary']['platforms_needing_refresh']}")
    print("=" * 60)
    
    # 返回状态码（用于 cron 判断）
    if report['summary']['platforms_needing_refresh'] > 0:
        sys.exit(1)  # 需要人工干预
    else:
        sys.exit(0)  # 一切正常


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
