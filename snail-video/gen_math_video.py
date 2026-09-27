"""Manim + HyperFrames 组合数学动画生成器
用法: python gen_math_video.py "题目" "解题步骤"

示例:
python gen_math_video.py "牛吃草问题" "27头牛6天吃完,23头牛9天吃完,21头牛几天吃完"
"""
import sys, os, json, subprocess, shutil, re
from pathlib import Path

WORKSPACE = Path(__file__).parent
PROJECT = WORKSPACE / "math_video"

def clean():
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    (PROJECT / "frames").mkdir(parents=True)
    (PROJECT / "media").mkdir()

def gen_manim_script(title, steps):
    """生成 Manim 公式推导脚本"""
    lines = []
    lines.append('''from manim import *

class MathScene(Scene):
    def construct(self):
''')
    # 标题
    lines.append(f'        title = Text("{title}", font_size=48, color=YELLOW)\n')
    lines.append('        title.to_edge(UP)\n')
    lines.append('        self.play(Write(title))\n')
    lines.append('        self.wait(0.5)\n')
    
    # 步骤
    y_offset = 1.0
    for i, step in enumerate(steps):
        lines.append(f'        step{i} = Text("{step}", font_size=36, color=WHITE)\n')
        lines.append(f'        step{i}.next_to(title, DOWN, buff={y_offset})\n')
        lines.append(f'        self.play(Write(step{i}))\n')
        lines.append(f'        self.wait(0.5)\n')
        y_offset += 0.5
    
    # 答案
    ans = steps[-1] if steps else "答案"
    lines.append('        self.wait(1)\n')
    lines.append(f'        result = Text("[OK] {ans}", font_size=48, color=GREEN)\n')
    lines.append(f'        result.next_to(step{len(steps)-1}, DOWN, buff=0.8)\n')
    lines.append('        self.play(Write(result))\n')
    lines.append('        self.wait(1.5)\n')
    
    lines.append('''
if __name__ == "__main__":
    config.pixel_height = 1080
    config.pixel_width = 1920
    config.frame_rate = 30
    scene = MathScene()
    scene.render()
''')
    return ''.join(lines)

