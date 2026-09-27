# -*- coding: utf-8 -*-
"""V6视频合成 - 修复截断问题
1. 用ffmpeg输出获取时长(替代ffprobe)
2. 循环素材到足够长度
3. 按文案时长动态生成字幕
"""
import sys, os, json, time, re, shutil, subprocess, tempfile
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

def get_dur_v2(path):
    """用ffmpeg输出获取时长(更可靠)"""
    r = subprocess.run(["ffmpeg", "-i", str(path)], capture_output=True, text=True, timeout=10)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            # 格式: Duration: 00:00:23.60, start: ...
            parts = line.split(",")[0].strip().split("Duration: ")[1]
            h, m, s = parts.split(":")
            return int(h)*3600 + int(m)*60 + float(s)
    return 10.0

def ff(args, timeout=30):
    r = subprocess.run(["ffmpeg", "-y"] + args, capture_output=True, timeout=timeout)
    return r.returncode == 0

# 素材
videos = [p for p in MAT.glob("*.mp4") if p.stat().st_size > 100000]
sp(f"素材: {[v.name for v in videos]}")

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

def make_srt_v2(lines, path, total_dur):
    """生成SRT，每句显示4秒"""
    entries = []
    t = 0.0
    idx = 0
    for line in lines:
        line = line.strip()
        if not line: continue
        idx += 1
        s, e = t, t + 4.0
        def ts(x):
            m = int(x // 60); sec = x % 60
            return f"{int(m//60):02d}:{int(m%60):02d}:{sec:05.2f}".replace(".", ",")
        entries.append(f"{idx}\n{ts(s)} --> {ts(e)}\n{line}\n")
        t = e
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

# 加载内容
jf = BASE / "data" / "output" / "llm_generated" / "llm_generated_20260820.json"
with open(jf, "r", encoding="utf-8") as f:
    contents = json.load(f)
a_level = [c for c in contents
    if len(c.get("body","")) >= 100
    and not any(x in c.get("hook","")+c.get("body","")+c.get("cta","") for x in ["测试","占位符","{title"])
    and (bool(re.search(r'\d+', c["hook"])) or bool(re.search(r'[？?！!]', c["hook"]))) ]

sp(f"加载 {len(a_level)} 条A级内容\n")

results = []
for i, c in enumerate(a_level):
    tid = c.get("tracking_id", f"PV_{i+1}")
    sp(f"[{i+1}/{len(a_level)}] {tid} ({c['direction']})")
    
    tmp = tempfile.mkdtemp(prefix='pv6_')
    try:
        bg = pick(c["direction"])
        bg_copy = os.path.join(tmp, bg.name)
        shutil.copy2(str(bg), bg_copy)
        
        bg_dur = get_dur_v2(bg_copy)
        full = f"{c['hook']}。{c['body']}。{c['cta']}"
        chars = len(full)
        # 目标时长：按字数估算，最少取素材长度
        need_dur = max(bg_dur, min(45, chars / 5))
        sp(f"  {bg.name[:20]} | 素材{bg_dur:.0f}s | 文案{chars}字→需{need_dur:.0f}s")
        
        # 循环素材到目标时长
        loop_n = max(1, int(need_dur / bg_dur) + 1)
        clipped = os.path.join(tmp, "clipped.mp4")
        ok = ff(["-stream_loop", str(loop_n), "-i", bg_copy, "-t", str(need_dur),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-c:a", "aac", "-b:a", "96k", clipped], 120)
        if not ok:
            sp("  循环截取失败"); continue
        
        # TTS
        audio = os.path.join(tmp, "tts.mp3")
        tts_ok = False
        for voice in ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]:
            try:
                communicate = edge_tts.Communicate(full, voice)
                asyncio.run(communicate.save(audio))
                if os.path.exists(audio) and os.path.getsize(audio) > 5000:
                    tts_ok = True; sp(f"  TTS OK"); break
            except: pass
        if not tts_ok: sp("  TTS失败"); continue
        
        audio_dur = get_dur_v2(audio)
        sp(f"  音频: {audio_dur:.0f}s")
        
        # 生成SRT字幕
        sentences = [c["hook"]]
        for part in c["body"].replace("→", "\n").split("\n"):
            p = part.strip()
            if p:
                for sub in p.split("。"):
                    s = sub.strip()
                    if s: sentences.append(s + "。")
        sentences.append(c["cta"])
        
        srt_path = os.path.join(tmp, "subs.srt")
        make_srt_v2(sentences, srt_path, audio_dur)
        sp(f"  SRT: {len(sentences)}句")
        
        # 烧录字幕
        srt_esc = srt_path.replace("\\", "/").replace(":", "\\:")
        subbed = os.path.join(tmp, "subbed.mp4")
        vf = f"subtitles='{srt_esc}':force_style='FontName=Microsoft YaHei Bold,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=30'"
        ok = ff(["-i", clipped, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-c:a", "copy", subbed], 120)
        if not ok:
            sp("  字幕烧录失败"); continue
        
        # 合音频
        final = os.path.join(tmp, "final.mp4")
        ok = ff(["-i", subbed, "-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", final], 30)
        if not ok: sp("  音频合成失败"); continue
        
        out = OUT / f"{tid}.mp4"
        shutil.copy2(final, str(out))
        mb = os.path.getsize(str(out)) / 1024 / 1024
        actual_dur = get_dur_v2(str(out))
        sp(f"  OK {mb:.1f}MB ({actual_dur:.0f}s)")
        results.append({"id": tid, "status": "ok", "path": str(out), "dur": actual_dur})
    except Exception as e:
        sp(f"  异常: {e}")
        results.append({"id": tid, "status": "failed", "reason": str(e)[:50]})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    time.sleep(0.5)

out_json = OUT / "generation_result_v6.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

ok = sum(1 for r in results if r["status"] == "ok")
sp(f"\n{'='*50}")
sp(f"完成! {ok}/{len(results)} 条")
sp(f"输出: {OUT}")