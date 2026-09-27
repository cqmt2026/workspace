# TOOLS.md - 本地工具笔记（投资系统）

**最后更新**: 2026-09-05

---

## 数据源

| 来源 | 接口 | 说明 |
|------|------|------|
| MX API | MX_APIKEY | 实时行情、财务数据 |
| BaoStock | BS_TOKEN | 历史K线、指标 |
| 东方财富 | EM_API | 资金流向、板块 |

## 核心脚本

| 脚本 | 功能 |
|------|------|
| market_collector.py | 行情数据采集 |
| strategy_runner.py | 策略回测执行 |
| ml_predictor.py | ML模型训练/预测 |
| holding_monitor.py | 持仓监控 |
| daily_report.py | 日报生成推送 |

## 数据模型

- **SQLite**: `workspace-investment/data/market.db`
- **Pickle**: `workspace-investment/models/unified_model.pkl`
- **LightGBM**: `workspace-investment/models/lgb_model_v*.txt`

## 策略配置

- 尾盘策略：多Agent + 37项评分 + 8层风控
- 监控频率：每日3次（10:00/13:30/14:30）

---
_由可悦🌸 维护，2026-09-05_
