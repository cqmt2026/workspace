# -*- coding: utf-8 -*-
"""
TTS Generator - 配音生成模块
职责：使用 Edge TTS 生成语音配音
"""
import os
import json
import logging
import random
import asyncio
import edge_tts

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



# P2: 多音色轮换配置
VOICES = {
    'female_natural': 'zh-CN-XiaoxiaoNeural',   # 女性自然音（默认）
    'female_news': 'zh-CN-XiaoyiNeural',         # 女性新闻播报
    'male_warm': 'zh-CN-YunxiNeural',            # 男性温暖音
    'male_news': 'zh-CN-YunyangNeural',          # 男性新闻播报
    'female_cute': 'zh-CN-liliangNeural',        # 女性可爱音
}

# 按题材类型推荐音色
VOICE_BY_CATEGORY = {
    '深一度': 'male_warm',        # 深度分析用沉稳男声
    '追热点': 'female_natural',   # 热点追踪用自然女声
    '一张图': 'female_news',      # 数据地图用新闻播报音
}

class TtsGenerator:
    """TTS语音生成器"""
    
    def __init__(self, voice=None, rate="+10%", category=None):
        """P2: 支持多音色轮换
        
        Args:
            voice: 指定音色名称（如 'female_natural'）或语音名（如 'zh-CN-XiaoxiaoNeural'）
            rate: 语速调整
            category: 选题类型（深一度/追热点/一张图），用于自动选择音色
        """
        if voice is None:
            # 根据题材类型自动选择音色
            if category and category in VOICE_BY_CATEGORY:
                voice_key = VOICE_BY_CATEGORY[category]
            else:
                # 默认随机选择一个女声（避免单调）
                voice_keys = ['female_natural', 'female_news', 'male_warm']
                voice_key = random.choice(voice_keys)
            voice = VOICES[voice_key]
        elif voice in VOICES:
            voice = VOICES[voice]
        self.voice = voice
        self.rate = rate
        self.voice = voice
        self.rate = rate
    
    def generate_from_script(self, script_path, category="一张图", video_id=None, voice=None):
        """根据脚本JSON生成配音
        
        支持的脚本格式：
          1. segments[n].narration（标准格式）
          2. sections[n].narration（旧格式）
          3. sections[n].data_point + interpretation（简化格式，自动拼接为口播）
          4. hook.text + sections[n].narration + outro.text
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load script: {e}")
            return None
        
        # 拼接所有旁白
        full_text = ''
        
        segments = script.get('segments', [])
        if segments:
            for seg in segments:
                full_text += seg.get('narration', '') + ' '
        else:
            hook = script.get('hook', {}).get('text', '')
            if hook:
                full_text += hook + ' '
            for sec in script.get('sections', []):
                narration = sec.get('narration', '')
                if narration:
                    full_text += narration + ' '
                else:
                    # fallback: 拼接 data_point + interpretation 作为口播
                    dp = sec.get('data_point', '')
                    interp = sec.get('interpretation', '')
                    if dp:
                        full_text += dp + '。'
                    if interp:
                        full_text += interp + '。'
            outro = script.get('outro', {}).get('text', '')
            if outro:
                full_text += outro + ' '
        
        if not full_text.strip():
            logger.error("Empty narration text")
            return None
        
        output_dir = os.path.join(BASE_DIR, 'data', 'audio')
        os.makedirs(output_dir, exist_ok=True)
        
        # 优先用video_id，其次script.city，兜底从script_path文件名推断
        if not video_id:
            video_id = script.get('city')
        if not video_id:
            video_id = os.path.splitext(os.path.basename(script_path))[0]
            # 去掉_script后缀
            if video_id.endswith('_script'):
                video_id = video_id[:-len('_script')]
        
        output_path = os.path.join(output_dir, f"{video_id}_tts.mp3")
        
        try:
            asyncio.run(self._generate(full_text.strip(), output_path))
            logger.info(f"TTS generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    async def _generate(self, text, output_path):
        """异步生成TTS"""
        communicate = edge_tts.Communicate(text, voice=self.voice, rate=self.rate)
        await communicate.save(output_path)
    
    def generate(self, text, output_path=None):
        """直接生成TTS（兼容旧接口）"""
        if not output_path:
            output_dir = os.path.join(BASE_DIR, 'data', 'audio')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'output_tts.mp3')
        
        try:
            asyncio.run(self._generate(text, output_path))
            return output_path
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    def save(self, text, output_path):
        """保存TTS（兼容旧接口）"""
        return self.generate(text, output_path)


if __name__ == '__main__':
    gen = TtsGenerator()
    path = gen.generate("深圳，中国改革开放的窗口，2026年GDP达到3.46万亿，排名全国城市第三。")
    print(f"Generated: {path}")