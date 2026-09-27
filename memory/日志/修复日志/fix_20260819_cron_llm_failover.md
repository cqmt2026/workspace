---
date: 2026-08-19
system: 主系统
type: 修复
severity: P0
---

# Cron LLM熔断修复

## 问题
6个Cron任务连续失败，所有错误模式一致：
- **timeout**: 模型调用超时（model-call-started阶段）
- **LLM request failed**: 模型调用直接失败

## 具体失败Cron

| Cron | 连续失败次数 | 错误类型 | 修复方案 |
|------|------------|---------|---------|
| Daily-Morning-Report-早间汇报 | 8次 | timeout | 加mixtral-675b fallback, timeout 300→600, lightContext |
| LOG-日志审计-每日检查 | 4次 | timeout | 同上 |
| 子系统健康检查 | 3次 | LLM request failed | 加mixtral-675b fallback, lightContext |
| INV-ZT-Kline-涨停K线收集 | 4次 | LLM request failed | 同上 |
| INV-Closing-Strategy-尾盘14:30 | 2次 | Agent无响应 | 同上 |
| 商业航天每日分析报告 | 1次 | LLM request failed | 同上 |

## 根因分析
所有失败Cron共同模式：deepseek-v4-flash模型不稳定，高峰期并发调用导致timeout或请求失败。fallback链不够深（只有agnes-2.0-flash/llama-3.3-70b/sense-6.7），没有覆盖到mixtral-675b这类更稳定的模型。

## 修复
1. 所有6个失败Cron的fallback链追加 `mistralai/mixtral-large-3-675b-instruct-2512`
2. 主系统Cron加 `lightContext: true` 减少上下文负载
3. timeout不足的从300s提升到600s

## 验证
- Cron配置已更新，下次触发时将使用新fallback链
- Self-Learning熔断器已恢复（consecutive_failures: 0, 最近2次OK）
- 15个废弃调试脚本已清理（scripts/_* 系列）

## 新增陷阱
| 陷阱 | 描述 | 修复方案 |
|------|------|---------|
| Cron LLM timeout | deepseek-v4-flash高峰期不稳定，导致连续8次timeout | fallback链必须包含mixtral-675b，加lightContext，timeout≥600s |