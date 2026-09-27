# 修复日志：sensenova 模型可用性完整审计（2026-09-25）

**日期**: 2026-09-25
**子系统**: 主系统
**任务**: 彻底检查 sensenova 下所有模型的可用性

## 执行步骤
1. 调用 `/models` API 获取平台所有可用模型列表
2. 对每个模型 ID 调用 `/chat/completions` 端点
3. 使用正确的认证方式（x-api-key header）
4. 汇总结果并写入报告

## 发现
- sensenova 平台实际有 9 个模型
- 其中 4 个可用：deepseek-v4-flash、glm-5.2、sensenova-6.8-flash-lite、kimi-k3
- 5 个不可用：u1-fast（404）、u1.5-lite（404）、v4-pro（429）、flash（429）、v4.1-flash（403）

## 关键教训
1. **不要只看 models.json 配置**，应该直接调用 `/models` API 获取真实列表
2. **sensenova 使用 x-api-key 认证**，不是 Bearer token
3. **版本号可能变化**：6.7 → 6.8

## 建议行动
- 更新 models.json 中 sensenova provider 的配置
- 移除不存在的模型 ID
- 添加新发现的可用模型

## 验证
- 已完成 9 个模型的 HTTP 连通性实测
- 报告保存至 workspace/sensenova_model_audit_20260925.md
- 新陷阱已写入 shared-knowledge/系统知识图谱与常见陷阱手册.md
