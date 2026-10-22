#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查查询 - 简化版"""
import asyncio
from playwright.async_api import async_playwright
import re, json, time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("[1] 打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        print(f"    URL: {page.url}")
        
        # 等待登录
        if "login" in page.url.lower():
            print("\n[!] 需要登录！请在浏览器中完成登录")
            print("登录完成后，在这里按回车继续...\n")
            input()
        
        print(f"[2] 已登录，开始查询...")
        
        companies = [
            "北京字节跳动科技有限公司",
            "上海哔哩哔哩科技有限公司",
            "深圳市腾讯计算机系统有限公司",
        ]
        
        results = []
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] {company}")
            
            # 回首页搜索
            await page.goto("https://www.tianyancha.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # 填入搜索词
            await page.evaluate(f"""() => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = (input.placeholder || '').toLowerCase();
                    if (ph.includes('search') || ph.includes('公司')) {{
                        input.value = '{company}';
                        input.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return;
                    }}
                }}
            }}""")
            await asyncio.sleep(1)
            
            # 按Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
            
            print(f"    URL: {page.url}")
            
            # 查找链接
            links = await page.evaluate("""() => {
                const result = [];
                document.querySelectorAll('a').forEach(a => {
                    const text = a.textContent.trim();
                    const href = a.getAttribute('href') || '';
                    if (text.length > 5 && href.includes('/company/')) {
                        result.push({text: text.substring(0, 40), href});
                    }
                });
                return result;
            }""")
            
            print(f"    找到 {len(links)} 个链接")
            for link in links[:3]:
                print(f"      - {link['text']}: {link['href'][:60]}")
            
            if links:
                await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
                await asyncio.sleep(3)
                
                text = await page.evaluate("() => document.body.innerText")
                
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
                    info["qualified"] = emp > 20 and not abnormal
                except:
                    pass
                
                status = "[OK]" if info["qualified"] else "[X]"
                print(f"    {status} 电话:{info['phone'] or '无'} 员工:{info['employees'] or '未知'} 异常:{abnormal}")
                results.append(info)
            else:
                print(f"    [X] 未找到企业")
        
        # 保存结果
        qualified = [r for r in results if r.get("qualified", False)]
        output = {
            "query_time": time.strftime("%Y-%m-%d %H:%M:%S"),
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
        
        print(f"\n{'='*50}")
        print(f"完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print(f"文件: tianyancha_result.json, tianyancha_result.csv")
        print("="*50)
        
        print("\n浏览器将在10秒后关闭...")
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())
