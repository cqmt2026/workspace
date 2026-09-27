# -*- coding: utf-8 -*-
"""
房地产自媒体热点采集脚本 V3.4 (BrowserAct版)

新增功能（2026-06-14）：
1. 3天周期过滤：超出3天的热点降权/不收录
2. 信息源评分：官方文件100分 / 权威媒体80分 / 自媒体60分，低于60分降权
3. 角度标签：每条热点自动打标（政策解读/市场信号/购房行为/区域分析/房企动向）

作者：可悦
版本：V3.4
日期：2026-06-14
"""

import sys
import io
import re
from datetime import datetime, timedelta

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

BROWSER = str(Path.home() / ".local" / "bin" / "browser-act.exe")
BROWSER_ID = "chrome_local_101489807684796440"

# 规则1：3天周期
MAX_AGE_DAYS = 3

# 规则2：信息源评分
# 官方文件/政府网站 100分
# 权威媒体（重庆日报/新重庆/中国房地产报/铭腾/克而瑞）80分
# 自媒体 60分
AUTHORITY_SOURCES = [
    # 官方（100分）
    ('公积金中心', 100), ('住建委', 100), ('房管局', 100), ('统计局', 100),
    ('央行', 100), ('政府', 100), ('重庆住建', 100), ('重庆公积金', 100),
    ('国家统计局', 100), ('重庆房管局', 100), ('公积金管理中心', 100),
    # 权威媒体（80分）
    ('重庆日报', 80), ('新重庆', 80), ('中国房地产报', 80), ('铭腾', 80),
    ('克而瑞', 80), ('央广', 80), ('央视', 80), ('新华社', 80),
    ('人民日报', 80), ('重庆发布', 80), ('上游新闻', 80),
    # 自媒体（60分，默认）
]

# 规则3：角度标签
ANGLE_KEYWORDS = {
    '政策解读': ['政策','公积金','房贷利率','限购','限售','降首付','贷款','契税','税费','补贴','新政','规定','文件','通知','办法'],
    '市场信号': ['成交','销量','涨幅','跌幅','回暖','降温','热销','日光','加推','开盘','走势','数据','分析','报告','V型','环比','同比','逆势'],
    '购房行为': ['购房','买房','选房','看房','上车','刚需','改善','落户','落户政策','怎么买','划算','捡漏','观望'],
    '区域分析': ['渝北','南岸','沙坪坝','江北','渝中','九龙坡','大渡口','巴南','北碚','璧山','江津','永川','万州','两江','科学城','高新区','照母山','中央公园','礼嘉','观音桥','茶园','西永'],
    '房企动向': ['房企','开发商','拿地','地王','土拍','流拍','溢价','容积率','交付','物业','开发商跑路','维权','停工'],
}

RE_KW = ['重庆楼市','重庆房价','购房政策','房产','楼市','房价','房地产','购房','买房','房贷',
         '公积金','限购','限售','房交会','二手房','学区房','房贷利率','首付','摇号','开盘',
         '交房','物业','精装房','验房','业主维权','降价','涨价','日光','两江新区','科学城',
         '高新区','照母山','中央公园','礼嘉','观音桥','沙坪坝','渝北','南岸','南滨路']


def score_source(title: str, author: str = '') -> int:
    """信息源评分（规则2）"""
    combined = title + ' ' + author
    for keyword, score in AUTHORITY_SOURCES:
        if keyword in combined:
            return score
    return 60  # 默认自媒体分


def detect_angle(title: str) -> str:
    """角度标签检测（规则3）"""
    for angle, keywords in ANGLE_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return angle
    return '其他'


def check_freshness(date_text: str) -> Tuple[bool, int]:
    """检查消息新鲜度（规则1）
    返回 (是否在3天内, 天数)"""
    if not date_text:
        return True, 0
    today = datetime.now()
    # 尝试解析日期
    patterns = [
        r'(\d{1,2})月(\d{1,2})日',
        r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})日?',
        r'(\d{1,2})[-/](\d{1,2})',
    ]
    for pat in patterns:
        m = re.search(pat, date_text)
        if m:
            groups = m.groups()
            if len(groups) == 2:
                month, day = int(groups[0]), int(groups[1])
                year = today.year
            else:
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            try:
                d = datetime(year, month, day)
                delta = (today - d).days
                if delta <= MAX_AGE_DAYS:
                    return True, delta
                else:
                    return False, delta
            except:
                return True, 0
    return True, 0


def is_re(title: str) -> bool:
    for kw in RE_KW:
        if kw in title:
            return True
    return False


