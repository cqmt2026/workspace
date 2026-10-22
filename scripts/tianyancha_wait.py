#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天眼查查询 - 等待用户手动操作版
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("=" * 60)
        print("天眼查查询工具")
        print("=" * 60)
        
        # 打开天眼查
        print("\n[1] 打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(2)
        
        print(f"    URL: {page.url}")
        print(f"    Title: {await page.title()}")
        
        # 检查登录状态
        if "login" in page.url.lower():
            print("\n[!] 需要登录！")
            print("\n请在浏览器中完成登录：")
            print("  1. 选择手机号登录")
            print("  2. 输入手机号")
            print("  3. 获取验证码")
            print("  4. 输入验证码")
            print("\n登录完成后，回到这个窗口输入 'ok' 按回车")
            print("(不会超时，我会一直等)\n")
            
            # 持续监控，直到登录成功
            while "login" in page.url.lower():
                await asyncio.sleep(3)
                current_url = page.url
                if "login" not in current_url.lower():
                    print("[OK] 检测到登录成功！")
                    break
            
            # 用户确认
            user_input = input("输入 'ok' 开始查询: ")
            if user_input.lower() != 'ok':
                print("已取消")
                await browser.close()
                return
        
        print("\n[2] 开始查询企业...")
        
        # 搜索企业
        companies = [
            "北京字节跳动科技有限公司",
            "上海哔哩哔哩科技有限公司", 
            "深圳市腾讯计算机系统有限公司"
        ]
        
        results = []
        
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] {company}")
            
            # 清空搜索框
            await page.goto("https://www.tianyancha.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # 填入搜索词
            js = f"""
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
            print(f"    搜索框: {await page.evaluate(js)}")
            await asyncio.sleep(1)
            
            # 按Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
            
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
            
            print(f"    找到 {len(links)} 个链接")
            
            if links:
                await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
                await asyncio.sleep(3)
                
                text = await page.evaluate("() => document.body.innerText")
                
                import re
                phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
                address = re.search(r'地址[：:]\s*([^\n]+)', text)
                employee = re.search(r'参保人数[：:]\s*(\d+)', text)
                abnormal = '经营异常' in text
                
                info = {
                    "company": company,
                    "phone": phone.group(1) if phone else "",
                    "address": address.group(1).strip()[:80] if address else "",
                    "employees": employee.group(1) if employee else "",
                    "has_abnormal": abnormal,
                    "qualified": False
                }
                
                try:
                    emp = int(info["employees"]) if info["employees"] else 0
                    info["qualified"] = emp > 20 and not info["has_abnormal"]
                except:
                    pass
                
                status = "[OK]" if info["qualified"] else "[X]"
                print(f"    {status} 电话:{info['phone'] or '无'} 员工:{info['employees'] or '未知'} 异常:{info['has_abnormal']}")
                
                results.append(info)
            else:
                print(f"    [X] 未找到")
            
            # 返回
            if i < len(companies):
                await page.goto("https://www.tianyancha.com", wait_until="networkidle")
                await asyncio.sleep(1)
        
        # 保存结果
        qualified = [r for r in results if r.get("qualified", False)]
        
        with open("tianyancha_result.json", "w", encoding="utf-8") as f:
            import json
            json.dump({"total": len(companies), "qualified": len(qualified), "results": results}, 
                     f, ensure_ascii=False, indent=2)
        
        with open("tianyancha_result.csv", "w", encoding="utf-8-sig") as f:
            f.write("企业名称,联系电话,地址,员工人数,是否符合\n")
            for r in qualified:
                f.write(f"{r['company']},{r['phone']},{r['address']},{r['employees']},是\n")
        
        print(f"\n{'='*60}")
        print(f"完成: 总{len(companies)} 符合{len(qualified)}")
        print(f"文件: tianyancha_result.json, tianyancha_result.csv")
        print('='*60)
        
        print("\n浏览器将在15秒后关闭...")
        await asyncio.sleep(15)
        await browser.close()

asyncio.run(main())
