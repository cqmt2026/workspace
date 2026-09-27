# -*- coding: utf-8 -*-
"""全字幕SRT + 主题匹配素材 v5"""
import sys, os, subprocess, random, tempfile, shutil, json
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
    return r.returncode == 0

# 方向→素材匹配规则
THEME_MAP = {
    "policy": ["rooftop", "solar power", "building solar"],
    "news": ["solar panels", "solar energy", "solar farm"],
    "tech": ["solar panel technology", "solar installation", "solar factory"],
    "benefit": ["solar farm", "solar energy", "green energy"],
    "avoid": ["solar installation", "rooftop solar", "solar panels"],
}

class C5:
    def __init__(self):
        self.mat = BASE / "data" / "materials"
        self.out = BASE / "data" / "output" / "douyin_videos_v5"
        self.out.mkdir(parents=True, exist_ok=True)
        self.font = "C:/Windows/Fonts/msyh.ttc"
        self.font_bold = "C:/Windows/Fonts/msyhbd.ttc"

    def pick(self, direction):
        """按方向匹配素材"""
        if not self.mat.exists():
            return None
        videos = [p for p in self.mat.glob("*.mp4") if p.stat().st_size > 100000]
        if not videos:
            return None
        # 尝试按关键词匹配文件名
        keywords = THEME_MAP.get(direction, ["solar"])
        # 优先匹配名称含关键词的
        scored = []
        for v in videos:
            name = v.stem.lower()
            score = sum(1 for kw in keywords if kw.replace(" ","_") in name or kw in name)
            scored.append((score, v))
        scored.sort(key=lambda x: -x[0])
        # 取最高分
        best = scored[0][1]
        sp(f"  match: {best.stem[:20]} (score={scored[0][0]}/{len(keywords)})")
        return best

    def _make_srt(self, lines, path, total_dur):
        """生成SRT字幕文件，每行显示3-5秒"""
        entries = []
        time_per_line = total_dur / max(len(lines), 1)
        current = 0.0
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            start = current
            end = min(start + time_per_line, total_dur)
            # 字幕格式: hh:mm:ss,mmm
            entries.append(f"{i+1}")
            entries.append(f"{self._ts(start)} --> {self._ts(end)}")
            entries.append(line)
            entries.append("")
            current = end
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(entries))

    def _ts(self, s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = s % 60
        return f"{h:02d}:{m:02d}:{sec:05.2f}".replace(".", ",")

    def synthesize(self, title, body, cta, tid, direction="news"):
        tmp = tempfile.mkdtemp(prefix='pv5_')
        try:
            bg = self.pick(direction)
            if not bg:
                sp("  无素材"); return None
            bg_name = bg.name.replace(" ", "_")
            bg_copy = os.path.join(tmp, bg_name)
            shutil.copy2(str(bg), bg_copy)

            bg_dur = get_dur(bg_copy)
            # 根据文案长度决定时长
            full_text = f"{title}。{body}。{cta}"
            need_dur = max(10, min(30, len(full_text) / 5))
            dur = min(bg_dur, need_dur)
            sp(f"  {bg_dur:.0f}s -> 截取{dur:.0f}s")

            # 截取
            clipped = os.path.join(tmp, "clipped.mp4")
            ok = ff(["-i", bg_copy, "-t", str(dur), "-c", "copy", clipped])
            if not ok:
                sp("  截取失败"); return None

            # TTS
            import edge_tts, asyncio
            audio = os.path.join(tmp, "tts.mp3")
            voices = ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]
            tts_ok = False
            for v in voices:
                try:
                    communicate = edge_tts.Communicate(full_text, v)
                    asyncio.run(communicate.save(audio))
                    if os.path.exists(audio) and os.path.getsize(audio) > 5000:
                        tts_ok = True
                        sp(f"  TTS: {v}")
                        break
                except: pass
            if not tts_ok:
                sp("  TTS失败"); return None

            # 匹配音频时长
            audio_dur = get_dur(audio)
            sp(f"  音频: {audio_dur:.0f}s")

            # 生成SRT字幕（全文逐句）
            # 把文案拆成句子
            import re
            sentences = []
            # 标题
            sentences.append(title)
            # 正文按→或。分割
            for part in body.replace("→", "\n").split("\n"):
                p = part.strip()
                if p:
                    # 长句再按句号切割
                    for sub in p.split("。"):
                        sub = sub.strip()
                        if sub:
                            sentences.append(sub + "。")
            # CTA
            sentences.append(cta)

            srt_path = os.path.join(tmp, "subs.srt")
            self._make_srt(sentences, srt_path, audio_dur)

            # 字幕叠加（用subtitles filter烧录字幕）
            srt_esc = str(srt_path).replace("\\", "/").replace(":", "\\:")
            vf = f"subtitles='{srt_esc}':force_style='FontName=Microsoft YaHei,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=40'"

            # 先叠加字幕，再合音频
            subbed = os.path.join(tmp, "subbed.mp4")
            ok = ff([
                "-i", clipped,
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-c:a", "copy",
                subbed
            ], 60)

            if not ok:
                sp("  字幕叠加失败, 尝试备用方案")
                # 备用：用drawtext只显示标题
                esc_title = title.replace("'", "''")
                vf2 = f"drawtext=text='{esc_title}':fontfile={self.font}:fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.6:boxborderw=8"
                ok = ff([
                    "-i", clipped,
                    "-vf", vf2,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                    "-c:a", "copy",
                    subbed
                ], 60)
                if not ok:
                    sp("  备用也失败"); return None

            # 合音频
            final = os.path.join(tmp, "final.mp4")
            ok = ff([
                "-i", subbed,
                "-i", audio,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "96k",
                "-shortest", final
            ], 30)

            if not ok:
                sp("  音频合成失败"); return None

            out = self.out / f"{tid}.mp4"
            shutil.copy2(final, str(out))
            mb = os.path.getsize(str(out)) / 1024 / 1024
            sp(f"  OK {mb:.1f}MB ({dur:.0f}s)")
            return str(out)
        except Exception as e:
            sp(f"  异常: {e}")
            return None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    c = C5()
    # 测试一条
    r = c.synthesize(
        "28.9GW！正泰电器光伏电站规模爆表，行业洗牌加速",
        "正泰电器一口气拿下超28.9GW的光伏电站装机量，这体量在行业里绝对是顶尖水平。截至2026年6月底，这一规模稳居国内企业前列。正泰正在从制造端向运营端深度转型，构建完整的产业链闭环。随着国家双碳目标推进，这种重资产运营模式将迎来更稳定的长期收益预期。",
        "想看更多光伏行业深度解读？私信关注，每天一条行业情报。",
        "TEST_V5_001",
        "news"
    )
    if r:
        sp(f"\n成功: {r}")
    else:
        sp("失败")