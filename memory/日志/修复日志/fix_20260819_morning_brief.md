# 修复日志 2026-08-19

## T07: data_api导入路径错误
**严重度**: 🔴 P0
**影响**: morning_brief.py持仓监控静默失败，显示价格=0.00
**根因**: `from scripts.data_api import DataAPI` 路径错误
**修复**: 改为 `from data_api import DataAPI`，并添加code标准化逻辑
**验证**: 持仓数据正确显示（英维克55.75，中国中免53.90）

## T08: portfolio字段名不一致
**严重度**: 🟡 P1
**影响**: 持仓成本显示为0.00，浮盈计算错误
**根因**: `portfolio.json`用`entry_price`字段，但代码查找`buy_price`/`cost`
**修复**: 添加`h.get('entry_price', h.get('buy_price', h.get('cost', 0)))`
**验证**: 浮盈正确计算（英维克-4511，中国中免-4242）

## 修复日志存档路径
`memory/日志/修复日志/fix_20260819_morning_brief.md`
