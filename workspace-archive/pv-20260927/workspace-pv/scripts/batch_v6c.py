# -*- coding: utf-8 -*-
"""V6最终补全 - drawtext标题，无SRT烧录(快)"""
import sys, os, json, re, shutil, subprocess, tempfile, time
from pathlib import Path
import edge_tts, asyncio

BASE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-pv")
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def sp(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'): print(msg)
    except: pass

FONT = "C:/Windows/Fonts/msyhbd.ttc"
MAT = BASE / "data" / "materials"
OUT = BASE / "data" / "output" / "douyin_videos_v6"
OUT.mkdir(parents=True, exist_ok=True)

def get_dur(path):
    r = subprocess.run(["ffmpeg", "-i", str(path)], capture_output=True, text=True, timeout=10)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split(",")[0].strip().split("Duration: ")[1]
            h, m, s = parts.split(":")
            return int(h)*3600 + int(m)*60 + float(s)
    return 10.0

def ff(args, timeout=20):
    r = subprocess.run(["ffmpeg", "-y"] + args, capture_output=True, timeout=timeout)
    return r.returncode == 0

videos = [p for p in MAT.glob("*.mp4") if p.stat().st_size > 100000]

THEME_MAP = {"policy": ["solar_power"], "news": ["solar_energy", "solar_panels"], "tech": ["solar_panels", "solar_eclipse"], "benefit": ["solar_farm"], "avoid": ["solar_panels"]}

def pick(d):
    kws = THEME_MAP.get(d, ["solar"])
    scored = [(sum(1 for kw in kws if kw in v.stem.lower()), v) for v in videos]
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]

# 已完成
done_ids = set(f.stem for f in OUT.glob("*.mp4") if "TEST" not in f.name)

jf = BASE / "data" / "output" / "llm_generated" / "llm_generated_20260820.json"
with open(jf, "r", encoding="utf-8") as f:
    contents = json.load(f)
a_level = [c for c in contents
    if len(c.get("body","")) >= 100
    and not any(x in c.get("hook","")+c.get("body","")+c.get("cta","") for x in ["测试","占位符","{title"])
    and (bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))) ]

pending = [c for c in a_level if c.get("tracking_id","") not in done_ids]
sp(f"待生成: {len(pending)}")

results = []
for i, c in enumerate(pending):
    tid = c.get("tracking_id", f"PV_{i}")
    sp(f"[{i+1}/{len(pending)}] {tid}")
    tmp = tempfile.mkdtemp(prefix='pv6c_')
    try:
        bg = pick(c["direction"])
        bg_copy = os.path.join(tmp, bg.name)
        shutil.copy2(str(bg), bg_copy)
        bg_dur = get_dur(bg_copy)
        
        # 短文案
        short_body = c["body"].split("→")[0][:50] if "→" in c["body"] else c["body"][:50]
        short_full = f"{c['hook']}。{short_body}。{c['cta']}"
        sp(f"  {bg.name[:15]} | {bg_dur:.0f}s")
        
        # 截取
        clipped = os.path.join(tmp, "clipped.mp4")
        ok = ff(["-i", bg_copy, "-t", str(bg_dur), "-c", "copy", clipped])
        if not ok: sp("  截取失败"); continue
        
        # TTS
        audio = os.path.join(tmp, "tts.mp3")
        tts_ok = False
        for voice in ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]:
            try:
                communicate = edge_tts.Communicate(short_full, voice)
                asyncio.run(communicate.save(audio))
                if os.path.exists(audio) and os.path.getsize(audio) > 2000:
                    tts_ok = True; sp(f"  TTS OK"); break
            except: pass
        if not tts_ok: sp("  TTS失败"); continue
        
        # drawtext标题(快)
        esc_title = c["hook"].replace("'", "''")
        vf = f"drawtext=text='{esc_title}':fontfile={FONT}:fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.6:boxborderw=8"
        subbed = os.path.join(tmp, "subbed.mp4")
        ok = ff(["-i", clipped, "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-c:a", "copy", subbed], 30)
        if not ok: sp("  drawtext失败"); continue
        
        # 合音频
        final = os.path.join(tmp, "final.mp4")
        ok = ff(["-i", subbed, "-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", final], 30)
        if not ok: sp("  合成失败"); continue
        
        out = OUT / f"{tid}.mp4"
        shutil.copy2(final, str(out))
        mb = os.path.getsize(str(out)) / 1024 / 1024
        dur = get_dur(str(out))
        sp(f"  OK {mb:.1f}MB ({dur:.0f}s)")
        results.append({"id": tid, "status": "ok"})
    except Exception as e:
        sp(f"  异常: {e}")
        results.append({"id": tid, "status": "failed"})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    time.sleep(0.2)

sp(f"\n完成! 本批{len(results)}条")