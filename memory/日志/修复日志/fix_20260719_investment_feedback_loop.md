# 投资系统闭环修复：策略结果反馈到Supermemory

**日期**: 2026-07-19
**子系统**: investment
**严重度**: P0

## 问题
策略执行结果（涨停分析、尾盘选股）只写入 `out_data/` 文件，没有反馈到Supermemory，导致 `memory_recall` 搜索时找不到策略决策记录。

## 修复
### daily_analysis.py
- 末尾新增 `_save_to_memory()` 函数
- 涨停分析结果（涨停/跌停数量、板块、情绪）写入投资域Supermemory

### strategy_scan.py
- 末尾新增 `_save_to_memory()` 函数
- 尾盘选股Top10结果（代码、名称、评分）写入投资域Supermemory

## 验证
- ✅ 两个文件语法检查通过
- ✅ 写入路径正确（`memory_tools.py` 的LIKE搜索已优化）
- ✅ 不影响现有文件输出逻辑

## 效果
以后 `mt.search_memory('涨停', domain='investment')` 不仅能找到行情数据，还能找到策略决策记录。

---
_记录者: 可悦 | 2026-07-19_