def ba_search(keyword: str, session: str) -> List[Dict]:
    results = []
    url = f"https://so.toutiao.com/search/?keyword={keyword}&pd=information"
    try:
        r = subprocess.run(
            [BROWSER, "--session", session, "browser", "open", BROWSER_ID, url],
            capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace'
        )
        if r.returncode != 0:
            try:
                subprocess.run([BROWSER, "session", "close", session], capture_output=True, timeout=10)
            except (subprocess.TimeoutExpired, Exception):
                pass
            return []

        # 增加超时：头条搜索页加载较慢，给足时间
        wait_result = None
        for attempt in range(2):
            try:
                wait_result = subprocess.run(
                    [BROWSER, "--session", session, "wait", "stable", "--timeout", "20000"],
                    capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
                )
                if wait_result.returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
        # 即使 wait stable 超时也继续（可能页面已加载）

        r = subprocess.run(
            [BROWSER, "--session", session, "get", "markdown"],
            capture_output=True, text=True, timeout=20, encoding='utf-8', errors='replace'
        )
        content = r.stdout if r else ""
    except subprocess.TimeoutExpired as e:
        print(f"  ⚠️ {keyword} 超时: {e}")
        try:
            subprocess.run([BROWSER, "session", "close", session], capture_output=True, timeout=10)
        except Exception:
            pass
        return []
    except Exception as e:
        print(f"  ⚠️ {keyword} 异常: {e}")
        return []

    lines = content.split('\n') if content else []
    # 缓存每篇文章的上下文：标题后面几行可能包含作者和日期
    title_buffer = None
    author_buffer = ''
    date_buffer = ''

    try:
        for i, line in enumerate(lines):
            line = line.strip()
            # 找包含文章标题的行
            if line.startswith('[') and '](' in line:
                title = line[1:line.index(']')]
                # 过滤导航项
                if title in ['综合','视频','资讯','小视频','图片','音乐','用户','微头条','搜索']:
                    title_buffer = None
                    continue
                if 'so.toutiao.com/search?' in line:
                    title_buffer = None
                    continue
                if len(title) >= 8 and is_re(title):
                    title_buffer = title.strip()[:80]
                    author_buffer = ''
                    date_buffer = ''
                    # 看下一行是否包含作者名
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('[!['):
                            # 头像行，再下一行是作者名+日期
                            if i + 2 < len(lines):
                                author_line = lines[i + 2].strip()
                                # 格式: [作者名](url)[日期](url)
                                auth_parts = re.findall(r'\[(.*?)\]', author_line)
                                if len(auth_parts) >= 1:
                                    author_buffer = auth_parts[0]
                                if len(auth_parts) >= 2:
                                    date_buffer = auth_parts[1]
                    # 应用三条规则
                    score = score_source(title_buffer, author_buffer)
                    fresh, age = check_freshness(date_buffer)
                    angle = detect_angle(title_buffer)
                    if score >= 60 and fresh:
                        results.append({
                            'title': title_buffer,
                            'source': '头条搜索',
                            'keyword': keyword,
                            'is_re': True,
                            'score': score,
                            'author': author_buffer,
                            'date': date_buffer,
                            'age_days': age,
                            'angle': angle
                        })
                continue

            # 备选：纯文本标题行
            if title_buffer is None and not line.startswith('[') and 'http' not in line:
                clean = line.strip('* ')
                if 10 <= len(clean) <= 80 and is_re(clean) and 'APP内打开' not in clean:
                    score = score_source(clean)
                    fresh, age = check_freshness('')
                    angle = detect_angle(clean)
                    if score >= 60 and fresh:
                        results.append({
                            'title': clean[:80],
                            'source': '头条搜索',
                            'keyword': keyword,
                            'is_re': True,
                            'score': score,
                            'author': '',
                            'date': '',
                            'age_days': age,
                            'angle': angle
                        })
    except Exception as e:
        print(f"  ⚠️ 解析异常: {e}")

    try:
        subprocess.run([BROWSER, "session", "close", session], capture_output=True, timeout=10)
    except subprocess.TimeoutExpired:
        try:
            subprocess.run([BROWSER, "session", "close", session, "--force"], capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            pass  # Session may already be dead; continue
    return results


def dedup(topics: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for t in topics:
        key = t['title'][:20]
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


def make_suggestions(topics: List[Dict]) -> List[Dict]:
    real = [t for t in topics if t.get('is_re', False)]
    if not real:
        return [
            {'type':'市场观察','title':'重庆楼市月度分析：哪些区域热度最高？','reason':'数据驱动内容', 'angle':'市场信号'},
            {'type':'购房指南','title':'2026年重庆最新购房资格认定标准（全）','reason':'搜索权重高', 'angle':'政策解读'},
        ]
    angles_used = set()
    s = []
    sorted_real = sorted(real, key=lambda x: x.get('score', 60), reverse=True)
    for t in sorted_real:
        angle = t.get('angle', '其他')
        if angle not in angles_used:
            if angle == '政策解读':
                s.append({'type':'政策解读','title':f'重要！{t["title"][:28]}... 一文读懂对购房的影响','reason':'蹭热点，时效性强', 'angle': angle, 'source_score': t.get('score', 60)})
            elif angle == '市场信号':
                s.append({'type':'市场分析','title':f'重庆楼市最新信号：{t["title"][:25]}','reason':'获取搜索流量', 'angle': angle, 'source_score': t.get('score', 60)})
            elif angle == '区域分析':
                s.append({'type':'区域解读','title':f'{t["title"][:25]}，这个区域值不值得买？','reason':'区域干货', 'angle': angle, 'source_score': t.get('score', 60)})
            elif angle == '购房行为':
                s.append({'type':'购房指南','title':f'{t["title"][:25]}，购房者该怎么做？','reason':'实操建议', 'angle': angle, 'source_score': t.get('score', 60)})
            elif angle == '房企动向':
                s.append({'type':'房企观察','title':f'{t["title"][:25]}，这对房价有什么影响？','reason':'行业分析', 'angle': angle, 'source_score': t.get('score', 60)})
            else:
                s.append({'type':'热点跟进','title':f'【今日热话】{t["title"][:28]}','reason':'热点跟进', 'angle': angle, 'source_score': t.get('score', 60)})
            angles_used.add(angle)
        if len(s) >= 3:
            break
    return s[:3]


def save_report(topics: List[Dict], suggestions: List[Dict]):
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    today_d = datetime.now().strftime('%Y-%m-%d')
    real = [t for t in topics if t.get('is_re', False)]
    out_dir = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\热点采集')
    out_dir.mkdir(parents=True, exist_ok=True)
    fpath = out_dir / f'hotspot_{today_d}.md'

    # 按角度分组统计
    angle_stats = {}
    for t in real:
        angle = t.get('angle', '其他')
        angle_stats[angle] = angle_stats.get(angle, 0) + 1

    content = f"""# 房地产热点采集报告 V3.4

**时间**: {today}
**方式**: BrowserAct chrome模式
**采集规则**:
- 3天周期过滤 ✅
- 信息源评分（官方100/权威80/自媒体60） ✅
- 角度标签 ✅

---

## 汇总

| 指标 | 数值 |
|------|------|
| 总热点 | {len(topics)} |
| 房产相关 | {len(real)} |

### 角度分布
"""
    for angle, count in sorted(angle_stats.items(), key=lambda x: -x[1]):
        content += f"| {angle} | {count} |\n"

    content += "\n---\n\n## 房产热点（按信息源评分排序）\n\n"
    # 按评分排序
    sorted_real = sorted(real, key=lambda x: x.get('score', 60), reverse=True)
    for i, t in enumerate(sorted_real[:15], 1):
        score = t.get('score', 60)
        angle = t.get('angle', '其他')
        author = t.get('author', '')
        score_label = '官方' if score >= 100 else '权威媒体' if score >= 80 else '自媒体'
        content += f"{i}. [{score_label}][{angle}] {t['title']}\n"

    if not real:
        content += "\n_暂无房产热点，已生成通用选题建议_\n"

    content += "\n---\n\n## 选题建议（不同角度）\n\n"
    for i, s in enumerate(suggestions, 1):
        angle = s.get('angle', '其他')
        score = s.get('source_score', 60)
        content += f"### {i}. [{angle}] {s['type']}\n**标题**: {s['title']}\n**理由**: {s['reason']}\n**信息源评分**: {score}\n\n"

    content += f"\n---\n_BrowserAct V3.4 | {today}_"

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(fpath)


def main():
    print("=" * 60)
    print("房地产热点采集 V3.4 (三条规则版)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    all_topics = []
    keywords = ['重庆楼市', '重庆房价', '购房政策', '重庆房产', '重庆新盘']

    for i, kw in enumerate(keywords):
        print(f"[{i+1}/{len(keywords)}] 头条搜索：{kw}")
        results = ba_search(kw, f"h{i}")
        print(f"  → {len(results)} 条")
        all_topics.extend(results)

    all_topics = dedup(all_topics)
    real = [t for t in all_topics if t.get('is_re', False)]
    suggestions = make_suggestions(all_topics)
    report = save_report(all_topics, suggestions)

    print(f"\n结果: 总{len(all_topics)}条 / 房产{len(real)}条")
    print(f"报告: {report}")
    print(f"\n房产TOP5（含角度+评分）:")
    for i, t in enumerate(real[:5], 1):
        score_label = '官方' if t.get('score', 60) >= 100 else '权威' if t.get('score', 60) >= 80 else '自媒体'
        print(f"  {i}. [{t.get('angle','其他')}][{score_label}] {t['title'][:50]}")
    print(f"\n选题建议（不同角度）:")
    for i, s in enumerate(suggestions, 1):
        angle = s.get('angle', '其他')
        print(f"  {i}. [{angle}] {s['title'][:50]}")

    return {'total': len(all_topics), 'real': len(real), 'suggestions': suggestions, 'report': report}


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    r = main()
    print("\n[RESULT]")
    print(json.dumps(r, ensure_ascii=False, indent=2))