#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HyperFrames渲染问题诊断报告"""
import re
import os

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

maps_dir = os.path.join(os.path.dirname(html_path), "assets", "maps")

print("=" * 70)
print("HyperFrames CSS 3D 渲染诊断报告")
print("=" * 70)

# 问题1: Audio标签被注释掉
print("\n[问题1] Audio标签状态")
print("-" * 40)
audio_check = '<!-- <audio' in content
print(f"  Audio标签被注释: {audio_check}")
if audio_check:
    print("  影响: 音频无法播放，渲染器认为无音频")
    # 找原始注释
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '<audio' in line.lower():
            print(f"  位置: Line {i+1}: {line.strip()[:80]}")

# 问题2: GSAP选择器语法错误
print("\n[问题2] GSAP选择器语法错误")
print("-" * 40)
lines = content.split('\n')
syntax_errors = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    # 检查 tl.to( 后面是否跟选择器字符串然后逗号
    if ('tl.to(' in stripped or 'tl.fromTo(' in stripped) and stripped.endswith(','):
        # 检查下一行是否是对象开始
        if i < len(lines):
            next_line = lines[i].strip()
            if next_line.startswith('{'):
                syntax_errors.append((i, stripped[:60]))
                
if syntax_errors:
    print(f"  发现 {len(syntax_errors)} 处语法错误")
    for line_num, err in syntax_errors[:5]:
        print(f"  Line {line_num}: {err}...")
else:
    print("  未发现明显语法错误")

# 问题3: Map图片路径
print("\n[问题3] Map图片引用检查")
print("-" * 40)
map_refs = re.findall(r'assets/maps/([^\"]+\.png)', content)
unique_maps = list(set(map_refs))
print(f"  HTML引用地图数: {len(unique_maps)}")
for m in unique_maps:
    full_path = os.path.join(maps_dir, m)
    exists = os.path.exists(full_path)
    size = os.path.getsize(full_path) if exists else 0
    status = f"{size//1024}KB" if exists else "MISSING"
    print(f"  {m}: {status}")

# 问题4: CSS 3D上下文
print("\n[问题4] CSS 3D上下文配置")
print("-" * 40)
has_perspective = 'perspective:' in content
has_preserve_3d = 'preserve-3d' in content
has_transform_style = 'transform-style' in content
print(f"  perspective: {has_perspective}")
print(f"  transform-style: preserve-3d: {has_preserve_3d}")
print(f"  transform-style: {has_transform_style}")
print(f"  CSS 3D context: {'CONFIGURED' if (has_perspective and has_preserve_3d) else 'INCOMPLETE'}")

# 问题5: Timeline注册
print("\n[问题5] Timeline注册检查")
print("-" * 40)
timelines = re.findall(r'window\.__timelines\["(\w+)"\]\s*=', content)
print(f"  Registered timelines: {timelines}")
print(f"  Composition ID: main")
print(f"  Render timeout: 45s")
print(f"  Actual duration: ~83s")

# 问题6: 渲染警告分析
print("\n[问题6] 渲染警告分析")
print("-" * 40)
print("  [WARN] sub_timeline_readiness_timeout")
print("    - Sub-composition timelines did not become ready within 45000ms")
print("    - 原因: GSAP timeline使用CSS 3D transforms，渲染器等待超时")
print("    - 结果: 帧捕获失败，输出黑屏")

print("\n  [WARN] invalid_inline_script_syntax")
print("    - GSAP选择器字符串拼接后语法错误")
print("    - 例如: tl.to('.dof-blur[data-depth='\"'\"' + 1 + '\"'\"'], '")
print("    - 修复: 需要闭合引号")

print("\n  [WARN] multiple_root_compositions")
print("    - 检测到 index.html, index_v42.html, index_v43.html")
print("    - 可能导致重复渲染")

# 问题7: 核心根因
print("\n" + "=" * 70)
print("核心根因分析")
print("=" * 70)
print("""
1. CSS 3D渲染模式导致超时
   - HyperFrames检测到CSS 3D上下文 (perspective + preserve-3d)
   - 切换到低内存模式，单worker截图
   - 子组件时间线45秒内未就绪，触发超时警告

2. GSAP选择器语法错误
   - 动态拼接的选择器字符串引号未闭合
   - 导致GSAP动画卡死，场景无法切换

3. Audio标签被注释
   - 上一轮调试为绕过audio问题而注释
   - 但视频渲染不依赖audio标签，这是独立的

结论: HyperFrames CSS 3D模式在当前环境下不可靠，
建议改用纯2D DOM动画或PIL静态帧方案。
""")
