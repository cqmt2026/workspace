# 系统工作节点全景图

> 最后更新: 2026-07-04 20:50
> 用途: 所有模块、脚本、Cron、数据资产的完整索引

---

## 一、目录结构

```
workspace-investment/
├── scripts/              ← 核心分析脚本
├── experimental/         ← 实验性脚本（不碰现有系统）
├── config/               ← 配置文件
├── data/                 ← 数据缓存/输出
├── out_data/             ← 分析结果输出
├── quant_ml/             ← ML模型框架
├── skills/               ← ClawHub安装的技能
├── memory/               ← 日志
└── docs/                 ← 文档
```

---

## 二、核心分析脚本 (scripts/)

### 选股策略

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `strategy_scan.py` | 尾盘精选策略扫描 | ✅ | 09:40/14:30 Cron |
| `multi_factor_scoring.py` | 多因子评分（37项） | ✅ | 110分制 |
| `magic_formula.py` | 神奇公式选股（ROIC+PE） | ✅ | 10:00 Cron |
| `factor_scorer.py` | 因子评分 | ✅ | 子模块 |
| `multi_agent.py` | 多Agent辩论（猎手/账房/守夜人） | ✅ | 子模块 |
| `risk_control.py` | 8层风控 | ✅ | 子模块 |

### RPS板块系统

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `fetch_board_rps.py` | 申万90板块RPS采集 | ✅ | 16:10 Cron |
| `rps_daily_summary.py` | RPS收盘全覆盖报告 | ✅ | 16:14 Cron |
| `rps_analysis.py` | RPS计算（5/10/20/60日） | ✅ | |
| `fetch_concept_rps.py` | 概念板块RPS（486个） | ✅ | 盘中30分钟 |
| `rps_push.py` | RPS强势股推送 | ✅ | |

### 形态捕手

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `xingtai_integration.py` | 6模板K线形态扫描 | ✅ | 16:05 Cron |
| `skills/xingtai-catcher/scripts/xingtai_search.py` | 形态搜索引擎 | ✅ | 子模块 |

### ML模型

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `quant_ml/pipeline/unified_train.py` | 统一训练（LightGBM+MSTNN） | ✅ | 20:00 Cron |
| `ml_factor_loader.py` | ML概率加载器（双模型融合） | ✅ | 评分系统调用 |
| `verify_ml_prob.py` | ML概率T+1验证 | ✅ | 09:05 Cron |
| `run_ml_predict.py` | 持仓ML预测 | ✅ | 20:15 Cron |
| `mstnn_model.py` | MSTNN模型 | ✅ | 独立训练 |
| `ppe_factor.py` | PPE周期编码因子 | ✅ | 集成到strategy_scan |

### 持仓管理

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `portfolio_analysis.py` | 持仓数据获取（共用模块） | ✅ | |
| `holding_alert.py` | 持仓异常监控+推送 | ✅ | 盘中30分钟 |
| `dynamic_stop_loss.py` | 移动止损 | ✅ | |
| `portfolio_ann_monitor.py` | 持仓股公告监控 | ✅ | 10:15 Cron |
| `portfolio_tracker.py` | 持仓管理 | ✅ | |

### 舆情/公告

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `sentiment_analyzer.py` | 舆情分析 | ✅ | |
| `mx_search_daily.py` | MXSearch每日采集+收益计算 | ✅ | 00:40/09:05 Cron |
| `mx_signal_loader.py` | 舆情信号加载 | ✅ | 00:50 Cron |
| `announcement_monitor.py` | 公告信号监控 | ✅ | |
| `news_push.py` | 快讯推送 | ✅ | |
| `evening_news_classified.py` | 晚间资讯P0-P3分类 | ✅ | 22:00 Cron |

### 回测/验证

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `backtest_framework.py` | 选股回测框架 | ✅ | |
| `quick_backtest.py` | 月频简化回测 | ✅ | |
| `zt_analysis_v2.py` | 涨停次日溢价分析 | ✅ | |
| `recommendation_tracker.py` | 推荐追踪系统 | ✅ | |
| `daily_tracking_update.py` | 每日追踪更新 | ✅ | 16:45 Cron |

