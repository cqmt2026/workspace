# -*- coding: utf-8 -*-
"""
PREFERENCES.md 自动同步脚本（增强版 - 支持系统标签）
从 self-improving/memory.md 和 corrections.md 提取学习成果，同步到 PREFERENCES.md
自动分类 + 系统标签检测 + 去重
"""

import os
import re
import sys
from datetime import datetime
import io

# 文件路径
WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
MEMORY_FILE = os.path.join(WORKSPACE, "self-improving", "memory.md")
CORRECTIONS_FILE = os.path.join(WORKSPACE, "self-improving", "corrections.md")
PREFERENCES_FILE = os.path.join(WORKSPACE, "PREFERENCES.md")

# 同步标记（避免重复同步）
SYNC_MARKER = "<!-- AUTO-SYNC MARKER -->"


def read_file(path):
    """读取文件内容"""
    if not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    """写入文件并验证"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    # 验证写入
    with open(path, 'r', encoding='utf-8') as f:
        verify = f.read()
    if len(verify) != len(content):
        raise Exception(f"写入验证失败：{path}")
    return True


def extract_hot_memories(content):
    """从 memory.md 提取 HOT 记忆"""
    memories = []
    pattern = r'### (⚠️|✅|📌)?\s*(.+?)\n\*\*问题\*\*: (.+?)\n(.*?)(?=\n### |\n---|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        emoji, title, problem, details = match
        lesson_match = re.search(r'\*\*教训\*\*: (.+?)(?=\n\n|\n### |\Z)', details, re.DOTALL)
        lesson = lesson_match.group(1).strip() if lesson_match else ""
        solution_match = re.search(r'\*\*解决方案\*\*: (.+?)(?=\n\n|\n### |\Z)', details, re.DOTALL)
        solution = solution_match.group(1).strip() if solution_match else ""
        
        memories.append({
            'title': title.strip(),
            'problem': problem.strip(),
            'lesson': lesson,
            'solution': solution,
            'type': '纠正' if '⚠️' in emoji else '方案' if '✅' in emoji else '记忆'
        })
    
    return memories


def extract_corrections(content):
    """从 corrections.md 提取纠正记录"""
    corrections = []
    pattern = r'## (.+?) — Correction #(\d+)\n\n\*\*触发\*\*: (.+?)\n\*\*严重程度\*\*: (.+?)\n\n\*\*问题\*\*: (.+?)\n\n(.*?)(?=\n---\n\n## |\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        date, num, trigger, severity, problem, details = match
        lesson_match = re.search(r'\*\*教训\*\*: (.+?)(?=\n\n|\n---|\Z)', details, re.DOTALL)
        lesson = lesson_match.group(1).strip() if lesson_match else ""
        measures_match = re.search(r'\*\*纠正措施\*\*:\n(.*?)(?=\n\n|\*\*教训\*\*|\Z)', details, re.DOTALL)
        measures = measures_match.group(1).strip() if measures_match else ""
        
        corrections.append({
            'date': date.strip(),
            'num': num,
            'trigger': trigger.strip(),
            'severity': severity.strip(),
            'problem': problem.strip(),
            'lesson': lesson,
            'measures': measures
        })
    
    return corrections


def categorize_learning(item, source):
    """将学习记录分类到 PREFERENCES.md 的对应板块，并标注适用系统"""
    category_map = {
        '禁忌': ['禁止', '绝对不能', '严禁', '不准', '❌'],
        '沟通偏好': ['沟通', '语言', '风格', '称呼', '回复'],
        '工作规则': ['流程', '规则', '步骤', '执行', '自动', '主动', '确认', '需求', '猜测'],
        '写作偏好': ['写作', '创作', '文案', '内容', '语气', '小说', '章节', '题材', '大纲', '爽点'],
        '注意事项': ['注意', '限制', '规范', '标准', '要求', '字体', '符号', 'emoji', 'PIL', 'draw'],
        '热点监控': ['热点', '监控', '采集', '平台'],
    }
    
    # 系统关键词映射（按优先级排序）
    system_keywords = {
        '全局': ['全局', '所有系统', '一律', '任何', '禁止', '绝对', '不准', '严禁', '必须', '先', '再', '不能', '不要', '每次'],
        '数学动画': ['数学', '动画', '帧', '视频', 'manim', 'ffmpeg', 'PIL', 'draw', 'emoji', '符号', '字体', 'EP00', '年级', '奥数', '五角星', '渲染', '盈亏问题', '年龄问题'],
        '小说创作': ['小说', '章节', '创作', '题材', '大纲', '鉴城', '旧城', '爽点', 'V7.0', '章尾', '悬念', '字数'],
        '自媒体运营': ['自媒体', '发布', '百家号', '头条号', '抖音', 'Cookie', '账号', '流量', '选题', '封面', '标题'],
        '投资分析': ['投资', '持仓', '股票', '基金', '周报', '市值', 'ETF', '仓位', '盈亏分析'],
    }
    
    text = f"{item.get('title', '')} {item.get('problem', '')} {item.get('lesson', '')} {item.get('solution', '')}"
    
    # 检测适用系统（带优先级）
    detected_systems = []
    for system, keywords in system_keywords.items():
        match_count = 0
        for keyword in keywords:
            if keyword.lower() in text.lower():
                match_count += 1
        
        # 全局规则：匹配 2 个以上关键词，或包含"必须/禁止/不准"等强规则词
        if system == '全局' and match_count >= 2:
            detected_systems.insert(0, '全局')  # 全局优先
        elif system != '全局' and match_count >= 1:
            detected_systems.append(system)
    
    # 确定最终系统标签
    if len(detected_systems) == 0:
        applicable_system = '全局'
    elif len(detected_systems) == 1:
        applicable_system = detected_systems[0]
    else:
        # 多个系统 → 如果包含全局，用全局
        if '全局' in detected_systems:
            applicable_system = '全局'
        else:
            applicable_system = ', '.join(detected_systems)
    
    # 检测分类
    for category, keywords in category_map.items():
        for keyword in keywords:
            if keyword in text:
                return category, applicable_system
    
    return '注意事项', applicable_system  # 默认分类


def format_preference_entry(item, source, category, system='全局'):
    """格式化 PREFERENCES.md 条目（带系统标签）"""
    date = datetime.now().strftime('%Y-%m-%d')
    
    if source == 'memory':
        # 压缩多行内容为单行
        content = item.get('lesson', item.get('solution', ''))
        content = ' '.join(content.split())[:100]  # 压缩空白，限制长度
        entry_text = f"**{item['title']}**: {content}"
    else:  # corrections
        content = item['lesson']
        content = ' '.join(content.split())[:100]  # 压缩空白，限制长度
        entry_text = f"**Correction #{item['num']}**: {content}"
    
    # 系统标签格式：[全局] 或 [数学动画] 或 [小说创作，自媒体运营]
    system_tag = f"[{system}]" if system else '[全局]'
    
    return f"| {date} | {entry_text} | {system_tag} |"


def sync_to_preferences(memories, corrections):
    """同步学习记录到 PREFERENCES.md"""
    prefs_content = read_file(PREFERENCES_FILE)
    original_content = prefs_content
    
    if not prefs_content:
        print("⚠️ PREFERENCES.md 不存在，创建新文件")
        prefs_content = f"""# PREFERENCES.md — 主人偏好数据库