def gen_hyperframes_html(title, steps, total_frames, manim_duration):
    """生成 HyperFrames 主框架 HTML"""
    # 场景段
    scenes = []
    scenes.append(f'''<div id="cover" class="clip" data-start="0" data-duration="3" data-track-index="1">
      <div class="cover-title">{title}</div>
      <div class="cover-sub">Manim 公式 + HyperFrames 场景</div>
    </div>''')
    
    scenes.append(f'''<div id="field_scene" class="clip" data-start="3" data-duration="4" data-track-index="2">
      <div class="cover-title" style="font-size:48px;">[目标] 题目</div>
      <div style="font-size: 32px; color: #aaa; text-align: center; margin-top: 40px; line-height: 1.8;">''')
    for s in steps:
        scenes.append(f'        {s}<br>')
    scenes.append('      </div></div>')
    
    # Manim 帧嵌入
    manim_start = 7
    scenes.append(f'''<div id="manim_scene" class="clip" data-start="{manim_start}" data-duration="{manim_duration}" data-track-index="3">
      <div id="manim-container" style="width:1080px;height:1920px;position:relative;"></div>
    </div>''')
    
    answer_start = manim_start + manim_duration
    scenes.append(f'''<div id="answer_scene" class="clip" data-start="{answer_start}" data-duration="5" data-track-index="4">
      <div class="section-tag">[目标] 答案</div>
      <div class="formula-card">
        <div class="answer-big">{steps[-1] if steps else "完成"} [OK]</div>
      </div>
    </div>''')
    
    total_duration = answer_start + 5
    
    html = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #0f0f1a; }}
    body {{ font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }}
    @font-face {{ font-family: 'PingFang SC'; src: local('PingFang SC'); }}
    @font-face {{ font-family: 'Microsoft YaHei'; src: local('Microsoft YaHei'); }}
    .clip {{ position: absolute; width: 1080px; height: 1920px; left: 0; top: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .cover-title {{ font-size: 72px; color: #fff; text-align: center; }}
    .cover-sub {{ font-size: 32px; color: #4ecdc4; text-align: center; margin-top: 20px; }}
    .manim-frame {{ position: absolute; width: 1080px; height: 1920px; left: 0; top: 0; }}
    .manim-frame img {{ width: 100%; height: 100%; object-fit: contain; }}
    .formula-card {{ background: rgba(0,0,0,0.6); border-radius: 20px; padding: 50px 40px; width: 800px; margin-top: 20px; }}
    .answer-big {{ font-size: 80px; color: #4ecdc4; text-align: center; }}
    .section-tag {{ display: inline-block; background: #4ecdc4; color: #0f0f1a; font-size: 24px; padding: 8px 24px; border-radius: 20px; margin-bottom: 20px; font-weight: bold; }}
  </style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{total_duration}" data-width="1080" data-height="1920">
    {chr(10).join(scenes)}
  </div>
  <script>
    const manimContainer = document.getElementById('manim-container');
    const totalFrames = {total_frames};
    const frameDuration = {manim_duration} / totalFrames;
    const frameElements = [];
    for (let i = 1; i <= totalFrames; i++) {{
      const div = document.createElement('div');
      div.className = 'manim-frame';
      div.style.opacity = '0';
      const num = String(i).padStart(3, '0');
      div.innerHTML = '<img src="frames/formula_' + num + '.png" />';
      manimContainer.appendChild(div);
      frameElements.push(div);
    }}

    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    tl.from("#cover .cover-title", {{ opacity: 0, y: -50, duration: 0.8, ease: "back.out(1.7)" }}, 0.2);
    tl.from("#cover .cover-sub", {{ opacity: 0, y: 20, duration: 0.6 }}, 0.8);
    tl.from("#field_scene", {{ opacity: 0, duration: 0.3 }}, 3.0);
    tl.from("#field_scene div", {{ opacity: 0, y: 20, duration: 0.5, stagger: 0.2 }}, 3.3);
    frameElements.forEach((frame, i) => {{
      const t = {manim_start} + i * frameDuration;
      if (i > 0) tl.to(frameElements[i-1], {{ opacity: 0, duration: 0.2 }}, t);
      tl.to(frame, {{ opacity: 1, duration: 0.3 }}, t);
    }});
    tl.from("#answer_scene .section-tag", {{ opacity: 0, y: -20, duration: 0.4 }}, {answer_start + 0.2});
    tl.from(".answer-big", {{ opacity: 0, scale: 0.5, duration: 0.8, ease: "back.out(2)" }}, {answer_start + 0.8});
    window.__timelines["main"] = tl;
  </script>
</body>
</html>'''
    return html

def main():
    if len(sys.argv) < 2:
        print("用法: python gen_math_video.py \"题目\" \"步骤1,步骤2,步骤3\"")
        sys.exit(1)
    
    title = sys.argv[1]
    steps_str = sys.argv[2] if len(sys.argv) > 2 else ""
    steps = [s.strip() for s in steps_str.split(",") if s.strip()]
    
    print("[生成数学动画]: " + title)
    print("  步骤: " + str(steps))
    
    # 1. 清理并创建项目
    clean()
    print("[OK] 项目目录创建")
    
    # 2. 生成 Manim 脚本
    manim_script = gen_manim_script(title, steps)
    (PROJECT / "math_scene.py").write_text(manim_script, encoding='utf-8')
    print("[OK] Manim 脚本生成")
    
    # 3. 渲染 Manim
    print("  渲染 Manim 公式动画...")
    result = subprocess.run(
        ["python", "-m", "manim", "-pqh", str(PROJECT / "math_scene.py"), "MathScene"],
        capture_output=True, text=True, encoding='utf-8', timeout=300
    )
    if result.returncode != 0:
        print(f"  Manim 渲染失败: {result.stderr[-500:]}")
        sys.exit(1)
    
    # 找到 Manim 输出视频
    manim_video = None
    for f in (PROJECT / "media" / "videos").rglob("*.mp4"):
        manim_video = f
        break
    
    if not manim_video:
        print("  Manim 视频未找到")
        sys.exit(1)
    
    print(f"[OK] Manim 渲染完成: {manim_video}")
    
    # 4. 提取帧
    print("  提取 Manim 帧...")
    frames_dir = PROJECT / "frames"
    subprocess.run([
        "ffmpeg", "-i", str(manim_video),
        "-vf", "fps=1,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-q:v", "2",
        str(frames_dir / "formula_%03d.png"),
        "-y"
    ], capture_output=True, timeout=60)
    
    total_frames = len(list(frames_dir.glob("*.png")))
    print(f"[OK] 提取 {total_frames} 帧")
    
    # 5. 获取 Manim 视频时长
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(manim_video)],
        capture_output=True, text=True, timeout=10
    )
    manim_duration = round(float(probe.stdout.strip()), 1)
    
    # 6. 生成 HyperFrames HTML
    html = gen_hyperframes_html(title, steps, total_frames, manim_duration)
    (PROJECT / "index.html").write_text(html, encoding='utf-8')
    print("[OK] HyperFrames HTML 生成")
    
    # 7. 渲染 HyperFrames
    print("  渲染 HyperFrames 组合视频...")
    result = subprocess.run(
        ["hyperframes", "render", "-o", str(WORKSPACE / f"{title}_final.mp4")],
        cwd=str(PROJECT), capture_output=True, text=True, timeout=300
    )
    
    output = WORKSPACE / f"{title}_final.mp4"
    if output.exists():
        size = output.stat().st_size / 1024 / 1024
        print(f"\n🎉 视频生成完成!")
        print(f"  路径: {output}")
        print(f"  大小: {size:.2f} MB")
    else:
        print(f"  HyperFrames 渲染失败: {result.stderr[-500:]}")
        sys.exit(1)

if __name__ == "__main__":
    main()