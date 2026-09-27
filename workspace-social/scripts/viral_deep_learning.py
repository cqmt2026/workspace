"""
V2.0 自媒体爆款深度学习（主动模式）

不再等上游复盘数据。主动：
1. 扫描 workspace-social 所有 md 文章文件
2. 分析标题特征、内容长度、选题方向
3. 产出爆款特征报告
4. 更新知识库中的爆款特征模型
"""
import os
import re
import json
import sys
import glob
from datetime import datetime, timedelta
from collections import Counter

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-social'
DATA_DIR = os.path.join(WORKSPACE, 'data')
MEMORY_DIR = os.path.join(WORKSPACE, 'memory')
RECORD_DIR = os.path.join(WORKSPACE, '记录')
REPORT_DIR = os.path.join(WORKSPACE, '记录', '复盘')
KNOWLEDGE_DIR = os.path.join(WORKSPACE, 'bank')

# 爆款关键词（从经验总结）
VIRAL_KEYWORDS = {
    '必看': 0.9, '重磅': 0.95, '新政': 0.85, '曝光': 0.9, '揭秘': 0.88,
    '首次': 0.8, '最新': 0.75, '紧急': 0.9, '注意': 0.7, '警惕': 0.75,
    '攻略': 0.82, '指南': 0.78, '技巧': 0.7, '方法': 0.65, '真相': 0.85,
    '楼市': 0.8, '房价': 0.85, '购房': 0.7, '买房': 0.7, '卖房': 0.6,
    '对比': 0.75, '差': 0.6, 'VS': 0.8, '区别': 0.7, '哪个': 0.7,
}

# 风格特征
STYLE_PATTERNS = {
    'question': {'kw': ['？', '?', '如何', '怎么', '吗'], 'weight': 0.8},
    'number': {'kw': [r'\d+'], 'weight': 0.75},
    'exclamation': {'kw': ['！', '!'], 'weight': 0.6},
    'policy': {'kw': ['政策', '新政', '楼市政策', '调控'], 'weight': 0.9},
    'market': {'kw': ['市场', '房价', '成交', '土地', '库存'], 'weight': 0.85},
    'guide': {'kw': ['指南', '攻略', '技巧', '方法', '建议'], 'weight': 0.7},
    'compare': {'kw': ['对比', 'VS', '区别', '哪个', '差异'], 'weight': 0.8},
    'reveal': {'kw': ['揭秘', '曝光', '真相', '内幕', '不为人知'], 'weight': 0.9},
}

def scan_all_content_files():
    """扫描 workspace-social 中所有文章/内容文件"""
    files = []
    targets = ['article_', 'auto_draft_', '今日头条_', '自媒体_', '热点_', '爆款_', '分析_', '复盘_']
    if os.path.exists(WORKSPACE):
        for root, dirs, fnames in os.walk(WORKSPACE):
            # 跳过 data/ 中的 json
            rel = os.path.relpath(root, WORKSPACE)
            for f in sorted(fnames):
                if f.endswith('.md') and any(t in f for t in targets):
                    fp = os.path.join(root, f)
                    size = os.path.getsize(fp)
                    if size > 500:  # 至少500B
                        files.append((fp, size))
    return sorted(files, key=lambda x: x[1], reverse=True)

def scan_json_data_files():
    """扫描 json 数据文件（复盘、发布记录等）"""
    files = []
    if os.path.exists(DATA_DIR):
        for root, dirs, fnames in os.walk(DATA_DIR):
            for f in sorted(fnames):
                if f.endswith('.json'):
                    fp = os.path.join(root, f)
                    size = os.path.getsize(fp)
                    if size > 100:
                        files.append((fp, size))
    return sorted(files, key=lambda x: x[1], reverse=True)

def analyze_title(title):
    """分析标题特征"""
    result = {
        'title': title,
        'viral_score': 0.0,
        'keywords_found': [],
        'styles': [],
        'length': len(title),
    }

    # 关键词评分
    for kw, score in VIRAL_KEYWORDS.items():
        if kw in title:
            result['viral_score'] += score
            result['keywords_found'].append(kw)

    # 风格评分
    for style, pattern in STYLE_PATTERNS.items():
        for kw in pattern['kw']:
            if kw == r'\d+':
                if re.search(r'\d+', title):
                    result['styles'].append(style)
                    result['viral_score'] += pattern['weight'] * 0.5
                    break
            elif kw in title:
                result['styles'].append(style)
                result['viral_score'] += pattern['weight'] * 0.5
                break

    # 标题长度评分（15-25字最佳）
    if 15 <= result['length'] <= 25:
        result['viral_score'] += 0.3
    elif result['length'] < 10:
        result['viral_score'] -= 0.2

    result['viral_score'] = min(1.0, max(0.0, result['viral_score']))
    return result

