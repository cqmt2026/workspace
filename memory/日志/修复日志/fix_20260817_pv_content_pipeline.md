# 修复日志 - 2026-08-17 光伏获客系统推进

## 目标
继续光伏获客系统任务，依次推进：①内容生成模块 ②竞品监控 ③定时任务

## 完成内容

### ① 内容生成模块（ContentGenerator）
- 文件：`workspace-pv/scripts/core/content_generator.py`
- 功能：从数据库热点+政策自动生成短视频脚本
- 5个内容方向：政策解读/收益计算/避坑指南/行业新闻/技术科普
- 每条脚本含：钩子 + 正文 + CTA，可直接发布
- 输出：单条脚本文件 + 汇总报告
- 今日产出：6条脚本，已保存到 workspace-pv/data/content/

### ② 竞品监控模块（CompetitorMonitor）
- 文件：`workspace-pv/scripts/core/competitor_monitor.py`
- 功能：注册管理头部光伏竞品账号
- 已录入13个账号：正泰安能、创维光伏、天合富家、皇明、阿特斯、协鑫、晶澳、隆基、阳光电源、户用光伏（抖音+头条）
- 内容采集需后续接入Playwright

### ③ 定时任务
- PV-Daily-Content-生成：每日09:00
- PV-HotTopic-采集：每日10:00

### ④ Bug修复
- pipeline.py emoji编码问题 → Windows GBK兼容修复
- database.py get_pv_analysis() 新增30天总量统计

## 数据库状态
- hot_topics: 20条PV相关（bjx/solarbe/nea/mx_search四源）
- policies: 15条政策（含2026年户用补贴/浙江深圳河南地方政策）
- competitors: 13个竞品账号
- 今日新增: 10条PV话题

## 已知问题
1. 竞品内容采集未自动化（需Playwright接入抖音/头条）
2. solarbe/bjx有重复数据（同名标题不同来源）
3. 内容脚本模板偏固定，需后续迭代丰富度
