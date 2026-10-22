#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查查询 - 单个企业"""
import asyncio, json, re, time
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path(__file__).parent.parent / "tianyancha_cookies.json"
RESULTS_FILE = Path(__file__).parent.parent / "tianyancha_result.json"
CSV_FILE = Path(__file__).parent.parent / "tianyancha_result.csv"

COMPANY = "重庆恒重机械制造有限责任公司"

async def main():
    cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    print(f"[+] 加载 {len(cookies)} 个Cookie")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(storage_state={"cookies": cookies, "origins": []})
        page = await ctx.new_page()

        print("[1] 打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        if "login" in page.url.lower():
            print("[!] Cookie已过期")
            await browser.close()
            return
        print("[+] 登录正常")

        print(f"\n[2] 搜索: {COMPANY}")
        search_url = f"https://www.tianyancha.com/search?key={COMPANY}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(5)
        print(f"    URL: {page.url}")

        # 截图
        await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/s{COMPANY[:4]}.png")

        # 查找企业链接
        all_links = await page.evaluate("""() => {
            const result = [];
            document.querySelectorAll('a[href*="/company/"]').forEach(a => {
                const text = a.textContent.trim();
                if (text.length > 3) {
                    result.push({text, href: a.getAttribute('href')});
                }
            });
            return result;
        }""")
        
        print(f"    找到 {len(all_links)} 个企业链接")
        
        # 精确匹配
        target_link = None
        for link in all_links:
            if COMPANY in link['text']:
                target_link = link
                print(f"    ✓ 精确匹配: {link['text']}")
                break
        
        if not target_link and all_links:
            target_link = all_links[0]
            print(f"    ⚠ 使用第一个: {target_link['text']}")
        
        if target_link:
            detail_url = "https://www.tianyancha.com" + target_link['href']
            print(f"    进入详情页...")
            
            await page.goto(detail_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)
            print(f"    详情页URL: {page.url[:70]}")

            # 截图
            await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/d{COMPANY[:4]}.png")

            # 提取信息
            text = await page.evaluate("() => document.body.innerText")
            
            phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
            address = re.search(r'地址[：:]\s*([^\n]+)', text)
            employee = re.search(r'参保人数[：:]\s*(\d+)', text)
            abnormal = '经营异常' in text or '异常经营' in text

            info = {
                "company": COMPANY,
                "actual_name": target_link['text'],
                "phone": phone.group(1) if phone else "",
                "address": address.group(1).strip()[:100] if address else "",
                "employees": employee.group(1) if employee else "",
                "has_abnormal": abnormal,
                "qualified": False,
            }
            try:
                emp = int(info["employees"]) if info["employees"] else 0
                info["qualified"] = emp > 20 and not abnormal
            except:
                pass

            status = "✓ 符合条件" if info["qualified"] else "✗ 不符合条件"
            print(f"\n    {status}")
            print(f"    企业名称: {info['actual_name']}")
            print(f"    联系电话: {info['phone'] or '未找到'}")
            if info['address']:
                print(f"    企业地址: {info['address'][:60]}...")
            else:
                print(f"    企业地址: 未找到")
            print(f"    员工人数: {info['employees'] or '未找到'} 人")
            print(f"    经营异常: {'有' if info['has_abnormal'] else '无'}")
            
            # 保存结果
            output = {
                "query_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total": 1,
                "found": 1,
                "qualified": 1 if info["qualified"] else 0,
                "results": [info],
            }
            RESULTS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
            
            with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
                f.write("企业名称,实际匹配名称,联系电话,地址,员工人数,是否有异常\n")
                if info["qualified"]:
                    f.write(f"{info['company']},{info['actual_name']},{info['phone']},{info['address']},{info['employees']},{info['has_abnormal']}\n")

        else:
            print(f"    [!] 未找到企业链接")

        print("\n[提示] 浏览器保持打开，输入'退出'关闭...")
        while True:
            try:
                inp = input("> ")
                if inp.strip().lower() in ['退出', 'exit']:
                    break
            except EOFError:
                break
        
        await browser.close()
        print("完成！")

asyncio.run(main())