### 日报/报告

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `morning_report.py` | 早报 | ✅ | 09:00 Cron |
| `daily_decision_report.py` | 决策参考日报 | ✅ | 16:30 Cron |
| `daily_analysis.py` | 涨停分析 | ✅ | 16:17 Cron |
| `hermes_market_analysis.py` | 盘面分析日报 | ✅ | |
| `self_learn_review.py` | 每周复盘 | ✅ | 周五16:30 |
| `weekly_review.py` | 推荐统计周报 | ✅ | 周五17:00 |

### 数据采集

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `update_today_kline.py` | 全市场日K→DB | ✅ | 16:35 Cron |
| `collect_daily_zt_kline.py` | 涨停股K线入库 | ✅ | 16:10 Cron |
| `backfill_board_rps.py` | 历史板RPS回补 | ✅ | 一次性 |

### 工具

| 脚本 | 功能 | 状态 | 备注 |
|------|------|------|------|
| `factor_library.py` | 技术因子库 | ✅ | |
| `strategy_optimizer.py` | 策略优化 | ✅ | |
| `multi_strategy.py` | 多策略框架 | ✅ | |
| `capital_flow.py` | 资金流分析 | ✅ | |
| `fundamental_factors.py` | 基本面因子 | ✅ | |
| `chan_minute_analysis.py` | 缠论多周期 | ✅ | |
| `margin_visualizer.py` | 融资融券可视化 | ✅ | |
| `analyze_pool_688.py` | 688池筛选 | ✅ | |
| `system_health_check.py` | 系统巡检 | ✅ | 周一09:00 |
| `daily_auto_fix.py` | 自动修复 | ✅ | 16:40 Cron |
| `cleanup_chrome.py` | Chrome进程清理 | ✅ | 盘中30分钟 |
| `trade_tracker.py` | 交易追踪 | ✅ | |
| `trade_result_tracker.py` | 交易结果追踪 | ✅ | 09:10 Cron |
| `add_decision.py` | 记录决策 | ✅ | |
| `anti_lookahead.py` | 反前瞻偏误 | ✅ | `src/tools_h/` |

---

## 三、实验目录 (experimental/)

> 所有实验性脚本，不碰现有系统

| 脚本 | 功能 | 状态 |
|------|------|------|
| `pipeline.py` | 三步串联主流程 | ✅ 跑通 |
| `step1_sector_filter.py` | 板块RPS筛选（efinance实时） | ✅ |
| `step2_volume_price.py` | 量价资金强度（量比>2.0） | ✅ |
| `step3_momentum_confirm.py` | 动量确认（4~7%,量比>2.0,3日<12%） | ✅ |
| `ml_regression_train.py` | 回归模型训练 | ✅ 验证通过 |
| `backfill_kline.py` | DB数据补充（腾讯API） | ✅ 已执行 |
| `rebuild_board_cache.py` | 板块缓存重建（akshare被封） | ⚠️ 待修复 |
| `_audit_data.py` | 数据质量审计 | ✅ |

---

## 四、ML模型文件

| 文件 | 功能 | 大小 | 更新 |
|------|------|------|------|
| `quant_ml/data/models/lgbm_unified.pkl` | 分类模型 | 600KB | 2026-07-04 16:02 |
| `quant_ml/data/models/lgbm_calibrator.pkl` | 分类校准器 | 1KB | 2026-07-04 16:02 |
| `quant_ml/data/models/lgbm_regressor.pkl` | 回归模型 | 614KB | 2026-07-04 16:37 |
| `quant_ml/data/models/mstnn_model.pth` | MSTNN | 65KB | 2026-07-04 01:56 |
| `scripts/ml_latest_prob.pkl` | 分类概率（2405只） | 19KB | 2026-07-04 16:02 |
| `scripts/ml_regression_pred.pkl` | 回归预测（421只） | 8KB | 2026-07-04 16:37 |
| `scripts/mstnn_latest_prob.pkl` | MSTNN概率 | 9KB | 2026-07-04 01:56 |