> **永久保留，禁止删除**

---

## 📌 基础信息
- **称呼**：主人
- **身份**：自媒体创作者 + 小说创作者 + 投资者
- **时区**：Asia/Shanghai

## 🎯 沟通偏好
- **风格**：直接、专业、不废话
- **语言**：中文为主
- **禁忌**：空洞客套、过度恭维

## 🚫 禁忌（绝对不能做）
| 日期 | 规则 | 适用系统 |
|------|------|----------|

## 🔄 工作规则
| 日期 | 规则 | 适用系统 |
|------|------|----------|

## ⚠️ 注意事项
| 日期 | 事项 | 适用系统 |
|------|------|----------|

## 📡 热点监控
- 平台：微博、抖音、知乎、B 站
- 话题：科技、互联网、创意
- 时间：每日 9:00 / 21:00

## ✍️ 写作偏好
- 语气：专业有观点
- 结构：标题 + 要点 + 案例
- 禁忌：空洞废话

## 🔄 更新规则

**触发时机**：主人给出纠正/偏好/新要求时，立即更新本文档

**更新原则**：
- 每次主人纠正 → 记录到学习日志
- 每次主人给偏好 → 立即写入对应板块
- 每次重要对话结论 → 提炼写入

**禁止**：
- 不覆盖旧记录（只追加）
- 不删除任何历史记录
- 不凭"我以为"修改

## 🧠 学习日志
| 日期 | 记录 |
|------|------|
| {datetime.now().strftime('%Y-%m-%d')} | 初始化自动同步机制（系统标签增强版） |

---

