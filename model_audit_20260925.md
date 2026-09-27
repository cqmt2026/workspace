# 模型可用性审计报告

**检查时间**: 2026-09-25 17:51
**检查方法**: 逐 provider 发 HTTP 实测请求（`/chat/completions`，发送 "hi"，max_tokens=5）

---

## 一、可用的模型（3个）

| Provider | Model ID | 名称 | 输入类型 | 上下文 | 响应时间 |
|----------|----------|------|----------|--------|----------|
| modal-glm | `zai-org/GLM-5.1-FP8` | GLM-5.1-FP8 | text | 1M | 1.9s |
| agnes-ai | `agnes-2.0-flash` | agnes-2.0-flash | text | 1M | 1.3s |
| sensenova | `deepseek-v4-flash` | DeepSeek-V4-Flash | text+image | 1M | 1.5s |

**当前默认模型**: `sensenova/deepseek-v4-flash` ✅ 正常工作

---

## 二、无法使用的模型（12个，含 4 类问题）

### 问题1: API Key 被截断/损坏 — agnes-25
```
agnes-25:apiKey = "sk-UF8…pN9e"   (长度仅11，含Unicode省略号)
```
**影响**: `agnes-25/agnes-2.5-flash`（fallback#1）无法使用

### 问题2: Nvidia API 返回 410 Gone — deepseek-ai / meta / mistralai
所有通过 Nvidia integrate.api 的模型全部返回 `410 Gone`：
- `deepseek-ai/deepseek-v4-pro` ❌
- `deepseek-ai/deepseek-v4-flash` ❌
- `meta/llama-3.3-70b-instruct` ❌
- `mistralai/mistral-small-4-119b-2603` ❌

**影响**: fallback#2~#6 全部失效（agnes-2.0-flash, sense-6.7, u1-fast, glm-5.1, llama-3.3-70b）

### 问题3: Sensenova 模型 ID 不匹配 — 4个404
sensenova provider 有5个模型配置，但只有 `deepseek-v4-flash` 能通：
- `deepseek-ai/deepseek-v4-flash` ❌ (404)
- `sensenova-u1-fast` ❌ (404)
- `sensenova-6.7-flash-lite` ❌ (404)
- `meta/llama-3.3-70b-instruct` ❌ (404)

**原因**: model ID 与实际部署的不一致（可能是命名映射问题）

### 问题4: 图片/视频模型 — HTTP 400（非对话接口）
- `agnes-ai/agnes-image-2.0-flash` ❌ (400 - 需用 `/v1/images/generations`)
- `agnes-ai/agnes-image-2.1-flash` ❌ (400 - 同上)
- `agnes-ai/agnes-video-v2.0` ❌ (400 - 需用 `/v1/video/generations`)

---

## 三、Catalog 条目 vs 实际配置

`openclaw models list` 列出 38+ 个模型，但实际在 `models.json` 中配置的 provider 只有 9 个：
- `bailian` (空 models)
- `modal-glm` ✅
- `codex` (特殊 key，跳过)
- `agnes-ai` ✅
- `sensenova` ✅
- `deepseek-ai` ❌ (410)
- `meta` ❌ (410)
- `mistralai` ❌ (410)
- `agnes-25` ❌ (key 截断)

大量 `modelstudio/`、`moonshot/`、`qwen/` 开头的模型出现在 catalog 列表但**没有对应 provider 配置**，这些是 OpenClaw 自动扫描 catalog 后展示的"潜在可用"条目，实际调用会失败。

---

## 四、当前 fallback 链状态

```
默认: sensenova/deepseek-v4-flash         ✅ OK (1.5s)
fallback#1: agnes-25/agnes-2.5-flash      ❌ key 截断
fallback#2: agnes-ai/agnes-2.0-flash      ✅ OK (1.3s) [但不在 fallback 链中，是直接配置的]
fallback#3: sensenova/sensenova-6.7-flash-lite  ❌ 404
fallback#4: sensenova/sensenova-u1-fast       ❌ 404
fallback#5: modal-glm/zai-org/GLM-5.1-FP8   ✅ OK (1.9s)
fallback#6: meta/llama-3.3-70b-instruct     ❌ 410 (Nvidia)
fallback#7: deepseek-ai/deepseek-v4-flash   ❌ 410 (Nvidia) + ❌ 404 (sensenova ID)
```

**结论**: 3 个可用 + 9 个不可用。fallback 链只剩 agnes-ai/agnes-2.0-flash 和 modal-glm/GLM-5.1-FP8 两个后备。

---

## 五、建议修复优先级

| 优先级 | 问题 | 修复动作 |
|--------|------|----------|
| P0 | agnes-25 key 截断 | 重新 paste 完整 API key (`openclaw models auth paste-api-key --provider agnes-25`) |
| P1 | Nvidia 端 410 Gone | 确认 Nvidia API 是否已下线这些模型；如已下线，从配置中移除 deepseek-ai/meta/mistralai provider |
| P2 | sensenova 404 模型 | 确认 sensenova 平台正确的 model ID，更新 models.json |
| P3 | agnes-image/agnes-video | 确认是否需要单独配置 image/video 端点 |
