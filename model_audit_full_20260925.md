# 模型可用性完整审计报告（最终版）

**检查时间**: 2026-09-25 17:57-18:17
**检查方法**: Python HTTP POST 实测 + auth store 验证 + session_status 确认
**当前默认模型**: agnes-25/agnes-2.5-flash ✅（session 正在使用）

---

## 一、实际可用的模型（4个对话 + 2个媒体生成）

### 对话模型（4个）

| # | Provider | Model ID | 名称 | 上下文 | 输入类型 | 响应时间 | 状态确认 |
|---|----------|----------|------|--------|----------|----------|----------|
| 1 | **agnes-25** | `agnes-2.5-flash` | agnes-2.5-flash | 512k | text | — | ✅ **当前默认，session 正在使用** |
| 2 | **agnes-ai** | `agnes-2.0-flash` | agnes-2.0-flash | 1M | text | ~1.5s | ✅ HTTP 实测通过 |
| 3 | **modal-glm** | `zai-org/GLM-5.1-FP8` | GLM-5.1-FP8 | 1M | text | ~1.5s | ✅ HTTP 实测通过 |
| 4 | **sensenova** | `deepseek-v4-flash` | DeepSeek-V4-Flash | 1M | text+image | ~1.6s | ✅ HTTP 实测通过 |

### 媒体生成模型（2个可用）

| # | Provider | Model ID | 端点 | 状态 |
|---|----------|----------|------|------|
| 5 | **agnes-ai** | `agnes-image-2.1-flash` | `/v1/images/generations` | ✅ 实测通过，返回图片 URL |
| 6 | **agnes-ai** | `agnes-video-v2.0` | `/v1/videos` | ✅ 端点可用，返回 queued 状态 |

---

## 二、不可用的模型（11个）

### 🔴 Nvidia API EOL（4个）
| Provider | Model | EOL 日期 |
|----------|-------|----------|
| deepseek-ai | `deepseek-ai/deepseek-v4-pro` | 2026-08-07 |
| deepseek-ai | `deepseek-ai/deepseek-v4-flash` | 2026-08-07 |
| meta | `meta/llama-3.3-70b-instruct` | 2026-08-26 |
| mistralai | `mistralai/mistral-small-4-119b-2603` | 2026-07-27 |

### 🟡 Sensenova model ID 不匹配（4个）
| Model ID (配置) | 实际正确 ID |
|-----------------|-------------|
| `deepseek-ai/deepseek-v4-flash` | `deepseek-v4-flash` |
| `sensenova-u1-fast` | 需确认 |
| `sensenova-6.7-flash-lite` | 需确认 |
| `meta/llama-3.3-70b-instruct` | 需确认 |

---

## 三、解决方案：代理脚本

已创建两个代理脚本，用于调用 agnes-ai 的媒体生成 API：

| 脚本 | 用途 | 用法 |
|------|------|------|
| `agnes_image_proxy.py` | 文生图 | `python agnes_image_proxy.py "prompt" [model] [output_dir]` |
| `agnes_video_proxy.py` | 文生视频 | `python agnes_video_proxy.py "prompt" [duration] [output_dir]` |

**实测结果**：
- 图片生成：✅ 成功，10s 返回 URL，图片已下载到本地
- 视频生成：端点可用，返回 queued 状态（视频生成是异步任务）

---

## 四、关键发现

1. **models.json 的 apiKey 是截断/脱敏显示**，不是真实 key。真实 key 存储在 Gateway 的加密 auth store 中。
2. **agnes-image/agnes-video 不能用 chat/completions 端点**，需要用独立的 `/images/generations` 和 `/videos` 端点。
3. **OpenClaw 的 image_generate/video_generate 工具是独立的**，不通过 models.json 路由。如需集成 agnes-ai 的媒体生成，需要通过代理脚本或自定义插件。

---

## 五、建议修复

| 优先级 | 行动 |
|--------|------|
| P1 | 从 models.json 移除 Nvidia 端 4 个 EOL 模型配置 |
| P2 | 在 sensenova 平台确认 u1-fast / 6.7-flash-lite / llama-3.3-70b 的正确 model ID |
| P3 | 将代理脚本纳入工作流（地图热点等需要图片/视频生成的场景） |
