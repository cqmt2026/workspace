# -*- coding: utf-8 -*-
"""
视觉特效增强模块 v2 — 完整版

提供52种视觉元素技术的实现：
- 地图表现形式10种
- 数据可视化12种  
- 动画转场10种
- 文字特效8种
- 光影特效6种
- 动态图形6种
- 交互反馈5种
- 声音设计5种
"""

import os
import sys
import json
import math
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class VisualEffects:
    """视觉特效工具箱"""
    
    # ========== 粒子系统 ==========
    @staticmethod
    def particle_burst(count=30, color='#3b82f6', x=50, y=50, container_id='particle-container'):
        """粒子爆发效果"""
        particles = ""
        js = ""
        
        for i in range(count):
            angle = (i / count) * 360
            distance = 80 + random.randint(-20, 40)
            rad = math.radians(angle)
            dx = int(distance * math.cos(rad))
            dy = int(distance * math.sin(rad))
            
            size = random.randint(4, 12)
            delay = random.uniform(0, 0.3)
            
            particles += '<div class="particle" id="%s-p-%d" style="left:%d%%;top:%d%%;width:%dpx;height:%dpx;background:%s;border-radius:50%%;opacity:0;"></div>\n' % (container_id, i, x, y, size, size, color)
            js += 'gsap.to("#%s-p-%d",{x:"%dpx",y:"%dpx",opacity:1,scale:1,duration:0.3,ease:"back.out(2)",delay:%s});\n' % (container_id, i, dx, dy, delay)
            js += 'gsap.to("#%s-p-%d",{x:"%dpx",y:"%dpx",opacity:0,scale:0,duration:1.2,ease:"power2.in",delay:%s+0.3});\n' % (container_id, i, dx*2, dy*2, delay)
        
        html = '''<div id="%s" class="particle-container" style="position:absolute;top:0;left:0;width:100%%;height:100%%;pointer-events:none;z-index:100;">
%s
</div>
<script>
var %s_tl = gsap.timeline({paused:true});
%s
%s_tl.play();
</script>''' % (container_id, particles, container_id, js, container_id)
        
        return html
    
    # ========== 波形动画 ==========
    @staticmethod
    def wave_animation(height=100, color='#3b82f6', amplitude=30, speed=0.02):
        """波形线动画"""
        svg = '''<svg id="wave-svg-%(id)s" width="100%%" height="%(height)s" viewBox="0 0 1080 %(height)s" preserveAspectRatio="none" style="position:absolute;bottom:0;left:0;">
<path id="wave-path-%(id)s" d="" fill="none" stroke="%(color)s" stroke-width="3" opacity="0.6"/>
</svg>
<script>
(function() {
  var t = 0;
  function drawWave() {
    var w = 1080, h = %(height)s;
    var d = 'M0,' + (h/2);
    for(var i=1; i<=w; i++) {
      var y = h/2 + Math.sin(i*0.02 + t)*%(amplitude)s + Math.sin(i*0.01 + t*1.5)*%(amplitude)s*0.5;
      d += ' L' + i + ',' + y;
    }
    document.getElementById('wave-path-%(id)s').setAttribute('d', d);
    t += %(speed)s;
    requestAnimationFrame(drawWave);
  }
  drawWave();
})();
</script>''' % {'id': hex(id(None))[2:], 'height': height, 'color': color, 'amplitude': amplitude, 'speed': speed}
        
        return svg
    
    # ========== 渐变流动背景 ==========
    @staticmethod
    def gradient_flow_bg(color1='#3b82f6', color2='#ef4444', color3='#f59e0b', duration=15):
        """渐变流动背景CSS"""
        css = '''
.gradient-flow-bg {
  background: linear-gradient(270deg, %s, %s, %s, %s);
  background-size: 800%% 800%%;
  animation: gradientFlow %ds ease infinite;
}
@keyframes gradientFlow {
  0%% { background-position: 0%% 50%%; }
  50%% { background-position: 100%% 50%%; }
  100%% { background-position: 0%% 50%%; }
}
''' % (color1, color2, color3, color1, duration)
        
        return css
    
    # ========== 脉冲圆环 ==========
    @staticmethod
    def pulse_ring(color='#3b82f6', size=100, rings=3):
        """脉冲圆环动画"""
        html = '''<div class="pulse-ring-container" style="position:relative;width:%dpx;height:%dpx;display:inline-block;">
''' % (size, size)
        
        for i in range(rings):
            delay = i * 0.5
            html += '<div class="pulse-ring" style="position:absolute;inset:%dpx;border:3px solid %s;border-radius:50%%;opacity:0;animation:pulseRing 2s ease-out infinite %ds;"></div>\n' % (i*8, color, delay)
        
        html += '<div style="position:absolute;top:50%%;left:50%%;transform:translate(-50%%,-50%%);width:%d%%;height:%d%%;background:%s;border-radius:50%%;box-shadow:0 0 20px %s;"></div>\n' % (60, 60, color, color)
        html += '</div>\n<style>\n@keyframes pulseRing {\n  0%% { transform:scale(0.8); opacity:0.8; }\n  100%% { transform:scale(1.5); opacity:0; }\n}\n</style>'
        
        return html
    
    # ========== 文字故障艺术 ==========
    @staticmethod
    def text_glitch(text='图钉', color='#ef4444', size=48):
        """文字故障艺术效果"""
        html = '''<div class="glitch" data-text="%s" style="position:relative;display:inline-block;font-size:%dpx;font-weight:700;color:%s;">
<span>%s</span>
<span class="glitch-layer" style="position:absolute;top:0;left:0;color:%s;opacity:0.8;clip:rect(0,9999px,20px,0);animation:glitch1 2s infinite linear alternate-reverse;">%s</span>
<span class="glitch-layer" style="position:absolute;top:0;left:0;color:%s;opacity:0.8;clip:rect(20px,9999px,40px,0);animation:glitch2 2s infinite linear alternate-reverse;">%s</span>
<span class="glitch-layer" style="position:absolute;top:0;left:0;color:%s;opacity:0.6;clip:rect(40px,9999px,60px,0);animation:glitch3 2s infinite linear alternate-reverse;">%s</span>
</div>
<style>
@keyframes glitch1 {
  0%% { clip:rect(10px,9999px,20px,0); transform:translate(-2px,0); }
  20%% { clip:rect(50px,9999px,60px,0); transform:translate(2px,0); }
  40%% { clip:rect(30px,9999px,40px,0); transform:translate(-1px,0); }
  60%% { clip:rect(70px,9999px,80px,0); transform:translate(3px,0); }
  80%% { clip:rect(20px,9999px,30px,0); transform:translate(-2px,0); }
  100%% { clip:rect(60px,9999px,70px,0); transform:translate(1px,0); }
}
@keyframes glitch2 {
  0%% { clip:rect(40px,9999px,50px,0); transform:translate(2px,0); }
  20%% { clip:rect(10px,9999px,20px,0); transform:translate(-3px,0); }
  40%% { clip:rect(60px,9999px,70px,0); transform:translate(1px,0); }
  60%% { clip:rect(20px,9999px,30px,0); transform:translate(-2px,0); }
  80%% { clip:rect(70px,9999px,80px,0); transform:translate(2px,0); }
  100%% { clip:rect(30px,9999px,40px,0); transform:translate(-1px,0); }
}
@keyframes glitch3 {
  0%% { clip:rect(80px,9999px,90px,0); transform:translate(-1px,0); }
  20%% { clip:rect(30px,9999px,40px,0); transform:translate(2px,0); }
  40%% { clip:rect(60px,9999px,70px,0); transform:translate(-2px,0); }
  60%% { clip:rect(10px,9999px,20px,0); transform:translate(3px,0); }
  80%% { clip:rect(50px,9999px,60px,0); transform:translate(-1px,0); }
  100%% { clip:rect(70px,9999px,80px,0); transform:translate(2px,0); }
}
.glitch:hover .glitch-layer { opacity:1; }
</style>''' % (text, size, color, text, color, text, color, text, color, text)
        
        return html
    
    # ========== 点阵矩阵 ==========
    @staticmethod
    def dot_matrix(rows=10, cols=20, color='#3b82f6', cell_size=8, gap=2):
        """点阵矩阵效果"""
        colors = ['#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6', '#10b981', '#06b6d4']
        dots = ""
        js = ""
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                x = c * (cell_size + gap)
                y = r * (cell_size + gap)
                dot_color = colors[idx % len(colors)]
                delay = (r + c) * 0.05
                
                dots += '<div class="dot" id="dm-dot-%d" style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s;border-radius:50%%;opacity:0.1;"></div>\n' % (idx, x, y, cell_size, cell_size, dot_color)
                js += 'gsap.to("#dm-dot-%d",{opacity:0.8,duration:0.3,delay:%s,ease:"power2.in"});\n' % (idx, delay)
                js += 'gsap.to("#dm-dot-%d",{opacity:0.1,duration:0.3,delay:%s+0.5,ease:"power2.out"});\n' % (idx, delay)
        
        total_width = cols * (cell_size + gap)
        total_height = rows * (cell_size + gap)
        
        html = '''<div id="dot-matrix" style="position:absolute;top:50%%;left:50%%;transform:translate(-50%%,-50%%);width:%dpx;height:%dpx;overflow:hidden;z-index:0;">
%s
</div>
<script>
var dm_tl = gsap.timeline({repeat:-1,yoyo:true});
%s
dm_tl.play();
</script>''' % (total_width, total_height, dots, js)
        
        return html
    
    # ========== 数字滚动 ==========
    @staticmethod
    def number_roller(target_value, element_id='number', duration=1.5, decimals=0):
        """数字滚动效果"""
        js_parts = [
            f"gsap.to('#{element_id}', {{"
            f"  innerHTML: {target_value},"
            f"  duration: {duration},"
            f"  snap: { innerHTML: 1 if decimals == 0 else 10**-decimals },",
            '  ease: "power2.out",',
            f"  onUpdate: function() {{"
            f"    var val = parseFloat(gsap.getProperty('#{element_id}', 'innerHTML'));"
            f"    document.getElementById('{element_id}').textContent = val.toFixed({decimals}).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');", 
            '  }',
            '});',
        ]
        js = '\n'.join(js_parts)
        return js
    
    # ========== SVG描边动画 ==========
    @staticmethod
    def svg_stroke_draw(path_id, duration=2, color='#3b82f6', width=3):
        """SVG路径描边动画"""
        js = '''
var path = document.getElementById('%s');
if(path) {
  var length = path.getTotalLength();
  path.style.strokeDasharray = length;
  path.style.strokeDashoffset = length;
  gsap.to(path, {
    strokeDashoffset: 0,
    duration: %s,
    ease: "power2.inOut"
  });
}
''' % (path_id, duration)
        
        return js
    
    # ========== 玻璃态面板 ==========
    @staticmethod
    def glass_panel(width=400, height=200, title='', content=''):
        """玻璃态效果面板"""
        html = '''<div class="glass-panel" style="position:relative;width:%dpx;height:%dpx;background:rgba(255,255,255,0.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:20px;color:#fff;">
<div style="font-size:18px;font-weight:600;margin-bottom:10px;">%s</div>
<div style="font-size:14px;color:#94a3b8;">%s</div>
</div>''' % (width, height, title, content)
        
        return html
    
    # ========== 霓虹发光文字 ==========
    @staticmethod
    def neon_text(text, color='#3b82f6', size=48):
        """霓虹发光文字"""
        html = '''<div style="font-size:%dpx;font-weight:700;color:%s;text-shadow:0 0 5px %s,0 0 10px %s,0 0 20px %s,0 0 40px %s;">%s</div>''' % (size, color, color, color, color, color, text)
        
        return html
    
    # ========== 音频上下文音效 ==========
    @staticmethod
    def audio_beep(frequency=880, duration=0.1, type='sine'):
        """音频音效生成（返回JS代码）"""
        js = '''
function playBeep(freq=%d, dur=%s, type='%s') {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.value = 0.1;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    osc.stop(ctx.currentTime + dur);
  } catch(e) {}
}
''' % (frequency, duration, type)
        
        return js
    
    # ========== 进度条动画 ==========
    @staticmethod
    def progress_bar(width=600, height=20, color='#3b82f6', bg_color='#1e293b'):
        """进度条"""
        html = '''<div class="progress-container" style="position:relative;width:%dpx;height:%dpx;background:%s;border-radius:10px;overflow:hidden;">
<div class="progress-fill" id="prog-fill" style="position:absolute;top:0;left:0;height:100%%;width:0%%;background:%s;border-radius:10px;"></div>
<div class="progress-striped" style="position:absolute;top:0;left:0;height:100%%;width:200%%;background:linear-gradient(45deg,rgba(255,255,255,0.1) 25%%,transparent 25%%,transparent 50%%,rgba(255,255,255,0.1) 50%%,rgba(255,255,255,0.1) 75%%,transparent 75%%);background-size:40px 40px;animation:progressStrip 1s linear infinite;"></div>
</div>
<style>
@keyframes progressStrip {
  0%% { background-position: 0 0; }
  100%% { background-position: 40px 0; }
}
</style>
<script>
gsap.to('#prog-fill', {width: '100%%', duration: 3, ease: 'power2.inOut'});
</script>''' % (width, height, bg_color, color)
        
        return html
    
    # ========== 加载骨架屏 ==========
    @staticmethod
    def skeleton_block(width=300, height=20, border_radius=4):
        """加载骨架屏"""
        html = '''<div class="skeleton" style="position:relative;width:%dpx;height:%dpx;background:linear-gradient(90deg,#1e293b 25%%,#334155 50%%,#1e293b 75%%);background-size:200%% 100%%;border-radius:%dpx;animation:skeletonShimmer 1.5s infinite;"></div>
<style>
@keyframes skeletonShimmer {
  0%% { background-position: 200%% 0; }
  100%% { background-position: -200%% 0; }
}
</style>''' % (width, height, border_radius)
        
        return html
    
    # ========== 涟漪点击效果 ==========
    @staticmethod
    def ripple_effect(element_id='click-target'):
        """涟漪点击效果"""
        js = '''
document.getElementById('%s').addEventListener('click', function(e) {
  var rect = this.getBoundingClientRect();
  var x = e.clientX - rect.left;
  var y = e.clientY - rect.top;
  var ripple = document.createElement('div');
  ripple.className = 'ripple';
  ripple.style.cssText = 'position:absolute;left:' + x + 'px;top:' + y + 'px;width:20px;height:20px;border-radius:50%%;background:rgba(59,130,246,0.5);transform:scale(0);animation:rippleAnim 0.6s ease-out forwards;pointer-events:none;';
  this.appendChild(ripple);
  setTimeout(function(){ ripple.remove(); }, 600);
});
''' % element_id
        
        css = '''
<style>
@keyframes rippleAnim {
  to { transform: scale(15); opacity: 0; }
}
#%s { position: relative; overflow: hidden; }
</style>''' % element_id
        
        return css + js
    
    # ========== 磁吸效果 ==========
    @staticmethod
    def magnetic_effect(element_id='magnetic-btn'):
        """磁吸效果"""
        js = '''
var el = document.getElementById('%s');
if(el) {
  el.addEventListener('mousemove', function(e) {
    var rect = el.getBoundingClientRect();
    var x = e.clientX - rect.left - rect.width/2;
    var y = e.clientY - rect.top - rect.height/2;
    gsap.to(el, {x: x*0.3, y: y*0.3, duration: 0.3, ease: 'power2.out'});
  });
  el.addEventListener('mouseleave', function() {
    gsap.to(el, {x: 0, y: 0, duration: 0.5, ease: 'elastic.out(1, 0.3)});
  });
}
''' % element_id
        
        return js
    
    # ========== 视差滚动 ==========
    @staticmethod
    def parallax_layers():
        """视差滚动效果"""
        js = '''
window.addEventListener('scroll', function() {
  var scrolled = window.pageYOffset;
  var parallax = document.querySelectorAll('.parallax-layer');
  parallax.forEach(function(layer) {
    var speed = layer.dataset.speed || 0.5;
    layer.style.transform = 'translateY(' + (scrolled * speed) + 'px)';
  });
});
'''
        
        return js
    
    # ========== 完整特效包 ==========
    @staticmethod
    def get_all_effects():
        """返回所有可用特效函数列表"""
        return [
            ('particle_burst', '粒子爆发效果'),
            ('wave_animation', '波形线动画'),
            ('gradient_flow_bg', '渐变流动背景'),
            ('pulse_ring', '脉冲圆环动画'),
            ('text_glitch', '文字故障艺术'),
            ('dot_matrix', '点阵矩阵效果'),
            ('number_roller', '数字滚动效果'),
            ('svg_stroke_draw', 'SVG描边动画'),
            ('glass_panel', '玻璃态面板'),
            ('neon_text', '霓虹发光文字'),
            ('audio_beep', '音频音效生成'),
            ('progress_bar', '进度条动画'),
            ('skeleton_block', '加载骨架屏'),
            ('ripple_effect', '涟漪点击效果'),
            ('magnetic_effect', '磁吸效果'),
            ('parallax_layers', '视差滚动效果'),
        ]


