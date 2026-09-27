# 模型官方文档查阅报告（2026-09-25）

## 执行方法
由于网络限制（web_search 不可用，部分网站被 Cloudflare 拦截），采用以下方法：
1. 通过 OpenClaw 内置 catalog 获取模型信息
2. 通过 HTTP API 实测验证可用模型
3. 对用户提供的 sensenova 官方文档进行核对

---

## 一、Modal (modal-glm)

### 官方文档状态
- ✅ 可访问：https://modal.com/llms.txt（完整文档索引）
- ✅ 可访问：https://modal.com/llms-full.txt（完整文档）

### 已验证模型
| Model ID | 名称 | 状态 | 备注 |
|----------|------|------|------|
| `zai-org/GLM-5.1-FP8` | GLM-5.1-FP8 | ✅ 可用 | 8.2s 响应，1M 上下文 |

### 文档要点
- Modal 是 AI 推理平台，支持 GPU 推理
- GLM-5.1-FP8 是智谱 AI 的模型，通过 Modal 部署
- 认证方式：Bearer token（modalres_前缀的 key）

---

## 二、Agnes AI (agnes-ai / agnes-25)

### 官方文档状态
- ❌ 被 Cloudflare 拦截：https://apihub.agnes-ai.com/docs
- ⚠️ 无法直接访问官方文档

### 已验证模型
| Model ID | 名称 | 状态 | 端点 | 备注 |
|----------|------|------|------|------|
| `agnes-2.5-flash` | agnes-2.5-flash | ✅ 可用 | /chat/completions | 当前默认，512k 上下文 |
| `agnes-2.0-flash` | agnes-2.0-flash | ✅ 可用 | /chat/completions | 1.2s 响应，1M 上下文 |
| `agnes-image-2.0-flash` | agnes-image-2.0-flash | ✅ 可用 | /v1/images/generations | 8.9s 响应 |
| `agnes-image-2.1-flash` | agnes-image-2.1-flash | ✅ 可用 | /v1/images/generations | 10.0s 响应 |
| `agnes-video-v2.0` | agnes-video-v2.0 | ✅ 可用 | /v1/videos | 2.2s 响应，异步任务 |

### 文档要点
- 两个域名：
  - 国内站：https://api.agnes-ai.cn/v1（agnes-25 provider）
  - 国际站：https://apihub.agnes-ai.com/v1（agnes-ai provider）
- 认证方式：Bearer token
- 图片生成：`/v1/images/generations`
- 视频生成：`/v1/videos`

---

## 三、Sensenova（日日新）

### 官方文档状态
- ✅ 用户提供了完整模型列表
- ⚠️ 官网部分页面 404，但 API 可用

### 已验证模型（来自用户提供的官方文档）
| 模型名称 | Model ID | 状态 | 响应时间 | 类型 |
|----------|----------|------|----------|------|
| DeepSeek V4.1 Flash | `deepseek-flash` | ✅ 可用 | 841ms | 对话 |
| GLM-5.2 | `glm-5.2` | ✅ 可用 | 854ms | 对话 |
| DeepSeek V4 Flash | `deepseek-v4-flash` | ✅ 可用 | 1238ms | 对话 |
| SenseNova 6.8 Flash Lite | `sensenova-6.8-flash-lite` | ✅ 可用 | 1657ms | 对话 |
| Kimi K3 | `kimi-k3` | ✅ 可用 | 4056ms | 对话 |
| SenseNova U1.5 Lite | `sensenova-u1.5-lite` | ❌ 404 | — | 图片生成（需独立端点） |
| SenseNova U1.5 Fast | `sensenova-u1.5-fast` | ❌ 404 | — | 图片生成（需独立端点） |

### 官方文档要点（用户提供）
1. **SenseNova 6.8 Flash Lite**：轻量高效的多模态智能体模型，面向真实复杂任务，适配数据分析和复杂信息呈现场景
2. **SenseNova U1.5 Lite**：新一代图片创作模型，基于 Neo-unify 架构，生成与编辑一体，支持参考图功能及灵活修改
3. **SenseNova U1.5 Fast**：图片创作模型加速版，基于 Neo-unify 架构，即时创作，高效修改
4. **DeepSeek V4 Flash**：高效经济型通用模型，在平衡推理与 Agent 能力的同时，速度更快、效率更优
5. **DeepSeek V4.1 Flash**：新一代高效通用模型，兼顾推理效率与成本，强化推理、Agent 与多模态理解能力
6. **GLM-5.2**：智谱旗舰开源模型，面向长程 Coding 与复杂工程任务，支持 1M 上下文
7. **Kimi K3**：月之暗面旗舰开源原生多模态 Agent 模型，2.8T 参数，原生视觉能力，1M 上下文

### 认证方式
- **x-api-key** header（不是 Bearer token）
- Key 格式：`sk-8lD...nQakA7Q9`（35字符）

---

## 四、Nvidia (deepseek-ai / meta / mistralai)

### 官方文档状态
- ✅ 可访问：https://docs.nvidia.com/nemo/megatron-model-family/index.html
- ⚠️ 部分模型已 EOL

### 已验证模型状态
| Model ID | 状态 | EOL 日期 | 原因 |
|----------|------|----------|------|
| `deepseek-ai/deepseek-v4-pro` | ❌ 410 Gone | 2026-08-07 | 官方下线 |
| `deepseek-ai/deepseek-v4-flash` | ❌ 410 Gone | 2026-08-07 | 官方下线 |
| `meta/llama-3.3-70b-instruct` | ❌ 410 Gone | 2026-08-26 | 官方下线 |
| `mistralai/mistral-small-4-119b-2603` | ❌ 410 Gone | 2026-07-27 | 官方下线 |

### 官方文档要点
- Nvidia AI Foundation Models 已下线多个模型
- 建议使用其他 provider（如 sensenova、modal-glm）替代

---

## 五、未查阅的 Provider

| Provider | 状态 | 原因 |
|----------|------|------|
| bailian | ⚠️ 未测试 | models.json 中无模型配置 |
| codex | ⚠️ 未测试 | key 为空，需要特殊认证 |
| minimax-portal | ⚠️ 未测试 | OAuth 认证，无 API key |
| modelstudio | ⚠️ 未测试 | key 已过期（2026-05-07） |
| moonshot | ⚠️ 未测试 | key 指向 Nvidia（已 EOL） |

---

## 六、建议

1. **更新 models.json**：
   - 移除 Nvidia 端 4 个 EOL 模型
   - 修正 sensenova 的 model ID（6.7 → 6.8）
   - 移除不存在的 sensenova 模型（u1-fast 等）
   - 添加新发现的 sensenova 模型（glm-5.2、kimi-k3、deepseek-flash）

2. **补充文档**：
   - 为 agnes-ai 整理官方 API 文档（需手动访问）
   - 为 modal-glm 整理 GLM 模型文档

3. **清理配置**：
   - 移除无效 provider（bailian、codex）
   - 更新过期 key（modelstudio）
