#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每个子系统生成独立的 Mermaid 关系图
嵌入到对应的看板笔记中
"""
import sys, os, re
import io
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'F:\.Obsidian\Jarvis'

# 领域定义
DOMAINS = {
    '投资': {
        'dirs': ['02-投资'],
        'title': '投资策略看板',
        'filename': '投资策略看板.md',
        'max_nodes': 30,
        'exclude_keywords': ['README', 'TEMPLATE', 'COMMIT', 'ADDITIONAL'],
    },
    '创作': {
        'dirs': ['01-创作/小说', '01-创作/自媒体', '01-创作/数学动画'],
        'title': '创作进度看板',
        'filename': '创作进度看板.md',
        'max_nodes': 25,
        'exclude_keywords': [],
    },
}

def get_all_names():
    """获取所有文件名"""
    names = {}
    for root, _, files in os.walk(BASE):
        if '.obsidian' in root or '.git' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                names[f[:-3]] = os.path.relpath(os.path.join(root, f), BASE)
    return names

def build_domain_graph(domain_dir, domain_name, max_nodes=30, exclude_kws=None):
    """为某个领域生成Mermaid关系图"""
    if exclude_kws is None:
        exclude_kws = []
    
    # 收集该领域的笔记
    note_files = {}  # title -> fp
    for d in domain_dir:
        full = os.path.join(BASE, d)
        if not os.path.exists(full):
            continue
        for root, _, files in os.walk(full):
            for f in files:
                if not f.endswith('.md'):
                    continue
                title = f[:-3]
                # 排除系统文档
                if any(kw in title.upper() for kw in exclude_kws):
                    continue
                note_files[title] = os.path.join(root, f)
    
    if not note_files:
        return '暂无笔记'
    
    # 提取笔记间的关系
    all_names = get_all_names()
    links = []  # (from, to)
    
    for title, fp in note_files.items():
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
        
        for link in re.findall(r'\[\[([^\]|#]+)\]\]', body):
            target = link.strip()
            if target in note_files and target != title:
                links.append((title, target))
    
    # 去重
    links = list(set(links))
    
    # 找出最核心的节点（连接数最多的前N个）
    node_degree = {}
    for a, b in links:
        node_degree[a] = node_degree.get(a, 0) + 1
        node_degree[b] = node_degree.get(b, 0) + 1
    
    # 筛选核心节点
    top_nodes = set()
    # 先保证所有有连接的节点都至少出现一次
    for a, b in links:
        top_nodes.add(a)
        top_nodes.add(b)
    
    # 如果节点太多，只保留连接数最多的
    if len(top_nodes) > max_nodes:
        sorted_nodes = sorted(top_nodes, key=lambda n: -node_degree.get(n, 0))
        top_nodes = set(sorted_nodes[:max_nodes])
    
    # 筛选连接
    filtered_links = [(a, b) for a, b in links if a in top_nodes and b in top_nodes]
    
    # 生成Mermaid
    lines = ['```mermaid', 'graph LR']
    
    # 给节点添加别名（显示标题）
    for title in sorted(top_nodes):
        # 缩短显示名
        short = title.replace('_', ' ')
        if len(short) > 20:
            short = short[:17] + '..'
        # 避免特殊字符
        safe_id = title.replace('-', '').replace('_', '').replace('.', '')
        safe_id = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', safe_id)
        if not safe_id:
            safe_id = 'n' + str(hash(title))[:8]
        lines.append(f'    {safe_id}["{short}"]')
    
    # 添加连接
    edge_set = set()
    for a, b in filtered_links:
        safe_a = a.replace('-', '').replace('_', '').replace('.', '')
        safe_a = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', safe_a)
        safe_b = b.replace('-', '').replace('_', '').replace('.', '')
        safe_b = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', safe_b)
        if not safe_a or not safe_b:
            continue
        edge = tuple(sorted([safe_a, safe_b]))
        if edge not in edge_set:
            lines.append(f'    {safe_a} --- {safe_b}')
            edge_set.add(edge)
    
    lines.append('```')
    
    return '\n'.join(lines)


def remove_old_graph_sections(lines):
    """移除所有旧的 ## 关系图谱 区块"""
    result = []
    skip = False
    skip_depth = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        # 检测到 ## 关系图谱 标题
        if line.strip() == '## 关系图谱':
            skip = True
            # 跳过标题行
            i += 1
            continue
        # 如果在跳过模式中，找到下一个同级或更高级别的标题就停止
        if skip:
            # 检查是否是新的 section 标题 (## 或 ###)
            if line.strip().startswith('## '):
                skip = False
                result.append(line)
            elif line.strip().startswith('#') and not line.strip().startswith('##'):
                # 一级标题，结束跳过
                skip = False
                result.append(line)
            else:
                # 跳过当前行
                pass
        else:
            result.append(line)
        i += 1
    return result


def update_board(domain_name, config):
    """更新看板笔记，嵌入Mermaid图"""
    fp = os.path.join(BASE, config['filename'])
    
    if not os.path.exists(fp):
        print(f'  看板文件不存在: {config["filename"]}')
        return
    
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 生成Mermaid图
    mermaid = build_domain_graph(
        config['dirs'], domain_name,
        max_nodes=config.get('max_nodes', 25),
        exclude_kws=config.get('exclude_keywords', [])
    )
    
    lines = content.split('\n')
    
    # 先移除所有旧的 ## 关系图谱 区块
    lines = remove_old_graph_sections(lines)
    
    # 找插入位置：在Dataview查询块之后、最后的分隔线之前
    # 找到第一个```之后和最后一个```之后的位置
    dataview_end = 0
    in_dataview = False
    for i, line in enumerate(lines):
        if '```dataview' in line:
            in_dataview = True
        elif in_dataview and '```' in line:
            dataview_end = i
            in_dataview = False
    
    # 在Dataview区块之后插入关系图
    insert_pos = dataview_end + 1 if dataview_end > 0 else len(lines) - 1
    
    # 构建新内容
    graph_section = [
        '',
        '## 关系图谱',
        '',
        '> 领域内笔记自动关联',
        '',
        mermaid,
        '',
        '_自动更新于 ' + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M'),
        '',
    ]
    
    new_lines = lines[:insert_pos] + graph_section + lines[insert_pos:]
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    # 统计连接数
    link_count = mermaid.count(' --- ')
    print(f'  {config["filename"]}: 已嵌入 {link_count} 条关系')


if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('更新领域关系图...')
    for name, config in DOMAINS.items():
        print(f'  {name}:')
        update_board(name, config)
    print('\n完成！重启Obsidian查看效果')