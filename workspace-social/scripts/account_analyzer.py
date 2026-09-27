#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百家号账号数据分析工具
分析账号优劣势，为后续运营提供思路

功能:
- 分析账号基础数据（发布数/阅读量/互动量/涨粉）
- 分析内容类型表现（新房/二手房/政策/区域）
- 分析标题效果（疑问式/数字式/对比式）
- 分析发布时间效果（时段/星期）
- 识别优势领域和待改进方向
- 生成运营建议报告

用法:
python account_analyzer.py [--account <账号名>] [--days <天数>]
"""

import io
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

# 尝试导入 pandas（可选）
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class BaijiahaoAnalyzer:
    """百家号账号数据分析器"""
    
    def __init__(self, account_name: str = None):
        """
        初始化分析器
        
        Args:
            account_name: 账号名称（默认读取配置的第一个账号）
        """
        self.account_name = account_name
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.data_dir = Path(__file__).parent.parent / 'data' / '采集数据'
        self.output_dir = Path(__file__).parent.parent / 'analysis_reports'
        self.output_dir.mkdir(exist_ok=True)
        
        # 加载账号配置
        self.account_config = self._load_account_config()
        
        # 加载采集数据
        self.articles = self._load_articles()
    
    def _load_account_config(self) -> Dict:
        """加载账号配置"""
        config_file = self.config_dir / 'baijiahao_accounts.json'
        if not config_file.exists():
            print(f"[WARN] 配置文件不存在：{config_file}")
            return {}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if self.account_name:
            for acc in config.get('accounts', []):
                if acc.get('name') == self.account_name:
                    return acc
            print(f"[WARN] 未找到账号：{self.account_name}")
            return {}
        else:
            accounts = config.get('accounts', [])
            if accounts:
                print(f"[INFO] 使用默认账号：{accounts[0].get('name')}")
                return accounts[0]
            return {}
    
    def _load_articles(self, days: int = 30) -> List[Dict]:
        """
        加载历史文章数据
        
        Args:
            days: 加载最近 N 天的数据
            
        Returns:
            文章列表
        """
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 遍历采集数据目录
        if not self.data_dir.exists():
            print(f"[WARN] 数据目录不存在：{self.data_dir}")
            return articles
        
        for file in self.data_dir.glob('*.json'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取文章数据
                if 'articles' in data:
                    for article in data['articles']:
                        # 检查日期
                        pub_date = article.get('publish_date', '')
                        if pub_date:
                            try:
                                article_date = datetime.strptime(pub_date, '%Y-%m-%d')
                                if article_date >= cutoff_date:
                                    articles.append(article)
                            except ValueError:
                                pass
            except Exception as e:
                print(f"[WARN] 读取文件失败 {file}: {e}")
        
        print(f"[OK] 加载最近{days}天文章：{len(articles)} 篇")
        return articles
    
    def analyze_basic_stats(self) -> Dict:
        """分析基础统计数据"""
        if not self.articles:
            return {'error': '无文章数据'}
        
        total_articles = len(self.articles)
        total_views = sum(a.get('views', 0) for a in self.articles)
        total_likes = sum(a.get('likes', 0) for a in self.articles)
        total_comments = sum(a.get('comments', 0) for a in self.articles)
        total_shares = sum(a.get('shares', 0) for a in self.articles)
        
        avg_views = total_views / total_articles if total_articles > 0 else 0
        avg_likes = total_likes / total_articles if total_articles > 0 else 0
        avg_comments = total_comments / total_articles if total_articles > 0 else 0
        avg_shares = total_shares / total_articles if total_articles > 0 else 0
        
        # 互动率
        engagement_rate = ((total_likes + total_comments + total_shares) / total_views * 100) if total_views > 0 else 0
        
        # 涨粉数（如果有）
        total_followers = sum(a.get('new_followers', 0) for a in self.articles)
        
        return {
            'total_articles': total_articles,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_followers': total_followers,
            'avg_views': round(avg_views, 2),
            'avg_likes': round(avg_likes, 2),
            'avg_comments': round(avg_comments, 2),
            'avg_shares': round(avg_shares, 2),
            'engagement_rate': round(engagement_rate, 4),
        }
    
    def analyze_content_types(self) -> Dict:
        """分析内容类型表现"""
        type_stats = defaultdict(lambda: {'count': 0, 'views': 0, 'likes': 0, 'comments': 0, 'shares': 0})
        
        for article in self.articles:
            content_type = article.get('content_type', '其他')
            type_stats[content_type]['count'] += 1
            type_stats[content_type]['views'] += article.get('views', 0)
            type_stats[content_type]['likes'] += article.get('likes', 0)
            type_stats[content_type]['comments'] += article.get('comments', 0)
            type_stats[content_type]['shares'] += article.get('shares', 0)
        
        # 计算平均表现
        result = {}
        for ctype, stats in type_stats.items():
            count = stats['count']
            result[ctype] = {
                'count': count,
                'avg_views': round(stats['views'] / count, 2) if count > 0 else 0,
                'avg_likes': round(stats['likes'] / count, 2) if count > 0 else 0,
                'avg_comments': round(stats['comments'] / count, 2) if count > 0 else 0,
                'avg_shares': round(stats['shares'] / count, 2) if count > 0 else 0,
            }
        
        # 按平均阅读量排序
        sorted_types = sorted(result.items(), key=lambda x: x[1]['avg_views'], reverse=True)
        
        return {
            'by_type': result,
            'best_performing': sorted_types[0][0] if sorted_types else None,
            'worst_performing': sorted_types[-1][0] if sorted_types else None,
        }
    
    def analyze_title_patterns(self) -> Dict:
        """分析标题模式效果"""
        patterns = {
            '数字式': [],  # 包含数字
            '疑问式': [],  # 包含问号或疑问词
            '对比式': [],  # 包含对比词
            '陈述式': [],  # 其他
        }
        
        for article in self.articles:
            title = article.get('title', '')
            views = article.get('views', 0)
            
            if re.search(r'\d+', title):
                patterns['数字式'].append(views)
            elif '？' in title or '?' in title or '吗' in title or '如何' in title or '为什么' in title:
                patterns['疑问式'].append(views)
            elif any(w in title for w in ['vs', '对比', '还是', '哪个', 'PK', '与']):
                patterns['对比式'].append(views)
            else:
                patterns['陈述式'].append(views)
        
        result = {}
        for pattern, views_list in patterns.items():
            if views_list:
                result[pattern] = {
                    'count': len(views_list),
                    'avg_views': round(sum(views_list) / len(views_list), 2),
                    'max_views': max(views_list),
                }
            else:
                result[pattern] = {'count': 0, 'avg_views': 0, 'max_views': 0}
        
        # 找出最佳标题模式
        best_pattern = max(result.items(), key=lambda x: x[1]['avg_views'])[0] if result else None
        
        return {
            'by_pattern': result,
            'best_performing': best_pattern,
        }
    
    def analyze_publish_time(self) -> Dict:
        """分析发布时间效果"""
        hour_stats = defaultdict(list)
        weekday_stats = defaultdict(list)
        
        for article in self.articles:
            publish_time = article.get('publish_time', '')
            views = article.get('views', 0)
            
            if publish_time:
                try:
                    dt = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
                    hour_stats[dt.hour].append(views)
                    weekday_stats[dt.weekday()].append(views)
                except ValueError:
                    pass
        
        # 按小时统计
        hour_result = {}
        for hour in range(24):
            views_list = hour_stats.get(hour, [])
            if views_list:
                hour_result[f"{hour:02d}:00"] = {
                    'count': len(views_list),
                    'avg_views': round(sum(views_list) / len(views_list), 2),
                }
        
        # 按星期统计
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_result = {}
        for wd in range(7):
            views_list = weekday_stats.get(wd, [])
            if views_list:
                weekday_result[weekday_names[wd]] = {
                    'count': len(views_list),
                    'avg_views': round(sum(views_list) / len(views_list), 2),
                }
        
        # 找出最佳时段
        best_hour = max(hour_result.items(), key=lambda x: x[1]['avg_views'])[0] if hour_result else None
        best_weekday = max(weekday_result.items(), key=lambda x: x[1]['avg_views'])[0] if weekday_result else None
        
        return {
            'by_hour': hour_result,
            'by_weekday': weekday_result,
            'best_hour': best_hour,
            'best_weekday': best_weekday,
        }
    
    def generate_suggestions(self, basic_stats: Dict, content_types: Dict, title_patterns: Dict, publish_time: Dict) -> List[str]:
        """生成运营建议"""
        suggestions = []
        
        # 基于内容类型
        if content_types.get('best_performing'):
            suggestions.append(f"[ADVANTAGE] 优势领域：{content_types['best_performing']}类内容表现最佳，建议加大创作力度")
        if content_types.get('worst_performing'):
            suggestions.append(f"[NEEDS_IMPROVEMENT] 待改进：{content_types['worst_performing']}类内容表现较弱，需优化或减少发布")
        
        # 基于标题模式
        if title_patterns.get('best_performing'):
            suggestions.append(f"[TITLE_TIP] 标题技巧：{title_patterns['best_performing']}标题效果最好，建议优先使用")
        
        # 基于发布时间
        if publish_time.get('best_hour'):
            suggestions.append(f"[BEST_TIME] 最佳时段：{publish_time['best_hour']}发布的文章阅读量最高，建议集中在此时间段发布")
        if publish_time.get('best_weekday'):
            suggestions.append(f"[BEST_DAY] 最佳日期：{publish_time['best_weekday']}发布的文章表现最佳")
        
        # 基于互动率
        engagement_rate = basic_stats.get('engagement_rate', 0)
        if engagement_rate < 0.5:
            suggestions.append("[INTERACTION] 互动提升：互动率偏低，建议在文末增加互动引导（如：你怎么看？欢迎评论区留言）")
        elif engagement_rate > 1.0:
            suggestions.append(f"[INTERACTION_GOOD] 互动优秀：互动率{engagement_rate:.2f}%，保持当前策略")
        
        # 基于平均阅读量
        avg_views = basic_stats.get('avg_views', 0)
        if avg_views < 1000:
            suggestions.append("[TRAFFIC] 流量提升：平均阅读量偏低，建议优化标题和选题，蹭热点话题")
        elif avg_views > 5000:
            suggestions.append(f"[TRAFFIC_GOOD] 流量优秀：平均阅读量{avg_views:.0f}，继续保持高质量输出")
        
        return suggestions
    
    def run_analysis(self, days: int = 30) -> Dict:
        """
        运行完整分析
        
        Args:
            days: 分析最近 N 天的数据
            
        Returns:
            完整分析报告
        """
        print("\n" + "="*60)
        print("百家号账号分析报告")
        print(f"分析周期：最近{days}天")
        print("="*60 + "\n")
        
        # 重新加载数据
        self.articles = self._load_articles(days)
        
        if not self.articles:
            print("[ERROR] 没有足够的文章数据进行分析")
            return {'error': '无文章数据'}
        
        # 各项分析
        basic_stats = self.analyze_basic_stats()
        content_types = self.analyze_content_types()
        title_patterns = self.analyze_title_patterns()
        publish_time = self.analyze_publish_time()
        
        # 生成建议
        suggestions = self.generate_suggestions(basic_stats, content_types, title_patterns, publish_time)
        
        # 汇总报告
        report = {
            'account_name': self.account_name,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_period': f"最近{days}天",
            'basic_stats': basic_stats,
            'content_types': content_types,
            'title_patterns': title_patterns,
            'publish_time': publish_time,
            'suggestions': suggestions,
        }
        
        # 打印报告
        self._print_report(report)
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def _print_report(self, report: Dict):
        """打印报告到控制台"""
        basic = report['basic_stats']
        
        print("[DATA] 基础统计数据")
        print(f"  文章总数：{basic.get('total_articles', 0)} 篇")
        print(f"  总阅读量：{basic.get('total_views', 0):,}")
        print(f"  总互动量：{basic.get('total_likes', 0) + basic.get('total_comments', 0) + basic.get('total_shares', 0):,}")
        print(f"  平均阅读量：{basic.get('avg_views', 0):,.0f}")
        print(f"  互动率：{basic.get('engagement_rate', 0):.2f}%")
        print()
        
        print("[CONTENT] 内容类型表现")
        for ctype, stats in report['content_types']['by_type'].items():
            print(f"  {ctype}: {stats['count']}篇，平均{stats['avg_views']:,.0f}阅读")
        print(f"  [BEST] 最佳：{report['content_types']['best_performing']}")
        print(f"  [NEEDS_IMPROVEMENT] 待改进：{report['content_types']['worst_performing']}")
        print()
        
        print("[TITLE] 标题模式效果")
        for pattern, stats in report['title_patterns']['by_pattern'].items():
            if stats['count'] > 0:
                print(f"  {pattern}: {stats['count']}篇，平均{stats['avg_views']:,.0f}阅读")
        print(f"  [BEST] 最佳标题：{report['title_patterns']['best_performing']}")
        print()
        
        print("[TIME] 最佳发布时间")
        print(f"  最佳时段：{report['publish_time']['best_hour']}")
        print(f"  最佳星期：{report['publish_time']['best_weekday']}")
        print()
        
        print("[SUGGESTION] 运营建议")
        for i, suggestion in enumerate(report['suggestions'], 1):
            print(f"  {i}. {suggestion}")
        print()
    
    def _save_report(self, report: Dict):
        """保存报告到文件"""
        # 保存 JSON
        json_file = self.output_dir / f"account_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 报告已保存:")
        print(f"  JSON: {json_file}")
        
        # 保存 Markdown
        md_file = self.output_dir / f"account_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._save_markdown_report(report, md_file)
        print(f"  Markdown: {md_file}")
    
    def _save_markdown_report(self, report: Dict, md_file: Path):
        """保存 Markdown 格式报告"""
        basic = report['basic_stats']
        
        md_content = f"""# 百家号账号分析报告\n\n**账号**: {report.get('account_name', 'N/A')}\n**分析时间**: {report['analysis_date']}\n**分析周期**: {report['analysis_period']}\n\n"""
        
        md_content += f"""## 基础统计数据\n\n- 文章总数：**{basic.get('total_articles', 0)} 篇**\n- 总阅读量：**{basic.get('total_views', 0):,}**\n- 总互动量：**{basic.get('total_likes', 0) + basic.get('total_comments', 0) + basic.get('total_shares', 0):,}**\n- 平均阅读量：**{basic.get('avg_views', 0):,.0f}**\n- 互动率：**{basic.get('engagement_rate', 0):.2f}%**\n\n"""
        
        md_content += "## 内容类型表现\n\n"
        for ctype, stats in report['content_types']['by_type'].items():
            md_content += f"- {ctype}: {stats['count']}篇，平均{stats['avg_views']:,.0f}阅读\n"
        md_content += f"\n**最佳表现**: {report['content_types']['best_performing']}\n"
        md_content += f"**待改进**: {report['content_types']['worst_performing']}\n\n"
        
        md_content += "## 标题模式效果\n\n"
        for pattern, stats in report['title_patterns']['by_pattern'].items():
            if stats['count'] > 0:
                md_content += f"- {pattern}: {stats['count']}篇，平均{stats['avg_views']:,.0f}阅读\n"
        md_content += f"\n**最佳标题**: {report['title_patterns']['best_performing']}\n\n"
        
        md_content += "## 最佳发布时间\n\n"
        md_content += f"- 最佳时段：**{report['publish_time']['best_hour']}**\n"
        md_content += f"- 最佳星期：**{report['publish_time']['best_weekday']}**\n\n"
        
        md_content += "## 运营建议\n\n"
        for i, suggestion in enumerate(report['suggestions'], 1):
            md_content += f"{i}. {suggestion}\n"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)


import re


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='百家号账号数据分析工具')
    parser.add_argument('--account', type=str, help='账号名称')
    parser.add_argument('--days', type=int, default=30, help='分析最近 N 天的数据（默认 30 天）')
    
    args = parser.parse_args()
    
    analyzer = BaijiahaoAnalyzer(account_name=args.account)
    analyzer.run_analysis(days=args.days)


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
