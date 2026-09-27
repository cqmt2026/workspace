#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库反哺各系统：建立决策信号库 + 策略参考索引 + 创作素材索引
"""
import io
import sys, os, re, json
from datetime import datetime

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'F:\.Obsidian\Jarvis'

# ========== 1. 投资系统：知识库 -> 决策信号 ==========
print('1. 投资决策信号库...')

# 扫描投资笔记，提取可操作的知识点
signal_file = os.path.join(BASE, '02-投资', '核心', '知识库决策信号.md')
signal_lines = [
    '---',
    'created: 2026-07-02',
    'source: auto_generated',
    'source_system: system',
    'tags: [投资, 信号, 决策]',
    'aliases: [决策信号, 知识库信号]',
    '---',
    '',
    '# 知识库决策信号',
    '',
    '> 从知识库分析笔记中提取的可操作信号',
    '> 由系统自动维护，每天更新',
    '',
    '---',
    '',
]

# 扫描分析笔记，提取关键结论
invest_analysis_dir = os.path.join(BASE, '02-投资', '分析')
invest_module_dir = os.path.join(BASE, '02-投资', '模块')

signals_found = 0
for root, _, files in os.walk(os.path.join(BASE, '02-投资')):
    if '.git' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, BASE)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
        except:
            continue
        
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
        
        # 提取包含"建议"、"关键"、"结论"、"信号"的行
        key_lines = []
        for line in body.split('\n'):
            line_s = line.strip()
            if any(kw in line_s for kw in ['建议', '关键', '结论', '信号', '策略', '注意', '风险']):
                if len(line_s) > 10 and not line_s.startswith('#'):
                    key_lines.append(line_s)
        
        if key_lines:
            title = f.replace('.md', '')
            signal_lines.append(f'## [[{title}]]')
            signal_lines.append('')
            for kl in key_lines[:3]:
                signal_lines.append(f'- {kl}')
            signal_lines.append('')
            signals_found += 1

signal_lines.append('---')
signal_lines.append('_由系统自动维护_')

with open(signal_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(signal_lines))
print(f'  提取 {signals_found} 篇笔记的关键信号')
print()

# ========== 2. 创作系统：知识库 -> 素材索引 ==========
print('2. 创作素材索引...')

material_file = os.path.join(BASE, '01-创作', '素材索引.md')
material_lines = [
    '---',
    'created: 2026-07-02',
    'source: auto_generated',
    'source_system: system',
    'tags: [创作, 素材, 索引]',
    'aliases: [素材索引, 创作素材]',
    '---',
    '',
    '# 创作素材索引',
    '',
    '> 从自媒体、小说、数学动画笔记中提取的可用素材',
    '',
    '---',
    '',
]

# 按素材类型分类
material_types = {
    '标题模板': ['标题', '钩子', '封面'],
    '结构模板': ['结构', '框架', '模板', '公式'],
    '选题方向': ['热点', '选题', '方向', '趋势'],
    '写作技巧': ['技巧', '方法', '节奏', '悬念'],
    '案例拆解': ['拆解', '分析', '对比'],
}

for mtype, keywords in material_types.items():
    material_lines.append(f'## {mtype}')
    material_lines.append('')
    
    found = 0
    for root, _, files in os.walk(os.path.join(BASE, '01-创作')):
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except:
                continue
            
            body = content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    body = parts[2]
            
            if any(kw in body for kw in keywords):
                title = f.replace('.md', '')
                material_lines.append(f'- [[{title}]]')
                found += 1
    
    if found == 0:
        material_lines.append('_（暂无素材）_')
    material_lines.append('')

material_lines.append('---')
material_lines.append('_由系统自动维护_')

with open(material_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(material_lines))
print('  素材索引已生成')
print()

# ========== 3. 微信小程序：知识库 -> 需求池 ==========
print('3. 小程序需求池...')

wx_dir = os.path.join(BASE, '03-项目', '微信小程序')
wx_file = os.path.join(wx_dir, '需求池.md')

wx_lines = [
    '---',
    'created: 2026-07-02',
    'source: auto_generated',
    'source_system: system',
    'tags: [微信小程序, 需求]',
    'aliases: [需求池, 小程序需求]',
    '---',
    '',
    '# 微信小程序需求池',
    '',
    '> 从知识库中提取的可产品化需求',
    '',
    '---',
    '',
    '## 已有产品',
    '',
    '- [[深度解剖-AI错题本小程序是否值得做]]',
    '',
    '## 潜在需求',
    '',
    '- 知识库搜索接口（供小程序调用）',
    '- 投资信号推送（从知识库提取信号推送到微信）',
    '- 创作素材API（为小程序提供内容素材）',
    '',
    '---',
    '_由系统自动维护_',
]

os.makedirs(wx_dir, exist_ok=True)
with open(wx_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(wx_lines))
print('  需求池已生成')
print()

# ========== 4. 更新 agent.md 决策信号引用 ==========
print('4. 更新 agent.md...')

agent_fp = os.path.join(BASE, 'agent.md')
if os.path.exists(agent_fp):
    with open(agent_fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加决策信号引用
    new_section = '\n## 决策参考\n\n- [[知识库决策信号]] - 投资可操作信号\n- [[素材索引]] - 创作素材库\n- [[需求池]] - 微信小程序需求\n\n---\n'
    
    if '决策参考' not in content:
        content += new_section
        with open(agent_fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print('  已添加决策参考链接')
    else:
        print('  决策参考链接已存在')

print()
print('完成！重启Obsidian查看效果')
print()
print('现在知识库不再是信息仓库，而是：')
print('  投资系统 -> 决策信号库（每日更新的可操作信号）')
print('  创作系统 -> 素材索引（按类型分类的可用素材）')
print('  小程序 -> 需求池（可产品化的功能需求）')