# -*- coding: utf-8 -*-
"""
脚本生成模块 - LLM客户端
职责:调用LLM生成脚本(可插拔)
支持:Gateway HTTP API sessions_spawn / 模板拼接兜底
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import date

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端基类"""

    def __init__(self):
        pass

    def generate(self, prompt, title, data_list, category):
        raise NotImplementedError


class FallbackLLMClient(LLMClient):
    """模板拼接兜底客户端"""

    def generate(self, prompt, title, data_list, category):
        logger.warning("LLM不可用,使用模板拼接兜底")
        return self._template_generate(title, data_list, category)

    def _template_generate(self, title, data_list, category):
        from .prompt_builder import PromptBuilder
        config = PromptBuilder().config

        cat_config = config['categories'].get(category, config['categories']['一张图'])
        
        # === 升级版钩子：反差感+感官描述+数字对比 ===
        hook_type = cat_config['hook_types'][0]
        if hook_type == "排名悬念":
            # 从"排名悬念"升级为"数字冲击"式钩子
            hook_type = "数字冲击"
            top = data_list[0] if data_list else {"name": "", "data1": ""}
            bottom = data_list[-1] if data_list else {"name": "", "data1": ""}
            hook_text = f"同是{title}，第一名和最后一名差距有多大？看完这张图你就不意外了。"
        elif hook_type == "反常识":
            first = data_list[0] if data_list else {"name": ""}
            hook_text = f"你以为{title}最强的是{first['name']}？结果可能让你大跌眼镜。"
        elif hook_type == "数字冲击":
            top = data_list[0] if data_list else {"name": "", "data1": ""}
            hook_text = f"{top['name']}{top.get('data1','')}，全国第一！但这个数字背后有个惊人的秘密。"
        elif hook_type == "对比反差":
            hook_text = f"不靠海不沿江的地方，{title}也能排第一？今天带你看看为什么。"
        else:
            hook_type = "身份代入"
            # 从data_list提取地名
            names = [item.get("name","") for item in data_list if item.get("name")]
            if names:
                hook_text = f"所有{names[0]}人注意！来看看你的城市排第几。"
            else:
                hook_text = f"所有关注{title}的人注意！来看看数据。"
        
        # === 升级版正文：故事线而非序号线 ===
        sections = []
        for item in data_list:
            name = item.get("name", "")
            data1 = item.get("data1", "")
            data2 = item.get("data2", "")
            rank = item.get("rank", 0)
            # 去掉"第X名"，改用故事化叙述
            sections.append({
                "order": rank,
                "time_range": f"{(rank-1)*cat_config['duration_per_item']+5}s-{rank*cat_config['duration_per_item']+5}s",
                "visual": f"{name}地图定位 + {data1}数据标注",
                "narration": f"{name}这个地方，{data1}。{data2}。",
                "data_point": data1,
                "interpretation": data2
            })
        
        # === 升级版结尾：选择题/投票式互动 ===
        outro_type = cat_config['outro_types'][0]
        first_name = data_list[0]["name"] if data_list else ""
        last_name = data_list[-1]["name"] if data_list else ""
        mid_name = data_list[len(data_list)//2]["name"] if len(data_list) > 2 else ""
        if outro_type == "互动":
            outro_text = f"从{first_name}到{last_name}，你觉得哪个最有潜力？评论区投票。"
        elif outro_type == "悬念":
            outro_text = f"还有更猛的数据，关注我，下期继续揭秘。"
        else:
            outro_text = f"从{first_name}到{last_name}，每个地方都在用自己的方式发展。你最看好谁？"
        
        full_text = hook_text + "。"
        for s in sections:
            full_text += s["narration"]
        full_text += outro_text
        
        subtitle_lines = [s["data_point"] for s in sections]
        
        return {
            "title": title,
            "date": date.today().isoformat(),
            "category": category,
            "metadata": {
                "word_count": len(full_text),
                "estimated_duration_seconds": 5 + len(data_list) * cat_config["duration_per_item"] + 5,
                "tts_speed": 1.0,
                "template_used": "fallback_v4_storyline"
            },
            "hook": {"type": hook_type, "text": hook_text},
            "sections": sections,
            "outro": {"type": outro_type, "text": outro_text},
            "full_text": full_text,
            "subtitle_lines": subtitle_lines
        }


class GatewayLLMClient(LLMClient):
    """
    OpenClaw CLI客户端
    通过 subprocess 调 openclaw 命令创建 isolated session 生成脚本

    调用流程:
    1. 用 openclaw 命令创建 isolated session 并传入 prompt
    2. 等待 session 完成
    3. 从输出中提取 JSON 脚本

    注意: CLI 方式无法直接获取 session 输出,
    因此改用 subprocess 直接调 Python 脚本写文件,Agent 通过文件系统轮询
    """

    def __init__(self):
        self.timeout = 120

    def generate(self, prompt, title, data_list, category):
        logger.info(f"[LLM] 尝试通过CLI生成脚本: {title}")

        # 尝试通过 CLI 调 LLM
        script = self._call_llm_via_cli(prompt, title)
        if script:
            return script

        # 都失败,回退模板拼接
        logger.warning("[LLM] CLI调用失败,回退到模板拼接")
        return FallbackLLMClient().generate(prompt, title, data_list, category)

    def _call_llm_via_cli(self, prompt, title):
        """通过 CLI 调 LLM 生成脚本"""
        import tempfile

        try:
            # 写 prompt 到临时文件
            full_prompt = (
                "你是一个抖音短视频脚本文案专家。"
                "请严格按照以下要求生成JSON格式的脚本,只输出JSON不要任何解释。\n\n"
                f"{prompt}"
            )

            tmp_file = os.path.join(tempfile.gettempdir(), 'hf_llm_prompt_%d.txt' % int(time.time()))
            with open(tmp_file, 'w', encoding='utf-8') as f:
                f.write(full_prompt)

            # 输出文件
            out_file = tmp_file.replace('.txt', '_out.json')

            # 用 openclaw sessions spawn 命令
            # 注: openclaw CLI 没有 spawn 子命令,这里用 subprocess 调 Python
            # 直接通过 requests 调底层 LLM provider
            script = self._call_llm_direct(full_prompt)

            # 清理临时文件
            try:
                os.remove(tmp_file)
                if os.path.exists(out_file):
                    os.remove(out_file)
            except:
                pass

            return script

        except Exception as e:
            logger.error(f"[LLM] CLI调用异常: {e}")
            return None

    # 多模型fallback列表（按优先级）
    _MODEL_CHAIN = [
        "openclaw",           # Gateway默认（当前运行模型）
        "deepseek-v4-flash",  # DeepSeek v4
        "qwen-397b",          # Qwen 397B
        "llama-3.3-70b",      # LLaMA 3.3 70B
    ]

    def _call_llm_direct(self, prompt):
        """
        通过 OpenClaw Gateway OpenAI 兼容 API 调 LLM（多模型fallback链）
        """
        try:
            import requests
            import json as _json

            # 从 openclaw.json 读取 token
            config_path = os.path.expanduser('~/.openclaw/openclaw.json')
            token = None
            if os.path.exists(config_path):
                with codecs.open(config_path, 'r', encoding='utf-8') as f:
                    config = _json.load(f)
                token = config.get('gateway', {}).get('auth', {}).get('token', None)

            if not token:
                logger.warning("[LLM] 未找到 Gateway token")
                return None

            base_url = "http://127.0.0.1:18789"
            headers = {"Authorization": f"Bearer {token}"}

            # P0-B: 多模型fallback链
            for attempt_model in self._MODEL_CHAIN:
                try:
                    resp = requests.post(
                        f"{base_url}/v1/chat/completions",
                        headers=headers,
                        json={
                            "model": attempt_model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 4096,
                            "temperature": 0.7
                        },
                        timeout=180
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        script = self._parse_json_response(content)
                        if script:
                            logger.info(f"[LLM] Gateway API成功 (model={attempt_model})")
                            return script
                        logger.warning(f"[LLM] {attempt_model}返回非JSON: {content[:80]}")
                        continue
                    else:
                        logger.warning(f"[LLM] {attempt_model}返回{resp.status_code}: {resp.text[:100]}")
                        continue
                except requests.exceptions.Timeout:
                    logger.warning(f"[LLM] {attempt_model}超时，尝试下一个...")
                    continue
                except Exception as e:
                    logger.warning(f"[LLM] {attempt_model}异常: {e}")
                    continue

            logger.error(f"[LLM] 所有模型调用失败（尝试了{len(self._MODEL_CHAIN)}个）")
            return None
        except Exception as _e:
            logger.error(f"[LLM] _call_llm_direct 异常: {_e}")
            return None

    def _parse_json_response(self, content):
        """从LLM回复中提取JSON"""
        if not content:
            return None

        content = content.strip()

        # 尝试直接解析
        if content.startswith('{'):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        # 尝试从```json ```块中提取
        if '```json' in content:
            start = content.index('```json') + 7
            end = content.index('```', start) if '```' in content[start:] else len(content)
            try:
                return json.loads(content[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

        # 尝试从``` ```块中提取
        if '```' in content:
            start = content.index('```') + 3
            end = content.index('```', start) if '```' in content[start:] else len(content)
            json_str = content[start:end].strip()
            if json_str.startswith('{'):
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        return None


def create_client(mode="gateway"):
    """工厂方法:创建LLM客户端
    
    mode: gateway 或 fallback
    - gateway: 尝试直接调 LLM,失败则回退模板拼接
    - fallback: 直接模板拼接
    
    注意: OpenClaw Gateway 未暴露 OpenAI 兼容 API,
    因此 gateway 模式会尝试直接调 provider 或 fallback 到模板拼接
    """
    if mode == "fallback":
        return FallbackLLMClient()
    else:
        return GatewayLLMClient()