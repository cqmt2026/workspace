# -*- coding: utf-8 -*-
"""
将Pixabay素材按时间段叠加到HyperFrames渲染视频上

工作流程：
1. 从 material_index.json 读取素材匹配结果
2. 对每个有素材的场景，用FFmpeg overlay叠加
3. 分段处理 + concat合并
"""
import os, sys, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 加载素材索引
index_path = os.path.join(BASE_DIR, 'data', 'materials', 'material_index.json')
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

print("素材索引:", len(index.get('materials', [])), '条')
for m in index.get('materials', []):
    print("  - %s (%s)" % (m['filename'], m.get('desc', '')))

# 素材路径映射
material_map = {
    'port_container.mp4': os.path.join(BASE_DIR, 'trade-circle', 'assets', 'port_container.mp4'),
    'night_port.mp4': os.path.join(BASE_DIR, 'trade-circle', 'assets', 'night_port.mp4'),
    'shanghai.mp4': os.path.join(BASE_DIR, 'trade-circle', 'assets', 'shanghai.mp4'),
}

# 时间段配置（根据material_matcher的输出）
segments = [
    {'start': 0, 'end': 7, 'material': 'port_container.mp4'},  # 开场
    {'start': 7, 'end': 13, 'material': 'port_container.mp4'},  # 对比
    {'start': 13, 'end': 22, 'material': 'port_container.mp4'},  # 地图
    {'start': 22, 'end': 30, 'material': 'night_port.mp4'},     # RCEP
    {'start': 30, 'end': 40, 'material': 'shanghai.mp4'},       # 伙伴
    {'start': 40, 'end': 48, 'material': 'shanghai.mp4'},       # 历史
    {'start': 48, 'end': 55, 'material': None},                 # 结尾
]

# 输入视频
input_video = os.path.join(BASE_DIR, 'data', 'videos', '中国贸易朋友圈_最终版_带字幕.mp4')
output_video = os.path.join(BASE_DIR, 'data', 'videos', 'overlay_%s.mp4' % time.strftime('%Y%m%d_%H%M%S'))

if not os.path.exists(input_video):
    print("错误: 输入视频不存在", input_video)
    sys.exit(1)

print("\n开始素材叠加...")
print("=" * 50)

# 分段处理
seg_files = []
seg_idx = 0
current_time = 0.0

for seg in segments:
    start = seg['start']
    end = seg['end']
    duration = end - start
    material = seg['material']
    
    seg_file = os.path.join(BASE_DIR, 'data', 'videos', 'seg_%02d.mp4' % seg_idx)
    seg_files.append(seg_file)
    
    if material and os.path.exists(material_map.get(material)):
        # 有素材：缩放+叠加
        pix_path = material_map[material]
        vf = ("scale=1080:1920:force_original_aspect_ratio=decrease,"
              "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1")
        cmd = ['ffmpeg', '-y',
               '-ss', str(start), '-i', input_video,
               '-ss', '0', '-t', str(min(duration, 15)), '-i', pix_path,
               '-filter_complex', '[0:v][1:v]overlay=0:0[v]',
               '-map', '[v]', '-map', '0:a:0',
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
               '-c:a', 'aac', '-b:a', '128k',
               '-t', str(duration), seg_file]
    else:
        # 无素材：直接截取
        cmd = ['ffmpeg', '-y',
               '-ss', str(start), '-t', str(duration), '-i', input_video,
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
               '-c:a', 'copy', seg_file]
    
    r = subprocess.run(cmd, capture_output=True, timeout=300,
                       encoding='utf-8', errors='replace')
    ok = os.path.exists(seg_file) and r.returncode == 0
    # 如果超时时ffmpeg写了一半，删除残片重试
    if not ok and os.path.exists(seg_file):
        try: os.remove(seg_file); ok = False
        except: pass
    sz = os.path.getsize(seg_file)//1024 if ok else 0
    status = '%dKB' % (sz//1024) if ok else 'FAIL'
    if not ok:
        err_text = (r.stderr or '').decode('utf-8','replace')[-200:] if isinstance(r.stderr, bytes) else str(r.stderr)[-200:]
        print("  [%d-%ds] %s -> FAIL (%s)" % (start, end, material or '无素材', err_text.strip()[:80]))
    else:
        print("  [%d-%ds] %s -> %s" % (start, end, material or '无素材', status))
    seg_idx += 1

# 合并
concat_file = os.path.join(BASE_DIR, 'data', 'videos', 'concat.txt')
with open(concat_file, 'w', encoding='utf-8') as f:
    for sf in seg_files:
        f.write("file '%s'\n" % sf.replace('\\', '/'))

cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
       '-c:a', 'aac', '-b:a', '192k', output_video]
# 删除可能存在的残片（上次失败的半成品）
if os.path.exists(output_video):
    try: os.remove(output_video)
    except: pass
r = subprocess.run(cmd, capture_output=True, timeout=300,
                   encoding='utf-8', errors='replace')

if os.path.exists(output_video) and r.returncode == 0:
    sz = os.path.getsize(output_video)//1024//1024
    # 验证 moov atom 完整性（二次确认）
    verify = subprocess.run(['ffmpeg', '-v', 'error', '-i', output_video, '-frames:v', '1', '-f', 'null', '-'],
                            capture_output=True, timeout=60)
    if verify.returncode != 0:
        print("\n⚠ 输出文件moov损坏，重新合并...")
        os.remove(output_video)
        cmd2 = cmd[:-1] + [output_video]  # 重试
        r2 = subprocess.run(cmd2, capture_output=True, timeout=300,
                            encoding='utf-8', errors='replace')
        if not (os.path.exists(output_video) and r2.returncode == 0):
            print("\n❌ 二次合并也失败")
            sys.exit(1)
    print("\n" + "=" * 50)
    print("完成！输出: %s (%d MB)" % (os.path.basename(output_video), sz))
else:
    err_text = (r.stderr or '').decode('utf-8','replace')[-300:] if isinstance(r.stderr, bytes) else str(r.stderr)[-300:]
    print("\n❌ 合并失败 rc=%d" % r.returncode)
    print(err_text)
