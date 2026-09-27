#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动创作引擎 V1.1
调用大模型 API 自动生成 2000-3000 字房地产文章

支持模型：
- 主系统模型（优先复用，无需额外配置）
- 通义千问（阿里）
- 文心一言（百度）
- Kimi（月之暗面）
- DeepSeek

作者：小智
版本：V1.1
创建时间：2026-03-25
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

sys.path.append(str(Path(__file__).parent))
from logger import logger


class AutoWriter:
    """
    自动创作引擎
    
    工作流程：
    1. 接收选题 + 知识卡片推荐
    2. 调用大模型 API 生成文章
    3. 输出完整文章（含标题 + 正文 + 互动引导）
    """
    
    def __init__(self, api_config: Optional[Dict] = None):
        self.api_config = api_config or self._load_api_config()
        self.output_dir = Path(__file__).parent.parent / 'pipeline_data' / 'auto_drafts'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 爆款文章结构模板
        self.article_structure = {
            'opening': '热点引入 + 核心观点（150 字）',
            'section1': '数据/事实支撑（500 字）',
            'section2': '深度分析/原因解读（600 字）',
            'section3': '实操建议/购房指南（500 字）',
            'section4': '案例/故事增强说服力（400 字）',
            'closing': '总结 + 互动引导（200 字）'
        }
        
        # 爆款元素库
        self.viral_elements = {
            'emotion_words': ['重磅', '刚刚', '注意', '警惕', '曝光', '揭秘', '真相', '信号', '变天', '必看'],
            'number_patterns': ['3 个', '5 大', '10 个', '90%', '50 万', '30%'],
            'contrast_patterns': ['之前 vs 现在', '买对 vs 买错', '赚 50 万 vs 亏 30 万'],
            'authority_sources': ['克而瑞', '重庆房管局', '国家统计局', '央行', '住建委'],
        }
        
        logger.info("自动创作引擎 V1.0 初始化完成")
    
    def _load_api_config(self) -> Dict:
        """加载 API 配置"""
        config_file = Path(__file__).parent.parent / 'api_config.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def write_article(self, topic: str, keywords: List[str], 
                      recommended_cards: List[Dict], 
                      word_count: int = 2500,
                      style: str = 'professional') -> Dict:
        """
        自动生成文章
        
        Args:
            topic: 选题标题
            keywords: 关键词列表
            recommended_cards: 推荐的知识卡片
            word_count: 目标字数
            style: 文章风格（professional/professional_casual/story）
        
        Returns:
            生成的文章（含标题/正文/元数据）
        """
        logger.info(f"开始创作：{topic}")
        
        # 构建提示词
        prompt = self._build_prompt(topic, keywords, recommended_cards, word_count, style)
        
        # 调用大模型 API
        article_content = self._call_llm_api(prompt)
        
        if not article_content:
            logger.error("API 调用失败")
            return self._generate_fallback_article(topic, keywords)
        
        # 解析文章（提取标题 + 正文）
        article = self._parse_article(article_content, topic)
        
        # 保存草稿
        self._save_draft(article)
        
        logger.info(f"文章生成完成：{len(article.get('content', ''))}字")
        return article
    
    def _build_prompt(self, topic: str, keywords: List[str], 
                      recommended_cards: List[Dict], 
                      word_count: int, style: str) -> str:
        """构建提示词"""
        
        # 知识卡片内容
        card_info = ""
        for card in recommended_cards[:3]:
            card_info += f"\n## 参考卡片：{card.get('title', '')}\n"
            for snippet in card.get('data_snippets', [])[:2]:
                card_info += f"- {snippet}\n"
        
        # 风格设定
        style_guide = {
            'professional': '专业严谨，数据支撑，适合政策解读/市场分析',
            'professional_casual': '专业但通俗，有个人观点，适合购房指南',
            'story': '故事化叙述，情感共鸣，适合案例分享'
        }
        
        prompt = f"""你是一位资深房地产自媒体作者，在百家号/头条号拥有 10 万 + 粉丝。

## 任务
根据以下选题创作一篇 {word_count}字左右的房地产文章。

## 选题信息
- 标题：{topic}
- 关键词：{', '.join(keywords)}
- 风格：{style_guide.get(style, '')}

## 参考素材
{card_info if card_info else '无特定参考，请基于你的知识库创作'}

## 文章要求
1. **开头抓人**：前 3 秒抓住读者注意力（用热点/数据/疑问开头）
2. **数据支撑**：引用具体数据（成交/价格/政策等）
3. **实用价值**：给读者可操作的建议
4. **情绪共鸣**：让读者有转发/评论的冲动
5. **避免 AI 味**：不要"总的来说/综上所述/值得注意的是"等表达

## 文章结构
1. 引言（150 字）：热点引入 + 核心观点
2. 数据/事实（500 字）：用具体数据支撑观点
3. 深度分析（600 字）：解读背后的原因/逻辑
4. 实操建议（500 字）：给读者的具体建议
5. 案例故事（400 字）：真实案例增强说服力
6. 总结互动（200 字）：总结 + 引导评论

## 爆款元素（至少使用 3 个）
- 情绪词：重磅、刚刚、注意、警惕、曝光、揭秘、真相
- 数字冲击：具体金额/比例/时间
- 对比冲突：前后对比/人群对比/买对买错对比
- 权威背书：官方数据/专家观点
- 实用价值：具体操作指南

## 输出格式
直接输出文章内容，不要解释。包含：
- 标题（1 个主标题 + 4 个备选标题）
- 正文（markdown 格式，用小标题分段）
- 互动引导（结尾引导评论）

开始创作："""
        
        return prompt
    
    def _call_llm_api(self, prompt: str) -> Optional[str]:
        """调用大模型 API（优先使用主系统模型）"""
        
        # 第 1 优先级：主系统模型（无需额外配置）
        try:
            return self._call_main_system(prompt)
        except Exception as e:
            logger.warning(f"主系统模型调用失败：{e}，尝试备用模型")
        
        # 第 2 优先级：配置的 API
        models = ['qwen', 'kimi', 'deepseek', 'wenxin']
        
        for model in models:
            if model not in self.api_config:
                continue
            
            try:
                if model == 'qwen':
                    return self._call_qwen(prompt)
                elif model == 'kimi':
                    return self._call_kimi(prompt)
                elif model == 'deepseek':
                    return self._call_deepseek(prompt)
                elif model == 'wenxin':
                    return self._call_wenxin(prompt)
            except Exception as e:
                logger.warning(f"{model} API 调用失败：{e}")
                continue
        
        logger.error("所有模型 API 调用失败")
        return None
    
    def _call_main_system(self, prompt: str) -> str:
        """
        调用MiniMax M2.7 API生成文章
        使用OpenClaw已配置的MiniMax API Key
        """
        import requests, json
        
        api_key = "sk-cp-UWJM1Y9JyzXSEzuMyDxSDGZOwJugKeloayveqA3Srgu67UoDYcQOpvAACdfr2598hwSdF8wU93xL-IgYt8rDiET7Ir0qr52DrifvrJIqDLwtnoM2yowfVJs"
        
        try:
            url = "https://api.minimaxi.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "MiniMax-M2.7",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.7
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                if content:
                    return content
        except Exception as e:
            logger.warning(f"MiniMax API调用失败: {e}")
        
        logger.error("所有模型API调用失败，返回占位内容")
        return ""
    
    def _call_qwen(self, prompt: str) -> str:
        """调用通义千问 API"""
        config = self.api_config.get('qwen', {})
        api_key = config.get('api_key', '')
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-plus",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {
                "max_tokens": 3000,
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        return result.get('output', {}).get('text', '')
    
    def _call_kimi(self, prompt: str) -> str:
        """调用 Kimi API"""
        config = self.api_config.get('kimi', {})
        api_key = config.get('api_key', '')
        
        url = "https://api.moonshot.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "moonshot-v1-8k",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    def _call_deepseek(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        config = self.api_config.get('deepseek', {})
        api_key = config.get('api_key', '')
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    def _call_wenxin(self, prompt: str) -> str:
        """调用文心一言 API"""
        config = self.api_config.get('wenxin', {})
        api_key = config.get('api_key', '')
        secret_key = config.get('secret_key', '')
        
        # 获取 access_token
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        token_response = requests.post(token_url, timeout=10)
        access_token = token_response.json().get('access_token', '')
        
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_output_tokens": 3000,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        return result.get('result', '')
    
    def _parse_article(self, content: str, default_topic: str) -> Dict:
        """解析文章（提取标题 + 正文）"""
        
        lines = content.split('\n')
        title = default_topic
        alt_titles = []
        content_lines = []
        in_titles = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测标题行
            if line.startswith('# ') and not title.startswith('#'):
                title = line.replace('# ', '').strip()
                in_titles = True
            elif in_titles and (line.startswith('- ') or line.startswith('备选')):
                alt_title = line.replace('- ', '').replace('备选', '').replace('标题', '').strip()
                if alt_title and len(alt_title) < 50:
                    alt_titles.append(alt_title)
            else:
                in_titles = False
                content_lines.append(line)
        
        # 如果没解析出标题，用选题
        if title == default_topic or not title:
            title = default_topic
        
        # 限制备选标题数量
        alt_titles = alt_titles[:4]
        
        return {
            'title': title,
            'alt_titles': alt_titles,
            'content': '\n'.join(content_lines),
            'word_count': len(content_lines),
            'generated_at': datetime.now().isoformat(),
            'raw_content': content
        }
    
    def _generate_fallback_article(self, topic: str, keywords: List[str]) -> Dict:
        """兜底文章（API 失败时用）"""
        
        return {
            'title': topic,
            'alt_titles': [f"{topic} - 深度解读", f"{topic} - 完整版"],
            'content': f"""# {topic}

## 引言

关于{'、'.join(keywords)}的话题，最近引起了很多人的关注。今天我们来详细分析一下。

## 核心观点

这个话题涉及到多个方面，需要从不同角度来理解。

## 数据分析

从数据来看，当前的情况比较复杂。具体数据需要参考官方统计。

## 实操建议

1. 关注官方政策发布
2. 多对比几个楼盘/方案
3. 根据自身情况做决策

## 总结

希望这篇文章对你有所帮助。你有什么看法？欢迎在评论区留言讨论。
""",
            'word_count': 300,
            'generated_at': datetime.now().isoformat(),
            'fallback': True
        }
    
    def _save_draft(self, article: Dict):
        """保存草稿"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存完整文章
        filename = f"auto_draft_{timestamp}.md"
        filepath = self.output_dir / filename
        
        content = f"# {article['title']}\n\n"
        if article.get('alt_titles'):
            content += f"**备选标题**：{' | '.join(article['alt_titles'])}\n\n"
        content += f"**生成时间**：{article.get('generated_at', '')}\n\n"
        content += f"**字数**：{article.get('word_count', 0)}\n\n"
        content += "---\n\n"
        content += article.get('content', '')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 保存元数据
        meta = {
            'title': article['title'],
            'alt_titles': article['alt_titles'],
            'word_count': article['word_count'],
            'generated_at': article['generated_at'],
            'filename': filename
        }
        meta_file = self.output_dir / f"meta_{timestamp}.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        logger.info(f"草稿已保存：{filepath}")


if __name__ == '__main__':
    # 测试
    writer = AutoWriter()
    
    test_topic = "重庆小阳春来了，现在是不是买房好时机？"
    test_keywords = ['小阳春', '买房', '重庆', '时机']
    test_cards = [
        {
            'title': '市场周期分析',
            'data_snippets': ['见底信号：成交量连续 3 月回升 + 库存下降']
        }
    ]
    
    article = writer.write_article(test_topic, test_keywords, test_cards)
    print(f"\n生成文章：{article['title']}")
    print(f"字数：{article['word_count']}")
    print(f"备选标题：{len(article.get('alt_titles', []))}个")
