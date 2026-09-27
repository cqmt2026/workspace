# -*- coding: utf-8 -*-
"""
光伏获客系统 - 配置
v0.2 重构：数据源迁移至 mx-search + web_search + 百度热搜s-data
"""

import os
from pathlib import Path

# 项目根目录（scripts/ 的父目录）
ROOT = Path(__file__).parent.parent.parent

# 数据存储
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 子目录
RAW_DIR = DATA_DIR / "raw"          # 原始数据
PROCESSED_DIR = DATA_DIR / "processed"  # 处理后数据
DB_PATH = DATA_DIR / "pv.db"        # SQLite 数据仓库

for d in [RAW_DIR, PROCESSED_DIR]:
    d.mkdir(exist_ok=True)

# 数据源配置
SOURCES = {
    "baidu_hot": {
        "url": "https://top.baidu.com/board?tab=realtime",
        "enabled": True,
        "timeout": 10,
    },
    "mx_search": {
        "enabled": True,
        "timeout": 30,
    },
    "web_search": {
        "enabled": True,
        "timeout": 15,
    },
}

# 光伏关键词（用于智能过滤）
PV_KEYWORDS = [
    "光伏", "太阳能", "分布式光伏", "屋顶光伏", "户用光伏",
    "光伏发电", "光伏安装", "光伏补贴", "光伏政策",
    "光伏电站", "光伏板", "光伏组件", "光伏逆变器",
    "光伏贷款", "光伏养老", "光伏+储能", "整县光伏",
    "BIPV", "光伏建筑", "光电建筑", "光储充",
    "新能源", "可再生能源", "双碳", "碳中和",
    "电价", "电费", "并网", "余电上网",
    "自建房", "屋顶", "厂房", "工商业光伏",
]

# 省份列表（用于区域分析）
PROVINCES = [
    "北京", "上海", "广东", "浙江", "江苏", "山东",
    "河北", "河南", "安徽", "福建", "江西", "湖南",
    "湖北", "四川", "重庆", "陕西", "山西", "辽宁",
    "吉林", "黑龙江", "内蒙古", "新疆", "甘肃", "宁夏",
    "青海", "西藏", "云南", "贵州", "广西", "海南",
    "天津",
]

# mx-search 搜索关键词（热点采集用）
MX_SEARCH_QUERIES = [
    "光伏行业最新新闻",
    "光伏发电政策动态",
    "分布式光伏市场趋势",
    "光伏补贴最新消息",
    "太阳能光伏产业新闻",
    "光伏+储能行业动态",
    "工商业光伏安装",
    "屋顶光伏发电",
]

# mx-search 搜索关键词（政策监控用）
MX_POLICY_QUERIES = [
    "光伏补贴政策",
    "分布式光伏并网政策",
    "光伏行业标准规范",
    "新能源光伏发展规划",
    "光伏发改委能源局",
    "光伏整县推进",
    "光伏可再生能源政策",
]

# web_search 搜索关键词（备用）
WEB_SEARCH_QUERIES = [
    "光伏 2026 最新新闻",
    "光伏发电 热点",
    "分布式光伏 安装 趋势",
    "光伏补贴 政策 2026",
    "太阳能光伏 行业发展",
]

# 采集频率（小时）
COLLECT_INTERVAL = {
    "hot_topic": 2,         # 热点每2小时
    "policy": 24,           # 政策每天
    "competitor": 6,        # 竞品每6小时
    "region_data": 24,      # 区域数据每天
}