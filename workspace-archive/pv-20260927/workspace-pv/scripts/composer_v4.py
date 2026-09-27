# -*- coding: utf-8 -*-
import sys, os, subprocess, random, tempfile, shutil
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def sp(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'): print(msg)
    except: pass

def get_dur(p):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", p],
                         capture_output=True, text=True, timeout=5)
        return float(r.stdout.strip())
    except: return 10.0

def ff(args, timeout=20):
    r = subprocess.run(["ffmpeg", "-y"] + args, capture_output=True, timeout=timeout)
    return r.returncode == 0, r.stderr.decode("utf-8", errors="replace")[-80:]

class C4:
    def __init__(self):
        self.mat = BASE / "data" / "materials"
        self.out = BASE / "data" / "output" / "douyin_videos_v4"
        self.out.mkdir(parents=True, exist_ok=True)
        self.font = "C:/Windows/Fonts/msyh.ttc"

    def pick(self, d):
        vs = [p for p in self.mat.glob("*.mp4") if p.stat().st_size > 100000]
        return random.choice(vs) if vs else None

    def synthesize(self, title, body, cta, tid, direction="news"):
        tmp = tempfile.mkdtemp(prefix='pv4_')
        try:
            bg = self.pick(direction)
            if not bg:
                sp("  无素材"); return None
            bg_name = bg.name.replace(" ", "_")
            bg_copy = os.path.join(tmp, bg_name)
            shutil.copy2(str(bg), bg_copy)

            bg_dur = get_dur(bg_copy)
            dur = min(bg_dur, 20)
            sp(f"  {bg_name[:20]} | {dur:.0f}s")

            # 截取
            clipped = os.path.join(tmp, "clipped.mp4")
            ok, _ = ff(["-i", bg_copy, "-t", str(dur), "-c", "copy", clipped])
            if not ok:
                sp("  截取失败"); return None

            # TTS
            import edge_tts, asyncio
            audio = os.path.join(tmp, "tts.mp3")
            full = f"{title}。{body}。{cta}"
            voices = ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]
            tts_ok = False
            for v in voices:
                try:
                    communicate = edge_tts.Communicate(full, v)
                    asyncio.run(communicate.save(audio))
                    if os.path.exists(audio) and os.path.getsize(audio) > 5000:
                        tts_ok = True
                        sp(f"  TTS OK ({v})")
                        break
                except: pass
            if not tts_ok:
                sp("  TTS失败"); return None

            # 方案A: 先overlay文字图片，再合音频
            # 用PIL画一张带标题的图片，叠加到视频底部
            try:
                from PIL import Image, ImageDraw, ImageFont
                # 截取一帧作为底图
                frame_path = os.path.join(tmp, "frame.jpg")
                ok, _ = ff(["-i", clipped, "-vframes", "1", "-q:v", "2", frame_path])

                if ok:
                    img = Image.open(frame_path)
                    w, h = img.size
                    draw = ImageDraw.Draw(img)
                    font = ImageFont.truetype(self.font, 40)

                    # 底部半透明条
                    draw.rectangle([0, h-80, w, h], fill=(0, 0, 0, 180))
                    # 标题文字
                    txt = title[:30]
                    bbox = draw.textbbox((0, 0), txt, font=font)
                    tw = bbox[2] - bbox[0]
                    draw.text(((w-tw)//2, h-70), txt, fill=(255, 255, 255), font=font)

                    overlay_path = os.path.join(tmp, "overlay.jpg")
                    img.save(overlay_path, quality=95)

                    # 把overlay帧叠到视频最后一秒
                    overlay_start = max(0, dur - 3)
                    final_raw = os.path.join(tmp, "final_raw.mp4")
                    ok, err = ff([
                        "-i", clipped,
                        "-ss", str(overlay_start),
                        "-i", overlay_path,
                        "-t", "3",
                        "-filter_complex", "[0:v][1:v]overlay=0:(H-h)-80[out]",
                        "-map", "[out]",
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                        "-c:a", "copy",
                        "-shortest",
                        final_raw
                    ], 30)

                    if ok:
                        # 合并前半段(无overlay) + 后半段(有overlay)
                        if overlay_start > 0:
                            part1 = os.path.join(tmp, "part1.mp4")
                            ff(["-i", clipped, "-t", str(overlay_start), "-c", "copy", part1])
                            concat_file = os.path.join(tmp, "concat.txt")
                            with open(concat_file, "w") as f:
                                f.write(f"file '{part1.replace(chr(92), chr(47))}'\n")
                                f.write(f"file '{final_raw.replace(chr(92), chr(47))}'\n")
                            final = os.path.join(tmp, "final.mp4")
                            ff(["-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", final])
                        else:
                            final = final_raw
                    else:
                        sp(f"  overlay失败, 用原始: {err[:60]}")
                        final = clipped
                else:
                    sp("  帧提取失败"); return None
            except ImportError:
                sp("  PIL不可用, 用原始"); final = clipped
            except Exception as e:
                sp(f"  overlay异常: {e}"); final = clipped

            # 合音频
            final_with_audio = os.path.join(tmp, "final_audio.mp4")
            ok, err = ff([
                "-i", final,
                "-i", audio,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "96k",
                "-shortest",
                final_with_audio
            ], 30)

            if not ok:
                sp(f"  音频合成失败: {err[:60]}"); return None

            out = self.out / f"{tid}.mp4"
            shutil.copy2(final_with_audio, str(out))
            mb = os.path.getsize(str(out)) / 1024 / 1024
            sp(f"  OK {mb:.1f}MB")
            return str(out)
        except Exception as e:
            sp(f"  异常: {e}")
            return None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    c = C4()
    r = c.synthesize(
        "28.9GW！正泰电器光伏电站规模爆表",
        "正泰电器一口气拿下超28.9GW的光伏电站装机量，这体量在行业里绝对是顶尖水平。截至2026年6月底，这一规模稳居国内企业前列。",
        "想看更多光伏行业深度解读？私信关注，每天一条行业情报。",
        "TEST_V4_001",
        "news"
    )
    if r:
        sp(f"\n成功: {r}")
        sp(f"大小: {os.path.getsize(r)/1024/1024:.1f}MB")
    else:
        sp("失败")
