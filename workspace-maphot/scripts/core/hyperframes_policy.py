# -*- coding: utf-8 -*-
"""
HyperFrames 政策影响模板 — 热力图脉冲版

适用题材：政策影响分析（公积金新规、税收政策、限购政策等）
表现手法：热力图展示影响范围 + 数据对比面板 + 分级色彩

用法：
  python hyperframes_policy.py --demo
  python hyperframes_policy.py --config policy_config.json
"""

import os
import sys
import json
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'my-video')


def generate_html(config, audio_duration=None):
    """生成政策影响HTML"""
    title = config.get('title', '政策影响分析')
    subtitle = config.get('subtitle', '')
    map_image = config.get('map_image', 'egg_price_map.png')
    badge_text = config.get('badge_text', '')
    badge_unit = config.get('badge_unit', '')
    
    policy_name = config.get('policy_name', '新规')
    impact_areas = config.get('impact_areas', [])
    key_stats = config.get('key_stats', [
        {'label': '影响人数', 'value': '5000万', 'color': '#ef4444'},
        {'label': '涉及城市', 'value': '50+', 'color': '#f59e0b'},
        {'label': '生效时间', 'value': '2025.01', 'color': '#3b82f6'},
    ])
    level_desc = config.get('level_desc', [
        {'level': '高影响', 'color': '#ef4444', 'desc': '直接受影响'},
        {'level': '中影响', 'color': '#f59e0b', 'desc': '间接受影响'},
        {'level': '低影响', 'color': '#3b82f6', 'desc': '潜在影响'},
    ])
    outro_question = config.get('outro_question', '这个政策对你有影响吗？')
    outro_sub = config.get('outro_sub', '评论区说说你的情况')
    cta_text = config.get('cta_text', '点赞关注，每天看数据')
    
    # 构建热力图点位HTML
    heatmap_points = ""
    for i, area in enumerate(impact_areas):
        x = area.get('x', 50)
        y = area.get('y', 50)
        color = area.get('color', '#ef4444')
        name = area.get('name', '区域')
        value = area.get('value', '')
        pulse_delay = i * 0.2
        heatmap_points += '<div class="heatmap-point" id="point-%d" style="left:%d%%;top:%d%%">' % (i, x, y)
        heatmap_points += '<div class="heat-circle" style="background:%s;animation-delay:%ds"></div>' % (color, pulse_delay)
        heatmap_points += '<div class="heat-label">%s%s</div>' % (name, '|'+value if value else '')
        heatmap_points += '</div>\n'
    
    # 构建关键数据卡片
    stats_cards = ""
    for stat in key_stats:
        stats_cards += '<div class="stat-card" id="stat-%s">' % stat['label']
        stats_cards += '<div class="stat-label">%s</div>' % stat['label']
        stats_cards += '<div class="stat-value" style="color:%s">%s</div>' % (stat['color'], stat['value'])
        stats_cards += '</div>\n'
    
    # 构建分级说明
    level_items = ""
    for ld in level_desc:
        level_items += '<div class="level-item" id="level-%s">' % ld['level']
        level_items += '<div class="level-dot" style="background:%s"></div>' % ld['color']
        level_items += '<div class="level-text">'
        level_items += '<span class="level-name">%s</span>' % ld['level']
        level_items += '<span class="level-desc">%s</span>' % ld['desc']
        level_items += '</div></div>\n'
    
    # CSS样式
    css = '''
body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0a0f1a;color:#e0e0e0;font-family:"PingFang SC","Microsoft YaHei",sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:linear-gradient(180deg,#0a0f1a 0%,#1a2744 50%,#0d1520 100%)}
.scene{position:absolute;top:0;left:0;width:1080px;height:1920px;overflow:hidden}

/* 品牌片头 */
#brand-intro{position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:50;background:#0a0f1a}
#brand-logo-wrap{position:relative;width:100px;height:100px}
#brand-logo-ring{position:absolute;inset:0;border:3px solid rgba(59,130,246,0.4);border-radius:50%;opacity:0}
#brand-logo-dot{position:absolute;top:50%%;left:50%%;width:14px;height:14px;background:#3b82f6;border-radius:50%%;transform:translate(-50%%,-50%%);opacity:0;box-shadow:0 0 25px rgba(59,130,246,0.8)}
#brand-name{font-size:42px;color:#fff;letter-spacing:10px;font-weight:300;margin-top:24px;opacity:0}
#brand-slogan{font-size:20px;color:#64748b;letter-spacing:5px;margin-top:8px;opacity:0}

/* 开场 */
#intro-title{position:absolute;top:25%%;left:0;right:0;text-align:center;font-size:96px;font-weight:700;color:#fff;letter-spacing:4px;text-shadow:0 0 60px rgba(239,68,68,0.6)}
#intro-sub{position:absolute;top:38%%;left:0;right:0;text-align:center;font-size:32px;color:#f59e0b;letter-spacing:4px}
#intro-badge{position:absolute;top:48%%;left:0;right:0;text-align:center;font-size:64px;font-weight:700;color:#ef4444}
#intro-unit{position:absolute;top:56%%;left:0;right:0;text-align:center;font-size:22px;color:#64748b}

/* 主画面 */
#scene2{z-index:2}
.map-wrap{position:absolute;top:0;left:0;width:100%%;height:75%%;overflow:hidden}
.map-wrap img{width:100%%;height:100%%;object-fit:cover;opacity:0.6}
.map-overlay{position:absolute;bottom:0;left:0;right:0;height:50%%;background:linear-gradient(0deg,rgba(10,15,26,0.98) 0%%,transparent 100%%)}

/* 热力图点位 */
.heatmap-container{position:absolute;top:5%%;left:5%%;right:5%%;bottom:35%%;overflow:hidden}
.heatmap-point{position:absolute;transform:translate(-50%%,-50%%);cursor:pointer}
.heat-circle{width:60px;height:60px;border-radius:50%%;opacity:0.7;animation:pulse 2s ease-in-out infinite}
.heat-label{position:absolute;top:70px;left:50%%;transform:translateX(-50%%);font-size:16px;color:#fff;white-space:nowrap;text-shadow:0 0 10px rgba(0,0,0,0.8)}
@keyframes pulse{0%%,100%%{transform:scale(1);opacity:0.7}50%%{transform:scale(1.3);opacity:0.4}}

/* 数据面板 */
.data-panel{position:absolute;bottom:5%%;left:4%%;right:4%%;background:rgba(15,23,42,0.95);border-radius:16px;padding:16px 20px;border:1px solid rgba(59,130,246,0.3)}
.panel-title{font-size:18px;color:#64748b;letter-spacing:3px;margin-bottom:12px}
.stats-grid{display:flex;gap:16px;justify-content:space-around}
.stat-card{text-align:center;padding:12px}
.stat-label{font-size:14px;color:#94a3b8;margin-bottom:4px}
.stat-value{font-size:36px;font-weight:700}

/* 分级说明 */
.level-panel{position:absolute;top:78%%;left:4%%;right:4%%;background:rgba(15,23,42,0.9);border-radius:12px;padding:12px 16px}
.level-items{display:flex;gap:20px;justify-content:space-around}
.level-item{display:flex;align-items:center;gap:8px}
.level-dot{width:12px;height:12px;border-radius:50%%}
.level-text{display:flex;flex-direction:column}
.level-name{font-size:16px;color:#fff;font-weight:600}
.level-desc{font-size:12px;color:#94a3b8}

/* 结尾 */
#scene3{z-index:3}
#outro-title{position:absolute;top:35%%;left:0;right:0;text-align:center;font-size:56px;font-weight:700;color:#fff;letter-spacing:3px}
#outro-sub{position:absolute;top:46%%;left:0;right:0;text-align:center;font-size:24px;color:#64748b}
#outro-cta{position:absolute;bottom:20%%;left:0;right:0;text-align:center;font-size:24px;color:#475569}
#brand-outro{position:absolute;bottom:6%%;left:0;right:0;text-align:center;z-index:50;opacity:0}
#brand-outro-text{font-size:22px;color:#475569;letter-spacing:7px}#brand-outro-text span{color:#3b82f6}
'''
    
    # JS动画
    js = '''
window.__timelines=window.__timelines||{};var tl=gsap.timeline({paused:true});

// 品牌片头 0-2.2s
tl.fromTo("#brand-logo-ring",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"power2.out"},0);
tl.fromTo("#brand-logo-dot",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"},0.3);
tl.fromTo("#brand-name",{y:-20,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},0.6);
tl.fromTo("#brand-slogan",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},0.8);
tl.to("#brand-intro",{opacity:0,duration:0.25,ease:"power2.in"},2.0);
tl.set("#brand-intro",{visibility:"hidden"},2.25);

// 开场 2.25s
tl.fromTo("#intro-title",{scale:0.3,opacity:0,rotation:-10,x:-150},{scale:1,opacity:1,rotation:0,x:0,duration:0.5,ease:"power3.out"},2.25);
tl.fromTo("#intro-sub",{x:200,opacity:0},{x:0,opacity:1,duration:0.4,ease:"power2.out"},2.6);
tl.fromTo("#intro-badge",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},3.0);
tl.fromTo("#intro-unit",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},3.5);
tl.to("#scene1",{opacity:0,duration:0.25,ease:"power2.in"},4.5);
tl.set("#scene1",{visibility:"hidden"},4.75);

// 主画面入场 4.75s
tl.fromTo("#scene2",{y:150,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},4.75);

// 热力图点位逐个弹出 6s开始
tl.fromTo("#heatmap-container",{opacity:0},{opacity:1,duration:0.5,ease:"power2.out"},6.0);
var pointCount = document.querySelectorAll('.heatmap-point').length;
for(var i=0;i<pointCount;i++){
  tl.fromTo("#point-"+i,{scale:0,opacity:0},{scale:1,opacity:1,duration:0.4,ease:"back.out(1.5)"},6.5+i*0.3);
}

// 数据面板 12s
tl.fromTo("#data-panel",{y:50,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},12.0);

// 分级说明 15s
tl.fromTo("#level-panel",{y:30,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},15.0);

// 地图持续缓慢平移
gsap.to(".map-wrap img",{x:"-3%%",duration:8,ease:"none",yoyo:true,repeat:5});

// 结尾 42s
tl.fromTo("#scene3",{yPercent:80,opacity:0},{yPercent:0,opacity:1,duration:0.5,ease:"power3.out"},42.0);
tl.fromTo("#outro-title",{y:-40,scale:0.5,opacity:0},{y:0,scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},42.5);
tl.fromTo("#outro-sub",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},43.2);
tl.fromTo("#outro-cta",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},44.0);
tl.fromTo("#brand-outro",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},45.5);
tl.set("#scene3",{visibility:"hidden"},54.5);

window.__timelines["main"]=tl;tl.play();
'''
    
    # HTML结构
    html_parts = []
    html_parts.append('<!doctype html>')
    html_parts.append('<html lang="zh-CN">')
    html_parts.append('<head>')
    html_parts.append('<meta charset="UTF-8">')
    html_parts.append('<meta name="viewport" content="width=1080,height=1920">')
    html_parts.append('<title>%s</title>' % title)
    html_parts.append('<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>')
    html_parts.append('<style>')
    html_parts.append(css)
    html_parts.append('</style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append('<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="55">')
    
    # 品牌片头
    html_parts.append('<div id="brand-intro">')
    html_parts.append('<div id="brand-logo-wrap"><div id="brand-logo-ring"></div><div id="brand-logo-dot"></div></div>')
    html_parts.append('<div id="brand-name">图钉</div>')
    html_parts.append('<div id="brand-slogan">地图热点 · 用地图讲新闻</div>')
    html_parts.append('</div>')
    
    # 开场
    html_parts.append('<div id="scene1" class="scene">')
    html_parts.append('<h1 id="intro-title">%s</h1>' % title)
    html_parts.append('<p id="intro-sub">%s</p>' % subtitle)
    html_parts.append('<div id="intro-badge">%s</div>' % badge_text)
    html_parts.append('<p id="intro-unit">%s</p>' % badge_unit)
    html_parts.append('</div>')
    
    # 主画面
    html_parts.append('<div id="scene2" class="scene">')
    html_parts.append('<div class="map-wrap"><img src="assets/maps/%s" alt=""><div class="map-overlay"></div></div>' % map_image)
    html_parts.append('<div class="heatmap-container" id="heatmap-container">%s</div>' % heatmap_points)
    html_parts.append('<div class="data-panel" id="data-panel">')
    html_parts.append('<div class="panel-title">%s影响范围</div>' % policy_name)
    html_parts.append('<div class="stats-grid">%s</div>' % stats_cards)
    html_parts.append('</div>')
    html_parts.append('<div class="level-panel" id="level-panel">')
    html_parts.append('<div class="level-items">%s</div>' % level_items)
    html_parts.append('</div>')
    html_parts.append('<div id="brand-outro"><div id="brand-outro-text"><span>📍</span> 图钉 · 地图热点</div></div>')
    html_parts.append('</div>')
    
    # 结尾
    html_parts.append('<div id="scene3" class="scene">')
    html_parts.append('<h1 id="outro-title">%s</h1>' % outro_question)
    html_parts.append('<p id="outro-sub">%s</p>' % outro_sub)
    html_parts.append('<p id="outro-cta"><span class="cta-icon">▶</span> %s</p>' % cta_text)
    html_parts.append('</div>')
    
    html_parts.append('</div>')  # close root
    html_parts.append('<script>')
    html_parts.append(js)
    html_parts.append('</script>')
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    return '\n'.join(html_parts)


def save_html(html, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('[OK] HTML saved: %s' % output_path)
    print('[INFO] Size: %d bytes, %d lines' % (len(html), len(html.splitlines())))
    return output_path


def render_video(output_dir, output_name, quality='draft'):
    print('[OK] Render start: %s (quality=%s)' % (output_name, quality))
    cmd = ['npx', 'hyperframes', 'render', '--quality', quality, '--output', output_name]
    result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=False, timeout=600)
    print('[OK] Render done: %s' % output_name)
    return output_name


def main():
    parser = argparse.ArgumentParser(description='HyperFrames 政策影响模板')
    parser.add_argument('--config', help='JSON配置文件路径')
    parser.add_argument('--demo', action='store_true', help='使用演示数据')
    parser.add_argument('--render', action='store_true', help='生成后渲染')
    parser.add_argument('--quality', default='draft', choices=['draft', 'standard', 'high'])
    args = parser.parse_args()

    if args.demo:
        config = {
            'title': '公积金新规影响分析',
            'subtitle': '2025年最新政策落地',
            'badge_text': '5000万人受影响',
            'badge_unit': '全国范围',
            'map_image': 'egg_price_map.png',
            'policy_name': '公积金缴存比例调整',
            'impact_areas': [
                {'name': '北京', 'x': 60, 'y': 30, 'radius': 50, 'color': '#ef4444', 'value': '高'},
                {'name': '上海', 'x': 65, 'y': 45, 'radius': 45, 'color': '#ef4444', 'value': '高'},
                {'name': '广州', 'x': 58, 'y': 65, 'radius': 40, 'color': '#f59e0b', 'value': '中'},
                {'name': '深圳', 'x': 60, 'y': 68, 'radius': 35, 'color': '#f59e0b', 'value': '中'},
                {'name': '杭州', 'x': 63, 'y': 50, 'radius': 30, 'color': '#3b82f6', 'value': '低'},
            ],
            'key_stats': [
                {'label': '影响人数', 'value': '5000万', 'color': '#ef4444'},
                {'label': '涉及城市', 'value': '50+', 'color': '#f59e0b'},
                {'label': '生效时间', 'value': '2025.01', 'color': '#3b82f6'},
            ],
            'level_desc': [
                {'level': '高影响', 'color': '#ef4444', 'desc': '直接受影响'},
                {'level': '中影响', 'color': '#f59e0b', 'desc': '间接受影响'},
                {'level': '低影响', 'color': '#3b82f6', 'desc': '潜在影响'},
            ],
            'outro_question': '这个政策对你有影响吗？',
            'outro_sub': '评论区说说你的情况',
            'cta_text': '点赞关注，每天看数据',
        }
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    elif args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    else:
        print("用法: python hyperframes_policy.py --config config.json 或 --demo")
        return

    html = generate_html(config)
    save_html(html, output_path)

    if args.render:
        render_video(TEMPLATE_DIR, 'policy_demo.mp4', args.quality)


if __name__ == '__main__':
    main()
