# 模型可用性完整审计报告（最终版 - 2026-09-25）

**检查时间**: 2026-09-25 18:31
**检查方法**: Python HTTP POST 实测（不同 provider 使用不同认证方式）
**当前默认模型**: agnes-25/agnes-2.5-flash ✅

---

## 一、可用的模型（7个）

### 对话模型（5个）

| # | Provider | Model ID | 名称 | 上下文 | 输入类型 | 响应时间 | 认证方式 |
|---|----------|----------|------|--------|----------|----------|----------|
| 1 | **agnes-25** | `agnes-2.5-flash` | agnes-2.5-flash | 512k | text | — | Bearer token |
| 2 | **agnes-ai** | `agnes-2.0-flash` | agnes-2.0-flash | 1M | text | 1.2s | Bearer token |
| 3 | **modal-glm** | `zai-org/GLM-5.1-FP8` | GLM-5.1-FP8 | 1M | text | 8.2s | Bearer token |
| 4 | **sensenova** | `deepseek-v4-flash` | DeepSeek-V4-Flash | 1M | text+image | 1.5s | **x-api-key** |

> 注：sensenova 使用 `x-api-key` header 认证，不是 Bearer token。这是其 API 的特殊要求。

### 图片生成模型（2个）

| # | Provider | Model ID | 端点 | 状态 |
|---|----------|----------|------|------|
| 5 | **agnes-ai** | `agnes-image-2.0-flash` | `/v1/images/generations` | ✅ 8.9s |
| 6 | **agnes-ai** | `agnes-image-2.1-flash` | `/v1/images/generations` | ✅ 10.0s |

### 视频生成模型（1个）

| # | Provider | Model ID | 端点 | 状态 |
|---|----------|----------|------|------|
| 7 | **agnes-ai** | `agnes-video-v2.0` | `/v1/videos` | ✅ 2.2s |

---

## 二、不可用的模型（11个）

### 🔴 Nvidia API EOL（4个）
| Provider | Model | EOL 日期 |
|----------|-------|----------|
| deepseek-ai | `deepseek-ai/deepseek-v4-pro` | 2026-08-07 |
| deepseek-ai | `deepseek-ai/deepseek-v4-flash` | 2026-08-07 |
| meta | `meta/llama-3.3-70b-instruct` | 2026-08-26 |
| mistralai | `mistralai/mistral-small-4-119b-2603` | 2026-07-27 |

> HTTP 410 Gone，明确返回 "has reached its end of life"。

### 🟡 Sensenova model ID 不存在（4个）
| Model ID (配置) | 原因 |
|-----------------|------|
| `deepseek-ai/deepseek-v4-flash` | 多了 `deepseek-ai/` 前缀 |
| `sensenova-u1-fast` | ID 不存在 |
| `sensenova-6.7-flash-lite` | ID 不存在 |
| `meta/llama-3.3-70b-instruct` | ID 不存在 |

> 仅 `deepseek-v4-flash` 在 sensenova 平台有效。

### 🟡 无有效 Key（3个）
| Provider | Model | 原因 |
|----------|-------|------|
| codex | gpt-5.4 / gpt-5.4-mini / gpt-5.2 | key 为空（特殊认证方式） |

---

## 三、关键发现

1. **sensenova 使用 x-api-key 认证**，不是 Bearer token。这是其 API 的特殊要求。
2. **models.json 的 apiKey 字段是脱敏显示**，但实际 key 有效（35字符）。
3. **图片/视频模型不能用 chat/completions 端点**，需用专用端点。
4. **OpenClaw 的 image_generate/video_generate 工具是独立的**，不通过 models.json 路由。

---

## 四、代理脚本

已创建两个代理脚本用于调用 agnes-ai 媒体生成 API：

| 脚本 | 用途 | 用法 |
|------|------|------|
| `agnes_image_proxy.py` | 文生图 | `python agnes_image_proxy.py "prompt" [model] [output_dir]` |
| `agnes_video_proxy.py` | 文生视频 | `python agnes_video_proxy.py "prompt" [duration] [output_dir]` |

---

## 五、建议修复

| 优先级 | 行动 |
|--------|------|
| P1 | 从 models.json 移除 Nvidia 端 4 个 EOL 模型配置 |
| P2 | 在 sensenova 平台确认 u1-fast / 6.7-flash-lite / llama-3.3-70b 的正确 model ID（如存在） |
| P3 | 将代理脚本纳入工作流 |
