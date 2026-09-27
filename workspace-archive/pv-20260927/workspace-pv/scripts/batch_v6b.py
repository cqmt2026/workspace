# -*- coding: utf-8 -*-
"""V6补全 - 用短文案适配10-20秒素材"""
import sys, os, json, re, shutil, subprocess, tempfile
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

def ff(args, timeout=30):
    r = subprocess.run(["ffmpeg", "-y"] + args, capture_output=True, timeout=timeout)
    return r.returncode == 0

videos = [p for p in MAT.glob("*.mp4") if p.stat().st_size > 100000]

THEME_MAP = {
    "policy": ["solar_power", "rooftop"],
    "news": ["solar_energy", "solar_panels"],
    "tech": ["solar_panels", "solar_eclipse"],
    "benefit": ["solar_farm", "solar_power"],
    "avoid": ["solar_panels", "solar_energy"],
}

def pick(d):
    kws = THEME_MAP.get(d, ["solar"])
    scored = [(sum(1 for kw in kws if kw in v.stem.lower()), v) for v in videos]
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]

def make_srt(lines, path, dur):
    entries = []
    per = dur / max(len([l for l in lines if l.strip()]), 1)
    t = 0.0
    idx = 0
    for line in lines:
        line = line.strip()
        if not line: continue
        idx += 1
        s, e = t, min(t + per, dur)
        def ts(x):
            m = int(x // 60); sec = x % 60
            return f"{int(m//60):02d}:{int(m%60):02d}:{sec:05.2f}".replace(".", ",")
        entries.append(f"{idx}\n{ts(s)} --> {ts(e)}\n{line}\n")
        t = e
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

# 加载已生成的内容，跳过已完成的
jf = BASE / "data" / "output" / "llm_generated" / "llm_generated_20260820.json"
with open(jf, "r", encoding="utf-8") as f:
    contents = json.load(f)
a_level = [c for c in contents
    if len(c.get("body","")) >= 100
    and not any(x in c.get("hook","")+c.get("body","")+c.get("cta","") for x in ["测试","占位符","{title"])
    and (bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))) ]

# 检查哪些已完成
done_ids = set()
for f in OUT.glob("*.mp4"):
    if "TEST" not in f.name:
        done_ids.add(f.stem)

pending = [c for c in a_level if c.get("tracking_id","") not in done_ids]
sp(f"已完成: {len(a_level)-len(pending)}/{len(a_level)} | 待生成: {len(pending)}")

results = []
for i, c in enumerate(pending):
    tid = c.get("tracking_id", f"PV_pending_{i}")
    sp(f"[{i+1}/{len(pending)}] {tid} ({c['direction']})")
    
    tmp = tempfile.mkdtemp(prefix='pv6b_')
    try:
        bg = pick(c["direction"])
        bg_copy = os.path.join(tmp, bg.name)
        shutil.copy2(str(bg), bg_copy)
        
        bg_dur = get_dur(bg_copy)
        
        # 短文案：只取钩子+1句正文+CTA，控制在20秒内
        short_body = c["body"].split("→")[0][:60] if "→" in c["body"] else c["body"][:60]
        short_full = f"{c['hook']}。{short_body}。{c['cta']}"
        
        sp(f"  素材{bg.name[:20]} | {bg_dur:.0f}s | 短文案{len(short_full)}字")
        
        # 截取素材（不循环）
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
        
        audio_dur = get_dur(audio)
        
        # SRT
        sentences = [c["hook"], short_body, c["cta"]]
        srt_path = os.path.join(tmp, "subs.srt")
        make_srt(sentences, srt_path, audio_dur)
        
        # 烧字幕
        srt_esc = srt_path.replace("\\", "/").replace(":", "\\:")
        subbed = os.path.join(tmp, "subbed.mp4")
        vf = f"subtitles='{srt_esc}':force_style='FontName=Microsoft YaHei Bold,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=30'"
        ok = ff(["-i", clipped, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-c:a", "copy", subbed], 60)
        if not ok: sp("  字幕失败"); continue
        
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
    time.sleep(0.3)

out_json = OUT / "generation_result_v6.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

sp(f"\n完成! 本批{len(results)}条")