#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 启动有头浏览器（能看到）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("=" * 60)
        print("天眼查登录调试")
        print("=" * 60)
        
        # 访问天眼查
        print("\n正在打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        print(f"当前URL: {page.url}")
        print(f"页面标题: {await page.title()}")
        
        # 检查是否需要在登录页登录
        if "login" in page.url.lower():
            print("\n[!] 检测到登录页面！")
            print("请在浏览器窗口中完成登录...")
            print("登录成功后，这个窗口会检测到并继续...\n")
            
            # 等待登录完成（最多5分钟）
            for i in range(30):
                await asyncio.sleep(10)
                current_url = page.url
                
                print(f"[{i+1}/30] 当前URL: {current_url}")
                
                if "login" not in current_url.lower():
                    print("[OK] 检测到已登录！")
                    break
            else:
                print("[WARN] 等待超时，可能未登录")
        else:
            print("[OK] 已检测到登录状态")
        
        print("\n" + "=" * 60)
        print("开始查询企业...")
        print("=" * 60)
        
        # 搜索企业
        companies = ["北京字节跳动科技有限公司", "上海哔哩哔哩科技有限公司"]
        
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] 搜索: {company}")
            
            # 清空搜索框
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
                        return 'Filled: ' + ph;
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
            
            # 截图
            await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/tianyancha_step{i}.png", full_page=True)
            print(f"    截图: tianyancha_step{i}.png")
            
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
                print(f"      - {link['text']}: {link['href'][:60]}...")
            
            # 点击第一个
            if links:
                await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
                await asyncio.sleep(3)
                
                await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/tianyancha_detail_{company[:4]}.png", full_page=True)
                print(f"    详情页截图: tianyancha_detail_{company[:4]}.png")
                
                # 提取信息
                text = await page.evaluate("() => document.body.innerText")
                
                import re
                phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
                address = re.search(r'地址[：:]\s*([^\n]+)', text)
                employee = re.search(r'参保人数[：:]\s*(\d+)', text)
                abnormal = '经营异常' in text
                
                phone_str = phone.group(1) if phone else "未找到"
                address_str = address.group(1).strip()[:50] if address else "未找到"
                employee_str = employee.group(1) if employee else "未找到"
                
                print(f"    电话: {phone_str}")
                print(f"    地址: {address_str}...")
                print(f"    员工: {employee_str} 人")
                print(f"    异常: {'有' if abnormal else '无'}")
            
            # 返回搜索页
            if i < len(companies):
                await page.goto("https://www.tianyancha.com", wait_until="networkidle")
                await asyncio.sleep(1)
        
        print("\n" + "=" * 60)
        print("查询完成！")
        print("=" * 60)
        
        # 保持浏览器打开10秒
        print("\n浏览器将在10秒后关闭...")
        await asyncio.sleep(10)
        await browser.close()
        print("完成！")

asyncio.run(main())
