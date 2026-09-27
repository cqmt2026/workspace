# TOOLS.md - 本地工具笔记（地图热点）

**最后更新**: 2026-09-05

---

## 流水线架构

```
选题采集 → 脚本生成 → 地图绘制 → 配音生成 → 调色 → 视频合成 → 发布
```

## 核心脚本

| 脚本 | 功能 |
|------|------|
| pipeline.py | 一站式流水线编排 |
| 选题采集_v3.py | 百度热搜+mx-search双源采集 |
| 脚本生成_v3.py | LLM生成口播脚本 |
| 地图绘制_v5.py | 高德地图+GeoJSON |
| 配音生成_v2.py | Edge TTS |
| 视频合成_v2.py | HyperFrames渲染 |
| 发布推送.py | 多平台发布 |

## 模块

| 模块 | 功能 |
|------|------|
| hot_topic_collector_v5.py | 热点采集引擎 |
| llm_client.py | LLM调用封装 |
| tts_generator.py | TTS生成 |
| video_composer_v2.py | 视频合成 |
| deconstruct_v3.py | 抖音视频拆解 |

## 工具集成

| 工具 | 路径 | 功能 |
|------|------|------|
| video-use | video-use/helpers/ | 调色grade.py |
| cutmv-video-tool | cutmv-video-tool/ | 裁剪/压缩 |
| douyin.js | skills/douyin-video/scripts/ | 抖音视频下载 |

## 城市配置

| 配置文件 | 城市 |
|---------|------|
| city_shenzhen.json | 深圳 |
| city_广州.json | 广州 |
| city_成都.json | 成都 |
| chongqing_video_config.json | 重庆 |

## 输出目录

- **视频**: workspace-maphot/data/videos/ (215个)
- **音频**: workspace-maphot/data/audio/ (41个)
- **地图**: workspace-maphot/data/maps/ (24个)
- **选题**: workspace-maphot/data/topics/ (2个)

---
_由可悦🌸 维护，2026-09-05_
