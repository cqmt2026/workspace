# MEMORY.md - 投资系统核心记忆

**最后更新**: 2026-06-08
**版本**: v3.3（Serenity方法论整合）

---

## ⚠️ 核心铁律（强制执行）

### 科学验证铁律（2026-05-25新增）
> **每一项假设都要被数据验证，错的扔掉，对的留下，最终得到一整套经过验证的方法论。**

> **除真实获取的数据外，所有工具和方法都只是假设，必须通过数据验证才能作为决策依据。**

> **未经数据验证的结论 = 假设，不是事实。**

**适用场景**：投资分析、策略设计、指标选择、工具开发等一切决策。
- **所有建议必须基于客观真实数据和经过回测验证的结论**
- 严禁假设数据、编造结论、脱口而出
- 数据不明时必须标注「未知」，不得猜测
- 建议格式：`结论` + `数据来源` + `验证方式`

### 数据严禁瞎编
- 持仓成本 → 必须由主人提供，绝不假设
- 盈亏计算 → 以实际成本为准，不编造数字
- 分析判断 → 基于真实数据，数据不明标注「未知」

### 止损纪律
- 单笔风险 ≤ 2%，组合 ≤ 15%
- 亏损 5% 必须止损，不侥幸

---

## 📊 尾盘精选策略（2026-06-06确立）

### 买入条件（全部满足）
| # | 条件 | 数值 |
|---|------|------|
| 1 | 今日涨幅 | 3% ~ 5% |
| 2 | 量比（当日成交量/5日均量） | > 1 |
| 3 | 近3日累计涨幅 | 0% ~ 10% |
| 4 | 前2日单日涨幅 | 均 < 7% |
| 5 | 5周均线（MA20）趋势 | 近5日向上 |
| 6 | 换手率 | 3% ~ 10% |

### 排除条件
| # | 条件 |
|---|------|
| 1 | 北交所股票（bj.开头） |
| 2 | ST股票 |

### 交易规则
| # | 规则 |
|---|------|
| 买入 | 尾盘14:50，收盘价买入 |
| 卖出 | 次日最高价卖出 |

### 回测结果（2019-2026）
| 年份 | 样本 | 均收益 | 胜率 |
|------|------|--------|------|
| 2019 | 28,205 | +2.18% | 82.6% |
| 2020 | 29,988 | +2.41% | 84.7% |
| 2021 | 32,607 | +2.47% | 85.2% |
| 2022 | 33,389 | +2.34% | 84.1% |
| 2023 | 32,101 | +2.17% | 83.8% |
| 2024 | 40,743 | +2.82% | 87.6% |
| 2025 | 38,364 | +2.33% | 84.4% |
| 2026 | 14,149 | +2.10% | 79.6% |
| **合计** | **249,546** | **+2.39%** | **83-87%** |

### 架构升级（参考EasyUp）
| 模块 | 说明 |
|------|------|
| 多Agent决策 | 猎手/账房/守夜人三角色辩论 |
| 8层风控 | ST排除/连续涨停/大盘判断/仓位/止损/止盈/集中度/复核 |
| 因子评分 | 动量/成交量/趋势/波动率因子 |

### 脚本
| 脚本 | 功能 |
|------|------|
| `scripts/strategy_scan.py` | 策略扫描 |
| `scripts/factor_scorer.py` | 因子评分 |
| `scripts/multi_agent.py` | 多Agent辩论 |
| `scripts/risk_control.py` | 8层风控 |

### Cron任务
| 任务 | 时间 |
|------|------|
| INV-Closing-Strategy-尾盘精选 | 10:00/14:30 |
| INV-Closing-Strategy-午盘13:30 | 13:30 |

---

### 持仓信息（2026-05-19更新）
| 股票 | 代码 | 成本 | 股数 | 市场 |
|------|------|------|------|------|
| **空仓** | — | — | 0 | — |

---

## 📊 多因子选股模型 v3.0

### 评分维度（满分100分）

| 维度 | 因子 | 满分 | 数据来源 |
|------|------|------|---------|
| 技术面 | 均线多头/RSI/MACD/量比 | 40 | dfcf/腾讯API |
| 布林带 | 收口突破信号 | 5 | 日K计算 |
| 均线支撑 | MA60上方 | 5 | 日K计算 |
| 资金面 | 5日主力净流入 | 20 | 东财f62 |
| 融资融券 | 融资占比 | 10 | 东财f47/f48 |
| 风险公告 | 无风险公告 | 10 | 东财公告API |
| 舆情 | 市场快讯情绪 | 10 | 东财+新浪 |

