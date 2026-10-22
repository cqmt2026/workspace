#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查查询 - 交互式版本，等待用户明确完成登录，不自动关闭浏览器"""
import asyncio
from playwright.async_api import async_playwright
import re
import json
import time

async def main():
    print("=" * 60)
    print("天眼查批量查询工具")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 打开天眼查
        print("\n[1] 正在打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        print(f"    URL: {page.url}")
        print(f"    Title: {await page.title()}")
        
        # 持续等待登录完成
        print("\n" + "=" * 60)
        print("请在此浏览器窗口中完成登录！")
        print("登录方式：手机号+验证码 或 微信扫码")
        print("登录完成后，在此终端输入 '完成' 并按回车")
        print("=" * 60)
        print()
        
        # 循环检查登录状态
        last_url = page.url
        logged_in = False
        while not logged_in:
            await asyncio.sleep(2)
            current_url = page.url
            title = await page.title()
            
            # 检测是否已登录（URL不再是登录页且页面有实际内容）
            if "login" not in current_url.lower() and current_url != last_url:
                if "天眼查" in title or "企业查询" in title:
                    print(f"\n[+] 检测到页面: {title}")
                    print("[+] 请确认登录完成，输入 '完成' 继续...")
                    
                    # 等待用户输入
                    try:
                        user_input = input("> ")
                        if user_input.strip().lower() in ['完成', 'ok', 'done', '继续']:
                            logged_in = True
                            print("[+] 开始查询...")
                        else:
                            print("[-] 输入无效，请重新输入 '完成'")
                    except EOFError:
                        print("\n[-] 无法读取输入，将继续...")
                        logged_in = True
            
            last_url = current_url
        
        print(f"\n[2] 已登录，开始查询 {len(companies)} 家企业...")
        
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
            
            # 查找企业链接
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
            
            # 间隔等待
            if i < len(companies):
                await asyncio.sleep(3)
        
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
        
        print(f"\n{'='*60}")
        print(f"查询完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print(f"文件: tianyancha_result.json, tianyancha_result.csv")
        print("=" * 60)
        
        print("\n[提示] 浏览器将保持打开状态，您可以手动关闭")
        print("[提示] 输入 '退出' 按回车结束程序...")
        
        # 保持运行，直到用户输入退出
        while True:
            try:
                user_input = input("> ")
                if user_input.strip().lower() in ['退出', 'exit', 'quit', '关闭']:
                    print("\n正在关闭...")
                    break
            except EOFError:
                break
        
        await browser.close()
        print("完成！")

if __name__ == "__main__":
    companies = [
        "北京字节跳动科技有限公司",
        "上海哔哩哔哩科技有限公司",
        "深圳市腾讯计算机系统有限公司",
    ]
    asyncio.run(main())
