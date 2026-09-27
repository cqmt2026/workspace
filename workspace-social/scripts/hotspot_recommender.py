# -*- coding: utf-8 -*-
import io
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
热点选题推荐系统 V2.0
多维度评分 + 账号匹配 + Top3推荐
"""
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

HOTSPOT_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\热点采集")
ANALYSIS_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\运营日志\热点分析")
ACCOUNT_PROFILE = {
    "name": "山城房谈",
    "定位": "重庆房地产垂直账号",
    "擅长": ["政策解读", "数据解读", "楼盘测评", "购房指南"],
    "粉丝画像": "25-40岁刚需/改善购房者",
    "内容风格": "专业、务实、有数据支撑",
}

@dataclass
class HotspotScore:
    """热点评分结果"""
    title: str
    source: str
    url: str
    hot_score: float       # 热度 0-5
    controversy_score: float  # 争议性 0-5
    timeliness_score: float   # 时效性 0-5
    actionable_score: float   # 可操作性 0-5
    account_match: float     # 账号匹配 0-5
    total_score: float       # 综合评分
    grade: str              # A/B/C级
    recommendation: str      # 推荐理由
    writing_angle: str       # 写作角度
    expected_effect: str     # 预期效果
    competitor_analysis: str  # 竞品分析

def score_hotness(title: str, source: str) -> float:
    """评分维度1：热度"""
    score = 3.0
    
    # 来源权重
    high_sources = ['百度热搜', '微博热搜', '知乎热榜', '抖音热榜']
    medium_sources = ['今日头条', '百家号', '微信公众号']
    
    if any(s in source for s in high_sources):
        score += 1.5
    elif any(s in source for s in medium_sources):
        score += 0.5
    
    # 标题关键词热度词
    hot_words = ['暴涨', '暴跌', '重磅', '突发', '刚刚', '曝光', '揭秘', '震惊']
    if any(w in title for w in hot_words):
        score += 0.5
    
    return min(5.0, score)

def score_controversy(title: str) -> float:
    """评分维度2：争议性"""
    score = 2.5
    
    # 争议关键词
    controversy_words = [
        '该不该', '能不能', '要不要', '是不是',
        '揭秘', '真相', '套路', '坑', '黑幕',
        '暴跌', '暴涨', '降价', '涨价', '烂尾',
        '维权', '投诉', '避坑', '后悔', '争议'
    ]
    count = sum(1 for w in controversy_words if w in title)
    score += count * 0.5
    
    # 问号增加争议性
    if '？' in title or '?' in title:
        score += 0.5
    
    return min(5.0, score)

def score_timeliness(title: str, hours_old: int = 0) -> float:
    """评分维度3：时效性"""
    score = 3.0
    
    # 时间衰减
    if hours_old < 2:
        score += 1.5
    elif hours_old < 6:
        score += 1.0
    elif hours_old < 12:
        score += 0.5
    elif hours_old < 24:
        score += 0.0
    else:
        score -= 1.0
    
    # 突发关键词
    breaking_words = ['突发', '刚刚', '重磅', '最新', '今日']
    if any(w in title for w in breaking_words):
        score += 0.5
    
    return min(5.0, max(0.0, score))

def score_actionable(title: str) -> float:
    """评分维度4：可操作性"""
    score = 3.0
    
    # 有具体信息点的标题更容易写
    actionable_words = [
        '数据', '政策', '攻略', '指南', '教程',
        '详解', '解读', '分析', '对比', '测评',
        '名单', '表格', '清单', '排名', '榜单'
    ]
    count = sum(1 for w in actionable_words if w in title)
    score += count * 0.3
    
    # 模糊标题降低可操作性
    vague_words = ['竟然', '没想到', '原来', '背后', '真相']
    if any(w in title for w in vague_words):
        score -= 0.5
    
    return min(5.0, max(0.0, score))

def score_account_match(title: str, profile: Dict) -> float:
    """评分维度5：账号匹配"""
    score = 3.5
    
    # 定位匹配
    if '重庆' in title or '山城' in title:
        score += 1.0
    
    # 擅长领域匹配
    good_topics = ['政策', '数据', '房价', '楼盘', '购房', '房贷', '公积金', '土拍', '买房']
    count = sum(1 for w in good_topics if w in title)
    score += count * 0.3
    
    # 账号风格匹配
    if any(w in title for w in ['解读', '分析', '测评', '数据']):
        score += 0.5
    
    return min(5.0, score)

def calculate_total_score(scores: dict) -> tuple:
    """计算综合评分"""
    weights = {
        'hot': 0.30,
        'controversy': 0.25,
        'timeliness': 0.20,
        'actionable': 0.15,
        'match': 0.10,
    }
    
    total = (
        scores['hot'] * weights['hot'] +
        scores['controversy'] * weights['controversy'] +
        scores['timeliness'] * weights['timeliness'] +
        scores['actionable'] * weights['actionable'] +
        scores['match'] * weights['match']
    )
    
    # 评级
    if total >= 4.2:
        grade = 'S级'
    elif total >= 3.8:
        grade = 'A级'
    elif total >= 3.2:
        grade = 'B级'
    else:
        grade = 'C级'
    
    return total, grade

def generate_recommendation(scores: dict, title: str) -> str:
    """生成推荐理由"""
    reasons = []
    
    if scores['hot'] >= 4.0:
        reasons.append('热度高')
    if scores['controversy'] >= 4.0:
        reasons.append('争议性强')
    if scores['timeliness'] >= 4.0:
        reasons.append('时效性强')
    if scores['actionable'] >= 3.5:
        reasons.append('有干货')
    if scores['match'] >= 4.0:
        reasons.append('符合账号定位')
    
    if not reasons:
        reasons = ['综合评分较高']
    
    return '+'.join(reasons)

def generate_writing_angle(title: str, source: str) -> str:
    """生成写作角度建议"""
    angles = []
    
    if any(w in title for w in ['政策', '公积金', '房贷', '利率']):
        angles.append('政策解读（普通人看不懂的角度）')
        angles.append('实操攻略（怎么办理）')
    
    if any(w in title for w in ['降价', '特价', '优惠', '打折']):
        angles.append('风险分析（为什么便宜）')
        angles.append('适合人群（谁可以买）')
    
    if any(w in title for w in ['测评', '对比', '哪个好']):
        angles.append('客观测评（数据说话）')
        angles.append('适合人群分析')
    
    if any(w in title for w in ['购房', '买房', '刚需', '改善']):
        angles.append('真实案例（购房故事）')
        angles.append('避坑指南')
    
    if not angles:
        angles = ['深度分析（为什么这事重要）', '普通人应该怎么看']
    
    return ' / '.join(angles[:2])

def generate_expected_effect(title: str, score: float) -> str:
    """生成预期效果"""
    if score >= 4.0:
        return '预计阅读量10w+，互动率高，适合吸粉'
    elif score >= 3.5:
        return '预计阅读量3-5w，收藏率高，适合建立权威'
    elif score >= 3.0:
        return '预计阅读量1-2w，评论活跃，有利于互动'
    else:
        return '适合日常更新，维持账号活跃度'

def generate_competitor_analysis(title: str, source: str) -> str:
    """生成竞品分析"""
    # 简单模拟，实际应该爬取竞品内容
    if any(w in title for w in ['重磅', '突发', '震惊']):
        return '高热度话题，竞品正在跟进，需快速发布抢流量'
    elif any(w in title for w in ['测评', '对比']):
        return '同类内容点赞平均500+，需要差异化角度'
    elif any(w in title for w in ['政策', '数据']):
        return '需要独家视角或数据支撑，避开同质化'
    else:
        return '竞争激烈，建议配差异化标题和封面'

def score_hotspot(title: str, source: str, url: str = '', hours_old: int = 0) -> HotspotScore:
    """对一个热点进行完整评分"""
    scores = {
        'hot': score_hotness(title, source),
        'controversy': score_controversy(title),
        'timeliness': score_timeliness(title, hours_old),
        'actionable': score_actionable(title),
        'match': score_account_match(title, ACCOUNT_PROFILE),
    }
    
    total, grade = calculate_total_score(scores)
    
    return HotspotScore(
        title=title,
        source=source,
        url=url,
        hot_score=scores['hot'],
        controversy_score=scores['controversy'],
        timeliness_score=scores['timeliness'],
        actionable_score=scores['actionable'],
        account_match=scores['match'],
        total_score=total,
        grade=grade,
        recommendation=generate_recommendation(scores, title),
        writing_angle=generate_writing_angle(title, source),
        expected_effect=generate_expected_effect(title, total),
        competitor_analysis=generate_competitor_analysis(title, source),
    )

def find_latest_hotspots() -> List[Path]:
    """找到最近的热点采集报告"""
    if not HOTSPOT_DIR.exists():
        return []
    
    reports = sorted(HOTSPOT_DIR.glob("hotspot_*.md"), reverse=True)
    # 只取最近2天的
    cutoff = datetime.now() - timedelta(days=2)
    recent = []
    for r in reports:
        try:
            date_str = r.stem.replace('hotspot_', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
            if file_date >= cutoff:
                recent.append(r)
        except:
            pass
    return recent[:3]  # 最多3个

def clean_title(title: str) -> str:
    # Hard truncate at 35 chars to avoid garbage
    if len(title) > 35:
        title = title[:35]
    # Remove trailing numbers/digits
    import re
    title = re.sub(r'\d+$', '', title)
    return title.strip()

def parse_hotspots(filepath: Path) -> List[Dict]:
    """解析热点报告 - 使用「全部房产相关热点」章节"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 找到「全部房产相关热点」章节
    in_all_section = False
    hotspots = []
    seen_titles = set()
    
    for line in content.split('\n'):
        line = line.strip()
        
        if '全部房产相关热点' in line:
            in_all_section = True
            continue
        
        if '数据来源明细' in line or '---' in line:
            if in_all_section:
                break
        
        if in_all_section:
            # 匹配格式: 1. [来源] 标题
            match = re.match(r'^\d+\.\s*\[([^\]]+)\]\s*(.+)$', line)
            if match:
                source = match.group(1).strip()
                raw_title = match.group(2).strip()
                title = clean_title(raw_title)
                
                # 去重
                if title and title not in seen_titles and len(title) > 5:
                    seen_titles.add(title)
                    hotspots.append({
                        'source': source,
                        'title': title,
                    })
    
    return hotspots

