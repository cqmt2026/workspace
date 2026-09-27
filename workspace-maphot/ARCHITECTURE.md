# 地图热点子系统 - 架构设计文档

> **最后更新**: 2026-08-28
> **版本**: v2.0（重构版）

---

## 一、整体架构

```
选题采集  ──→ 脚本生成  ──→ 地图绘制  ──→ 配音生成  ──→ 模板生成  ──→ 视频渲染
  │             │            │            │            │            │
智能体驱动    LLM生成      matplotlib   Edge TTS    HyperFrames  hf render
              + LLM         + 高德瓦片              HTML模板     → MP4
```

### 模块职责

| 层级 | 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| L1 | 选题采集 | 从百度热搜/mx-search采集热点选题 | 城市名 | 选题结构体 |
| L2 | 脚本生成 | 根据选题数据生成口播文案和时间分配 | 选题JSON | 脚本JSON |
| L3 | 地图绘制 | 绘制城市区县地图（数据驱动配色） | 选题JSON + 样式配置 | PNG图片 |
| L4 | 配音生成 | 合成口播语音 | 脚本JSON | MP3音频 |
| L5 | 模板生成 | 生成HyperFrames HTML模板 | 选题JSON + 地图PNG + 音频MP3 | index.html |
| L6 | 视频渲染 | 渲染为MP4视频 | index.html + 素材目录 | MP4视频 |

---

## 二、核心文件

### 2.1 流水线入口

```
scripts/core/pipeline.py  # 唯一入口，串联全流程
```

用法：
```bash
python scripts/core/pipeline.py "选题名称"
```

### 2.2 题材分类与视觉匹配

| 文件 | 职责 |
|------|------|
| `core/match_maker_v2.py` | 题材分类决策器（8类题材） |
| `core/visual_matcher.py` | 视觉技术匹配器 |
| `core/visual_tech_complete.py` | 视觉效果技术库 |
| `core/material_matcher.py` | 素材匹配器 |

### 2.3 地图绘制

| 文件 | 职责 |
|------|------|
| `modules/province_map_drawer.py` | 省级地图绘制 |
| `modules/tile_map_drawer.py` | 高德瓦片实景地图 |
| `modules/city_map_fetcher.py` | 城市GeoJSON自动获取 |
| `core/advanced_maps.py` | 高级地图绘制工具 |

### 2.4 HyperFrames模板

| 文件 | 职责 |
|------|------|
| `core/hyperframes_template.py` | 城市多区模板（v4） |
| `core/hyperframes_ranking_v43.py` | 省份排名模板（v4.3） |
| `core/hyperframes_flow.py` | 人口流动模板 |
| `core/hyperframes_policy.py` | 政策影响模板 |
| `core/hyperframes_industry.py` | 产业结构模板 |
| `core/hyperframes_institution.py` | 制度起源模板 |

### 2.5 数据源

| 文件 | 职责 |
|------|------|
| `modules/hot_topic_collector_v5.py` | 热点采集（百度/微博等） |
| `modules/official_topic_loader_v2.py` | 官方数据源采集 |
| `modules/topic_loader.py` | 选题加载器 |
| `modules/llm_client.py` | LLM客户端 |
| `modules/tts_generator.py` | Edge TTS配音 |
| `modules/video_composer_v2.py` | 视频合成 |

---

## 三、目录结构

```
workspace-maphot/
├── scripts/
│   ├── core/               # 核心引擎（16个文件）
│   │   ├── pipeline.py              # 主流水线入口
│   │   ├── match_maker_v2.py        # 题材分类决策器
│   │   ├── visual_matcher.py        # 视觉技术匹配器
│   │   ├── visual_tech_complete.py  # 视觉效果技术库
│   │   ├── material_matcher.py      # 素材匹配器
│   │   ├── hyperframes_template.py  # 城市多区模板（v4）
│   │   ├── hyperframes_ranking_v43.py # 省份排名模板（v4.3）
│   │   ├── hyperframes_flow.py      # 人口流动模板
│   │   ├── hyperframes_policy.py    # 政策影响模板
│   │   ├── hyperframes_industry.py  # 产业结构模板
│   │   ├── hyperframes_institution.py # 制度起源模板
│   │   ├── advanced_maps.py         # 高级地图绘制
│   │   ├── advanced_charts.py       # 高级图表绘制
│   │   ├── audio_engine.py          # 音频引擎
│   │   ├── visual_effects_v2.py     # 视觉特效
│   │   └── config_loader.py         # 配置加载
│   ├── modules/           # 功能模块（21个文件）
│   │   ├── hot_topic_collector_v5.py  # 热点采集
│   │   ├── official_topic_loader_v2.py # 官方数据源
│   │   ├── topic_loader.py            # 选题加载
│   │   ├── match_maker.py            # 旧版题材匹配（保留兼容）
│   │   ├── province_map_drawer.py    # 省级地图
│   │   ├── tile_map_drawer.py        # 高德瓦片实景地图
│   │   ├── city_map_fetcher.py       # 城市地图自动获取
│   │   ├── video_composer_v2.py      # 视频合成
│   │   ├── tts_generator.py          # Edge TTS配音
│   │   ├── llm_client.py             # LLM客户端
│   │   └── ...（其他模块）
│   ├── select_topics.py      # 选题筛选入口
│   └── 选题采集_v3.py        # 选题采集入口
├── config/                  # 城市配置文件
├── data/                    # 数据输出目录
│   ├── audio/              # 音频文件
│   ├── maps/               # 地图输出
│   └── scripts/            # 脚本JSON
├── assets/                  # 素材资源
├── backup/                  # 备份目录
└── shared-knowledge/       # 知识手册
```

---

## 四、数据流标准

### 4.1 城市数据JSON（city_{name}.json）

位置: `config/city_{name}.json`

```json
{
  "city": "深圳",
  "year": "2026",
  "total_gdp": "3.46万亿",
  "gdp_rank": "全国城市第三",
  "area": "1,997km²",
  "population": "1,766万",
  "districts": [
    {
      "name": "南山区",
      "gdp": "8,400亿",
      "gdp_raw": 8400,
      "per_gdp": "249万",
      "pct": "24.3%",
      "desc": "腾讯总部 · 中国硅谷",
      "tag": "中国硅谷"
    }
  ]
}
```

### 4.2 地图输出标准

```
位置: data/maps/
命名: {city}_{name}_map.png
尺寸: 1080×1920（竖屏，300dpi）
格式: PNG
```

### 4.3 音频输出标准

```
位置: data/audio/
命名: {city}_{topic}_tts.mp3
格式: MP3, 44100Hz, 单声道
```

---

## 五、产品线

| 系列 | 频率 | 时长 | 定位 |
|------|------|------|------|
| 深一度 | 每周1条 | 3-5分钟 | 核心壁垒，拉粉丝 |
| 追热点 | 每周2条 | 1-2分钟 | 蹭流量，拉新 |
| 一张图 | 每周2条 | 30-60秒 | 短平快，拉完播率 |

---

## 六、技术规格

- **地图**: matplotlib + geopandas + 高德瓦片
- **配音**: Edge TTS (zh-CN-XiaoxiaoNeural)
- **视频**: HyperFrames HTML → ffmpeg渲染，1080×1920竖屏
- **码率**: CRF 18, ~2000kbps, 30fps
- **BGM**: -20dB，淡入淡出2s

---

## 七、版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-25 | 初版架构文档 |
| v2.0 | 2026-08-28 | 重构：适配pipeline_v3、HyperFrames模板体系、MatchMakerV2 |
