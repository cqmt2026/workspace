# sensenova 模型可用性完整报告（2026-09-25）

## 测试方法
1. 调用 `/models` API 获取平台所有可用模型列表
2. 对每个模型 ID 调用 `/chat/completions` 端点
3. 使用 `x-api-key` 认证（不是 Bearer token）

## 结果

### ✅ 可用模型（4个）

| Model ID | 响应时间 | 说明 |
|----------|----------|------|
| `deepseek-v4-flash` | 1723ms | DeepSeek V4 Flash，1M 上下文 |
| `glm-5.2` | 792ms | GLM-5.2，1M 上下文，最快 |
| `sensenova-6.8-flash-lite` | 513ms | SenseNova 6.8 Flash Lite，最快 |
| `kimi-k3` | 4301ms | Kimi K3，262k 上下文 |

### ❌ 不可用模型（5个）

| Model ID | 状态 | 原因 |
|----------|------|------|
| `sensenova-u1-fast` | 404 | 平台不存在 |
| `sensenova-u1.5-lite` | 404 | 平台不存在 |
| `deepseek-v4-pro` | 429 | Rate limit（配额限制） |
| `deepseek-flash` | 429 | Rate limit（配额限制） |
| `deepseek-v4.1-flash` | 403 | 当前 token plan 不可用 |

## 关键发现

1. **sensenova 使用 `x-api-key` 认证**，不是 Bearer token
2. **models.json 配置有误**：
   - 配置了 `sensenova-6.7-flash-lite`，但实际是 `sensenova-6.8-flash-lite`
   - 配置了 `sensenova-u1-fast` 和 `sensenova-u1.5-lite`，但平台不存在
   - 配置了 `meta/llama-3.3-70b-instruct`，但平台不存在
3. **新发现的可用模型**：`glm-5.2`、`kimi-k3`、`sensenova-6.8-flash-lite`、`deepseek-v4.1-flash`（403）

## 建议

需要更新 models.json 中 sensenova provider 的配置：
- 移除不存在的模型 ID
- 添加新发现的可用模型
- 修正版本号（6.7 → 6.8）
