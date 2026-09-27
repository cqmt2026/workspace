import os
BASE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot'
TEMPLATE_DIR = os.path.join(BASE_DIR, 'my-video')
t='公积金缴存20强'
st='2025年全国城市排名公布'
bt='北京3340亿';bu='全国第一'
mi='egg_price_map.png'
sl='广州';nl='深圳'
sv='1376亿';nv='1340亿'
sr='人数少200万 总额反超';nr='人均1.78万 20强最低'
al='深圳';av='1.78万';an='深圳GDP第4但人均最低'
oq='你的城市公积金有多少？';osb='评论区说说你的城市排第几'
cta='点赞关注，每天看数据'
rl=[(1,'北京','3340亿','3.5万',False),(2,'上海','2660亿','2.8万',False),(3,'广州','1376亿','2.6万',False),(4,'深圳','1340亿','1.78万',True),(5,'杭州','980亿','2.4万',False),(6,'宁波','820亿','2.2万',False),(7,'苏州','780亿','2.0万',False),(8,'南京','760亿','2.1万',False),(9,'无锡','620亿','2.3万',False),(10,'成都','580亿','1.8万',False)]
rh=''
for rk,na,va,pe,ia in rl:
    ac=' anomaly-row' if ia else ''
    hc=' highlight-row' if rk<=3 else ''
    rh+='<div class="rank-row%s%s" id="rank-%d"><div class="rank-num">%d</div><div class="rank-name">%s</div><div class="rank-value">%s</div><div class="rank-per">%s</div></div>\n'%(ac,hc,rk,rk,na,va,pe)
ra=''
for idx,(rk,na,va,pe,ia) in enumerate(rl):
    ti=12.0+idx*1.5;rc='#rank-%d'%(idx+1)
    ra+='tl.fromTo("%s",{y:40,opacity:0,scale:0.8},{y:0,opacity:1,scale:1,duration:0.5,ease:"power3.out"},%.1f);\n'%(rc,ti)
    if ia:
        ra+='tl.to("%s .rank-value",{color:"#ef4444",scale:1.2,duration:0.3,ease:"back.out(2)"},%.1f);tl.to("%s .rank-value",{scale:1,duration:0.3,ease:"power2.out"},%.1f);\n'%(rc,ti+0.5,rc,ti+0.8)
    else:
        ra+='tl.to("%s .rank-value",{color:"#f59e0b",duration:0.5,ease:"power2.out"},%.1f);\n'%(rc,ti+0.3)
