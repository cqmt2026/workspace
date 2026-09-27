#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RPA 反爬绕过模块
绕过 User-Agent 检测、IP 封禁、指纹检测等反爬措施

作者：房地产自媒体团队
版本：V1.0
创建时间：2026-03-15
"""

import random
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# 导入日志系统
import sys
sys.path.append(str(Path(__file__).parent))
from logger import logger


class AntiDetection:
    """反爬绕过器"""
    
    def __init__(self):
        # User-Agent 池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # 代理池（示例）
        self.proxies = [
            # 'http://user:pass@ip1:port',
            # 'http://user:pass@ip2:port',
        ]
        
        # 反爬配置
        self.config = {
            'random_delay': True,      # 随机延迟
            'delay_range': (2, 5),     # 延迟范围（秒）
            'rotate_ua': True,         # 轮换 UA
            'use_proxy': False,        # 使用代理
            'stealth_mode': True,      # 隐身模式
        }
        
        logger.info("反爬绕过器初始化完成")
    
    def get_random_user_agent(self) -> str:
        """
        获取随机 User-Agent
        
        返回:
            str: User-Agent 字符串
        """
        return random.choice(self.user_agents)
    
    def get_random_proxy(self) -> Optional[str]:
        """
        获取随机代理
        
        返回:
            str: 代理地址，无代理返回 None
        """
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def get_browser_args(self) -> List[str]:
        """
        获取反爬浏览器参数
        
        返回:
            list: 浏览器启动参数
        """
        args = [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080',
            f'--user-agent={self.get_random_user_agent()}',
        ]
        
        # 添加代理
        if self.config['use_proxy']:
            proxy = self.get_random_proxy()
            if proxy:
                args.append(f'--proxy-server={proxy}')
        
        return args
    
    def add_stealth_scripts(self, page) -> None:
        """
        添加隐身脚本
        
        参数:
            page: Playwright page 对象
        """
        stealth_scripts = [
            # 隐藏 webdriver 属性
            """() => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            }""",
            
            # 修改 plugins
            """() => {
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            }""",
            
            # 修改 languages
            """() => {
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh'],
                });
            }""",
        ]
        
        for script in stealth_scripts:
            page.evaluate(script)
        
        logger.debug("隐身脚本已注入")
    
    def random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """
        随机延迟
        
        参数:
            min_seconds (float): 最小延迟（秒）
            max_seconds (float): 最大延迟（秒）
        """
        if not self.config['random_delay']:
            return
        
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"随机延迟 {delay:.2f}秒")
        time.sleep(delay)
    
    def get_anti_detection_config(self) -> Dict:
        """
        获取反爬配置
        
        返回:
            dict: 反爬配置
        """
        return {
            'user_agent': self.get_random_user_agent() if self.config['rotate_ua'] else self.user_agents[0],
            'proxy': self.get_random_proxy() if self.config['use_proxy'] else None,
            'browser_args': self.get_browser_args(),
            'stealth_mode': self.config['stealth_mode'],
            'random_delay': self.config['random_delay'],
        }
    
    def test_anti_detection(self) -> Dict[str, Any]:
        """
        测试反爬配置
        
        返回:
            dict: 测试结果
        """
        from playwright.sync_api import sync_playwright
        
        logger.info("开始测试反爬配置...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=self.get_browser_args()
                )
                
                page = browser.new_page()
                
                # 注入隐身脚本
                if self.config['stealth_mode']:
                    self.add_stealth_scripts(page)
                
                # 访问测试页面
                page.goto('https://httpbin.org/headers')
                
                # 获取请求头
                headers = page.text_content()
                
                # 截图
                page.screenshot(path='screenshots/anti_detection_test.png')
                
                browser.close()
                
                logger.success("反爬测试完成")
                
                return {
                    'status': 'success',
                    'headers': headers,
                    'screenshot': 'screenshots/anti_detection_test.png'
                }
                
        except Exception as e:
            logger.error(f"反爬测试失败：{e}")
            return {
                'status': 'error',
                'error': str(e)
            }


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("RPA 反爬绕过模块")
    logger.info("=" * 60)
    
    anti_detection = AntiDetection()
    
    # 获取配置
    config = anti_detection.get_anti_detection_config()
    
    print("\n" + "=" * 60)
    print("反爬配置")
    print("=" * 60)
    print(f"User-Agent: {config['user_agent'][:50]}...")
    print(f"代理：{config['proxy'] or '未使用'}")
    print(f"隐身模式：{config['stealth_mode']}")
    print(f"随机延迟：{config['random_delay']}")
    print("=" * 60)
    
    # 测试反爬
    print("\n是否测试反爬配置？(y/n): ", end='')
    choice = input().strip().lower()
    
    if choice == 'y':
        result = anti_detection.test_anti_detection()
        
        if result['status'] == 'success':
            print("\n✅ 反爬测试成功！")
            print(f"截图已保存：{result['screenshot']}")
        else:
            print(f"\n❌ 反爬测试失败：{result['error']}")
    
    logger.success("反爬绕过模块执行完成")


if __name__ == '__main__':
    main()
