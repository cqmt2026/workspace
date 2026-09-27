# -*- coding: utf-8 -*-
"""
HyperFrames 制度起源模板 — 时间轴推进版

适用题材：制度起源、政策背景、历史沿革（计划单列市、经济特区、自贸区等）
表现手法：时间轴推进 + 历史节点标注 + 地图变迁动画

用法：
  python hyperframes_institution.py --demo
  python hyperframes_institution.py --config institution_config.json
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
    """生成制度起源HTML"""
    title = config.get('title', '制度起源分析')
    subtitle = config.get('subtitle', '')
    map_image = config.get('map_image', 'egg_price_map.png')
    badge_text = config.get('badge_text', '')
    badge_unit = config.get('badge_unit', '')
    
    # 时间轴数据
    timeline = config.get('timeline', [])
    if not timeline:
        timeline = [
            {'year': '1984', 'event': '首批计划单列市设立', 'cities': ['大连', '青岛', '宁波', '厦门', '深圳']},
            {'year': '1988', 'event': '新增计划单列市', 'cities': ['青岛', '宁波']},
            {'year': '1994', 'event': '计划单列市定型', 'cities': ['5个城市']},
        ]
    
    # 构建时间轴HTML
    timeline_items = ""
    for i, item in enumerate(timeline):
        year = item.get('year', '')
        event = item.get('event', '')
        cities = item.get('cities', [])
        cities_str = ', '.join(cities) if cities else ''
        timeline_items += '<div class="timeline-item" id="tl-%d">' % i
        timeline_items += '<div class="timeline-year">%s</div>' % year
        timeline_items += '<div class="timeline-event">%s</div>' % event
        if cities_str:
            timeline_items += '<div class="timeline-cities">%s</div>' % cities_str
        timeline_items += '</div>\n'
    
    # 关键信息卡片
    key_info = config.get('key_info', [
        {'label': '设立时间', 'value': '1984年', 'color': '#3b82f6'},
        {'label': '城市数量', 'value': '5个', 'color': '#f59e0b'},
        {'label': '行政级别', 'value': '副省级', 'color': '#ef4444'},
    ])
    
    info_cards = ""
    for card in key_info:
        info_cards += '<div class="info-card" id="info-%s">' % card['label']
        info_cards += '<div class="info-label">%s</div>' % card['label']
        info_cards += '<div class="info-value" style="color:%s">%s</div>' % (card['color'], card['value'])
        info_cards += '</div>\n'
    
    outro_question = config.get('outro_question', '这些制度对城市发展有什么影响？')
    outro_sub = config.get('outro_sub', '评论区说说你的看法')
    cta_text = config.get('cta_text', '点赞关注，每天看数据')
    
    # CSS样式
    css = '''
body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0a0f1a;color:#e0e0e0;font-family:"PingFang SC","Microsoft YaHei",sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:linear-gradient(180deg,#0a0f1a 0%,#1a2744 50%,#0d1520 100%)}
.scene{position:absolute;top:0;left:0;width:1080px;height:1920px;overflow:hidden}

/* 品牌片头 */
#brand-intro{position:absolute;top:0;left:0;width:100%%;height:100%%;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:50;background:#0a0f1a}
#brand-logo-wrap{position:relative;width:100px;height:100px}
#brand-logo-ring{position:absolute;inset:0;border:3px solid rgba(59,130,246,0.4);border-radius:50%%;opacity:0}
#brand-logo-dot{position:absolute;top:50%%;left:50%%;width:14px;height:14px;background:#3b82f6;border-radius:50%%;transform:translate(-50%%,-50%%);opacity:0;box-shadow:0 0 25px rgba(59,130,246,0.8)}
#brand-name{font-size:42px;color:#fff;letter-spacing:10px;font-weight:300;margin-top:24px;opacity:0}
#brand-slogan{font-size:20px;color:#64748b;letter-spacing:5px;margin-top:8px;opacity:0}

/* 开场 */
#intro-title{position:absolute;top:22%%;left:0;right:0;text-align:center;font-size:96px;font-weight:700;color:#fff;letter-spacing:4px;text-shadow:0 0 60px rgba(245,158,11,0.6)}
#intro-sub{position:absolute;top:35%%;left:0;right:0;text-align:center;font-size:32px;color:#f59e0b;letter-spacing:4px}
#intro-badge{position:absolute;top:45%%;left:0;right:0;text-align:center;font-size:64px;font-weight:700;color:#ef4444}
#intro-unit{position:absolute;top:53%%;left:0;right:0;text-align:center;font-size:22px;color:#64748b}

/* 主画面 */
#scene2{z-index:2}
.map-wrap{position:absolute;top:0;left:0;width:100%%;height:65%%;overflow:hidden}
.map-wrap img{width:100%%;height:100%%;object-fit:cover;opacity:0.5}
.map-overlay{position:absolute;bottom:0;left:0;right:0;height:40%%;background:linear-gradient(0deg,rgba(10,15,26,0.98) 0%%,transparent 100%%)}

/* 时间轴 */
.timeline-container{position:absolute;bottom:5%%;left:4%%;right:4%%;height:30%%;display:flex;align-items:center}
.timeline-track{position:absolute;top:50%%;left:0;right:0;height:4px;background:rgba(59,130,246,0.3);transform:translateY(-50%%)}
.timeline-progress{position:absolute;top:50%%;left:0;height:4px;background:#3b82f6;transform:translateY(-50%%);width:0%%}
.timeline-items{position:relative;display:flex;justify-content:space-around;width:100%%;z-index:1}
.timeline-item{text-align:center;padding:12px;background:rgba(15,23,42,0.9);border-radius:12px;border:1px solid rgba(59,130,246,0.3);min-width:140px}
.timeline-year{font-size:24px;font-weight:700;color:#3b82f6;margin-bottom:4px}
.timeline-event{font-size:16px;color:#e2e8f0;margin-bottom:4px}
.timeline-cities{font-size:12px;color:#94a3b8}

/* 信息卡片 */
.info-panel{position:absolute;top:68%%;left:4%%;right:4%%;background:rgba(15,23,42,0.95);border-radius:16px;padding:16px 20px;border:1px solid rgba(59,130,246,0.3)}
.info-grid{display:flex;gap:20px;justify-content:space-around}
.info-card{text-align:center;padding:12px}
.info-label{font-size:14px;color:#94a3b8;margin-bottom:4px}
.info-value{font-size:32px;font-weight:700}

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

// 地图淡入 5s
tl.fromTo(".map-wrap img",{opacity:0},{opacity:0.5,duration:0.8,ease:"power2.out"},5.0);

// 时间轴推进 8s开始
var tlItems = document.querySelectorAll('.timeline-item');
tl.fromTo(".timeline-track",{width:"0%%"},{width:"100%%",duration:3,ease:"power2.inOut"},8.0);

tlItems.forEach(function(item, i) {
  tl.fromTo(item,{scale:0,opacity:0},{scale:1,opacity:1,duration:0.4,ease:"back.out(1.5)"},8.5+i*0.8);
});

// 信息卡片 14s
tl.fromTo(".info-panel",{y:50,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},14.0);

// 地图持续缓慢平移
gsap.to(".map-wrap img",{x:"-2%%",duration:10,ease:"none",yoyo:true,repeat:3});

// 结尾 40s
tl.fromTo("#scene3",{yPercent:80,opacity:0},{yPercent:0,opacity:1,duration:0.5,ease:"power3.out"},40.0);
tl.fromTo("#outro-title",{y:-40,scale:0.5,opacity:0},{y:0,scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},40.5);
tl.fromTo("#outro-sub",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},41.2);
tl.fromTo("#outro-cta",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},42.0);
tl.fromTo("#brand-outro",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},43.5);
tl.set("#scene3",{visibility:"hidden"},52.5);

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
    html_parts.append('<div class="timeline-container">')
    html_parts.append('<div class="timeline-track"><div class="timeline-progress"></div></div>')
    html_parts.append('<div class="timeline-items">%s</div>' % timeline_items)
    html_parts.append('</div>')
    html_parts.append('<div class="info-panel" id="info-panel">')
    html_parts.append('<div class="info-grid">%s</div>' % info_cards)
    html_parts.append('</div>')
    html_parts.append('<div id="brand-outro"><div id="brand-outro-text"><span>📍</span> 图钉 · 地图热点</div></div>')
    html_parts.append('</div>')
    
    # 结尾
    html_parts.append('<div id="scene3" class="scene">')
    html_parts.append('<h1 id="outro-title">%s</h1>' % outro_question)
    html_parts.append('<p id="outro-sub">%s</p>' % outro_sub)
    html_parts.append('<p id="outro-cta"><span class="cta-icon">▶</span> %s</p>' % cta_text)
    html_parts.append('</div>')
    
    html_parts.append('</div>')
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
    parser = argparse.ArgumentParser(description='HyperFrames 制度起源模板')
    parser.add_argument('--config', help='JSON配置文件路径')
    parser.add_argument('--demo', action='store_true', help='使用演示数据')
    parser.add_argument('--render', action='store_true', help='生成后渲染')
    parser.add_argument('--quality', default='draft', choices=['draft', 'standard', 'high'])
    args = parser.parse_args()

    if args.demo:
        config = {
            'title': '计划单列市起源',
            'subtitle': '一个制度如何改变5座城市的命运',
            'badge_text': '1984年',
            'badge_unit': '国务院批准设立',
            'map_image': 'egg_price_map.png',
            'timeline': [
                {'year': '1984', 'event': '首批设立', 'cities': ['大连', '青岛', '宁波', '厦门', '深圳']},
                {'year': '1988', 'event': '新增扩展', 'cities': ['青岛', '宁波']},
                {'year': '1994', 'event': '正式定型', 'cities': ['5个城市']},
            ],
            'key_info': [
                {'label': '设立时间', 'value': '1984年', 'color': '#3b82f6'},
                {'label': '城市数量', 'value': '5个', 'color': '#f59e0b'},
                {'label': '行政级别', 'value': '副省级', 'color': '#ef4444'},
            ],
            'outro_question': '这些制度对城市发展有什么影响？',
            'outro_sub': '评论区说说你的看法',
            'cta_text': '点赞关注，每天看数据',
        }
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    elif args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        output_path = os.path.join(TEMPLATE_DIR, 'index.html')
    else:
        print("用法: python hyperframes_institution.py --config config.json 或 --demo")
        return

    html = generate_html(config)
    save_html(html, output_path)

    if args.render:
        render_video(TEMPLATE_DIR, 'institution_demo.mp4', args.quality)


if __name__ == '__main__':
    main()
