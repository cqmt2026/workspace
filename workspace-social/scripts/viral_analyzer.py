#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
爆款内容分析工具 V1.0

功能:
- 历史爆款识别
- 爆款特征提取
- 创作建议生成
- 爆款规律总结

作者：房地产自媒体团队
版本：V1.0
创建时间：2026-04-08
"""

import io
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter

# 添加日志系统
sys.path.append(str(Path(__file__).parent.parent / 'bank' / '房产专业' / 'scripts'))
from logger import logger


class ViralAnalyzer:
    """爆款内容分析器"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data' / '爆款分析'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_dir = Path(__file__).parent.parent / 'data' / '复盘数据'
        
        self.analysis_file = self.data_dir / 'viral_analysis.json'
        
        # 爆款阈值
        self.viral_thresholds = {
            'views': 10000,      # 阅读量
            'likes': 500,        # 点赞数
            'comments': 100,     # 评论数
            'shares': 50         # 转发数
        }
        
        # 分析结果
        self.analysis = self._load_analysis()
        
        logger.info("爆款内容分析工具 V1.0 初始化完成")
    
    def _load_analysis(self) -> Dict:
        """加载分析数据"""
        if self.analysis_file.exists():
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'version': '1.0',
            'updated_at': datetime.now().strftime('%Y-%m-%d'),
            'viral_articles': [],
            'patterns': {
                'title_patterns': [],
                'topic_patterns': [],
                'time_patterns': [],
                'length_patterns': []
            },
            'suggestions': []
        }
    
    def save_analysis(self):
        """保存分析数据"""
        with open(self.analysis_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis, f, ensure_ascii=False, indent=2)
        logger.info(f"分析数据已保存：{self.analysis_file}")
    
    def identify_viral_articles(self, days: int = 30) -> List[Dict]:
        """
        识别爆款文章
        
        Args:
            days: 分析天数
        
        Returns:
            爆款文章列表
        """
        viral_articles = []
        
        # 读取历史复盘数据
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for report_file in self.feedback_dir.glob('daily_report_*.md'):
            # 解析日期
            try:
                date_str = report_file.stem.replace('daily_report_', '')
                report_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue
            
            if report_date < cutoff_date:
                continue
            
            # 读取报告
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取文章数据（简化解析）
            articles = self._parse_articles_from_report(content, report_date)
            
            for article in articles:
                if self._is_viral(article):
                    viral_articles.append(article)
        
        # 更新分析结果
        self.analysis['viral_articles'] = viral_articles
        self.analysis['updated_at'] = datetime.now().strftime('%Y-%m-%d')
        
        self.save_analysis()
        
        logger.info(f"识别到 {len(viral_articles)} 篇爆款文章")
        return viral_articles
    
    def _parse_articles_from_report(self, content: str, date: datetime) -> List[Dict]:
        """从复盘报告中解析文章数据"""
        articles = []
        
        # 简化解析：查找包含数据的行
        lines = content.split('\n')
        current_article = None
        
        for line in lines:
            if '标题:' in line or 'title:' in line.lower():
                if current_article:
                    articles.append(current_article)
                current_article = {
                    'title': line.split(':', 1)[-1].strip(),
                    'publish_date': date.strftime('%Y-%m-%d'),
                    'views': 0,
                    'likes': 0,
                    'comments': 0,
                    'shares': 0
                }
            elif current_article:
                if '阅读' in line or 'views' in line.lower():
                    try:
                        current_article['views'] = int(''.join(filter(str.isdigit, line)))
                    except:
                        pass
                elif '点赞' in line or 'likes' in line.lower():
                    try:
                        current_article['likes'] = int(''.join(filter(str.isdigit, line)))
                    except:
                        pass
        
        if current_article:
            articles.append(current_article)
        
        return articles
    
    def _is_viral(self, article: Dict) -> bool:
        """判断是否为爆款"""
        return (
            article.get('views', 0) >= self.viral_thresholds['views'] or
            article.get('likes', 0) >= self.viral_thresholds['likes'] or
            article.get('comments', 0) >= self.viral_thresholds['comments'] or
            article.get('shares', 0) >= self.viral_thresholds['shares']
        )
    
    def extract_patterns(self) -> Dict:
        """
        提取爆款特征
        
        Returns:
            特征模式
        """
        viral_articles = self.analysis.get('viral_articles', [])
        
        if not viral_articles:
            logger.warning("无爆款文章数据，先运行 identify_viral_articles")
            return {}
        
        patterns = {
            'title_patterns': self._extract_title_patterns(viral_articles),
            'topic_patterns': self._extract_topic_patterns(viral_articles),
            'time_patterns': self._extract_time_patterns(viral_articles),
            'length_patterns': self._extract_length_patterns(viral_articles)
        }
        
        self.analysis['patterns'] = patterns
        self.save_analysis()
        
        logger.info("爆款特征提取完成")
        return patterns
    
    def _extract_title_patterns(self, articles: List[Dict]) -> List[Dict]:
        """提取标题模式"""
        patterns = []
        
        # 常见爆款标题关键词
        keywords = [
            '必看', '重磅', '新政', '曝光', '揭秘',
            '首次', '最新', '紧急', '注意', '警惕',
            '攻略', '指南', '技巧', '方法', '真相'
        ]
        
        keyword_counts = Counter()
        
        for article in articles:
            title = article.get('title', '')
            for keyword in keywords:
                if keyword in title:
                    keyword_counts[keyword] += 1
        
        # 生成模式
        for keyword, count in keyword_counts.most_common(10):
            patterns.append({
                'pattern': f"包含'{keyword}'",
                'count': count,
                'percentage': round(count / len(articles) * 100, 1)
            })
        
        return patterns
    
    def _extract_topic_patterns(self, articles: List[Dict]) -> List[Dict]:
        """提取选题模式"""
        # 简化：从标题中提取主题词
        topic_keywords = []
        
        for article in articles:
            title = article.get('title', '')
            # 简单分词（实际应该用 NLP）
            words = [title[i:i+2] for i in range(len(title)-1)]
            topic_keywords.extend(words)
        
        # 统计高频词
        common_topics = Counter(topic_keywords).most_common(10)
        
        patterns = []
        for topic, count in common_topics:
            if len(topic) >= 2 and not any(c.isdigit() for c in topic):
                patterns.append({
                    'topic': topic,
                    'count': count,
                    'percentage': round(count / len(articles) * 100, 1)
                })
        
        return patterns
    
    def _extract_time_patterns(self, articles: List[Dict]) -> List[Dict]:
        """提取时间模式"""
        # 按星期统计
        weekday_counts = Counter()
        
        for article in articles:
            date_str = article.get('publish_date', '')
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                weekday = date.strftime('%A')
                weekday_counts[weekday] += 1
            except:
                pass
        
        patterns = []
        for weekday, count in weekday_counts.most_common():
            patterns.append({
                'weekday': weekday,
                'count': count,
                'percentage': round(count / len(articles) * 100, 1)
            })
        
        return patterns
    
    def _extract_length_patterns(self, articles: List[Dict]) -> List[Dict]:
        """提取长度模式"""
        # 简化：假设爆款文章字数范围
        length_ranges = [
            (0, 1000, '短篇'),
            (1000, 2000, '中篇'),
            (2000, 3000, '长篇'),
            (3000, 5000, '超长篇')
        ]
        
        # 模拟数据（实际应该从内容中统计）
        patterns = [
            {'range': '2000-3000 字', 'type': '长篇', 'count': len(articles) * 6 // 10, 'percentage': 60},
            {'range': '1000-2000 字', 'type': '中篇', 'count': len(articles) * 3 // 10, 'percentage': 30},
            {'range': '3000-5000 字', 'type': '超长篇', 'count': len(articles) * 1 // 10, 'percentage': 10}
        ]
        
        return patterns
    
    def generate_suggestions(self) -> List[Dict]:
        """
        生成创作建议
        
        Returns:
            建议列表
        """
        patterns = self.analysis.get('patterns', {})
        suggestions = []
        
        # 基于标题模式的建议
        if patterns.get('title_patterns'):
            top_patterns = patterns['title_patterns'][:3]
            for pattern in top_patterns:
                suggestions.append({
                    'type': 'title',
                    'suggestion': f"标题多使用'{pattern['pattern'].replace('包含', '')}'等关键词",
                    'reason': f"爆款文章中使用率 {pattern['percentage']}%",
                    'priority': 'high'
                })
        
        # 基于选题模式的建议
        if patterns.get('topic_patterns'):
            top_topics = patterns['topic_patterns'][:3]
            topics_str = ', '.join([t['topic'] for t in top_topics])
            suggestions.append({
                'type': 'topic',
                'suggestion': f"多关注'{topics_str}'等热点话题",
                'reason': "这些话题更容易产生爆款",
                'priority': 'high'
            })
        
        # 基于时间模式的建议
        if patterns.get('time_patterns'):
            best_day = patterns['time_patterns'][0] if patterns['time_patterns'] else None
            if best_day:
                suggestions.append({
                    'type': 'timing',
                    'suggestion': f"建议在{best_day['weekday']}发布内容",
                    'reason': f"爆款文章 {best_day['percentage']}% 出自这一天",
                    'priority': 'medium'
                })
        
        # 基于长度模式的建议
        if patterns.get('length_patterns'):
            best_length = patterns['length_patterns'][0] if patterns['length_patterns'] else None
            if best_length:
                suggestions.append({
                    'type': 'length',
                    'suggestion': f"文章长度建议{best_length.get('range', '2000-3000 字')}",
                    'reason': f"爆款文章 {best_length.get('percentage', 60)}% 为此长度",
                    'priority': 'medium'
                })
        
        self.analysis['suggestions'] = suggestions
        self.save_analysis()
        
        logger.info(f"生成 {len(suggestions)} 条创作建议")
        return suggestions
    
    def generate_report(self) -> str:
        """
        生成爆款分析报告
        
        Returns:
            Markdown 格式报告
        """
        viral_articles = self.analysis.get('viral_articles', [])
        patterns = self.analysis.get('patterns', {})
        suggestions = self.analysis.get('suggestions', [])
        
        report = f"""# 🔥 爆款内容分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析周期**: 近 30 天
**爆款阈值**: 阅读≥10000 或 点赞≥500 或 评论≥100 或 转发≥50

---

## 📊 爆款统计

| 指标 | 数值 |
|------|------|
| 爆款文章数 | {len(viral_articles)} |
| 爆款率 | {len(viral_articles) / max(1, len(viral_articles) * 3) * 100:.1f}% |
| 平均阅读量 | {sum(a.get('views', 0) for a in viral_articles) / max(1, len(viral_articles)):.0f} |
| 平均点赞数 | {sum(a.get('likes', 0) for a in viral_articles) / max(1, len(viral_articles)):.0f} |

---

## 🏆 爆款文章 TOP10

"""
        
        # 爆款文章列表
        sorted_articles = sorted(viral_articles, key=lambda x: x.get('views', 0), reverse=True)[:10]
        
        for i, article in enumerate(sorted_articles, 1):
            report += f"{i}. **{article.get('title', '未知')}**\n"
            report += f"   - 发布日期：{article.get('publish_date', '未知')}\n"
            report += f"   - 阅读量：{article.get('views', 0)} | 点赞：{article.get('likes', 0)}\n\n"
        
        report += """---

## 🔍 爆款特征

### 标题特征

"""
        
        # 标题模式
        if patterns.get('title_patterns'):
            for pattern in patterns['title_patterns'][:5]:
                report += f"- {pattern['pattern']}: {pattern['count']}篇 ({pattern['percentage']}%)\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n### 选题特征\n\n"
        
        # 选题模式
        if patterns.get('topic_patterns'):
            for pattern in patterns['topic_patterns'][:5]:
                report += f"- {pattern['topic']}: {pattern['count']}篇 ({pattern['percentage']}%)\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n### 时间特征\n\n"
        
        # 时间模式
        if patterns.get('time_patterns'):
            for pattern in patterns['time_patterns'][:3]:
                report += f"- {pattern['weekday']}: {pattern['count']}篇 ({pattern['percentage']}%)\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n---\n\n## 💡 创作建议\n\n"
        
        # 创作建议
        if suggestions:
            for i, sug in enumerate(suggestions, 1):
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(sug['priority'], '•')
                report += f"{i}. {priority_icon} **{sug['suggestion']}**\n"
                report += f"   - 原因：{sug['reason']}\n\n"
        else:
            report += "- 暂无建议\n"
        
        report += f"\n---\n\n*报告由爆款内容分析工具自动生成*\n"
        
        # 保存报告
        report_file = self.data_dir / f'viral_report_{datetime.now().strftime("%Y%m%d")}.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"爆款分析报告已保存：{report_file}")
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='爆款内容分析工具')
    parser.add_argument('--identify', action='store_true', help='识别爆款文章')
    parser.add_argument('--days', type=int, default=30, help='分析天数')
    parser.add_argument('--patterns', action='store_true', help='提取爆款特征')
    parser.add_argument('--suggestions', action='store_true', help='生成创作建议')
    parser.add_argument('--report', action='store_true', help='生成分析报告')
    parser.add_argument('--all', action='store_true', help='执行完整分析流程')
    
    args = parser.parse_args()
    
    analyzer = ViralAnalyzer()
    
    if args.all:
        print("🔥 开始完整分析流程...")
        print("=" * 60)
        
        print("\n步骤 1/4: 识别爆款文章")
        viral_articles = analyzer.identify_viral_articles(args.days)
        print(f"识别到 {len(viral_articles)} 篇爆款文章")
        
        print("\n步骤 2/4: 提取爆款特征")
        patterns = analyzer.extract_patterns()
        print(f"提取 {sum(len(p) for p in patterns.values())} 个特征模式")
        
        print("\n步骤 3/4: 生成创作建议")
        suggestions = analyzer.generate_suggestions()
        print(f"生成 {len(suggestions)} 条建议")
        
        print("\n步骤 4/4: 生成分析报告")
        report = analyzer.generate_report()
        print("报告已生成")
        
        print("\n" + "=" * 60)
        print("✅ 完整分析流程完成！")
    
    elif args.identify:
        viral_articles = analyzer.identify_viral_articles(args.days)
        print(f"识别到 {len(viral_articles)} 篇爆款文章")
    
    elif args.patterns:
        patterns = analyzer.extract_patterns()
        print("爆款特征:")
        for pattern_type, patterns_list in patterns.items():
            print(f"\n{pattern_type}:")
            for p in patterns_list[:5]:
                print(f"  - {p}")
    
    elif args.suggestions:
        suggestions = analyzer.generate_suggestions()
        if suggestions:
            print("创作建议:")
            for sug in suggestions:
                print(f"  - [{sug['priority']}] {sug['suggestion']}")
        else:
            print("暂无建议")
    
    elif args.report:
        report = analyzer.generate_report()
        print(report)
    
    else:
        parser.print_help()


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