### 评分标准
| 分数 | 评级 |
|------|------|
| 75+ | ⭐强烈推荐 |
| 60-74 | ✅关注 |
| 45-59 | ⚠️观察 |
| <45 | ❌不关注 |

### 脚本位置
```
workspace-investment/scripts/multi_factor_scoring.py  # 主脚本
```

---

## 🤖 已安装Skills（ClawHub）

| Skill | 版本 | 功能 |
|-------|------|------|
| investment-analyst | 1.0.0 | 投资分析（基本面+技术面） |
| china-stock-analysis | 1.0.0 | A股/港股行情分析+买卖建议 |
| china-stock-sentiment | 0.1.1 | A股舆情分析 |
| multi-factor-strategy | 1.0.0 | 多因子策略配置生成 |
| portfolio | 3.4.2 | 持仓管理+再平衡建议 |
| backtest | 1.0.2 | 回测引擎 |
| akshare-backtest | 1.0.3 | Akshare回测工具 |

**Skills目录**: `workspace-investment/skills/`

---

## 🔧 分析脚本（核心）

| 脚本 | 功能 | 优先级 |
|------|------|--------|
| multi_factor_scoring.py | 多因子评分 | 🔴核心 |
| sentiment_analyzer.py | 舆情分析 | 🔴核心 |
| portfolio_tracker.py | 持仓管理 | 🔴核心 |
| dynamic_stop_loss.py | 移动止损（追踪止损） | 🔴核心 |
| chan_minute_analysis.py | 缠论多周期 | 🟡辅助 |
| capital_flow.py | 资金流分析 | 🟡辅助 |
| fundamental_factors.py | 基本面因子 | 🟡辅助 |
| announcement_monitor.py | 公告监控 | 🟡辅助 |
| margin_visualizer.py | 融资融券可视化 | 🟡辅助 |
| news_push.py | 快讯推送 | 🟢日常 |
| analyze_pool_688.py | 688池筛选 | 🟢日常 |
| factor_library.py | 技术因子库 | 🟢工具 |
| strategy_optimizer.py | 策略优化 | 🟢工具 |
| multi_strategy.py | 多策略框架 | 🟢工具 |

---

## 📡 数据源API

| 数据 | API | 状态 |
|------|-----|------|
| 分时/日K | push2his.eastmoney.com | ✅ |
| 实时行情 | qt.gtimg.cn (腾讯) | ✅ |
| 资金流向 | push2.eastmoney.com f62 | ✅ |
| 融资融券 | push2.eastmoney.com f47/f48 | ✅ |
| 公告 | np-anotice-stock.eastmoney.com | ✅ |
| 快讯 | newsapi.eastmoney.com | ✅ |
| 龙虎榜 | 待接 | ❌ |
| 大宗交易 | 待接 | ❌ |

## 📊 行业板块数据

| 数据源 | 函数 | 数量 | 状态 |
|--------|------|------|------|
| THS申万行业板块名称 | `stock_board_industry_name_ths()` | 90个 | ✅ akshare |
| 行业板块实时涨跌 | `stock_sector_spot()` | 49个 | ✅ akshare |
| 概念板块名称 | `stock_board_concept_name_ths()` | 375个 | ✅ akshare |
| 东财行业板块历史 | RPT_INDUSTRY_INDEX | 仅4板块历史 | ⚠️ 备用 |

---

## 📊 RPS板块强弱研究框架（2026-05-19新增）

**核心公式**: `RPS = (1 - 排名 / 板块总数) × 100`
- RPS=100：涨幅第1，最强板块
- RPS=0：涨幅最后，最弱板块
- 强势基准：RPS≥70 | 弱势基准：RPS≤30

### 数据层级
| 层级 | 数据 | 来源 | 时效 | 数量 |
|------|------|------|------|------|
| L1a行业板块RPS盘中 | 49行业板块实时RPS | `stock_sector_spot()`（EastMoney实时）| 盘中9:30-15:00 ✅ | 49 |
| L1b概念板块RPS盘中 | 486概念板块实时RPS | `stock_board_concept_name_em()`（EastMoney）| 盘中9:30-15:00 ✅ | 486 |
| L1板块RPS收盘 | 90申万行业完整RPS | THS申万指数收盘价 | 收盘后16:00+ ✅ | 90 |
| L2个股RPS | HS300成分股RPS | Sina HS300 + 实时涨跌 | 盘中/收盘后均可用 | 300 |
| L3趋势均线 | MA5/MA20历史积累 | 每日JSON历史积累 | 需5+/20+交易日 | -

