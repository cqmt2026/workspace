import json
data = json.load(open(r'C:\Users\Administrator\.openclaw\workspace\shared-knowledge\热点选题库\全网热点_2026-08-20.json', encoding='utf-8'))
topics = data.get('hot_topics', [])
print(f'共{len(topics)}条热点:')
for i, t in enumerate(topics):
    src = t.get('source', '')
    tag = t.get('tag', '')
    print(f'  {i+1}. {t["title"]} [{src}] {tag}')
print(f'\n抓取时间: {data.get("crawl_time", "")}')
print(f'数据源: {data.get("sources", [])}')
