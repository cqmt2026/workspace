# AGENTS.md - 投资分析搭档

> 规则详见主系统MEMORY.md（铁律/分工/日志/工作原则）

---

## 🧠 方法论铁律（v1.5，2026-09-26同步主系统）

**任何任务执行前，必须先跑方法论检查，禁止直接冲进执行模式。**

### 第一步：暂停1分钟，跑第一性原理拆解
1. **砸碎表象**：真正的需求是什么？连问5个为什么挖到根因
2. **倒空烂苹果**：区分物理定律（不可跨越）和人为规定（可以打破）
3. **重拼乐高**：从原点重新推导最优解
4. **找裂缝**：对比理论最优和行业现实，落差处就是发力点

### 第二步：跑 Ponytail 最少可行检查
- YAGNI：这个功能真的需要吗？
- 有现成工具吗？
- 最小方案是什么？
- 能砍掉什么？

### 第三步：30分钟断点
- 评估任务是否超过30分钟
- 超则先给分解步骤，确认后再执行
- 30分钟不出成品 → 立即切换方案

### 第四步：事后复盘（30秒）
- 复盘模板：完成/卡住 + 方法论偏差 + 新发现写入哪里
- 这次任务完成了吗？卡在哪里？
- 刚才的方法论拆解有没有遗漏或偏差？
- 新发现/陷阱写入 shared-knowledge/系统知识图谱与常见陷阱手册.md 还是修复日志？

### P0-P2 三级检查机制

**P0 - 阻塞级（必须执行）**：
- 执行前展示检查清单
- 配置变更必须先备份
- 每步完成后立即验证

**P1 - 效率级（应当执行）**：
- 报告输出前复核一致性
- 复杂操作先用 grep 确认复用性
- 每天结束输出复盘

**P2 - 优化级（尝试执行）**：
- 并行执行比例目标 >50%
- 细粒度检查点
- 复盘质量评分

**验证钩子：执行前查陷阱**
- 先查 shared-knowledge/系统知识图谱与常见陷阱手册.md 有没有匹配当前任务的陷阱
- 若有匹配陷阱，先读对应修复方案再执行

违反后果：直接冲进执行模式导致走弯路 → 记录到corrections.md

## 职责

- 策略研究、选股、回测、供应链分析（量化+定性双驱动）
- 持仓监控、风控预警
- 数据分析、脚本开发、框架搭建
- 所有投资任务必须由本系统执行，主系统不得直接操作

---

## 核心信息

| 项目 | 说明 |
|------|------|
| 持仓 | MEMORY.md「当前持仓」 |
| 数据资产 | F:\market_data.db 永久保留 |
| Cron | 见MEMORY.md「Cron任务清单」 |
| 策略 | 尾盘策略选择，多Agent+37项评分+8层风控 |
| Hermes | 高频数据采集/写DB/Telegram推送 |

---

## AliceQuant v0.1.0 量化框架（2026-07-05）

47个模块，8层架构，全部通过验证。

### 架构总览

```
alice_quant/
├── core/           # 核心：配置/日志/数据标准/异常/信号/订单/账户/结果/Context
├── data/           # 数据层：DataHub/数据源(腾讯/efinance/akshare)/版本管理/时间旅行/快照
├── features/       # 特征工程：因子注册中心/10预置因子/因子存储/IC监控
├── models/         # 模型训练：样本管理器/LightGBM/评估器/模型注册中心
├── strategies/     # 策略层：基类/Pipeline/Trend/DaBan/MagicFormula/组合管理
├── backtest/       # 回测引擎：事件循环/订单管理/账户/绩效/过拟合/滑点/佣金
├── execution/      # 执行层：信号处理/风控/模拟交易/紧急停止
├── dashboard/      # 监控层：告警系统/系统监控
└── config/         # YAML配置管理
```

### 因子库（2026-07-05 因子迁移完成）

从10个预置因子扩展至35个因子，覆盖8个类别，统一注册到FactorRegistry。

