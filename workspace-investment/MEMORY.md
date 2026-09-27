# MEMORY.md - 投资系统核心记忆

**更新**: 2026-07-16 19:00（系统健康检查+大规模修复：Cron超时/推送/脚本修复）

---

## 核心原则

### 科学验证
> 每一个结论都要经过数据验证，从最简单的假设开始，最终得到一个已经验证过的结论。
> 未经验证的结论 = 假设，不是事实。

### 铁律
- 所有结论基于客观数据，未经数据验证的结论标注为假设
- 数据不足时标注未知，不做猜测
- 仓位/成本/盈亏以实际数据为准

### 止损规则
- 机械止损: 5% 硬性止损，不犹豫
- 动态止损: 浮盈每增加5%，止损线上移2%（只上移不下移）
  - 浮盈0%：止损=买入价×0.95
  - 浮盈+5%：止损=买入价×0.96
  - 浮盈+10%：止损=买入价×0.97
  - 浮盈+15%：止损=买入价×0.98
  - 浮盈+20%+：止损=买入价×0.99
- 止盈触发:
  - 单日涨幅>7%且量比>2 → 减仓1/3
  - 高位放量滞涨 → 减仓1/2
  - 累计涨幅>30% → 至少减仓1/3
- 总回撤: 15% 启动风控方案

---

## 当前持仓（2026-07-13 11:20更新）

**空仓**

> 2026-07-13 09:50 清仓斯瑞新材(500@40.0, 板块崩盘-13%, 浮盈归零前止损)
> 2026-07-10 清仓宝信软件(500@18.4, 浮盈+8.7%)
> 2026-07-09 清仓高测股份、钢研高纳

---

## 收盘任务链（每日16:05~17:00）

按执行顺序，每个任务产出文件供下游使用：

| 时间 | 任务 | 脚本 | 输出 | 推送 |
|------|------|------|------|------|
| 16:05 | 形态雷达 | xingtai_integration.py | out_data/xingtai_*.md | ❌（内部）|
| 16:10 | 90板块RPS采集 | fetch_board_rps.py | rps_history/RPS_board_*.json | ❌（内部）|
| 16:10 | 涨停K线采集 | collect_daily_zt_kline.py | out_data/daily_zt_*.json | ❌（内部）|
| 16:17 | 涨停分析 | daily_analysis.py | out_data/zt_analysis_*.txt | ❌（内部）|
| 16:30 | **每日决策报告** | daily_decision_report.py | out_data/daily_decision_*.txt | ✅ 微信 |
| 16:35 | K线数据入库 | update_today_kline.py | DB更新 | ❌（内部）|
| 16:45 | 因子计算 | daily_factor_compute.py | factors.db | ❌（内部）|
| 16:45 | 四象共振扫描 | si_xiang_bottom_scan.py | out_data/si_xiang_bottom_*.md | ✅ 微信 |
| 16:50 | IC计算 | daily_ic_compute.py | out_data/factor_ic_*.json | ❌（内部）|
| 16:55 | 收盘全链路 | close_pipeline.py | out_data/prefilter+review | ❌（内部）|
| 16:55 | 信号聚合 | signal_aggregator.py | out_data/signal_aggregated_*.json | ❌（内部）|
| 17:00 | 行业研报 | industry_research_trigger.py | out_data/industry_*.json | ❌（内部）|
| **17:05** | **检查链条** | check_chain.py | out_data/chain_check_*.json | ✅ 微信 |
| **17:05** | **论文追踪** | thesis_tracker.py | 检查结果 | ✅ 微信 |
| **17:08** | **红线检查** | red_line_check.py | 检查结果 | ✅ 微信 |
| **17:10** | **财务精度审计** | financial_rigor.py | 检查结果 | ❌（内部）|

