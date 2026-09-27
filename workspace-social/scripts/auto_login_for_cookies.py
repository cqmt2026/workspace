#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动登录获取新 Cookie (Plan B)

功能:
1. 使用 Playwright 启动浏览器
2. 模拟人工登录百家号/头条号
3. 登录成功后提取新 Cookie
4. 自动更新配置文件
5. 验证新 Cookie 有效性

技术要求:
- 使用 Playwright（已安装）
- 不安装 Selenium

账号密码配置:
- 需要在 config/baijiahao_accounts.json 和 config/toutiao_accounts.json 中配置
- 或在本脚本的 ACCOUNT_CREDENTIALS 中配置（优先使用）

作者：自媒体自动化团队
版本：V1.0
创建时间：2026-04-11
"""

import io
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# 配置目录
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / 'config'
LOG_DIR = SCRIPT_DIR.parent / 'data' / 'cookie_logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# TODO: 账号密码配置（待主人确认）
# ============================================================================
# 方式一：在这里直接配置（优先级高）
ACCOUNT_CREDENTIALS = {
    'baijiahao': [
        {
            'name': '主账号',
            'username': '',  # TODO: 待确认 - 百家号登录用户名（手机号/邮箱）
            'password': '',  # TODO: 待确认 - 百家号登录密码
        }
    ],
    'toutiao': [
        {
            'name': '主账号',
            'username': '',  # TODO: 待确认 - 头条号登录用户名（手机号/邮箱）
            'password': '',  # TODO: 待确认 - 头条号登录密码
        }
    ]
}

# 方式二：从配置文件读取（如果上面为空）
# 需要在配置文件中添加 credentials.username 和 credentials.password 字段
# ============================================================================


class AutoLoginForCookies:
    """自动登录获取新 Cookie"""
    
    def __init__(self, platform: str = 'all', headless: bool = False):
        """
        Args:
            platform: 'baijiahao', 'toutiao', 或 'all'
            headless: 是否无头模式（调试时建议设为 False）
        """
        self.platform = platform
        self.headless = headless
        self.log_file = LOG_DIR / f'auto_login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # 登录 URL
        self.login_urls = {
            'baijiahao': 'https://baijiahao.baidu.com/',
            'toutiao': 'https://mp.toutiao.com/',
        }
        
        # 登录后验证 URL
        self.verify_urls = {
            'baijiahao': 'https://baijiahao.baidu.com/u/api/article/getlist',
            'toutiao': 'https://mp.toutiao.com/profile_v4/index',
        }
        
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        self.log(f"自动登录工具 V1.0 初始化完成")
        self.log(f"目标平台：{platform}")
        self.log(f"无头模式：{headless}")
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def load_credentials(self, platform: str) -> List[Dict]:
        """加载账号凭证"""
        # 优先使用硬编码配置
        creds = ACCOUNT_CREDENTIALS.get(platform, [])
        
        if creds and creds[0].get('username'):
            self.log(f"使用硬编码配置的账号")
            return creds
        
        # 否则从配置文件读取
        config_file = CONFIG_DIR / f'{platform}_accounts.json'
        
        if not config_file.exists():
            self.log(f"未找到配置文件：{config_file}")
            return []
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        accounts = config.get('accounts', [])
        credentials_list = []
        
        for account in accounts:
            username = account.get('credentials', {}).get('username', '')
            password = account.get('credentials', {}).get('password', '')
            
            if username and password:
                credentials_list.append({
                    'name': account.get('name', '账号'),
                    'username': username,
                    'password': password
                })
            else:
                self.log(f"⚠️ 账号 {account.get('name', '未知')} 的用户名/密码未配置")
        
        if not credentials_list:
            self.log("❌ 所有账号的用户名/密码均为空，请在配置文件中补充")
        
        return credentials_list
    
    def start_browser(self):
        """启动浏览器"""
        self.log("启动 Playwright 浏览器...")
        
        self.playwright = sync_playwright().start()
        
        # 启动 Chromium
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        # 创建浏览器上下文
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 隐藏 webdriver 特征
        self.page = self.context.new_page()
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)
        
        self.log("浏览器启动完成")
    
    def stop_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
            self.log("浏览器已关闭")
        
        if self.playwright:
            self.playwright.stop()
    
    def login_baijiahao(self, username: str, password: str) -> bool:
        """
        登录百家号
        
        百家号使用百度统一登录，需要处理：
        1. 点击登录按钮
        2. 输入用户名/密码
        3. 可能需要验证码（需要人工介入）
        4. 登录成功后跳转
        """
        self.log("开始登录百家号...")
        
        try:
            # 打开百家号
            self.page.goto(self.login_urls['baijiahao'], wait_until='networkidle', timeout=30000)
            self.page.wait_for_timeout(3000)
            
            # 检查是否已登录
            if self.is_logged_in('baijiahao'):
                self.log("✅ 已登录状态，跳过登录")
                return True
            
            # 查找登录按钮并点击
            # 百家号的登录按钮通常在右上角
            login_button_selectors = [
                'a[href*="login"]',
                'button:has-text("登录")',
                '.login-btn',
                '[data-action="login"]',
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    login_btn = self.page.query_selector(selector)
                    if login_btn:
                        login_btn.click()
                        self.log(f"点击登录按钮：{selector}")
                        login_clicked = True
                        self.page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            if not login_clicked:
                # 尝试直接跳转到登录页
                self.log("未找到登录按钮，尝试直接访问登录页...")
                self.page.goto('https://passport.baidu.com/v2/?login', wait_until='networkidle', timeout=30000)
                self.page.wait_for_timeout(3000)
            
            # 输入用户名（手机号）
            username_input = self.page.query_selector('input[id="username"]')
            if not username_input:
                username_input = self.page.query_selector('input[name="username"]')
            if not username_input:
                username_input = self.page.query_selector('input[type="text"]')
            
            if username_input:
                username_input.fill(username)
                self.log("已输入用户名")
                self.page.wait_for_timeout(1000)
            else:
                self.log("⚠️ 未找到用户名输入框，可能需要人工介入")
                # 截图保存当前状态
                self.save_screenshot('baijiahao_username_missing')
                return False
            
            # 输入密码
            password_input = self.page.query_selector('input[type="password"]')
            if password_input:
                password_input.fill(password)
                self.log("已输入密码")
                self.page.wait_for_timeout(1000)
            else:
                self.log("⚠️ 未找到密码输入框")
                self.save_screenshot('baijiahao_password_missing')
                return False
            
            # 点击登录按钮
            submit_button = self.page.query_selector('input[type="submit"]')
            if not submit_button:
                submit_button = self.page.query_selector('button[type="submit"]')
            if not submit_button:
                submit_button = self.page.query_selector('button:has-text("登录")')
            
            if submit_button:
                submit_button.click()
                self.log("已点击登录按钮")
            else:
                # 尝试按回车
                self.page.keyboard.press('Enter')
                self.log("已按回车键尝试登录")
            
            # 等待登录完成
            self.log("等待登录完成...")
            self.page.wait_for_timeout(5000)
            
            # 检查是否需要验证码
            if self.has_captcha('baijiahao'):
                self.log("⚠️ 检测到验证码，需要人工介入")
                self.save_screenshot('baijiahao_captcha')
                self.log("请在 60 秒内手动完成验证码...")
                
                # 等待人工完成（最多 60 秒）
                for i in range(60):
                    self.page.wait_for_timeout(1000)
                    if not self.has_captcha('baijiahao'):
                        self.log("✅ 验证码已完成")
                        break
                else:
                    self.log("❌ 验证码超时，登录失败")
                    return False
            
            # 等待跳转
            self.page.wait_for_timeout(5000)
            
            # 验证登录是否成功
            if self.is_logged_in('baijiahao'):
                self.log("✅ 百家号登录成功")
                return True
            else:
                self.log("❌ 百家号登录失败")
                self.save_screenshot('baijiahao_login_failed')
                return False
                
        except Exception as e:
            self.log(f"❌ 百家号登录异常：{str(e)}")
            self.save_screenshot('baijiahao_error')
            return False
    
    def login_toutiao(self, username: str, password: str) -> bool:
        """
        登录头条号
        
        头条号也使用头条/抖音统一登录
        """
        self.log("开始登录头条号...")
        
        try:
            # 打开头条号
            self.page.goto(self.login_urls['toutiao'], wait_until='networkidle', timeout=30000)
            self.page.wait_for_timeout(3000)
            
            # 检查是否已登录
            if self.is_logged_in('toutiao'):
                self.log("✅ 已登录状态，跳过登录")
                return True
            
            # 查找登录按钮
            login_button_selectors = [
                'button:has-text("登录")',
                '.login-btn',
                '[data-action="login"]',
                'a[href*="login"]',
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    login_btn = self.page.query_selector(selector)
                    if login_btn:
                        login_btn.click()
                        self.log(f"点击登录按钮：{selector}")
                        login_clicked = True
                        self.page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            if not login_clicked:
                # 尝试直接跳转到登录页
                self.log("未找到登录按钮，尝试访问登录页...")
                self.page.goto('https://sso.toutiao.com/login', wait_until='networkidle', timeout=30000)
                self.page.wait_for_timeout(3000)
            
            # 输入用户名（手机号）
            username_input = self.page.query_selector('input[type="text"]')
            if username_input:
                username_input.fill(username)
                self.log("已输入用户名")
                self.page.wait_for_timeout(1000)
            else:
                self.log("⚠️ 未找到用户名输入框")
                self.save_screenshot('toutiao_username_missing')
                return False
            
            # 输入密码
            password_input = self.page.query_selector('input[type="password"]')
            if password_input:
                password_input.fill(password)
                self.log("已输入密码")
                self.page.wait_for_timeout(1000)
            else:
                self.log("⚠️ 未找到密码输入框")
                self.save_screenshot('toutiao_password_missing')
                return False
            
            # 点击登录按钮
            submit_button = self.page.query_selector('button[type="submit"]')
            if submit_button:
                submit_button.click()
                self.log("已点击登录按钮")
            else:
                self.page.keyboard.press('Enter')
                self.log("已按回车键尝试登录")
            
            # 等待登录完成
            self.log("等待登录完成...")
            self.page.wait_for_timeout(5000)
            
            # 检查是否需要验证码
            if self.has_captcha('toutiao'):
                self.log("⚠️ 检测到验证码，需要人工介入")
                self.save_screenshot('toutiao_captcha')
                self.log("请在 60 秒内手动完成验证码...")
                
                for i in range(60):
                    self.page.wait_for_timeout(1000)
                    if not self.has_captcha('toutiao'):
                        self.log("✅ 验证码已完成")
                        break
                else:
                    self.log("❌ 验证码超时，登录失败")
                    return False
            
            # 等待跳转
            self.page.wait_for_timeout(5000)
            
            # 验证登录是否成功
            if self.is_logged_in('toutiao'):
                self.log("✅ 头条号登录成功")
                return True
            else:
                self.log("❌ 头条号登录失败")
                self.save_screenshot('toutiao_login_failed')
                return False
                
        except Exception as e:
            self.log(f"❌ 头条号登录异常：{str(e)}")
            self.save_screenshot('toutiao_error')
            return False
    
    def is_logged_in(self, platform: str) -> bool:
        """检查是否已登录"""
        try:
            if platform == 'baijiahao':
                # 检查是否有用户信息元素
                selectors = [
                    '.user-info',
                    '[class*="user"]',
                    'a[href*="profile"]',
                ]
                for selector in selectors:
                    if self.page.query_selector(selector):
                        return True
                
                # 或者检查当前 URL
                if 'baijiahao.baidu.com' in self.page.url:
                    return True
                    
            elif platform == 'toutiao':
                # 检查是否有管理后台元素
                selectors = [
                    '.profile-v4',
                    '[class*="profile"]',
                    'a[href*="manage"]',
                ]
                for selector in selectors:
                    if self.page.query_selector(selector):
                        return True
                
                if 'mp.toutiao.com' in self.page.url:
                    return True
                    
        except:
            pass
        
        return False
    
    def has_captcha(self, platform: str) -> bool:
        """检查是否有验证码"""
        captcha_keywords = ['验证码', 'captcha', 'verify', '滑动', '拼图']
        
        try:
            page_text = self.page.inner_text('body').lower()
            return any(keyword in page_text for keyword in captcha_keywords)
        except:
            return False
    
    def save_screenshot(self, name: str):
        """保存截图"""
        screenshot_dir = LOG_DIR / 'screenshots'
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = screenshot_dir / f'{name}_{timestamp}.png'
        
        self.page.screenshot(path=str(screenshot_path))
        self.log(f"截图已保存：{screenshot_path}")
    
    def extract_cookies(self) -> str:
        """提取当前 Cookie 字符串"""
        cookies = self.context.cookies()
        
        cookie_strs = []
        for cookie in cookies:
            cookie_strs.append(f"{cookie['name']}={cookie['value']}")
        
        return '; '.join(cookie_strs)
    
    def update_config(self, platform: str, new_cookie: str):
        """更新配置文件中的 Cookie"""
        config_file = CONFIG_DIR / f'{platform}_accounts.json'
        
        if not config_file.exists():
            self.log(f"❌ 配置文件不存在：{config_file}")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新第一个账号的 Cookie
        if config.get('accounts') and len(config['accounts']) > 0:
            config['accounts'][0]['credentials']['cookie'] = new_cookie
            config['accounts'][0]['credentials']['last_refresh'] = datetime.now().isoformat()
            
            # 添加配置备注
            if 'config_notes' not in config:
                config['config_notes'] = {}
            config['config_notes']['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            config['config_notes']['cookie_status'] = '✅ 已更新（自动登录）'
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.log(f"✅ {platform} Cookie 已更新到配置文件")
            return True
        else:
            self.log(f"❌ {platform} 账号配置为空")
            return False
    
    def verify_cookie(self, platform: str, cookie: str) -> bool:
        """验证 Cookie 是否有效"""
        self.log(f"验证 {platform} Cookie 有效性...")
        
        # 创建新的浏览器上下文进行测试
        test_context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        test_context.add_cookies([
            {'name': c.split('=')[0], 'value': c.split('=')[1], 'domain': f'.{platform}.baidu.com' if platform == 'baijiahao' else '.toutiao.com', 'path': '/'}
            for c in cookie.split('; ') if '=' in c
        ])
        
        test_page = test_context.new_page()
        
        try:
            test_page.goto(self.verify_urls[platform], timeout=30000)
            test_page.wait_for_timeout(3000)
            
            # 简单检查：页面是否包含错误信息
            page_text = test_page.inner_text('body').lower()
            
            if 'error' in page_text or 'login' in page_text or '登录' in page_text:
                self.log(f"❌ {platform} Cookie 验证失败")
                return False
            
            self.log(f"✅ {platform} Cookie 验证通过")
            return True
            
        except Exception as e:
            self.log(f"❌ Cookie 验证异常：{str(e)}")
            return False
        finally:
            test_page.close()
            test_context.close()
    
    def run(self, platform: str) -> bool:
        """
        执行自动登录流程
        
        Args:
            platform: 'baijiahao' 或 'toutiao'
        
        Returns:
            是否成功
        """
        self.log(f"\n{'='*60}")
        self.log(f"开始 {platform} 自动登录流程")
        self.log(f"{'='*60}")
        
        # 加载凭证
        credentials = self.load_credentials(platform)
        
        if not credentials:
            self.log(f"❌ 没有可用的账号凭证，请先在配置文件中填写 username 和 password")
            return False
        
        # 启动浏览器
        self.start_browser()
        
        success = False
        
        for cred in credentials:
            self.log(f"\n尝试登录：{cred['name']}")
            
            if platform == 'baijiahao':
                login_success = self.login_baijiahao(cred['username'], cred['password'])
            else:
                login_success = self.login_toutiao(cred['username'], cred['password'])
            
            if login_success:
                # 提取 Cookie
                new_cookie = self.extract_cookies()
                
                # 验证 Cookie
                if self.verify_cookie(platform, new_cookie):
                    # 更新配置文件
                    if self.update_config(platform, new_cookie):
                        success = True
                        self.log(f"✅ {cred['name']} 登录并更新 Cookie 成功")
                        break
                else:
                    self.log(f"⚠️ {cred['name']} Cookie 验证失败，跳过更新")
        
        # 关闭浏览器
        self.stop_browser()
        
        self.log(f"\n{'='*60}")
        if success:
            self.log(f"✅ {platform} 自动登录完成")
        else:
            self.log(f"❌ {platform} 自动登录失败")
        self.log(f"{'='*60}")
        
        return success
    
    def run_all(self) -> Dict[str, bool]:
        """执行所有平台的自动登录"""
        results = {}
        
        platforms = []
        if self.platform == 'all':
            platforms = ['baijiahao', 'toutiao']
        else:
            platforms = [self.platform]
        
        for platform in platforms:
            results[platform] = self.run(platform)
        
        return results


def main():
    """主函数 - 可被 Plan A 调用或独立运行"""
    import sys
    
    # 命令行参数
    platform = 'all'
    headless = True
    
    for arg in sys.argv[1:]:
        if arg.startswith('--platform='):
            platform = arg.split('=')[1]
        elif arg == '--headful':
            headless = False
        elif arg == '--help':
            print("用法：python auto_login_for_cookies.py [选项]")
            print("选项:")
            print("  --platform=baijiahao|toutiao|all  指定平台（默认：all）")
            print("  --headful                        有头模式（显示浏览器）")
            print("  --help                           显示帮助")
            return
    
    # 创建自动登录器
    auto_login = AutoLoginForCookies(platform=platform, headless=headless)
    
    # 执行登录
    if platform == 'all':
        results = auto_login.run_all()
        
        print("\n" + "=" * 60)
        print("自动登录结果汇总")
        print("=" * 60)
        for p, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{p}: {status}")
        print("=" * 60)
        
        # 返回状态码
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        success = auto_login.run(platform)
        sys.exit(0 if success else 1)


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
