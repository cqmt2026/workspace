#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查批量查询 - 改进版"""
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

        # 访问天眼查
        print("[1] 打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        print(f"    URL: {page.url}")
        print(f"    Title: {await page.title()}")

        if "login" in page.url.lower():
            print("[!] Cookie已过期")
            await browser.close()
            return
        print("[+] 登录正常")

        results = []
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] {company}")

            # 回首页
            await page.goto("https://www.tianyancha.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # JS填入搜索词
            filled = await page.evaluate(f"""() => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = (input.placeholder || '').toLowerCase();
                    if (ph.includes('search') || ph.includes('公司')) {{
                        input.value = '{company}';
                        input.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return true;
                    }}
                }}
                return false;
            }}""")
            print(f"    搜索框: {'找到' if filled else '未找到'}")
            await asyncio.sleep(0.5)

            # 按Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            # 截图查看
            await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/s{company[:4]}.png")
            print(f"    截图: s{company[:4]}.png")
            print(f"    URL: {page.url}")

            # 获取页面文本检查
            title = await page.title()
            text = await page.evaluate("() => document.body.innerText")
            print(f"    标题: {title}")
            print(f"    页面包含'{company}': {company in text}")

            # 尝试多种查找方式
            # 方式1: 直接构造搜索URL
            search_url = f"https://www.tianyancha.com/search?key={company}"
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            print(f"    直接搜索URL: {page.url}")

            # 截图
            await page.screenshot(path=f"C:/Users/Administrator/.openclaw/workspace/s2{company[:4]}.png")

            # 查找企业链接
            links = await page.evaluate("""() => {
                const result = [];
                document.querySelectorAll('a').forEach(a => {
                    const text = a.textContent.trim();
                    const href = a.getAttribute('href') || '';
                    if (text.length > 5 && href.includes('/company/') && !href.includes('/search')) {
                        result.push({text: text.substring(0, 40), href});
                    }
                });
                return result.slice(0, 5);
            }""")
            print(f"    找到 {len(links)} 个链接")
            for l in links[:3]:
                print(f"      - {l['text']}: {l['href'][:60]}")

            if not links:
                # 尝试另一种方式
                links = await page.evaluate("""() => {
                    const result = [];
                    document.querySelectorAll('a').forEach(a => {
                        const href = a.getAttribute('href') || '';
                        if (href.includes('/company/') && !href.includes('/search')) {
                            const text = a.textContent.trim().substring(0, 40);
                            result.push({text, href});
                        }
                    });
                    return result.slice(0, 5);
                }""")
                print(f"    备用查找: 找到 {len(links)} 个链接")

            if links:
                # 进入详情页
                detail_url = f"https://www.tianyancha.com{links[0]['href']}"
                await page.goto(detail_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                print(f"    详情页: {page.url[:60]}")

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
                print(f"    [!] 未找到企业")
                results.append({"company": company, "error": "未找到企业", "qualified": False})

            # 间隔
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
            f.write("企业名称,联系电话,地址,员工人数,是否有异常\n")
            for r in qualified:
                f.write(f"{r['company']},{r['phone']},{r['address']},{r['employees']},{r['has_abnormal']}\n")

        print(f"\n{'='*50}")
        print(f"完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print("="*50)
        
        print("\n浏览器保持打开，输入'退出'关闭...")
        while True:
            try:
                inp = input("> ")
                if inp.strip().lower() in ['退出', 'exit']:
                    break
            except:
                break
        await browser.close()
        print("完成！")

asyncio.run(main())
