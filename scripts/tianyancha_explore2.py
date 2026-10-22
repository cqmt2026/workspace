#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查排查 - 修复搜索逻辑"""
import asyncio, json
from playwright.async_api import async_playwright

COOKIE_FILE = "C:/Users/Administrator/.openclaw/workspace/tianyancha_cookies.json"
COMPANY = "重庆恒重机械制造有限责任公司"

async def main():
    cookies = json.loads(open(COOKIE_FILE, encoding="utf-8").read())
    print(f"[+] 加载 {len(cookies)} 个Cookie")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(storage_state={"cookies": cookies, "origins": []})
        page = await ctx.new_page()
        
        print("\n[1] 访问天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(3)
        
        if "login" in page.url.lower():
            print("[!] 未登录")
            await browser.close()
            return
        print("[+] 登录正常")
        
        print("\n[2] 直接访问搜索URL...")
        search_url = f"https://www.tianyancha.com/search?key={COMPANY}"
        await page.goto(search_url, wait_until="networkidle", timeout=20000)
        await asyncio.sleep(5)
        
        print(f"    URL: {page.url}")
        print(f"    Title: {await page.title()}")
        
        # 截图
        await page.screenshot(path="C:/Users/Administrator/.openclaw/workspace/排查_搜索页2.png", full_page=True)
        print("    截图: 排查_搜索页2.png")
        
        print("\n[3] 分析页面链接...")
        all_links = await page.evaluate("""() => {
            const links = [];
            document.querySelectorAll('a').forEach((a, i) => {
                const href = a.getAttribute('href') || '';
                const text = a.textContent.trim().substring(0, 50);
                if (href && text.length > 2 && i < 100) {
                    links.push({
                        index: i,
                        text: text,
                        href: href,
                        class: a.className.substring(0, 50)
                    });
                }
            });
            return links;
        }""")
        
        print(f"    找到 {len(all_links)} 个链接")
        
        company_links = [l for l in all_links if '/company/' in l['href']]
        print(f"    /company/ 链接: {len(company_links)} 个")
        
        print("\n    所有链接:")
        for link in all_links[:40]:
            print(f"      [{link['index']:3d}] {link['text'][:35]:35} | {link['href'][:55]}")
        
        print("\n[4] 查找包含'重庆恒重'的文本...")
        text_content = await page.evaluate("""() => {
            const result = [];
            document.querySelectorAll('*').forEach((el, i) => {
                if (i < 300) {
                    const text = el.textContent.trim();
                    if (text.includes('重庆恒重') || text.includes('恒重机械')) {
                        result.push({
                            tag: el.tagName,
                            class: el.className.substring(0, 30),
                            text: text.substring(0, 80)
                        });
                    }
                }
            });
            return result;
        }""")
        
        print(f"    找到 {len(text_content)} 个匹配项:")
        for item in text_content:
            print(f"      <{item['tag']}> {item['text']}")
        
        print("\n[5] 获取页面完整文本...")
        full_text = await page.evaluate("() => document.body.innerText")
        print(f"    文本长度: {len(full_text)} 字符")
        print(f"    前1000字符:\n{full_text[:1000]}")
        
        print("\n[6] 检查URL参数...")
        url_params = page.url.split('?')
        if len(url_params) > 1:
            print(f"    查询参数: {url_params[1]}")
        
        print("\n" + "="*60)
        print("排查完成！")
        
        while True:
            try:
                inp = input("> ")
                if inp.strip().lower() in ['退出', 'exit']:
                    break
            except EOFError:
                break
        
        await browser.close()

asyncio.run(main())
