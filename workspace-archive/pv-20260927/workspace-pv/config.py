# -*- coding: utf-8 -*-
"""
光伏获客系统 - 子系统配置
v0.1 完整子系统配置
"""
import os
from pathlib import Path

# 子系统根目录
BASE = Path(__file__).parent.parent.parent

# 数据存储
DATA_DIR = BASE / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
DB_PATH = DATA_DIR / "pv.db"

# 创建目录
for d in [DATA_DIR, RAW_DIR, PROCESSED_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 日志
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "system.log"

# 数据源配置
SOURCES = {
    "baidu_hot": {
        "url": "https://top.baidu.com/board?tab=realtime",
        "enabled": True,
        "timeout": 10,
    },
    "toutiao_hot": {
        "url": "https://www.toutiao.com/hot-event/hot-board/",
        "enabled": True,
        "timeout": 10,
    },
    "douyin_hot": {
        "url": "https://www.douyin.com/hot",
        "enabled": True,
        "timeout": 10,
    },
    "bjx_news": {
        "url": "https://guangfu.bjx.com.cn/yw/",
        "enabled": True,
        "timeout": 10,
    },
    "ofweek_news": {
        "url": "https://solar.ofweek.com/tag-%E5%85%89%E4%BC%8F%E6%96%B0%E9%97%BB.HTM",
        "enabled": True,
        "timeout": 10,
    },
}

# 光伏关键词（用于智能过滤）
PV_KEYWORDS = [
    # 核心词
    "光伏", "太阳能", "光伏发电", "分布式光伏", "屋顶光伏", "户用光伏",
    # 组件/设备
    "光伏板", "光伏组件", "光伏逆变器", "光伏支架", "光伏电池",
    # 场景/应用
    "工商业光伏", "工厂光伏", "农村光伏", "自建房光伏", "BIPV", "农光互补",
    # 政策/经济
    "光伏补贴", "光伏并网", "余电上网", "自发自用", "绿电交易",
    "光伏电价", "光伏备案", "光伏审批",
    # 技术
    "TOPCon", "HJT", "PERC", "BC电池", "钙钛矿", "储能",
    # 行业事件
    "光伏产能", "光伏价格", "光伏龙头", "光伏企业",
    # 配套
    "充电桩", "光储充", "光伏+储能", "微电网",
]

# 省份列表
PROVINCES = [
    "北京", "上海", "广东", "浙江", "江苏", "山东",
    "河北", "河南", "安徽", "福建", "江西", "湖南",
    "湖北", "四川", "重庆", "陕西", "山西", "辽宁",
    "吉林", "黑龙江", "内蒙古", "新疆", "甘肃", "宁夏",
    "青海", "西藏", "云南", "贵州", "广西", "海南", "天津",
]

# 采集频率（小时）
COLLECT_INTERVAL = {
    "hot_topic": 2,
    "policy": 24,
    "competitor": 6,
    "region_data": 24,
    "news": 4,
}

# 竞品账号列表（后续手动补充）
COMPETITORS = []

# 输出配置
CONTENT_DIRECTIONS = [
    "政策解读",
    "安装指南",
    "收益分析",
    "避坑指南",
    "技术科普",
    "行业新闻",
]

if __name__ == "__main__":
    print(f"PV System Base: {BASE}")
    print(f"Data Dir: {DATA_DIR}")
    print(f"DB: {DB_PATH}")
    print(f"SOURCES: {list(SOURCES.keys())}")