# -*- coding: utf-8 -*-
"""
生成口播脚本 - 中国贸易朋友圈加速扩容
"""
import os, sys, json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 脚本内容（基于公开数据）
script_data = {
    "title": "中国贸易朋友圈加速扩容",
    "hook": {
        "text": "你知道吗？中国的\u2018贸易朋友圈\u2019已经扩张到了160多个国家和地区！",
        "duration": 4
    },
    "sections": [
        {
            "narration": "最新数据显示，中国已成为全球160多个国家和地区的主要贸易伙伴，比2020年增加了20多个。",
            "data_point": "160+ 主要贸易伙伴",
            "interpretation": "这个数字意味着什么？意味着地球上大部分地区，都在和中国做生意。",
            "duration": 6
        },
        {
            "narration": "其中，RCEP成员国是中国贸易的核心圈。15个国家，去年进出口额达到12.6万亿元，占中国外贸总额的30%以上。",
            "data_point": "RCEP: 15国, 12.6万亿",
            "interpretation": "东盟连续四年保持中国第一大贸易伙伴地位。",
            "duration": 7
        },
        {
            "narration": "除了RCEP，中国还和24个国家签署了自贸协定，涉及31个国家和地区。从智利到挪威，从巴基斯坦到哥斯达黎加，朋友圈遍布五大洲。",
            "data_point": "24个FTA, 31个伙伴",
            "interpretation": "自贸协定数量，中国排名全球第三。",
            "duration": 7
        },
        {
            "narration": "金砖国家扩容后，中国贸易朋友圈再添新成员。巴西、南非、埃及、埃塞俄比亚等国，都是中国重要的新兴市场。",
            "data_point": "金砖10国",
            "interpretation": "新兴市场正在成为中国贸易增长的新引擎。",
            "duration": 6
        },
        {
            "narration": "从2001年加入WTO到如今，中国从一个贸易大国成长为全球贸易第一大国。160多个贸易伙伴，背后是中国深度融入全球经济的缩影。",
            "data_point": "全球第一",
            "interpretation": "这，就是中国贸易朋友圈的\u2018加速度\u2019。",
            "duration": 7
        }
    ],
    "outro": {
        "text": "你怎么看中国贸易朋友圈的扩张？评论区告诉我。点赞关注，每天看数据。",
        "duration": 4
    },
    "metadata": {
        "estimated_duration_seconds": 35,
        "word_count": 280,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
}

# 计算总字数和时长
total_words = len(script_data['hook']['text']) + sum(len(s['narration']) for s in script_data['sections']) + len(script_data['outro']['text'])
total_duration = sum(s.get('duration', 5) for s in script_data['sections']) + script_data['hook']['duration'] + script_data['outro']['duration']
script_data['metadata']['word_count'] = total_words
script_data['metadata']['estimated_duration_seconds'] = total_duration

# 保存脚本
output_dir = os.path.join(BASE_DIR, 'data', 'scripts')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'trade_circle_script.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(script_data, f, ensure_ascii=False, indent=2)

print(f"脚本已保存: {output_path}")
print(f"总字数: {total_words}, 预计时长: {total_duration}秒")

# 提取完整文本用于TTS
full_text = script_data['hook']['text']
for s in script_data['sections']:
    full_text += s['narration']
full_text += script_data['outro']['text']

tts_output = os.path.join(BASE_DIR, 'data', 'audio', 'trade_circle_tts.mp3')
os.makedirs(os.path.dirname(tts_output), exist_ok=True)

import asyncio
import edge_tts

async def generate_tts():
    """使用Edge TTS生成配音"""
    try:
        communicate = edge_tts.Communicate(full_text, "zh-CN-XiaoxiaoNeural")
        await communicate.save(tts_output)
        print(f"配音已生成: {tts_output}")
    except Exception as e:
        print(f"TTS生成失败: {e}")

asyncio.run(generate_tts())

# 输出完整文本到文件（用于字幕）
subtitles_path = os.path.join(BASE_DIR, 'data', 'scripts', 'trade_circle_subtitles.txt')
with open(subtitles_path, 'w', encoding='utf-8') as f:
    f.write(full_text)
print(f"字幕文本已保存: {subtitles_path}")
