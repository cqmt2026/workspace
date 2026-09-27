# -*- coding: utf-8 -*-
"""
Pixabay 视频素材获取模块
用于从 Pixabay 免费视频库搜索和下载实拍素材
"""

import os
import json
import logging
import urllib.request
import urllib.parse
import shutil

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MATERIAL_DIR = os.path.join(BASE_DIR, 'data', 'materials')

# Pixabay API 配置
PIXABAY_API_URL = "https://pixabay.com/api/videos/"
PIXABAY_API_KEY = ""

def _load_api_key():
    """从 .env 加载 API key"""
    global PIXABAY_API_KEY
    if PIXABAY_API_KEY:
        return PIXABAY_API_KEY
    
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('PIXABAY_API_KEY='):
                    PIXABAY_API_KEY = line.split('=', 1)[1].strip()
                    return PIXABAY_API_KEY
    
    # 也检查环境变量
    import os as _os
    PIXABAY_API_KEY = _os.environ.get('PIXABAY_API_KEY', '')
    return PIXABAY_API_KEY


def search_videos(query, per_page=5, page=1, min_width=720, min_height=1080):
    """
    搜索视频
    
    Args:
        query: 搜索关键词（英文）
        per_page: 每页数量
        page: 页码
        min_width: 最小宽度
        min_height: 最小高度
    
    Returns:
        list of dict: 视频列表
    """
    key = _load_api_key()
    if not key:
        logger.error("PIXABAY_API_KEY 未设置")
        return []
    
    params = {
        'key': key,
        'q': query,
        'per_page': max(3, min(per_page, 200)),
        'page': page,
        'safesearch': 'true',
    }
    
    url = f"{PIXABAY_API_URL}?{urllib.parse.urlencode(params)}"
    logger.info(f"搜索 Pixabay: {query}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        hits = data.get('hits', [])
        logger.info(f"找到 {len(hits)} 个视频")
        
        # 筛选
        results = []
        for hit in hits:
            videos = hit.get('videos', {})
            # 优先选大尺寸
            for size_key in ['large', 'medium', 'small', 'tiny']:
                if size_key in videos:
                    v = videos[size_key]
                    w = v.get('width', 0)
                    h = v.get('height', 0)
                    if w >= min_width and h >= min_height:
                        results.append({
                            'id': hit.get('id'),
                            'page_url': hit.get('pageURL'),
                            'url': v.get('url'),
                            'width': w,
                            'height': h,
                            'size': size_key,
                            'duration': hit.get('duration'),
                            'tags': hit.get('tags', ''),
                            'user': hit.get('user', ''),
                            'type': v.get('url', '').split('.')[-1] if '.' in v.get('url', '') else 'mp4',
                        })
                        break
        
        return results
    
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return []


def download_video(video_info, output_dir=None):
    """
    下载视频
    
    Args:
        video_info: search_videos 返回的单个结果
        output_dir: 输出目录，默认 data/materials/{query}/
    
    Returns:
        str: 下载文件路径，失败返回 None
    """
    if output_dir is None:
        output_dir = MATERIAL_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    url = video_info.get('url', '')
    if not url:
        logger.error("视频URL为空")
        return None
    
    # 文件名
    vid = video_info.get('id', 'unknown')
    tags = video_info.get('tags', 'video').split(',')[0].strip()
    ext = video_info.get('type', 'mp4')
    fname = f"{tags}_{vid}.{ext}"
    out_path = os.path.join(output_dir, fname)
    
    if os.path.exists(out_path):
        logger.info(f"已存在: {fname} ({os.path.getsize(out_path)/1024:.0f}KB)")
        return out_path
    
    try:
        logger.info(f"下载: {url[:80]}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(out_path, 'wb') as f:
                shutil.copyfileobj(resp, f)
        
        sz = os.path.getsize(out_path) / 1024 / 1024
        logger.info(f"下载完成: {fname} ({sz:.1f}MB)")
        return out_path
    
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return None


def search_and_download(query, output_dir=None, max_results=3):
    """
    搜索并下载视频（一站式）
    
    Args:
        query: 搜索关键词
        output_dir: 输出目录
        max_results: 最大下载数量
    
    Returns:
        list of str: 下载文件路径列表
    """
    if output_dir is None:
        output_dir = os.path.join(MATERIAL_DIR, query.replace(' ', '_'))
    
    os.makedirs(output_dir, exist_ok=True)
    
    videos = search_videos(query, per_page=max_results)
    if not videos:
        logger.warning(f"未找到 {query} 相关视频")
        return []
    
    downloaded = []
    for v in videos[:max_results]:
        path = download_video(v, output_dir)
        if path:
            downloaded.append(path)
    
    return downloaded


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 测试连接
    test = search_videos('city street', per_page=1)
    if test:
        print(f'[OK] Pixabay API 连接成功，找到 {len(test)} 个视频')
        print(f'  示例: {test[0]["tags"][:60]} ({test[0]["width"]}x{test[0]["height"]})')
    else:
        print('[NO] Pixabay API 连接失败')