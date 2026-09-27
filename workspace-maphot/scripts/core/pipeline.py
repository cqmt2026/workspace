# -*- coding: utf-8 -*-
"""
地图热点流水线 v3 - 模块化编排器
职责：编排各模块化入口，完成 选题→脚本→地图→配音→调色→视频合成→发布 全流程

用法：
  python pipeline.py shenzhen              # 完整流水线
  python pipeline.py shenzhen --skip-llm   # 跳过LLM，使用模板拼接
  python pipeline.py shenzhen --step 3     # 从第3步开始（地图绘制）
  python pipeline.py shenzhen --step 4-5   # 只跑第4-5步

工具集成：
  - video-use: 调色 grade.py（位于 ../video-use/helpers/）
  - cutmv-video-tool: 裁剪/压缩（位于 ../cutmv-video-tool/）
  - deconstruct: 抖音视频拆解引擎（modules/deconstruct.py）

竞品拆解能力：
  在选题采集阶段，可自动调用抖音视频拆解引擎分析竞品视频结构：
  python -c "from modules.deconstruct import deconstruct_video; print(deconstruct_video('https://v.douyin.com/xxx/'))"
  python -c "from modules.deconstruct import generate_template_from_video; print(generate_template_from_video('https://v.douyin.com/xxx/'))"
"""

import io
import os
import sys
import json
import logging
import argparse
import time
import subprocess
import random
from datetime import datetime

# 确保模块目录和核心目录在路径中
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'pipeline.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("maphot.pipeline")

