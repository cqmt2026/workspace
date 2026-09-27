# -*- coding: utf-8 -*-
"""光伏短视频合成器 v2.0 - 实拍视频背景 + 字幕叠加"""
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

def get_video_duration(filepath):
    """获取视频时长(秒)"""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                         capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except:
        return 10.0

def get_video_resolution(filepath):
    """获取视频分辨率"""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height",
                          "-of", "csv=s=x:p=0", filepath],
                         capture_output=True, text=True, timeout=10)
        return r.stdout.strip().split("x")
    except:
        return ["1920", "1080"]

def run_ffmpeg(args, timeout=60):
    """安全执行ffmpeg"""
    r = subprocess.run(["ffmpeg", "-y"] + args, capture_output=True, timeout=timeout)
    return r.returncode == 0, r.stderr.decode("utf-8", errors="replace")[-200:]


class PVVideoComposerV2:
    """v2: 实拍视频背景 + 字幕叠加"""

    def __init__(self):
        self.materials_dir = BASE / "data" / "materials"
        self.output_dir = BASE / "data" / "output" / "douyin_videos_v2"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = 1080
        self.height = 1920
        self.font_path = "C:/Windows/Fonts/msyhbd.ttc"
        self.font_path_reg = "C:/Windows/Fonts/msyh.ttc"

    def _get_bg_video(self, direction):
        """从素材目录选一个视频"""
        if not self.materials_dir.exists():
            return None
        videos = list(self.materials_dir.glob("*.mp4"))
        # 排除0字节文件
        videos = [v for v in videos if v.stat().st_size > 100000]
        if not videos:
            return None
        return random.choice(videos)

    def _duration_for_content(self, body_text, cta_text):
        """根据文案长度估算所需时长"""
        # 中文TTS约4-5字/秒
        total_chars = len(body_text) + len(cta_text)
        duration = max(12, total_chars / 4.5)
        return min(duration, 45)  # 最多45秒

    def synthesize(self, title, body, cta, tracking_id, direction="news"):
        """合成一条视频"""
        temp_dir = tempfile.mkdtemp(prefix='pv_v2_')
        try:
            # 1. 获取背景视频
            bg_video = self._get_bg_video(direction)
            if not bg_video:
                safe_print(f"  无素材，跳过 {tracking_id}")
                return None

            bg_dur = get_video_duration(str(bg_video))
            target_dur = self._duration_for_content(body, cta)
            safe_print(f"  素材: {bg_video.name} ({bg_dur:.1f}s), 需要{target_dur:.1f}s")

            # 2. 截取/循环背景视频到目标时长
            bg_clipped = os.path.join(temp_dir, "bg_clipped.mp4")
            if bg_dur >= target_dur:
                # 从中间截取
                start = random.uniform(0, max(0, bg_dur - target_dur))
                ok, _ = run_ffmpeg([
                    "-ss", str(start), "-i", str(bg_video),
                    "-t", str(target_dur),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "96k",
                    "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                           f"crop={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2",
                    bg_clipped
                ])
            else:
                # 循环
                ok, _ = run_ffmpeg([
                    "-stream_loop", str(int(target_dur / bg_dur) + 1),
                    "-i", str(bg_video),
                    "-t", str(target_dur),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "96k",
                    "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                           f"crop={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2",
                    bg_clipped
                ])
            if not ok:
                safe_print(f"  背景截取失败")
                return None

            # 3. 生成TTS配音
            full_text = f"{title}\n{body}\n{cta}"
            audio_path = os.path.join(temp_dir, "tts.mp3")
            import edge_tts
            import asyncio
            voice = "zh-CN-YunxiNeural"
            communicate = edge_tts.Communicate(full_text, voice)
            asyncio.run(communicate.save(audio_path))

            audio_dur = get_video_duration(audio_path)
            safe_print(f"  配音: {audio_dur:.1f}s")

            # 4. 生成字幕SRT
            srt_path = os.path.join(temp_dir, "subs.srt")
            self._write_srt(srt_path, title, body, cta)

            # 5. 叠加字幕到视频
            final_path = os.path.join(temp_dir, "final.mp4")
            ok, err = run_ffmpeg([
                "-i", bg_clipped,
                "-i", audio_path,
                "-vf", f"subtitles='{srt_path}':force_style='FontName=Microsoft YaHei Bold,FontSize=36,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1'",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "96k",
                "-shortest",
                final_path
            ], timeout=120)

            if not ok:
                safe_print(f"  字幕叠加失败: {err[:100]}")
                return None

            # 6. 复制到输出目录
            out_path = self.output_dir / f"{tracking_id}.mp4"
            shutil.copy2(final_path, str(out_path))

            size_mb = os.path.getsize(str(out_path)) / 1024 / 1024
            safe_print(f"  ✅ {size_mb:.1f}MB")
            return str(out_path)

        except Exception as e:
            safe_print(f"  ❌ {e}")
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _write_srt(self, path, title, body, cta):
        """生成SRT字幕文件"""
        # 把文案拆成短句
        lines = []
        # 标题
        for i in range(0, len(title), 20):
            lines.append(title[i:i+20])
        lines.append("")
        # 正文（按→分割）
        for part in body.replace("→", "\n→").split("\n"):
            part = part.strip()
            if part:
                for i in range(0, len(part), 25):
                    lines.append(part[i:i+25])
        lines.append("")
        # CTA
        lines.append(cta[:40])

        # 去掉空行，写入SRT
        content_lines = [l for l in lines if l.strip()]
        srt_entries = []
        dur_per_line = 3.5  # 每行字幕显示时长
        for i, line in enumerate(content_lines):
            start = i * dur_per_line
            end = start + dur_per_line
            srt_entries.append(f"{i+1}\n{self._format_time(start)} --> {self._format_time(end)}\n{line}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(srt_entries))

    def _format_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:05.2f}"
        return f"{m:02d}:{s:05.2f}"


if __name__ == "__main__":
    composer = PVVideoComposerV2()

    # 测试一条
    result = composer.synthesize(
        title="28.9GW！正泰电器光伏电站规模爆表",
        body="正泰电器一口气拿下超28.9GW的光伏电站装机量，这体量在行业里绝对是顶尖水平。→截至2026年6月底，这一规模稳居国内企业前列。→作为新能源运营的领跑者，正泰正在从制造端向运营端深度转型。",
        cta="想看更多光伏行业深度解读？私信关注，每天一条行业情报。",
        tracking_id="TEST_V2_001",
        direction="news"
    )
    if result:
        safe_print(f"\n测试视频: {result}")
    else:
        safe_print("\n测试失败")
