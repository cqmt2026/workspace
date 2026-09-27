# 每日交易任务时序（工作日）

## 上午

| 时间 | 任务 | 说明 |
|------|------|------|
| 09:00 | INV-Morning-News | 早间新闻 |
| 09:00 | Hot-Topic-Finder | 热点发现 |
| 09:00 | Web-Hot | 全网热点 |
| 09:00 | Novel-Daily-Write | 小说创作 |
| 09:00 | AI-Retry | 错题重试 |
| 09:35 | INV-Watchlist-Verify | 观察池验证 |
| 10:00 | INV-PaperTrading-H074 | 早盘强势扫描 |
| 10:00 | WX-知识库-自动更新 | 微信知识库 |
| 10:30 | WX-Corrections-同步检查 | 踩坑记录检查 |

## 盘中

| 时间 | 任务 | 说明 |
|------|------|------|
| 每30分 | INV-RPS-Intraday | RPS板块实时采集（9:00-14:00） |
| 12:00 | 子系统健康检查 | 核心文档完整性 |
| 14:00 | 流程问题触发检查 | 重复踩坑检测 |

## 下午

| 时间 | 任务 | 说明 |
|------|------|------|
| 14:25 | INV-Closing-Strategy | 尾盘策略 |
| 14:45 | INV-PaperTrading-v5 | 尾盘双轨扫描 |
| 15:00 | INV-RPS-Closing | 收盘RPS采集 |
| 16:00 | INV-数据质量监控 | 数据质量检查 |
| 16:05 | **INV-Daily-Fetch** | **每日增量K线采集（新增）** |
| 16:10 | INV-ZT-Kline-Collect | 涨停K线采集 |
| 16:10 | INV-Daily-Analysis | 每日分析 |
| 16:10 | INV-RPS-Daily-Summary | RPS日报 |

## 盘后

| 时间 | 任务 | 说明 |
|------|------|------|
| 20:00 | INV-ML-Training | 机器学习训练 |
| 22:00 | INV-Evening-News | 晚间新闻 |

## 每30分钟（不分交易日）

| 任务 | 说明 |
|------|------|
| INV-Holding-Alert | 持仓提醒 |
| INV-Chrome-Cleanup | Chrome清理 |
| System-Maintenance | 综合维护 |

---
更新：2026-05-30 修复4个announce投递错误，改为none模式安静执行