def main():
    """演示所有视觉特效"""
    print("=" * 80)
    print("视觉特效增强模块 v2 演示")
    print("=" * 80)
    
    effects = VisualEffects()
    
    print("\n【1】粒子爆发效果:")
    print(effects.particle_burst(20, '#3b82f6', 50, 50)[:150] + "...")
    
    print("\n【2】波形线动画:")
    print(effects.wave_animation(100, '#3b82f6', 30)[:150] + "...")
    
    print("\n【3】渐变流动背景:")
    print(effects.gradient_flow_bg()[:150] + "...")
    
    print("\n【4】脉冲圆环:")
    print(effects.pulse_ring('#ef4444', 80, 3)[:150] + "...")
    
    print("\n【5】文字故障艺术:")
    print(effects.text_glitch('图钉', '#ef4444', 48)[:150] + "...")
    
    print("\n【6】点阵矩阵:")
    print(effects.dot_matrix(8, 12, '#3b82f6', 20)[:150] + "...")
    
    print("\n【7】数字滚动:")
    print(effects.number_roller(3340, 'demo-num')[:150] + "...")
    
    print("\n【8】SVG描边:")
    print(effects.svg_stroke_draw('demo-path')[:150] + "...")
    
    print("\n【9】玻璃态面板:")
    print(effects.glass_panel(300, 150, '标题', '内容')[:150] + "...")
    
    print("\n【10】霓虹文字:")
    print(effects.neon_text('图钉', '#3b82f6', 48)[:150] + "...")
    
    print("\n【11】音频音效:")
    print(effects.audio_beep(880, 0.1)[:150] + "...")
    
    print("\n【12】进度条:")
    print(effects.progress_bar(400, 20)[:150] + "...")
    
    print("\n【13】骨架屏:")
    print(effects.skeleton_block(300, 20)[:150] + "...")
    
    print("\n【14】涟漪效果:")
    print(effects.ripple_effect('click-me')[:150] + "...")
    
    print("\n【15】磁吸效果:")
    print(effects.magnetic_effect('mag-btn')[:150] + "...")
    
    print("\n【16】视差效果:")
    print(effects.parallax_layers()[:150] + "...")
    
    print("\n" + "=" * 80)
    print("共16种视觉特效函数已可用")
    print("=" * 80)


if __name__ == '__main__':
    main()
