# -*- coding: utf-8 -*-
"""
HyperFrames 人口流动模板 — 流向动画版

适用题材：人口流动迁徙、人才流入流出、打工潮等
表现手法：贝塞尔曲线流动动画 + 箭头指示方向 + 规模可视化

用法：
  python hyperframes_flow.py --demo
  python hyperframes_flow.py --config flow_config.json
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
    """生成人口流动HTML"""
    title = config.get('title', '人口流动分析')
    subtitle = config.get('subtitle', '')
    map_image = config.get('map_image', 'egg_price_map.png')
    badge_text = config.get('badge_text', '')
    badge_unit = config.get('badge_unit', '')
    
    flows = config.get('flows', [])
    total_flow = config.get('total_flow', '')
    net_inflow = config.get('net_inflow', '')
    top_source = config.get('top_source', '')
    
    outro_question = config.get('outro_question', '你的家乡人口流出还是流入？')
    outro_sub = config.get('outro_sub', '评论区说说你的城市')
    cta_text = config.get('cta_text', '点赞关注，每天看数据')
    
    # 构建流向SVG路径
    flow_paths = ""
    for i, flow in enumerate(flows):
        x1 = flow.get('x1', 30)
        y1 = flow.get('y1', 40)
        x2 = flow.get('x2', 70)
        y2 = flow.get('y2', 60)
        value = flow.get('value', '100万')
        color = flow.get('color', '#3b82f6')
        width = max(2, min(8, int(value.replace('万', '').replace('亿', '')) / 10))
        
        # 贝塞尔曲线控制点
        cx1 = (x1 + x2) / 2
        cy1 = min(y1, y2) - 10
        
        flow_paths += '<path id="flow-path-%d" class="flow-path" d="M%d,%d Q%d,%d %d,%d" ' % (i, x1, y1, cx1, cy1, x2, y2)
        flow_paths += 'stroke="%s" stroke-width="%d" fill="none" stroke-dasharray="8,4" opacity="0"/>\n' % (color, width)
        flow_paths += '<circle id="flow-start-%d" class="flow-node" cx="%d" cy="%d" r="6" fill="%s" opacity="0"/>\n' % (i, x1, y1, color)
        flow_paths += '<circle id="flow-end-%d" class="flow-node" cx="%d" cy="%d" r="6" fill="%s" opacity="0"/>\n' % (i, x2, y2, color)
        flow_paths += '<text id="flow-label-%d" class="flow-label" x="%d" y="%d" text-anchor="middle" ' % (i, cx1, cy1-5)
        flow_paths += 'fill="#fff" font-size="14" opacity="0">%s</text>\n' % value
    
    # CSS样式
    css = '''
body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0a0f1a;color:#e0e0e0;font-family:"PingFang SC","Microsoft YaHei",sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:linear-gradient(180deg,#0a0f1a 0%%,#1a2744 50%%,#0d1520 100%%)}
.scene{position:absolute;top:0;left:0;width:1080px;height:1920px;overflow:hidden}

/* 品牌片头 */
#brand-intro{position:absolute;top:0;left:0;width:100%%;height:100%%;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:50;background:#0a0f1a}
#brand-logo-wrap{position:relative;width:100px;height:100px}
#brand-logo-ring{position:absolute;inset:0;border:3px solid rgba(59,130,246,0.4);border-radius:50%%;opacity:0}
#brand-logo-dot{position:absolute;top:50%%;left:50%%;width:14px;height:14px;background:#3b82f6;border-radius:50%%;transform:translate(-50%%,-50%%);opacity:0;box-shadow:0 0 25px rgba(59,130,246,0.8)}
#brand-name{font-size:42px;color:#fff;letter-spacing:10px;font-weight:300;margin-top:24px;opacity:0}
#brand-slogan{font-size:20px;color:#64748b;letter-spacing:5px;margin-top:8px;opacity:0}

/* 开场 */
#intro-title{position:absolute;top:25%%;left:0;right:0;text-align:center;font-size:96px;font-weight:700;color:#fff;letter-spacing:4px}
#intro-sub{position:absolute;top:38%%;left:0;right:0;text-align:center;font-size:32px;color:#f59e0b;letter-spacing:4px}
#intro-badge{position:absolute;top:48%%;left:0;right:0;text-align:center;font-size:64px;font-weight:700;color:#3b82f6}
#intro-unit{position:absolute;top:56%%;left:0;right:0;text-align:center;font-size:22px;color:#64748b}

/* 主画面 */
#scene2{z-index:2}
.map-wrap{position:absolute;top:0;left:0;width:100%%;height:75%%;overflow:hidden}
.map-wrap img{width:100%%;height:100%%;object-fit:cover;opacity:0.5}
.map-overlay{position:absolute;bottom:0;left:0;right:0;height:50%%;background:linear-gradient(0deg,rgba(10,15,26,0.98) 0%%,transparent 100%%)}

/* 流向SVG */
.flow-svg{position:absolute;top:5%%;left:5%%;right:5%%;bottom:30%%;width:90%%;height:60%%}
.flow-path{stroke-linecap:round;filter:drop-shadow(0 0 6px currentColor)}
.flow-node{r:8;filter:drop-shadow(0 0 8px currentColor)}
.flow-label{font-weight:600;paint-order:stroke;stroke:rgba(0,0,0,0.8);stroke-width:3px}

/* 统计面板 */
.stats-panel{position:absolute;bottom:5%%;left:4%%;right:4%%;background:rgba(15,23,42,0.95);border-radius:16px;padding:16px 20px;border:1px solid rgba(59,130,246,0.3)}
.stats-grid{display:flex;gap:20px;justify-content:space-around}
.stat-item{text-align:center}
.stat-value{font-size:42px;font-weight:700;color:#3b82f6}
.stat-label{font-size:14px;color:#94a3b8;margin-top:4px}

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

// 流向线条动画 6s开始
var flowPaths = document.querySelectorAll('.flow-path');
var flowNodes = document.querySelectorAll('.flow-node');
var flowLabels = document.querySelectorAll('.flow-label');

flowPaths.forEach(function(path, i) {
  var length = path.getTotalLength();
  path.style.strokeDasharray = length;
  path.style.strokeDashoffset = length;
  
  tl.fromTo(path,{strokeDashoffset:length},{strokeDashoffset:0,duration:1.5,ease:"power2.inOut"},6+i*0.5);
  tl.to(path,{opacity:0.8,duration:0.2},6+i*0.5);
});

// 节点弹出
flowNodes.forEach(function(node, i) {
  tl.fromTo(node,{scale:0,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"},7+i*0.5);
});

// 标签显示
flowLabels.forEach(function(label, i) {
  tl.fromTo(label,{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},8+i*0.5);
});

// 统计面板 12s
tl.fromTo("#stats-panel",{y:50,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},12.0);

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
    html_parts.append('<svg class="flow-svg" viewBox="0 0 100 100" preserveAspectRatio="none">%s</svg>' % flow_paths)
    html_parts.append('<div class="stats-panel" id="stats-panel">')
    html_parts.append('<div class="stats-grid">')
    html_parts.append('<div class="stat-item"><div class="stat-value" id="stat-total">%s</div><div class="stat-label">总流动量</div></div>' % total_flow)
    html_parts.append('<div class="stat-item"><div class="stat-value" id="stat-net" style="color:#ef4444">%s</div><div class="stat-label">净流入</div></div>' % net_inflow)
    html_parts.append('<div class="stat-item"><div class="stat-value" id="stat-source" style="color:#f59e0b">%s</div><div class="stat-label">主要来源</div></div>' % top_source)
    html_parts.append('</div></div>')
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
    parser = argparse.ArgumentParser(description='HyperFrames 人口流动模板')
    parser.add_argument('--config', help='JSON配置文件路径')
    parser.add_argument('--demo', action='store_true', help='使用演示数据')
    parser.add_argument('--render', action='store_true', help='生成后渲染')
    parser.add_argument('--quality', default='draft', choices=['draft', 'standard', 'high'])
    args = parser.parse_args()

    if args.demo:
        config = {
            'title': '广东人口净流入分析',
            'subtitle': '为什么年轻人更愿意去广东？',
            'badge_text': '103万人',
            'badge_unit': '年出生人口，连续6年第一',
            'map_image': 'egg_price_map.png',
            'flows': [
                {'x1': 30, 'y1': 30, 'x2': 65, 'y2': 70, 'value': '50万', 'color': '#ef4444'},
                {'x1': 25, 'y1': 45, 'x2': 60, 'y2': 65, 'value': '30万', 'color': '#f59e0b'},
                {'x1': 40, 'y1': 25, 'x2': 70, 'y2': 60, 'value': '20万', 'color': '#3b82f6'},
                {'x1': 50, 'y1': 20, 'x2': 65, 'y2': 55, 'value': '15万', 'color': '#8b5cf6'},
            ],
            'total_flow': '120万',
            'net_inflow': '+85万',
            'top_source': '湖南',
            'outro_question': '你的家乡人口流出还是流入？',
            'outro_sub': '评论区说说你的城市',
            'cta_text': '点赞关注，每天看数据',
        }
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    elif args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    else:
        print("用法: python hyperframes_flow.py --config config.json 或 --demo")
        return

    html = generate_html(config)
    save_html(html, output_path)

    if args.render:
        render_video(TEMPLATE_DIR, 'flow_demo.mp4', args.quality)


if __name__ == '__main__':
    main()
