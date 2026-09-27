# HEARTBEAT.md - Cron任务总表（光伏获客）

**最后更新**: 2026-09-05

---

## 光伏获客子系统

| 任务 | 时间 | 说明 |
|------|------|------|
| PV-HotTopic-采集 | 10:00 | 四源采集+热点评分 |
| PV-Daily-Content-生成 | 09:00 | 热点+政策→生成短视频脚本 |

> 架构：`workspace-pv/docs/ARCHITECTURE.md`
> 工具链：hot_topic_collector + policy_monitor + content_generator + competitor_monitor
> 数据：workspace-pv/data/pv.db (SQLite)

---
_由可悦🌸 维护，2026-09-05_
