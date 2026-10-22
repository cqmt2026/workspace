#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天眼查查询 - 等待手动登录版本
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("=" * 60)
        print("天眼查查询 - 等待登录")
        print("=" * 60)
        
        # 访问天眼查
        print("\n[1] 正在打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 检查是否已登录
        current_url = page.url
        
        if "login" in current_url.lower():
            print("[!] 检测到登录页面")
            print("\n请在弹出的浏览器窗口中完成登录！")
            print("登录完成后，输入 'ok' 并按回车继续...")
            
            while "login" in page.url.lower():
                await asyncio.sleep(2)
                current_url = page.url
                if "login" not in current_url.lower():
                    print("[OK] 检测到已登录！")
                    break
            
            # 用户确认
            user_input = input("\n按回车开始查询...")
        else:
            print("[OK] 已检测到登录状态")
        
        # 截图确认
        await page.screenshot(path="C:/Users/Administrator/.openclaw/workspace/tianyancha_after_login.png", full_page=True)
        print("\n截图已保存: tianyancha_after_login.png")
        
        # 搜索企业
        companies = ["北京字节跳动科技有限公司", "上海哔哩哔哩科技有限公司"]
        
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] 搜索: {company}")
            
            # 填写搜索框
            js_fill = f"""
            () => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = (input.placeholder || '').toLowerCase();
                    if (ph.includes('search') || ph.includes('公司') || ph.includes('企业')) {{
                        input.value = '{company}';
                        input.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return 'Filled';
                    }}
                }}
                return 'Not found';
            }}
            """
            print(f"    搜索框: {await page.evaluate(js_fill)}")
            await asyncio.sleep(0.5)
            
            # 按Enter
            await page.keyboard.press("Enter")
            print(f"    已按Enter")
            await asyncio.sleep(3)
            
            # 检查URL
            print(f"    URL: {page.url}")
            
            # 查找企业链接
            links = await page.evaluate("""
                () => {
                    const result = [];
                    document.querySelectorAll('a').forEach(a => {
                        const text = a.textContent.trim();
                        const href = a.getAttribute('href') || '';
                        if (text.length > 5 && href.includes('/company/')) {
                            result.push({text: text.substring(0, 40), href});
                        }
                    });
                    return result.slice(0, 5);
                }
            """)
            
            print(f"    找到 {len(links)} 个企业链接")
            for link in links[:3]:
                print(f"      - {link['text']}: {link['href'][:50]}...")
            
            # 点击第一个
            if links:
                await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
                await asyncio.sleep(3)
                
                await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/tianyancha_{company[:4]}.png", full_page=True)
                print(f"    详情页截图: tianyancha_{company[:4]}.png")
                
                # 提取信息
                text = await page.evaluate("() => document.body.innerText")
                print(f"\n    --- 页面内容 (前500字) ---")
                print(f"    {text[:500]}")
            
            # 返回搜索页
            if i < len(companies):
                await page.goto("https://www.tianyancha.com", wait_until="networkidle")
                await asyncio.sleep(1)
        
        print("\n" + "=" * 60)
        print("调试完成")
        print("=" * 60)
        
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(main())
