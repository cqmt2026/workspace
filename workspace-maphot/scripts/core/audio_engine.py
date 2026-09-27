# -*- coding: utf-8 -*-
"""
声音设计系统 — 音效触发、音频同步、BGM控制

提供完整的音频交互能力：
- 短音效触发（beep、click、whoosh等）
- BGM渐入渐出控制
- 音频波形可视化
- 节拍同步动画
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AudioEngine:
    """声音设计引擎"""
    
    def __init__(self):
        self.ctx = None
        self.bgm_node = None
        self.master_gain = None
    
    def init_audio_js(self):
        """生成初始化音频上下文的JS代码"""
        js = '''
var audioCtx = null;
function initAudio() {
  try {
    if(!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      masterGain = audioCtx.createGain();
      masterGain.gain.value = 0.3;
      masterGain.connect(audioCtx.destination);
    }
    return true;
  } catch(e) {
    return false;
  }
}
'''
        return js
    
    # ========== 音效定义 ==========
    SOUND_EFFECTS = {
        'beep': {'freq': 880, 'duration': 0.1, 'type': 'sine'},
        'click': {'freq': 600, 'duration': 0.05, 'type': 'square'},
        'whoosh': {'freq': 200, 'duration': 0.3, 'type': 'sawtooth'},
        'success': {'freq': 523, 'duration': 0.2, 'type': 'sine', 'notes': [523, 659, 784]},
        'error': {'freq': 200, 'duration': 0.3, 'type': 'sawtooth', 'notes': [200, 150]},
        'pop': {'freq': 400, 'duration': 0.08, 'type': 'triangle'},
        'slide': {'freq': 300, 'duration': 0.15, 'type': 'sine'},
        'ding': {'freq': 1200, 'duration': 0.5, 'type': 'sine'},
    }
    
    @staticmethod
    def generate_beep_js(freq=880, duration=0.1, type='sine', gain=0.1):
        """生成Beep音效JS代码"""
        js = 'function playBeep(freq=%d, dur=%s, type=\'%s\', gainVal=%s) {\n' % (freq, duration, type, gain)
        js += '  try {\n'
        js += '    var ctx = new (window.AudioContext || window.webkitAudioContext)();\n'
        js += '    var osc = ctx.createOscillator();\n'
        js += '    var g = ctx.createGain();\n'
        js += "    osc.type = type;\n"
        js += '    osc.frequency.value = freq;\n'
        js += '    g.gain.value = gainVal;\n'
        js += '    osc.connect(g);\n'
        js += '    g.connect(ctx.destination);\n'
        js += '    osc.start();\n'
        js += '    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);\n'
        js += '    osc.stop(ctx.currentTime + dur);\n'
        js += '  } catch(e) {}\n'
        js += '}\n'
        return js
    
    @staticmethod
    def generate_success_sound():
        """成功音效（三个上升音符）"""
        js = 'function playSuccess() {\n'
        js += '  var notes = [523, 659, 784];\n'
        js += '  notes.forEach(function(f, i) {\n'
        js += "    setTimeout(function() { playBeep(f, 0.15, 'sine', 0.15); }, i * 100);\n"
        js += '  });\n'
        js += '}\n'
        return js + AudioEngine.generate_beep_js()
    
    @staticmethod
    def generate_error_sound():
        """错误音效（两个下降音符）"""
        js = 'function playError() {\n'
        js += '  var notes = [200, 150];\n'
        js += '  notes.forEach(function(f, i) {\n'
        js += "    setTimeout(function() { playBeep(f, 0.2, 'sawtooth', 0.1); }, i * 150);\n"
        js += '  });\n'
        js += '}\n'
        return js + AudioEngine.generate_beep_js()
    
    @staticmethod
    def generate_whoosh_sound():
        """滑动音效"""
        js = '''
function playWhoosh() {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    var g = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(400, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(100, ctx.currentTime + 0.3);
    g.gain.value = 0.1;
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
    osc.connect(g);
    g.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch(e) {}
}
'''
        return js
    
    # ========== BGM控制 ==========
    @staticmethod
    def generate_bgm_controls(audio_src, volume=0.2):
        """生成BGM控制JS"""
        js = "var bgmAudio = new Audio('%s');\n" % audio_src
        js += 'bgmAudio.loop = true;\n'
        js += 'bgmAudio.volume = %s;\n\n' % volume
        js += 'function playBGM() { bgmAudio.play().catch(function(e) { console.log("BGM play failed:", e); }); }\n'
        js += 'function pauseBGM() { bgmAudio.pause(); }\n'
        js += 'function stopBGM() { bgmAudio.pause(); bgmAudio.currentTime = 0; }\n'
        js += 'function setBGMVolume(v) { bgmAudio.volume = Math.max(0, Math.min(1, v)); }\n'
        js += '''
function fadeBGMTo(targetVol, duration) {
  var startVol = bgmAudio.volume;
  var startTime = performance.now();
  function update() {
    var elapsed = (performance.now() - startTime) / 1000;
    var progress = Math.min(elapsed / duration, 1);
    var currentVol = startVol + (targetVol - startVol) * progress;
    bgmAudio.volume = currentVol;
    if(progress < 1) requestAnimationFrame(update);
  }
  update();
}
'''
        return js
    
    # ========== 音频波形可视化 ==========
    @staticmethod
    def generate_waveform_visualizer(canvas_id='wave-canvas', height=60, color='#3b82f6'):
        """生成音频波形可视化JS"""
        js = 'var %s_ctx = null;\n' % canvas_id
        js += 'var %s_analyser = null;\n' % canvas_id
        js += "var %s_canvas = document.getElementById('%s');\n" % (canvas_id, canvas_id)
        js += 'var %s_ctx2 = %s_canvas.getContext(\'2d\');\n' % (canvas_id, canvas_id)
        js += 'var %s_width = %s_canvas.width;\n' % (canvas_id, canvas_id)
        js += 'var %s_height = %s_canvas.height;\n' % (canvas_id, canvas_id)
        js += 'var %s_animation_id = null;\n\n' % canvas_id
        
        js += '''function initWaveform(audioElement) {
  try {
    if(!%s_ctx) {
      %s_ctx = new (window.AudioContext || window.webkitAudioContext)();
      %s_analyser = %s_ctx.createAnalyser();
      %s_analyser.fftSize = 256;
      var source = %s_ctx.createMediaElementSource(audioElement);
      source.connect(%s_analyser);
      %s_analyser.connect(%s_ctx.destination);
    }
    drawWaveform();
  } catch(e) { console.log('Waveform init failed:', e); }
}

function drawWaveform() {
  if(!%s_analyser) return;
  %s_animation_id = requestAnimationFrame(drawWaveform);
  var bufferLength = %s_analyser.frequencyBinCount;
  var dataArray = new Uint8Array(bufferLength);
  %s_analyser.getByteTimeDomainData(dataArray);
  
  %s_ctx2.fillStyle = 'rgba(10, 15, 26, 0.2)';
  %s_ctx2.fillRect(0, 0, %s_width, %s_height);
  %s_ctx2.lineWidth = 2;
  %s_ctx2.strokeStyle = '%s';
  %s_ctx2.beginPath();
  
  var sliceWidth = %s_width / bufferLength;
  var x = 0;
  for(var i = 0; i < bufferLength; i++) {
    var v = dataArray[i] / 128.0;
    var y = v * %d / 2;
    if(i === 0) %s_ctx2.moveTo(x, y);
    else %s_ctx2.lineTo(x, y);
    x += sliceWidth;
  }
  %s_ctx2.stroke();
}

function stopWaveform() {
  if(%s_animation_id) {
    cancelAnimationFrame(%s_animation_id);
    %s_animation_id = null;
  }
}
''' % (canvas_id, canvas_id, canvas_id, canvas_id, canvas_id, canvas_id, canvas_id, 
       canvas_id, canvas_id, canvas_id, canvas_id, canvas_id, color, canvas_id, 
       height, canvas_id, canvas_id, canvas_id, canvas_id, canvas_id)
        
        return js
    
    # ========== 节拍检测同步 ==========
    @staticmethod
    def generate_beat_sync(animated_elements, beat_callback):
        """生成节拍同步动画JS"""
        js = '''
function syncToBeat(elements, callback) {
  var beatInterval = 500; // ms
  setInterval(function() {
    elements.forEach(function(el) {
      callback(el);
    });
  }, beatInterval);
}
'''
        return js


def get_audio_js_bundle():
    """生成完整的音频JS代码包"""
    engine = AudioEngine()
    
    all_js = []
    all_js.append('// Audio Engine v1.0')
    all_js.append('// Initialize')
    all_js.append(engine.init_audio_js())
    all_js.append('// Basic sounds')
    all_js.append(engine.generate_beep_js())
    all_js.append('// Special effects')
    all_js.append(engine.generate_success_sound())
    all_js.append(engine.generate_error_sound())
    all_js.append(engine.generate_whoosh_sound())
    all_js.append('// Sound Manager')
    all_js.append('var SoundManager = {')
    all_js.append("  beep: function(freq, dur, type) { playBeep(freq || 880, dur || 0.1, type || 'sine'); },")
    all_js.append("  click: function() { playBeep(600, 0.05, 'square'); },")
    all_js.append("  whoosh: function() { playWhoosh(); },")
    all_js.append("  success: function() { playSuccess(); },")
    all_js.append("  error: function() { playError(); },")
    all_js.append('};')
    all_js.append('')
    
    return '\n'.join(all_js)


def main():
    """演示声音设计系统"""
    print("=" * 80)
    print("声音设计系统演示")
    print("=" * 80)
    
    engine = AudioEngine()
    
    print("\n【1】Beep音效:")
    print(engine.generate_beep_js(880, 0.1)[:150] + "...")
    
    print("\n【2】成功音效:")
    print(engine.generate_success_sound()[:150] + "...")
    
    print("\n【3】错误音效:")
    print(engine.generate_error_sound()[:150] + "...")
    
    print("\n【4】Whoosh音效:")
    print(engine.generate_whoosh_sound()[:150] + "...")
    
    print("\n【5】BGM控制:")
    print(engine.generate_bgm_controls('music.mp3', 0.2)[:150] + "...")
    
    print("\n【6】波形可视化:")
    print(engine.generate_waveform_visualizer('wave-canvas')[:150] + "...")
    
    print("\n" + "=" * 80)
    print("完整音频代码包:")
    print(get_audio_js_bundle()[:300] + "...")
    print("=" * 80)


if __name__ == '__main__':
    main()
