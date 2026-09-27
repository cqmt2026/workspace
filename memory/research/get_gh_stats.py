import urllib.request, json, sys

repos = [
    'facebookresearch/mbrl-lib',
    'instadeepai/mbrl',
    'katerakelly/pets',
    'nicklashansen/plan2explore',
    'MishaLaskin/mworld',
]

results = {}
for repo in repos:
    try:
        r = urllib.request.urlopen(f'https://api.github.com/repos/{repo}')
        d = json.loads(r.read())
        results[repo] = {
            'stars': d['stargazers_count'],
            'forks': d['forks_count'],
            'pushed': d['pushed_at'],
            'description': d.get('description', '')
        }
    except Exception as e:
        results[repo] = {'error': str(e)}

with open(r'C:\Users\Administrator\.openclaw\workspace\memory\research\gh_stats.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print('done')