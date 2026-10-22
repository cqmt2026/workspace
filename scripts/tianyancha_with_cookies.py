#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Cookie登录天眼查
"""
import asyncio
import json
from playwright.async_api import async_playwright
import sys

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("=" * 60)
        print("天眼查查询 - Cookie登录方式")
        print("=" * 60)
        
        # 提示获取Cookie
        print("\n请按照以下步骤获取Cookie:")
        print("1. Chrome访问 https://www.tianyancha.com 并登录")
        print("2. F12 → Application → Cookies → https://www.tianyancha.com")
        print("3. 右键 → Export")
        print("4. 将JSON内容保存到: C:\\Users\\Administrator\\.openclaw\\workspace\\tianyancha_cookies.json")
        print("5. 保存完成后，按回车继续...")
        
        input()
        
        # 读取Cookie
        cookie_file = "C:/Users/Administrator/.openclaw/workspace/tianyancha_cookies.json"
        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            print(f"\n[OK] 已读取 {len(cookies)} 个Cookie")
        except Exception as e:
            print(f"\n[ERROR] 读取Cookie失败: {e}")
            print("请确保Cookie文件存在且格式正确")
            await browser.close()
            return
        
        # 设置Cookie
        print("\n[1] 设置Cookie...")
        await context.add_cookies(cookies)
        
        # 访问天眼查
        print("[2] 访问天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(2)
        
        print(f"    URL: {page.url}")
        print(f"    Title: {await page.title()}")
        
        if "login" in page.url.lower():
            print("\n[!] Cookie可能已过期，请重新获取")
            await browser.close()
            return
        
        print("[OK] 登录成功！")
        
        # 截图
        await page.screenshot(path="C:/Users/Administrator/.openclaw/workspace/tianyancha_login_ok.png", full_page=True)
        print("    截图: tianyancha_login_ok.png")
        
        # 搜索企业
        companies = ["北京字节跳动科技有限公司", "上海哔哩哔哩科技有限公司", "深圳市腾讯计算机系统有限公司"]
        
        results = []
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
            
            # 返回搜索页
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
        
        with open("tianyancha_final_result.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        with open("tianyancha_results.csv", "w", encoding="utf-8-sig") as f:
            f.write("企业名称,联系电话,地址,员工人数,是否有异常\n")
            for r in qualified:
                f.write(f"{r['company']},{r['phone']},{r['address']},{r['employees']},{r['has_abnormal']}\n")
        
        print(f"\n{'='*60}")
        print(f"完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print(f"文件: tianyancha_final_result.json, tianyancha_results.csv")
        print('='*60)
        
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(main())
