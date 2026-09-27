---
date: 2026-08-19
system: 光伏获客(workspace-pv)
type: L6Dashboard+清理
severity: P1
---

# L6 Dashboard + 系统清理

## 完成内容

### L6 战略层 - ROI Dashboard
- **新增模块**: `scripts/core/l6_dashboard.py`（ROI战略看板）
- **集成**: 自动调用在 content_generator.run() 末尾
- **输出**: `data/output/dashboard/l6_dashboard_YYYYMMDD_HHMM.txt`
- **分析维度**: 整体概览 / 渠道ROI / 模板表现 / 策略建议
- **框架完整**，待真实数据回填后激活策略建议

### Web Dashboard (进行中)
- **后端API**: `scripts/core/dashboard_api.py` — 查询DB返回JSON
- **HTTP服务**: `scripts/core/dashboard_server.py` — 端口8765
- **前端**: `docs/dashboard.html` — 交互式面板
  - 核心指标卡（总数/发布/草稿/收入）
  - 渠道对比柱状图
  - 日趋势图（近7天）
  - 内容表格（Tab切换+搜索筛选）
  - 回填数据弹窗
  - 架构健康度展示
- **状态**: 服务器已启动但浏览器打不开，待排查

### 废弃日志清理
- 删除63个旧调试报告（report_/content_/insights_/final_等）
- data/output/ 从80个文件 → 约17个

### S5 渠道路径修复
- douyin.py / toutiao.py 的 BASE 路径从 parent.parent.parent 改为 parent.parent.parent.parent（4级）
- 输出路径修正为 workspace-pv/data/output/douyin/ 和 toutiao/

## 今日数据
- 总内容: 135条 | 已发布: 104 | 草稿: 31
- 归因: 2条（测试）| 成交: ¥13,000
- 热点: 319条 | 政策: 16条 | 线索: 6条