def extract_title_from_file(filepath):
    """从文件中提取标题"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # 文件名提取
        basename = os.path.basename(filepath).replace('.md', '')
        # 内容中的标题
        for line in content.split('\n')[:5]:
            if line.startswith('# ') and len(line) < 100:
                return line[2:].strip(), content
        # 文件名中有标题
        for sep in ['_', '-', '：', ':', '（', '(']:
            if sep in basename:
                return basename.split(sep, 1)[1].strip(), content
        return basename, content
    except:
        return os.path.basename(filepath), ''

def run():
    print("=" * 60)
    print("V2.0 自媒体爆款深度学习（主动模式）")
    print("=" * 60)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 扫描所有文章文件
    articles = scan_all_content_files()
    print(f"[扫描] 文章文件: {len(articles)} 篇")

    # 2. 扫描 json 数据
    data_files = scan_json_data_files()
    print(f"[扫描] 数据文件: {len(data_files)} 个")

    # 3. 分析所有文章标题
    title_analyses = []
    all_titles = []
    keyword_counter = Counter()
    style_counter = Counter()

    for filepath, size in articles:
        title, content = extract_title_from_file(filepath)
        if not title:
            continue
        analysis = analyze_title(title)
        title_analyses.append(analysis)
        all_titles.append(title)
        for kw in analysis['keywords_found']:
            keyword_counter[kw] += 1
        for style in analysis['styles']:
            style_counter[style] += 1

    print(f"[分析] 有效标题: {len(all_titles)} 个")

    # 4. 排序找高分标题
    top_titles = sorted(title_analyses, key=lambda x: x['viral_score'], reverse=True)[:10]

    # 5. 生成报告
    report = f"""# 🧠 自媒体爆款深度学习报告

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**模式**: V2.0 主动扫描

---

## 数据概况

- 文章文件扫描: {len(articles)} 篇
- 数据文件: {len(data_files)} 个
- 有效标题: {len(all_titles)} 个
- 平均标题长度: {sum(len(t['title']) for t in title_analyses) // max(1, len(title_analyses))} 字
- 平均爆款评分: {sum(t['viral_score'] for t in title_analyses) / max(1, len(title_analyses)):.2f}

---

## 🔥 爆款关键词 TOP10

"""
    for kw, count in keyword_counter.most_common(10):
        bar = '█' * min(20, count * 3)
        report += f"- **{kw}**: {count}次 {bar}\n"

    if not keyword_counter:
        report += "- 暂无关键词数据（无文章文件可分析）\n"

    report += f"""
---

## 🎨 风格分布

"""
    for style, count in style_counter.most_common(10):
        bar = '█' * min(20, count * 3)
        report += f"- **{style}**: {count}次 {bar}\n"

    if not style_counter:
        report += "- 暂无风格数据\n"

    report += f"""
---

## 🏆 高分标题 TOP10

"""
    for i, t in enumerate(top_titles, 1):
        stars = '★' * min(5, int(t['viral_score'] * 5))
        report += f"{i}. **{t['title']}** 评分 {t['viral_score']:.2f} {stars}\n"
        if t['keywords_found']:
            report += f"   关键词: {', '.join(t['keywords_found'])}\n"

    if not top_titles:
        report += "- 暂无标题可分析\n"

    report += f"""
---

## 📝 建议

"""
    if not keyword_counter:
        report += "1. **无文章文件可分析** — 建议先创作或采集一批文章\n"
    else:
        top_kw = keyword_counter.most_common(3)
        report += f"1. 高频关键词: {', '.join(f'**{k}**({v})' for k,v in top_kw)}\n"
        if style_counter.get('reveal', 0) > style_counter.get('guide', 0):
            report += "2. 揭秘/曝光类标题更受欢迎，建议多采用\n"
        else:
            report += "2. 指南/攻略类标题占主导，可尝试揭秘类\n"
        if style_counter.get('question', 0) < 2:
            report += "3. 疑问句标题较少，建议增加（'如何...''怎么...'）\n"
        report += "4. 标题长度控制在15-25字最佳\n"

    report += "5. 如有复盘数据（文章阅读量/点赞量），本系统可自动从 json 文件中提取\n"

    report += f"\n---\n_自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"

    # 6. 写入报告
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, f"爆款深度学习_{datetime.now().strftime('%Y%m%d')}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[输出] 报告已写入: {os.path.relpath(report_path, WORKSPACE)}")

    # 7. 保存模型到 memory
    os.makedirs(MEMORY_DIR, exist_ok=True)
    model = {
        'version': '2.0',
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_articles_scanned': len(articles),
        'top_keywords': dict(keyword_counter.most_common(10)),
        'top_styles': dict(style_counter.most_common(10)),
        'avg_viral_score': round(sum(t['viral_score'] for t in title_analyses) / max(1, len(title_analyses)), 3),
    }
    model_path = os.path.join(MEMORY_DIR, 'viral_model.json')
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    print(f"[模型] 模型已更新: {os.path.basename(model_path)}")
    
    # 存入supermemory
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
        from memory_adapter import save_topic
        summary = '爆款深度学习: 扫描%d篇, 热门关键词: %s' % (
            len(articles),
            ', '.join(k for k, _ in keyword_counter.most_common(5))
        )
        save_topic(summary, source='social-learning')
        print('  [Supermemory] 已保存深度学习结果')
    except Exception as e:
        print('  [Supermemory] 写入失败: %s' % e)

    print()
    print(f"[OK] 深度学习完成")
    print("=" * 60)

if __name__ == '__main__':
    run()
