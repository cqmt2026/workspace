# 修复日志：memory.db 缺少 entities 列

**日期**: 2026-07-18
**子系统**: 记忆层（Supermemory）
**触发**: self_learning.py 清理步骤失败，报 memory_tools 模块缺失（实际是 entities 列缺失导致写入失败）

## 问题描述

- `F:/supermemory/memory.db` 中 `memories` 表缺少 `entities` 列
- 5 个分库 DB（memory_novel/memory_investment/memory_social/memory_math/memory_system）均有 `entities` 列
- 全局 DB 有额外列（event_date, superseded_by, created_at, updated_at）但缺少 entities
- 说明全局 DB 是更早版本创建，未随 schema 升级同步

## 根因

分库 DB 由 `memory_tools.py` 的 `_ensure_db()` 创建（含 entities 列），而全局 DB `memory.db` 是在更早版本创建，创建脚本没有包含 entities 列。后续 schema 升级只覆盖了分库，全局 DB 被遗漏。

## 修复方案

```sql
ALTER TABLE memories ADD COLUMN entities TEXT;
```

## 验证结果

- 写入全局 DB：✅ 成功
- 写入分库 DB（system）：✅ 成功
- 全局 DB 搜索：✅ 找到 1 条
- 分库 DB 搜索：✅ 找到 3 条

## 长期措施

- `_ensure_db()` 函数应改为 **幂等升级** 模式：每次连接时检查所有预期列是否存在，缺失则 ALTER TABLE ADD COLUMN
- 或者统一所有 DB 由同一个 migration 脚本创建

## 关联文件

- `memory/memory_tools.py` - 包含 `_ensure_db()` 函数
- `F:/supermemory/memory.db` - 修复后的全局 DB