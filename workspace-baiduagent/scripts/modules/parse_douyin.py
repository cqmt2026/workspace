# -*- coding: utf-8 -*-
"""解析抖音视频页面内嵌JSON"""
import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

videoid = "7675329107789466906"
# 用新的分享链接带完整签名参数可能过期，用基础解析接口
url = f"https://www.iesdouyin.com/share/video/{videoid}/"

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://www.douyin.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

r = requests.get(url, headers=headers, timeout=20)
print("状态码:", r.status_code)
text = r.text
print("HTML长度:", len(text))

# 尝试提取RENDER_DATA（老接口）或__pace_f或内嵌JSON
# 方式1: RENDER_DATA (base64)
m = re.search(r'id="RENDER_DATA"[^>]*>([^<]+)<', text)
if m:
    import base64, urllib.parse
    b64 = m.group(1)
    try:
        decoded = urllib.parse.unquote(base64)
        data = json.loads(decoded)
        # 递归找视频标题和描述
        def find(ob, key):
            results = []
            if isinstance(ob, dict):
                for k, v in ob.items():
                    if k == key:
                        results.append(v)
                    results.extend(find(v, key))
            elif isinstance(ob, list):
                for item in ob:
                    results.extend(find(item, key))
            return results
        for k in ['desc', 'title', 'C']:
            found = find(data, k)
            if found:
                print(f"找到 {k}:", found[:5])
        print("RAW:", decoded[:3000])
    except Exception as e:
        print("RENDER_DATA解析失败:", e)
        print("原始:", b64[:500])

# 方式2: 直接抓取 __pace_f / window._ROUTER_DATA
for key in ['__pace_f', '_ROUTER_DATA', 'window.__INITIAL_STATE__']:
    idx = text.find(key)
    if idx != -1:
        print(f"找到标记: {key} at {idx}")
        print(text[idx:idx+1500])

# 方式3: 找 desc / 视频描述
m2 = re.findall(r'"desc"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
if m2:
    print("\ndesc字段:", m2[:5])
m3 = re.findall(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
if m3:
    print("title字段:", m3[:5])
