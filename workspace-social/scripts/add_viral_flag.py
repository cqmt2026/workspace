import json
from pathlib import Path

f = Path('data/爆款深度学习/training_data.json')
data = json.loads(f.read_text(encoding='utf-8'))

VIRAL_THRESHOLD = {'views': 10000, 'likes': 500, 'comments': 100, 'shares': 50}
def is_viral(a):
    return (a.get('views', 0) >= VIRAL_THRESHOLD['views'] or
            a.get('likes', 0) >= VIRAL_THRESHOLD['likes'] or
            a.get('comments', 0) >= VIRAL_THRESHOLD['comments'] or
            a.get('shares', 0) >= VIRAL_THRESHOLD['shares'])

for a in data['data']:
    a['is_viral'] = is_viral(a)

f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('Done, is_viral added to all articles')
print('Viral count: ' + str(sum(1 for a in data['data'] if a['is_viral'])))