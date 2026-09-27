# 修复日志：TOOLS.md/HEARTBEAT.md 从主系统根目录消失

**日期**: 2026-09-05
**子系统**: 主系统
**严重度**: 中

## 问题描述

2026-09-05 系统深度检查时发现：
- 主系统根目录 `TOOLS.md` (15KB) 和 `HEARTBEAT.md` (7KB) 不存在
- 但 `backup/full_20260903_214200/` 中这两个文件完好（mtime: 08-28 和 08-26）
- AGENTS.md 引用了 TOOLS.md，导致引用断裂

## 根因分析

1. **不是脚本删除**：`auto_cleanup.py` 只清理 C 盘 Temp/缓存，不碰 workspace
2. **不是 git 操作**：workspace 根目录不是 git 仓库，无操作日志
3. **时间窗口**：09-03 备份时文件存在 → 09-05 检查时发现缺失
4. **最可能原因**：手动移动/删除，或某次未记录的维护操作

## 修复方案

1. 从备份恢复：`cp backup/full_20260903_214200/TOOLS.md workspace/`
2. 从备份恢复：`cp backup/full_20260903_214200/HEARTBEAT.md workspace/`
3. MD5 校验一致，恢复完整
4. 同步清理 64 个空目录（backup 内残留）

## 验证

- ✅ TOOLS.md: 15014 bytes, MD5=cf6218518748cd0c8150e60635f85798
- ✅ HEARTBEAT.md: 7296 bytes, MD5=d0b9c7a6b7edb810df268683fb36d1f0
- ✅ AGENTS.md 引用恢复有效

## 教训

1. workspace 根目录非 git 仓库，无法追溯文件变更历史
2. 建议关键文档增加 git 追踪或定期备份到版本控制
3. 系统级文档（TOOLS/HEARTBEAT）应纳入备份策略重点保护

---
_记录人：可悦 | 2026-09-05 11:20_
