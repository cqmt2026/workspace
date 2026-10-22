# HEARTBEAT.md - Cron任务总表

**最后更新**: 2026-10-18

## 🕐 9点高峰期错峰时间表（2026-09-05优化）

| 时间 | 任务 | 说明 |
|------|------|------|
| 08:45 | Pre-Market-Check | 开盘前预检(交易日) |
| 09:01 | Daily-Morning-Report | 主系统早报 |
| 09:02 | Hot-Topic-Finder | 头条房地产热点采集 |
| 09:05 | LOG-日志审计-每日检查 | 等早报完成后执行 |
| 09:06 | Web-Hot-全网热点 | 全网热点采集 |
| 09:12 | AI-Retry-错题重试(9/15点) | 9点和15点各一次 |
| 09:15 | INV-RPS-每日推送(交易日) | 开盘后推送强势股 |
| 09:22 | INV-Morning-Brief-早盘参考(交易日) | 开盘后参考 |
| 09:35 | INV-Closing-Strategy-开盘(交易日) | 尾盘策略扫描 |
| 15:30 | INV-Closing-Report | 收盘主动汇报(交易日) |

**原则**：9点高峰期错峰触发，依次间隔1-5分钟，避免并发过载。
**Model**: `sensenova/sensenova-6.7-flash-lite`（主）→ `meta/llama-3.3-70b-instruct`（fallback）

---

## ⚡ 2026-09-05 优化记录

### Cron错峰调度（13个任务）
- 早间区（09:25-09:40）：Daily-Inspection、Morning-Report、LOG审计
- 午间区（09:20-16:45）：Memory-Recall、AI-Retry、INV-Analysis
- 晚间区（18:30-22:50）：Evening-Report、Self-Learning、P0-P3任务

### 模型切换
- 高失败率任务切换为 `sensenova-6.7-flash-lite`
- 预期成功率：52% → 70-75%

---

## 基础维护

| 任务 | 时间 | 说明 |
|------|------|------|
| System-Maintenance | 每30min | Session+Token+PREF整合+自我优化 |
| Self-Heal-L1-Monitor | 每30min | Cron异常检测+微信推送 |
| Core-Docs-Sync | 每1h | 文档平台同步 |
| Memory Dreaming | 每天03:00 | 认知收编 |
| Obsidian-日记生成 | 每天21:00 | 自动生成日记 |
| Obsidian-领域关系图更新 | 每天05:00 | 更新投资/创作领域Mermaid图 |
| Obsidian-今日推荐 | 每天08:00 | 更新agent.md的未读笔记推荐 |

## 内容/热点

| 任务 | 时间 | 说明 |
|------|------|------|
| Hot-Topic-Finder V4.0 | 09:02 | BrowserAct采集头条房地产热点 |
| Web-Hot | 09:06 | 全网热点 |
| AI-Retry | 09:12/15:12 | 失败重试 |

## 地图热点子系统

| 任务 | 时间 | 说明 |
|------|------|------|
| MapHot-选题采集 | 10:00 | 百度热搜+mx-search双源采集 |
| MapHot-流水线 | 10:00后 | 自动执行完整流水线 |

> 完整流程：选题采集(1) → 脚本生成(2) → 地图绘制(3) → 配音生成(4) → 调色(4.5) → 视频合成(5) → 发布
> 工具：pipeline.py (core/) + hyperframes_template.py (core/) + video-use (video-use/helpers/) + cutmv-video-tool (cutmv-video-tool/)

## 微信小程序

| 任务 | 时间 | 说明 |
|------|------|------|
| WX-知识库更新 | 10:00 | 知识库一致性检测 |
| WX-Corrections同步 | 10:30 | 踩坑记录检测 |

## 百都工作子系统

| 任务 | 时间 | 说明 |
|------|------|------|
| Baidu-早间计划 | 09:00 | 生成今日拨打清单+话术提醒 |
| Baidu-日报生成 | 17:30 | 汇总今日拨打数据 |
| Baidu-周复盘 | 周三14:00 | 本周数据分析+话术迭代 |

> 路径：workspace-baiduagent/
> 核心：客户名单（2275家专精特新+5大蓝海行业）+ 电话脚本 + CRM

