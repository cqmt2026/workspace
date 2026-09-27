# -*- coding: utf-8 -*-
"""
HyperFrames 省份排名模板 v4.3 — 全时段动画版

基于v4改进：
1. 地图持续缓慢平移（永不静止）
2. 精简到8个城市，每行停留2.5秒
3. 总时长压缩到50秒
4. 背景呼吸缩放循环

用法：
  python hyperframes_ranking_v43.py --demo
  python hyperframes_ranking_v43.py --config ranking_config.json
"""

import io
import os
import sys
import json
import argparse
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'my-video')

SCENE_WIDTH = 1080
SCENE_HEIGHT = 1920


def generate_html(config, audio_duration=None):
    """根据配置生成省份排名HTML（v4.3全时段动画版）"""
    topic = config.get('topic', '数据地图')
    title = config.get('title', '数据地图')
    subtitle = config.get('subtitle', '')
    badge_text = config.get('badge_text', '')
    badge_unit = config.get('badge_unit', '')
    map_image = config.get('map_image', 'egg_price_map.png')
    ring_value = config.get('ring_value', 0)
    ring_label = config.get('ring_label', '涨幅')
    south_label = config.get('south_label', '南方均价')
    north_label = config.get('north_label', '北方均价')
    south_val = config.get('south_val', 0)
    north_val = config.get('north_val', 0)
    south_rank = config.get('south_rank', '')
    north_rank = config.get('north_rank', '')
    reasons = config.get('reasons', [])
    outro_question = config.get('outro_question', '你家多少钱？')
    outro_sub = config.get('outro_sub', '评论区告诉我')
    options = config.get('options', [])
    cta_text = config.get('cta_text', '点赞关注，每天看数据')
    
    # v4.3: 精简到最多8个城市
    ranking_data = config.get('ranking_data', [])
    max_cities = min(len(ranking_data), 8)
    cities = ranking_data[:max_cities]
    
    # 异常值高亮配置
    anomaly_idx = config.get('anomaly_idx', 3)  # 默认第4名
    anomaly_highlight = cities[anomaly_idx] if anomaly_idx < len(cities) else None
    
    # 对比双栏配置
    compare_south = config.get('compare_south', {})
    compare_north = config.get('compare_north', {})

    # v4.3: 总时长50秒
    intro_dur = 2.25
    content_dur = 40.0  # 从52s压缩到40s
    outro_dur = 8.0     # 从15s压缩到8s
    total_dur = intro_dur + content_dur + outro_dur
    outro_start = intro_dur + content_dur

    if audio_duration:
        total_dur = max(total_dur, audio_duration + 2)

    # v4.3: 榜单滚动动画（8个城市，每行2.5秒）
    rank_anims = ""
    t_rs = intro_dur + 8.0  # 榜单从开场后8秒开始
    for idx, city in enumerate(cities):
        ti = t_rs + idx * 2.5
        rc = '#rank-%d' % (idx + 1)
        rank_anims += 'tl.fromTo("%s",{y:30,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},%.1f);\n' % (rc, ti)
        # 异常值强调
        if city.get('is_anomaly', False) or (idx == anomaly_idx and anomaly_highlight):
            rank_anims += 'tl.to("%s .rank-value",{color:"#ef4444",scale:1.15,duration:0.25,ease:"back.out(2)"},%.1f);\n' % (rc, ti + 0.3)
            rank_anims += 'tl.to("%s .rank-value",{scale:1,duration:0.25,ease:"power2.out"},%.1f);\n' % (rc, ti + 0.55)
    rank_anims += 'tl.to("#rank-list-wrap",{opacity:0,duration:0.4,ease:"power2.in"},%.1f);\n' % (outro_start - 2.0)

    # 构建reason cards HTML（保留v4结构）
    reason_cards = ""
    for i, r in enumerate(reasons):
        num = r.get("num", chr(9312 + i))
        r_title = r.get("title", "")
        r_desc = r.get("desc", "")
        bar_html = ""
        if r.get("bar", False):
            bar_class = "hot" if r.get("hot", False) else "empty"
            bar_html = '<div class="rc-bar"><div class="rc-bar-fill ' + bar_class + '" id="bar-' + str(i) + '"></div></div>'
        reason_cards += '''
    <div class="reason-card" id="reason-%d">
      <div class="rc-title"><span class="rc-num">%s</span> %s</div>
      <div class="rc-sub">%s</div>
      %s
    </div>''' % (i, num, r_title, r_desc, bar_html)

    # 构建options HTML
    options_html = ""
    for j, opt in enumerate(options):
        letter = chr(65 + j)
        options_html += '      <div class="outro-opt" id="opt-%s"><span class="opt-label">%s.</span> %s</div>\n' % (letter, letter, opt)

    # 生成原因卡片的动画代码（v4.3: 加快节奏）
    reason_anims = ""
    for i, r in enumerate(reasons):
        t_in = 12.0 + i * 6.0  # 从15s提前到12s
        t_out = t_in + 5.0     # 停留时间缩短
        bar_width = "85%" if r.get("hot", False) else ("12%" if r.get("empty", False) else "50%")
        rotation = "-5" if i % 2 == 0 else "5"
        reason_anims += '\n// 原因%d (%s) - %.1fs入场\n' % (i + 1, r.get('title', ''), t_in)
        reason_anims += 'tl.fromTo("#reason-%d",{y:100,opacity:0,rotation:%s},{y:0,opacity:1,rotation:0,duration:0.6,ease:"power3.out"}, %.1f);\n' % (i, rotation, t_in)
        if r.get("bar", False):
            reason_anims += 'tl.to("#bar-%d",{width:"%s",duration:1.0,ease:"power2.out"}, %.1f);\n' % (i, bar_width, t_in + 1)
        if r.get("flash", False):
            reason_anims += 'tl.to("#reason-%d .rc-num",{color:"#ef4444",scale:1.2,duration:0.2,ease:"power2.inOut",yoyo:true,repeat:4}, %.1f);\n' % (i, t_in + 1.5)
        if i > 0:
            prev_t_out = 12.0 + (i - 1) * 6.0 + 5.0
            reason_anims += '// %.1fs: 推出原因%d\n' % (t_out, i)
            reason_anims += 'tl.to("#reason-%d",{scale:0.8,y:-80,opacity:0,duration:0.4,ease:"power2.in"}, %.1f);\n' % (i - 1, t_out)

    # 生成选项动画
    option_anims = ""
    for j, opt in enumerate(options):
        letter = chr(65 + j)
        t_opt = outro_start + 1.0 + j * 0.5  # 加快选项动画
        option_anims += 'tl.fromTo("#opt-%s",{x:-80,opacity:0},{x:0,opacity:1,duration:0.5,ease:"back.out(1.4)"}, %.1f);\n' % (letter, t_opt)

    # v4.3 CSS样式（添加地图持续动画）
    css_v43 = '''
  /* v4.3: 地图持续缓慢平移 */
  #map-bg { position: absolute; width: 110%; height: 100%; object-fit: cover; top: 0; }
  #bg-img-1 { position: absolute; width: 120%; height: 120%; top: -10%; left: -10%; object-fit: cover; opacity: 0.1; filter: blur(8px); }
  
  /* v4.3: 对比双栏 */
  .compare-wrap { position: absolute; top: 6%; left: 4%; right: 4%; display: flex; gap: 16px; opacity: 0; }
  .compare-col { flex: 1; border-radius: 20px; padding: 20px 18px; text-align: center; border: 2px solid rgba(59,130,246,0.3); background: rgba(15,23,42,0.95); }
  .compare-col.south { border-color: rgba(239,68,68,0.4); background: rgba(239,68,68,0.08); }
  .compare-col.north { border-color: rgba(59,130,246,0.4); background: rgba(59,130,246,0.08); }
  .compare-col .cc-label { font-size: 20px; color: #64748b; letter-spacing: 3px; margin-bottom: 8px; }
  .compare-col .cc-val { font-size: 52px; font-weight: 700; letter-spacing: 2px; }
  .compare-col.south .cc-val { color: #ef4444; }
  .compare-col.north .cc-val { color: #3b82f6; }
  .compare-col .cc-sub { font-size: 14px; color: #94a3b8; margin-top: 6px; line-height: 1.3; }
  
  /* v4.3: 异常值高亮 */
  #ab-hl { position: absolute; top: 48%; left: 50%; transform: translate(-50%, -50%) scale(0.8); background: rgba(239,68,68,0.15); border: 3px solid #ef4444; border-radius: 20px; padding: 16px 32px; opacity: 0; z-index: 10; }
  .ab-hl-text { font-size: 28px; color: #ef4444; font-weight: 700; letter-spacing: 2px; }
  #ab-note { position: absolute; top: 58%; left: 50%; transform: translateX(-50%) translateY(15px); font-size: 18px; color: #f59e0b; letter-spacing: 2px; opacity: 0; }
  
  /* v4.3: 榜单样式 */
  .rank-list-wrap { position: absolute; top: 40%; left: 4%; right: 4%; opacity: 0; }
  .rank-list-header { display: flex; gap: 12px; margin-bottom: 8px; padding: 0 50px 0 0; font-size: 15px; color: #64748b; }
  .rank-row { display: flex; gap: 12px; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(59,130,246,0.1); opacity: 0; }
  .rank-num { width: 36px; height: 36px; border-radius: 50%; background: rgba(59,130,246,0.2); color: #3b82f6; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; }
  .rank-name { flex: 1; font-size: 22px; color: #fff; font-weight: 500; }
  .rank-value { flex: 1; font-size: 22px; text-align: right; }
  .rank-per { width: 100px; font-size: 16px; color: #94a3b8; text-align: right; }
  .rank-row.anomaly-row .rank-value { color: #ef4444; font-weight: 700; }
  .rank-row.anomaly-row { background: rgba(239,68,68,0.1); border-radius: 8px; padding: 8px 6px; }
  .rank-row.highlight-row .rank-num { background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff; }
'''

    # 构建完整HTML — 用占位符+replace，避免%格式冲突
    html = '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>__TITLE__</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  body { margin:0; width:1080px; height:1920px; overflow:hidden; background:#0a0f1a; color:#e0e0e0; font-family:"PingFang SC","Microsoft YaHei",sans-serif; }
  #root { position:relative; width:1080px; height:1920px; overflow:hidden; background:linear-gradient(180deg,#0a0f1a 0%,#1a2744 50%,#0d1520 100%); }
  .scene { position:absolute; top:0; left:0; width:1080px; height:1920px; overflow:hidden; }
  
  /* v4 品牌片头 */
  #brand-intro { position:absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:50; background:#0a0f1a; }
  #brand-logo-wrap { position:relative; width:100px; height:100px; }
  #brand-logo-ring { position:absolute; inset:0; border:3px solid rgba(59,130,246,0.4); border-radius:50%; opacity:0; }
  #brand-logo-dot { position:absolute; top:50%; left:50%; width:14px; height:14px; background:#3b82f6; border-radius:50%; transform:translate(-50%,-50%); opacity:0; box-shadow:0 0 25px rgba(59,130,246,0.8); }
  #brand-name { font-size:42px; color:#fff; letter-spacing:10px; font-weight:300; margin-top:24px; opacity:0; }
  #brand-slogan { font-size:20px; color:#64748b; letter-spacing:5px; margin-top:8px; opacity:0; }
  
  /* scene1 开场 */
  #scene1 { z-index:1; }
  #intro-title { position:absolute; top:22%; left:0; right:0; text-align:center; font-size:130px; font-weight:700; color:#fff; letter-spacing:5px; text-shadow:0 0 80px rgba(239,68,68,0.6); }
  #intro-sub { position:absolute; top:36%; left:0; right:0; text-align:center; font-size:36px; color:#f59e0b; letter-spacing:5px; font-weight:400; }
  #intro-divider { position:absolute; top:40%; left:25%; right:25%; height:3px; background:linear-gradient(90deg,transparent,#f59e0b,transparent); }
  #intro-badge { position:absolute; top:44%; left:0; right:0; text-align:center; font-size:72px; font-weight:700; color:#f59e0b; letter-spacing:3px; }
  #intro-unit { position:absolute; top:52%; left:0; right:0; text-align:center; font-size:26px; color:#64748b; letter-spacing:2px; }
  
  /* scene2 主画面 */
  #scene2 { z-index:2; opacity:0; }
  .map-wrap { position:absolute; top:0; left:0; width:100%; height:82%; overflow:hidden; }
  .map-wrap img { width:100%; height:100%; object-fit:cover; }
  .map-overlay { position:absolute; bottom:0; left:0; right:0; height:60%; background:linear-gradient(0deg,rgba(10,15,26,0.98) 0%,transparent 100%); pointer-events:none; }
  
  /* 圆环进度 */
  .ring-wrap { position:absolute; top:38%; left:50%; transform:translate(-50%,-50%); }
  #ring-progress { width:160px; height:160px; }
  #ring-bg { fill:none; stroke:rgba(59,130,246,0.2); stroke-width:10; }
  #ring-fill { fill:none; stroke:url(#ringGrad); stroke-width:10; stroke-linecap:round; stroke-dasharray:408; stroke-dashoffset:408; transform:rotate(-90deg); transform-origin:center; }
  #ring-value { font-size:42px; font-weight:700; fill:#f59e0b; text-anchor:middle; dominant-baseline:middle; }
  #ring-label { font-size:14px; fill:#64748b; text-anchor:middle; }
  
  /* 数据面板 */
  .panel-section { position:absolute; bottom:5%; left:4%; right:4%; background:rgba(15,23,42,0.92); border-radius:16px; padding:14px 18px; }
  .panel-label { font-size:14px; color:#64748b; letter-spacing:3px; margin-bottom:8px; }
  .big-val { font-size:44px; font-weight:700; color:#3b82f6; letter-spacing:2px; }
  .big-val.hot { color:#ef4444; }
  .big-unit { font-size:20px; color:#94a3b8; font-weight:300; margin-left:4px; }
  .panel-desc { font-size:16px; color:#94a3b8; margin-top:4px; letter-spacing:1px; }
  .highlight { color:#ef4444; font-weight:700; }
  
  /* 原因卡片 */
  .reasons-section { position:absolute; top:52%; left:4%; right:4%; }
  .reasons-label { font-size:14px; color:#64748b; letter-spacing:3px; margin-bottom:10px; }
  .reason-card { background:rgba(15,23,42,0.92); border:1px solid rgba(59,130,246,0.2); border-radius:12px; padding:14px 18px; margin-bottom:10px; opacity:0; }
  .rc-title { font-size:18px; color:#e0e0e0; font-weight:600; margin-bottom:4px; }
  .rc-num { color:#3b82f6; font-weight:700; margin-right:6px; }
  .rc-sub { font-size:14px; color:#94a3b8; line-height:1.4; }
  .rc-bar { height:6px; background:rgba(59,130,246,0.15); border-radius:3px; margin-top:8px; overflow:hidden; }
  .rc-bar-fill { height:100%; border-radius:3px; width:0; transition:width 1s ease; }
  .rc-bar-fill.hot { background:linear-gradient(90deg,#ef4444,#f97316); }
  .rc-bar-fill.empty { background:#64748b; }
  
  /* 结尾互动 */
  #scene3 { z-index:3; }
  #outro-title { position:absolute; top:35%; left:0; right:0; text-align:center; font-size:64px; font-weight:700; color:#fff; letter-spacing:4px; }
  #outro-sub { position:absolute; top:46%; left:0; right:0; text-align:center; font-size:24px; color:#64748b; }
  #outro-cta { position:absolute; bottom:20%; left:0; right:0; text-align:center; font-size:24px; color:#475569; }
  #brand-outro { position:absolute; bottom:6%; left:0; right:0; text-align:center; z-index:50; opacity:0; }
  #brand-outro-text { font-size:22px; color:#475569; letter-spacing:7px; }
  #brand-outro-text span { color:#3b82f6; }
  
  /* v4.3 新增样式 */
__V43_CSS__
  
  /* 旧版样式兼容 */
  .scene { position:absolute; top:0; left:0; width:1080px; height:1920px; overflow:hidden; }
  .stage { position:absolute; inset:0; perspective:1000px; }
  .world { position:absolute; inset:-100px; transform-style:preserve-3d; transform-origin:50% 50%; will-change:transform; }
  .corner-accent { position:absolute; width:80px; height:80px; border:2px solid rgba(59,130,246,0.2); }
  .corner-tl { top:20px; left:20px; border-right:none; border-bottom:none; }
  .corner-tr { top:20px; right:20px; border-left:none; border-bottom:none; }
  .corner-bl { bottom:20px; left:20px; border-right:none; border-top:none; }
  .corner-br { bottom:20px; right:20px; border-left:none; border-top:none; }
  #scene1 { z-index:1; }
  #intro-title { position:absolute; top:22%; left:0; right:0; text-align:center; font-size:130px; font-weight:700; color:#fff; letter-spacing:5px; text-shadow:0 0 80px rgba(239,68,68,0.6); }
  #intro-sub { position:absolute; top:36%; left:0; right:0; text-align:center; font-size:36px; color:#f59e0b; letter-spacing:5px; font-weight:400; }
  #intro-divider { position:absolute; top:40%; left:25%; right:25%; height:3px; background:linear-gradient(90deg,transparent,#f59e0b,transparent); }
  #intro-badge { position:absolute; top:44%; left:0; right:0; text-align:center; font-size:72px; font-weight:700; color:#f59e0b; letter-spacing:3px; }
  #intro-unit { position:absolute; top:52%; left:0; right:0; text-align:center; font-size:26px; color:#64748b; letter-spacing:2px; }
  #scene2 { z-index:2; opacity:0; }
  .map-wrap { position:absolute; top:0; left:0; width:100%; height:82%; overflow:hidden; }
  .map-wrap img { width:100%; height:100%; object-fit:cover; }
  .map-overlay { position:absolute; bottom:0; left:0; right:0; height:60%; background:linear-gradient(0deg,rgba(10,15,26,0.98) 0%,transparent 100%); pointer-events:none; }
  .region-overlay { position:absolute; top:0; left:0; width:100%; height:82%; pointer-events:none; }
  .region-mask { position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; }
  .big-price { position:absolute; background:rgba(15,23,42,0.92); border:2px solid rgba(59,130,246,0.3); border-radius:20px; padding:20px 30px; text-align:center; opacity:0; }
  .big-price .bp-val { font-size:56px; font-weight:700; letter-spacing:2px; }
  .big-price .bp-label { font-size:18px; color:#64748b; margin-top:4px; letter-spacing:2px; }
  .big-price .bp-unit { font-size:22px; color:#94a3b8; font-weight:300; }
  .big-price.south-price { top:35%; left:50%; transform:translateX(-50%); }
  .big-price.south-price .bp-val { color:#ef4444; }
  .big-price.north-price { top:30%; left:50%; transform:translateX(-50%); }
  .ring-wrap { position:absolute; top:38%; left:50%; transform:translate(-50%,-50%); }
  #ring-progress { width:160px; height:160px; }
  #ring-bg { fill:none; stroke:rgba(59,130,246,0.2); stroke-width:10; }
  #ring-fill { fill:none; stroke:url(#ringGrad); stroke-width:10; stroke-linecap:round; stroke-dasharray:408; stroke-dashoffset:408; transform:rotate(-90deg); transform-origin:center; }
  #ring-value { font-size:42px; font-weight:700; fill:#f59e0b; text-anchor:middle; dominant-baseline:middle; }
  #ring-label { font-size:14px; fill:#64748b; text-anchor:middle; }
  .panel-section { position:absolute; bottom:5%; left:4%; right:4%; background:rgba(15,23,42,0.92); border-radius:16px; padding:14px 18px; }
  .panel-label { font-size:14px; color:#64748b; letter-spacing:3px; margin-bottom:8px; }
  .big-val { font-size:44px; font-weight:700; color:#3b82f6; letter-spacing:2px; }
  .big-val.hot { color:#ef4444; }
  .big-unit { font-size:20px; color:#94a3b8; font-weight:300; margin-left:4px; }
  .panel-desc { font-size:16px; color:#94a3b8; margin-top:4px; letter-spacing:1px; }
  .highlight { color:#ef4444; font-weight:700; }
  .reasons-section { position:absolute; top:52%; left:4%; right:4%; }
  .reasons-label { font-size:14px; color:#64748b; letter-spacing:3px; margin-bottom:10px; }
  .reason-card { background:rgba(15,23,42,0.92); border:1px solid rgba(59,130,246,0.2); border-radius:12px; padding:14px 18px; margin-bottom:10px; opacity:0; }
  .rc-title { font-size:18px; color:#e0e0e0; font-weight:600; margin-bottom:4px; }
  .rc-num { color:#3b82f6; font-weight:700; margin-right:6px; }
  .rc-sub { font-size:14px; color:#94a3b8; line-height:1.4; }
  .rc-bar { height:6px; background:rgba(59,130,246,0.15); border-radius:3px; margin-top:8px; overflow:hidden; }
  .rc-bar-fill { height:100%; border-radius:3px; width:0; transition:width 1s ease; }
  .rc-bar-fill.hot { background:linear-gradient(90deg,#ef4444,#f97316); }
  .rc-bar-fill.empty { background:#64748b; }
  #scene3 { z-index:3; }
  #outro-title { position:absolute; top:35%; left:0; right:0; text-align:center; font-size:64px; font-weight:700; color:#fff; letter-spacing:4px; }
  #outro-sub { position:absolute; top:46%; left:0; right:0; text-align:center; font-size:24px; color:#64748b; }
  #outro-cta { position:absolute; bottom:20%; left:0; right:0; text-align:center; font-size:24px; color:#475569; }
  .outro-opt { display:flex; align-items:center; gap:10px; background:rgba(15,23,42,0.8); border:1px solid rgba(59,130,246,0.3); border-radius:10px; padding:10px 14px; margin-bottom:8px; opacity:0; }
  .opt-label { font-size:22px; font-weight:700; color:#3b82f6; }
  .opt-text { font-size:20px; color:#e0e0e0; }
  #brand-outro { position:absolute; bottom:6%; left:0; right:0; text-align:center; z-index:50; opacity:0; }
  #brand-outro-text { font-size:22px; color:#475569; letter-spacing:7px; }
  #brand-outro-text span { color:#3b82f6; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="__TOTAL_DUR__">

  <!-- 品牌片头 -->
  <div id="brand-intro">
    <div id="brand-logo-wrap">
      <div id="brand-logo-ring"></div>
      <div id="brand-logo-dot"></div>
    </div>
    <div id="brand-name">\u56fe\u9489</div>
    <div id="brand-slogan">\u5730\u56fe\u70ed\u70b9 \u00b7 \u7528\u5730\u56fe\u8bb2\u65b0\u95fb</div>
  </div>

  <!-- scene1: 开场 -->
  <div id="scene1" class="scene">
    <div class="stage">
      <img src="__MAP_IMAGE__" alt="" style="position:absolute;width:120%;height:120%;top:-10%;left:-10%;object-fit:cover;opacity:0.1;filter:blur(8px)" id="bg-img-1">
      <h1 id="intro-title">__TITLE__</h1>
      <p id="intro-sub">__SUBTITLE__</p>
      <div id="intro-divider"></div>
      <div id="intro-badge">__BADGE_TEXT__</div>
      <p id="intro-unit">__BADGE_UNIT__</p>
    </div>
  </div>

  <!-- scene2: 主画面 -->
  <div id="scene2" class="scene">
    <img src="__MAP_IMAGE__" alt="" id="map-bg" style="position:absolute;width:110%;height:100%;object-fit:cover;top:0">
    <div class="map-overlay"></div>
    
    <!-- 对比双栏 -->
    <div class="compare-wrap" id="compare-wrap">
      <div class="compare-col south">
        <div class="cc-label">__SOUTH_LABEL__</div>
        <div class="cc-val">__SOUTH_VAL__</div>
        <div class="cc-sub">__SOUTH_RANK__</div>
      </div>
      <div class="compare-col north">
        <div class="cc-label">__NORTH_LABEL__</div>
        <div class="cc-val">__NORTH_VAL__</div>
        <div class="cc-sub">__NORTH_RANK__</div>
      </div>
    </div>
    
    <!-- 异常值高亮 -->
    __ANOMALY_HTML__
    
    <!-- 圆环进度 -->
    <div class="ring-wrap">
      <svg id="ring-progress" viewBox="0 0 140 140">
        <defs>
          <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#f59e0b" />
            <stop offset="100%" stop-color="#ef4444" />
          </linearGradient>
        </defs>
        <circle id="ring-bg" cx="70" cy="70" r="65" />
        <circle id="ring-fill" cx="70" cy="70" r="65" />
        <text id="ring-value" x="70" y="65">0</text>
        <text id="ring-label" x="70" y="95">__RING_LABEL__</text>
      </svg>
    </div>
    
    <!-- 数据面板 -->
    <div class="panel-section">
      <div class="panel-label">\u6d6e\u52a8\u8d8b\u52bf</div>
      <div>
        <span class="big-val hot">__SOUTH_VAL__</span>
        <span class="big-unit">\u5143/kg</span>
      </div>
      <div class="panel-desc">\u6700\u65b0\u6570\u636e \u00b7 \u521b\u8fd1\u4e94\u5e74\u540c\u671f\u65b0\u9ad8</div>
    </div>
    
    <!-- 原因卡片 -->
    <div class="reasons-section">
      <div class="reasons-label">\u4e3a\u4ec0\u4e48\u6da8\uff1f</div>
      __REASON_CARDS__
    </div>
    
    <!-- 榜单列表 -->
    __RANK_LIST_HTML__
    
    <!-- 结尾品牌 -->
    <div id="brand-outro">
      <div id="brand-outro-text"><span>\U0001f4cd</span> \u56fe\u9489 \u00b7 \u5730\u56fe\u70ed\u70b9</div>
    </div>
  </div>

  <!-- scene3: 结尾互动 -->
  <div id="scene3" class="scene">
    <h1 id="outro-title">__OUTRO_QUESTION__</h1>
    <p id="outro-sub">__OUTRO_SUB__</p>
    <div class="outro-options">__OPTIONS_HTML__</div>
    <p id="outro-cta"><span class="cta-icon">\u25b6</span> __CTA_TEXT__</p>
  </div>

</div>

<script>
window.__timelines=window.__timelines||{};var tl=gsap.timeline({paused:true});
__BRAND_ANIMS__
// 开场 2.25s
__INTRO_ANIMS__
// scene2入场 + 地图持续平移
__MAP_ANIMS__
// 对比双栏
__COMPARE_ANIMS__
// 异常值高亮
__ANOMALY_ANIMS__
// 圆环进度
__RING_ANIMS__
// 榜单滚动
__RANK_ANIMS__
// 原因卡片
__REASON_ANIMS__
// 结尾
__OUTRO_ANIMS__
// 选项
__OPTION_ANIMS__
window.__timelines["main"]=tl;tl.play();
</script>
</body>
</html>'''

    # v4.3 JS动画逻辑
    brand_anims = """
// 品牌片头 0-2.2s
tl.fromTo("#brand-logo-ring",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"power2.out"},0);
tl.fromTo("#brand-logo-dot",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"},0.3);
tl.fromTo("#brand-name",{y:-20,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},0.6);
tl.fromTo("#brand-slogan",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},0.8);
tl.to("#brand-intro",{opacity:0,duration:0.25,ease:"power2.in"},2.0);
tl.set("#brand-intro",{visibility:"hidden"},2.25);
"""
    
    intro_anims = """
// 开场 2.25s
tl.fromTo("#intro-title",{scale:0.3,opacity:0,rotation:-10,x:-150},{scale:1,opacity:1,rotation:0,x:0,duration:0.5,ease:"power3.out"},2.25);
tl.fromTo("#intro-sub",{x:200,opacity:0},{x:0,opacity:1,duration:0.4,ease:"power2.out"},2.6);
tl.fromTo("#intro-badge",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},3.0);
tl.fromTo("#intro-unit",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},3.5);
tl.to("#scene1",{opacity:0,duration:0.25,ease:"power2.in"},4.5);
tl.set("#scene1",{visibility:"hidden"},4.75);
"""
    
    # v4.3核心：地图持续平移
    map_anims = """
// scene2入场
tl.fromTo("#scene2",{y:150,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},4.75);
// v4.3: 地图持续缓慢平移（全片不静止）
gsap.to("#map-bg",{x:"-5%",duration:8,ease:"none",yoyo:true,repeat:-1});
gsap.to("#bg-img-1",{scale:1.03,duration:6,ease:"none",yoyo:true,repeat:-1});
"""
    
    compare_anims = """
// 对比双栏 7s
tl.fromTo("#compare-wrap",{y:40,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},7.0);
tl.fromTo("#compare-wrap .compare-col:nth-child(1)",{x:-30,opacity:0},{x:0,opacity:1,duration:0.3,ease:"power2.out"},7.3);
tl.fromTo("#compare-wrap .compare-col:nth-child(2)",{x:30,opacity:0},{x:0,opacity:1,duration:0.3,ease:"power2.out"},7.6);
"""
    
    anomaly_anims = """
// 异常值高亮
tl.to("#ab-hl",{opacity:1,scale:1.05,duration:0.3,ease:"power2.out"},12.0);
tl.to("#ab-note",{opacity:1,y:0,duration:0.3,ease:"power2.out"},12.4);
tl.to("#ab-hl",{scale:1,duration:0.2,ease:"power2.out"},12.7);
"""
    
    ring_anims = """
// 圆环进度计数动画
tl.fromTo("#ring-fill",{strokeDashoffset:408},{strokeDashoffset:0,duration:1.2,ease:"power2.out"},5.0);
gsap.to("#ring-value",{innerHTML:"__RING_VALUE__",duration:1.2, snap:{innerHTML:1}, ease:"power1.out"},5.0);
tl.fromTo("#ring-value",{scale:0.8,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"power2.out"},5.0);
"""
    
    outro_anims = """
// 结尾
tl.fromTo("#scene3",{yPercent:80,opacity:0},{yPercent:0,opacity:1,duration:0.5,ease:"power3.out"},%.1f);
tl.fromTo("#outro-title",{y:-40,scale:0.5,opacity:0},{y:0,scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},%.1f);
tl.fromTo("#outro-sub",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},%.1f);
tl.fromTo("#outro-cta",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},%.1f);
tl.fromTo("#brand-outro",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},%.1f);
tl.set("#scene3",{visibility:"hidden"},%.1f);
""" % (outro_start - 2.0, outro_start, outro_start + 0.5, outro_start + 1.5, outro_start + 2.5, total_dur - 0.5)

    # 构建替换字典
    replacements = {
        '__TITLE__': title,
        '__MAP_IMAGE__': map_image,
        '__SUBTITLE__': subtitle,
        '__BADGE_TEXT__': badge_text,
        '__BADGE_UNIT__': badge_unit,
        '__RING_LABEL__': ring_label,
        '__SOUTH_LABEL__': south_label,
        '__SOUTH_VAL__': str(south_val),
        '__SOUTH_RANK__': south_rank,
        '__NORTH_LABEL__': north_label,
        '__NORTH_VAL__': str(north_val),
        '__NORTH_RANK__': north_rank,
        '__REASON_CARDS__': reason_cards,
        '__OUTRO_QUESTION__': outro_question,
        '__OUTRO_SUB__': outro_sub,
        '__OPTIONS_HTML__': options_html,
        '__CTA_TEXT__': cta_text,
        '__RING_VALUE__': str(ring_value),
        '__REASON_ANIMS__': reason_anims,
        '__OUTRO_START__': str(outro_start),
        '__OPTION_ANIMS__': option_anims,
        '__TOTAL_DUR__': str(total_dur),
        '__V43_CSS__': css_v43,
        '__BRAND_ANIMS__': brand_anims,
        '__INTRO_ANIMS__': intro_anims,
        '__MAP_ANIMS__': map_anims,
        '__COMPARE_ANIMS__': compare_anims,
        '__ANOMALY_ANIMS__': anomaly_anims,
        '__RING_ANIMS__': ring_anims,
        '__RANK_ANIMS__': rank_anims,
        '__OUTRO_ANIMS__': outro_anims,
    }

    # 构建异常值高亮HTML
    if anomaly_highlight:
        anomaly_html = '''<div id="ab-hl"><div class="ab-hl-text">%s: %s</div></div><div id="ab-note">%s</div>''' % (
            anomaly_highlight.get('name', '异常'),
            anomaly_highlight.get('value', ''),
            anomaly_highlight.get('note', '')
        )
        replacements['__ANOMALY_HTML__'] = anomaly_html
    else:
        replacements['__ANOMALY_HTML__'] = ''
    
    # 构建榜单列表HTML
    rank_list_html = '<div class="rank-list-wrap" id="rank-list-wrap"><div class="rank-list-header"><div class="col-num" style="width:36px">#</div><div class="col-name" style="flex:1">\u57ce\u5e02</div><div class="col-val" style="flex:1;text-align:right">\u6570\u636e</div><div class="col-per" style="width:100px;text-align:right">\u4eba\u5747</div></div>'
    for idx, city in enumerate(cities):
        is_anomaly = city.get('is_anomaly', False) or (idx == anomaly_idx and anomaly_highlight)
        ac = ' anomaly-row' if is_anomaly else ''
        hc = ' highlight-row' if idx < 3 else ''
        rank_list_html += '<div class="rank-row%s%s" id="rank-%d"><div class="rank-num">%d</div><div class="rank-name">%s</div><div class="rank-value">%s</div><div class="rank-per">%s</div></div>\n' % (
            ac, hc, idx + 1, idx + 1,
            city.get('name', ''),
            city.get('value', ''),
            city.get('per_capita', '')
        )
    rank_list_html += '</div>'
    replacements['__RANK_LIST_HTML__'] = rank_list_html

    for k, v in replacements.items():
        html = html.replace(k, v)

    return html


def save_html(html, output_path):
    """保存HTML到指定路径"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("[OK] HTML saved: %s" % output_path)
    print("[INFO] Size: %d bytes, %d lines" % (len(html), len(html.splitlines())))
    return output_path


def render_video(output_dir, output_name, quality='draft'):
    """调用HyperFrames渲染视频"""
    print("[OK] Render start: %s (quality=%s)" % (output_name, quality))
    cmd = ['npx', 'hyperframes', 'render', '--quality', quality, '--output', output_name]
    result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=False, timeout=600)
    print("[OK] Render done: %s" % output_name)
    return output_name


def main():
    parser = argparse.ArgumentParser(description='HyperFrames 省份排名模板 v4.3 — 全时段动画版')
    parser.add_argument('--config', help='JSON配置文件路径')
    parser.add_argument('--demo', action='store_true', help='使用演示数据')
    parser.add_argument('--render', action='store_true', help='生成后渲染')
    parser.add_argument('--quality', default='draft', choices=['draft', 'standard', 'high'])
    args = parser.parse_args()

    if args.demo:
        config = {
            'topic': '公积金缴存20强',
            'title': '公积金缴存20强',
            'subtitle': '2025年全国城市排名公布',
            'badge_text': '北京3340亿',
            'badge_unit': '全国第一',
            'map_image': 'assets/maps/egg_price_map.png',
            'ring_value': 15.5,
            'ring_label': '覆盖率',
            'south_label': '广州',
            'north_label': '深圳',
            'south_val': '1376亿',
            'north_val': '1340亿',
            'south_rank': '人数少200万 总额反超',
            'north_rank': '人均1.78万 20强最低',
            'anomaly_highlight': {
                'name': '深圳',
                'value': '1.78万',
                'note': '深圳GDP第4但人均最低'
            },
            'reasons': [
                {'num': '①', 'title': '经济强度', 'desc': '一线城市社保基数高，缴存额自然领先', 'bar': True, 'hot': True},
                {'num': '②', 'title': '政策力度', 'desc': '各地提高缴存比例上限，激励企业参保', 'bar': False},
                {'num': '③', 'title': '人口结构', 'desc': '年轻城市缴存率更高，老龄化城市缴存率低', 'bar': True, 'empty': True}
            ],
            'ranking_data': [
                {'name': '北京', 'value': '3340亿', 'per_capita': '3.5万', 'is_anomaly': False},
                {'name': '上海', 'value': '2660亿', 'per_capita': '2.8万', 'is_anomaly': False},
                {'name': '广州', 'value': '1376亿', 'per_capita': '2.6万', 'is_anomaly': False},
                {'name': '深圳', 'value': '1340亿', 'per_capita': '1.78万', 'is_anomaly': True},
                {'name': '杭州', 'value': '980亿', 'per_capita': '2.4万', 'is_anomaly': False},
                {'name': '宁波', 'value': '820亿', 'per_capita': '2.2万', 'is_anomaly': False},
                {'name': '苏州', 'value': '780亿', 'per_capita': '2.0万', 'is_anomaly': False},
                {'name': '南京', 'value': '760亿', 'per_capita': '2.1万', 'is_anomaly': False}
            ],
            'outro_question': '你的城市公积金有多少？',
            'outro_sub': '评论区说说你的城市排第几',
            'options': ['3万以上', '2-3万', '2万以下'],
            'cta_text': '点赞关注，每天看数据'
        }
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    elif args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    else:
        print("用法: python hyperframes_ranking_v43.py --config config.json 或 --demo")
        return

    html = generate_html(config)
    save_html(html, output_path)

    if args.render:
        render_video(TEMPLATE_DIR, 'ranking_v43.mp4', args.quality)


if __name__ == '__main__':
    main()
