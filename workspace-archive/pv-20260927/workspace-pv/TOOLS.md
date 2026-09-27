# TOOLS.md - 本地工具笔记（光伏获客）

**最后更新**: 2026-09-05

---

## 内容流程

```
热点采集 → 脚本生成 → 视频合成 → 发布
```

## 核心脚本

| 脚本 | 功能 |
|------|------|
| pipeline.py | 一站式流水线编排 |
| hot_topic_collector.py | 四源热点采集 |
| policy_monitor.py | 政策监控 |
| content_generator.py | 视频脚本生成 |
| competitor_monitor.py | 竞品分析 |

## 数据源

- **头条**: BrowserAct采集
- **微博**: web_search
- **抖音**: douyin.js
- **36氪**: web_fetch

## 视频合成

- **HyperFrames**: v0.7.63
- **FFmpeg**: v8.1
- **输出**: workspace-pv/output/videos/

---
_由可悦🌸 维护，2026-09-05_
