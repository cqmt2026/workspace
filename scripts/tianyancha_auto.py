#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天眼查查询 - 使用Chrome已登录状态
通过CDP协议连接已运行的Chrome
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

async def main():
    print("=" * 60)
    print("天眼查批量查询工具")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器（不指定用户数据，使用默认配置）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n[1] 打开天眼查登录页...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 检查是否已登录
        current_url = page.url
        print(f"    URL: {current_url}")
        
        if "login" in current_url.lower():
            print("\n[!] 未登录，请在弹出的浏览器窗口中登录")
            print("\n请按以下步骤操作:")
            print("1. 在浏览器中完成登录（扫码或账号密码）")
            print("2. 登录成功后，返回这个窗口输入 'ok'")
            print("3. 我会自动开始查询\n")
            
            while "login" in page.url.lower():
                await asyncio.sleep(2)
            
            print("[OK] 检测到已登录！")
        
        # 获取页面信息
        print(f"\n    Title: {await page.title()}")
        
        # 截图确认
        await page.screenshot(path="C:/Users/Administrator/.openclaw/workspace/tianyancha_ready.png", full_page=True)
        print("    截图: tianyancha_ready.png")
        
        # 搜索企业
        companies = [
            "北京字节跳动科技有限公司",
            "上海哔哩哔哩科技有限公司", 
            "深圳市腾讯计算机系统有限公司"
        ]
        
        results = []
        
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] 搜索: {company}")
            
            # 清空搜索框
            await page.goto("https://www.tianyancha.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # 填入搜索词（JS方式）
            js_code = f"""
            () => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = (input.placeholder || '').toLowerCase();
                    if (ph.includes('search') || ph.includes('公司')) {{
                        input.value = '{company}';
                        input.dispatchEvent(new Event('input', {{bubbles: true}}));
                        input.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'Filled: ' + ph;
                    }}
                }}
                return 'Not found';
            }}
            """
            result = await page.evaluate(js_code)
            print(f"    {result}")
            await asyncio.sleep(1)
            
            # 按Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
            
            print(f"    URL: {page.url}")
            
            # 查找企业链接
            links = await page.evaluate(f"""
                () => {{
                    const result = [];
                    document.querySelectorAll('a').forEach(a => {{
                        const text = a.textContent.trim();
                        const href = a.getAttribute('href') || '';
                        if (text.includes('%s') && href.includes('/company/')) {{
                            result.push({{text, href}});
                        }}
                    }});
                    return result;
                }}
            """ % company)
            
            print(f"    找到 {len(links)} 个企业链接")
            
            if links:
                # 点击第一个
                await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
                await asyncio.sleep(3)
                
                # 截图
                await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/detail_{i}.png", full_page=True)
                print(f"    截图: detail_{i}.png")
                
                # 提取信息
                text = await page.evaluate("() => document.body.innerText")
                
                import re
                phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
                address = re.search(r'地址[：:]\s*([^\n]+)', text)
                employee = re.search(r'参保人数[：:]\s*(\d+)', text)
                abnormal = '经营异常' in text
                
                info = {
                    "company": company,
                    "phone": phone.group(1) if phone else "",
                    "address": address.group(1).strip() if address else "",
                    "employees": employee.group(1) if employee else "",
                    "has_abnormal": abnormal,
                    "qualified": False
                }
                
                try:
                    emp_count = int(info["employees"]) if info["employees"] else 0
                    info["qualified"] = emp_count > 20 and not info["has_abnormal"]
                except:
                    pass
                
                status = "[OK]" if info["qualified"] else "[X]"
                print(f"    {status} 电话:{info['phone'] or '无'} 员工:{info['employees'] or '未知'} 异常:{info['has_abnormal']}")
                
                results.append(info)
            else:
                print(f"    [X] 未找到企业链接")
            
            # 返回首页
            if i < len(companies):
                await page.goto("https://www.tianyancha.com", wait_until="networkidle")
                await asyncio.sleep(1)
        
        # 保存结果
        qualified = [r for r in results if r.get("qualified", False)]
        
        output = {
            "query_time": asyncio.get_event_loop().time(),
            "total": len(companies),
            "found": len(results),
            "qualified": len(qualified),
            "results": results
        }
        
        with open("tianyancha_result.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        with open("tianyancha_result.csv", "w", encoding="utf-8-sig") as f:
            f.write("企业名称,联系电话,地址,员工人数,是否有异常\n")
            for r in qualified:
                f.write(f"{r['company']},{r['phone']},{r['address']},{r['employees']},{r['has_abnormal']}\n")
        
        print(f"\n{'='*60}")
        print(f"完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print(f"文件: tianyancha_result.json, tianyancha_result.csv")
        print('='*60)
        
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())