> ⚠️ EastMoney概念板块API不稳定（60%成功率），`fetch_concept_rps.py`内置3次重试+3秒延迟+30分钟缓存，稳定性接近100%。

### 输出文件（out_data/）
| 文件 | 内容 |
|------|------|
| `RPS_board_49_YYYY-MM-DD.json/md` | 49行业板块实时RPS（盘中）|
| `RPS_concept_YYYY-MM-DD.json/md` | 486概念板块实时RPS（盘中，含领涨股）|
| `RPS_board_90_YYYY-MM-DD.json/md` | 90申万行业完整RPS（收盘后）|
| `RPS_stock_YYYY-MM-DD.json/md` | HS300个股RPS排名 |
| `RPS_trend_YYYY-MM-DD.json/md` | 均线趋势分析 |
| `RPS_daily_summary_YYYY-MM-DD.json/md` | 收盘RPS全覆盖报告（TOP20/BOTTOM20/7日走势/MA5分类）|
| `sentiment_rps_latest.json` | 情绪快照+RPS+轮动信号 |
| `daily_recommend_rps_YYYY-MM-DD.json/md` | RPS增强版推荐TOP20 |
| `rps_alert_latest.json` | 板块轮动预警事件 |
| `rps_history/` | 每日原始JSON历史积累 |

### Cron任务
| 任务 | 时间 | 脚本 | 功能 |
|------|------|------|------|
| INV-RPS-Intraday | 每30分钟(9-14点) | fetch_board_rps.py + fetch_concept_rps.py | 盘中板块RPS实时跟踪（49行业+486概念）|
| INV-RPS-Closing | 16:10(收盘后) | board+stock+trend+snapshot+recommend+alert | 收盘RPS全套分析 |
| INV-RPS-Daily-Summary | 16:10(收盘后) | rps_daily_summary.py | **新增**收盘90板块全覆盖日报（TOP20/BOTTOM20/7日走势/异动/MA5分类）|

### 行业研究系统（全自动）
**触发来源**：
  1. RPS预警（新晋强势板块）
  2. 持仓板块异动
  3. 手动指定

**脚本**：`scripts/industry_research.py`
**四层研究框架**：
  ①行业趋势（成分股涨跌幅+RPS+资金态度）
  ②产业链（炒作路径：成交额排序核心标的）
  ③核心段（成本结构：财务数据毛利率/ROE）
  ④核心公司（持续跟踪标的）

**数据流**：
```
alert触发/手动 -> find_board_code(缓存读) -> get_concept_stocks(成分股)
-> analyze_trend(RPS分析) -> get_stock_financials(财务)
-> generate_report(Obsidian归档)
```

**输出**：
  - `Obsidian/Jarvis/03-知识/投资行业研究/YYYY-MM-DD_板块名_行业研究.md`
  - `out_data/industry_YYYY-MM-DD_板块名.md`

**说明**：报告初稿自动生成，人工补充产业链/核心段判断

### 均线系统（积累中）
| 均线 | 含义 | 强势信号 | 弱势信号 |
|------|------|---------|--------|
| MA5 | 短期5日动量 | RPS>MA5>MA20 | RPS<MA5<MA20 |
| MA20 | 中期20日趋势 | 均线多头排列 | 均线空头排列 |

---


## 🔧 反前瞻偏误系统（v3.1+）

**核心问题**：回测时能看到当天收盘价，"偷看"未来数据导致策略虚高、实盘亏损。

### 解决方案

| 组件 | 路径 | 功能 |
|------|------|------|
| 核心掩码函数 | `src/tools_h/anti_lookahead.py` | 最新日期只保留buy price，删除sell price |
| 验证工具 | `mask_latest_date()` | 单股票数据掩码 |
| JSONL工具 | `mask_latest_date_jsonl()` | JSONL文件批量掩码 |
| 校验工具 | `validate_no_lookahead()` | 验证数据无前瞻偏误 |
| 回测前检查 | `check_data_before_backtest()` | DataFrame前瞻检查 |
| 批量工具 | `batch_mask_directory()` | 目录下文件批量掩码 |

