# 模型额度参考手册

> 创建时间：2026-10-05
> 状态：待补充各provider实际额度数据

---

## Provider查询链接

| Provider | 控制台链接 | API文档 | 当前状态 |
|----------|-----------|---------|----------|
| **SenseNova** | https://platform.sensenova.cn | https://platform.sensenova.cn/docs | ⚠️ 今日额度已用完 |
| **agnes-ai** | https://apihub.agnes-ai.com | https://docs.agnes-ai.com | ✅ 正常 |
| **Modal** | https://modal.com/dashboard | https://modal.com/docs | ✅ 正常（按量计费） |

---

## 模型清单与配置

### SenseNova（深度求索）

| 模型ID | 别名 | 上下文 | 功能 | 当前fallback优先级 |
|--------|------|--------|------|-------------------|
| sensenova/glm-5.2 | glm-5.2 | 1000k | 文本，推理 | fallback#1 |
| sensenova/sensenova-6.8-flash-lite | - | 256k | 文本，快速 | fallback#2 |
| sensenova/deepseek-v4-flash | ds-v4 | 1000k | 文本+图像 | fallback#4 |
| sensenova/kimi-k3 | - | 1049k | 文本+图像 | fallback#7 |

**限制说明**：
- 周额度60万tokens，5小时窗口6万tokens
- 高峰期易触发5小时窗口限流
- 错误表现：`billing error — API key has run out of credits`
- 建议：非紧急任务安排在5小时窗口重置后（每5小时重置一次）

### agnes-ai（银兰）

| 模型ID | 别名 | 上下文 | 功能 | 当前fallback优先级 |
|--------|------|--------|------|-------------------|
| agnes-25/agnes-2.5-flash | agnes-2.5-flash | 512k | 文本 | default（主模型） |
| agnes-ai/agnes-2.0-flash | agnes-2.0-flash | 1000k | 文本 | fallback#5 |

**限制说明**：
- 当前无明确额度限制记录
- 可能为按量计费或高额度套餐
- 建议：登录控制台确认实际额度

### Modal（GLM）

| 模型ID | 别名 | 上下文 | 功能 | 当前fallback优先级 |
|--------|------|--------|------|-------------------|
| modal-glm/zai-org/GLM-5.1-FP8 | glm-5.1 | 1000k | 文本 | fallback#6 |

**限制说明**：
- 按调用计费，无公开额度限制
- 适合备用fallback

---

## 今日错误记录

| 时间 | 任务 | 错误 | 根因 |
|------|------|------|------|
| 13:07 | skill-collection-review(main) | 429额度限制 | SenseNova每日额度用完 |
| 13:07 | Baidu-周报 | 429额度限制 | SenseNova每日额度用完 |

---

## 建议策略

### 1. 任务分层调度

| 层级 | 场景 | 推荐Provider | 时段建议 |
|------|------|-------------|----------|
| L1 | 核心自愈（fix/learn/validate） | agnes-ai | 任意时段 |
| L2 | 投资分析、代码生成 | Sensenova/Modal | 避开高峰 |
| L3 | 非紧急任务（周报/ review） | agnes-ai | 22:00后 |

### 2. Fallback链优化

当前顺序：`glm-5.2 → sensenova-6.8-flash-lite → agnes-2.5-flash → ds-v4 → agnes-2.0-flash → glm-5.1 → kimi-k3`

**问题**：前两个SenseNova模型今日已触发额度限制

**建议调整**：
```
agnes-2.5-flash → agnes-2.0-flash → glm-5.1 → ds-v4 → glm-5.2 → sensenova-6.8-flash-lite → kimi-k3
```

### 3. 额度监控

待实现功能：
- [ ] 每日自动检查各Provider剩余额度
- [ ] 剩余<20%时发送预警
- [ ] 额度用尽时自动切换Provider

---

## 2026-10-20 实际额度数据（主人提供）

### SenseNova 额度详情

| 指标 | 数值 |
|------|------|
| **周额度** | 600,000 tokens |
| **本周已用** | 599,999.824 tokens (99.99997%) |
| **5小时窗口** | 60,000 tokens |
| **5小时已用** | 59,093.18 tokens (98.5%) |
| **5小时重置** | 2026-10-20 21:10（已过） |
| **周额度重置** | 2026-10-21 18:10（明天） |
| **Flash-Lite专属池** | 600,000 tokens |

**结论**：
- ✅ 免费额度存在，每周60万tokens
- ⚠️ 已接近用完（99.99997%）
- ⏰ 明天18:10重置后恢复
- 🔴 当前触发billing error是因为5小时窗口超限（98.5%）

### 模型可用性分析

| 模型 | 状态 | 说明 |
|------|------|------|
| deepseek-v4-flash | ❌ 限流 | 5小时窗口超限 |
| sensenova-6.7-flash-lite | ✅ 可用 | Flash-Lite专属池独立 |
| sensenova-u1-fast | ⚠️ 未测试 | 可能共用额度 |

---

## 待补充信息

| Provider | 查询内容 | 状态 |
|----------|----------|------|
| agnes-ai | 账户余额/套餐 | ⏳ 待查询 |
| Modal | 计费单价 | ⏳ 待查询 |

---

_由可悦🌸 维护 | 最后更新：2026-10-05_
