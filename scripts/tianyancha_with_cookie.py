#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天眼查查询 - 支持Cookie持久化"""
import asyncio
import json
import os
import re
import time
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path(__file__).parent.parent / "tianyancha_cookies.json"
RESULTS_FILE = Path(__file__).parent.parent / "tianyancha_result.json"
CSV_FILE = Path(__file__).parent.parent / "tianyancha_result.csv"

async def load_cookies():
    """加载已保存的Cookie"""
    if COOKIE_FILE.exists():
        try:
            with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

async def save_cookies(context):
    """保存Cookie到文件"""
    cookies = await context.cookies("https://www.tianyancha.com")
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"[+] Cookie已保存到: {COOKIE_FILE}")

async def check_login_status(page):
    """检查登录状态"""
    url = page.url
    title = await page.title()
    
    # 未登录状态
    if "login" in url.lower() or "登录" in title:
        return False
    
    # 已登录状态
    if "tianyancha.com" in url and "login" not in url.lower():
        return True
    
    return False

async def search_company(page, company_name):
    """搜索单个企业"""
    # 回首页
    await page.goto("https://www.tianyancha.com", wait_until="networkidle")
    await asyncio.sleep(2)
    
    # 填入搜索词
    await page.evaluate(f"""() => {{
        const inputs = document.querySelectorAll('input');
        for (const input of inputs) {{
            const ph = (input.placeholder || '').toLowerCase();
            if (ph.includes('search') || ph.includes('公司')) {{
                input.value = '{company_name}';
                input.dispatchEvent(new Event('input', {{bubbles: true}}));
                return;
            }}
        }}
    }}""")
    await asyncio.sleep(1)
    
    # 按Enter
    await page.keyboard.press("Enter")
    await asyncio.sleep(4)
    
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
    
    if not links:
        return None
    
    # 进入详情页
    await page.goto(f"https://www.tianyancha.com{links[0]['href']}", wait_until="networkidle")
    await asyncio.sleep(3)
    
    # 提取信息
    text = await page.evaluate("() => document.body.innerText")
    
    phone = re.search(r'电话[：:]\s*(\d{3,4}[-]?\d{7,8})', text)
    address = re.search(r'地址[：:]\s*([^\n]+)', text)
    employee = re.search(r'参保人数[：:]\s*(\d+)', text)
    abnormal = '经营异常' in text
    
    return {
        "company": company_name,
        "phone": phone.group(1) if phone else "",
        "address": address.group(1).strip()[:80] if address else "",
        "employees": employee.group(1) if employee else "",
        "has_abnormal": abnormal,
        "qualified": False
    }

async def main():
    print("=" * 60)
    print("天眼查批量查询工具（带Cookie持久化）")
    print("=" * 60)
    
    # 加载已有Cookie
    saved_cookies = await load_cookies()
    print(f"\n[1] Cookie状态: {'已加载 {len(saved_cookies)} 个Cookie' if saved_cookies else '无保存Cookie'}")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        
        # 创建上下文（如果有Cookie则注入）
        if saved_cookies:
            context = await browser.new_context(storage_state={"cookies": saved_cookies, "origins": []})
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        
        # 访问天眼查
        print("\n[2] 打开天眼查...")
        await page.goto("https://www.tianyancha.com", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 检查登录状态
        logged_in = await check_login_status(page)
        
        if not logged_in:
            print("\n" + "=" * 60)
            print("需要登录！请在浏览器中完成登录")
            print("登录方式：手机号+验证码 或 微信扫码")
            print("登录完成后，在此终端输入 '完成' 并按回车")
            print("=" * 60)
            print()
            
            # 等待用户登录
            while not logged_in:
                await asyncio.sleep(2)
                logged_in = await check_login_status(page)
                
                if logged_in:
                    print("\n[+] 检测到登录成功！")
                    print("[+] 输入 '完成' 保存Cookie并继续...")
                    
                    try:
                        user_input = input("> ")
                        if user_input.strip().lower() in ['完成', 'ok', 'done']:
                            # 保存Cookie
                            await save_cookies(context)
                            print("[+] Cookie已保存，开始查询...")
                            break
                        else:
                            print("[-] 输入无效，请重新输入 '完成'")
                    except EOFError:
                        print("\n[-] 无法读取输入，继续查询...")
                        await save_cookies(context)
                        break
        else:
            print("[+] 检测到已登录状态")
        
        # 查询企业
        companies = [
            "北京字节跳动科技有限公司",
            "上海哔哩哔哩科技有限公司",
            "深圳市腾讯计算机系统有限公司",
            "杭州阿里巴巴广告有限公司",
            "网易有限公司"
        ]
        
        print(f"\n[3] 开始查询 {len(companies)} 家企业...")
        
        results = []
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] {company}")
            
            try:
                info = await search_company(page, company)
                if info:
                    # 判断是否符合条件
                    try:
                        emp = int(info["employees"]) if info["employees"] else 0
                        info["qualified"] = emp > 20 and not info["has_abnormal"]
                    except:
                        info["qualified"] = False
                    
                    status = "[OK]" if info["qualified"] else "[X]"
                    print(f"    {status} 电话:{info['phone'] or '无'} 员工:{info['employees'] or '未知'} 异常:{info['has_abnormal']}")
                    results.append(info)
                else:
                    print(f"    [X] 未找到企业")
            except Exception as e:
                print(f"    [!] 错误: {str(e)[:50]}")
                results.append({
                    "company": company,
                    "error": str(e)[:100],
                    "qualified": False
                })
            
            # 间隔等待
            if i < len(companies):
                await asyncio.sleep(2)
        
        # 保存结果
        qualified = [r for r in results if r.get("qualified", False)]
        output = {
            "query_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(companies),
            "found": len([r for r in results if "error" not in r]),
            "qualified": len(qualified),
            "results": results
        }
        
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
            f.write("企业名称,联系电话,地址,员工人数,是否有异常\n")
            for r in qualified:
                f.write(f"{r['company']},{r['phone']},{r['address']},{r['employees']},{r['has_abnormal']}\n")
        
        print(f"\n{'='*60}")
        print(f"查询完成: 总{output['total']} 找到{output['found']} 符合{output['qualified']}")
        print(f"结果文件: {RESULTS_FILE}")
        print(f"CSV文件: {CSV_FILE}")
        print("=" * 60)
        
        print("\n[提示] 浏览器将保持打开状态")
        print("[提示] Cookie已保存，下次无需重新登录")
        print("[提示] 输入 '退出' 关闭浏览器\n")
        
        # 保持运行
        while True:
            try:
                user_input = input("> ")
                if user_input.strip().lower() in ['退出', 'exit', 'quit']:
                    print("\n正在关闭...")
                    break
            except EOFError:
                break
        
        await browser.close()
        print("完成！")

if __name__ == "__main__":
    asyncio.run(main())
