# -*- coding: utf-8 -*-
"""
光伏获客系统 - LLM内容增强模块 v0.3
修复验证逻辑 + 集成到content_generator
"""
import sys, os, json, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

if sys.platform == 'win32' and sys.stdout and hasattr(sys.stdout, 'buffer'):
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except ValueError:
        pass  # stdout closed, skip


class SolarLLMClient:
    """光伏内容LLM客户端"""

    def __init__(self):
        self.api_key = None
        self.api_url = None
        self.model = "deepseek-v4-flash"
        self._rate_limited = False  # 429限流保护标记
        self._last_rate_limit_time = None
        self._rate_limit_window = 3600  # 限流后1小时内不再尝试
        self._load_config()

    def _load_config(self):
        config_path = os.path.expanduser('~/.openclaw/openclaw.json')
        if not os.path.exists(config_path):
            return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            providers = cfg.get('models', {}).get('providers', {})
            for pname in ['sensenova', 'deepseek', 'openai', 'moonshot']:
                provider = providers.get(pname, {})
                key = provider.get('apiKey', '')
                base_url = provider.get('baseUrl', '')
                if key and base_url:
                    self.api_key = key
                    bu = base_url.rstrip('/')
                    if bu.endswith('/v1'):
                        self.api_url = bu + '/chat/completions'
                    else:
                        self.api_url = bu + '/v1/chat/completions'
                    if 'sensenova' in pname or 'deepseek' in pname:
                        self.model = 'deepseek-v4-flash'
                    break
        except Exception as e:
            pass  # 配置加载失败不影响模板fallback

    def generate_body(self, title: str, direction: str, source: str = "") -> str:
        if not self.api_key or not self.api_url:
            return ""

        prompt = f"""你是一位资深的光伏行业内容策划专家，擅长用短视频语言把复杂政策和技术讲清楚。

请根据以下热点标题，生成一段150字以内的短视频正文：

标题：{title}
方向：{direction}（policy/benefit/avoid/news/tech）
来源：{source}

要求：
1. 开头先复述核心信息（1句话概括）
2. 中间分2-3个点展开（每点用"→"连接）
3. 结尾给结论/行动建议
4. 禁止用专业术语，全部口语化
5. 总字数150字以内

直接输出正文，不要解释，不要加引号。"""

        for attempt in range(3):
            body = self._call_llm(prompt, max_tokens=400)
            if body and len(body) > 20:
                return body.strip()
            time.sleep(2 * (attempt + 1))
        return ""

    def generate_hook(self, title: str, direction: str) -> str:
        if not self.api_key or not self.api_url:
            return ""

        prompt = f"""你是一位资深的光伏行业内容策划专家，擅长用短视频语言提炼政策热点、制造用户兴趣。

请根据以下光伏热点标题，生成一个30字以内的爆款钩子：

标题：{title}
方向：{direction}

要求：
1. 必须含数字或问句（如"3个坑""赚多少""什么意思"）
2. 必须有情绪钩子（好奇/恐惧/利益/紧迫）
3. 口语化，像朋友圈聊天
4. 不要超过30字

直接输出钩子，不要解释。"""

        for attempt in range(3):
            hook = self._call_llm(prompt, max_tokens=100)
            if hook and len(hook) > 5:
                return hook.strip()
            time.sleep(2 * (attempt + 1))
        return ""

    def _call_llm(self, prompt: str, max_tokens: int = 200) -> str:
        import urllib.request
        try:
            body = json.dumps({
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": prompt}]
            }, ensure_ascii=False).encode("utf-8")

            req = urllib.request.Request(
                self.api_url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self._rate_limited = True
                self._last_rate_limit_time = time.time()
                self._log_error(f"LLM 429 rate limited, will skip for {self._rate_limit_window}s")
            else:
                self._log_error(f"LLM HTTP {e.code}: {e}")
            return ""
        except Exception as e:
            self._log_error(f"LLM error: {e}")
            return ""

    def is_available(self) -> bool:
        """检查LLM是否可用（含限流保护）"""
        if not self.api_key or not self.api_url:
            return False
        if self._rate_limited:
            # 检查限流窗口是否已过
            if self._last_rate_limit_time:
                elapsed = time.time() - self._last_rate_limit_time
                if elapsed < self._rate_limit_window:
                    return False
                else:
                    # 窗口已过，清除标记
                    self._rate_limited = False
                    self._last_rate_limit_time = None
        return True

    def _log_error(self, msg: str):
        """安全写日志，避免Windows stdout closed报错"""
        try:
            log_dir = BASE / "data" / "output"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"llm_errors_{datetime.now().strftime('%Y%m%d')}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} {msg}\n")
        except Exception:
            pass  # 日志写失败不能影响主流程

    def generate_hook(self, title: str, direction: str) -> str:
        if not self.api_key or not self.api_url:
            return ""
        prompt = f"你是光伏行业短视频专家，用口语化风格写一条50字以内的爆款钩子，主题是：{title}"
        for attempt in range(3):
            hook = self._call_llm(prompt, max_tokens=100)
            if hook and len(hook) > 5:
                return hook.strip()
            # 429限流时等待更长，否则短等待
            wait = 10 * (attempt + 1) if attempt > 0 else 2
            time.sleep(wait)
        self._log_error(f"LLM generate_hook failed after 3 attempts: {title[:30]}")
        return ""

    def generate_body(self, title: str, direction: str, source: str = "") -> str:
        if not self.api_key or not self.api_url:
            return ""
        prompt = (f"你是一位资深的光伏行业内容策划专家，擅长用短视频语言把复杂政策和技术讲清楚。\n\n"
                  f"请根据以下热点标题，生成一段150字以内的短视频正文，口语化、接地气：\n\n"
                  f"标题：{title}\n"
                  f"来源：{source}")
        for attempt in range(3):
            body = self._call_llm(prompt, max_tokens=300)
            if body and len(body) > 20:
                return body.strip()
            wait = 15 * (attempt + 1) if attempt > 0 else 3
            time.sleep(wait)
        self._log_error(f"LLM generate_body failed after 3 attempts: {title[:30]}")
        return ""


def enhance_content(content: dict, llm_client: SolarLLMClient) -> dict:
    """增强单条内容。LLM限流时自动fallback到模板内容，不覆盖原内容。
    只有LLM成功返回新内容时才替换，否则保持模板生成内容。
    """
    new_hook = llm_client.generate_hook(content["source_title"], content["direction"])
    new_body = llm_client.generate_body(content["source_title"], content["direction"], content["source"])

    # 只有LLM成功时才替换，否则保持模板生成的内容
    if new_hook:
        content["hook"] = new_hook
    if new_body:
        content["body"] = new_body
        content["enhanced"] = True
        content["enhanced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 没有新body说明LLM失败，保持模板fallback内容

    # 更新完整脚本（always，因为hook可能被更新了）
    content["full_script"] = f"{content['hook']}\n\n{content['body']}\n\n{content['cta']}"
    return content


if __name__ == "__main__":
    client = SolarLLMClient()
    print(f"LLM available: {client.is_available()}")
    print(f"API URL: {client.api_url}")

    test_title = "江苏镇江市：到2030年分布式光伏装机实现倍增，规模达5.6GW"
    print(f"\nTest: {test_title}")

    hook = client.generate_hook(test_title, "news")
    print(f"Hook: {hook}")

    body = client.generate_body(test_title, "news", "bjx")
    print(f"Body: {body[:120]}...")
