#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用已登录的Chrome浏览器的Cookie
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 连接到已运行的Chrome（需要启动时带上调试端口）
        # 或者使用用户数据目录
        print("=" * 60)
        print("天眼查查询 - 使用Chrome用户数据")
        print("=" * 60)
        
        # 方法1: 使用Chrome用户数据目录（保留登录状态）
        user_data_dir = r"C:\Users\Administrator\AppData\Local\Google\Chrome\User Data"
        
        print(f"\n[1] 启动Chrome (使用已有登录状态)...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = await browser.new_page()
        
        # 访问天眼查
        print("[2] 访问天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(2)
        
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")
        
        # 检查是否登录
        if "login" in page.url.lower():
            print("\n[!] 未登录！请先在Chrome中登录天眼查")
            print("登录完成后按回车继续...")
            input()
        else:
            print("[OK] 已检测到登录状态")
        
        # 截图确认
        await page.screenshot(path="C:/Users/Administrator/.openclaw/workspace/chrome_login_check.png", full_page=True)
        print("截图: chrome_login_check.png")
        
        # 搜索企业
        companies = ["北京字节跳动科技有限公司", "上海哔哩哔哩科技有限公司"]
        
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] {company}")
            
            # 回到首页搜索
            await page.goto("https://www.tianyancha.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # 填入搜索词
            js_fill = f"""
            () => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = (input.placeholder || '').toLowerCase();
                    if (ph.includes('search') || ph.includes('公司')) {{
                        input.value = '{company}';
                        input.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return 'Filled';
                    }}
                }}
                return 'Not found';
            }}
            """
            print(f"    搜索框: {await page.evaluate(js_fill)}")
            await asyncio.sleep(1)
            
            # 按Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
            
            print(f"    URL: {page.url}")
            
            # 查找企业链接
            links = await page.evaluate("""
                () => {
                    const result = [];
                    document.querySelectorAll('a').forEach(a => {
                        const text = a.textContent.trim();
                        const href = a.getAttribute('href') || '';
                        if (text.includes('%s') && href.includes('/company/')) {
                            result.push({text, href});
                        }
                    });
                    return result;
                }
            """ % company)
            
            print(f"    找到 {len(links)} 个链接")
            
            if links:
                await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
                await asyncio.sleep(3)
                
                await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/detail_{company[:4]}.png", full_page=True)
                print(f"    截图: detail_{company[:4]}.png")
                
                text = await page.evaluate("() => document.body.innerText")
                
                import re
                phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
                employee = re.search(r'参保人数[：:]\s*(\d+)', text)
                abnormal = '经营异常' in text
                
                print(f"    电话: {phone.group(1) if phone else '未找到'}")
                print(f"    员工: {employee.group(1) if employee else '未找到'} 人")
                print(f"    异常: {'有' if abnormal else '无'}")
        
        print("\n完成！浏览器将在5秒后关闭...")
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(main())
