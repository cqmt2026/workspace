#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取Dify GitHub文档信息"""
import urllib.request
import json
import ssl
import sys
import os
import base64

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_url(url):
    """获取URL内容"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/vnd.github.v3+json'
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def main():
    repo = 'langgenius/dify'
    
    print('=' * 70)
    print('Dify 项目文档调研')
    print('=' * 70)
    
    # 1. 获取仓库基本信息
    print('\n【1. 仓库基本信息】')
    repo_info = fetch_url(f'https://api.github.com/repos/{repo}')
    if 'error' in repo_info:
        print(f'错误: {repo_info["error"]}')
        return
    
    print(f"名称: {repo_info.get('full_name')}")
    print(f"Stars: {repo_info.get('stargazers_count')}")
    print(f"Forks: {repo_info.get('forks_count')}")
    print(f"语言: {repo_info.get('language')}")
    print(f"描述: {repo_info.get('description', 'N/A')}")
    print(f"创建时间: {repo_info.get('created_at')}")
    print(f"最后更新: {repo_info.get('updated_at')}")
    print(f"链接: {repo_info.get('html_url')}")
    print(f"Topics: {', '.join(repo_info.get('topics', []))}")
    
    # 2. 获取README
    print('\n【2. README内容】')
    readme = fetch_url(f'https://api.github.com/repos/{repo}/readme')
    if 'content' in readme:
        content = base64.b64decode(readme['content']).decode('utf-8', errors='ignore')
        print(content[:5000])
    else:
        print(f'获取失败: {readme.get("message", "unknown")}')
    
    # 3. 获取文件结构
    print('\n【3. 目录结构】')
    tree = fetch_url(f'https://api.github.com/repos/{repo}/contents')
    if 'error' not in tree:
        for item in tree[:20]:
            type_icon = '[DIR]' if item['type'] == 'dir' else '[FILE]'
            print(f"  {type_icon} {item['name']}")
    else:
        print(f'获取失败: {tree.get("message", "unknown")}')
    
    # 4. 获取主要分支
    print('\n【4. 分支信息】')
    branches = fetch_url(f'https://api.github.com/repos/{repo}/branches')
    if 'error' not in branches:
        for b in branches[:5]:
            print(f"  - {b['name']}")
    else:
        print(f'获取失败: {branches.get("message", "unknown")}')
    
    # 5. 保存完整信息
    output_file = r'C:\Users\Administrator\.openclaw\workspace\memory\商业案例调研\dify_info.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'repo': repo_info,
            'readme': readme.get('content', ''),
            'structure': tree if 'error' not in tree else [],
            'branches': branches if 'error' not in branches else []
        }, f, indent=2, ensure_ascii=False)
    
    print(f'\n完整信息已保存至: {output_file}')
    
    # 6. 获取部署文档
    print('\n【5. 部署文档预览】')
    deploy_doc = fetch_url(f'https://api.github.com/repos/{repo}/contents/web/docker')
    if 'error' not in deploy_doc:
        print('Docker部署文件:')
        for item in deploy_doc[:10]:
            print(f"  - {item['name']}")
    else:
        # 尝试根目录docker文件
        docker_files = fetch_url(f'https://api.github.com/repos/{repo}/contents')
        if 'docker' in str(docker_files):
            print('找到Docker相关文件')

if __name__ == "__main__":
    main()
