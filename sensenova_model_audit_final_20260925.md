# sensenova 模型可用性完整报告（最终版 - 2026-09-25）

**数据来源**: 官网文档 + HTTP 实测验证

---

## 一、可用模型（5个对话模型）

| 模型名称 | Model ID | 响应时间 | 特性 |
|----------|----------|----------|------|
| **DeepSeek V4.1 Flash** | `deepseek-flash` | 841ms | 最新最快，推理+Agent+多模态 |
| **GLM-5.2** | `glm-5.2` | 854ms | 旗舰开源，1M 上下文，长程 Coding |
| **DeepSeek V4 Flash** | `deepseek-v4-flash` | 1238ms | 高效经济型，日常问答+代码辅助 |
| **SenseNova 6.8 Flash Lite** | `sensenova-6.8-flash-lite` | 1657ms | 轻量高效，数据分析+信息呈现 |
| **Kimi K3** | `kimi-k3` | 4056ms | 旗舰多模态，2.8T 参数，1M 上下文 |

---

## 二、不可用模型（2个）

| 模型名称 | Model ID | 状态 | 原因 |
|----------|----------|------|------|
| SenseNova U1.5 Lite | `sensenova-u1.5-lite` | ❌ 404 | 图片生成模型，需用 `/v1/images/generations` |
| SenseNova U1.5 Fast | `sensenova-u1.5-fast` | ❌ 404 | 图片生成模型，需用 `/v1/images/generations` |

---

## 三、认证方式

**sensenova 使用 `x-api-key` header 认证**，不是 Bearer token：

```http
POST /v1/chat/completions
Content-Type: application/json
x-api-key: sk-xxxxx...xxxxx

{
  "model": "deepseek-v4-flash",
  "messages": [{"role": "user", "content": "hi"}]
}
```

---

## 四、建议更新 models.json

```json
"sensenova": {
  "baseUrl": "https://token.sensenova.cn/v1",
  "apiKey": "***",
  "api": "openai-completions",
  "models": [
    {
      "id": "deepseek-flash",
      "name": "DeepSeek V4.1 Flash",
      "reasoning": true,
      "input": ["text"],
      "contextWindow": 1000000,
      "maxTokens": 65536
    },
    {
      "id": "glm-5.2",
      "name": "GLM-5.2",
      "reasoning": true,
      "input": ["text"],
      "contextWindow": 1000000,
      "maxTokens": 131072
    },
    {
      "id": "deepseek-v4-flash",
      "name": "DeepSeek V4 Flash",
      "reasoning": false,
      "input": ["text"],
      "contextWindow": 1000000,
      "maxTokens": 65536
    },
    {
      "id": "sensenova-6.8-flash-lite",
      "name": "SenseNova 6.8 Flash Lite",
      "reasoning": false,
      "input": ["text"],
      "contextWindow": 256000,
      "maxTokens": 65536
    },
    {
      "id": "kimi-k3",
      "name": "Kimi K3",
      "reasoning": true,
      "input": ["text", "image"],
      "contextWindow": 1048576,
      "maxTokens": 65536
    }
  ]
}
```

---

## 五、关键教训

1. **不要只看 models.json 配置**，应该调用 `/models` API 获取真实列表
2. **sensenova 使用 x-api-key 认证**，不是 Bearer token
3. **图片生成模型**（U1.5 Lite/Fast）不能用 chat/completions 端点
4. **版本号可能变化**：6.7 → 6.8
