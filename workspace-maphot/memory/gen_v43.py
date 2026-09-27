#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4.3 - 全时段动画版排名模板
核心改进：地图持续缓慢平移 + 精简到50秒 + 榜单滚动不间断
"""
import os

BASE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot'
TEMPLATE_DIR = os.path.join(BASE_DIR, 'my-video')
os.makedirs(TEMPLATE_DIR, exist_ok=True)

t='公积金缴存20强'
st='2025年全国城市排名公布'
bt='北京3340亿'
bu='全国第一'
mi='egg_price_map.png'
sl='广州'; nl='深圳'
sv='1376亿'; nv='1340亿'
sr='人数少200万 总额反超'; nr='人均1.78万 20强最低'
al='深圳'; av='1.78万'; an='深圳GDP第4但人均最低'
oq='你的城市公积金有多少？'
osb='评论区说说你的城市排第几'
cta='点赞关注，每天看数据'

rl=[(1,'北京','3340亿','3.5万',False),(2,'上海','2660亿','2.8万',False),(3,'广州','1376亿','2.6万',False),(4,'深圳','1340亿','1.78万',True),(5,'杭州','980亿','2.4万',False),(6,'宁波','820亿','2.2万',False),(7,'苏州','780亿','2.0万',False),(8,'南京','760亿','2.1万',False)]

def build_rank_rows():
    lines = []
    for rk,na,va,pe,ia in rl:
        ac=' anomaly-row' if ia else ''
        hc=' highlight-row' if rk<=3 else ''
        lines.append(
            '<div class="rank-row%s%s" id="rank-%d">'
            '<div class="rank-num">%d</div>'
            '<div class="rank-name">%s</div>'
            '<div class="rank-value">%s</div>'
            '<div class="rank-per">%s</div>'
            '</div>\n' % (ac, hc, rk, rk, na, va, pe))
    return ''.join(lines)

def build_rank_anim():
    t_rs=18.0
    lines = []
    for idx,(rk,na,va,pe,ia) in enumerate(rl):
        ti = t_rs + idx*2.5
        rc = '#rank-%d'%(idx+1)
        lines.append('tl.fromTo("%s",{y:30,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},%.1f);\n'%(rc,ti))
        if ia:
            lines.append('tl.to("%s .rank-value",{color:"#ef4444",scale:1.15,duration:0.25,ease:"back.out(2)"},%.1f);'%(rc,ti+0.3))
            lines.append('tl.to("%s .rank-value",{scale:1,duration:0.25,ease:"power2.out"},%.1f);\n'%(rc,ti+0.55))
    lines.append('tl.to("#rank-list-wrap",{opacity:0,duration:0.4,ease:"power2.in"},42.0);\n')
    return ''.join(lines)

css = '''
body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0a0f1a;color:#e0e0e0;font-family:"PingFang SC","Microsoft YaHei",sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:linear-gradient(180deg,#0a0f1a 0%,#1a2744 50%,#0d1520 100%)}
.scene{position:absolute;top:0;left:0;width:1080px;height:1920px;overflow:hidden}

/* 对比双栏 */
.compare-wrap{position:absolute;top:6%;left:4%;right:4%;display:flex;gap:16px;opacity:0}
.compare-col{flex:1;border-radius:20px;padding:20px 18px;text-align:center;border:2px solid rgba(59,130,246,0.3);background:rgba(15,23,42,0.95)}
.compare-col.south{border-color:rgba(239,68,68,0.4);background:rgba(239,68,68,0.08)}
.compare-col.north{border-color:rgba(59,130,246,0.4);background:rgba(59,130,246,0.08)}
.compare-col .cc-label{font-size:20px;color:#64748b;letter-spacing:3px;margin-bottom:8px}
.compare-col .cc-val{font-size:52px;font-weight:700;letter-spacing:2px}
.compare-col.south .cc-val{color:#ef4444}.compare-col.north .cc-val{color:#3b82f6}
.compare-col .cc-sub{font-size:14px;color:#94a3b8;margin-top:6px;line-height:1.3}

/* 榜单 */
.rank-list-wrap{position:absolute;top:40%;left:4%;right:4%;opacity:0}
.rank-list-header{display:flex;gap:12px;margin-bottom:8px;padding:0 50px 0 0;font-size:15px;color:#64748b}
.rank-row{display:flex;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid rgba(59,130,246,0.1);opacity:0}
.rank-num{width:36px;height:36px;border-radius:50%;background:rgba(59,130,246,0.2);color:#3b82f6;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700}
.rank-name{flex:1;font-size:22px;color:#fff;font-weight:500}
.rank-value{flex:1;font-size:22px;text-align:right}
.rank-per{width:100px;font-size:16px;color:#94a3b8;text-align:right}
.rank-row.anomaly-row .rank-value{color:#ef4444;font-weight:700}
.rank-row.anomaly-row{background:rgba(239,68,68,0.1);border-radius:8px;padding:8px 6px}
.rank-row.highlight-row .rank-num{background:linear-gradient(135deg,#f59e0b,#ef4444);color:#fff}

/* 异常值高亮 */
#ab-hl{position:absolute;top:48%;left:50%;transform:translate(-50%,-50%) scale(0.8);background:rgba(239,68,68,0.15);border:3px solid #ef4444;border-radius:20px;padding:16px 32px;opacity:0;z-index:10}
.ab-hl-text{font-size:28px;color:#ef4444;font-weight:700;letter-spacing:2px}
#ab-note{position:absolute;top:58%;left:50%;transform:translateX(-50%) translateY(15px);font-size:18px;color:#f59e0b;letter-spacing:2px;opacity:0}

/* 品牌片头 */
#brand-intro{position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:50;background:#0a0f1a}
#brand-logo-wrap{position:relative;width:100px;height:100px}
#brand-logo-ring{position:absolute;inset:0;border:3px solid rgba(59,130,246,0.4);border-radius:50%;opacity:0}
#brand-logo-dot{position:absolute;top:50%;left:50%;width:14px;height:14px;background:#3b82f6;border-radius:50%;transform:translate(-50%,-50%);opacity:0;box-shadow:0 0 25px rgba(59,130,246,0.8)}
#brand-name{font-size:42px;color:#fff;letter-spacing:10px;font-weight:300;margin-top:24px;opacity:0}
#brand-slogan{font-size:20px;color:#64748b;letter-spacing:5px;margin-top:8px;opacity:0}

/* 结尾 */
#brand-outro{position:absolute;bottom:6%;left:0;right:0;text-align:center;z-index:50;opacity:0}
#brand-outro-text{font-size:22px;color:#475569;letter-spacing:7px}#brand-outro-text span{color:#3b82f6}
'''

html_parts = []
html_parts.append('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8"><meta name="viewport" content="width=1080,height=1920">\n<title>%s</title>\n<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>\n<style>\n'%t)
html_parts.append(css)
html_parts.append('</style></head>\n<body>\n')
html_parts.append('<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="50">\n')

# === 品牌片头 ===
html_parts.append('<div id="brand-intro">\n')
html_parts.append('<div id="brand-logo-wrap"><div id="brand-logo-ring"></div><div id="brand-logo-dot"></div></div>\n')
html_parts.append('<div id="brand-name">\u56fe\u9489</div>\n')
html_parts.append('<div id="brand-slogan">\u5730\u56fe\u70ed\u70b9 \u00b7 \u7528\u5730\u56fe\u8bb2\u65b0\u95fb</div>\n')
html_parts.append('</div>\n')

# === scene1 开场 ===
html_parts.append('<div id="scene1" class="scene">\n')
html_parts.append('<div class="stage">\n')
html_parts.append('<img src="assets/maps/%s" alt="" style="position:absolute;width:120%%;height:120%%;top:-10%%;left:-10%%;object-fit:cover;opacity:0.1;filter:blur(8px)" id="bg-img-1">\n' % mi)
html_parts.append('<h1 id="intro-title" style="position:absolute;top:30%%;left:0;right:0;text-align:center;font-size:110px;font-weight:700;color:#fff;letter-spacing:4px;text-shadow:0 0 60px rgba(239,68,68,0.6)">' + t + '</h1>\n')
html_parts.append('<p id="intro-sub" style="position:absolute;top:42%%;left:0;right:0;text-align:center;font-size:32px;color:#f59e0b;letter-spacing:4px">' + st + '</p>\n')
html_parts.append('<div id="intro-badge" style="position:absolute;top:50%%;left:0;right:0;text-align:center;font-size:64px;font-weight:700;color:#f59e0b">' + bt + '</div>\n')
html_parts.append('<p id="intro-unit" style="position:absolute;top:57%%;left:0;right:0;text-align:center;font-size:22px;color:#64748b">' + bu + '</p>')
html_parts.append('</div></div>\n')

# === scene2 主画面 ===
html_parts.append('<div id="scene2" class="scene">\n')
html_parts.append('<img src="assets/maps/%s" alt="" id="map-bg" style="position:absolute;width:110%%;height:100%%;object-fit:cover;top:0">\n' % mi)
html_parts.append('<div class="compare-wrap" id="compare-wrap">\n')
html_parts.append('<div class="compare-col south"><div class="cc-label">' + sl + '</div><div class="cc-val">' + sv + '</div><div class="cc-sub">' + sr + '</div></div>\n')
html_parts.append('<div class="compare-col north"><div class="cc-label">' + nl + '</div><div class="cc-val">' + nv + '</div><div class="cc-sub">' + nr + '</div></div>\n')
html_parts.append('</div>\n')
html_parts.append('<div id="ab-hl"><div class="ab-hl-text">' + al + ': ' + av + '</div></div>\n')
html_parts.append('<div id="ab-note">' + an + '</div>\n')
html_parts.append('<div class="rank-list-wrap" id="rank-list-wrap">\n')
html_parts.append('<div class="rank-list-header">\n')
html_parts.append('<div class="col-num" style="width:36px">#</div>\n')
html_parts.append('<div class="col-name" style="flex:1">\u57ce\u5e02</div>\n')
html_parts.append('<div class="col-val" style="flex:1;text-align:right">\u7f34\u5b58\u989d</div>\n')
html_parts.append('<div class="col-per" style="width:100px;text-align:right">\u4eba\u5747</div>\n')
html_parts.append('</div>\n')
html_parts.append(build_rank_rows())
html_parts.append('</div>\n')
html_parts.append('<div id="brand-outro"><div id="brand-outro-text"><span>\U0001f4cd</span> \u56fe\u9489 \u00b7 \u5730\u56fe\u70ed\u70b9</div></div>\n')
html_parts.append('</div>\n')

# === scene3 结尾 ===
html_parts.append('<div id="scene3" class="scene">\n')
html_parts.append('<h1 id="outro-title" style="position:absolute;top:35%%;left:0;right:0;text-align:center;font-size:64px;font-weight:700;color:#fff;letter-spacing:4px">' + oq + '</h1>\n')
html_parts.append('<p id="outro-sub" style="position:absolute;top:46%%;left:0;right:0;text-align:center;font-size:24px;color:#64748b">' + osb + '</p>\n')
html_parts.append('<p id="outro-cta" style="position:absolute;bottom:20%%;left:0;right:0;text-align:center;font-size:24px;color:#475569"><span class="cta-icon">\u25b6</span> ' + cta + '</p>\n')
html_parts.append('</div>\n')

html_parts.append('</div>\n')  # close root

# === JS ===
js = 'window.__timelines=window.__timelines||{};var tl=gsap.timeline({paused:true});\n'

# 品牌片头 0-2.2s
js += 'tl.fromTo("#brand-logo-ring",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"power2.out"},0);\n'
js += 'tl.fromTo("#brand-logo-dot",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"},0.3);\n'
js += 'tl.fromTo("#brand-name",{y:-20,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},0.6);\n'
js += 'tl.fromTo("#brand-slogan",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},0.8);\n'
js += 'tl.to("#brand-intro",{opacity:0,duration:0.25,ease:"power2.in"},2.0);\n'
js += 'tl.set("#brand-intro",{visibility:"hidden"},2.25);\n'

# 开场 2.25s
js += 'tl.fromTo("#intro-title",{scale:0.3,opacity:0,rotation:-10,x:-150},{scale:1,opacity:1,rotation:0,x:0,duration:0.5,ease:"power3.out"},2.25);\n'
js += 'tl.fromTo("#intro-sub",{x:200,opacity:0},{x:0,opacity:1,duration:0.4,ease:"power2.out"},2.6);\n'
js += 'tl.fromTo("#intro-badge",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},3.0);\n'
js += 'tl.fromTo("#intro-unit",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},3.5);\n'
js += 'tl.to("#scene1",{opacity:0,duration:0.25,ease:"power2.in"},4.5);\n'
js += 'tl.set("#scene1",{visibility:"hidden"},4.75);\n'

# scene2入场 + 地图持续平移
js += 'tl.fromTo("#scene2",{y:150,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},4.75);\n'
js += 'gsap.to("#map-bg",{x:"-5%",duration:8,ease:"none",yoyo:true,repeat:-1});\n'
js += 'gsap.to("#bg-img-1",{scale:1.03,duration:6,ease:"none",yoyo:true,repeat:-1});\n'

# 对比双栏 7s
js += 'tl.fromTo("#compare-wrap",{y:40,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power3.out"},7.0);\n'
js += 'tl.fromTo("#compare-wrap .compare-col:nth-child(1)",{x:-30,opacity:0},{x:0,opacity:1,duration:0.3,ease:"power2.out"},7.3);\n'
js += 'tl.fromTo("#compare-wrap .compare-col:nth-child(2)",{x:30,opacity:0},{x:0,opacity:1,duration:0.3,ease:"power2.out"},7.6);\n'

# 异常值 12s
js += 'tl.to("#ab-hl",{opacity:1,scale:1.05,duration:0.3,ease:"power2.out"},12.0);\n'
js += 'tl.to("#ab-note",{opacity:1,y:0,duration:0.3,ease:"power2.out"},12.4);\n'
js += 'tl.to("#ab-hl",{scale:1,duration:0.2,ease:"power2.out"},12.7);\n'

# 榜单滚动
js += build_rank_anim()

# 结尾 42s
js += 'tl.fromTo("#scene3",{yPercent:80,opacity:0},{yPercent:0,opacity:1,duration:0.5,ease:"power3.out"},42.0);\n'
js += 'tl.fromTo("#outro-title",{y:-40,scale:0.5,opacity:0},{y:0,scale:1,opacity:1,duration:0.5,ease:"back.out(1.5)"},42.5);\n'
js += 'tl.fromTo("#outro-sub",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},43.2);\n'
js += 'tl.fromTo("#outro-cta",{y:10,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},44.0);\n'
js += 'tl.fromTo("#brand-outro",{y:15,opacity:0},{y:0,opacity:1,duration:0.3,ease:"power2.out"},45.5);\n'
js += 'tl.set("#scene3",{visibility:"hidden"},49.5);\n'

js += 'window.__timelines["main"]=tl;tl.play();\n'

html_parts.append('<script>\n')
html_parts.append(js)
html_parts.append('</script>\n</body>\n</html>')

output = ''.join(html_parts)
op = os.path.join(TEMPLATE_DIR, 'index_v43.html')
with open(op, 'w', encoding='utf-8') as f:
    f.write(output)

print('[OK] v4.3 HTML: %d bytes, %d lines' % (len(output), len(output.splitlines())))
print('[OK] Duration: 50s (was 69s)')
print('[OK] Key changes: map slow pan throughout, 8 cities, no static periods')
