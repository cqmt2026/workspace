# -*- coding: utf-8 -*-
"""光伏短视频合成器 v3 - 简化版，避免路径和性能问题"""
import sys, os, subprocess, random, tempfile, shutil
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def safe_print(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

def get_dur(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", path],
                         capture_output=True, text=True, timeout=5)
        return float(r.stdout.strip())
    except: return 10.0

def ff(args, timeout=30):
    r = subprocess.run(["ffmpeg", "-y"] + args, capture_output=True, timeout=timeout)
    return r.returncode == 0

class ComposerV3:
    def __init__(self):
        self.mat_dir = BASE / "data" / "materials"
        self.out_dir = BASE / "data" / "output" / "douyin_videos_v3"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # 16:9横版素材 → 1280x720
        self.w, self.h = 1280, 720

    def _video_path(self, d):
        videos = [p for p in self.mat_dir.glob("*.mp4") if p.stat().st_size > 100000]
        if not videos: return None
        return random.choice(videos)

    def synthesize(self, title, body, cta, tid, direction="news"):
        tmp = tempfile.mkdtemp(prefix='pv3_')
        try:
            bg = self._video_path(direction)
            if not bg:
                safe_print(f"  无素材"); return None

            bg_name = bg.name.replace(" ", "_")
            bg_copy = os.path.join(tmp, bg_name)
            shutil.copy2(str(bg), bg_copy)

            bg_dur = get_dur(bg_copy)
            target = max(15, min(30, len(body) / 5))
            safe_print(f"  素材:{bg_name[:20]} ({bg_dur:.0f}s) 需要{target:.0f}s")

            # 截取/循环
            clipped = os.path.join(tmp, "clipped.mp4")
            if bg_dur >= target:
                ok = ff(["-ss", "0", "-i", bg_copy, "-t", str(target),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                        "-c:a", "aac", "-b:a", "96k", clipped], 60)
            else:
                loop_n = max(1, int(target / bg_dur) + 1)
                ok = ff(["-stream_loop", str(loop_n), "-i", bg_copy,
                        "-t", str(target),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                        "-c:a", "aac", "-b:a", "96k", clipped], 60)
            if not ok:
                safe_print(f"  截取失败"); return None

            # TTS
            import edge_tts, asyncio
            audio = os.path.join(tmp, "tts.mp3")
            full = f"{title}\n{body}\n{cta}"
            try:
                communicate = edge_tts.Communicate(full, "zh-CN-YunxiNeural")
                asyncio.run(communicate.save(audio))
            except:
                safe_print(f"  TTS失败"); return None

            # drawtext字幕
            final = os.path.join(tmp, "final.mp4")
            # 底部居中字幕
            font = "C:/Windows/Fonts/msyh.ttc"
            vf = f"drawtext=text='{title.replace(chr(39), chr(39)+chr(39))}':fontfile={font}:fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h-120:box=1:boxcolor=black@0.5:boxborderw=5"

            ok = ff([
                "-i", clipped, "-i", audio,
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-c:a", "aac", "-b:a", "96k",
                "-shortest", final
            ], 120)

            if not ok:
                safe_print(f"  合成失败"); return None

            out = self.out_dir / f"{tid}.mp4"
            shutil.copy2(final, str(out))
            mb = os.path.getsize(str(out)) / 1024 / 1024
            safe_print(f"  OK {mb:.1f}MB")
            return str(out)
        except Exception as e:
            safe_print(f"  异常: {e}")
            return None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    c = ComposerV3()
    r = c.synthesize(
        "28.9GW！正泰电器光伏电站规模爆表",
        "正泰电器一口气拿下超28.9GW的光伏电站装机量，这体量在行业里绝对是顶尖水平。截至2026年6月底，这一规模稳居国内企业前列，显示出强大的项目储备和开发能力。作为新能源运营的领跑者，正泰正在从制造端向运营端深度转型，构建起完整的产业链闭环。",
        "想看更多光伏行业深度解读？私信关注，每天一条行业情报。",
        "TEST_V3_001",
        "news"
    )
    if r:
        safe_print(f"\n视频: {r}")
    else:
        safe_print("\n失败")