# ============================================================
# 重试装饰器
# ============================================================
def retry(max_attempts=3, delay=1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(f"  [{func.__name__}] 第{attempt}次尝试成功")
                    return result
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts:
                        logger.warning(f"  [{func.__name__}] 第{attempt}次失败: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"  [{func.__name__}] 重试{max_attempts}次后仍失败: {e}")
            raise last_error
        return wrapper
    return decorator


# ============================================================
# 步骤1: 选题采集
# ============================================================
def step_collect_topics():
    """步骤1: 采集今日热点选题"""
    logger.info("=" * 50)
    logger.info("步骤1: 选题采集")
    logger.info("=" * 50)
    
    try:
        from 选题采集_v3 import fetch_baidu, merge_and_rank
        topics = collect_topics_v3(max_items=15)
        logger.info(f"选题采集完成: {len(topics)}条")
        return topics
    except Exception as e:
        logger.error(f"选题采集失败: {e}")
        return []


# ============================================================
# 步骤2: 脚本生成
# ============================================================
def step_generate_script(title, data_list, category="一张图", skip_llm=False, video_id=None):
    """步骤2: 生成口播脚本"""
    logger.info("=" * 50)
    logger.info(f"步骤2: 脚本生成 - {title}")
    logger.info("=" * 50)

    try:
        from modules.llm_client import GatewayLLMClient, FallbackLLMClient
        from modules.prompt_builder import PromptBuilder

        pb = PromptBuilder()
        prompt = pb.build(title, data_list, category)

        if skip_llm:
            logger.info("使用模板拼接模式（跳过LLM）")
            script = FallbackLLMClient().generate(prompt, title, data_list, category)
        else:
            logger.info("调用 LLM 生成脚本...")
            client = GatewayLLMClient()
            script = client.generate(prompt, title, data_list, category)

        # 转换为 TTS 兼容格式（必须在保存之前）
        if 'segments' not in script or not script.get('segments'):
            script['segments'] = []
            hook = script.get('hook', {})
            if hook.get('text'):
                script['segments'].append({'narration': hook['text']})
            for sec in script.get('sections', []):
                script['segments'].append({
                    'narration': sec.get('narration', ''),
                    'data_point': sec.get('data_point', ''),
                    'interpretation': sec.get('interpretation', '')
                })
            outro = script.get('outro', {})
            if outro.get('text'):
                script['segments'].append({'narration': outro['text']})
            logger.info(f"脚本格式转换: {len(script['segments'])}段")

        # 保存脚本到 data/scripts/
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(DATA_DIR, "scripts", f"{title}_{ts}.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

        # 统计字数和时长
        full_text = script.get('full_text', '')
        word_count = len(full_text)
        duration = script.get('metadata', {}).get('estimated_duration_seconds', word_count * 60 / 90)
        logger.info(f"脚本字数: {word_count}字, 预计时长: {duration:.1f}s")
        logger.info(f"脚本已保存: {output_path}")
        return script, output_path
    except Exception as e:
        logger.error(f"脚本生成失败: {e}")
        return None, None



# ============================================================
# 步骤3: 地图绘制
# ============================================================
@retry(max_attempts=2, delay=2.0)
def step_draw_maps(video_id, config=None, output_dir=None):
    """步骤3: 生成地图帧图（优先使用 MapMgr 注册表）"""
    logger.info("=" * 50)
    logger.info(f"步骤3: 地图绘制 - {video_id}")
    logger.info("=" * 50)

    try:
        if not config:
            from config_loader import load_config
            config = load_config(video_id)

        # P3: 尝试使用 MapMgr（注册表模式）
        try:
            from modules.map_mgr import MapMgr
            mgr = MapMgr(style="direct", output_dir=output_dir)
            
            # 构建 ScriptSegment 列表
            districts = config.get('districts', [])
            city = config.get('city', '')
            title = config.get('title', video_id)
            
            segments = []
            if districts and city:
                # 城市多区模式
                for i, d in enumerate(districts):
                    from modules.schemas import ScriptSegment
                    seg = ScriptSegment(
                        id=f"seg_{i:03d}",
                        technique="地图定位",
                        text=d.get('desc', d.get('name', '')),
                        map_instruction=f"{city} · {d.get('name','')} 区域高亮",
                        duration_seconds=8,
                        highlight_data={'name': d.get('name', ''), 'value': d.get('gdp', '')},
                        all_provinces=[{'name': dd.get('name',''), 'value': dd.get('gdp','')} for dd in districts],
                        title=f"{city} · {d.get('name','')}",
                        subtitle=d.get('desc', ''),
                    )
                    segments.append(seg)
            elif config.get('provinces_data') or config.get('data_list'):
                # 省份排名模式
                from modules.schemas import ScriptSegment
                provinces = config.get('provinces_data') or config.get('data_list', [])
                seg = ScriptSegment(
                    id="seg_000",
                    technique="榜单展示",
                    text=title,
                    map_instruction="全国俯瞰图 省份排名",
                    duration_seconds=10,
                    highlight_data={'name': provinces[0].get('name','') if provinces else ''},
                    all_provinces=provinces,
                    title=title,
                )
                segments.append(seg)
            
            if segments:
                results = mgr.draw_all(segments)
                frames = []
                for r in results:
                    for mf in r.output_files:
                        frames.append(mf.path)
                logger.info(f"MapMgr 绘制完成: {len(frames)}帧")
                return frames
        except Exception as e:
            logger.warning(f"MapMgr 绘制失败 ({e}), 回退到直接调用")
        
        # 回退：直接调用 ProvinceMapDrawer
        from modules.province_map_drawer import ProvinceMapDrawer
        drawer = ProvinceMapDrawer(style="direct")
        
        city = config.get('city', '')
        districts = config.get('districts', [])
        title = config.get('title', video_id)
        
        if districts and city:
            frames = []
            for d in districts:
                out_filename = f"{city}_{d.get('name','')}_map_v3.png"
                out_path = os.path.join(output_dir, out_filename) if output_dir else None
                frame = drawer.draw_province_map(
                    provinces_data=[d],
                    highlight_name=d.get('name', ''),
                    output_path=out_path,
                    map_title=f"{city} · {d.get('name','')}",
                    map_subtitle=d.get('desc', '')
                )
                if frame and output_dir:
                    frames.append(out_path)
            logger.info(f"城市多区地图绘制完成: {len(frames)}帧")
        else:
            provinces_data = config.get('provinces_data', [])
            if not provinces_data and config.get('data_list'):
                provinces_data = config.get('data_list', [])
            if provinces_data:
                out_path = os.path.join(output_dir, "map_rank.png") if output_dir else None
                drawer.draw_rank_map(provinces_data, output_path=out_path, title=title)
                frames = [out_path] if out_path else []
            else:
                frames = []
            logger.info(f"省份排名地图绘制完成: {len(frames)}帧")

        logger.info(f"地图绘制完成: {len(frames)}帧, 输出目录: {output_dir}")
        return frames
    except Exception as e:
        logger.error(f"地图绘制失败: {e}")
        import traceback
        traceback.print_exc()
        return []


# ============================================================
# 步骤4: 配音生成
# ============================================================
@retry(max_attempts=2, delay=2.0)
def step_generate_audio(script_path, category="一张图", video_id=None):
    """步骤4: TTS配音生成"""
    logger.info("=" * 50)
    logger.info(f"步骤4: 配音生成 - {os.path.basename(script_path)}")
    logger.info("=" * 50)
    
    try:
        from modules.tts_generator import TtsGenerator
        
        generator = TtsGenerator()
        output_path = generator.generate_from_script(script_path, category=category, video_id=video_id)
        
        if output_path:
            logger.info(f"配音已生成: {output_path}")
            return output_path
        else:
            logger.error("配音生成失败")
            return None
    except Exception as e:
        logger.error(f"配音生成异常: {e}")
        return None


# ============================================================
# 步骤4a: 素材裁剪/压缩（cutmv-video-tool）
# ============================================================
@retry(max_attempts=2, delay=2.0)
def step_cut_video(input_path, start_time=None, end_time=None, output_path=None):
    """
    步骤4a: 使用 cutmv-video-tool 裁剪/压缩视频素材
    依赖：cutmv-video-tool 已安装（位于 ../cutmv-video-tool/skill.py）
    """
    logger.info("=" * 50)
    logger.info(f"步骤4a: 素材裁剪 - {os.path.basename(input_path)}")
    logger.info("=" * 50)

    if not input_path or not os.path.exists(input_path):
        logger.error("输入文件不存在，跳过裁剪")
        return input_path

    cutmv_script = os.path.join(BASE_DIR, 'cutmv-video-tool', 'skill.py')
    if not os.path.exists(cutmv_script):
        logger.warning(f"cutmv-video-tool 未找到 ({cutmv_script})，跳过裁剪")
        return input_path

    try:
        if not output_path:
            name, ext = os.path.splitext(os.path.basename(input_path))
            output_path = os.path.join(os.path.dirname(input_path), f"{name}_cut{ext}")

        if start_time is not None and end_time is not None:
            cmd = [sys.executable, cutmv_script, 'cut', input_path, output_path, str(start_time), str(end_time)]
        else:
            # 仅压缩
            cmd = [sys.executable, cutmv_script, 'compress', input_path, output_path, '1000k']

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and os.path.exists(output_path):
            orig_sz = os.path.getsize(input_path) / 1024 / 1024
            new_sz = os.path.getsize(output_path) / 1024 / 1024
            logger.info(f"裁剪/压缩完成: {output_path} ({orig_sz:.1f}MB → {new_sz:.1f}MB)")
            return output_path
        else:
            logger.warning(f"裁剪失败 (rc={r.returncode})，使用原文件")
            return input_path
    except Exception as e:
        logger.error(f"裁剪异常: {e}")
        return input_path


# ============================================================
# 步骤4b: 调色（video-use grade.py）
# ============================================================
@retry(max_attempts=2, delay=2.0)
def step_grade_video(video_path, config=None):
    """
    步骤4b: 使用 video-use 的 grade.py 进行调色
    依赖：video-use 已安装（位于 ../video-use/helpers/grade.py）
    """
    logger.info("=" * 50)
    logger.info(f"步骤4b: 调色 - {os.path.basename(video_path)}")
    logger.info("=" * 50)

    if not video_path or not os.path.exists(video_path):
        logger.error("视频文件不存在，跳过调色")
        return video_path

    grade_script = os.path.join(BASE_DIR, 'video-use', 'helpers', 'grade.py')
    if not os.path.exists(grade_script):
        logger.warning(f"video-use grade.py 未找到 ({grade_script})，跳过调色")
        return video_path

    try:
        output_path = video_path.replace('.mp4', '_graded.mp4')
        cmd = [
            sys.executable, grade_script,
            video_path,
            '-o', output_path
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and os.path.exists(output_path):
            sz = os.path.getsize(output_path) / 1024 / 1024
            logger.info(f"调色完成: {output_path} ({sz:.1f}MB)")
            return output_path
        else:
            logger.warning(f"调色失败 (rc={r.returncode})，使用原视频")
            return video_path
    except Exception as e:
        logger.error(f"调色异常: {e}")
        return video_path


# ============================================================
# 步骤5: 视频合成（FFmpeg drawtext方案）
# ============================================================
@retry(max_attempts=2, delay=2.0)
def step_compose_video(video_id, script_path, audio_path, frames, config=None):
    """步骤5: 合成视频（FFmpeg分段+drawtext字幕+音频）"""
    # 注意：此步骤已不再默认使用，优先使用 HyperFrames 渲染（步骤5b）
    logger.info("=" * 50)
    logger.info(f"步骤5: 视频合成 - {video_id}")
    logger.info("=" * 50)
    
    if not config:
        from config_loader import load_config
        config = load_config(video_id)
    
    if not audio_path or not os.path.exists(audio_path):
        logger.error("配音文件不存在")
        return None
    
    if not frames:
        logger.error("帧图为空")
        return None
    
    ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
    
    # 读取脚本
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    # 构建段落列表
    segments = []
    # 钩子
    segments.append(("hook", script.get('hook', {}).get('text', '')))
    # 各段
    for s in script.get('sections', []):
        segments.append((s.get('order', 0), s.get('narration', '')))
    # 结尾
    segments.append(("outro", script.get('outro', {}).get('text', '')))
    
    # 获取音频时长
    dur_result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
        capture_output=True, text=True, timeout=10
    )
    total_duration = float(dur_result.stdout.strip()) if dur_result.stdout else 120
    total_chars = sum(len(str(t)) for _, t in segments)
    if total_chars == 0:
        total_chars = 1
    
    # 生成逐段视频
    segment_dir = os.path.join(DATA_DIR, 'cache', f"{video_id}_segments")
    os.makedirs(segment_dir, exist_ok=True)
    
    segment_files = []
    current_time = 0.0
    
    for i, (name, text) in enumerate(segments):
        if not text:
            continue
        
        ratio = len(str(text)) / total_chars
        seg_dur = max(1.0, total_duration * ratio)
        end_time = current_time + seg_dur
        
        # 匹配帧图
        img_path = None
        for fr in frames:
            fr_name = fr[0] if isinstance(fr, tuple) else fr.get('name', '')
            if str(fr_name) == str(name):
                img_path = fr[1] if isinstance(fr, tuple) else fr.get('path', '')
                break
        if not img_path and frames:
            img_path = frames[0][1] if isinstance(frames[0], tuple) else frames[0].get('path', '')
        if not img_path or not os.path.exists(img_path):
            current_time = end_time
            continue
        
        seg_path = os.path.join(segment_dir, f"seg_{i:03d}_{name}.mp4")
        fade_out = max(0, seg_dur - 0.5)
        fade_dur = config.get('video', {}).get('fade_duration', 0.5)
        fps = config.get('video', {}).get('fps', 15)
        crf = config.get('video', {}).get('crf', 18)
        
        # 尝试zoompan+淡入淡出
        vf_filter = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920,"
            f"fps={fps},"
            f"fade=t=in:st=0:d={fade_dur},"
            f"fade=t=out:st={fade_out}:d={fade_dur}"
        )
        
        cmd = [
            ffmpeg, '-y', '-loop', '1', '-i', img_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', str(crf),
            '-pix_fmt', 'yuv420p', '-r', str(fps), '-t', str(seg_dur),
            '-vf', vf_filter, seg_path
        ]
        
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            r = type('obj', (object,), {'returncode': -1})()
        
        if r.returncode == 0:
            segment_files.append(seg_path)
            logger.info(f"  [{i+1}/{len(segments)}] {name} ({seg_dur:.1f}s)")
        else:
            # fallback 无zoompan
            vf_simple = (
                f"scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,"
                f"fade=t=in:st=0:d={fade_dur},"
                f"fade=t=out:st={fade_out}:d={fade_dur}"
            )
            cmd2 = [
                ffmpeg, '-y', '-loop', '1', '-i', img_path,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', str(crf),
                '-pix_fmt', 'yuv420p', '-r', str(fps), '-t', str(seg_dur),
                '-vf', vf_simple, seg_path
            ]
            try:
                r2 = subprocess.run(cmd2, capture_output=True, timeout=60)
                if r2.returncode == 0:
                    segment_files.append(seg_path)
                    logger.info(f"  [{i+1}/{len(segments)}] {name} (static)")
            except:
                pass
        
        current_time = end_time
    
    if not segment_files:
        logger.error("没有成功生成任何分段")
        return None
    
    # 拼接
    concat_file = os.path.join(DATA_DIR, 'cache', f"{video_id}_concat.txt")
    with open(concat_file, 'w', encoding='utf-8') as f:
        for seg in segment_files:
            f.write(f"file '{seg.replace(os.sep, '/')}'\n")
    
    no_audio_video = os.path.join(DATA_DIR, 'cache', f"{video_id}_no_audio.mp4")
    try:
        cmd = [ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c:v', 'copy', no_audio_video]
        subprocess.run(cmd, capture_output=True, timeout=120)
    except:
        logger.error("画面拼接失败")
        return None
    
    # 生成字幕（从脚本subtitle_lines）
    srt_path = os.path.join(DATA_DIR, 'cache', f"{video_id}.srt")
    _generate_srt(script, srt_path, segments, total_duration, total_chars)
    
    # drawtext字幕叠加
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
    subtitle_y = config.get('video', {}).get('subtitle_y', 200)
    
    filter_parts = []
    for start, end, text in subtitles:
        escaped = text.replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            f"drawtext=text='{escaped}':"
            f"fontfile='{FONTFILE}':"
            f"fontsize=28:fontcolor=white:"
            f"box=1:boxcolor=black@0.5:boxborderw=8:"
            f"x=(w-text_w)/2:y=h-{subtitle_y}:"
            f"enable='between(t,{start},{end})'"
        )
    
    vf = ','.join(filter_parts)
    
    sub_video = os.path.join(DATA_DIR, 'cache', f"{video_id}_sub.mp4")
    cmd = [
        ffmpeg, '-y', '-i', no_audio_video,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', str(config.get('video', {}).get('crf', 18)),
        '-pix_fmt', 'yuv420p', '-vf', vf, '-c:a', 'copy', sub_video
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    
    if r.returncode != 0:
        logger.warning("字幕渲染失败，使用无字幕版本")
        sub_video = no_audio_video
    
    # 合入音频
    video_path = os.path.join(DATA_DIR, 'videos', config.get('output', {}).get('video_file', f'{video_id}_final.mp4'))
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    cmd = [
        ffmpeg, '-y', '-i', sub_video, '-i', audio_path,
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', video_path
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    
    if r.returncode == 0:
        sz = os.path.getsize(video_path) / 1024
        logger.info(f"视频已合成: {video_path} ({sz:.0f}KB, {sz/1024:.1f}MB)")
    else:
        logger.error("视频合成失败")
        return None
    
    # 清理
    import shutil
    shutil.rmtree(segment_dir, ignore_errors=True)
    for f in [no_audio_video, sub_video, concat_file, srt_path]:
        try: os.remove(f)
        except: pass
    
    return video_path


def _generate_srt(script, srt_path, segments, total_duration, total_chars):
    """从脚本生成SRT字幕"""
    with open(srt_path, 'w', encoding='utf-8') as f:
        current_time = 0.0
        idx = 1
        
        for name, text in segments:
            if not text:
                continue
            ratio = len(str(text)) / total_chars
            dur = max(1.0, total_duration * ratio)
            end_time = current_time + dur
            
            def ts_str(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
            f.write(f"{idx}\n")
            f.write(f"{ts_str(current_time)} --> {ts_str(end_time)}\n")
            f.write(f"{text}\n\n")
            
            current_time = end_time
            idx += 1


# ============================================================
# 一站式流水线
# ============================================================
def run_pipeline(video_id, skip_llm=False, step_range=None, quality='draft'):
    """
    运行完整流水线（HyperFrames渲染）

    数据流：用 ctx 字典在步骤间传递明确路径，不靠文件名模糊匹配
    """
    from config_loader import load_config, validate_config

    config = load_config(video_id)
    ok, issues = validate_config(config)
    if not ok:
        logger.error(f"配置验证失败: {issues}")
        return False

    # 统一上下文：步骤间通过明确路径传递数据
    ctx = {
        'video_id': video_id,
        'config': config,
        'topics': [],           # 步骤1 产出
        'script_path': None,    # 步骤2 产出
        'audio_path': None,     # 步骤4 产出
        'maps_dir': None,       # 步骤3 产出
        'output_path': None,    # 步骤5 产出
    }

    # 素材匹配（新增：根据文案自动匹配Pixabay素材）
    _match_and_overlay_materials(video_id, config)

    logger.info(f"\n{'='*60}")
    logger.info(f"地图热点流水线启动: {video_id} - {config.get('title', '')}")
    logger.info(f"{'='*60}")

    def _run_collect():
        ctx['topics'] = step_collect_topics()
        return ctx['topics']

    def _run_script():
        title = config.get('title', '未命名')
        category = config.get('category', '深一度')
        districts = config.get('districts', [])
        data_list = [{
            'rank': i + 1, 'name': d.get('name', ''),
            'data1': d.get('gdp', ''), 'data2': d.get('tag', ''),
            'desc': d.get('desc', ''), 'pct': d.get('pct', ''),
            'per_gdp': d.get('per_gdp', '')
        } for i, d in enumerate(districts)]
        script, path = step_generate_script(title, data_list, category, skip_llm, video_id=video_id)
        ctx['script_path'] = path
        return path

    def _run_maps():
        date_str = datetime.now().strftime('%Y%m%d')
        out_dir = os.path.join(DATA_DIR, 'maps', date_str)
        frames = step_draw_maps(video_id, config, output_dir=out_dir)
        ctx['maps_dir'] = out_dir
        return frames

    def _run_audio():
        if not ctx['script_path'] or not os.path.exists(ctx['script_path']):
            logger.error(f"脚本文件不存在: {ctx['script_path']}")
            return None
        category = config.get('category', '深一度')
        path = step_generate_audio(ctx['script_path'], category, video_id=video_id)
        if path and os.path.exists(path):
            ctx['audio_path'] = path
        return path

    def _run_grade():
        """调色步骤"""
        output = ctx.get('output_path')
        if not output or not os.path.exists(output):
            logger.info("视频尚未合成，跳过调色（渲染后自动调色）")
            return None
        graded = step_grade_video(output, config)
        if graded and graded != output:
            ctx['output_path'] = graded
        return graded

    def _run_video():
        audio = ctx['audio_path']
        maps = ctx['maps_dir']
        if not audio or not os.path.exists(audio):
            logger.error(f"音频文件不存在: {audio}")
            return None
        if not maps or not os.path.exists(maps):
            logger.error(f"地图目录不存在: {maps}")
            return None
        path = _step_hyperframes(video_id, config, quality, audio_path=audio, maps_dir=maps)
        ctx['output_path'] = path
        return path

    steps = {
        1: ("选题采集", _run_collect),
        2: ("脚本生成", _run_script),
        3: ("地图绘制", _run_maps),
        4: ("配音生成", _run_audio),
        4.5: ("调色", _run_grade),
        5: ("视频合成", _run_video),
    }

    start, end = step_range or (1, 5)

    for step_num in range(start, end + 1):
        if step_num not in steps:
            logger.warning(f"步骤{step_num}不存在，跳过")
            continue

        step_name, step_func = steps[step_num]
        logger.info(f"\n>>> 步骤{step_num}/{end}: {step_name}")

        try:
            result = step_func()
            if result is None and step_num >= 3:
                logger.error(f"步骤{step_num}失败，流水线终止")
                return False
            logger.info(f"<<< 步骤{step_num}完成")
        except Exception as e:
            logger.error(f"步骤{step_num}异常: {e}")
            if step_num >= 3:
                return False

    logger.info(f"\n{'='*60}")
    logger.info(f"流水线执行完成 ✅  输出: {ctx['output_path']}")
    logger.info(f"{'='*60}")
    return True


def _step_script(config, skip_llm):
    """脚本生成步骤的内部封装"""
    title = config.get('title', '未命名')
    category = config.get('category', '深一度')
    video_id = config.get('video_id', '')
    
    # 从config构建data_list
    districts = config.get('districts', [])
    data_list = []
    for i, d in enumerate(districts):
        data_list.append({
            'rank': i + 1,
            'name': d.get('name', ''),
            'data1': d.get('gdp', ''),
            'data2': d.get('tag', ''),
            'desc': d.get('desc', ''),
            'tag': d.get('tag', '')
        })
    
    script, path = step_generate_script(title, data_list, category, skip_llm, video_id=video_id)
    if path:
        # 保存脚本路径供后续步骤使用
        _cache_script_path(config['video_id'], path)
    return path


def _step_audio(config, skip_llm):
    """配音步骤的内部封装"""
    video_id = config['video_id']
    script_path = _get_cached_script_path(video_id)
    if not script_path or not os.path.exists(script_path):
        logger.error(f"脚本文件不存在: {script_path}")
        return None
    
    category = config.get('category', '深一度')
    return step_generate_audio(script_path, category)


def _step_video(video_id, config, skip_llm):
    """视频合成步骤（已废弃，改用 HyperFrames）"""
    logger.error("_step_video 已废弃，请使用 HyperFrames 渲染（默认）")
    return None
    
    
    
    return step_compose_video(video_id, script_path, audio_path, frames, config)


# ============================================================
# 步骤5b: HyperFrames渲染
# ============================================================
@retry(max_attempts=2, delay=2.0)
def _step_hyperframes(video_id, config, quality='draft', audio_path=None, maps_dir=None):
    """
    步骤5b: 使用HyperFrames渲染视频

    Args:
        video_id: 视频ID
        config: 城市配置
        quality: 渲染质量
        audio_path: 音频文件绝对路径（明确传入，不再搜索）
        maps_dir: 地图帧图目录绝对路径（明确传入，不再搜索日期）
    """
    logger.info("=" * 50)
    logger.info("步骤5b: HyperFrames渲染")
    logger.info("=" * 50)

    # 提前定义 hf_dir（BGM 轮换需要用到）
    hf_dir = os.path.join(BASE_DIR, 'my-video')
    os.makedirs(hf_dir, exist_ok=True)

    # 1. 题材分类与模板匹配（新增）
    title = config.get('title', video_id)
    subtitle = config.get('subtitle', '')
    data_list = config.get('data_list', [])
    
    # 尝试从 MatchMakerV2 自动选择模板
    from match_maker_v2 import MatchMakerV2
    match_config = MatchMakerV2.to_render_config(title, subtitle, data_list)
    auto_type = match_config.get('video_type', 'city')
    auto_template = match_config.get('template', 'hyperframes_template')
    
    logger.info(f"题材分类: {match_config.get('topic_type', 'unknown')}")
    logger.info(f"自动模板: {auto_template}")
    logger.info(f"分类置信度: {match_config.get('classify_info', {}).get('confidence', 0):.0%}")
    
    # 城市多区数据优先用 city 模板
    districts = config.get('districts', [])
    if districts and len(districts) >= 3:
        video_type = 'city'
    else:
        video_type = config.get('video_type', auto_type)

    # P1-B: 完整模板映射（match_maker_v2 → generate_html）
    TEMPLATE_MAP = {
        'city': ('hyperframes_template', 'generate_html'),
        'ranking': ('hyperframes_ranking_v43', 'generate_html'),
        'comparison': ('hyperframes_ranking_v43', 'generate_comparison_html'),
        'single_event': ('hyperframes_flow', 'generate_html'),
        'industry_analysis': ('hyperframes_industry', 'generate_html'),
        'historical_geo': ('hyperframes_institution', 'generate_html'),
        'population_flow': ('hyperframes_flow', 'generate_html'),
        'policy_effect': ('hyperframes_policy', 'generate_html'),
    }
    tpl_module_name, tpl_func_name = TEMPLATE_MAP.get(video_type, ('hyperframes_template', 'generate_html'))
    logger.info(f"使用模板: {tpl_module_name}.{tpl_func_name} (video_type={video_type})")
    
    # 2. 准备数据（支持城市多区和省份排名两种模式）
    category = config.get('category', '深一度')

    # 2b. 提前获取音频时长（在 HTML 生成之前）
    audio_dur = None
    if audio_path and os.path.exists(audio_path):
        try:
            r = subprocess.run(['ffmpeg', '-i', audio_path], capture_output=True, text=True, timeout=10)
            for _line in r.stderr.split('\n'):
                if 'Duration' in _line:
                    import re as _re2
                    m2 = _re2.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', _line)
                    if m2:
                        h, mi, s, ms = int(m2.group(1)), int(m2.group(2)), int(m2.group(3)), int(m2.group(4).ljust(2,'0')[:2])
                        audio_dur = h * 3600 + mi * 60 + s + ms / 100
                        logger.info(f"音频时长: {audio_dur:.1f}s")
                    break
        except Exception as e:
            logger.warning(f"获取音频时长失败: {e}")
    if audio_dur is None:
        logger.warning("无法获取音频时长，视频将使用默认长度")

    # P1-B: 动态模板加载（支持全部8种题材类型）
    try:
        tpl_module = __import__(tpl_module_name, fromlist=[tpl_func_name])
        generate_html_fn = getattr(tpl_module, tpl_func_name)
    except Exception as e:
        logger.error(f"模板导入失败 {tpl_module_name}.{tpl_func_name}: {e}，回退到 hyperframes_template")
        tpl_module_name = 'hyperframes_template'
        tpl_func_name = 'generate_html'
        tpl_module = __import__('hyperframes_template', fromlist=['generate_html'])
        generate_html_fn = tpl_module.generate_html

    # 构建通用配置（各模板共用字段）
    districts = config.get('districts', [])
    common_config = {
        'city': config.get('city', video_id),
        'title': config.get('title', video_id),
        'subtitle': config.get('subtitle', ''),
        'year': '2026',
        'total_gdp': config.get('total_gdp', ''),
        'gdp_rank': config.get('gdp_rank', ''),
        'area': config.get('area', ''),
        'population': config.get('population', ''),
        'districts': [
            {
                'name': d.get('name', ''),
                'gdp': d.get('gdp', d.get('tag', '')),
                'gdp_raw': d.get('gdp_raw', 0),
                'per_gdp': d.get('per_gdp', ''),
                'pct': d.get('pct', ''),
                'desc': d.get('desc', ''),
                'tag': d.get('tag', '')
            }
            for d in districts
        ],
        'topic': config.get('topic', video_id),
        'badge_text': config.get('badge_text', ''),
        'badge_unit': config.get('badge_unit', ''),
        'map_image': config.get('map_image', ''),
    }
    # 城市多区特有的 opt_a/b/c
    if districts:
        common_config['opt_a'] = config.get('opt_a', districts[0].get('name','')+' — 实力最强')
        common_config['opt_b'] = config.get('opt_b', districts[1].get('name','')+' — 潜力最大' if len(districts)>1 else '')
        common_config['opt_c'] = config.get('opt_c', districts[2].get('name','')+' — 后起之秀' if len(districts)>2 else '')
    # ranking 特有字段
    if video_type in ('ranking', 'comparison'):
        common_config.update({
            'ring_value': config.get('ring_value', 0),
            'ring_label': config.get('ring_label', ''),
            'south_label': config.get('south_label', ''),
            'north_label': config.get('north_label', ''),
            'south_val': config.get('south_val', ''),
            'north_val': config.get('north_val', ''),
            'south_rank': config.get('south_rank', ''),
            'north_rank': config.get('north_rank', ''),
            'reasons': config.get('reasons', []),
            'outro_question': config.get('outro_question', ''),
            'outro_sub': config.get('outro_sub', ''),
            'options': config.get('options', []),
            'cta_text': config.get('cta_text', '点赞关注，每天看数据'),
        })
        if video_type == 'comparison':
            common_config['anomaly_highlight'] = config.get('anomaly_highlight')
            common_config['ranking_data'] = data_list


    # P2-B: BGM 轮换（从 data/audio/ 随机选择）
    import glob as _glob
    bgm_dir = os.path.join(BASE_DIR, 'data', 'audio')
    bgm_files = _glob.glob(os.path.join(bgm_dir, 'bgm_*.mp3'))
    if bgm_files:
        selected_bgm = random.choice(bgm_files)
        bgm_relpath = os.path.relpath(selected_bgm, hf_dir).replace('\\', '/')
        logger.info(f"BGM 轮换: {os.path.basename(selected_bgm)}")
    else:
        bgm_relpath = None
        logger.warning("未找到 BGM 文件")

    html = generate_html_fn(common_config, audio_duration=audio_dur)
    logger.info(f"模板 {tpl_module_name}.{tpl_func_name} 生成完成")

    # 保存配置JSON
    # hf_dir 已在函数开头定义
    config_save_path = os.path.join(hf_dir, f'{video_type}_config.json')
    with open(config_save_path, 'w', encoding='utf-8') as f:
        json.dump(common_config, f, ensure_ascii=False, indent=2)
    logger.info(f"配置已保存: {config_save_path}")

    # 3. 复制地图素材到 my-video
    hf_maps_dir = os.path.join(hf_dir, 'assets', 'maps')
    if maps_dir and os.path.exists(maps_dir):
        import shutil
        os.makedirs(hf_maps_dir, exist_ok=True)
        # 清掉旧素材
        if os.listdir(hf_maps_dir):
            shutil.rmtree(hf_maps_dir)
            os.makedirs(hf_maps_dir, exist_ok=True)
        for f in os.listdir(maps_dir):
            if f.endswith('.png'):
                shutil.copy2(os.path.join(maps_dir, f), os.path.join(hf_maps_dir, f))
        logger.info(f"地图素材已复制: {maps_dir} -> {hf_maps_dir} ({len([x for x in os.listdir(hf_maps_dir) if x.endswith('.png')])} 张)")
    else:
        logger.error(f"地图素材不存在: maps_dir={maps_dir}")
        return None

    # 4. 复制音频素材到 my-video
    hf_audio_dir = os.path.join(hf_dir, 'assets')
    hf_audio_path = os.path.join(hf_audio_dir, 'audio.mp3')
    if audio_path and os.path.exists(audio_path):
        import shutil
        os.makedirs(hf_audio_dir, exist_ok=True)
        shutil.copy2(audio_path, hf_audio_path)
        logger.info(f"音频已复制: {audio_path}")
    else:
        logger.error(f"音频文件不存在: audio_path={audio_path}")
        return None

    # 5. 生成HTML（使用audio_dur，已在步骤2b获取）
    html_path = os.path.join(hf_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        # 替换 BGM 路径
        if 'bgm_relpath' in dir() and bgm_relpath:
            html = html.replace('assets/bgm_random.mp3', bgm_relpath)
        f.write(html)
    logger.info(f"HTML已生成: {html_path}")

    # 7. 调用HyperFrames渲染
    output_name = f"{video_id}_final.mp4"
    output_path = os.path.join(hf_dir, output_name)

    # ---- P0-A: 渲染模式自动选择（视频数>3用截图模式，稳定但慢） ----
    video_count = 0
    try:
        import re as _re
        html_src = html if isinstance(html, str) else open(html_path, encoding='utf-8').read()
        video_count = len(_re.findall(r'<video[^>]*src=', html_src))
    except:
        pass
    capture_mode = '' if video_count <= 3 else ' --experimental-fast-capture=false'
    logger.info(f"检测到 {video_count} 路视频背景 → {'截图模式(稳定)' if video_count > 3 else 'drawElement模式(快速)'}")

    # 构建渲染命令 - 使用node直接调用cli.js（避免npx在Windows上的问题）
    hyperframes_cli = r"C:\Users\Administrator\AppData\Roaming\npm\node_modules\hyperframes\dist\cli.js"
    
    quality_flag = f' --quality {quality}' if quality != 'standard' else ''
    output_flag = f' --output {output_name}'
    no_lmm = ' --no-low-memory-mode' if quality in ('standard', 'high') else ''

    cmd_base = ['node', hyperframes_cli, 'render', quality_flag + capture_mode + output_flag + no_lmm]

    def _try_render(cmd, label):
        try:
            r = subprocess.run(cmd, cwd=hf_dir, capture_output=True, timeout=900)
            ok = r.returncode == 0 and os.path.exists(output_path)
            return r.returncode, ok
        except subprocess.TimeoutExpired:
            return -1, False
        except Exception as e:
            logger.warning(f"  渲染异常({label}): {e}")
            return -1, False

    # 重试策略：先尝试drawElement，失败则加--experimental-fast-capture=false再试
    logger.info(f"开始HyperFrames渲染 (quality={quality}, videos={video_count})...")
    rc, ok = _try_render(cmd_base, 'mode1')
    if not ok:
        logger.warning("drawElement模式失败，切换到截图模式重试...")
        cmd_fallback = cmd_base[:1] + cmd_base[2:]  # 去掉原capture_mode
        cmd_fallback.append('--experimental-fast-capture=false')
        rc, ok = _try_render(cmd_fallback, 'mode2')

    if not ok:
        logger.error("HyperFrames渲染失败（两种模式均失败）")
        return None

    sz = os.path.getsize(output_path) / 1024 / 1024
    logger.info(f"HyperFrames渲染完成: {output_path} ({sz:.1f}MB, {video_count}路视频, 截图模式={'是' if video_count>3 else '否'})")

    # 复制到data/videos
    dest_path = os.path.join(DATA_DIR, 'videos', output_name)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    import shutil
    shutil.copy2(output_path, dest_path)
    logger.info(f"已复制到: {dest_path}")
    return output_path

    logger.error(f"渲染输出文件不存在: {output_path}")
    return None


# ============================================================
# 素材匹配与背景叠加（新增）
# ============================================================
def _match_and_overlay_materials(video_id, config):
    """
    步骤0.5: 文案 → 素材匹配 + 自动叠加
    功能：读取脚本，提取关键词，匹配素材，生成渲染清单
    """
    try:
        from material_matcher import MaterialMatcher
        matcher = MaterialMatcher()
        
        # 读取脚本
        script_path = _get_cached_script_path(video_id)
        if not script_path or not os.path.exists(script_path):
            logger.info("未找到脚本文件，跳过素材匹配")
            return
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
        
        # 构建完整文案
        full_text = script.get('full_text', '')
        if not full_text:
            parts = []
            if script.get('hook', {}).get('text'): parts.append(script['hook']['text'])
            for sec in script.get('sections', []): parts.append(sec.get('narration', ''))
            if script.get('outro', {}).get('text'): parts.append(script['outro']['text'])
            full_text = ' '.join(parts)
        
        if not full_text.strip():
            return
        
        # 估算视频时长
        audio_path = config.get('audio_path')
        video_dur = None
        if audio_path and os.path.exists(audio_path):
            try:
                r = subprocess.run(['ffmpeg','-i',audio_path], capture_output=True, text=True, timeout=10)
                for line in r.stderr.split('\n'):
                    if 'Duration' in line:
                        import re as _re2
                        m2 = _re2.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', line)
                        if m2:
                            h,mi,s,ms = int(m2.group(1)),int(m2.group(2)),int(m2.group(3)),int(m2.group(4).ljust(2,'0')[:2])
                            video_dur = h*3600+mi*60+s+ms/100
                            break
            except:
                pass
        
        # 匹配素材
        result = matcher.build_render_scheme(full_text, video_dur)
        if result['coverage'] >= 0.3:
            logger.info("素材匹配: %.0f%%覆盖 (%d/%d段)" % (result['coverage']*100, result['scheme']['covered_count'], result['scheme']['match_count']))
            # 输出缺失素材提示
            missing = [m for m in result['matches'] if not m['material']]
            if missing:
                logger.info("需补充素材: %d段" % len(missing))
                for seg in missing[:3]:
                    logger.info("  %ds-%ds: %s" % (seg['start'], seg['end'], seg['keywords'][:2]))
        else:
            logger.info("无需素材叠加，纯动画方案")
        
    except Exception as e:
        logger.warning("素材匹配跳过: %s" % str(e)[:80])


def _overlay_materials(video_path):
    """
    步骤7b: 将匹配的素材叠加到已渲染视频
    使用FFmpeg overlay滤镜，在对应时间段叠加背景素材
    """
    try:
        from material_matcher import MaterialMatcher
        matcher = MaterialMatcher()
        
        # 检查是否有待叠加的素材
        pixabay_dir = os.path.join(BASE_DIR, 'trade-circle', 'assets')
        if not os.path.exists(pixabay_dir):
            return video_path
        
        # 查找Pixabay素材
        pix_videos = []
        for f in os.listdir(pixabay_dir):
            if f.endswith('.mp4'):
                pix_videos.append((f, os.path.join(pixabay_dir, f)))
        
        if not pix_videos:
            return video_path
        
        logger.info("找到 %d 个Pixabay素材，准备叠加" % len(pix_videos))
        
        # 简单叠加：最后30%的时间段叠加素材背景
        out_path = video_path.replace('.mp4', '_with_materials.mp4')
        
        # 获取原视频时长
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',video_path],
                          capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace')
        total_dur = float(r.stdout.strip()) if r.stdout.strip() else 55
        
        # 在最后30秒叠加素材
        overlay_start = max(0, total_dur - 30)
        
        # 准备overlay素材（缩放到竖屏）
        bg_idx = 0
        seg_durations = [12, 10, 8]  # 每段素材时长
        bg_paths = []
        for i, (name, path) in enumerate(pix_videos):
            dur = min(seg_durations[i] if i < len(seg_durations) else 10, total_dur - overlay_start)
            bg_out = os.path.join(BASE_DIR, 'data', 'videos', 'bg_overlay_%d.mp4' % i)
            cmd = ['ffmpeg','-y','-i',path,'-vf',
                   'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
                   '-t',str(dur),'-c:v','libx264','-preset','fast','-crf','22','-an',bg_out]
            subprocess.run(cmd, capture_output=True, timeout=60)
            if os.path.exists(bg_out):
                bg_paths.append(bg_out)
        
        if not bg_paths:
            logger.info("无有效叠加素材，输出原始视频")
            return video_path
        
        # concat所有背景素材
        concat_bg = os.path.join(BASE_DIR, 'data', 'videos', 'bg_concat.txt')
        with open(concat_bg, 'w', encoding='utf-8') as f:
            for p in bg_paths:
                f.write("file '%s'\n" % p.replace(os.sep, '/'))
        bg_all = os.path.join(BASE_DIR, 'data', 'videos', 'bg_all.mp4')
        cmd = ['ffmpeg','-y','-f','concat','-safe','0','-i',concat_bg,'-c:v','libx264','-preset','fast','-crf','22','-an',bg_all]
        subprocess.run(cmd, capture_output=True, timeout=60)
        
        # 叠加：后半段用素材背景，前半段保持原视频
        start_offset = overlay_start
        bg_dur = total_dur - overlay_start
        
        vf = "color=size=1080x1920:duration=%s:r=30:color=black[vblack];[vblack][%s]overlay=0:0:enable=between(t,0,%s)[vbg];[0:v][vbg]overlay=0:0:enable=gte(t,%s)" % (total_dur, bg_all, bg_dur, overlay_start)
        
        cmd = ['ffmpeg','-y','-i',video_path,'-filter_complex',vf,'-map','[v]','-map','0:a:0',
               '-c:v','libx264','-preset','medium','-crf','20','-c:a','copy',out_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
        
        if os.path.exists(out_path):
            sz = os.path.getsize(out_path)//1024//1024
            logger.info("素材叠加完成: %s (%d MB)" % (os.path.basename(out_path), sz))
            return out_path
        else:
            logger.warning("素材叠加失败: %s" % r.stderr[-200:])
            return video_path
            
    except Exception as e:
        logger.warning("素材叠加失败: %s" % str(e)[:80])
        return video_path


# 缓存脚本路径
_SCRIPT_CACHE = {}

def _cache_script_path(video_id, path):
    _SCRIPT_CACHE[video_id] = path

def _get_cached_script_path(video_id):
    if video_id in _SCRIPT_CACHE:
        return _SCRIPT_CACHE[video_id]
    # 尝试自动查找：先找含video_id的，再找最新的script JSON
    scripts_dir = os.path.join(DATA_DIR, 'scripts')
    if os.path.exists(scripts_dir):
        candidates = [f for f in os.listdir(scripts_dir) if f.endswith('.json') and 'script' in f]
        # 优先匹配video_id
        for f in candidates:
            if video_id in f:
                return os.path.join(scripts_dir, f)
        # 取最新
        if candidates:
            candidates.sort(key=lambda x: os.path.getmtime(os.path.join(scripts_dir, x)), reverse=True)
            return os.path.join(scripts_dir, candidates[0])
    return None


# ============================================================
# 命令行入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="地图热点流水线 v2（HyperFrames渲染）")
    parser.add_argument("video_id", help="视频配置ID（如 shenzhen, chongqing）")
    parser.add_argument("--skip-llm", action="store_true", help="跳过LLM，使用模板拼接")
    parser.add_argument("--step", help="步骤范围，如 1-5 或 3", default="1-5")
    parser.add_argument("--quality", choices=["draft", "standard", "high"], default="draft", help="HyperFrames渲染质量")
    
    args = parser.parse_args()
    
    if '-' in args.step:
        parts = args.step.split('-')
        step_range = (int(parts[0]), int(parts[1]))
    else:
        s = int(args.step)
        step_range = (s, s)
    
    try:
        success = run_pipeline(args.video_id, skip_llm=args.skip_llm, step_range=step_range, quality=args.quality)
    except Exception as e:
        logger.exception("流水线顶层异常")
        sys.exit(1)
    logger.info(f"[exit] success={success}, code={0 if success else 1}")
    sys.exit(0 if success else 1)


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()