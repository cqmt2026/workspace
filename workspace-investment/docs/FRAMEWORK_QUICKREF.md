# AliceQuant 框架速查表

> 版本：v4.3 | 更新：2026-07-05 | 快速查阅用，详细设计见 FRAMEWORK_DESIGN.md

---

## 整体架构

```
DataHub → Feature → Strategy → Portfolio → Backtest → Execute
     ↑          ↕           ↑          ↓
     └── ModelTrain (预计算)   └── Dashboard (只读)
     └── ConfigManager / Logger (贯穿所有层)
```

## 7层 + 2管理 + 1监控

| 层 | 目录 | 核心职责 |
|----|------|---------|
| 数据层 | data/ | 数据版本管理、时间旅行、按需加载、质量降级 |
| 特征工程 | features/ | 因子计算/筛选/IC监控、预加载、LRU缓存 |
| 模型训练 | models/ | 离线训练、预计算推理、模型生命周期管理 |
| 策略层 | strategies/ | 策略基类、因子缓存、置信度校准 |
| 组合管理 | strategies/portfolio.py | 策略依赖解析、仓位计算、资金管理、风险预算 |
| 回测层 | backtest/ | 事件循环、成交量限制、Walk-Forward、显著性检验 |
| 执行层 | execution/ | 信号处理、风控(黑白名单)、模拟交易、紧急停止 |
| 配置管理 | core/config.py | 统一配置入口，支持热更新 |
| 日志管理 | core/logger.py | 结构化日志，统一输出 |
| 监控层 | dashboard/ | 绩效/风险/告警/自动化报告/系统监控 |

## 层间依赖规则

```
允许: Execute → Backtest → Portfolio → Strategy → Feature → DataHub
      ModelTrain → Feature → DataHub
      Dashboard → 所有层 (只读)
禁止: Strategy → DataHub, Strategy → ModelTrain, Backtest → Feature
```

## 核心数据标准

| 对象 | 所在文件 | 关键字段 |
|------|---------|---------|
| Signal | core/signal.py | date/code/direction/price/volume/weight/confidence/reason |
| Order | core/order.py | order_id/date/code/price/volume/status/filled_price |
| Account | core/account.py | date/total_value/cash/positions |
| Position | core/account.py | code/volume/avg_cost/current_price/profit |
| Context | core/context.py | current_date/all_dates/account/portfolio_signals |
| BacktestResult | core/result.py | sharpe/max_drawdown/win_rate/significance |

## 目录结构

```
alice_quant/
├── core/               # 核心: config/logger/context/result/signal/order/account
├── data/               # 数据层: datahub/version/snapshot/quality/cache/sources/
├── features/           # 特征工程: engine/registry/auto_feature/selection/store/calculators/
├── models/             # 模型训练: sample/feature/trainers/evaluator/inference/monitor/scheduler
├── strategies/         # 策略层: base/portfolio/pipeline/trend/dabanz/magic_formula
├── backtest/           # 回测层: engine/order/account/commission/slippage/performance/overfitting
├── execution/          # 执行层: signal_handler/risk_manager/paper_trading/emergency_stop
├── dashboard/          # 监控层: performance/risk_panel/alerts/monitor/auto_report
├── examples/           # 示例: run_backtest/create_strategy/run_optimization
├── config/             # 配置: default/data/features/models/strategies/backtest/risk
├── data/               # 数据存储: raw/factors/models/results/snapshots
├── reports/            # 报告输出: charts/backtest_*.html
└── docs/               # 文档: QUICKSTART/FRAMEWORK_DESIGN/API
```

## 修复历史

| 版本 | 修复内容 |
|------|---------|
| v1.0 | 初版6层架构 |
| v3.0 | 加ConfigManager/Logger/层间依赖规则 |
| v4.0 | 加模型训练层/数据版本管理/时间旅行/预计算模式/Portfolio独立层/结果数据库/风控回传 |
| v4.1 | 加数据源监控/成交量限制/Walk-Forward/显著性检验/策略上线标准 |
| v4.2 | 加按需加载/尾盘模拟/策略依赖解析/仓位计算统一/前瞻检测/嵌套CV |
| v4.3 | 加依赖管理/Context/Result定义/示例代码/快速开始/ML使用规范/模拟交易模式 |

---

_速查: Alice | 2026-07-05_