**Cron推送机制（2026-07-13 大规模修复）：**
- ✅ **15个Cron**从`systemEvent`改为`agentTurn+isolated`+`delivery=announce`模式
- ✅ 所有关键告警类Cron（持仓监控/日报/链检查/红线/论文/晚间资讯/早盘/尾盘策略/模拟盘/ML训练）统一推送微信
- ✅ 持仓监控脚本修复：指数API格式`sh.000001`→`sh000001`，增加中证军工/有色金属板块监控
- ✅ RPS文件降级逻辑：当日找不到→昨日→最新文件

---

## Cron任务清单（2026-07-13 全面修复后）

### 交易日（周一~五）

| 时间 | 任务 | 模式 | 推送 | 说明 |
|------|------|------|------|------|
| 09:00 | 早盘+外围简报 | agentTurn+isolated | 微信 | 隔夜外盘/期货/A50/情绪 |
| 09:05 | MXSearch日间计算 | systemEvent+main | 内部 | T+1情绪计算 |
| 09:10 | 交易结果追踪 | systemEvent+main | 内部 | 检查pending交易 |
| 09:40 | 尾盘策略(早盘) | systemEvent+main | 内部 | strategy_scan.py --mx |
| **每30分** | **持仓监控** | **agentTurn+isolated** | **微信** | **异动/板块暴跌告警** |
| 10:15 | 持仓公告监控 | agentTurn+isolated | 微信 | 公告异常推送 |
| 14:00 | SmartMoney扫描 | systemEvent+main | 内部 | 资金因子扫描 |
| **14:30** | **尾盘策略(下午)** | **agentTurn+isolated** | **微信** | 选股策略+推送Top10 |
| **14:35** | **模拟盘交易** | **agentTurn+isolated** | **微信** | 根据信号执行 |
| 16:05 | 形态雷达 | agentTurn+isolated | 内部 | 6模板K线扫描 |
| 16:10 | 90板块RPS采集 | agentTurn+isolated | 内部 | fetch_board_rps.py |
| 16:10 | 涨停K线采集 | agentTurn+isolated | 内部 | collect_daily_zt_kline.py |
| 16:17 | 涨停分析 | agentTurn+isolated | 内部 | daily_analysis.py |
| **16:30** | **每日决策报告** | **agentTurn+isolated** | **微信** | 大盘/持仓/候选/建议 |
| 16:35 | K线数据入库 | agentTurn+isolated | 内部 | update_today_kline.py |
| 16:45 | 因子计算 | agentTurn+isolated | 内部 | daily_factor_compute.py |
| **16:45** | **四象共振扫描** | **agentTurn+isolated** | **微信** | **底部反转候选Top5** |
| 16:50 | IC计算 | agentTurn+isolated | 内部 | daily_ic_compute.py（单日，超时600s）|
| 10:00(周六) | IC滚动60天 | agentTurn+isolated | 内部 | daily_ic_compute.py --days 60（超时7200s）|
| 16:55 | 收盘全链路 | agentTurn+isolated | 内部 | 前置过滤+多策略引擎+信号聚合 |
| 17:00 | 行业研报 | agentTurn+isolated | 内部 | industry_research_trigger.py |
| **17:05** | **检查链条** | **agentTurn+isolated** | **微信** | 有异常自动告警 |
| **17:05** | **论文追踪** | **agentTurn+isolated** | **微信** | 检查持仓论文是否被证伪 |
| **17:08** | **红线检查** | **agentTurn+isolated** | **微信** | 8条否决红线自动检测 |
| 17:10 | 财务精度审计 | systemEvent+main | 内部 | 市值验算+PE/PB检查 |
| **20:00** | **ML训练** | **systemEvent+main** | **微信** | **全量LightGBM训练** |
| 20:15 | ML持仓预测 | systemEvent+main | 内部 | run_ml_predict.py |
| **22:00** | **晚间资讯** | **agentTurn+isolated** | **微信** | **P0-P3分类报告** |

**已禁用：**
- ML概率T+1验证（verify_ml_prob.py脚本不存在）

### 定时任务（非交易日）

