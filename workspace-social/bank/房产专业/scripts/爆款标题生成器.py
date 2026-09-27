#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
爆款标题生成器 V2.0
基于爆款元素分析生成高点击率标题

爆款公式：
- 情绪触发（焦虑/贪婪/好奇/认同）
- 数字冲击（具体金额/比例/时间）
- 对比冲突（前后/人群/买对买错）
- 权威背书（官方/专家/数据）
- 实用价值（指南/攻略/避坑）

作者：小智
版本：V2.0
创建时间：2026-03-25
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys

sys.path.append(str(Path(__file__).parent))
from logger import logger


class ViralTitleGenerator:
    """
    爆款标题生成器
    
    生成 7 大类型标题，每种类型 5 个版本，共 35 个标题备选
    """
    
    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / 'pipeline_data' / 'viral_titles'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 爆款标题模板库（100+ 模板）
        self.templates = self._load_templates()
        
        # 情绪词库
        self.emotion_words = {
            '焦虑': ['警惕', '注意', '小心', '风险', '陷阱', '坑', '别买', '后悔'],
            '贪婪': ['赚翻', '暴涨', '抄底', '机会', '红利', '福利', '省 XX 万'],
            '好奇': ['揭秘', '真相', '内幕', '没想到', '居然是', '曝光', '罕见'],
            '认同': ['终于', '总算', '建议', '忠告', '心里话', '大实话', '戳中'],
            '紧迫': ['刚刚', '速看', '马上', '最后', '倒计时', '即将', '末班车'],
        }
        
        # 数字模式
        self.number_patterns = [
            '3 个', '5 大', '7 个', '10 个', '90%', '50%', '30%',
            '100 万', '50 万', '30 万', '10 万', '5 万',
            '3 年', '5 年', '10 年', '30 年',
            '第 1 个', '第 2 个', '最后一个'
        ]
        
        # 对比模式
        self.contrast_patterns = [
            '之前 vs 现在', '买对 vs 买错', '赚 50 万 vs 亏 30 万',
            '劝你买 vs 劝你别买', '内行 vs 外行', '10 年前 vs 现在'
        ]
        
        logger.info("爆款标题生成器 V2.0 初始化完成")
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """加载标题模板"""
        return {
            # 数字型（具体数字冲击）
            'number': [
                '重庆{topic}，这{num}个信号你一定要知道',
                '{num}个{topic}真相，第{num2}个最扎心',
                '关于{topic}，我说{num}句大实话',
                '{topic}的{num}个陷阱，踩中一个就完了',
                '花了{num}天，整理出这份{topic}指南',
                '{num}年房产经验，总结的{topic}{num2}条',
                '{topic}，{num}%的人都搞错了',
            ],
            
            # 对比型（前后/人群对比）
            'contrast': [
                '{topic}之前 vs 现在，差距太大了',
                '买对{topic}赚{money}万，买错亏{money2}万',
                '{topic}，内行和外行的差距在哪？',
                '同样是{topic}，为什么别人{result}你却{result2}',
                '{topic}：10 年前{state}，现在{state2}',
                '劝你{topic}vs 劝你别{topic}，听哪个？',
            ],
            
            # 指南型（实用价值）
            'guide': [
                '{topic}全攻略，看这一篇就够了',
                '{topic}避坑指南，这{num}点一定要看',
                '第一次{topic}，如何避免被坑？',
                '{topic}最全指南，建议收藏',
                '手把手教你{topic}，超详细',
                '{topic}流程 + 注意事项，一篇搞定',
            ],
            
            # 揭秘型（好奇心）
            'reveal': [
                '{topic}的真相，终于有人说了',
                '揭秘{topic}内幕，看完震惊了',
                '{topic}背后，藏着什么秘密？',
                '关于{topic}，销售不会告诉你的{num}件事',
                '{topic}套路大曝光，第{num}个最常见',
                '深度揭秘：{topic}的真实情况',
            ],
            
            # 预测型（未来趋势）
            'predict': [
                '{topic}，未来{time}年走势分析',
                '预测{topic}，{time}个信号已经出现',
                '{topic}要变天了？{num}个迹象很明显',
                '现在{topic}，{time}年后会怎样？',
                '{topic}窗口期，还剩{time}年',
            ],
            
            # 故事型（情感共鸣）
            'story': [
                '{topic}，我最后悔的{num}个决定',
                '一个{topic}的真实故事，看哭了',
                '{topic}经历，说多了都是泪',
                '粉丝投稿：{topic}，我踩过的坑',
                '{topic}血泪史，希望你别犯',
            ],
            
            # 权威型（数据/专家背书）
            'authority': [
                '官方数据：{topic}最新情况',
                '专家解读：{topic}意味着什么',
                '{topic}，统计局数据说明了一切',
                '央行/{topic}政策，影响多少人？',
                '克而瑞数据：{topic}真相',
            ],
            
            # 争议型（引发讨论）
            'controversy': [
                '{topic}，我说{num}个不受欢迎的真话',
                '为什么我劝你别{topic}？',
                '{topic}争议：支持 vs 反对',
                '{topic}，这次我站{side}',
                '对不起，{topic}我不同意',
            ],
        }
    
    def generate_titles(self, topic: str, keywords: List[str] = None, 
                        count: int = 35) -> List[Dict]:
        """
        生成爆款标题
        
        Args:
            topic: 选题主题
            keywords: 关键词列表
            count: 生成数量
        
        Returns:
            标题列表（含评分和类型）
        """
        logger.info(f"开始生成爆款标题：{topic}")
        
        if not keywords:
            keywords = [topic[:4]]
        
        all_titles = []
        
        # 每种类型生成 5 个标题
        for title_type, templates in self.templates.items():
            for template in templates:
                try:
                    title = self._fill_template(template, topic, keywords)
                    if title and len(title) < 40:
                        all_titles.append({
                            'title': title,
                            'type': title_type,
                            'score': self._score_title(title),
                            'elements': self._analyze_elements(title)
                        })
                except Exception:
                    continue
        
        # 按评分排序
        all_titles.sort(key=lambda x: x['score'], reverse=True)
        
        # 去重 + 截取
        seen = set()
        unique_titles = []
        for t in all_titles:
            if t['title'] not in seen and len(unique_titles) < count:
                seen.add(t['title'])
                unique_titles.append(t)
        
        # 保存结果
        self._save_titles(unique_titles, topic)
        
        logger.info(f"生成{len(unique_titles)}个爆款标题")
        return unique_titles
    
    def _fill_template(self, template: str, topic: str, keywords: List[str]) -> str:
        """填充模板"""
        
        # 替换通用占位符
        title = template.replace('{topic}', topic)
        
        # 替换数字
        if '{num}' in title:
            title = title.replace('{num}', random.choice(['3', '5', '7', '10']))
        if '{num2}' in title:
            title = title.replace('{num2}', random.choice(['2', '3', '4']))
        
        # 替换金额
        if '{money}' in title:
            title = title.replace('{money}', random.choice(['30', '50', '100']))
        if '{money2}' in title:
            title = title.replace('{money2}', random.choice(['20', '30', '50']))
        
        # 替换时间
        if '{time}' in title:
            title = title.replace('{time}', random.choice(['3', '5', '10']))
        
        # 替换状态
        if '{state}' in title:
            title = title.replace('{state}', random.choice(['没人买', '白菜价']))
            title = title.replace('{state2}', random.choice(['抢着买', '买不起']))
        
        # 替换结果
        if '{result}' in title:
            title = title.replace('{result}', random.choice(['赚了', '抢到了']))
            title = title.replace('{result2}', random.choice(['亏了', '没抢到']))
        
        # 替换立场
        if '{side}' in title:
            title = title.replace('{side}', random.choice(['买方', '卖方']))
        
        return title
    
    def _score_title(self, title: str) -> int:
        """标题评分（0-100）"""
        score = 0
        
        # 长度评分（20-30 字最佳）
        length = len(title)
        if 20 <= length <= 30:
            score += 20
        elif 15 <= length < 20 or 30 < length <= 35:
            score += 15
        else:
            score += 10
        
        # 情绪词评分
        for emotion, words in self.emotion_words.items():
            if any(w in title for w in words):
                score += 15
                break
        
        # 数字评分
        if any(num in title for num in self.number_patterns):
            score += 20
        
        # 对比评分
        if any(c in title for c in ['vs', '对比', '差距', '赚', '亏', '前', '后']):
            score += 15
        
        # 疑问/悬念评分
        if any(c in title for c in ['？', '吗', '呢', '如何', '为什么']):
            score += 10
        
        # 实用性评分
        if any(c in title for c in ['指南', '攻略', '教程', '避坑', '建议']):
            score += 10
        
        # 负面情绪扣分（过度焦虑）
        if any(c in title for c in ['完了', '死', '血亏', '崩盘']):
            score -= 10
        
        return min(100, max(0, score))
    
    def _analyze_elements(self, title: str) -> Dict:
        """分析标题包含的爆款元素"""
        elements = {
            'emotion': [],
            'numbers': [],
            'contrast': False,
            'question': False,
            'practical': False
        }
        
        # 检测情绪词
        for emotion, words in self.emotion_words.items():
            if any(w in title for w in words):
                elements['emotion'].append(emotion)
        
        # 检测数字
        if any(num in title for num in self.number_patterns):
            elements['numbers'] = [n for n in self.number_patterns if n in title]
        
        # 检测对比
        if any(c in title for c in ['vs', '对比', '差距', '赚', '亏']):
            elements['contrast'] = True
        
        # 检测疑问
        if any(c in title for c in ['？', '吗', '呢', '如何']):
            elements['question'] = True
        
        # 检测实用性
        if any(c in title for c in ['指南', '攻略', '教程', '避坑']):
            elements['practical'] = True
        
        return elements
    
    def _save_titles(self, titles: List[Dict], topic: str):
        """保存标题"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.output_dir / f'titles_{timestamp}.json'
        
        data = {
            'generated_at': datetime.now().isoformat(),
            'topic': topic,
            'count': len(titles),
            'titles': titles,
            'top_5': titles[:5]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"标题已保存：{filepath}")
    
    def get_best_titles(self, titles: List[Dict], count: int = 5) -> List[str]:
        """获取评分最高的标题"""
        sorted_titles = sorted(titles, key=lambda x: x['score'], reverse=True)
        return [t['title'] for t in sorted_titles[:count]]
    
    def format_for_display(self, titles: List[Dict]) -> str:
        """格式化标题列表供展示"""
        lines = ["爆款标题推荐（按评分排序）\n"]
        
        for i, t in enumerate(titles[:10], 1):
            score_emoji = '🔥' if t['score'] >= 80 else '📈' if t['score'] >= 60 else '📝'
            lines.append(f"{i}. {score_emoji}【{t['type']}】{t['title']}")
            lines.append(f"   评分:{t['score']} | 元素:{', '.join(t['elements'].get('emotion', [])) or '无'}")
            lines.append('')
        
        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试
    generator = ViralTitleGenerator()
    
    test_topic = "重庆小阳春买房时机分析"
    test_keywords = ['小阳春', '买房', '重庆', '时机']
    
    titles = generator.generate_titles(test_topic, test_keywords, count=35)
    
    print(generator.format_for_display(titles))
    print(f"\nTop 5 推荐：")
    for i, title in enumerate(generator.get_best_titles(titles, 5), 1):
        print(f"{i}. {title}")
