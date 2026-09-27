# MEMORY.md - 地图热点搭档工作空间

> 最后更新：2026-08-28 16:10（遗留架构清理：删除old_topic_loader_v1）

---

## 系统架构（2026-08-24 整理后）

### 入口
- **`scripts/core/pipeline.py`** — 唯一入口流水线（39KB）
  - 用法：`python scripts/core/pipeline.py <选题名>`
  - 步骤：选题→脚本→地图→配音→HyperFrames渲染→视频
  - 集成 MatchMakerV2 自动选题分类

### 目录结构
```
scripts/
├── core/           # 核心引擎（16个文件）
│   ├── pipeline.py              # 主流水线
│   ├── match_maker_v2.py        # 题材分类决策器
│   ├── material_matcher.py      # 素材匹配器
│   ├── visual_matcher.py        # 视觉技术匹配器
│   ├── visual_tech_complete.py  # 视觉效果技术库
│   ├── hyperframes_template.py  # 城市多区 HyperFrames 模板（v4）
│   ├── hyperframes_ranking_v43.py # 省份排名 HyperFrames 模板（v4.3）
│   ├── hyperframes_flow.py      # 人口流动模板
│   ├── hyperframes_policy.py    # 政策影响模板
│   ├── hyperframes_industry.py  # 产业结构模板
│   ├── hyperframes_institution.py # 制度起源模板
│   ├── advanced_maps.py         # 高级地图绘制
│   ├── advanced_charts.py       # 高级图表绘制
│   ├── audio_engine.py          # 音频引擎
│   ├── visual_effects_v2.py     # 视觉特效
│   └── config_loader.py         # 配置加载
├── modules/        # 功能模块（20个文件）
│   ├── hot_topic_collector_v5.py  # 热点采集（百度/微博等）
│   ├── official_topic_loader_v2.py # 官方数据源采集
│   ├── topic_loader.py           # 选题加载器
│   ├── diagnose_city.py          # 城市诊断工具

│   ├── prompt_builder.py         # 提示词构建
│   ├── script_validator.py       # 脚本验证
│   ├── map_mgr.py                # 地图管理器
│   ├── province_map_drawer.py    # 省级地图绘制
│   ├── tile_map_drawer.py        # 高德瓦片实景地图
│   ├── video_composer_v2.py      # 视频合成
│   ├── tts_generator.py          # Edge TTS 配音
│   ├── llm_client.py             # LLM 客户端
│   ├── schemas.py                # 数据Schema
│   └── deconstruct_v3.py         # 竞品拆解
├── select_topics.py   # 选题筛选入口
└── 选题采集_v3.py     # 选题采集入口
```

### 已清理
- 移走 64 个临时/测试脚本到 `scripts/backup/`
- 删除冗余版本文件（template v2/v3, ranking 旧版, generic, terrain_3d 等）
- 修复 visual_effects_v2.py 转义警告
- 删除 `modules/match_maker.py`（旧版，已被 match_maker_v2 替代）
- 删除 `modules/official_topic_loader.py`（v1，已被 v2 替代）

---

## 2026-08-24 系统清理

### 问题
昨天做了大量升级（16个新core文件+多个模板），但：
1. 只新增不整合——新文件堆在 core/ 里，没接入主流水线
2. 路径引用断裂——pipeline.py 引用不存在的 map_drawer_v3
3. 版本碎片化——10+模板版本并存，30+临时脚本散落根目录
4. MEMORY.md 未更新——描述的是已消失的 pipeline_v2 架构

### 清理结果
| 项目 | 清理前 | 清理后 |
|------|--------|--------|
| scripts/ 根目录 | 63 个文件 | 2 个（select_topics.py, 选题采集_v3.py） |
| scripts/modules/ | 28 个文件 | 20 个 |
| scripts/core/ | 30 个文件 | 16 个 |
| backup/ 大小 | - | 3.6 MB |
| 编译验证 | 1 FAIL | 41 OK, 0 FAIL |



---

## 2026-08-28 遗留架构清理

| 项目 | 处理 | 状态 |
|------|------|------|
| match_maker.py vs match_maker_v2.py | 旧版已不存在，仅v2保留 | ✅ 已解决 |
| official_topic_loader.py vs v2 | 删除v1，保留v2增强版 | ✅ 已清理 |
| output vs videos路径 | pipeline.py统一输出到data/videos/ | ✅ 已统一 |
| ARCHITECTURE.md乱码 | 重写为v2.0当前架构文档 | ✅ 已重建 |
| AGENTS.md旧引用 | pipeline_v2→v3, match_maker→v2 | ✅ 已更新 |

---

## 2026-08-23 工作成果

### HyperFrames 模板体系
- `hyperframes_template.py` v4 — 城市多区模板（3D相机飞行+粒子爆发）
- `hyperframes_ranking_v43.py` — 省份排名模板（永不停止的地图平移）
- `hyperframes_flow/policy/industry/institution.py` — 4个专项模板
- `visual_matcher.py` + `match_maker_v2.py` — 题材分类+视觉匹配决策链

### 产出视频
- `beijing_metro_v3.mp4` (1.3MB) — HyperFrames 3D模板
- `egg_price_20260822.mp4` — 鸡蛋价格排名
- 3条 topic 测试视频

---

## 产品线

| 系列 | 频率 | 时长 | 内容 | 定位 |
|------|------|------|------|------|
| **深一度** | 每周1条 | 3-5分钟 | 深度拆解一个城市/省份/产业 | 核心壁垒，拉粉丝 |
| **追热点** | 每周2条 | 1-2分钟 | 紧跟新闻，地图快速解读 | 蹭流量，拉新 |
| **一张图** | 每周2条 | 30-60秒 | 纯数据排名，地图+数字 | 短平快，拉完播率 |

---

## 技术规格

- **地图**: matplotlib + geopandas + 高德瓦片（tile_map_drawer.py）
- **配音**: Edge TTS (zh-CN-XiaoxiaoNeural)
- **视频**: HyperFrames HTML→ffmpeg渲染，1080×1920竖屏
- **码率**: CRF 18, ~2000kbps, 30fps
- **BGM**: -20dB，淡入淡出2s

---

## 待办事项

- [ ] 确定账号名
- [ ] 注册新账号（抖音/头条/百家号/B站）
- [ ] 发布第一条正式视频
- [ ] 建立选题池（每周更新）
- [x] 配置Cron定时任务（每日10:00选题采集）
- [x] HyperFrames 模板体系
- [x] MatchMakerV2 题材分类
- [x] 遗留架构清理（match_maker/official_loader/output路径）
- [ ] 补充BGM库

---

_最后更新：2026-08-28 16:10（遗留架构问题清理：删除old_topic_loader_v1、清理match_maker标注）_