ah='tl.to("#ab-hl",{opacity:1,scale:1.1,duration:0.4,ease:"power2.out"},16.0);tl.to("#ab-note",{opacity:1,y:0,duration:0.4,ease:"power2.out"},16.5);tl.to("#ab-hl",{scale:1,duration:0.3,ease:"power2.inOut"},17.0);'
h='<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8"><meta name="viewport" content="width=1080,height=1920">\n<title>'+t+'</title>\n<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>\n<style>\n'
h+='body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0a0f1a;color:#e0e0e0;font-family:"PingFang SC","Microsoft YaHei",sans-serif}\n'
h+='#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:linear-gradient(180deg,#0a0f1a 0%,#1a2744 50%,#0d1520 100%)}\n'
h+='.scene{position:absolute;top:0;left:0;width:1080px;height:1920px;overflow:hidden}\n'
h+='.compare-wrap{position:absolute;top:8%;left:4%;right:4%;display:flex;gap:16px;opacity:0}\n'
h+='.compare-col{flex:1;border-radius:20px;padding:24px 20px;text-align:center;border:2px solid rgba(59,130,246,0.3);background:rgba(15,23,42,0.95)}\n'
h+='.compare-col.south{border-color:rgba(239,68,68,0.4);background:rgba(239,68,68,0.08)}\n'
h+='.compare-col.north{border-color:rgba(59,130,246,0.4);background:rgba(59,130,246,0.08)}\n'
h+='.compare-col .cc-label{font-size:22px;color:#64748b;letter-spacing:3px;margin-bottom:10px}\n'
h+='.compare-col .cc-val{font-size:56px;font-weight:700;letter-spacing:2px}\n'
h+='.compare-col.south .cc-val{color:#ef4444}\n.compare-col.north .cc-val{color:#3b82f6}\n'
h+='.compare-col .cc-sub{font-size:16px;color:#94a3b8;margin-top:8px;line-height:1.4}\n'
h+='.rank-list-wrap{position:absolute;top:42%;left:4%;right:4%;opacity:0}\n'
h+='.rank-list-header{display:flex;gap:12px;margin-bottom:10px;padding:0 60px 0 0;font-size:16px;color:#64748b}\n'
h+='.rank-row{display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid rgba(59,130,246,0.1);opacity:0}\n'
h+='.rank-num{width:40px;height:40px;border-radius:50%;background:rgba(59,130,246,0.2);color:#3b82f6;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700}\n'
h+='.rank-name{flex:1;font-size:24px;color:#fff;font-weight:500}\n'
h+='.rank-value{flex:1;font-size:24px;text-align:right}\n.rank-per{width:120px;font-size:18px;color:#94a3b8;text-align:right}\n'
h+='#ab-hl{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) scale(0.8);background:rgba(239,68,68,0.15);border:3px solid #ef4444;border-radius:24px;padding:20px 40px;opacity:0;z-index:10}\n'
h+='.ab-hl-text{font-size:32px;color:#ef4444;font-weight:700;letter-spacing:3px}\n'
h+='#ab-note{position:absolute;top:62%;left:50%;transform:translateX(-50%) translateY(20px);font-size:20px;color:#f59e0b;letter-spacing:2px;opacity:0}\n'
h+='.ring-wrap{position:absolute;top:8%;right:4%;width:140px;height:140px;opacity:0}\n'
h+='.ring-wrap .ring-bg{fill:none;stroke:rgba(59,130,246,0.1);stroke-width:12}\n'
h+='.ring-wrap .ring-fg{fill:none;stroke:#f59e0b;stroke-width:12;stroke-linecap:round;stroke-dasharray:377;stroke-dashoffset:377;transform:rotate(-90deg);transform-origin:50% 50%}\n'
h+='.ring-wrap .ring-text{position:absolute;top:50%;left:0;right:0;text-align:center;transform:translateY(-50%)}\n.ring-wrap .ring-val{font-size:32px;font-weight:700;color:#f59e0b}\n.ring-wrap .ring-label{font-size:13px;color:#64748b;letter-spacing:1px}\n'
h+='#brand-intro{position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:50;background:#0a0f1a}\n'
h+='#brand-logo-wrap{position:relative;width:120px;height:120px}\n#brand-logo-ring{position:absolute;inset:0;border:3px solid rgba(59,130,246,0.4);border-radius:50%;opacity:0}\n'
h+='#brand-logo-dot{position:absolute;top:50%;left:50%;width:16px;height:16px;background:#3b82f6;border-radius:50%;transform:translate(-50%,-50%);opacity:0;box-shadow:0 0 30px rgba(59,130,246,0.8)}\n'
h+='#brand-name{font-size:48px;color:#fff;letter-spacing:12px;font-weight:300;margin-top:30px;opacity:0}\n'
h+='#brand-slogan{font-size:22px;color:#64748b;letter-spacing:6px;margin-top:10px;opacity:0}\n'
h+='#brand-outro{position:absolute;bottom:6%;left:0;right:0;text-align:center;z-index:50;opacity:0}\n#brand-outro-text{font-size:24px;color:#475569;letter-spacing:8px}\n#brand-outro-text span{color:#3b82f6}\n</style></head>\n<body>\n'
h+='<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="69">\n'
h+='<div id="brand-intro"><div id="brand-logo-wrap"><div id="brand-logo-ring"></div><div id="brand-logo-dot"></div></div><div id="brand-name">\u56fe\u9489</div><div id="brand-slogan">\u5730\u56fe\u70ed\u70b9 \u00b7 \u7528\u5730\u56fe\u8bb2\u65b0\u95fb</div></div>\n'
h+='<div id="scene1" class="scene"><div class="stage"><img src="assets/maps/%s" alt="" style="position:absolute;width:130%%;height:130%%;top:-15%%;left:-15%%;object-fit:cover;opacity:0.08;filter:blur(12px)"></div>\n'%mi
h+='<h1 id="intro-title">%s</h1><p id="intro-sub">%s</p><div id="intro-divider" style="height:3px;background:linear-gradient(90deg,transparent,#f59e0b,transparent);margin:0 25%% 0 25%%"></div><div id="intro-badge">%s</div><p id="intro-unit">%s</p></div>\n'%(t,st,bt,bu)
h+='<div id="scene2" class="scene"><img src="assets/maps/%s" alt="" id="map-img" style="position:absolute;width:110%%;height:82%%;object-fit:cover">\n'%mi
h+='<div class="compare-wrap" id="compare-wrap"><div class="compare-col south"><div class="cc-label">%s</div><div class="cc-val">%s</div><div class="cc-sub">%s</div></div><div class="compare-col north"><div class="cc-label">%s</div><div class="cc-val">%s</div><div class="cc-sub">%s</div></div></div>\n'%(sl,sv,sr,nl,nv,nr)
h+='<div class="ring-wrap" id="ring-wrap"><svg viewBox="0 0 130 130" width="140" height="140"><circle class="ring-bg" cx="65" cy="65" r="60"/><circle class="ring-fg" id="ring-circle" cx="65" cy="65" r="60"/></svg><div class="ring-text"><div class="ring-val" id="ring-val">0%</div><div class="ring-label">\u8986\u76d6\u7387</div></div></div>\n'
h+='<div id="ab-hl"><div class="ab-hl-text">%s: %s</div></div><div id="ab-note">%s</div>\n'%(al,av,an)
h+='<div class="rank-list-wrap" id="rank-list-wrap"><div class="rank-list-header"><div class="col-num" style="width:40px">#</div><div class="col-name" style="flex:1">\u57ce\u5e02</div><div class="col-val" style="flex:1;text-align:right">\u7f34\u5b58\u989d</div><div class="col-per" style="width:120px;text-align:right">\u4eba\u5747</div></div>\n'
h+=rh+'</div>\n</div>\n'
h+='<div id="scene3" class="scene"><h1 id="outro-title">%s</h1><p id="outro-subtitle">%s</p>'%(oq,osb)
h+='<p id="outro-cta"><span class="cta-icon">\u25b6</span> %s</p>'%cta
h+='<div id="brand-outro"><div id="brand-outro-text"><span>\U0001f4cd</span> \u56fe\u9489 \u00b7 \u5730\u56fe\u70ed\u70b9</div></div></div>\n'
h+='</div>\n<script>\nwindow.__timelines=window.__timelines||{};var tl=gsap.timeline({paused:true});\n'
h+='tl.fromTo("#brand-logo-ring",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.5,ease:"power2.out"},0);\n'
h+='tl.fromTo("#brand-logo-dot",{scale:0,opacity:0},{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"},0.3);\n'
h+='tl.fromTo("#brand-name",{y:-30,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},0.6);\n'
h+='tl.fromTo("#brand-slogan",{y:15,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},0.9);\n'
h+='tl.to("#brand-intro",{opacity:0,duration:0.3,ease:"power2.in"},2.2);tl.set("#brand-intro",{visibility:"hidden"},2.5);\n'
h+='tl.fromTo("#intro-title",{scale:0.3,opacity:0,rotation:-15,x:-200},{scale:1,opacity:1,rotation:0,x:0,duration:0.6,ease:"power3.out"},2.5);\n'
h+='tl.fromTo("#intro-sub",{x:300,opacity:0},{x:0,opacity:1,duration:0.5,ease:"power2.out"},2.8);\n'
h+='tl.fromTo("#intro-divider",{scaleX:0},{scaleX:1,duration:0.5,ease:"power2.inOut"},3.1);\n'
h+='tl.fromTo("#intro-badge",{scale:0,opacity:0,rotation:20},{scale:1,opacity:1,rotation:0,duration:0.7,ease:"back.out(1.7)"},3.3);\n'
h+='tl.fromTo("#intro-unit",{y:15,opacity:0},{y:0,opacity:1,duration:0.4,ease:"power2.out"},4.0);\n'
h+='tl.to("#scene1",{opacity:0,duration:0.3,ease:"power2.in"},5.0);tl.set("#scene1",{visibility:"hidden"},5.3);\n'
h+='tl.fromTo("#scene2",{y:200,scale:0.9,opacity:0,rotation:3},{y:0,scale:1,opacity:1,rotation:0,duration:0.5,ease:"power3.out"},5.3);\n'
h+='// 对比双栏\n'
h+='tl.fromTo("#compare-wrap",{y:60,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power3.out"},8.5);\n'
h+='tl.fromTo("#compare-wrap .compare-col:nth-child(1)",{x:-40,opacity:0},{x:0,opacity:1,duration:0.4,ease:"power2.out"},8.8);\n'
h+='tl.fromTo("#compare-wrap .compare-col:nth-child(2)",{x:40,opacity:0},{x:0,opacity:1,duration:0.4,ease:"power2.out"},9.2);\n'
h+='// 异常值\n'
h+=ah+'\n'
h+='// 榜单\n'
h+=ra+'\n'
h+='// 结尾\nlet outroStart=54.5;\n'
h+='tl.to("#scene2",{scale:1.3,opacity:0,filter:"blur(12px)",duration:0.5,ease:"power4.in"},outroStart);\n'
h+='tl.fromTo("#scene3",{yPercent:100,opacity:0},{yPercent:0,opacity:1,duration:0.6,ease:"power3.out"},outroStart+0.2);\n'
h+='tl.fromTo("#outro-title",{y:-60,scale:0.5,opacity:0},{y:0,scale:1,opacity:1,duration:0.6,ease:"back.out(1.7)"},outroStart+0.8);\n'
h+='tl.fromTo("#outro-subtitle",{y:20,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},outroStart+1.5);\n'
h+='tl.fromTo("#outro-cta",{y:15,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},outroStart+3.5);\n'
h+='tl.fromTo("#brand-outro",{y:20,opacity:0},{y:0,opacity:1,duration:0.5,ease:"power2.out"},outroStart+6);\n'
h+='window.__timelines["main"]=tl;tl.play();\n</script>\n</body>\n</html>'
op=os.path.join(TEMPLATE_DIR,'index_v42.html')
os.makedirs(os.path.dirname(op),exist_ok=True)
with open(op,'w',encoding='utf-8') as f:
    f.write(h)
print('OK v4.2 HTML:',len(h),'bytes, saved to',op)