## 日志管理

| 任务 | 时间 | 说明 |
|------|------|------|
| LOG-审计-每日检查 | 09:05 | Cron日志完整性 |
| Self-Learning统一学习 | 21:00 | 日志审计+corrections+知识库+报告 |
| LOG-审计-晚间检查 | 22:00 | 当日完整性检测 |
| Novel-自我学习 | 11:00 | 小说知识入库 |
| Social-自我学习 | 11:30 | 爆款特征学习 |
| Math-自动学习 | 12:00 | 数学动画数据分析 |

## 小说子系统

| 任务 | 时间 | 说明 |
|------|------|------|
| Novel-质检审核 | 12:00 | 章节质量检查 |
| Novel-去AI味 | 13:00 | 内容优化 |

> 路径：workspace-novel/
> 核心：创作引擎 + 知识库 + 去AI味

## 子系统管理

| 任务 | 时间 | 说明 |
|------|------|------|
| Daily-Morning-Report | 09:00 | 仪表盘推送子系统状态 |
| 子系统健康检查 | 12:00 | 指标采集+异常检测 |
| Cross-System-Bridge | 12:00 | 跨系统内容推荐 |
| Daily-Evening-Report | 18:00 | 仪表盘推送 |
| 流程问题检测 | 14:00 | 重复踩坑+流程问题 |
| 周巡检 | 周一10:00 | 一致性检查 |
| 备份清理 | 周日20:00 | 备份核心文档+清理过期文件 |
| C盘清理 | 周日17:00 | 清理缓存 |

## Obsidian知识库

| 任务 | 时间 | 说明 |
|------|------|------|
| Obsidian-知识沉淀 | 每天21:30 | 收集Cron产出→分类写笔记 |
| Obsidian-会话沉淀 | 每天22:00 | 扫描产出写入Obsidian |
| Obsidian-知识库审计 | 每周日20:00 | 检查损坏/重复/过期笔记 |
| Obsidian-知识关联 | 每周一11:00 | 提取关键词→生成关联图 |
| P0-读取率监控 | 22:30 | 扫描知识库笔记read_count |
| P1-知识驱动决策 | 22:35 | 扫描知识库策略信号 |
| P2-语义关联 | 22:40 | 跨分类关键词关联 |
| P3-时效管理 | 22:45 | 检查笔记时效性 |

## 投资系统

| 任务 | 时间 | 说明 |
|------|------|------|
| INV-策略-开盘 | 10:00 | 开盘策略测试 |
| INV-策略-午盘 | 13:30 | 午盘策略测试 |
| INV-策略-尾盘 | 14:30 | 尾盘策略测试 |
| INV-每日分析 | 16:15 | 每日分析报告 |
| INV-ZT-Kline收集 | 16:00 | 涨停K线数据 |
| INV-ML训练 | 20:00 | ML训练(timeout=2400s) |
| INV-策略回顾 | 周五16:00 | 策略回顾+修正 |

| 知识库一致性 | 12:00 | 卡点库+策略脚本 |
| 卡点优先级重审 | 每周五 | S/A/B等级验证 |

**当前策略**: 尾盘策略选择，多Agent+37项评分+8层风控，每日监控3次(10:00/13:30/14:30)

## Skill路由

脚本 scripts/skill_router.py 自动匹配，不需定义。
视频→video-script-generator | 热点→hot-topic-finder/web-hot | 去AI味→humanizer-zh | 投资→investment-analyst | 报错→capability-evolver-pro | 小说→novel-generator | 大纲→chapter_outline_check | 质检→chapter_quality_gate | 数学动画→video-frames | 标题→ai-prompt-optimizer-cn | 抖音视频→douyin-video/douyin.js

## Heartbeat规定

**启动时**: 读SOUL/USER/MEMORY/HEARTBEAT/session-state/daily_reminder → 检测Token状态
**运行中**: Token>80%提示主人 | 异常配置记corrections | 任务自动匹配Skill | 新学习同步PREFERENCES

## Hermes分工

Hermes=执行层(高频数据/写DB/Telegram推送)，OpenClaw=决策层(策略/写作/商业化)

---

_由可悦🌸 维护，2026-09-05_
