"""
蜗牛幼儿园素材自动筛选脚本 v1.0
功能：扫描 raw 文件夹中的照片/视频，分析内容质量，选出最佳素材
用法：python material_picker.py
输出：打印推荐素材列表，并将选中的文件复制到 selected 文件夹
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\snail-video')
RAW_DIR = BASE_DIR / 'daily_materials' / 'raw'
SELECTED_DIR = BASE_DIR / 'daily_materials' / 'selected'
ARCHIVE_DIR = BASE_DIR / 'daily_materials' / 'archive'

# 支持的文件格式
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp'}
VIDEO_EXT = {'.mp4', '.mov', '.avi'}

def get_image_info(filepath):
    """获取图片基本信息：文件大小、修改时间"""
    stat = filepath.stat()
    return {
        'path': str(filepath),
        'name': filepath.name,
        'size_kb': round(stat.st_size / 1024, 1),
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
        'ext': filepath.suffix.lower(),
    }

def check_image_quality(filepath):
    """
    图片质量初筛（不依赖外部库）
    规则：
    - 文件太小(<10KB) -> 可能模糊或损坏
    - 文件太大(>5MB) -> 原图，可接受但需压缩
    - 文件名含"blur""dark"等关键词 -> 标记
    """
    stat = filepath.stat()
    size_kb = stat.st_size / 1024
    
    issues = []
    if size_kb < 10:
        issues.append('文件太小，可能模糊或损坏')
    if size_kb > 5120:
        issues.append('文件过大，建议压缩')
    
    name_lower = filepath.name.lower()
    if any(kw in name_lower for kw in ['blur', 'dark', 'bad', '模糊', '暗']):
        issues.append('文件名含质量警告词')
    
    return {
        'size_kb': round(size_kb, 1),
        'pass_quality': len(issues) == 0,
        'issues': issues,
    }

def classify_scene(filepath):
    """
    根据文件名和路径关键词分类场景
    不依赖外部库，基于关键词匹配
    """
    name_lower = filepath.name.lower()
    path_lower = str(filepath).lower()
    
    scene_keywords = {
        '运动场': ['运动场', '操场', '户外', '奔跑', '跑步', 'sport', 'playground', '运动'],
        '陶艺': ['陶艺', '陶泥', '陶', 'clay', 'pottery'],
        '手工': ['手工', '画画', '画', '折纸', '剪纸', 'art', 'craft', 'draw'],
        '阅读': ['阅读', '绘本', '书', '读书', 'read', 'book', 'library'],
        '音乐': ['音乐', '奥尔夫', '唱歌', '乐器', 'music', 'sing'],
        '种植园': ['种植', '种菜', '植物', '花园', 'garden', 'plant', '农场'],
        '沙池': ['沙池', '沙', 'sand', '沙坑'],
        '生活': ['吃饭', '午睡', '排队', '喝水', '洗手', 'eat', 'sleep', 'lunch'],
        '入园离园': ['入园', '离园', '晨检', '接送', 'morning', 'pickup'],
        '课堂': ['课堂', '上课', '学习', 'class', 'learn', '教室'],
        '其他': [],
    }
    
    for scene, keywords in scene_keywords.items():
        if scene == '其他':
            continue
        if any(kw in name_lower or kw in path_lower for kw in keywords):
            return scene
    
    return '其他'

def select_best_materials():
    """扫描raw文件夹，筛选最佳素材"""
    if not RAW_DIR.exists():
        print(f'素材目录不存在: {RAW_DIR}')
        return []
    
    files = list(RAW_DIR.iterdir())
    if not files:
        print('素材目录为空')
        return []
    
    # 分类
    images = []
    videos = []
    for f in files:
        if f.is_file():
            if f.suffix.lower() in IMAGE_EXT:
                images.append(f)
            elif f.suffix.lower() in VIDEO_EXT:
                videos.append(f)
    
    print(f'共发现 {len(images)} 张图片, {len(videos)} 个视频')
    
    results = []
    
    # 处理图片
    for img in images:
        info = get_image_info(img)
        quality = check_image_quality(img)
        scene = classify_scene(img)
        
        if quality['pass_quality']:
            results.append({
                'type': 'image',
                'info': info,
                'quality': quality,
                'scene': scene,
                'score': _calc_score(info, quality),
            })
    
    # 处理视频（仅基本信息）
    for vid in videos:
        info = get_image_info(vid)
        results.append({
            'type': 'video',
            'info': info,
            'scene': classify_scene(vid),
            'score': round(info['size_kb'] / 100, 1),  # 视频评分简单按大小
        })
    
    # 按评分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

def _calc_score(info, quality):
    """
    计算图片评分 (0-100)
    - 文件大小适中得高分 (50-500KB最佳)
    - 通过质量检测加分
    """
    score = 50  # 基础分
    
    # 文件大小评分
    size = info['size_kb']
    if 50 <= size <= 500:
        score += 30
    elif 500 < size <= 2000:
        score += 20
    elif size > 2000:
        score += 10
    else:
        score += 0
    
    # 质量检测
    if quality['pass_quality']:
        score += 20
    
    return min(score, 100)

def archive_processed():
    """将已选中的文件归档"""
    if not SELECTED_DIR.exists():
        return
    
    today = datetime.now().strftime('%Y%m%d')
    archive_subdir = ARCHIVE_DIR / today
    archive_subdir.mkdir(parents=True, exist_ok=True)
    
    for f in SELECTED_DIR.iterdir():
        if f.is_file():
            dest = archive_subdir / f.name
            shutil.move(str(f), str(dest))
    
    print(f'已归档到: {archive_subdir}')

def main():
    print('=' * 50)
    print('蜗牛幼儿园素材筛选器 v1.0')
    print(f'运行时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('=' * 50)
    print()
    
    # 筛选素材
    results = select_best_materials()
    
    if not results:
        print()
        print('没有找到可用的素材')
        return
    
    print()
    print('--- 推荐素材 Top 5 ---')
    print()
    
    # 按场景分组
    scenes = {}
    for r in results:
        s = r['scene']
        if s not in scenes:
            scenes[s] = []
        scenes[s].append(r)
    
    # 每个场景推荐1张
    selected = []
    for scene in ['运动场', '陶艺', '手工', '阅读', '音乐', '种植园', '沙池', '生活', '课堂', '入园离园', '其他']:
        if scene in scenes and scenes[scene]:
            best = scenes[scene][0]
            selected.append(best)
            print(f'【{scene}】{best["info"]["name"]}')
            print(f'  大小: {best["info"]["size_kb"]}KB | 评分: {best["score"]}')
            print(f'  修改时间: {best["info"]["modified"]}')
            if best.get('quality', {}).get('issues'):
                print(f'  注意: {", ".join(best["quality"]["issues"])}')
            print()
    
    # 复制选中的到selected文件夹
    SELECTED_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for r in selected:
        src = Path(r['info']['path'])
        dst = SELECTED_DIR / src.name
        if not dst.exists():
            shutil.copy2(str(src), str(dst))
            copied += 1
    
    print(f'已复制 {copied} 个文件到 selected 文件夹')
    
    # 输出JSON供其他程序使用
    output = {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_scanned': len(results),
        'selected': [{
            'name': r['info']['name'],
            'scene': r['scene'],
            'score': r['score'],
            'path': r['info']['path'],
        } for r in selected],
    }
    json_path = BASE_DIR / 'daily_materials' / 'latest_pick.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'筛选结果已保存: {json_path}')
    print()
    print('=' * 50)

if __name__ == '__main__':
    main()