| 时间 | 任务 | 说明 |
|------|------|------|
| 00:40 | MXSearch采集 | 周一~五，采集10只股票舆情 |
| 00:50 | MXSearch信号加载 | 加载信号到评分系统 |

---

## 2026-07-16 系统健康检查+大规模修复

### 发现问题

| # | 问题 | 严重 | 状态 |
|---|------|------|------|
| 1 | **13个Cron持续失败** — isolated agentTurn超时（120-180s不够），LLM响应超时 | P0 | ✅ |
| 2 | **9个Cron delivery=none** — 任务执行了但结果不推送到微信 | P0 | ✅ |
| 3 | **config/market_config.yaml缺失** — market_timing.py引用该文件但不存在 | P1 | ✅ |
| 4 | **daily_decision_report.py导入bug** — `from scripts.data_api` 在Cron执行时路径不对 | P0 | ✅ |
| 5 | **fetch_board_rps.py BOM头** — 文件含U+FEFF导致语法错误 | P1 | ✅ |
| 6 | **6个脚本被归档到_archive/** — system_health_check/weekly_review/self_learn_review/review_to_obsidian/run_strategy/run_analysis 不在scripts/ | P1 | ✅ |

### 修复措施

**P0 — Cron超时+推送修复（10个任务）**

| 任务 | 原timeout | 新timeout | 原delivery | 新delivery |
|------|-----------|-----------|-----------|-----------|
| 早盘简报 09:00 | 300s | 600s | none | announce |
| 尾盘策略 14:30 | 180s | 600s | none | announce |
| 模拟盘交易 14:35 | 120s | 600s | none | announce |
| 每日决策报告 16:30 | 180s | 600s | none | announce |
| 四象共振扫描 16:45 | 180s | 600s | none | announce |
| 晚间资讯 22:00 | 180s | 600s | none | announce |
| 链检查 17:05 | 120s | 600s | none | announce |
| 论文追踪 17:05 | 120s | 600s | none | announce |
| 红线检查 17:08 | 120s | 600s | none | announce |
| 模型健康度 17:10 | 120s | 600s | none | announce |

所有任务增加 fallback 链: agnes-2.0 → deepseek-v4 → sense-6.7 → llama-70b

**P1 — 脚本修复**
- `config/market_config.yaml` — 已创建（大盘择时参数+板块跟踪+数据源优先级）
- `daily_decision_report.py` — 修复 `from scripts.data_api` → 动态路径导入
- `fetch_board_rps.py` — 移除BOM头(U+FEFF)
- 从 `_archive/` 恢复6个脚本到 `scripts/`

**P2 — 验证确认**
- 持仓监控/金十快讯/SmartMoney/财务精度审计 — 正确跳过（非交易日），明天开盘自动恢复

### 实测验证

| 环节 | 结果 |
|------|------|
| 36个脚本语法检查 | ✅ 全部通过 |
| 11个关键模块导入测试 | ✅ 全部通过 |
| morning_brief.py 运行 | ✅ 外盘数据正常 |
| market_timing.py 运行 | ✅ 大盘判定正确 |
| strategy_scan.py 运行 | ✅ 188只候选 |
| sim_trade.py 运行 | ✅ 空仓正常 |
| daily_decision_report.py 运行 | ✅ 修复后正常输出 |
| si_xiang_bottom_scan.py 运行 | ✅ 正常扫描 |
| check_chain.py 运行 | ✅ 15个任务全部通过 |
| thesis_tracker.py 运行 | ✅ 空仓正常 |
| red_line_check.py 运行 | ✅ 正常 |
| evening_news_classified.py 运行 | ✅ P0 2条/P3 18条 |
| Cron手动触发+微信推送 | ✅ 58秒完成，delivered=true |

---

## 数据资产

| 资产 | 路径 | 说明 |
|------|------|------|
| 日K数据库 | F:\market_data.db | 979MB，2019-2026年，5065只股票 |
| 持仓记录 | data/portfolio.json | 当前持仓（2026-07-06重建） |
| 交易历史 | data/trade_history.json | 2026年5月至今交易记录 |
| 股票池 | config/stock_pool.json | 67只核心股票 |
| 报告输出 | out_data/ | 所有日报/RPS/分析报告 |
| 因子库 | data/factors.db | 35个因子日频数据 |
| 板块缓存 | data/stock_board_cache.json | 3848只股票映射到53个板块 |

---

## 数据源API

| 数据 | API | 状态 |
|------|-----|------|
| 实时行情 | qt.gtimg.cn (腾讯) | ✅ 稳定 |
| 日K/分时 | push2his.eastmoney.com | ✅ 稳定 |
| 资金流向 | push2.eastmoney.com f62 | ✅ 稳定 |
| 融资融券 | push2.eastmoney.com f47/f48 | ✅ 稳定 |
| 公告 | np-anotice-stock.eastmoney.com | ✅ 稳定 |
| 资讯 | newsapi.eastmoney.com | ✅ 稳定 |
| 板块RPS | akshare (THS) | ⚠️ 不稳定，需重试 |
| 板块实时 | akshare (stock_sector_spot) | ⚠️ 不稳定 |

---

## 抖音内容提取（2026-07-06固化）

| 类型 | 方案 | 说明 |
|------|------|------|
| 多图帖子(images>=2) | easyocr逐图OCR | 适用图文作品 |
| 长视频(duration>=60s) | Whisper tiny音频转写 | 适用有配音视频 |
| 短视频/封面 | desc文案为主 | 适用图文封面 |

> 脚本: `scripts/douyin_extractor.py` v3.0

---

## 尾盘精选策略（2026-07-06验证）

### 选股流程
1. MX选股: 涨幅2%~8%全市场筛选（排除ST、北交所）
2. ML概率: 双模型融合评分（LightGBM+MSTNN）
3. PPE板块: 板块RPS位置+动量评分（+0~+13分）
4. 综合评分: 多维加权

### 关键参数
- 涨幅区间: 3%~8%
- 量比: 当日成交量/5日均量 > 1
- 前3日累计涨幅: 0%~10%
- 前2日单日涨幅: < 7%
- 5周均线: 在5日线上方
- 换手率: 3%~10%

### 回测历史（历史数据，仅供参考）
> 2019-2026年累计249,546次交易，平均收益率+2.39%，胜率83-87%

---

## 2026-07-11 修复记录

### signal_aggregator.py
- 涨幅过滤动态化：bull 1.5%~5% / bear 0.5%~5% / stop不评分
- 删除重复函数：calc_take_profit×2, load_zt_confirmation_signals×2

### market_timing.py
- 涨停数据兜底：daily_zt为空时从daily_k自算涨幅>9.5%的股票数
- 指数数据三级兜底：万得优先 → 腾讯实时 → MX搜索 → 平安银行K线
- 7/10修复效果：涨停0家→88家，大盘判定从"规避"→"谨慎"

### daily_ic_compute.py
- 冷启动机制：n_days<5标记为cold，不做淘汰判定
- IC_IR计算：样本<5时不计算，避免虚高
- JOIN查询：改为INNER JOIN+双表条件
- 淘汰阈值：|mean_ic|<0.005且sig_ratio>0.2
- 科创板排除：增加NOT LIKE 'sh.68%'
- inf值过滤：增加np.isinf检查

### Cron
- 每日IC：16:50单日模式，超时600s
- 新增周末IC：每周六10:00滚动60天，超时7200s

---

## 关键路径

| 内容 | 路径 |
|------|------|
| 工作空间 | `C:\Users\Administrator\.openclaw\workspace\workspace-investment\` |
| 分析脚本 | `scripts/` |
| 量化框架 | `alice_quant/` |
| ML框架 | `quant_ml/` |
| 配置文件 | `config/` |
| 输出数据 | `out_data/` |
| 交易数据 | `data/` |
| 核心K线库 | `F:\market_data.db` |
| 持仓记录 | `data/portfolio.json` |
| 交易历史 | `data/trade_history.json` |
| 股票池 | `config/stock_pool.json` |
| 微信推送 | `openclaw-weixin` |
| Obsidian归档 | `C:\Users\Administrator\Obsidian\Jarvis\` |

---

## 首日运行记录（2026-07-06）

### 发现问题清单
1. **Cron推送不触达** — systemEvent模式只注入不推送，用户收不到结果
2. **4个关键任务被禁用** — 早盘简报、晚间资讯、持仓公告、盘中异动
3. **缺失脚本** — daily_tracking_update.py已删除但Cron仍引用
4. **持仓信息为空** — 6月29日清仓后未重建
5. **收盘任务链无输出** — 10个任务中6个无输出文件

### 已修复
1. 决策报告+尾盘策略改为agentTurn+announce模式
2. 4个禁用任务重新启用
3. 从Cron链移除已删除脚本
4. 重建持仓（高测11.98/1000股、钢研17.85/1000股）→ 后调整为斯瑞新材+宝信软件，7/10清仓宝信
5. 新增check_chain.py + Cron（17:05自动检查+推送）
6. 抖音提取v3.0固化（3种方案自动选择）

### 待修复
1. 形态雷达/RPS采集/涨停分析等任务无输出文件 — 需逐个排查脚本
2. 盘中异动监控上次运行报错"LLM request failed" — 需监控明天是否正常
3. AliceQuant框架的10个工程问题 — 待v0.1.1修复

---

## 2026-07-14 大规模修复（00:00~01:00）

### 修复清单

| # | 问题 | 修复 | 验证 |
|---|------|------|------|
| 1 | **12个因子名不匹配**（策略写flow_intensity，DB无） | 9个缺失因子映射到实际存在因子 | 全市场3002只评分，最高91.9分 ✅ |
| 2 | **FactorStore路径错**（指向alice_quant/子目录） | 改为workspace根目录的data/factors.db | 直接查询113K行OK ✅ |
| 3 | **run_strategy.py --backtest参数错位**（list被传成initial_capital） | 修复调用传参 | 回测8天跑通 ✅ |
| 4 | **GBK编码崩溃**（⚠️字符） | 替换为[WARN] | 回测输出正常 ✅ |
| 5 | **signal_aggregator评分与PipelineStrategy不一致** | 替换为直接调用PipelineStrategy.generate_signals() | Bull=150只，规避=0只 ✅ |
| 6 | **因子计算Cron无超时，连续2次timeout** | systemEvent→agentTurn+600s超时 | 已替换 ✅ |
| 7 | **ML训练Cron无超时** | systemEvent→agentTurn+1800s超时+步骤容错 | 已替换 ✅ |
| 8 | **WalkForward+Optimizer无CLI入口** | 新建run_analysis.py（支持backtest/walkforward/optimize） | 跑通 ✅ |
| 9 | **daily_factor_compute.py语法错误**（多一个括号） | 修复 | 50只4s ✅ |

### 验证结果

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

### 2026-07-14 收盘决策

- **大盘环境**: 谨慎（涨停22家+指数平盘+放量），仓位上限50%
- **持仓**: 空仓
- **Top 3候选**: sh.688409(87.1分) / sh.688147(86.7分) / sh.603991(86.0分)
- **操作建议**: 大盘谨慎，半仓操作，尾盘可考虑买入Top1，止损95%

---

_最后更新: 2026-07-14 01:15（大规模修复+全链路验证）_

## Promoted From Short-Term Memory (2026-07-21)

<!-- openclaw-memory-promotion:memory:memory/2026-07-13.md:45:45 -->
- -*- coding: utf-8 -*-: P1 - 文档同步 [score=0.841 recalls=0 avg=0.620 source=memory/2026-07-13.md:45-45]
