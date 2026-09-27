# -*- coding: utf-8 -*-
"""PV HyperFrames Template v4.0 - No audio in HTML, merge later with FFmpeg"""
import json, os, sys, subprocess
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, SCRIPT_DIR)


def load_script(script_path):
    if script_path and os.path.exists(script_path):
        with open(script_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    from core.database import PVDatabase
    db = PVDatabase()
    rows = db.get_all_items(status='published', limit=1)
    if rows:
        row = rows[0]
        title = row.get('title', '') or row.get('tracking_id', '光伏内容')
        body = row.get('body', '') or row.get('content', '') or ''
        cta = row.get('cta', '关注获取更多')
        full_script = row.get('full_script', body)
        direction = row.get('direction', 'benefit')
        direction_name = row.get('direction_name', '收益')
        target_audience = row.get('target_audience', '有屋顶的家庭')
        province = row.get('geo_primary_province', '全国')
        tracking_id = row.get('tracking_id', 'PV_' + datetime.now().strftime("%Y%m%d_%H%M"))
        if not body:
            body = title
            if full_script and len(full_script) > len(title):
                body = full_script[len(title):].strip() or title
        return {"title": title, "body": body, "cta": cta, "full_script": full_script,
                "tracking_id": tracking_id, "direction": direction, "direction_name": direction_name,
                "target_audience": target_audience, "geo_primary_province": province}
    return None


def generate_tts_audio(script_text, output_path):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(script_text, "zh-CN-YunxiNeural")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_path = output_path.replace('.mp3', '_temp.mp3')
        asyncio_run(communicate.save(temp_path))
        r = subprocess.run(['ffmpeg', '-y', '-i', temp_path, '-codec:a', 'libmp3lame', '-q:a', '2', output_path],
                          capture_output=True, text=True, encoding='utf-8', errors='replace')
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"TTS error: {e}")
        return None


