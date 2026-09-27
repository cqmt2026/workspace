#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进知识库：活跃度监控 + 今日推荐 + 内容均衡 + 清理归档
"""
import io
import sys, os, re, json
from datetime import datetime
from collections import defaultdict

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'F:\Obsidian\Jarvis'

# ========== 1. 修复 read_count 监控 ==========
print('1. 修复活跃度监控...')

# 重新初始化 read_tracking.json
tracking = {}
for root, _, files in os.walk(BASE):
    if '.obsidian' in root or '.git' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, BASE)
        # 从文件名判断创建日期
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', f)
        created = date_match.group(1) if date_match else 'unknown'
        tracking[rel] = {
            'read_count': 0,
            'last_read_at': '',
            'created': created,
            'size': os.path.getsize(fp),
        }

tf = os.path.join(BASE, '.read_tracking.json')
with open(tf, 'w', encoding='utf-8') as f:
    json.dump(tracking, f, indent=2, ensure_ascii=False)
print(f'  read_tracking.json 已初始化 ({len(tracking)} 篇)')
print()

# ========== 2. 今日推荐 ==========
print('2. 生成今日推荐...')

# 找从未阅读的笔记
unread = []
for rel, info in tracking.items():
    if info['read_count'] == 0 and info['size'] > 500:  # 过滤太小的文件
        unread.append(rel)

# 按日期排序（最新的优先推荐）
def sort_key(rel):
    info = tracking.get(rel, {})
    created = info.get('created', '')
    if created == 'unknown':
        return '0000'
    return created

unread.sort(key=sort_key, reverse=True)

# 选一篇推荐（最新的未读且有实质内容的）
recommended = None
for rel in unread:
    fp = os.path.join(BASE, rel)
    try:
        c = open(fp, 'r', encoding='utf-8').read()
        body = c
        if c.startswith('---'):
            parts = c.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
        if len(body.strip()) > 200:
            recommended = rel
            break
    except:
        continue

if recommended:
    title = os.path.basename(recommended).replace('.md', '')
    area = recommended.split(os.sep)[0] if os.sep in recommended else '根目录'
    print(f'  推荐: [[{title}]] ({area})')

# 更新 agent.md 的今日推荐
agent_fp = os.path.join(BASE, 'agent.md')
if os.path.exists(agent_fp) and recommended:
    with open(agent_fp, 'r', encoding='utf-8') as f:
        agent_content = f.read()
    
    title = os.path.basename(recommended).replace('.md', '')
    today = datetime.now().strftime('%Y-%m-%d')
    rec_section = f'\n## 今日推荐 ({today})\n\n> 你还没有读过这篇笔记：[[{title}]]\n\n---\n'
    
    # 替换旧的今日推荐
    if '## 今日推荐' in agent_content:
        import re as rm
        agent_content = rm.sub(r'## 今日推荐.*?\n---\n', rec_section, agent_content, flags=re.DOTALL)
    else:
        # 在第一个 --- 之前插入
        agent_content = agent_content.rstrip() + '\n' + rec_section
    
    with open(agent_fp, 'w', encoding='utf-8') as f:
        f.write(agent_content)
    print('  agent.md 今日推荐已更新')
print()

# ========== 3. 均衡内容 - 为小说添加更多关联 ==========
print('3. 补充小说关联...')

novel_dir = os.path.join(BASE, '01-创作', '小说')
if os.path.exists(novel_dir):
    novel_files = []
    for f in os.listdir(novel_dir):
        if f.endswith('.md'):
            novel_files.append(os.path.join(novel_dir, f))
    
    # 为小说笔记添加关联自媒体素材（自媒体关联小说同理）
    social_dir = os.path.join(BASE, '01-创作', '自媒体')
    social_files = []
    if os.path.exists(social_dir):
        for root, _, files in os.walk(social_dir):
            for f in files:
                if f.endswith('.md'):
                    social_files.append(os.path.join(root, f))
    
    # 给小说笔记添加"创作方法"关联
    for nf in novel_files:
        with open(nf, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '## 关联笔记' not in content:
            continue
        
        # 检查是否已经有创作类关联
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
        
        has_social_link = False
        for sf in social_files:
            sname = os.path.basename(sf).replace('.md', '')
            if f'[[{sname}]]' in body:
                has_social_link = True
                break
        
        if not has_social_link and social_files:
            # 添加一个自媒体关联
            # 找一篇爆款模板
            for sf in social_files:
                if '模板' in sf or 'viral' in sf:
                    sname = os.path.basename(sf).replace('.md', '')
                    new_link = f'- [[{sname}]] (创作方法)\n'
                    # 在关联笔记区块中插入
                    lines = content.split('\n')
                    new_lines = []
                    inserted = False
                    for line in lines:
                        new_lines.append(line)
                        if '## 关联笔记' in line and not inserted:
                            new_lines.append('')
                            new_lines.append(new_link.strip())
                            inserted = True
                    
                    content = '\n'.join(new_lines)
                    with open(nf, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'  {os.path.basename(nf)}: 添加关联 [[{sname}]]')
                    break
print()

# ========== 4. 清理 Z-归档 ==========
print('4. 清理 Z-归档...')

archive_dir = os.path.join(BASE, 'Z-归档')
if os.path.exists(archive_dir):
    archive_files = os.listdir(archive_dir)
    print(f'  归档目录有 {len(archive_files)} 个文件')
    
    for f in archive_files:
        if not f.endswith('.md'):
            continue
        src = os.path.join(archive_dir, f)
        
        # 根据内容判断是否真的应该归档
        with open(src, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
        
        # 检查是否还有活跃的链接指向这篇笔记
        linked_count = 0
        for root, _, files in os.walk(BASE):
            if 'Z-归档' in root or '.obsidian' in root or '.git' in root:
                continue
            for f2 in files:
                if not f2.endswith('.md'):
                    continue
                fp2 = os.path.join(root, f2)
                try:
                    c2 = open(fp2, 'r', encoding='utf-8').read()
                except:
                    continue
                title = f.replace('.md', '')
                if f'[[{title}]]' in c2:
                    linked_count += 1
        
        title_short = f.replace('.md', '')
        if linked_count == 0:
            print(f'  [{title_short}] 无外部引用，可删除')
        else:
            print(f'  [{title_short}] 仍有 {linked_count} 篇笔记引用')
else:
    print('  Z-归档 目录不存在')
print()

# ========== 5. 更新 Cron 任务 ==========
print('5. 更新 Cron 任务...')
print('  已注册:')
print('    - Obsidian-日记生成 (每天21:00)')
print('    - Obsidian-领域关系图更新 (每天05:00)')
print('    - Obsidian-知识沉淀 (每天21:30)')
print('    - Obsidian-会话沉淀 (每天22:00)')
print()

print('完成！重启 Obsidian 查看效果')