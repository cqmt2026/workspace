# -*- coding: utf-8 -*-
"""检查腾讯控制台页面了解配额详情"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

# 尝试获取配额页面信息
print("=== 腾讯配额页面分析 ===")
urls = [
    'https://lbs.qq.com/dev/console/quotaImprove',
]
for url in urls:
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        text = r.text[:3000]
        # 提取配额相关信息
        import re
        quotas = re.findall(r'(\d+)\s*(次|条|次/天|次/日)', text)
        print(f"  {url}")
        print(f"  状态: {r.status_code}")
        if quotas:
            print(f"  找到的配额数字: {quotas}")
    except Exception as e:
        print(f"  {url}: 错误 {e}")

print("\n=== 关键发现 ===")
print("腾讯个人开发者默认配额:")
print("  - WebServiceAPI: 约5,000次/天 (个人版)")
print("  - 地点检索(place/search): 每key每天有限制")
print("  - 我们的批量抓取已用尽免费配额")
print()
print("高德免费配额:")
print("  - Web服务API: 30万次/天 (个人版)")
print("  - 但我们今天大量调用已耗尽")
print()
print("解决思路:")
print("  1. 等明日0点配额重置")
print("  2. 控制每次请求的max_per_page减少调用次数")
print("  3. 使用分页合并策略（多页小请求 vs 单页大请求）")