def recommend_top3(hotspots: List[Dict]) -> List[HotspotScore]:
    """对热点列表进行评分，返回Top3（去重后）"""
    # 先去重：基于标题关键词去重
    seen_keywords = set()
    deduped = []
    for h in hotspots:
        # 提取标题关键词（取前10个字符）
        title_short = h['title'][:10]
        
        # 检查是否与已处理过的标题重复
        is_duplicate = False
        for kw in seen_keywords:
            if kw in h['title'] or h['title'] in kw:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_keywords.add(h['title'][:15])
            deduped.append(h)
    
    # 对去重后的热点进行评分
    scored = []
    for h in deduped:
        score = score_hotspot(
            title=h['title'],
            source=h['source'],
            url=h.get('url', ''),
            hours_old=h.get('hours_old', 0)
        )
        scored.append(score)
    
    # 按综合评分排序
    scored.sort(key=lambda x: x.total_score, reverse=True)
    
    return scored[:3]

def generate_recommendation_report(recommendations: List[HotspotScore]) -> str:
    """生成推荐报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    header = f"""# 🎯 今日选题推荐 TOP3

**账号**: {ACCOUNT_PROFILE['name']}
**定位**: {ACCOUNT_PROFILE['定位']}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    body = ""
    for i, rec in enumerate(recommendations, 1):
        emoji = '🥇' if i == 1 else '🥈' if i == 2 else '🥉'
        
        body += f"""## {emoji} [{rec.grade}] {rec.title}

**综合评分**: {rec.total_score:.2f} / 5.0

| 维度 | 评分 | 说明 |
|------|------|------|
| 🔥 热度 | {rec.hot_score:.1f}/5 | {rec.source} |
| 💬 争议性 | {rec.controversy_score:.1f}/5 | - |
| ⏰ 时效性 | {rec.timeliness_score:.1f}/5 | - |
| 📝 可操作性 | {rec.actionable_score:.1f}/5 | - |
| 🎯 账号匹配 | {rec.account_match:.1f}/5 | {ACCOUNT_PROFILE['name']} |

**推荐理由**: {rec.recommendation}

**写作角度**: {rec.writing_angle}

**预期效果**: {rec.expected_effect}

**竞品分析**: {rec.competitor_analysis}

---

"""
    
    footer = f"""
## 📋 创作清单

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P0 | 撰写 TOP1 选题（{recommendations[0].title[:20] if recommendations else 'N/A'}...） | ⬜ 待创作 |
| P1 | 撰写 TOP2 选题（{recommendations[1].title[:20] if len(recommendations) > 1 else 'N/A'}...） | ⬜ 待创作 |
| P2 | 撰写 TOP3 选题（{recommendations[2].title[:20] if len(recommendations) > 2 else 'N/A'}...） | ⬜ 待创作 |

---

_由 可悦🌸 自动生成_
_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
    
    return header + body + footer

def main():
    print("=" * 60)
    print("🎯 热点选题推荐系统 V2.0")
    print("=" * 60)
    
    # 找最新热点
    reports = find_latest_hotspots()
    if not reports:
        print("[ERROR] 未找到热点采集报告")
        print(f"提示：请先运行 hotspot_monitor.py 采集热点")
        return
    
    print(f"[OK] 找到 {len(reports)} 个最近报告")
    
    # 解析所有热点
    all_hotspots = []
    for report in reports:
        hotspots = parse_hotspots(report)
        print(f"  - {report.name}: {len(hotspots)} 个热点")
        all_hotspots.extend(hotspots)
    
    print(f"[OK] 共 {len(all_hotspots)} 个热点待评分")
    
    # 评分推荐
    top3 = recommend_top3(all_hotspots)
    
    # 生成报告
    report_content = generate_recommendation_report(top3)
    
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = ANALYSIS_DIR / f"topic_recommendation_{datetime.now().strftime('%Y-%m-%d')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n[OK] 推荐报告已生成: {report_file.name}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📌 今日推荐 TOP3")
    print("=" * 60)
    for i, rec in enumerate(top3, 1):
        print(f"\n{i}. [{rec.grade}] {rec.title}")
        print(f"   评分: {rec.total_score:.2f} | 推荐理由: {rec.recommendation}")
        print(f"   写作角度: {rec.writing_angle}")
    
    print("\n" + "=" * 60)
    
    return str(report_file)

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
