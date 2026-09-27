# corrections.md - 投资分析搭档踩坑记录

**创建时间**: 2026-05-23
**最后更新**: 2026-06-12
**版本**: V1.0

---

## 记录规范

| 字段 | 说明 |
|------|------|
| 问题 | 现象描述 |
| 根因 | 为什么出错 |
| 触发条件 | 什么场景下触发 |
| 解法 | 解决方案 |
| 来源 | 实测/回测/主人纠正 |
| 日期 | 记录时间 |

---

## 🚧 待填充

（从第一次踩坑开始记录）

---

_由 可悦🌸 维护_

## 2026-06-13 [日志机制与记忆系统] 自动化必须绑定系统

### 问题
昨晚对话丢失，日志规则写在文档里但没有技术机制强制执行。

### 根因
自动化机制与系统核心是分离的，不是系统的一部分。

### 固化措施
- [x] 所有Cron任务必须通过run_with_log.py执行并记录日志
- [x] task_logger.py作为所有自动化的基础设施
- [x] Supermemory提取每30分钟自动运行
- [x] corrections.md由log_audit.py每日自动更新新踩坑
- [x] 系统迭代时，所有自动化必须同步迁移，不得丢失

_由可悦🌸 维护_

## 2026-06-15 [INV-Daily-Market-Update] Timeout after 600s

### 问题
INV-Daily-Market-Update 执行失败：Timeout after 600s

### 根因
待分析（详见当日日志审计报告）

### 固化措施
- [ ] 待填写

## 2026-06-22 [INV-RPS-每日推送] Script not found: workspace-investment\scripts\rps_psuh.py

### 问题
INV-RPS-每日推送 执行失败：Script not found: workspace-investment\scripts\rps_psuh.py

### 根因
Cron payload中脚本名拼写错误：rps_psuh.py → 应为 rps_push.py

### 固化措施
- [x] Cron已验证指向正确路径 workspace-investment\scripts\rps_push.py（该错误已于之前修复）

---

## 2026-06-22 Supermemory 服务宕机

### 问题
Supermemory API服务（端口8642）连接被拒绝，无法进行记忆提取和查询。

### 根因
supermemory npm包未安装，导致 `supermemory serve` 命令不存在。

### 固化措施
- [x] npm install -g supermemory 安装成功
- [x] Supermemory 服务已重启（PID 508），端口8642健康检查通过
- [x] 当前状态: 3230条记忆，服务正常

---

## 2026-06-22 [INV-Daily-Market-Update] LLM request failed

### 问题
INV-Daily-Market-Update 执行失败：LLM request failed（435776ms，约7.3分钟）

### 根因
数据采集实际完成，但LLM报告阶段token超限；超时限制仅600s不足

### 固化措施
- [x] 超时从600s增加至1200s（20分钟）
- [ ] 长期方案：考虑将数据采集与LLM报告分离为两个独立任务

## 2026-09-08 [INV-Closing-Strategy-尾盘14:30] Script not found: investment\scripts\strategy_scan.py

### 问题
INV-Closing-Strategy-尾盘14:30 执行失败：Script not found: investment\scripts\strategy_scan.py

### 根因
待分析（详见当日日志审计报告）

### 固化措施
- [ ] 待填写
