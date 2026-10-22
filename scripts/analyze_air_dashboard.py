#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析Air-Quality-Dashboard项目"""
import urllib.request
import json
import ssl
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_github_api(path):
    """获取GitHub API数据"""
    url = f'https://api.github.com{path}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def main():
    repo = 'Akajiaku11/Air-Quality-Dashboard-Project'
    
    print('=' * 70)
    print(f'分析项目: {repo}')
    print('=' * 70)
    
    # 1. 获取仓库基本信息
    print('\n【1. 仓库基本信息】')
    repo_info = fetch_github_api(f'/repos/{repo}')
    if 'error' in repo_info:
        print(f'错误: {repo_info["error"]}')
        return
    
    print(f"Stars: {repo_info.get('stargazers_count')}")
    print(f"Forks: {repo_info.get('forks_count')}")
    print(f"Language: {repo_info.get('language')}")
    print(f"Description: {repo_info.get('description', 'N/A')}")
    print(f"Created: {repo_info.get('created_at')}")
    print(f"Updated: {repo_info.get('updated_at')}")
    license_info = repo_info.get('license')
    print(f"License: {license_info.get('spdx_id', 'N/A') if license_info else 'N/A'}")
    print(f"Size: {repo_info.get('size')} KB")
    print(f"Open Issues: {repo_info.get('open_issues_count')}")
    
    # 2. 获取文件结构
    print('\n【2. 文件结构】')
    tree = fetch_github_api(f'/repos/{repo}/git/trees/main?recursive=1')
    if 'error' not in tree:
        files = [item['path'] for item in tree.get('tree', []) if item['type'] == 'blob']
        dirs = set([os.path.dirname(f) for f in files if os.path.dirname(f)])
        
        print(f'总文件数: {len(files)}')
        print(f'目录结构:')
        for d in sorted(dirs)[:20]:
            print(f'  /{d}')
        
        print(f'\n主要文件:')
        for f in sorted(files):
            if f.endswith(('.py', '.js', '.html', '.json', '.md', '.yml', '.env')):
                print(f'  {f}')
    else:
        print(f'获取文件结构失败: {tree.get("message", "unknown error")}')
    
    # 3. 获取README
    print('\n【3. README内容】')
    readme = fetch_github_api(f'/repos/{repo}/readme')
    if 'content' in readme:
        import base64
        content = base64.b64decode(readme['content']).decode('utf-8', errors='ignore')
        print(content[:3000])
    else:
        print(f'获取README失败: {readme.get("message", "unknown")}')
    
    # 4. 获取issues
    print('\n【4. 最近Issues】')
    issues = fetch_github_api(f'/repos/{repo}/issues?state=all&per_page=5')
    if 'error' not in issues:
        for issue in issues[:5]:
            print(f"  [{issue['state']}] #{issue['number']}: {issue['title']}")
    else:
        print(f'获取Issues失败: {issues.get("message", "unknown")}')
    
    # 5. 获取contributors
    print('\n【5. Contributors】')
    contributors = fetch_github_api(f'/repos/{repo}/contributors?per_page=5')
    if 'error' not in contributors:
        for c in contributors[:5]:
            print(f"  @{c['login']} - {c['contributions']} commits")
    else:
        print(f'获取Contributors失败: {contributors.get("message", "unknown")}')

if __name__ == "__main__":
    main()
