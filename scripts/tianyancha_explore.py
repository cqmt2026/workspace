#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查排查 - 详细分析页面结构"""
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
            print("[!] 未登录，请手动登录后回车继续")
            input()
        
        print("\n[2] 搜索企业...")
        # 使用搜索框
        await page.evaluate(f"""() => {{
            const inputs = document.querySelectorAll('input');
            for (const input of inputs) {{
                const ph = (input.placeholder || '').toLowerCase();
                if (ph.includes('search') || ph.includes('公司')) {{
                    input.value = '{COMPANY}';
                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return;
                }}
            }}
        }}""")
        await asyncio.sleep(1)
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        
        print(f"    URL: {page.url}")
        print(f"    Title: {await page.title()}")
        
        # 截图
        await page.screenshot(path="C:/Users/Administrator/.openclaw/workspace/排查_搜索页.png", full_page=True)
        print("    截图: 排查_搜索页.png")
        
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
        
        # 分类统计
        company_links = [l for l in all_links if '/company/' in l['href']]
        search_links = [l for l in all_links if '/search?' in l['href']]
        
        print(f"    /company/ 链接: {len(company_links)} 个")
        print(f"    /search? 链接: {len(search_links)} 个")
        
        print("\n    所有链接预览:")
        for link in all_links[:30]:
            print(f"      [{link['index']:3d}] {link['text'][:35]:35} | {link['href'][:50]}")
        
        print("\n[4] 查找包含'重庆恒重'的文本...")
        text_content = await page.evaluate("""() => {
            const result = [];
            document.querySelectorAll('*').forEach((el, i) => {
                if (i < 200) {
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
            print(f"      <{item['tag']}> class={item['class']}: {item['text']}")
        
        print("\n[5] 检查搜索结果容器...")
        containers = await page.evaluate("""() => {
            const result = [];
            const selectors = [
                '.search-result', '.result-list', '.company-list', 
                '.list-item', '.card', '[class*="search"]',
                '[class*="result"]', '[class*="list"]'
            ];
            selectors.forEach(sel => {
                const elements = document.querySelectorAll(sel);
                if (elements.length > 0) {
                    result.push({
                        selector: sel,
                        count: elements.length,
                        first_html: elements[0].outerHTML.substring(0, 300)
                    });
                }
            });
            return result;
        }""")
        
        print(f"    找到 {len(containers)} 个容器:")
        for c in containers:
            print(f"      {c['selector']}: {c['count']} 个元素")
            print(f"        HTML: {c['first_html'][:150]}...")
        
        print("\n[6] 获取页面完整文本...")
        full_text = await page.evaluate("() => document.body.innerText")
        print(f"    文本长度: {len(full_text)} 字符")
        
        # 查找关键信息
        keywords = ['重庆恒重', '恒重机械', '电话', '地址', '注册']
        for kw in keywords:
            if kw in full_text:
                idx = full_text.find(kw)
                print(f"    '{kw}' 位置 {idx}: ...{full_text[max(0,idx-20):idx+50]}...")
        
        print("\n" + "="*60)
        print("排查完成！浏览器保持打开，可以手动查看")
        print("输入'退出'关闭浏览器...")
        
        while True:
            try:
                inp = input("> ")
                if inp.strip().lower() in ['退出', 'exit']:
                    break
            except EOFError:
                break
        
        await browser.close()

asyncio.run(main())
