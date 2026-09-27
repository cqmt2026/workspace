# -*- coding: utf-8 -*-
"""单条高质量内容生成 - 用LLM增强模板"""
import sys, os, json, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def safe_print(msg):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

from core.llm_enhancer import SolarLLMClient
from core.database import init_db

init_db()
llm = SolarLLMClient()

if not llm.is_available():
    safe_print("LLM不可用")
    sys.exit(1)

safe_print(f"LLM可用: {llm.model}")

def llm_enhance(title, source, direction):
    hook = llm.generate_hook(title, direction)
    time.sleep(1)
    body = llm.generate_body(title, direction, source)
    time.sleep(1)
    if not body or len(body) < 30:
        safe_print("  LLM body为空，尝试备用方案...")
        for attempt in range(2):
            import urllib.request
            try:
                body_prompt = (f"你是光伏行业短视频内容策划专家。\n\n"
                              f"请根据以下标题，生成一段120-180字的短视频正文，口语化、接地气：\n\n"
                              f"标题：{title}\n来源：{source}\n方向：{direction}")
                data = json.dumps({
                    "model": llm.model,
                    "max_tokens": 400,
                    "temperature": 0.7,
                    "messages": [{"role": "user", "content": body_prompt}]
                }, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(
                    llm.api_url, data=data,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {llm.api_key}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    body = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if body and len(body) > 30:
                        break
            except Exception as e:
                safe_print(f"  备用方案失败: {e}")
            time.sleep(3)
    return hook or title[:25], body or "内容待补充"

safe_print("\n生成测试内容...\n")

# 用单引号包裹含双引号的字符串
test_contents = [
    ('上海黄浦区十五五规划：新建机关办公和教育建筑屋顶安装光伏面积比例>=50%', 'solarbe', 'policy'),
    ('正泰晶澳英利通威等6家企业入围中核4.3GW光伏组件集采订单', 'bjx', 'tech'),
    ('冀东油田29.35MW分布式光伏项目并网', 'bjx', 'news'),
]

output_dir = BASE / "data" / "output" / "rewritten"
output_dir.mkdir(parents=True, exist_ok=True)

for i, (title, source, direction) in enumerate(test_contents):
    safe_print(f"[{i+1}/3] {title[:40]}... ({direction})")
    hook, body = llm_enhance(title, source, direction)

    cta_map = {
        "policy": "你家屋顶能装几kW？私信我省份+面积，免费出当地补贴政策+收益测算表。",
        "tech": "不懂怎么选组件？私信我城市+屋顶类型，帮你推荐适合的光伏方案。",
        "news": "想看更多光伏行业深度解读？私信关注，每天一条行业情报。",
    }

    content = {
        "title": title,
        "source": source,
        "direction": direction,
        "hook": hook,
        "body": body,
        "cta": cta_map.get(direction, cta_map["news"]),
        "tracking_id": f"PV_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
    }

    md = f"# {content['tracking_id']}\n来源: {source}\n方向: {direction}\n\n## 钩子\n{content['hook']}\n\n## 正文\n{content['body']}\n\n## CTA\n{content['cta']}\n\n---\n*PV获客系统生成*"
    md_file = output_dir / f"{content['tracking_id']}_v2.md"
    md_file.write_text(md, encoding="utf-8")

    safe_print(f"  钩子: {hook[:45]}...")
    safe_print(f"  正文: {body[:80]}...")
    safe_print(f"  保存: {md_file.name}")
    time.sleep(2)

safe_print(f"\n完成! 检查 output/rewritten/ 目录下的 *_v2.md 文件")
