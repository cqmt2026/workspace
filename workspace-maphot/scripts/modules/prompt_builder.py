# -*- coding: utf-8 -*-
"""
脚本生成模块 - Prompt构建器
职责：根据选题数据+栏目类型，组装LLM prompt
输入：选题标题、数据列表、栏目类型、配置
输出：结构化prompt字符串
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'script_gen_config.json')


def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


class PromptBuilder:
    """Prompt构建器"""

    def __init__(self):
        self.config = load_config()

    def build(self, title, data_list, category="一张图"):
        """
        构建LLM prompt
        
        Args:
            title: 选题标题
            data_list: 数据列表 [{name, rank, data1, data2, tag, desc}, ...]
            category: 栏目类型
            
        Returns:
            prompt字符串
        """
        cat_config = self.config['categories'].get(category, self.config['categories']['一张图'])
        
        # 构建数据摘要
        data_summary = "\n".join([
            f"第{item.get('rank', i+1)}名：{item.get('name','')} | {item.get('data1','')} | {item.get('data2','')}"
            for i, item in enumerate(data_list)
        ])
        
        hook_types_str = "、".join(cat_config['hook_types'])
        outro_types_str = "、".join(cat_config['outro_types'])
        spoken_rules_str = "\n".join([f"- {r}" for r in self.config['spoken_rules']])
        
        today = self._get_today()
        
        prompt = f"""你是一个抖音短视频脚本文案专家，擅长用地图+数据讲故事，产出的每条视频都是百万播放爆款。

【选题】{title}
【栏目类型】{category}
【数据】{data_summary}
【目标字数】约{cat_config['intro_word_count'] + len(data_list) * cat_config['per_item_word_count'] + cat_config['outro_word_count']}字
【节奏】{cat_config['pace']}，每段约{cat_config['duration_per_item']}秒

## 爆款文案公式（必须遵循）

### 1. 黄金3秒钩子 — 制造反差/悬念/感官冲击
❌ 错误示范："上半年XX出炉，前X名有哪些？我们来看一张图。"
✅ 正确写法：
- 反常识："你以为广东外贸最强？其实西藏增速才是全国第一，差了X倍！"
- 感官描述："同样的沿海城市，为什么这里充电最快？"
- 数字对比："同一个城市内部，GDP差距39倍！浦东17502亿vs崇明448亿"
- 身份代入："所有广东人注意！你的家乡外贸增速排第几？"
- 悬念提问："不靠海不沿江的地方，外贸增速也能排第一？"

### 2. 三层递进叙事（秒懂山河级别）
❌ 错误写法："第一名XX，第二名XX，第三名XX..."
✅ 正确结构：
- 第一层（现象）：先摆一个反常现象/认知冲突，让观众产生"为什么"的疑问
- 第二层（数据）：用具体数字支撑现象，逐项解读时用比喻/类比让普通人听懂
- 第三层（本质）：揭示现象背后的根本原因，比表面答案更深一层

**关键：每层都要有具体例子，不要空讲道理。**
**比喻要求：用生活化比喻解释抽象概念——比如"广东给普通人的是失败地板，江浙沪给精英的是成功天花板"**

### 3. 选择题结尾 + 金句收尾
❌ 错误示范："还有更猛的数据，关注我下期继续。"
✅ 正确写法：
- 结尾互动："今年夏天你打算怎么过？继续在家躺着吹空调，还是杀去山西感受一下真正的自然凉？"
- 金句收尾：全片最后必须有一句可截图转发的金句，总结核心观点
  示例："选城市不是选天花板有多高，而是选地板有多厚。"
  示例："真正能抢人的城市，是能一边搞高精尖、一边容得下菜市场和城中村的'大熔炉'。"
- 投票式提问："从A到B，你觉得哪个最有潜力？评论区投票。"

## 口语化铁则（必须遵守）
{spoken_rules_str}

