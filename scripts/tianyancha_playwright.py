#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天眼查批量查询 - Playwright 版本
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

# 配置
TIANYANCHA_URL = "https://www.tianyancha.com"
OUTPUT_FILE = "tianyancha_pw_result.json"
SEARCH_DELAY = 3  # 搜索间隔（秒）

# 测试用企业列表
TEST_COMPANIES = [
    "北京字节跳动科技有限公司",
    "上海哔哩哔哩科技有限公司",
    "深圳市腾讯计算机系统有限公司"
]

async def search_company(page, company_name: str) -> dict:
    """搜索单个企业"""
    result = {
        "company": company_name,
        "found": False,
        "data": None,
        "error": None
    }
    
    try:
        # 等待页面加载
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        
        # 检查是否已登录
        current_url = page.url
        if "login" in current_url.lower():
            result["error"] = "未登录或登录已过期"
            return result
        
        # 用JS找到搜索框（更可靠）
        search_js = """
        () => {
            // 方法1: 查找所有input
            const inputs = document.querySelectorAll('input');
            for (const input of inputs) {
                const ph = (input.placeholder || '').toLowerCase();
                if (ph.includes('search') || ph.includes('企业') || ph.includes('公司') || ph.includes('天眼查')) {
                    return {found: true, tag: input.tagName, id: input.id, class: input.className, placeholder: ph};
                }
            }
            // 方法2: 查找第一个visible的input
            for (const input of inputs) {
                const style = window.getComputedStyle(input);
                if (style.display !== 'none' && style.visibility !== 'hidden' && input.offsetParent !== null) {
                    return {found: true, tag: input.tagName, id: input.id, class: input.className, placeholder: input.placeholder};
                }
            }
            return {found: false};
        }
        """
        
        search_info = await page.evaluate(search_js)
        print(f"  Search box info: {search_info}")
        
        if not search_info.get('found'):
            result["error"] = "未找到搜索框"
            return result
        
        # 获取所有input元素
        inputs = page.locator('input:visible')
        count = await inputs.count()
        print(f"  Found {count} visible inputs")
        
        # 尝试找到搜索框
        search_input = None
        for i in range(min(count, 10)):
            input_placeholder = await inputs.nth(i).get_attribute('placeholder') or ''
            input_class = await inputs.nth(i).get_attribute('class') or ''
            if 'search' in input_placeholder.lower() or 'search' in input_class.lower() or 'input' in input_class.lower():
                search_input = inputs.nth(i)
                print(f"  Found search input at index {i}")
                break
        
        if not search_input:
            # 使用第一个visible input作为备选
            search_input = inputs.first
            print(f"  Using first input as search box")
        
        # 输入企业名称
        await search_input.fill(company_name)
        await asyncio.sleep(0.5)
        
        # 按回车搜索
        await search_input.press("Enter")
        
        # 等待搜索结果
        await asyncio.sleep(SEARCH_DELAY)
        
        # 获取结果页面信息
        page_title = await page.title()
        page_content = await page.content()
        
        # 检查是否找到企业信息
        company_found = company_name in page_content or company_name in page_title
        
        if company_found:
            result["found"] = True
            result["data"] = {
                "page_title": page_title,
                "url": page.url,
                "content_preview": page_content[:500]
            }
        else:
            result["error"] = "未在结果中找到企业信息"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

async def main():
    print("=" * 60)
    print("Tianyancha Query Test - Playwright")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器（有头模式，方便查看）
        print("\n[1] Starting browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 访问天眼查
        print(f"\n[2] Opening {TIANYANCHA_URL}...")
        await page.goto(TIANYANCHA_URL, wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 检查登录状态
        print("\n[3] Checking login status...")
        current_url = page.url
        page_title = await page.title()
        print(f"URL: {current_url}")
        print(f"Title: {page_title}")
        
        is_logged_in = "login" not in current_url.lower()
        print(f"Logged in: {is_logged_in}")
        
        if not is_logged_in:
            print("[WARN] Please login manually in the browser window!")
            print("Press Enter when ready to continue...")
            input()
        
        # 批量搜索
        print(f"\n[4] Searching {len(TEST_COMPANIES)} companies...")
        
        all_results = []
        for i, company in enumerate(TEST_COMPANIES, 1):
            print(f"\n--- [{i}/{len(TEST_COMPANIES)}] {company} ---")
            
            result = await search_company(page, company)
            all_results.append(result)
            
            print(f"Found: {result['found']}")
            if result['error']:
                print(f"Error: {result['error']}")
            
            # 间隔等待
            if i < len(TEST_COMPANIES):
                print(f"Waiting {SEARCH_DELAY}s...")
                await asyncio.sleep(SEARCH_DELAY)
        
        # 保存结果
        output = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_companies": len(TEST_COMPANIES),
            "success_count": sum(1 for r in all_results if r["found"]),
            "is_logged_in": is_logged_in,
            "results": all_results
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print("Test Summary")
        print('='*60)
        print(f"Total searched: {output['total_companies']}")
        print(f"Success: {output['success_count']}")
        print(f"Failed: {output['total_companies'] - output['success_count']}")
        print(f"\nResults saved to: {OUTPUT_FILE}")
        
        # 保持浏览器打开10秒查看结果
        print("\nBrowser will close in 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()
    
    print("\nTest complete")

if __name__ == "__main__":
    asyncio.run(main())
