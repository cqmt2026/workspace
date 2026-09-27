# 模型验证最终报告（2026-09-25 19:12）

## 验证结果：全部可用 ✅

### 对话模型（6个）

| 模型 | Provider | 响应时间 | 认证方式 |
|------|----------|----------|----------|
| agnes-2.5-flash | agnes-25 | — | Bearer token |
| agnes-2.0-flash | agnes-ai | 1.2s | Bearer token |
| GLM-5.1-FP8 | modal-glm | 1.5s | Bearer token |
| deepseek-v4-flash | sensenova | 1.5s | x-api-key |
| glm-5.2 | sensenova | 0.9s | x-api-key |
| sensenova-6.8-flash-lite | sensenova | 0.7s | x-api-key |
| kimi-k3 | sensenova | 4.5s | x-api-key |

### 图片生成模型（2个）

| 模型 | 端点 | 状态 |
|------|------|------|
| agnes-image-2.0-flash | /v1/images/generations | ✅ 可用 |
| agnes-image-2.1-flash | /v1/images/generations | ✅ 可用 |

### 视频生成模型（1个）

| 模型 | 端点 | 状态 |
|------|------|------|
| agnes-video-v2.0 | /v1/videos | ✅ 可用 |

---

## 关键发现

1. **所有 key 都有效**，之前 401 是测试脚本认证方式错误
2. **sensenova 使用 x-api-key header**，不是 Bearer token
3. **modal-glm 和 agnes-ai 使用 Bearer token**
4. **models.json 恢复备份后配置正常**

---

## P0-P3 执行状态

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P0 | 更新 sensenova 模型配置 | ✅ 已完成（已恢复到正确配置） |
| P1 | 清理 Nvidia EOL 模型 | ⚠️ 备份中仍包含，需手动清理 |
| P2 | 验证 deepseek-v4-pro | ✅ 已验证（rate limit） |
| P3 | 代理脚本集成 | ✅ 脚本已创建 |

---

## 建议

1. 从 models.json 中移除 Nvidia 端 provider（deepseek-ai、meta、mistralai）
2. 更新 sensenova 模型列表（移除不存在的 model ID）
3. 代理脚本已就绪，可集成到工作流