请生成一个抖音短视频脚本，严格按照以下JSON格式输出：

{{
  "title": "{title}",
  "date": "{today}",
  "category": "{category}",
  "metadata": {{
    "word_count": 实际字数,
    "estimated_duration_seconds": 预计时长,
    "tts_speed": 1.0
  }},
  "hook": {{
    "type": "从以下类型中选择：{hook_types_str}",
    "text": "钩子文案（3秒内抓住注意力，必须用感官描述/反差感/数字对比/认知冲突）"
  }},
  "sections": [
    {{
      "order": 序号,
      "time_range": "时间范围，如0-5s",
      "visual": "画面描述（地图区域+标注内容）",
      "narration": "口播文案（口语化，数据+解读各一句，不要'第一名''第二名'这种序号线）",
      "data_point": "核心数据（用于大字标注）",
      "interpretation": "一句话解读（用比喻/类比让普通人听懂）"
    }}
  ],
  "outro": {{
    "type": "从以下类型中选择：{outro_types_str}",
    "text": "结尾文案（必须是选择题或投票式提问，降低回复门槛）",
    "golden_sentence": "全片金句（一句话总结本质，可截图转发）"
  }},
  "full_text": "完整口播稿（按sections顺序拼接narration，必须是连贯的故事线）",
  "subtitle_lines": [
    "字幕第1行（不超过15字）"
  ]
}}

【强制校验清单（生成前自检）】
- [ ] 钩子用了感官描述/反差/数字对比/认知冲突吗？不是平淡陈述
- [ ] 正文是三层递进（现象→数据→本质）还是单层罗列？必须三层递进
- [ ] 每项有数据+比喻/类比解读吗？
- [ ] 有转折或反转吗？
- [ ] 结尾是选择题/投票式提问吗？
- [ ] 有可截图转发的金句吗？
- [ ] 全文口语化，无书面连接词？
- [ ] 字数匹配目标时长（≥75字/分钟）？

【格式要求】
- 只输出JSON，不要任何解释
- hook.text必须是能让人停下来的钩子（感官描述/反差/数字对比/认知冲突）
- 每个section.narration不要写"第一名XX"，要写"XX这个地方..."
- outro.text必须是选择题或投票式互动
- outro.golden_sentence必须有一句可截图转发的金句
- full_text必须是连贯的三层递进故事线（现象→数据→本质），不是序号罗列
- subtitle_lines每行不超过15字
- 全文信息密度必须≥75字/分钟（目标90字/分钟）"""
        
        return prompt

    def build_with_recommend(self, title, data_list, category="一张图", recommend=None):
        """
        构建带推荐方案的LLM prompt
        
        Args:
            title: 选题标题
            data_list: 数据列表
            category: 栏目类型
            recommend: 推荐方案字典（含writing_techniques, map_forms等）
        """
        base_prompt = self.build(title, data_list, category)
        
        if recommend:
            techniques = recommend.get('writing_techniques', [])
            map_forms = recommend.get('map_forms', [])
            content_type = recommend.get('content_type', '')
            emotion = recommend.get('emotion', '')
            
            recommend_section = f"""

【推荐方案（请严格遵循）】
- 推荐文案手法：{', '.join(techniques) if techniques else '无'}
- 推荐地图形式：{', '.join(map_forms) if map_forms else '无'}
- 内容类型：{content_type}
- 情感基调：{emotion}

请在脚本中融入以上推荐手法，在visual字段中优先使用推荐的地图形式。
"""
            # 插入到JSON格式要求之前
            marker = "请生成一个抖音短视频脚本，严格按照以下JSON格式输出："
            if marker in base_prompt:
                idx = base_prompt.index(marker)
                base_prompt = base_prompt[:idx] + recommend_section + "\n" + base_prompt[idx:]
            else:
                base_prompt += recommend_section
        
        return base_prompt

    def _get_today(self):
        from datetime import date
        return date.today().isoformat()
