# 投资知识库索引

**更新**: 2026-07-01

---

## 财报分析体系（核心框架）

| 文件 | 内容 |
|------|------|
| `财务分析/00-财报分析框架概览.md` | ⭐ 黄金三角框架 |
| `财务分析/01-价值投资体系.md` | 巴菲特体系 |
| `财务分析/02-成长股分析框架.md` | 成长股分析 |
| `财务分析/03-量化筛选指标.md` | 量化指标公式 |
| `财务分析/04-行业对比方法.md` | 同行对比 |

---

## 技术指标与分析工具（2026-04-30更新）

| 文件 | 内容 | 脚本 |
|------|------|------|
| `05-技术指标库.md` | MA/MACD/KDJ/RSI/BOLL/ATR | `technical_indicators.py` |
| `06-风控模块.md` | 止损/止盈/仓位 | `risk_management.py` |
| `07-舆情分析.md` | 新闻情绪 | `sentiment_analysis.py` |
| `08-量化回测.md` | 策略回测 | `backtest.py` |
| `09-机构研报.md` | 券商研报 | `research_report.py` |
| `10-资金流分析.md` | 主力动向/龙虎榜 | `money_flow.py` |
| `11-宏观数据.md` | GDP/利率/CPI/M2 | `macro_data.py` |
| `12-数据库模块.md` | SQLite行情库 | `market_db.py` |
| `13-AI-ML预测.md` | 机器学习预测 | `ml_predictor.py` |
| `14-监控告警.md` | 健康检查/告警 | `monitoring.py` |
| `15-每日推荐.md` | 每日选股自动化 | `daily_recommend.py` |
| `16-缠论分析.md` | 15+60分钟缠论 | `chan_analysis.py` |

---

## 股票池（689只）

| 分类 | 数量 |
|------|------|
| 核心池 | 188只 |
| 重点池 | 416只 |
| 观察池 | 85只 |

---

## 外部策略参考（学习笔记）

| 文件 | 来源 | 内容 |
|------|------|------|
| `交易数学底层逻辑_深度分析_20260702.md` | 抖音@数学有门道 | 8大数学定律深度分析 + 投资系统逐条对照 + P0/P1/P2优化优先级 |
| `香农索普13因子选股策略_20260701.md` | 抖音@香农索普 | 5维度13因子等权策略，侧重数据预处理和实战落地 |

---

## 核心脚本工具

| 脚本 | 功能 |
|------|------|
| `technical_indicators.py` | 技术指标 |
| `risk_management.py` | 风控 |
| `sentiment_analysis.py` | 舆情分析 |
| `backtest.py` | 量化回测 |
| `research_report.py` | 机构研报 |
| `money_flow.py` | 资金流分析 |
| `macro_data.py` | 宏观数据 |
| `market_db.py` | SQLite数据库 |
| `monitoring.py` | 监控告警 |
| `auto_risk_check.py` | 自动风控 |
| `cache.py` | 缓存模块 |
| `ml_predictor.py` | ML股价预测 |
| `strategies.py` | 12个量化策略 |
| `daily_recommend.py` | 每日推荐 |
| `chan_analysis.py` | 缠论分析 |
| `task_router.py` | 自动任务路由 |

---

## 系统能力（90分）

| 维度 | 能力 |
|------|------|
| 数据获取 | ✅ akshare/baostock/同花顺 |
| 技术分析 | ✅ 8大指标+12策略 |
| 缠论 | ✅ 15分钟+60分钟分析 |
| 风控 | ✅ 自动化止损/仓位 |
| 舆情/研报 | ✅ NLP+东财研报 |
| 资金流/宏观 | ✅ 主力动向/GDP |
| AI/ML | ✅ 股价预测 |
| 每日推荐 | ✅ 16:00自动 |
| 自动路由 | ✅ task_router.py |
| 实盘交易 | ⏸️ 待定 |