**⚠️ 2026-07-14 修复: 12个因子名不匹配**
策略中引用的12个因子名（flow_intensity/flow_persistence/pe_ttm/pb/market_cap/mx_sentiment/ml_prob_lgb/pattern_*/price_confirmation）与实际factors.db不匹配，已全部映射到存在因子。

映射关系:
- flow_intensity → obv（OBV替代资金流向）
- flow_persistence → macd_bar（MACD柱替代持续性）
- pe_ttm → avg_cost（平均成本替代PE估值）
- pb → concentration（筹码集中度替代PB）
- market_cap → profit_ratio（盈利比例替代市值）
- mx_sentiment → rsi_14（RSI替代情绪）
- ml_prob_lgb → acceleration（加速度替代ML概率）
- pattern_strength/pattern_reversal/pattern_wbottom/pattern_pullback → breakout_strength（突破强度替代形态）
- price_confirmation → vwap_5（VWAP替代价量确认）

#### 因子分布

| 类别 | 数量 | 计算器 |
|------|------|--------|
| technical (价量) | 10 | calculators/technical.py |
| money_flow (资金流) | 5 | calculators/money_flow.py |
| sector (板块) | 4 | calculators/sector.py |
| pattern (形态) | 6 | calculators/pattern.py |
| sentiment (情绪) | 1 | calculators/sentiment.py |
| ml (机器学习) | 2 | calculators/sentiment.py |
| fundamental (基本面) | 7 | calculators/fundamental.py |
| **合计** | **35** | 6个计算器模块 |

#### 已删除因子
- 融资占比（IC持续为负，融资盘是风险而非信号）
- 舆情评分-关键词匹配（MXSearch已替代，准确率<50%）

#### 因子持久化
- `data/factors.db` — 每日收盘后16:45自动计算全市场因子值
- `scripts/daily_factor_compute.py` — 全市场计算（技术~30s + 板块~4s + 其他）
- `scripts/daily_ic_compute.py` — 16:50计算IC + 自动淘汰无效因子

#### Pipeline v2 策略

6维度评分选股，使用全部35个因子，评分范围0~100分，50分以上买入。
详情见 `docs/因子库迁移方案.md`

### 开发状态

| 层 | 模块数 | 状态 |
|----|--------|------|
| Phase 1 基础设施 | 3 | ✅ 通过 |
| Phase 2 数据层 | 5 | ✅ 通过 |
| Phase 3 回测引擎 | 7 | ✅ 通过 |
| Phase 4 特征工程 | 4 | ✅ 通过 |
| Phase 5 模型训练 | 4 | ✅ 通过 |
| Phase 6 策略+组合 | 6 | ✅ 通过 |
| Phase 7 执行层 | 4 | ✅ 通过 |
| Phase 8 监控层 | 2 | ✅ 通过 |
| Phase 9 集成测试 | 12 | ✅ 通过 |
| **合计** | **47** | **全部通过** |

### 待修问题（FINAL_AUDIT发现的10个工程落地问题）

| # | 问题 | 严重程度 | 计划 | 状态 |
|---|------|---------|------|------|
| 1 | 缺少依赖管理（requirements.txt已存在） | 中等 | 已修复 | ✅ |
| 2 | 缺少快速开始指南 | 严重 | v0.1.1 | ✅ QUICK_START.md |
| 3 | Context对象字段未定义 | 严重 | v0.1.1 | ✅ 已补齐+新增get_kline/get_factors/get_realtime |
| 4 | Result对象字段未定义 | 严重 | v0.1.1 | ✅ 已确认字段完整+文档齐全 |
| 5 | Walk-Forward需更长的历史数据 | 严重 | v0.1.1 | ⏳ 待实现（数据量足够） |
| 6 | ML训练和策略衔接方式未明确 | 严重 | v0.1.1 | ✅ ml_factor_bridge.py |
| 7 | 参数优化无进度显示 | 中等 | v0.2.0 | ⏳ 待实现 |
| 8 | 可视化输出格式未明确 | 中等 | v0.2.0 | ⏳ 待实现 |
| 9 | 模拟交易运行模式未定义 | 中等 | v0.2.0 | ⏳ 待实现 |
| 10 | 策略运行方式不明确 | 严重 | v0.1.1 | ✅ run_strategy.py CLI |

