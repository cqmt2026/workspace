# 修复日志：Cron任务批量超时修复

**日期**: 2026-08-26 16:20
**子系统**: 主系统/Cron调度
**严重度**: P1

## 问题

Gateway 16:03重启后，多个Cron任务连续超时失败：
1. MapHot-选题采集：连续2-3次失败
2. Cross-System-Bridge：连续4次超时
3. INV-ML-Training：2277s超时（timeout 2400s不够）
4. INV-Closing-Strategy：300s不够
5. Obsidian-决策信号更新：300s不够
6. Self-Heal-L1-Monitor：120s不够

## 根因

1. **MapHot脚本路径错误**：cron配置指向 scripts/core/选题采集_v3.py，实际文件在 scripts/选题采集_v3.py
2. **timeout普遍不足**：isolated agent setup + model call 额外耗时 60-120s，未计入原始timeout
3. **无fallback模型**：主模型超时后直接失败，没有降级到备用模型
4. **Gateway重启放大效应**：重启后大量任务并发重试，加剧资源争抢

## 修复

| 任务 | 修复项 | 旧值 → 新值 |
|------|--------|------------|
| MapHot-选题采集 | 脚本路径 | core/选题采集_v3.py → 选题采集_v3.py |
| MapHot-选题采集 | timeout | 120s → 180s |
| MapHot-选题采集 | fallback | 无 → agnes-2.0-flash + llama-3.3-70b |
| Cross-System-Bridge | timeout | 120s → 300s |
| Cross-System-Bridge | fallback | 无 → agnes-2.0-flash + llama-3.3-70b |
| INV-ML-Training | timeout | 2400s → 3600s |
| INV-ML-Training | fallback | 无 → agnes-2.0-flash + llama-3.3-70b |
| INV-Closing-Strategy | timeout | 300s → 600s |
| INV-Closing-Strategy | fallback | 无 → agnes-2.0-flash + llama-3.3-70b + sense-6.7 |
| Obsidian-决策信号更新 | timeout | 300s → 600s |
| Self-Heal-L1-Monitor | timeout | 120s → 180s |

## 验证

- MapHot 和 Cross-System-Bridge 已手动触发重跑（正在执行中）
- TOOLS.md 路径已同步修正
- 下一个心跳周期验证所有任务是否恢复正常

## 陷阱记录

| 日期 | 子系统 | 陷阱描述 | 修复方案 | 严重度 |
|------|--------|---------|---------|--------|
| 2026-08-26 | Cron | MapHot脚本路径引用了不存在的core/子目录 | 修正为scripts/根目录 | P1 |
| 2026-08-26 | Cron | isolated agent setup 额外耗时60-120s未计入timeout | 统一增加50% buffer | P1 |
