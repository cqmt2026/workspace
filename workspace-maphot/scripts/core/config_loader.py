# -*- coding: utf-8 -*-
"""
地图热点子系统 - 视频配置管理
每个视频对应一个JSON配置文件,定义所有参数
支持自定义路径、默认值回退、配置验证
"""
import json, os, sys

# ============================================================
# 路径配置(支持独立路径覆盖)
# ============================================================
# 默认:从脚本目录向上两级为workspace-maphot根(即本模块的父父目录)
_MAPHOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKSPACE_BASE = _MAPHOT_DIR

# 环境变量优先(允许外部覆盖)
_ENV_BASE = os.environ.get("MAPHOT_BASE_DIR", "")
BASE_DIR = _ENV_BASE if _ENV_BASE else _WORKSPACE_BASE

CONFIG_DIR = os.path.join(BASE_DIR, "config")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

for d in [CONFIG_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# 默认配置模板
# ============================================================
DEFAULT_CONFIG = {
    "video_id": "",
    "title": "",
    "city": "",
    "adcode": "",
    "districts": [],
    "intro": "",
    "outro": "",
    "theme": {
        "bg_color": "#1a1a2e",
        "map_color": "#16213e",
        "card_color": "#0f3460"
    },
    "tts": {
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "+10%"
    },
    "video": {
        "subtitle_y": 120,
        "ken_burns": True,
        "fade_duration": 0.3,
        "fps": 25,
        "crf": 23
    },
    "output": {
        "frame_dir": "maps",
        "audio_file": "tts.mp3",
        "video_file": "output.mp4"
    }
}

CONFIG_SCHEMA = {
    "video_id": "str, 唯一标识",
    "title": "str, 视频标题",
    "city": "str, 城市名",
    "adcode": "str, 行政区划代码",
    "districts": "list, 区县列表",
    "intro": "str, 开头文案",
    "outro": "str, 结尾文案",
    "theme": "dict, 主题配色",
    "tts": "dict, TTS设置",
    "video": "dict, 视频参数",
    "output": "dict, 输出设置"
}

# ============================================================
# 核心API
# ============================================================

def load_config(video_id):
    """加载视频配置，缺失字段用默认值填充"""
    path = os.path.join(CONFIG_DIR, f"{video_id}.json")
    if not os.path.exists(path):
        return dict(DEFAULT_CONFIG)

    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 从 video_id 参数回填缺失的必填字段
    if not cfg.get("video_id"):
        cfg["video_id"] = video_id
    if not cfg.get("title"):
        # 尝试从 city + districts 构建标题
        city = cfg.get("city", video_id)
        n = len(cfg.get("districts", []))
        cfg["title"] = f"{city}{n}个行政区" if n else city
    if not cfg.get("city"):
        cfg["city"] = video_id
    if not cfg.get("adcode"):
        cfg["adcode"] = "500000"  # 默认，如不匹配则首次运行时从DataV下载

    # 合并默认值（确保新字段不缺失）
    for key, default_val in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = default_val
        elif isinstance(default_val, dict) and key in cfg and isinstance(cfg[key], dict):
            for sub_key, sub_default in default_val.items():
                if sub_key not in cfg[key]:
                    cfg[key][sub_key] = sub_default

    return cfg

def save_config(video_id, data):
    """保存配置到JSON文件"""
    path = os.path.join(CONFIG_DIR, f"{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def list_configs():
    """列出所有可用配置"""
    if not os.path.exists(CONFIG_DIR):
        return []
    files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    return sorted([f.replace(".json", "") for f in files])

def create_config(video_id, data=None):
    """创建新配置,data为None时使用默认模板"""
    if data is None:
        data = dict(DEFAULT_CONFIG)
        data["video_id"] = video_id
    path = save_config(video_id, data)
    print(f"配置已创建: {path}")
    return path

def get_data_dir(subdir=None):
    """获取数据目录路径"""
    d = DATA_DIR
    if subdir:
        d = os.path.join(d, subdir)
    os.makedirs(d, exist_ok=True)
    return d

def get_maps_dir(date_str=None):
    """获取地图输出目录"""
    base = get_data_dir("maps")
    if date_str:
        base = os.path.join(base, date_str)
    os.makedirs(base, exist_ok=True)
    return base

def get_audio_dir():
    """获取音频目录"""
    return get_data_dir("audio")

def get_video_dir():
    """获取视频输出目录"""
    return get_data_dir("videos")

def get_cache_dir():
    """获取缓存目录"""
    return get_data_dir("cache")

def get_geojson_dir():
    """获取GeoJSON目录"""
    return get_data_dir(os.path.join("cache", "geojson"))

def validate_config(cfg):
    """验证配置完整性,返回(是否通过, 问题列表)"""
    issues = []
    required_fields = ["video_id", "title", "city", "adcode"]
    for field in required_fields:
        if not cfg.get(field):
            issues.append(f"缺少必填字段: {field}")

    districts = cfg.get("districts", [])
    if not districts:
        issues.append("districts为空,至少需要一个区县")
    else:
        for i, d in enumerate(districts):
            if not d.get("name"):
                issues.append(f"districts[{i}]缺少name字段")

    return len(issues) == 0, issues

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "list":
            print("可用配置:", list_configs())
        elif cmd == "load":
            vid = sys.argv[2] if len(sys.argv) > 2 else ""
            cfg = load_config(vid)
            print(json.dumps(cfg, ensure_ascii=False, indent=2))
        elif cmd == "create":
            vid = sys.argv[2] if len(sys.argv) > 2 else "new_video"
            create_config(vid)
        elif cmd == "validate":
            vid = sys.argv[2] if len(sys.argv) > 2 else ""
            cfg = load_config(vid)
            ok, issues = validate_config(cfg)
            print(f"{'OK' if ok else 'FAIL'}: {issues if issues else '配置完整'}")
        else:
            print(f"用法: config_loader.py [list|load <id>|create <id>|validate <id>]")
    else:
        print("地图热点配置管理工具")
        print(f"工作目录: {BASE_DIR}")
        print(f"配置目录: {CONFIG_DIR}")
        print(f"数据目录: {DATA_DIR}")
        print()
        print("可用配置:", list_configs())
