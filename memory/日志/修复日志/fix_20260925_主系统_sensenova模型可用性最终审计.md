# 修复日志：sensenova 模型可用性完整审计（最终版 2026-09-25）

**日期**: 2026-09-25
**子系统**: 主系统
**任务**: 根据官网文档重新验证 sensenova 所有模型可用性

## 执行步骤
1. 用户提供官网模型列表（7个模型）
2. 对每个模型 ID 调用 `/chat/completions` 端点
3. 使用正确的认证方式（x-api-key header）
4. 汇总结果并写入报告

## 发现
- 7 个官方模型中 5 个可用、2 个不可用
- 可用的 5 个都是对话模型
- 不可用的 2 个（U1.5 Lite/Fast）是图片生成模型，需要独立端点

## 可用模型（5个）
1. deepseek-flash (841ms) - DeepSeek V4.1 Flash
2. glm-5.2 (854ms) - GLM-5.2
3. deepseek-v4-flash (1238ms) - DeepSeek V4 Flash
4. sensenova-6.8-flash-lite (1657ms) - SenseNova 6.8 Flash Lite
5. kimi-k3 (4056ms) - Kimi K3

## 不可用模型（2个）
1. sensenova-u1.5-lite - 图片生成模型，需 `/v1/images/generations`
2. sensenova-u1.5-fast - 图片生成模型，需 `/v1/images/generations`

## 关键教训
1. 图片生成模型不能用 chat/completions 端点
2. 应该以官网文档为准，不要只看 models.json 配置
3. sensenova 使用 x-api-key 认证

## 建议行动
- 更新 models.json 中 sensenova provider 的配置
- 移除不存在的模型 ID
- 添加新发现的可用模型
- 图片模型需要单独配置 image generation 端点

## 验证
- 已完成 7 个官方模型的 HTTP 连通性实测
- 报告保存至 workspace/sensenova_model_audit_final_20260925.md
- 新陷阱已写入 shared-knowledge/系统知识图谱与常见陷阱手册.md
