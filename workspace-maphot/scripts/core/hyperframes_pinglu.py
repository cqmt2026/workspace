# -*- coding: utf-8 -*-
"""
HyperFrames 平陆运河地理故事流模板
4场景切换：广西全貌 -> 起点横州 -> 穿越丘陵 -> 终点茅尾海
"""
import os

JS_CODE = r"""
window.__timelines = {};
var tl = gsap.timeline({paused:true});

// 品牌片头 0-2s
tl.fromTo("#brand-logo-ring",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"power2.out"},0);
tl.fromTo("#brand-logo-dot",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"},0.3);
tl.fromTo("#brand-name",{y:-20,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},0.6);
tl.fromTo("#brand-slogan",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},0.8);
tl.to("#brand-intro",{opacity:0,duration:0.2,ease:"power2.in"},1.8);
tl.set("#brand-intro",{visibility:"hidden"},2.0);

// 场景1 2s-14s
tl.fromTo("#scene-0",{y:100,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},2.0);
tl.to("#scene-0",{opacity:0,duration:0.3,ease:"power2.in"},14.0);
tl.set("#scene-0",{visibility:"hidden"},14.3);

// 场景2 14s-26s
tl.fromTo("#scene-1",{y:100,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},14.3);
tl.to("#scene-1",{opacity:0,duration:0.3,ease:"power2.in"},26.0);
tl.set("#scene-1",{visibility:"hidden"},26.3);

// 场景3 26s-40s
tl.fromTo("#scene-2",{y:100,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},26.3);
tl.to("#scene-2",{opacity:0,duration:0.3,ease:"power2.in"},40.0);
tl.set("#scene-2",{visibility:"hidden"},40.3);

// 场景4 40s-54s
tl.fromTo("#scene-3",{y:100,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},40.3);
tl.to("#scene-3",{opacity:0,duration:0.3,ease:"power2.in"},54.0);
tl.set("#scene-3",{visibility:"hidden"},54.3);

// 结尾 54s-60s
tl.fromTo("#outro",{yPercent:50,opacity:0},{yPercent:0,opacity:1,duration:0.5,ease:"power3.out"},54.3);
tl.fromTo("#outro-title",{y:-30,scale:0.5,opacity:0},{y:0,scale:1,opacity:1,duration:0.4,ease:"back.out(1.5)"},54.8);
tl.fromTo("#outro-sub",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},55.5);
tl.fromTo("#outro-cta",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},56.2);
tl.fromTo("#brand-outro",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},57.5);
tl.set("#outro",{visibility:"hidden"},62.0);

window.__timelines["main"]=tl;
tl.play();
"""

CSS_CODE = r"""
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1920px; overflow: hidden; background: #0A0F1A; font-family: "Microsoft YaHei","PingFang SC",sans-serif; }
#root { position: relative; width: 1080px; height: 1920px; }
.scene-card { position: absolute; top: 0; left: 0; width: 1080px; height: 1920px; opacity: 0; visibility: hidden; }
.scene-bg { width: 1080px; height: 1920px; object-fit: cover; display: block; }
.scene-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(10,15,26,0.3) 0%, transparent 30%, transparent 60%, rgba(10,15,26,0.9) 100%); }
.scene-badge-wrap { position: absolute; bottom: 220px; left: 50%; transform: translateX(-50%); text-align: center; }
.scene-badge { font-size: 72px; font-weight: 700; color: #00D4FF; text-shadow: 0 0 30px rgba(0,212,255,0.5); }
.scene-badge-unit { font-size: 22px; color: #FFD740; margin-top: 4px; letter-spacing: 2px; }
.scene-title { position: absolute; top: 120px; left: 0; right: 0; font-size: 48px; font-weight: 700; color: #FFFFFF; text-align: center; letter-spacing: 3px; }
.scene-subtitle { position: absolute; top: 185px; left: 0; right: 0; font-size: 22px; color: #FFD740; text-align: center; letter-spacing: 2px; }
#brand-intro { position: absolute; inset: 0; z-index: 100; background: #0A0F1A; display: flex; flex-direction: column; align-items: center; justify-content: center; }
#brand-logo-ring { position: absolute; width: 120px; height: 120px; border: 3px solid rgba(0,212,255,0.4); border-radius: 50%; opacity: 0; }
#brand-logo-dot { position: absolute; top: 50%; left: 50%; width: 16px; height: 16px; background: #00D4FF; border-radius: 50%; transform: translate(-50%,-50%); opacity: 0; box-shadow: 0 0 30px rgba(0,212,255,0.8); }
#brand-name { font-size: 48px; color: #fff; letter-spacing: 12px; font-weight: 300; margin-top: 30px; opacity: 0; }
#brand-slogan { font-size: 20px; color: #64748B; letter-spacing: 6px; margin-top: 10px; opacity: 0; }
#outro { position: absolute; inset: 0; z-index: 50; background: linear-gradient(180deg, #0A0F1A 0%, #0D1525 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0; visibility: hidden; }
#outro-title { font-size: 52px; color: #fff; font-weight: 700; letter-spacing: 3px; }
#outro-sub { font-size: 24px; color: #64748B; margin-top: 16px; letter-spacing: 2px; }
#outro-cta { font-size: 24px; color: #475569; margin-top: 40px; }
#brand-outro { position: absolute; bottom: 80px; left: 0; right: 0; text-align: center; font-size: 22px; color: #475569; letter-spacing: 7px; }
#brand-outro span { color: #00D4FF; }
"""

