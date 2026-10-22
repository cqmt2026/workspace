#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查查询 - 等待登录版"""
import asyncio
import json
import re
import time
from playwright.async_api import async_playwright

COMPANIES = [
    "北京字节跳动科技有限公司",
    "上海哔哩哔哩科技有限公司",
    "深圳市腾讯计算机系统有限公司",
]

async def main():
    print("="*50)
    print("天眼查批量查询")
    print("="*50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("\n[1] 打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        print(f"    URL: {page.url}")
        
        # 等待登录
        print("\n" + "="*50)
        print("请在浏览器中完成登录")
        print("手机号+验证码 或 微信扫码")
        print("登录完成后输入 'ok' 继续")
        print("="*50)
        
        # 监控登录
        for _ in range(60):  # 最多等5分钟
            await asyncio.sleep(5)
            url = page.url
            if "login" not in url.lower():
                print(f"\n[+] 检测到登录成功: {url}")
                break
        
        # 等待用户确认
        confirm = input("\n按回车开始查询...")
        
        print("\n[2] 开始查询...")
        results = []
        
        for i, company in enumerate(COMPANIES, 1):
            print(f"\n[{i}/{len(COMPANIES)}] {company}")
            
            # 搜索
            await page.goto("https://www.tianyancha.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # 填搜索框
            await page.evaluate(f"""() => {{
                const input = document.querySelector('input[placeholder*="搜索"]');
                if (input) {{ input.value = '{company}'; input.dispatchEvent(new Event('input', {{bubbles:true}})); }}
            }}""")
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
            
            # 找链接
            links = await page.evaluate("""() => {
                const r = [];
                document.querySelectorAll('a').forEach(a => {
                    const t = a.textContent.trim();
                    const h = a.getAttribute('href')||'';
                    if(t.length>5 && h.includes('/company/')) r.push({t:h.substring(0,40), href:h});
                });
                return r;
            }""")
            
            print(f"    找到 {len(links)} 个链接")
            
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
                print(f"    [X] 未找到")
            
            if i < len(COMPANIES):
                await asyncio.sleep(3)
        
        # 保存
        qualified = [r for r in results if r.get("qualified")]
        output = {"query_time": time.strftime("%Y-%m-%d %H:%M:%S"), "total": len(COMPANIES), 
                  "found": len(results), "qualified": len(qualified), "results": results}
        
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
        print("\n浏览器保持打开，手动关闭即可。输入回车退出程序...")
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
