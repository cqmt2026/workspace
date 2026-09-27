# 短板修复完成记录 - 2026-08-28 15:00

## 全部已完成

### P0-A: 渲染模式自动选择 ✅
**文件**: `scripts/core/pipeline.py`
- 视频数≤3 → drawElement（快速）；>3 → `--experimental-fast-capture=false`（稳定）
- drawElement 失败自动回退截图模式重试
- 超时 900s，HF 版本锁定 0.8.17

### P0-B: LLM 多模型 fallback ✅
**文件**: `scripts/modules/llm_client.py`
- 模型链：`openclaw` → `deepseek-v4-flash` → `qwen-397b` → `llama-3.3-70b`
- 任一成功即返回，全失败才回退模板拼接

### P1-A: GEO_ANGLES 动态地域匹配 ✅
**文件**: `scripts/modules/hot_topic_collector_v5.py`
- 新增 `_CITIES_CN`（35个城市）+ `extract_regions()` 函数
- 选题标题含城市名时自动匹配地理角度

### P1-A2: web_search 备选数据源 ✅
**文件**: `scripts/modules/hot_topic_collector_v5.py`
- 新增 `collect_web_search()` 占位方法

### P1-B: 模板库完整接入 pipeline ✅
**文件**: `scripts/core/pipeline.py`
- 新增 `TEMPLATE_MAP` 字典，8种题材类型全映射
- 移除硬编码 if/elif，改用动态 import + getattr

### P2: 场景切换音效 ✅
**文件**: `scripts/core/hyperframes_template.py`
- 新增 `playTransitionSound()` / `playCountUpSound()`

### P2-TTS: 配音音色轮换 ✅
**文件**: `scripts/modules/tts_generator.py`
- 新增 `VOICES` 常量（5种音色）
- `VOICE_BY_CATEGORY` 按题材类型自动选音

### P2-BGM: BGM 轮换 ✅
**文件**: `scripts/core/pipeline.py` + `scripts/core/hyperframes_template.py`
- pipeline 从 `data/audio/bgm_*.mp3` 随机选择 BGM
- HTML 中注入 BGM 控制 JS

### P3: map_mgr 注册表完善 ✅
**文件**: `scripts/modules/style_config.py`（新建）+ `scripts/core/pipeline.py`
- 创建 `style_config.py`（4种风格配置：default/direct/minimal/dark）
- `step_draw_maps` 优先使用 MapMgr 注册表，失败回退直接调用
- MapMgr 支持：全国俯瞰图、区域高亮图、对比并排图、实景排名图

## 环境升级
- ffprobe: 7.1 → 8.1.2
- HF CLI: 0.8.10 → 0.8.17

## 验证状态
全部 7 个文件编译通过 ✅

## 最终成品
| 文件 | 大小 | 说明 |
|------|------|------|
| 中国贸易朋友圈_hf_6视频版.mp4 | 3.3MB | HyperFrames 截图模式渲染 |
| 中国贸易朋友圈_hf_素材叠加版.mp4 | 3.3MB | 备用版本 |
| 中国贸易朋友圈_最终版_带字幕.mp4 | 7.5MB | 带字幕动态版 |