---

## 五、数据资产

| 资产 | 路径 | 大小 | 说明 |
|------|------|------|------|
| **market_data.db** | `F:\market_data.db` | 979MB | 核心K线数据库，永久保留 |
| 符号链接 | `data/market_data.db` | — | 指向F盘 |
| 板块缓存 | `data/stock_board_cache.json` | 3848只/53板块 | 待扩展到90板块 |
| 推荐追踪 | `data/recommendation_tracker.json` | 2条 | 待T+1验证 |
| 持仓记录 | `data/portfolio.json` | 空仓 | 2026-06-29清仓 |
| 交易历史 | `data/trade_history.json` | — | |
| 决策日志 | `data/decisions.json` | — | |
| 股票池 | `config/stock_pool.json` | 67只 | Q1高增长 |

### DB表结构

| 表 | 行数 | 说明 |
|----|------|------|
| `daily_k` | 6,743,457 | 日K线（2019~2026） |
| `stock_turnover` | 234,187 | 换手率 |
| `stock_st_status` | 8,772 | ST标记 |
| `daily_zt` | 2,027 | 涨停数据 |
| `zt_kline` | 0 | 涨停K线（未填充） |

---

## 六、Cron任务时间轴

### 早盘

| 时间 | 任务 | 脚本 | 模式 |
|------|------|------|------|
| 00:40 | MXSearch采集 | `mx_search_daily.py --collect` | systemEvent |
| 00:50 | MXSearch信号加载 | `mx_signal_loader.py` | systemEvent |
| 09:00 | 外盘+情绪早报 | `morning_report.py` | systemEvent |
| 09:05 | ML概率T+1验证 | `verify_ml_prob.py` | systemEvent |
| 09:05 | MXSearch收益计算 | `mx_search_daily.py --calculate` | systemEvent |
| 09:10 | 交易结果追踪 | `trade_result_tracker.py` | systemEvent |
| 09:40 | 尾盘策略(早盘) | `strategy_scan.py --mx` | systemEvent |

### 盘中（每30分钟）

| 时间 | 任务 | 脚本 |
|------|------|------|
| 9:00~14:00 | 盘中RPS跟踪 | `rps_analysis.py` |
| 9:00~14:00 | 持仓异动提醒 | `holding_alert.py --check --push` |
| 9:00~16:00 | Chrome进程清理 | `cleanup_chrome.py` |

### 午盘

| 时间 | 任务 | 脚本 | 模式 |
|------|------|------|------|
| 10:00 | 神奇公式选股 | `magic_formula.py` | systemEvent |
| 10:15 | 持仓公告监控 | `portfolio_ann_monitor.py` | systemEvent |
| 14:30 | 尾盘策略(午盘) | `strategy_scan.py --mx` | systemEvent |

### 收盘后

| 时间 | 任务 | 脚本 | 模式 |
|------|------|------|------|
| 16:05 | 形态捕手雷达 | `xingtai_integration.py all` | systemEvent |
| 16:10 | 申万90板RPS采集 | `fetch_board_rps.py` | systemEvent |
| 16:10 | 涨停K线收集 | `collect_daily_zt_kline.py` | systemEvent |
| 16:14 | RPS收盘分析 | `rps_daily_summary.py` | systemEvent |
| 16:17 | 涨停溢价分析 | `daily_analysis.py` | systemEvent |
| 16:30 | 决策参考日报 | `daily_decision_report.py` | systemEvent |
| 16:35 | K线数据入库 | `update_today_kline.py` | systemEvent |
| 16:40 | 每日自动修复 | `daily_auto_fix.py` | systemEvent |
| 16:45 | 推荐追踪更新 | `daily_tracking_update.py` | systemEvent |

### 晚间

