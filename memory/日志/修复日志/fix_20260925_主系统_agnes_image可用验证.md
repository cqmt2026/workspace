# 修复日志：agnes-image 模型可用性验证（2026-09-25）

**日期**: 2026-09-25
**子系统**: 主系统
**任务**: 验证 agnes-image-2.0/2.1 是否可用

## 执行步骤
1. 读取 models.json 获取真实 API key（51字符）
2. 分别测试两个模型的 `/v1/images/generations` 端点
3. 确认错误端点（`/chat/completions`）会返回 HTTP 400

## 发现
- **agnes-image-2.0-flash**: ✅ 可用，8.9s 返回图片 URL
- **agnes-image-2.1-flash**: ✅ 可用，10.0s 返回图片 URL
- 两个模型都需要用 `/v1/images/generations` 端点，不能用 chat/completions

## 原因分析
之前的检查报告中将这两个模型标记为"不可用"是因为：
1. 第一次测试用了错误的端点（`/chat/completions`）
2. 得到了 HTTP 400 错误，误判为模型不可用
3. 实际上只是端点用错了，模型本身是可用的

## 解决方案
- 已通过代理脚本 `agnes_image_proxy.py` 验证可用
- 图片生成成功，返回 URL 并可下载

## 修正报告
- 更新 `model_audit_final_20260925.md`
- 更新陷阱手册
