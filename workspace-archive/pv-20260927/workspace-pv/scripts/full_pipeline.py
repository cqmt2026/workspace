# -*- coding: utf-8 -*-
"""光伏短视频完整生成流水线 v1.0
Pixabay素材 + LLM文案 + Edge TTS配音 + FFmpeg合成
"""
import sys, os, json, time, re, shutil, urllib.request
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "workspace-maphot" / "scripts" / "modules"))
os.chdir(str(BASE))

def safe_print(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

# ========== 1. Pixabay素材 ==========
from pixabay_fetcher import search_videos, download_video

MATERIAL_DIR = BASE / "data" / "materials"
MATERIAL_DIR.mkdir(parents=True, exist_ok=True)

# 搜索并下载素材
QUERY_MAP = {
    "news": "solar panels factory",
    "tech": "solar installation worker",
    "policy": "rooftop solar",
    "benefit": "solar farm",
    "avoid": "solar panels",
}

all_materials = {}
for direction, query in QUERY_MAP.items():
    videos = search_videos(query, per_page=3)
    downloaded = []
    for v in videos[:2]:  # 每个方向最多2个
        path = download_video(v, MATERIAL_DIR)
        if path:
            downloaded.append(path)
    all_materials[direction] = downloaded
    safe_print(f"{direction}: {len(downloaded)} 素材")

# ========== 2. 加载A级内容 ==========
content_dir = BASE / "data" / "output" / "llm_generated"
json_file = content_dir / "llm_generated_20260820.json"
with open(json_file, "r", encoding="utf-8") as f:
    contents = json.load(f)

a_level = []
for c in contents:
    body_len = len(c.get("body",""))
    has_placeholder = any(x in c.get("hook","") + c.get("body","") + c.get("cta","") for x in ["测试", "占位符", "{title"])
    has_number_or_q = bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))
    if body_len >= 100 and not has_placeholder and has_number_or_q:
        a_level.append(c)

safe_print(f"加载 {len(a_level)} 条A级内容\n")

# ========== 3. 视频合成 ==========
from core.video_composer import PVVideoComposer
composer = PVVideoComposer()

VIDEO_DIR = BASE / "data" / "output" / "douyin_videos_v2"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

results = []
for i, c in enumerate(a_level):
    tid = c.get("tracking_id", f"PV_{i+1}")
    direction = c["direction"]
    
    # 选素材
    materials = all_materials.get(direction, all_materials["news"])
    bg_video = materials[0] if materials else None
    
    safe_print(f"[{i+1}/{len(a_level)}] {tid} ({direction})")
    safe_print(f"  素材: {os.path.basename(bg_video) if bg_video else '无'}")
    
    script_data = {
        "title": c["hook"],
        "body": c["body"],
        "cta": c["cta"],
        "full_script": f"{c['hook']}\n\n{c['body']}\n\n{c['cta']}",
        "tracking_id": tid,
        "direction": direction,
        "bg_video": bg_video,
    }
    
    output_path = VIDEO_DIR / f"{tid}.mp4"
    try:
        result = composer.synthesize_video(script_data, str(output_path))
        if result and os.path.exists(result):
            size_mb = os.path.getsize(result) / 1024 / 1024
            safe_print(f"  ✅ {size_mb:.1f}MB")
            results.append({"id": tid, "status": "ok", "path": result, "size_mb": round(size_mb, 1)})
        else:
            safe_print(f"  ❌ 合成失败")
            results.append({"id": tid, "status": "failed"})
    except Exception as e:
        safe_print(f"  ❌ {e}")
        results.append({"id": tid, "status": "error", "reason": str(e)[:50]})
    time.sleep(1)

# 保存结果
out_json = VIDEO_DIR / "generation_result_v2.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

ok_count = sum(1 for r in results if r["status"] == "ok")
safe_print(f"\n{'='*50}")
safe_print(f"完成! {ok_count}/{len(results)} 条视频生成成功")
safe_print(f"输出目录: {VIDEO_DIR}")
safe_print(f"素材目录: {MATERIAL_DIR}")