| 时间 | 任务 | 脚本 | 模式 |
|------|------|------|------|
| 20:00 | ML统一训练 | `pipeline/unified_train.py --quick` | systemEvent |
| 20:15 | ML持仓预测 | `run_ml_predict.py` | systemEvent |
| 22:00 | 晚间资讯分类 | `evening_news_classified.py` | systemEvent |

### 周度

| 时间 | 任务 | 脚本 | 模式 |
|------|------|------|------|
| 周一09:00 | 系统巡检 | `system_health_check.py` | systemEvent |
| 周五16:30 | 每周复盘 | `self_learn_review.py` | systemEvent |
| 周五17:00 | 推荐统计周报 | `weekly_review.py` | systemEvent |

---

## 七、Skills（ClawHub安装）

| Skill | 版本 | 功能 |
|-------|------|------|
| investment-analyst | 1.0.0 | 投资分析（基本面+技术面） |
| china-stock-analysis | 1.0.0 | A股/港股行情+买卖建议 |
| china-stock-sentiment | 0.1.1 | A股舆情分析 |
| multi-factor-strategy | 1.0.0 | 多因子策略配置 |
| portfolio | 3.4.2 | 持仓管理+再平衡 |
| backtest | 1.0.2 | 回测引擎 |
| akshare-backtest | 1.0.3 | Akshare回测 |
| xingtai-catcher | — | 形态捕手（手动安装） |

---

## 八、数据源API

| 数据 | API | 状态 |
|------|-----|------|
| 日K线 | 腾讯 `ifzq.gtimg.cn` | ✅ |
| 实时行情 | 腾讯 `qt.gtimg.cn` | ✅ |
| 板块成分股 | efinance `get_belong_board` | ✅ |
| 板块指数 | 腾讯 `ifzq.gtimg.cn` | ✅ |
| 历史K线回补 | 腾讯 `ifzq.gtimg.cn` | ✅ |
| 资金流向 | 东财 f62/f47/f48 | ❌ 被封 |
| 板块RPS | akshare THS申万 | ⚠️ 不稳定 |
| 行业板块成分股 | akshare 东财 | ❌ 被封 |
| 公告 | 东财公告API | ❌ 被封 |

---

## 九、Pipeline参数（最终版）

```
Step1: 板块RPS筛选
  - RPS≥70的强势板块
  - efinance实时获取成分股
  - 不依赖本地缓存

Step2: 量价资金强度
  - MA多头排列（MA5>MA10>MA20）
  - 量比>2.0
  - 今日上涨

Step3: 动量确认
  - 今日涨幅 4%~7%
  - 量比>2.0
  - 近3日涨幅 <12%
  - 前2日单日涨幅 <7%
  - MA20趋势向上（近5日上升）
```

---

## 十、已知问题

| 问题 | 影响 | 状态 |
|------|------|------|
| 东财资金流API被封 | 无法获取主力净流入 | 用量价替代 |
| akshare不稳定 | 板块数据获取失败 | 用efinance替代 |
| 板块缓存53/90个 | 部分强势板块无法匹配 | efinance实时获取 |
| DB 7天异常日 | 数据缺失 | 需补充 |
| 复权数据不一致 | 部分股票价格长时间不变 | 需清理 |
| 训练标签极端值 | 回归模型被拉偏 | 需裁剪 |
| ML概率均值0.0019 | 评分映射需用排名分 | 已修复 |
| RPS历史数据仅15天 | 无法回测RPS效果 | 需积累 |

---

## 十一、Pipeline回测验证结论

```
尾盘策略（宽松版）：
  涨幅 4~7% + 量比>2.0 + MA20向上 + 近3日<12%
  
  量比≥2.0:  144次, 胜率43.1%, 均值-0.56%, 盈亏比0.92
  量比≥3.0:   50次, 胜率50.0%, 均值+0.77%, 盈亏比1.86  ← 最佳
  量比≥4.0:   24次, 胜率54.2%, 均值+1.29%, 盈亏比2.18  ← 信号少但质量高

  结论：量比越高胜率越高，但信号越少。
  当前使用量比>2.0作为平衡点。
```

---

_文档维护: Alice | 最后更新: 2026-07-04 20:50_