def generate_html(config, audio_duration=None):
    title = config.get('title', '平陆运河')
    outro_question = config.get('outro_question', '')
    outro_sub = config.get('outro_sub', '')
    cta_text = config.get('cta_text', '')
    
    scenes = [
        {'image': 'assets/maps/scene1_full_guangxi.png', 'title': '平陆运河', 'subtitle': '广西 · 新中国成立以来第一条江海连通超级运河', 'badge': '507亿', 'badge_unit': '元总投资'},
        {'image': 'assets/maps/scene2_nanning_start.png', 'title': '起点：西津渡口', 'subtitle': '南宁横州市 · 西江支流上的普通渡口', 'badge': '海拔60米', 'badge_unit': '起点高程'},
        {'image': 'assets/maps/scene3_crossing.png', 'title': '穿越广西丘陵', 'subtitle': '19座梯级船闸 · 逐级提水翻山', 'badge': '落差19米', 'badge_unit': '19座船闸'},
        {'image': 'assets/maps/scene4_sea_end.png', 'title': '终点：茅尾海', 'subtitle': '注入北部湾 · 直通南海', 'badge': '缩短560km', 'badge_unit': '比绕行广州'},
    ]
    
    scene_cards = ""
    for i, s in enumerate(scenes):
        scene_cards += '<div class="scene-card" id="scene-%d" data-scene-index="%d">\n' % (i, i)
        scene_cards += '  <img src="%s" alt="" class="scene-bg">\n' % s['image']
        scene_cards += '  <div class="scene-overlay"></div>\n'
        scene_cards += '  <div class="scene-badge-wrap">\n'
        scene_cards += '    <div class="scene-badge">%s</div>\n' % s['badge']
        scene_cards += '    <div class="scene-badge-unit">%s</div>\n' % s['badge_unit']
        scene_cards += '  </div>\n'
        scene_cards += '  <div class="scene-title">%s</div>\n' % s['title']
        scene_cards += '  <div class="scene-subtitle">%s</div>\n' % s['subtitle']
        scene_cards += '</div>\n'
    
    html = '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080,height=1920">
<title>%s</title>
<style>
%s
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="65">

<div id="brand-intro">
  <div style="position:relative;width:120px;height:120px">
    <div id="brand-logo-ring"></div>
    <div id="brand-logo-dot"></div>
  </div>
  <div id="brand-name">图钉</div>
  <div id="brand-slogan">地图热点 · 用地图讲新闻</div>
</div>

%s

<div id="outro">
  <div id="outro-title">%s</div>
  <div id="outro-sub">%s</div>
  <div id="outro-cta"><span style="font-size:28px">&#9654;</span> %s</div>
  <div id="brand-outro"><span>&#128205;</span> 图钉 · 地图热点</div>
</div>

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
%s
</script>
</body>
</html>''' % (title, CSS_CODE, scene_cards, outro_question, outro_sub, cta_text, JS_CODE)
    
    return html


def save_html(html, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('[OK] HTML saved: %s (%d bytes)' % (output_path, len(html)))
    return output_path


if __name__ == '__main__':
    import sys
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    config = {
        'title': '平陆运河',
        'outro_question': '你的省份，离海有多远？',
        'outro_sub': '评论区说说你的城市',
        'cta_text': '点赞关注，用地图看懂地理背后的故事',
    }
    
    html = generate_html(config)
    out_path = os.path.join(BASE_DIR, 'my-video', 'index.html')
    save_html(html, out_path)
