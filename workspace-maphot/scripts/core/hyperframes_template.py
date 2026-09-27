# -*- coding: utf-8 -*-
"""
HyperFrames模板生成器 v3 — 高质量动画升级版

核心升级（基于 hyperframes-animation 规则库）：
- counting-dynamic-scale: 数字滚动+scale同步增长（开场GDP、各区GDP）
- 3d-camera-flight: 相机飞行穿过各区地图序列
- depth-of-field-blur: 当前区清晰，背景区模糊（选择性聚焦）
- stat-bars-and-fills + svg-path-draw: SVG圆环进度替代柱状图
- spring-pop-entrance: power3.out平滑入口，移除back.out弹跳
- zoom-through转场: 从全景快速推进到当前区（medium-high能量）

用法：
  python hyperframes_template.py shenzhen   # 生成深圳的HTML
  python hyperframes_template.py shenzhen --render  # 生成并渲染
"""

import io
import os
import sys
import json

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from visual_matcher import VisualMatcher as _VM
    from advanced_charts import AdvancedCharts as _AC
    from visual_tech_complete import CompleteVisualTech as _CVT
    from audio_engine import AudioEngine as _AE
    _HAS_VIZ = True
except ImportError:
    _HAS_VIZ = False

def _get_visual_plan(config, script_text=""):
    if not _HAS_VIZ or not script_text:
        return None
    try:
        return _VM.match_visual("data_ranking", script_text)
    except:
        return None

def _generate_chart_html(visual_plan, config):
    if not visual_plan or not _HAS_VIZ:
        return ""
    districts = config.get("districts", [])
    charts = []
    chart_type = visual_plan.get("chart_type", "bar_chart")
    
    # 旭日图
    if chart_type in ("bar_chart", "sunburst", "treemap"):
        sb = {"name": config.get("city", "City"), "value": 100,
              "children": [{"name": d["name"], "value": int(float(d.get("pct", "10").replace("%", "")))}
                           for d in districts[:8]]}
        charts.append("<div id='chart-sunburst' class='viz-overlay' style='display:none;'>" +
                      _AC.sunburst_chart(sb, size=400) + "</div>")
    
    # 折线图
    if chart_type == "line_chart":
        ld = [{"x": i, "y": 3000 + i*400, "label": str(2020+i)} for i in range(5)]
        charts.append("<div id='chart-line' class='viz-overlay' style='display:none;'>" +
                      _CVT.line_chart(ld, width=600, height=300) + "</div>")
    
    # 漏斗图
    if chart_type == "funnel":
        fd = [{"name": "全市", "value": 32000}, {"name": "工业", "value": 15000},
              {"name": "服务业", "value": 12000}, {"name": "金融", "value": 5000}]
        charts.append("<div id='chart-funnel' class='viz-overlay' style='display:none;'>" +
                      _CVT.funnel_chart(fd, width=500, height=300) + "</div>")
    
    sound = _AE.generate_success_sound() + _AE.generate_beep_js(freq=600, duration=0.05)
    return "".join(charts) + "<script>" + sound + "</script>"

import argparse
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'my-video')

# ===== 常量 =====
SCENE_WIDTH = 1080
SCENE_HEIGHT = 1920
TOTAL_DUR = 65