def asyncio_run(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def generate_html(data):
    title = data.get("title", "光伏内容").replace('?', '？').replace('！', '！')
    body = data.get("body", "")
    cta = data.get("cta", "关注获取更多")
    full_script = data.get("full_script", body)
    direction = data.get("direction", "benefit")
    direction_name = data.get("direction_name", "收益")
    target_audience = data.get("target_audience", "有屋顶的家庭")
    province = data.get("geo_primary_province", "全国")
    tracking_id = data.get("tracking_id", "PV_" + datetime.now().strftime("%Y%m%d_%H%M"))

    word_count = len(full_script)
    duration = max(25, min(45, int(word_count / 5)))

    bg_map = {"benefit": "bg_green energy_0.jpg", "policy": "bg_roof solar_0.jpg",
              "news": "bg_photovoltaic_0.jpg", "tech": "bg_solar panels_0.jpg", "avoid": "bg_roof solar_0.jpg"}
    bg_img = bg_map.get(direction, "bg_green energy_0.jpg")
    bg_src = f"data:assets/{bg_img}"

    brand_name = "九箭新能源"
    brand_slogan = "专业光伏获客方案"
    pc = "#FF6B00"
    sc = "#1E3A5F"
    body_preview = body[:100] + ("..." if len(body) > 100 else "")

    W, H = 1920, 1080

    # Subtitles
    sentences = []
    current = ""
    for ch in full_script:
        current += ch
        if ch in '。！？':
            if current.strip():
                sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    sentence_duration = duration / max(len(sentences), 1)
    subtitle_timing = []
    t = 0
    for i, s in enumerate(sentences):
        subtitle_timing.append((round(t, 1), round(t + sentence_duration, 1), s))
        t += sentence_duration

    subtitle_html = ""
    for i, (start, end, text) in enumerate(subtitle_timing):
        subtitle_html += f'''  <div class="subtitle" id="sub-{i}" style="display:none; bottom: 12%; left: 100px; right: 100px; text-align: center;">
    <div class="sub-bg"></div>
    <div class="sub-text">{text}</div>
  </div>
'''

    points_map = {"benefit": ["政策补贴持续，部分地区最高补贴", "自发自用，余电上网，多重收益叠加", "无需贷款，零首付安装，省心省力"],
                  "policy": ["国家补贴到位，地方配套跟进", "补贴政策稳定，长期受益", "安装门槛低，申请流程简单"],
                  "news": ["光伏行业最新动态解读", "最新政策对普通家庭的影响", "未来发展趋势分析"],
                  "tech": ["高效组件技术普及", "储能系统搭配方案", "智能化监控管理"],
                  "avoid": ["警惕低价陷阱，选择正规品牌", "安装位置影响发电效率", "合同条款需谨慎审查"]}
    points = points_map.get(direction, points_map["benefit"])

    html_parts = []
    html_parts.append(f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<title>PV Content</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ width: {W}px; height: {H}px; overflow: hidden; background: #0a0f1a; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }}
  #root {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; }}
  .bg-layer {{ position: absolute; inset: 0; background-size: cover; background-position: center; filter: brightness(0.3) saturate(0.8); z-index: 0; }}
  .bg-gradient {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(10,15,26,0.9) 0%, rgba(10,15,26,0.6) 30%, rgba(10,15,26,0.8) 70%, rgba(10,15,26,0.95) 100%); z-index: 1; }}
  .glow {{ position: absolute; border-radius: 50%; filter: blur(80px); pointer-events: none; }}
  .glow-1 {{ background: {pc}; width: 400px; height: 400px; top: -100px; right: -100px; opacity: 0.15; }}
  .glow-2 {{ background: {sc}; width: 300px; height: 300px; bottom: -50px; left: -50px; opacity: 0.2; }}
  .scene {{ position: absolute; top: 0; left: 0; width: {W}px; height: {H}px; overflow: hidden; }}
  #scene1 {{ z-index: 1; }} #scene2 {{ z-index: 2; opacity: 0; }}
  #scene3 {{ z-index: 3; opacity: 0; }} #scene4 {{ z-index: 4; opacity: 0; }}
  #scene5 {{ z-index: 5; opacity: 0; }}
  #s1-brand {{ position: absolute; top: 10%; left: 0; right: 0; text-align: center; font-size: 32px; color: rgba(255,255,255,0.5); letter-spacing: 8px; }}
  #s1-title {{ position: absolute; top: 20%; left: 100px; right: 100px; font-size: 80px; font-weight: 700; color: #fff; line-height: 1.2; }}
  #s1-subtitle {{ position: absolute; top: 38%; left: 100px; right: 100px; font-size: 36px; font-weight: 300; color: {pc}; line-height: 1.5; }}
  #s1-tag {{ position: absolute; top: 52%; left: 50%; transform: translateX(-50%); display: inline-block; background: rgba({pc},0.2); border: 1px solid {pc}; border-radius: 20px; padding: 8px 24px; font-size: 24px; color: {pc}; }}
  #s1-divider {{ position: absolute; top: 60%; left: 15%; right: 15%; height: 2px; background: linear-gradient(90deg, transparent, {pc}44, transparent); }}
  #s1-province {{ position: absolute; top: 64%; left: 0; right: 0; text-align: center; font-size: 24px; color: rgba(255,255,255,0.4); }}
  #s2-card {{ position: absolute; top: 12%; left: 80px; right: 80px; background: rgba(15,20,35,0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 40px 36px; }}
  #s2-label {{ font-size: 20px; color: {pc}; margin-bottom: 16px; font-weight: 500; letter-spacing: 2px; }}
  #s2-body {{ font-size: 32px; color: rgba(255,255,255,0.9); line-height: 1.8; }}
  #s2-highlight {{ position: absolute; top: 62%; left: 80px; right: 80px; display: flex; gap: 30px; }}
  .h-item {{ flex: 1; background: rgba(255,107,0,0.08); border: 1px solid rgba(255,107,0,0.2); border-radius: 16px; padding: 20px 16px; text-align: center; }}
  .h-num {{ font-size: 56px; font-weight: 700; color: {pc}; }}
  .h-label {{ font-size: 18px; color: rgba(255,255,255,0.6); margin-top: 4px; }}
  #s3-list {{ position: absolute; top: 15%; left: 100px; right: 100px; }}
  .point {{ display: flex; align-items: flex-start; gap: 24px; margin-bottom: 32px; }}
  .point-num {{ width: 56px; height: 56px; background: {pc}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 700; color: #fff; flex-shrink: 0; }}
  .point-text {{ font-size: 28px; color: rgba(255,255,255,0.9); line-height: 1.6; padding-top: 10px; }}
  #s4-cta-box {{ position: absolute; top: 25%; left: 120px; right: 120px; background: rgba(255,107,0,0.12); border: 2px solid {pc}; border-radius: 24px; padding: 40px; text-align: center; }}
  #s4-cta-title {{ font-size: 52px; font-weight: 700; color: #fff; margin-bottom: 16px; }}
  #s4-cta-text {{ font-size: 28px; color: rgba(255,255,255,0.7); line-height: 1.6; }}
  #s4-cta-btn {{ position: absolute; top: 60%; left: 50%; transform: translateX(-50%); background: {pc}; border-radius: 30px; padding: 20px 60px; font-size: 32px; font-weight: 600; color: #fff; }}
  #s4-brand {{ position: absolute; bottom: 8%; left: 0; right: 0; text-align: center; font-size: 22px; color: rgba(255,255,255,0.3); }}
  #s5-logo {{ position: absolute; top: 30%; left: 0; right: 0; text-align: center; }}
  #s5-logo-text {{ font-size: 100px; font-weight: 700; color: {pc}; letter-spacing: 8px; }}
  #s5-slogan {{ font-size: 28px; color: rgba(255,255,255,0.5); margin-top: 12px; letter-spacing: 4px; }}
  #s5-follow {{ position: absolute; top: 60%; left: 0; right: 0; text-align: center; font-size: 36px; color: #fff; }}
  #s5-sub {{ position: absolute; top: 70%; left: 0; right: 0; text-align: center; font-size: 24px; color: rgba(255,255,255,0.4); }}
  .subtitle {{ position: absolute; z-index: 10; }}
  .sub-bg {{ position: absolute; bottom: 0; left: 0; right: 0; height: 60px; background: rgba(0,0,0,0.7); border-radius: 8px; }}
  .sub-text {{ position: relative; z-index: 1; font-size: 28px; color: #fff; padding: 10px 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="{W}" data-height="{H}" data-duration="{duration}">
  <div class="bg-layer" style="background-image: url('{bg_src}');"></div>
  <div class="bg-gradient"></div>
  <div class="glow glow-1"></div>
  <div class="glow glow-2"></div>
''')

    # Scenes (same as before)
    html_parts.append(f'''
  <div id="scene1" class="scene">
    <div id="s1-brand">BRAND</div>
    <h1 id="s1-title">TITLE</h1>
    <p id="s1-subtitle">面向AUDIENCE</p>
    <div id="s1-tag">#DIRECTION</div>
    <div id="s1-divider"></div>
    <p id="s1-province">PROVINCE</p>
  </div>
  <div id="scene2" class="scene">
    <div id="s2-card">
      <div id="s2-label">核心分析</div>
      <div id="s2-body">BODY</div>
    </div>
    <div id="s2-highlight">
      <div class="h-item"><div class="h-num">25</div><div class="h-label">年寿命</div></div>
      <div class="h-item"><div class="h-num">3-4</div><div class="h-label">年回本</div></div>
      <div class="h-item"><div class="h-num">8万+</div><div class="h-label">总收益</div></div>
    </div>
  </div>
''')

    html_parts.append('  <div id="scene3" class="scene">\n    <div id="s3-list">\n')
    for i, pt in enumerate(points):
        html_parts.append(f'      <div class="point" id="p{i}"><div class="point-num">{i+1}</div><div class="point-text">{pt}</div></div>\n')
    html_parts.append('    </div>\n  </div>\n')

    cta_display = cta if cta else "关注获取更多"
    html_parts.append(f'''
  <div id="scene4" class="scene">
    <div id="s4-cta-box">
      <div id="s4-cta-title">现在咨询，免费评估</div>
      <div id="s4-cta-text">{"→ " + cta_display}</div>
    </div>
    <div id="s4-cta-btn">立即私信</div>
    <div id="s4-brand">BRAND</div>
  </div>
''')

    html_parts.append(f'''
  <div id="scene5" class="scene">
    <div id="s5-logo">
      <div id="s5-logo-text">BRAND</div>
      <div id="s5-slogan">SLOGAN</div>
    </div>
    <div id="s5-follow">关注我 获取更多光伏资讯</div>
    <div id="s5-sub">PROVINCE地区专业安装 25年质保</div>
  </div>
''')

    html_parts.append(subtitle_html)
    html_parts.append("</div>\n")

    # JS (no audio timeline)
    js_lines = [
        '<script>',
        'window.__timelines = window.__timelines || {};',
        'var tl = gsap.timeline({ paused: true });',
        'var T = 0;',
        f'tl.to(".glow-1", {{ scale: 1.3, opacity: 0.25, duration: 4, ease: "sine.inOut", yoyo: true, repeat: Math.floor({duration} / 4) - 1 }}, 0);',
        f'tl.to(".glow-2", {{ scale: 1.2, opacity: 0.3, duration: 5, ease: "sine.inOut", yoyo: true, repeat: Math.floor({duration} / 5) - 1 }}, 0);',
        'T = 0;',
        f'tl.from("#s1-brand", {{ y: -20, opacity: 0, duration: 0.8, ease: "power2.out" }}, T);',
        f'tl.from("#s1-title", {{ y: 60, opacity: 0, scale: 0.9, duration: 1.2, ease: "power3.out" }}, T + 0.3);',
        f'tl.from("#s1-subtitle", {{ y: 30, opacity: 0, duration: 0.8, ease: "power2.out" }}, T + 1.2);',
        f'tl.from("#s1-tag", {{ scale: 0, opacity: 0, duration: 0.6, ease: "back.out(2)" }}, T + 2.0);',
        f'tl.to("#s1-divider", {{ scaleX: 1, opacity: 1, duration: 0.8, ease: "power2.inOut" }}, T + 2.6);',
        f'tl.from("#s1-province", {{ y: 20, opacity: 0, duration: 0.5, ease: "power2.out" }}, T + 3.2);',
        'T = 5;',
        f'tl.to("#scene1", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, T);',
        f'tl.fromTo("#scene2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, T);',
        f'tl.from("#s2-card", {{ y: 80, opacity: 0, duration: 0.8, ease: "power3.out" }}, T + 0.3);',
        f'tl.from("#s2-label", {{ x: -20, opacity: 0, duration: 0.5, ease: "power2.out" }}, T + 0.8);',
        f'tl.fromTo("#s2-body", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, T + 1.0);',
        f'tl.from(".h-item", {{ y: 30, opacity: 0, stagger: 0.1, duration: 0.5, ease: "back.out(1.5)" }}, T + 1.5);',
        'T = 13;',
        f'tl.to("#scene2", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, T);',
        f'tl.fromTo("#scene3", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, T);',
        f'tl.from(".point", {{ x: -40, opacity: 1, stagger: 0.2, duration: 0.6, ease: "power3.out" }}, T + 0.3);',
        'T = 20;',
        f'tl.to("#scene3", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, T);',
        f'tl.fromTo("#scene4", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, T);',
        f'tl.from("#s4-cta-box", {{ scale: 0.8, opacity: 0, duration: 0.8, ease: "back.out(1.5)" }}, T + 0.3);',
        f'tl.from("#s4-cta-btn", {{ y: 20, opacity: 0, duration: 0.5, ease: "power2.out" }}, T + 1.0);',
        f'T = {duration} - 8;',
        f'tl.to("#scene4", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, T);',
        f'tl.fromTo("#scene5", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, T);',
        f'tl.from("#s5-logo-text", {{ y: -30, opacity: 0, duration: 0.8, ease: "power3.out" }}, T + 0.3);',
        f'tl.from("#s5-slogan", {{ opacity: 0, duration: 0.5, ease: "power2.out" }}, T + 1.0);',
        f'tl.from("#s5-follow", {{ y: 20, opacity: 0, duration: 0.5, ease: "power2.out" }}, T + 1.4);',
        f'tl.from("#s5-sub", {{ opacity: 0, duration: 0.4, ease: "power2.out" }}, T + 1.7);',
        'T = 5;',
    ]
    for i, (start, end, text) in enumerate(subtitle_timing):
        rel_start = round(start - 5, 1)
        js_lines.append(f'tl.set("#sub-{i}", {{ display: "block" }}, T + {rel_start});')
        js_lines.append(f'tl.set("#sub-{i}", {{ display: "none" }}, T + {round(end - 5, 1)});')
    js_lines.extend(['', 'window.__timelines["main"] = tl;', '</script>', '</body>', '</html>'])

    html = '\n'.join(html_parts)
    html = html.replace('PC;', pc + ';').replace('SC;', sc + ';').replace('PC)', pc + ')').replace('PC44', pc + '44')
    html = html.replace('BG_SRC', bg_src).replace('W', str(W)).replace('H', str(H))
    html = html.replace('DURATION', str(duration)).replace('BRAND', brand_name)
    html = html.replace('TITLE', title).replace('AUDIENCE', target_audience)
    html = html.replace('DIRECTION', direction_name).replace('PROVINCE', province)
    html = html.replace('BODY', body_preview).replace('SLOGAN', brand_slogan)

    return html, duration, subtitle_timing


def render_video(html_path, output_dir):
    out_file = os.path.join(output_dir, "pv_content_v4.mp4")
    try:
        cmd = ["C:\\Program Files\\nodejs\\npx.CMD", "--yes", "hyperframes", "render",
               os.path.dirname(html_path), "--composition", os.path.basename(html_path),
               "--output", out_file, "--quality", "draft"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                              encoding='utf-8', errors='replace')
        if result.returncode == 0 and os.path.exists(out_file):
            return out_file
        else:
            print("Render failed:", result.stderr[-300:] if result.stderr else "unknown")
            return None
    except Exception as e:
        print(f"Render error: {e}")
        return None


def merge_audio(video_path, audio_path, output_path):
    """Merge video and audio using ffmpeg"""
    try:
        cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path,
               '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0',
               '-shortest', output_path]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        if os.path.exists(output_path):
            return output_path
        else:
            print(f"Merge failed: {r.stderr[:200]}")
            return None
    except Exception as e:
        print(f"Merge error: {e}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PV HyperFrames Template v4.0")
    parser.add_argument("--script", help="Script JSON path")
    parser.add_argument("--render", action="store_true", help="Render video")
    parser.add_argument("--tts", action="store_true", help="Generate TTS audio")
    args = parser.parse_args()

    data = load_script(args.script)
    if not data:
        print("ERROR: No script data available")
        return 1

    print(f"Generating HTML for: {data.get('title', 'Untitled')}")

    # Generate TTS
    audio_path = None
    if args.tts and data.get('full_script'):
        audio_dir = os.path.join(BASE_DIR, "data", "videos", "html")
        os.makedirs(audio_dir, exist_ok=True)
        audio_path = os.path.join(audio_dir, "audio.mp3")
        print("Generating TTS audio...")
        result = generate_tts_audio(data['full_script'], audio_path)
        if result:
            print(f"TTS OK: {result} ({os.path.getsize(result)} bytes)")
        else:
            print("TTS failed")
            audio_path = None

    # Generate HTML
    html, duration, _ = generate_html(data)
    output_dir = os.path.join(BASE_DIR, "data", "videos", "html")
    os.makedirs(output_dir, exist_ok=True)
    tracking_id = data.get("tracking_id", "PV_TEST")
    html_path = os.path.join(output_dir, f"{tracking_id}_v4.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved: {html_path}")

    if args.render:
        video_dir = os.path.join(BASE_DIR, "data", "videos")
        os.makedirs(video_dir, exist_ok=True)

        # Step 1: Render video without audio
        video_path = render_video(html_path, video_dir)
        if not video_path:
            print("Video rendering failed")
            return 1

        print(f"Video rendered: {video_path}")

        # Step 2: Merge audio if available
        if audio_path and os.path.exists(audio_path):
            merged_path = video_path.replace('.mp4', '_with_audio.mp4')
            print("Merging audio...")
            result = merge_audio(video_path, audio_path, merged_path)
            if result:
                sz = os.path.getsize(result)
                print(f"Final video: {result} ({sz//1024}KB)")
                return 0
            else:
                print("Audio merge failed, using video without audio")

        size_kb = os.path.getsize(video_path) // 1024
        print(f"Final video (no audio): {video_path} ({size_kb}KB)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