_最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}_
"""
    
    # 添加同步标记
    if SYNC_MARKER not in prefs_content:
        prefs_content = prefs_content.replace('</preferences>', f'{SYNC_MARKER}\n</preferences>') if '</preferences>' in prefs_content else prefs_content + f'\n{SYNC_MARKER}\n'
    
    # 板块映射
    section_map = {
        '禁忌': '## 🚫 禁忌（绝对不能做）',
        '沟通偏好': '## 🎯 沟通偏好',
        '工作规则': '## 🔄 工作规则',
        '写作偏好': '## ✍️ 写作偏好',
        '注意事项': '## ⚠️ 注意事项',
        '热点监控': '## 📡 热点监控',
    }
    
    # 处理 HOT 记忆
    synced_count = 0
    for memory in memories:
        category, system = categorize_learning(memory, 'memory')
        entry = format_preference_entry(memory, 'memory', category, system)
        
        # 检查是否已存在（避免重复）
        entry_text = entry.split('|')[2].strip()[:50] if len(entry.split('|')) > 2 else ''
        if entry_text and entry_text not in prefs_content:
            section = section_map.get(category, '## ⚠️ 注意事项')
            
            if section in prefs_content:
                lines = prefs_content.split('\n')
                for i, line in enumerate(lines):
                    if section in line:
                        # 查找表格分隔线（更灵活的正则）
                        for j in range(i+1, min(i+10, len(lines))):
                            if re.match(r'^\|[-\s]+\|[-\s]+\|', lines[j]) or re.match(r'^\|[-\s]+\|[-\s]+\|[-\s]+\|', lines[j]):
                                # 检查是否有系统标签列，没有则添加
                                header = lines[j-1] if j > 0 else ''
                                if '| 日期 | 规则 |' in header and '| 适用系统 |' not in header:
                                    lines[j-1] = '| 日期 | 规则 | 适用系统 |'
                                    lines[j] = '|------|------|------------|'
                                lines.insert(j+1, entry)
                                prefs_content = '\n'.join(lines)
                                synced_count += 1
                                print(f"  [SYNC] HOT 记忆：{memory['title']} -> {category} [{system}]")
                                break
                        break
    
    # 处理纠正记录
    for correction in corrections:
        category, system = categorize_learning(correction, 'correction')
        entry = format_preference_entry(correction, 'correction', category, system)
        
        # 检查是否已存在（避免重复）
        if f"Correction #{correction['num']}" not in prefs_content:
            section = section_map.get(category, '## ⚠️ 注意事项')
            
            if section in prefs_content:
                lines = prefs_content.split('\n')
                for i, line in enumerate(lines):
                    if section in line:
                        # 查找表格分隔线（更灵活的正则）
                        for j in range(i+1, min(i+10, len(lines))):
                            if re.match(r'^\|[-\s]+\|[-\s]+\|', lines[j]) or re.match(r'^\|[-\s]+\|[-\s]+\|[-\s]+\|', lines[j]):
                                # 检查是否有系统标签列，没有则添加
                                header = lines[j-1] if j > 0 else ''
                                if '| 日期 | 规则 |' in header and '| 适用系统 |' not in header:
                                    lines[j-1] = '| 日期 | 规则 | 适用系统 |'
                                    lines[j] = '|------|------|------------|'
                                elif '| 日期 | 事项 |' in header and '| 适用系统 |' not in header:
                                    lines[j-1] = '| 日期 | 事项 | 适用系统 |'
                                    lines[j] = '|------|------|------------|'
                                lines.insert(j+1, entry)
                                prefs_content = '\n'.join(lines)
                                synced_count += 1
                                print(f"  [SYNC] 纠正记录：Correction #{correction['num']} -> {category} [{system}]")
                                break
                        break
    
    # 更新最后更新时间
    update_pattern = r'_最后更新：\d{4}-\d{2}-\d{2}[^_]*_'
    if re.search(update_pattern, prefs_content):
        prefs_content = re.sub(update_pattern, f"_最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}_", prefs_content)
    else:
        prefs_content += f"\n\n_最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"
    
    # 写入文件
    write_file(PREFERENCES_FILE, prefs_content)
    return synced_count


def main():
    print("=" * 60)
    print("PREFERENCES.md 自动同步（系统标签增强版）")
    print("=" * 60)
    
    # 读取源文件
    memory_content = read_file(MEMORY_FILE)
    corrections_content = read_file(CORRECTIONS_FILE)
    
    if not memory_content and not corrections_content:
        print("[WARN] 源文件为空，跳过同步")
        return
    
    # 提取学习记录
    memories = extract_hot_memories(memory_content)
    corrections = extract_corrections(corrections_content)
    
    print(f"[MEM] 提取到 {len(memories)} 条 HOT 记忆")
    print(f"[CORR] 提取到 {len(corrections)} 条纠正记录")
    
    # 同步到 PREFERENCES.md
    if memories or corrections:
        synced = sync_to_preferences(memories, corrections)
        print(f"\n[OK] 同步完成：{synced} 条记录")
    else:
        print("\n[INFO] 无需要同步的记录")
    
    print("=" * 60)


if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
