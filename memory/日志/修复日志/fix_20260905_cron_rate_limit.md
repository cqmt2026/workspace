# Cron Rate Limit 修复日志

**日期**: 2026-09-05
**子系统**: 主系统/Cron
**严重度**: 高

## 问题回顾

13个Cron任务因API rate limit失败（429 tpm/rpm exhausted）

## 修复尝试

### 方案A: 切换模型 ✅ 已诊断
- 目标：将5个关键任务的model从`deepseek-v4-flash`改为`sensenova/sensenova-6.7-flash-lite`
- 原因：sense-6.7速度更快，token消耗更少，降低rate limit概率
- **状态**：遇到权限限制（"scheduled account policy must match the persisted job owner"）

### 方案B: 错峰调度 ⏸️ 待执行
- 将高失败率任务分散到不同时区
- 早间（06-09点）: 轻量任务
- 午间（12-14点）: 中等任务
- 晚间（20-23点）: 重量任务

### 方案C: 合并任务 ⏸️ 待执行
- P0+P1+P2+P3 → 合并为"知识库维护任务"
- 减少API调用次数

## 当前状态

| 任务 | 当前model | 建议model | 连续失败 | 状态 |
|------|-----------|-----------|----------|------|
| AI-Retry-错题AI重试 | deepseek-v4-flash | sense-6.7 | 5次 | ⚠️ 需人工修改 |
| INV-Daily-Analysis | deepseek-v4-flash | sense-6.7 | 4次 | ⚠️ 需人工修改 |
| Daily-Evening-Report | deepseek-v4-flash | sense-6.7 | 4次 | ⚠️ 需人工修改 |
| Memory-Recall | deepseek-v4-flash | sense-6.7 | 6次 | ⚠️ 需人工修改 |
| Self-Learning-统一学习 | deepseek-v4-flash | sense-6.7 | 4次 | ⚠️ 需人工修改 |

## 手动修复命令

主人可在OpenClaw Control UI或命令行执行：

```bash
# 方法1: 使用openclaw cron edit命令
openclaw cron edit 2efc38a0-8613-42d7-82cd-2951429ebdd0 --model sensenova/sensenova-6.7-flash-lite

# 方法2: 修改openclaw.json配置文件
# 找到对应job的payload.model字段，改为"sensenova/sensenova-6.7-flash-lite"

# 方法3: 在Control UI的Cron管理页面手动修改
```

## 其他可立即执行的优化

1. **增加timeout**（部分任务已配置）：
   - AI-Retry: 120s → 180s
   - Memory-Recall: 300s → 180s（已够）
   - Self-Learning: 900s → 600s（已够）

2. **添加staggerMs**（避免并发）：
   - 在schedule中添加"staggerMs": 300000（5分钟延迟）

---
_记录人：可悦 | 2026-09-05 11:40_