### 使用时机

- **每日数据获取后**：立即掩码处理最新日期
- **回测前**：必须验证数据无前瞻偏误
- **多因子评分**：评分只能使用T-1及之前数据

---

## ⏰ Cron任务

| 任务 | 时间 | 脚本 | 状态 |
|------|------|------|------|
| 持仓异动提醒 | 每30分钟(9-15点) | holding_alert.py | ⚠️ timeout需关注 |
| 尾盘策略分析 | 14:25 | analyze_pool_688.py | ✅ |
| Chrome进程清理 | 每30分钟(9-16点) | cleanup_chrome.py | ✅ |
| 早间快讯 | 09:00 | news_push.py | ✅ |
| 晚间快讯 | 22:00 | news_push.py | ✅ |
| ML模型训练 | 20:00 | ml_daily_train.py | ⚠️ 被重启中断 |
| 涨停K线收集 | 16:10 | collect_daily_zt_kline.py | ✅ |
| 涨停分析 | 16:15 | daily_analysis.py | ✅ |

---

## 📂 关键路径

| 类型 | 路径 |
|------|------|
| 股票池 | config/stock_pool.json (688只) |
| 持仓记录 | data/portfolio.json |
| 交易历史 | data/trade_history.json |
| 分析结果 | outputs/afterhour_analysis_689_v2.json |
| **日报/汇报输出** | **out_data/** (按日期排序) ⚠️重要资料输出目录 |
| 微信推送 | Server酱 SCT345078TEFwhlSFcUKuEuPBQ2D21riKC |

---

## 🚨 循环执行强制中断铁律

**任何任务陷入循环（执行→验证→失败→重试→验证→失败）时，最多执行2次循环，必须跳出并报错！**

| 场景 | 最多循环次数 | 达到后动作 |
|------|-------------|-----------|
| 字数不足扩充 | 2次 | 立即交付，说明字数差XX字 |
| 修复/修改章节 | 2次 | 交付当前版本，列出未解决问题 |
| 工具调用失败后重试 | 2次 | 报错，说明原因，等主人指令 |
| 检查同一问题 | 2次 | 跳过，继续下一步 |
| 任何尝试→失败→重试 | 2次 | 报错，不继续尝试 |

---



---

## ⚠️ ML模型过拟合问题（2026-06-08发现）

**问题**：训练集准确率92% vs 验证集准确率51%，过拟合率41%

**原因分析**：
- 模型学习了训练数据的噪声，而非通用模式
- 当前特征工程不够稳健
- 数据量不足（部分股票样本量少）

**改进方向**：
1. 简化模型（减少树深度/减少树数量）
2. 增加正则化
3. 改进特征工程（引入更稳健的技术指标）
4. 增加训练数据时间跨度

**当前状态**：ML训练Cron仍在运行（有checkpoint机制），但预测能力有限



---

## 🧠 自我学习系统（v1.0 - 2026-06-09新增）

**目标**：从「存储型记忆」升级为「推理型学习」，让系统能从决策结果中自动改进。

### 核心文件

| 文件 | 用途 |
|------|------|
| data/decisions.json | 决策日志（每个决策记录理由、标签、结果） |
| data/review_weekly.json | 每周复盘分析 |
| scripts/add_decision.py | 记录决策脚本 |
| scripts/self_learn_review.py | 每周复盘脚本 |

### 决策记录流程

1. **做决策时**：调用dd_decision.py记录
   `ash
   python scripts/add_decision.py --code 300034 --action buy --reason 'RSI超卖' --tags RSI,超卖 --price 16.94
   `

2. **结果出来后**：标记结果
   `ash
   python scripts/add_decision.py --mark1 --result success --profit 5.2
   `

3. **每周五**：自动复盘
   `ash
   python scripts/self_learn_review.py
   `

### 学习闭环

`
决策 → 记录理由/标签 → 追踪结果 → 复盘分析 → 更新策略 → 下次改进
`

### 迭代阶段

| 阶段 | 功能 | 状态 |
|------|------|------|
| v1.0 | 决策日志 + 每周复盘 | ✅ 完成 |
| v2.0 | 自动结果追踪 |🚧 待开发 |
| v3.0 | 策略因子自动调整 | 📋 规划中 |

_最后更新: 2026-06-09_

_