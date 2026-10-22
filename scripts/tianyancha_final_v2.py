#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查批量查询 - 最终版"""
import asyncio, json, re, time
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path(__file__).parent.parent / "tianyancha_cookies.json"
RESULTS_FILE = Path(__file__).parent.parent / "tianyancha_result.json"
CSV_FILE = Path(__file__).parent.parent / "tianyancha_result.csv"

async def main():
    cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    print(f"[+] 加载 {len(cookies)} 个Cookie")

    companies = [
        "北京字节跳动科技有限公司",
        "上海哔哩哔哩科技有限公司",
        "深圳市腾讯计算机系统有限公司",
        "杭州阿里巴巴广告有限公司",
        "网易有限公司",
    ]

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

        results = []
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] {company}")

            # 直接访问搜索页
            search_url = "https://www.tianyancha.com/search?key=" + company
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(5)
            print(f"    URL: {page.url}")

            # 截图
            await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/s{company[:4]}.png")

            # 查找所有企业链接
            all_links = await page.evaluate("""() => {
                const result = [];
                document.querySelectorAll('a[href*="/company/"]').forEach(a => {
                    const text = a.textContent.trim();
                    if (text.length > 3) {
                        result.push({
                            text: text,
                            href: a.getAttribute('href')
                        });
                    }
                });
                return result;
            }""")
            
            print(f"    找到 {len(all_links)} 个企业链接")
            
            # 精确匹配
            target_link = None
            for link in all_links:
                if company in link['text']:
                    target_link = link
                    print(f"    ✓ 精确匹配: {link['text']}")
                    break
            
            # 取第一个
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
                await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/d{company[:4]}.png")

                # 提取信息
                text = await page.evaluate("() => document.body.innerText")
                
                phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
                address = re.search(r'地址[：:]\s*([^\n]+)', text)
                employee = re.search(r'参保人数[：:]\s*(\d+)', text)
                abnormal = '经营异常' in text or '异常经营' in text

                info = {
                    "company": company,
                    "actual_name": target_link['text'],
                    "phone": phone.group(1) if phone else "",
                    "address": address.group(1).strip()[:80] if address else "",
                    "employees": employee.group(1) if employee else "",
                    "has_abnormal": abnormal,
                    "qualified": False,
                }
                try:
                    emp = int(info["employees"]) if info["employees"] else 0
                    info["qualified"] = emp > 20 and not abnormal
                except:
                    pass

                status = "✓" if info["qualified"] else "✗"
                print(f"    {status} 电话:{info['phone'] or '无'} 员工:{info['employees'] or '未知'} 异常:{abnormal}")
                results.append(info)
            else:
                print(f"    [!] 未找到企业链接")
                results.append({"company": company, "error": "未找到企业链接", "qualified": False})

            if i < len(companies):
                await asyncio.sleep(2)

        # 保存结果
        qualified = [r for r in results if r.get("qualified", False)]
        output = {
            "query_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(companies),
            "found": len([r for r in results if "error" not in r]),
            "qualified": len(qualified),
            "results": results,
        }
        RESULTS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
            f.write("企业名称,实际匹配名称,联系电话,地址,员工人数,是否有异常\n")
            for r in qualified:
                actual = r.get('actual_name', r['company'])
                f.write(f"{r['company']},{actual},{r['phone']},{r['address']},{r['employees']},{r['has_abnormal']}\n")

        print(f"\n{'='*50}")
        print(f"完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print("="*50)
        
        print("\n浏览器保持打开，输入'退出'关闭...")
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
