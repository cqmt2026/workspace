# -*- coding: utf-8 -*-
"""批量生成V5短视频 - 主题匹配 + 全字幕"""
import sys, os, json, time, re
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def sp(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'): print(msg)
    except: pass

from composer_v5 import C5
c5 = C5()

# 加载A级内容
json_file = BASE / "data" / "output" / "llm_generated" / "llm_generated_20260820.json"
with open(json_file, "r", encoding="utf-8") as f:
    contents = json.load(f)

a_level = []
for c in contents:
    body_len = len(c.get("body",""))
    has_placeholder = any(x in c.get("hook","") + c.get("body","") + c.get("cta","") for x in ["测试", "占位符", "{title"])
    has_number_or_q = bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))
    if body_len >= 100 and not has_placeholder and has_number_or_q:
        a_level.append(c)

sp(f"加载 {len(a_level)} 条A级内容\n")

results = []
for i, c in enumerate(a_level):
    tid = c.get("tracking_id", f"PV_{i+1}")
    sp(f"[{i+1}/{len(a_level)}] {tid} ({c['direction']})")

    result = c5.synthesize(
        title=c["hook"],
        body=c["body"],
        cta=c["cta"],
        tid=tid,
        direction=c["direction"]
    )
    if result:
        results.append({"id": tid, "status": "ok", "path": result})
    else:
        results.append({"id": tid, "status": "failed"})
    time.sleep(1)

out_json = c5.out / "generation_result_v5.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

ok = sum(1 for r in results if r["status"] == "ok")
sp(f"\n完成! {ok}/{len(results)} 条")
sp(f"输出: {c5.out}")