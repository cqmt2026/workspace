# -*- coding: utf-8 -*-
"""优化版step_compose_video - FFmpeg drawtext实时渲染字幕"""
def step_compose_video():
    """步骤5: 合成视频（含字幕叠加）"""
    logger.info("=" * 50)
    logger.info("步骤5: 合成视频 (优化)")
    logger.info("=" * 50)
    
    config = CONFIG
    script_path = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}_script.json")
    srt_path = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}.srt")
    audio_path = os.path.join(DATA_DIR, 'audio', config['output']['audio_file'])
    frames_path = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}_frames.json")
    video_path = os.path.join(DATA_DIR, 'videos', config['output']['video_file'])
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    if not os.path.exists(frames_path):
        logger.error("帧图索引不存在")
        return None
    if not os.path.exists(audio_path):
        logger.error("配音不存在")
        return None
    if not os.path.exists(srt_path):
        logger.error("字幕不存在")
        return None
    
    with open(frames_path, 'r', encoding='utf-8') as f:
        frames = json.load(f)
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
    
    segments = []
    segments.append(("intro", script['intro']))
    for s in script['sections']:
        segments.append((s['name'], s['narration']))
    segments.append(("outro", script['outro']))
    
    dur = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
        capture_output=True, text=True, timeout=10
    )
    total_duration = float(dur.stdout.strip()) if dur.stdout else 120
    total_chars = sum(len(t) for _, t in segments)
    
    # 生成逐段视频
    segment_dir = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}_segments")
    os.makedirs(segment_dir, exist_ok=True)
    
    segment_files = []
    current_time = 0.0
    
    for i, (name, text) in enumerate(segments):
        ratio = len(text) / total_chars
        seg_dur = total_duration * ratio
        end_time = current_time + seg_dur
        
        img_path = None
        for fr in frames:
            if fr['name'] == name:
                img_path = fr['path']
                break
        if not img_path:
            img_path = frames[0]['path'] if frames else None
        if not img_path:
            current_time = end_time
            continue
        
        seg_path = os.path.join(segment_dir, f"{name}.mp4")
        fade_out = max(0, seg_dur - 0.5)
        
        cmd = [
            ffmpeg, '-y', '-loop', '1', '-i', img_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', str(config['video']['crf']),
            '-pix_fmt', 'yuv420p', '-r', str(config['video']['fps']), '-t', str(seg_dur),
            '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920,fps={config['video']['fps']},fade=t=in:st=0:d={config['video']['fade_duration']},fade=t=out:st={fade_out}:d={config['video']['fade_duration']}",
            seg_path
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if r.returncode == 0:
            segment_files.append(seg_path)
            logger.info(f"  [{i+1}/{len(segments)}] {name} ({seg_dur:.1f}s)")
        else:
            cmd2 = [
                ffmpeg, '-y', '-loop', '1', '-i', img_path,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', str(config['video']['crf']),
                '-pix_fmt', 'yuv420p', '-r', str(config['video']['fps']), '-t', str(seg_dur),
                '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fade=t=in:st=0:d={config['video']['fade_duration']},fade=t=out:st={fade_out}:d={config['video']['fade_duration']}",
                seg_path
            ]
            r2 = subprocess.run(cmd2, capture_output=True, timeout=30)
            if r2.returncode == 0:
                segment_files.append(seg_path)
                logger.info(f"  [{i+1}/{len(segments)}] {name} (static)")
        
        current_time = end_time
    
    if not segment_files:
        logger.error("没有成功生成任何分段")
        return None
    
    concat_file = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}_concat.txt")
    with open(concat_file, 'w', encoding='utf-8') as f:
        for seg in segment_files:
            f.write(f"file '{seg.replace('\\\\\\\\', '/')}'\n")
    
    no_audio_video = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}_no_audio.mp4")
    cmd = [ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c:v', 'copy', no_audio_video]
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    if r.returncode != 0:
        logger.error("画面合成失败")
        return None
    
    # 字幕叠加：FFmpeg drawtext实时渲染（秒级完成）
    subtitles = []
    with open(srt_path, 'r', encoding='utf-8') as f:
        blocks = f.read().strip().split('\n\n')
        for block in blocks:
            parts = block.split('\n')
            if len(parts) >= 3:
                time_str = parts[1]
                text = '\n'.join(parts[2:])
                start_str, end_str = time_str.split(' --> ')
                def parse_ts(ts):
                    h, m, rest = ts.split(':')
                    s, ms = rest.split(',')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
                subtitles.append((parse_ts(start_str), parse_ts(end_str), text.strip()))
    
    FONTFILE = "C\\:\\\\Windows\\\\Fonts\\\\msyh.ttc"
    subtitle_y = config['video']['subtitle_y']
    
    filter_parts = []
    for i, (start, end, text) in enumerate(subtitles):
        escaped = text.replace("'", "\\'")
        filter_parts.append(
            "drawtext=text='" + escaped + "':"
            "fontfile='" + FONTFILE + "':"
            "fontsize=28:fontcolor=white:"
            "box=1:boxcolor=black@0.5:boxborderw=8:"
            "x=(w-text_w)/2:y=h-" + str(subtitle_y) + ":"
            "enable=between(t\\," + str(start) + "\\," + str(end) + ")"
        )
    
    vf = ','.join(filter_parts)
    
    sub_video = os.path.join(DATA_DIR, 'cache', f"{config['video_id']}_sub.mp4")
    cmd = [
        ffmpeg, '-y',
        '-i', no_audio_video,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', str(config['video']['crf']),
        '-pix_fmt', 'yuv420p', '-r', str(config['video']['fps']),
        '-vf', vf,
        '-c:a', 'copy',
        sub_video
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    
    if r.returncode != 0:
        err = r.stderr[-500:] if r.stderr else b''
        with open(os.path.join(DATA_DIR, 'cache', 'sub_err.txt'), 'wb') as ef:
            ef.write(err)
        logger.warning("字幕渲染失败，使用无字幕版本")
        sub_video = no_audio_video
    
    # 合入音频
    cmd = [
        ffmpeg, '-y', '-i', sub_video, '-i', audio_path,
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', video_path
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    
    if r.returncode == 0:
        sz = os.path.getsize(video_path) / 1024
        logger.info(f"视频已合成: {video_path} ({sz:.0f}KB, {sz/1024:.1f}MB)")
    else:
        logger.error("视频合成失败")
        return None
    
    # 清理
    import shutil
    shutil.rmtree(segment_dir, ignore_errors=True)
    try: os.remove(no_audio_video)
    except: pass
    try: os.remove(sub_video)
    except: pass
    try: os.remove(concat_file)
    except: pass
    
    return video_path