# ===== 主HTML模板 =====
HTML_MAIN = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={WIDTH}, height={HEIGHT}" />
<title>{city} — 数据地图</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  body {{ margin: 0; width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; background: #0f1923; color: #e0e0e0; font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }}
  @font-face {{ font-family: 'PingFang SC'; src: local('PingFang SC'), local('Microsoft YaHei'); }}
  @font-face {{ font-family: 'Microsoft YaHei'; src: local('Microsoft YaHei'), local('PingFang SC'); }}
  #root {{ position: relative; width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; background: linear-gradient(180deg, #0a0f1a 0%, #1a2744 50%, #0d1520 100%); }}
  
  /* 场景容器 — 全屏叠放 */
  .scene {{ position: absolute; top: 0; left: 0; width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; }}
  #scene1 {{ z-index: 1; background: #0a0f1a; }}
  #scene2 {{ z-index: 2; background: #0a0f1a; opacity: 0; }}
  #scene3 {{ z-index: 3; background: #0a0f1a; opacity: 0; }}
  #scene4 {{ z-index: 4; background: #0a0f1a; opacity: 0; }}
  #scene5 {{ z-index: 5; background: #0a0f1a; opacity: 0; }}
  #scene6 {{ z-index: 6; background: #0a0f1a; opacity: 0; }}
  #scene7 {{ z-index: 7; background: #0a0f1a; opacity: 0; }}
  #scene8 {{ z-index: 8; background: #0a0f1a; opacity: 0; }}
  #scene9 {{ z-index: 9; background: #0a0f1a; opacity: 0; }}
  #scene10 {{ z-index: 10; background: #0a0f1a; opacity: 0; }}
  #scene11 {{ z-index: 11; background: #0a0f1a; opacity: 0; }}

  /* 3D舞台 — 用于相机飞行 */
  .stage {{ position: absolute; inset: 0; perspective: 1000px; }}
  .world {{ position: absolute; inset: -100px; transform-style: preserve-3d; }}
  
  /* 背景粒子层 */
  .particle {{ position: absolute; width: 4px; height: 4px; background: #3b82f6; border-radius: 50%; opacity: 0.3; }}
  
  /* 开场元素 */
  #intro-title {{ 
    position: absolute; top: 22%; left: 0; right: 0; 
    text-align: center; font-size: 160px; font-weight: 200; 
    letter-spacing: 40px; color: #fff;
    text-shadow: 0 0 60px rgba(59,130,246,0.5);
  }}
  #intro-sub {{ 
    position: absolute; top: 36%; left: 0; right: 0; 
    text-align: center; font-size: 38px; color: #60a5fa; 
    letter-spacing: 12px; font-weight: 300;
  }}
  #intro-divider {{ 
    position: absolute; top: 42%; left: 20%; right: 20%; height: 2px; 
    background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  }}
  
  /* 计数动画容器 */
  .counter-wrap {{ 
    position: absolute; top: 48%; left: 0; right: 0; 
    text-align: center; 
  }}
  .counter {{ 
    font-variant-numeric: tabular-nums; 
    display: inline-block; 
    font-size: 200px; font-weight: 200; 
    color: #3b82f6; 
    transform-origin: center center;
    text-shadow: 0 0 80px rgba(59,130,246,0.6);
  }}
  .counter-unit {{ 
    font-size: 48px; color: #60a5fa; margin-left: 8px; 
    opacity: 0; transform: translateY(20px);
  }}
  #intro-unit {{ 
    position: absolute; top: 66%; left: 0; right: 0; 
    text-align: center; font-size: 32px; color: #64748b; 
    letter-spacing: 4px;
  }}
  
  /* 地图容器 */
  .map-wrap {{ 
    position: absolute; top: 5%; left: 5%; width: 90%; height: 72%; 
    border-radius: 32px; overflow: hidden; 
    box-shadow: 0 30px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
    background: #111827;
  }}
  .map-wrap img {{ width: 100%; height: 100%; object-fit: cover; }}
  .map-overlay {{ 
    position: absolute; bottom: 0; left: 0; right: 0; height: 50%; 
    background: linear-gradient(0deg, rgba(10,15,26,0.95) 0%, transparent 100%); 
    pointer-events: none; 
  }}
  
  /* 数据标签 */
  .data-label {{ 
    position: absolute; top: 8%; left: 5%; 
    background: rgba(15,23,42,0.9); 
    backdrop-filter: blur(16px); 
    border: 1px solid rgba(59,130,246,0.3); 
    border-radius: 16px; padding: 16px 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }}
  .data-label .tag {{ 
    display: inline-block; background: linear-gradient(135deg, #3b82f6, #6366f1); 
    color: #fff; font-size: 16px; padding: 6px 14px; border-radius: 20px;
    margin-bottom: 8px; font-weight: 500;
  }}
  .data-label .name {{ font-size: 36px; color: #fff; font-weight: 300; letter-spacing: 2px; }}
  .data-label .gdp {{ font-size: 28px; color: #60a5fa; margin-top: 4px; font-weight: 300; }}
  
  /* SVG圆环进度 - 替代柱状图 */
  .ring-container {{ 
    position: absolute; top: 12%; right: 5%; 
    width: 200px; height: 200px;
  }}
  .ring-container svg {{ width: 100%; height: 100%; transform: rotate(-90deg); }}
  .ring-bg {{ fill: none; stroke: #1e293b; stroke-width: 12; }}
  .ring-fill {{ 
    fill: none; stroke: url(#ringGradient); stroke-width: 12; 
    stroke-linecap: round; filter: drop-shadow(0 0 8px rgba(59,130,246,0.5));
  }}
  .ring-center-text {{ 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    font-size: 32px; font-weight: 300; color: #fff; text-align: center;
  }}
  .ring-center-text span {{ font-size: 18px; color: #64748b; display: block; margin-top: 4px; }}
  
  /* 信息面板 */
  .info-panel {{ 
    position: absolute; bottom: 3%; left: 5%; right: 5%; 
    background: rgba(15,23,42,0.95); 
    border: 1px solid rgba(59,130,246,0.2); 
    border-radius: 24px; padding: 28px 32px;
    box-shadow: 0 16px 48px rgba(0,0,0,0.5);
  }}
  .info-panel .title {{ 
    font-size: 48px; font-weight: 200; color: #fff; letter-spacing: 4px;
  }}
  .info-panel .stats {{ 
    display: flex; gap: 16px; margin-top: 16px; 
  }}
  .info-panel .stat-item {{ 
    flex: 1; background: rgba(59,130,246,0.06); 
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 16px; padding: 14px 10px; text-align: center;
    transition: all 0.3s ease;
  }}
  .info-panel .stat-val {{ 
    font-size: 32px; font-weight: 200; color: #60a5fa; 
    font-variant-numeric: tabular-nums;
  }}
  .info-panel .stat-val.accent {{ color: #3b82f6; }}
  .info-panel .stat-label {{ 
    font-size: 14px; color: #64748b; margin-top: 6px; letter-spacing: 1px;
  }}
  .info-panel .desc {{ 
    font-size: 20px; color: #94a3b8; margin-top: 14px; 
    font-weight: 300; text-align: center; letter-spacing: 2px;
  }}
  
  /* 结尾 */
  #outro-title {{ 
    position: absolute; top: 20%; left: 0; right: 0; 
    text-align: center; font-size: 72px; font-weight: 200; 
    color: #fff; letter-spacing: 12px;
  }}
  #outro-subtitle {{ 
    position: absolute; top: 32%; left: 0; right: 0; 
    text-align: center; font-size: 32px; color: #64748b; letter-spacing: 6px;
  }}
  #outro-options {{ 
    position: absolute; top: 44%; left: 80px; right: 80px; 
  }}
  .outro-opt {{ 
    padding: 28px 36px; margin-bottom: 18px; 
    border: 1px solid rgba(59,130,246,0.2); 
    border-radius: 16px; 
    background: rgba(59,130,246,0.04); 
    font-size: 32px; color: #cbd5e1; font-weight: 300;
  }}
  .outro-opt .opt-label {{ color: #3b82f6; font-weight: 500; margin-right: 12px; }}
  #outro-cta {{ 
    position: absolute; bottom: 18%; left: 0; right: 0; 
    text-align: center; font-size: 32px; color: #475569;
  }}
  #outro-cta .cta-icon {{ color: #3b82f6; margin-right: 8px; }}
  
  /* DoF模糊层 — filter由CSS var驱动，JS只改--dof值 */
  .dof-blur {{
    --dof: 0px;
    filter: blur(var(--dof));
    will-change: filter;
  }}
  
  /* 装饰元素 */
  .corner-accent {{
    position: absolute; width: 80px; height: 80px;
    border: 2px solid rgba(59,130,246,0.2);
  }}
  .corner-tl {{ top: 20px; left: 20px; border-right: none; border-bottom: none; }}
  .corner-tr {{ top: 20px; right: 20px; border-left: none; border-bottom: none; }}
  .corner-bl {{ bottom: 20px; left: 20px; border-right: none; border-top: none; }}
  .corner-br {{ bottom: 20px; right: 20px; border-left: none; border-top: none; }}
  
  /* 扫描线效果 */
  .scanline {{
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,0.3), transparent);
    opacity: 0;
  }}
</style>

<script>
/* P2: 场景切换音效 */
var lastSceneIndex = -1;
function playTransitionSound() {{
  try {{
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(600, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(200, ctx.currentTime + 0.15);
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.15);
  }} catch(e) {{}}
}}
/* 数字递增音效 */
function playCountUpSound() {{
  try {{
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.06, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.08);
  }} catch(e) {{}}
}}
</script>
<script>
/* BGM 轮换控制 */
var BGM_SRC = 'assets/bgm_random.mp3';
function initBGM() {{
  if (!BGM_SRC) return;
  try {{
    var b = new Audio(BGM_SRC);
    b.loop = true;
    b.volume = 0.15;
    b.play().catch(function(e) {{ console.log('BGM blocked:', e); }});
    document.addEventListener('click', function() {{
      b.play().catch(function(){{}});
    }}, {{once: true}});
  }} catch(e) {{}}
}}
window.addEventListener('load', initBGM);
</script>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="{WIDTH}" data-height="{HEIGHT}" data-duration="{TOTAL}">
  <div id="viz-layer"></div>

  <!-- SVG渐变定义 -->
  <svg width="0" height="0" style="position:absolute">
    <defs>
      <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#3b82f6" />
        <stop offset="100%" stop-color="#6366f1" />
      </linearGradient>
      <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#60a5fa" />
        <stop offset="100%" stop-color="#3b82f6" />
      </linearGradient>
    </defs>
  </svg>

  <!-- 开场场景 -->
  <div id="scene1" class="scene">
    <div class="stage">
      <div class="world" id="world1">
        <!-- 背景地图 -->
        <img src="assets/maps/{city}_全景_map_v3.png" alt="" 
             style="position:absolute;width:120%;height:120%;top:-10%;left:-10%;object-fit:cover;opacity:0.15;filter:blur(8px);" />
        <!-- 粒子装饰 -->
        <div class="particle" style="top:20%;left:15%;"></div>
        <div class="particle" style="top:35%;left:80%;"></div>
        <div class="particle" style="top:60%;left:25%;"></div>
        <div class="particle" style="top:75%;left:70%;"></div>
        <div class="particle" style="top:45%;left:50%;"></div>
        <!-- 角标装饰 -->
        <div class="corner-accent corner-tl"></div>
        <div class="corner-accent corner-tr"></div>
        <div class="corner-accent corner-bl"></div>
        <div class="corner-accent corner-br"></div>
      </div>
    </div>
    <h1 id="intro-title">{city}</h1>
    <p id="intro-sub">数据地图 · {year}</p>
    <div id="intro-divider"></div>
    <div class="counter-wrap">
      <span class="counter" id="intro-counter">0</span>
      <span class="counter-unit">万亿</span>
    </div>
    <p id="intro-unit">全市GDP总量 · {gdp_rank}</p>
  </div>

  <!-- 各区场景（scene2~sceneN） -->
  {DISTRICT_SCENES}

  <!-- 结尾场景 -->
  <div id="scene{OUTRO_ID}" class="scene">
    <div class="stage">
      <div class="world" id="world-outro">
        <img src="assets/maps/{city}_全景_map_v3.png" alt="" 
             style="position:absolute;width:110%;height:110%;top:-5%;left:-5%;object-fit:cover;opacity:0.2;filter:blur(4px);" />
        <div class="corner-accent corner-tl"></div>
        <div class="corner-accent corner-tr"></div>
        <div class="corner-accent corner-bl"></div>
        <div class="corner-accent corner-br"></div>
      </div>
    </div>
    <h1 id="outro-title">从{first}到{last}</h1>
    <p id="outro-subtitle">哪个区最让你意外？</p>
    <div id="outro-options">
      <div class="outro-opt" id="opt-a"><span class="opt-label">A.</span> {opt_a}</div>
      <div class="outro-opt" id="opt-b"><span class="opt-label">B.</span> {opt_b}</div>
      <div class="outro-opt" id="opt-c"><span class="opt-label">C.</span> {opt_c}</div>
    </div>
    <p id="outro-cta"><span class="cta-icon">▸</span> 评论区告诉我你的选择</p>
  </div>

  <!-- <audio id="bgm" src="assets/audio.mp3" data-start="0" data-track-index="10" data-volume="0.8"></audio> -->
</div>

<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{ paused: true }});
var T = 0;

// ===== 开场动画 (0-{INTRO_END}s) =====
// 基于 counting-dynamic-scale 规则：数字滚动+scale同步增长
T = 0;

// 标题 spring-pop 入场（power3.out平滑落地）
tl.fromTo("#intro-title", 
  {{ scale: 0, opacity: 0, rotation: -5 }}, 
  {{ scale: 1, opacity: 1, rotation: 0, duration: 1.2, ease: "power3.out" }}, T);

// 副标题滑入
tl.fromTo("#intro-sub", 
  {{ y: 40, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 0.8, ease: "power2.out" }}, T + 0.4);

// 分割线展开
tl.fromTo("#intro-divider", 
  {{ scaleX: 0, opacity: 0 }}, 
  {{ scaleX: 1, opacity: 1, duration: 1.0, ease: "power2.inOut" }}, T + 0.8);

// GDP数字计数 + scale增长（核心：counting-dynamic-scale）
var gdpState = {{ value: 0 }};
var INTRO_GDP = {TOTAL_GDP_RAW};
tl.to(gdpState, {{ 
  value: INTRO_GDP, duration: 2.0, ease: "power2.out",
  onUpdate: function() {{
    document.getElementById("intro-counter").textContent = Math.round(gdpState.value).toLocaleString();
  }}
}}, T + 1.2);
// scale同步增长
tl.fromTo("#intro-counter", 
  {{ scale: 0.3, opacity: 0 }}, 
  {{ scale: 1, opacity: 1, duration: 2.0, ease: "power2.out" }}, T + 1.2);
// 单位文字淡入
tl.fromTo(".counter-unit", 
  {{ opacity: 0, y: 20 }}, 
  {{ opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }}, T + 3.0);

// 底部单位说明
tl.fromTo("#intro-unit", 
  {{ y: 30, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 0.8, ease: "power2.out" }}, T + 3.5);

// ===== 开场 → 第一个区：zoom-through 转场 =====
// 注意：scene2入场由区1转场统一处理，此处只做scene1退出
T = {INTRO_END};
// scene1 推出 + visibility kill
tl.to("#scene1", 
  {{ scale: 1.5, opacity: 0, filter: "blur(15px)", duration: 0.6, ease: "power4.in", overwrite: "auto" }}, T);
tl.set("#scene1", {{ visibility: "hidden" }}, T + 0.6);
// scene2 在区1转场时统一入场（避免重复tween）

// ===== 各区展示动画函数 =====
// 基于 depth-of-field-blur + counting-dynamic-scale + stat-bars-and-fills

{DISTRICT_ANIMATIONS}

// ===== 最后一个区 → 结尾：zoom-through 转场 =====
T = {OUTRO_START};
// 最后一个区推出 + visibility kill
tl.to("#scene{LAST_DISTRICT_ID}", 
  {{ scale: 1.5, opacity: 0, filter: "blur(15px)", duration: 0.6, ease: "power4.in", overwrite: "auto" }}, T);
tl.set("#scene{LAST_DISTRICT_ID}", {{ visibility: "hidden" }}, T + 0.6);
// 结尾场景滑入
tl.fromTo("#scene{OUTRO_ID}", 
  {{ yPercent: 100, opacity: 0 }}, 
  {{ yPercent: 0, opacity: 1, duration: 0.9, ease: "power3.out" }}, T);

// ===== 结尾动画 =====
tl.fromTo("#outro-title", 
  {{ y: 60, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 1.0, ease: "power3.out" }}, T + 0.5);
tl.fromTo("#outro-subtitle", 
  {{ y: 40, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 0.8, ease: "power2.out" }}, T + 1.2);
tl.fromTo("#opt-a", 
  {{ x: -80, opacity: 0 }}, 
  {{ x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, T + 2.0);
tl.fromTo("#opt-b", 
  {{ x: -80, opacity: 0 }}, 
  {{ x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, T + 2.5);
tl.fromTo("#opt-c", 
  {{ x: -80, opacity: 0 }}, 
  {{ x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, T + 3.0);
tl.fromTo("#outro-cta", 
  {{ y: 30, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 0.7, ease: "power2.out" }}, T + 3.8);

window.__timelines["main"] = tl;
</script>

%%CHART_HTML_PLACEHOLDER%%
<script>%%VIZ_ANIM_PLACEHOLDER%%</script>
</body>
</html>'''

# 每个区的场景HTML模板
HTML_DISTRICT_SCENE = '''  <div id="scene{SCENE_ID}" class="scene">
    <div class="stage">
      <div class="world" id="world-{ID}">
        <img src="assets/maps/{city}_{NAME}_map_v3.png" alt="{NAME}" 
             class="dof-blur" data-depth="{DEPTH}" />
        <div class="map-overlay"></div>
        <div class="corner-accent corner-tl"></div>
        <div class="corner-accent corner-tr"></div>
        <div class="corner-accent corner-bl"></div>
        <div class="corner-accent corner-br"></div>
      </div>
    </div>
    <div class="data-label" id="lbl-{ID}">
      <span class="tag" id="tag-{ID}">#{RANK}</span>
      <div class="name" id="name-{ID}">{NAME}</div>
      <div class="gdp" id="gdp-{ID}">{GDP}</div>
    </div>
    <!-- SVG圆环进度 -->
    <div class="ring-container" id="ring-{ID}">
      <svg viewBox="0 0 200 200">
        <circle class="ring-bg" cx="100" cy="100" r="85" />
        <circle class="ring-fill" id="ring-fill-{ID}" cx="100" cy="100" r="85" 
                stroke-dasharray="534" stroke-dashoffset="534" />
      </svg>
      <div class="ring-center-text">
        <span id="ring-pct-{ID}">0%</span>
        <span>占比</span>
      </div>
    </div>
    <!-- 信息面板 -->
    <div class="info-panel" id="panel-{ID}">
      <div class="title" id="ptitle-{ID}">{NAME}</div>
      <div class="stats">
        <div class="stat-item">
          <div class="stat-val accent" id="sgdp-{ID}">{GDP}</div>
          <div class="stat-label">GDP</div>
        </div>
        <div class="stat-item">
          <div class="stat-val" id="sper-{ID}">{PER_GDP}</div>
          <div class="stat-label">人均GDP</div>
        </div>
        <div class="stat-item">
          <div class="stat-val" id="spct-{ID}">{PCT}</div>
          <div class="stat-label">占比</div>
        </div>
      </div>
      <div class="desc" id="desc-{ID}">{DESC}</div>
    </div>
  </div>'''


def generate_html(config, audio_duration=None, visual_plan=None, script_text=""):
    """根据城市配置生成HyperFrames v3 HTML"""
    city = config['city']
    districts = config['districts']
    n = len(districts)
    
    # 时间参数
    intro_dur = 7.5
    district_dur = 6.0  # 每个区展示时间
    outro_dur = 8.0
    
    if audio_duration:
        remaining = audio_duration - intro_dur - outro_dur
        if remaining > 0:
            district_dur = max(remaining / n, 4.0)
    
    # 计算总时长
    intro_end = intro_dur
    district_start = intro_end + 0.3  # 转场后开始
    district_end = district_start + n * district_dur
    outro_start = district_end + 0.3
    total_duration = outro_start + outro_dur
    
    # GDP原始值（用于计数动画）
    total_gdp_raw = 34600  # 3.46万亿 = 34600亿
    
    # 获取最大GDP用于圆环比例
    gdp_values = [d.get('gdp_raw', 0) or 0 for d in districts]
    max_gdp = max(gdp_values) if gdp_values else 1
    
    # 生成各区场景HTML和动画
    district_scenes_html = ""
    district_animations_js = ""
    
    for i, d in enumerate(districts):
        scene_id = i + 2  # scene2开始
        did = f"d{i}"
        depth = i + 1  # DoF深度层级
        
        # 圆环周长 = 2 * π * 85 ≈ 534
        ring_circumference = 534
        pct_value = float(d.get('pct', '0%').replace('%', ''))
        ring_target = ring_circumference * (1 - pct_value / 100)
        
        # 生成场景HTML
        district_scenes_html += HTML_DISTRICT_SCENE.format(
            SCENE_ID=scene_id,
            ID=did,
            city=city,
            NAME=d['name'],
            RANK=i + 1,
            GDP=d.get('gdp', ''),
            PER_GDP=d.get('per_gdp', ''),
            PCT=d.get('pct', ''),
            DESC=d.get('desc', ''),
            DEPTH=depth
        )
        
        # 计算转场时间
        t_scene_in = district_start + i * district_dur
        
        # 转场动画：zoom-through
        if i == 0:
            prev_scene = "scene1"
        else:
            prev_scene = f"scene{scene_id - 1}"
        
        # 转场：从上一场景zoom through到当前场景
        district_animations_js += f'''
// ===== 区{i+1}: {d['name']} (scene{prev_scene.replace("scene", "")} → scene{scene_id}) =====
T = {t_scene_in:.1f};

// 上一场景推出（zoom out + blur）+ visibility kill
var prevScene{did.upper()} = "#scene{prev_scene.replace("scene", "")}";
tl.to(prevScene{did.upper()}, 
  {{ scale: 1.5, opacity: 0, filter: "blur(15px)", duration: 0.6, ease: "power4.in", overwrite: "auto" }}, T);
tl.set(prevScene{did.upper()}, {{ visibility: "hidden" }}, T + 0.6);

// 当前场景拉入（zoom in + 清晰）
tl.fromTo("#scene{scene_id}", 
  {{ scale: 0.6, opacity: 0, filter: "blur(25px)" }}, 
  {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.8, ease: "power3.out" }}, T);

// ===== 当前区内容动画 =====
var t{did} = T + 0.5;

// 1. 数据标签 spring-pop 入场
tl.fromTo("#lbl-{did}", 
  {{ scale: 0.3, opacity: 0, rotation: -10 }}, 
  {{ scale: 1, opacity: 1, rotation: 0, duration: 0.7, ease: "power3.out" }}, t{did});

// 2. 地图容器淡入（带轻微scale）
tl.fromTo("#wrap-{did}, #world-{did}", 
  {{ scale: 0.85, opacity: 0 }}, 
  {{ scale: 1, opacity: 1, duration: 0.9, ease: "power2.out" }}, t{did} + 0.1);

// 3. SVG圆环进度动画（基于 stat-bars-and-fills + svg-path-draw）
var ring{did} = document.getElementById("ring-fill-{did}");
var LEN{did.upper()} = ring{did}.getTotalLength();
ring{did}.style.strokeDasharray = LEN{did.upper()};
ring{did}.style.strokeDashoffset = LEN{did.upper()};
tl.to(ring{did}, {{ 
  strokeDashoffset: {ring_target:.1f}, duration: 1.4, ease: "power2.out" 
}}, t{did} + 0.3);

// 4. 百分比数字计数（counting-dynamic-scale）
var pctState{did.upper()} = {{ value: 0 }};
tl.to(pctState{did.upper()}, {{ 
  value: {pct_value}, duration: 1.4, ease: "power2.out",
  onUpdate: function() {{
    var el = document.getElementById("ring-pct-{did}");
    if(el) el.textContent = Math.round(pctState{did.upper()}.value) + "%";
  }}
}}, t{did} + 0.3);

// 5. 信息面板 slide-up 入场
tl.fromTo("#panel-{did}", 
  {{ y: 100, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 0.7, ease: "power3.out" }}, t{did} + 0.4);

// 6. 数据项依次弹出（stagger）
tl.fromTo("#panel-{did} .stat-item:nth-child(1)", 
  {{ scale: 0.5, opacity: 0 }}, 
  {{ scale: 1, opacity: 1, duration: 0.5, ease: "power3.out" }}, t{did} + 0.6);
tl.fromTo("#panel-{did} .stat-item:nth-child(2)", 
  {{ scale: 0.5, opacity: 0 }}, 
  {{ scale: 1, opacity: 1, duration: 0.5, ease: "power3.out" }}, t{did} + 0.75);
tl.fromTo("#panel-{did} .stat-item:nth-child(3)", 
  {{ scale: 0.5, opacity: 0 }}, 
  {{ scale: 1, opacity: 1, duration: 0.5, ease: "power3.out" }}, t{did} + 0.9);

// 7. 描述文字淡入
tl.fromTo("#desc-{did}", 
  {{ y: 15, opacity: 0 }}, 
  {{ y: 0, opacity: 1, duration: 0.5, ease: "power2.out" }}, t{did} + 1.1);

// 8. DoF效果：当前区清晰，只模糊最近3个背景层（避免heavy overlay警告）
tl.to('.dof-blur[data-depth="' + {depth} + '"]', 
  {{ "--dof": "0px", opacity: 1, duration: 0.8, ease: "power2.out" }}, t{did});
// 只模糊depth > current的层，最多3层（渐进模糊：5px/10px/15px）
var dofTarget{did.upper()} = {depth};
if(dofTarget{did.upper()} + 1 <= {n}) {{
  tl.to(".dof-blur[data-depth='" + (dofTarget{did.upper()} + 1) + "']", 
    {{ "--dof": "5px", opacity: 0.6, duration: 0.8, ease: "power2.inOut" }}, t{did});
}}
if(dofTarget{did.upper()} + 2 <= {n}) {{
  tl.to(".dof-blur[data-depth='" + (dofTarget{did.upper()} + 2) + "']", 
    {{ "--dof": "10px", opacity: 0.45, duration: 0.8, ease: "power2.inOut" }}, t{did});
}}
if(dofTarget{did.upper()} + 3 <= {n}) {{
  tl.to(".dof-blur[data-depth='" + (dofTarget{did.upper()} + 3) + "']", 
    {{ "--dof": "15px", opacity: 0.35, duration: 0.8, ease: "power2.inOut" }}, t{did});
}}
'''
    
    # 结尾场景ID
    outro_id = n + 2
    last_district_id = n + 1
    
    # 背景装饰动画
    glow_repeat = int(total_duration / 10)
    
    # 渲染HTML
    # 新增：视觉技术图表和音效
    _chart_html = ""
    if _HAS_VIZ and visual_plan:
        _chart_html = _generate_chart_html(visual_plan, config)
    
    html = HTML_MAIN.format(
        WIDTH=SCENE_WIDTH,
        HEIGHT=SCENE_HEIGHT,
        TOTAL=total_duration,
        city=city,
        year=config.get('year', '2026'),
        total_gdp=config['total_gdp'],
        gdp_rank=config['gdp_rank'],
        TOTAL_GDP_RAW=total_gdp_raw,
        INTRO_END=intro_end,
        DISTRICT_ANIMATIONS=district_animations_js,
        OUTRO_START=outro_start,
        OUTRO_ID=outro_id,
        LAST_DISTRICT_ID=last_district_id,
        DISTRICT_SCENES=district_scenes_html,
        first=districts[0]['name'],
        last=districts[-1]['name'],
        opt_a=config['opt_a'],
        opt_b=config['opt_b'],
        opt_c=config['opt_c']
    )
    
    # 注入图表HTML和音效
    if _chart_html:
        html = html + "\n<div id='viz-layer'>" + _chart_html + "</div>"
        # 添加动画
        viz_js = "var sb=document.getElementById('chart-sunburst');if(sb)gsap.fromTo(sb,{opacity:0,scale:0.8},{opacity:1,scale:1,duration:1.2,ease:'power2.out'},%%OUTRO_START%%+1.5);"

    
    # 新增：注入图表和音效
    if _chart_html:
        html = html.replace("%%CHART_HTML_PLACEHOLDER%%", _chart_html)
        viz_js = ""
        if "chart-sunburst" in _chart_html:
            viz_js += "var sb=document.getElementById('chart-sunburst');if(sb)gsap.fromTo(sb,{opacity:0,scale:0.8},{opacity:1,scale:1,duration:1.2,ease:'power2.out'},%%OUTRO_START%%+1.5);"
        if "chart-line" in _chart_html:
            viz_js += "var ln=document.getElementById('chart-line');if(ln)gsap.fromTo(ln,{opacity:0,y:30},{opacity:1,y:0,duration:1,ease:'power2.out'},%%OUTRO_START%%+2.1);"
        html = html.replace("%%VIZ_ANIM_PLACEHOLDER%%", "<script>" + viz_js + "</script>")
    else:
        html = html.replace("%%CHART_HTML_PLACEHOLDER%%", "").replace("%%VIZ_ANIM_PLACEHOLDER%%", "")
    
    # 新增：注入图表HTML和音效
    if _chart_html:
        html = html.replace("%%CHART_HTML_PLACEHOLDER%%", _chart_html)
        viz_js = ""
        if "chart-sunburst" in _chart_html:
            viz_js += "var sb=document.getElementById('chart-sunburst');if(sb)gsap.fromTo(sb,{opacity:0,scale:0.8},{opacity:1,scale:1,duration:1.2,ease:'power2.out'},OUTRO_START+1.5);"
        if "chart-line" in _chart_html:
            viz_js += "var ln=document.getElementById('chart-line');if(ln)gsap.fromTo(ln,{opacity:0,y:30},{opacity:1,y:0,duration:1,ease:'power2.out'},OUTRO_START+2.1);"
        html = html.replace("%%VIZ_ANIM_PLACEHOLDER%%", "<script>" + viz_js + "</script>")
    else:
        html = html.replace("%%CHART_HTML_PLACEHOLDER%%", "").replace("%%VIZ_ANIM_PLACEHOLDER%%", "")
    
    return html
