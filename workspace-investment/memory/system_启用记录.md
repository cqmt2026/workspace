# 系统启用确认
# 2026-07-05 23:26

## 启用状态

### 已启用（明天Cron自动运行）
- [x] 16:45 因子计算 → factors.db (daily_factor_compute.py)
- [x] 16:50 IC监控 → factor_status表 (daily_ic_compute.py)
- [x] 基本面+资金流已回补32天历史数据
- [x] 回测引擎（fast/full双模式）

### 保留老系统（策略执行层不变）
- [ ] 09:40/14:30 尾盘策略 (strategy_scan.py --mx)
- [ ] 16:30 每日日报 (daily_decision_report.py)
- [ ] RPS全链路分析

### 等待Cron积累后切换
- [ ] Pipeline v2 评分替代37项评分（等35因子齐全）
- [ ] 全量回测验证（等20天+完整数据）

## 关键日期
- 明天（周一 2026-07-06）：首个完整Cron日，16:45因子计算首次运行
- 5~10个交易日后：factors.db积累到35因子，准备切换策略评分