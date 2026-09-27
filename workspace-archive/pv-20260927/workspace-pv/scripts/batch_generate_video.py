# -*- coding: utf-8 -*-
"""批量生成抖音视频 - 使用video_composer"""
import sys, os, json, time
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def safe_print(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

from core.video_composer import PVVideoComposer

# 加载A级内容
content_dir = BASE / "data" / "output" / "llm_generated"
json_file = content_dir / "llm_generated_20260820.json"
with open(json_file, "r", encoding="utf-8") as f:
    contents = json.load(f)

# 筛选A级（正文>=100字且无占位符）
import re
a_level = []
for c in contents:
    body_len = len(c.get("body",""))
    has_placeholder = any(x in c.get("hook","") + c.get("body","") + c.get("cta","") for x in ["测试", "占位符", "{title"])
    has_number_or_q = bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))
    if body_len >= 100 and not has_placeholder and has_number_or_q:
        a_level.append(c)

safe_print(f"加载 {len(a_level)} 条A级内容")

# 初始化合成器
composer = PVVideoComposer()

# 输出目录
output_dir = BASE / "data" / "output" / "douyin_videos"
output_dir.mkdir(parents=True, exist_ok=True)

results = []
for i, c in enumerate(a_level):
    tracking_id = c.get("tracking_id", f"PV_{i+1}")
    safe_print(f"\n[{i+1}/{len(a_level)}] 生成视频: {tracking_id}")
    safe_print(f"  方向: {c['direction']}")
    safe_print(f"  标题: {c['hook'][:30]}...")

    # 构造脚本数据
    script_data = {
        "title": c["hook"],
        "body": c["body"],
        "cta": c["cta"],
        "full_script": f"{c['hook']}\n\n{c['body']}\n\n{c['cta']}",
        "tracking_id": tracking_id,
        "direction": c["direction"],
        "geo_primary_province": "",  # 暂不指定省份
    }

    # 合成视频
    output_path = output_dir / f"{tracking_id}.mp4"
    try:
        result = composer.synthesize_video(script_data, str(output_path))
        if result and os.path.exists(result):
            size_kb = os.path.getsize(result) // 1024
            safe_print(f"  ✅ 成功: {size_kb}KB")
            results.append({"id": tracking_id, "status": "ok", "path": result, "size_kb": size_kb})
        else:
            safe_print(f"  ❌ 失败: video_composer返回空")
            results.append({"id": tracking_id, "status": "failed", "reason": "composer returned None"})
    except Exception as e:
        safe_print(f"  ❌ 异常: {e}")
        results.append({"id": tracking_id, "status": "error", "reason": str(e)[:50]})
    time.sleep(2)  # 避免FFmpeg冲突

# 保存结果
out_json = output_dir / "generation_result.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

ok_count = sum(1 for r in results if r["status"] == "ok")
safe_print(f"\n{'='*50}")
safe_print(f"完成! {ok_count}/{len(results)} 条视频生成成功")
safe_print(f"输出目录: {output_dir}")
safe_print(f"结果记录: {out_json}")