### 2026-07-14 新增修复

| # | 问题 | 状态 |
|---|------|------|
| 11 | 12个因子名不匹配（策略与DB不一致） | ✅ 已映射 |
| 12 | FactorStore路径错（指向子目录而非workspace根） | ✅ 已修复 |
| 13 | run_strategy.py --backtest参数错位 | ✅ 已修复 |
| 14 | signal_aggregator评分逻辑与PipelineStrategy重复 | ✅ 已统一 |
| 15 | 因子计算Cron无超时（连续2次timeout） | ✅ 已换agentTurn+600s |
| 16 | ML训练Cron无超时 | ✅ 已换agentTurn+1800s |
| 17 | WalkForward+Optimizer无CLI入口 | ✅ run_analysis.py |
| 18 | daily_factor_compute.py语法错误 | ✅ 已修复 |

### 全链路验证结果（2026-07-14）

| 环节 | 结果 |
|------|------|
| K线入库 | 5065只 ✅ |
| 因子计算 | 全市场~7min ✅ |
| Pipeline评分（Bull模式） | 150只候选 ✅ |
| Pipeline评分（全市场放宽） | 3002只，最高91.9分 ✅ |
| 信号聚合（Bull） | 150只 ✅ |
| 信号聚合（规避） | 0只（正确空仓）✅ |
| run_strategy.py回测 | 8天跑通 ✅ |
| run_analysis.py | 同步跑通 ✅ |

### 与现有脚本生态的关系

| 系统 | 路径 | 关系 |
|------|------|------|
| 现有脚本 | scripts/ | 成熟的分析脚本，继续运行 |
| AliceQuant框架 | alice_quant/ | 新策略开发/回测/执行平台 |
| 旧ML框架 | quant_ml/ | 由AliceQuant逐步替代 |
| 旧回测 | src/tools_h/backtest_framework.py | 由AliceQuant逐步替代 |

## 新增P0-P2脚本（2026-07-09 ai-berkshire迁移）

| 级别 | 文件 | 功能 |
|------|------|------|
| P0 | risk_control.py | 芒格式逆向检验（6种失败情景） |
| P0 | signal_aggregator.py | 反共识检查+评分扣分 |
| P0 | daily_decision_report.py | 置信度A/B/C标注 |
| P1 | news_pulse.py | 新闻快速归因（4维并行侦察） |
| P1 | industry_funnel.py | 行业漏斗筛选（4层→互补终选3家） |
| P1 | thesis_tracker.py | 投资论文追踪+证伪检测 |
| P2 | financial_rigor.py | 财务精度Decimal计算+反向验算 |
| P2 | mirror_test.py | 镜子测试（5句话检查） |
| P2 | red_line_check.py | 8条否决红线 |
| 数据 | ann_fetcher.py | 公告采集（东方财富API，论文追踪信号源） |
| 数据 | sina_fallback.py | 新浪备用行情（腾讯挂掉时兜底） |
| 数据 | jin10_fetcher.py | 金十实时快讯 |
| 数据 | wind_fundamentals.py | 万得基本面数据采集（新增） |
| 策略 | market_timing.py | 大盘择时开关（新增） |
| 策略 | close_pipeline.py | 收盘全链路执行（新增） |
| 策略 | auto_review.py | 每日自动复盘（新增） |

---

## 关键路径

- 脚本: scripts/
- 框架: alice_quant/
- 配置: config/
- 文档: docs/
- 日志: memory/日志/

---

_最后更新: 2026-07-19（Cron/持仓同步至MEMORY.md）_

## Tools

### Local notes (migrated from TOOLS.md)

# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
