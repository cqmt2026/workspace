import requests, json, sys, os, io
from datetime import datetime

API_BASE = "https://60s.viki.moe/v2"
OUTPUT_DIR = r"C:\Users\Administrator\.openclaw\workspace\shared-knowledge\热点选题库"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 抓取所有平台
result = {}
platforms = ["weibo", "zhihu", "douyin", "baidu_hot", "bili"]
for platform in platforms:
    url = f"{API_BASE}/{platform}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", [])
            result[platform] = items[:10]
            print(f"  [{platform}] {len(items)}条 -> 取前{len(items[:10])}条")
        else:
            result[platform] = []
            print(f"  [{platform}] HTTP {r.status_code}")
    except Exception as e:
        result[platform] = []
        print(f"  [{platform}] ERROR: {e}")

today = datetime.now().strftime("%Y-%m-%d")
out_file = os.path.join(OUTPUT_DIR, f"全网热点_{today}.json")

# 构建输出结构：保留原始platforms，同时生成hot_topics列表
hot_topics = []
for platform, items in result.items():
    for item in items:
        title = item.get("title", "")
        if not title:
            continue
        hot_topics.append({
            "title": title,
            "source": platform,
            "hot_value": item.get("hot_value") or item.get("hot_value_desc", ""),
            "link": item.get("link", ""),
        })

output = {
    "date": today,
    "time": datetime.now().strftime("%H:%M:%S"),
    "platforms": result,
    "hot_topics": hot_topics,
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

sys.stdout.reconfigure(encoding='utf-8')
print(f"\n抓取到 {len(hot_topics)} 条热点")
print(f"已保存: {out_file}")
for t in hot_topics[:15]:
    print(f"  - [{t['source']}] {t['title']}")

# 保存Supermemory
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'memory'))
    from memory_adapter import save_topic
    for t in hot_topics:
        save_topic(f"[{t['source']}] {t['title']}", source='web-hot')
    print("  [Supermemory] 已保存")
except Exception as e:
    print(f"  [Supermemory] 写入失败: {e}")
