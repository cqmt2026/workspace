# TOOLS.md - 本地工具笔记（主系统）

**最后更新**: 2026-09-25

---

## Windows中文路径

PowerShell编码有问题。统一用Python：`scripts/cn_io.py`（read_file/write_file/find_novel_chapters）。
子任务写入后附前50字凭证，主会话Python读回验证，对上了才算完成。

## 网络工具

web_search ❌（DuckDuckGo被墙，用Python+Bing替代）| web_fetch ✅

## 抖音视频获取

**成功方法**：使用Node.js脚本 `skills/douyin-video/scripts/douyin.js`
**命令**：`node douyin.js "抖音短链"`
**原理**：HTTP请求→正则提取videoInfoRes JSON→解析视频信息→下载视频
**优势**：简单稳定，绕过JS渲染和反爬机制
**详情**：见 `skills/douyin-video/DOUYIN_METHOD.md`

**复用场景**:
- 投资系统: 分析财经类爆款视频
- 数学动画: 拆解竞品视频结构和内容
- 自媒体: 研究热点内容和互动数据
- 地图热点: 竞品视频下载+结构分析

## 关键脚本

| 路径 | 功能 |
|------|------|
| scripts/cn_io.py | 中文路径读写 |
| scripts/novel_workflow.py | 小说质控→去AI味→归档 |
| scripts/social_workflow.py | 自媒体调研→优化→去AI味→发布 |
| scripts/humanize_text.py | 去AI味 |
| scripts/obsidian_sync.py | Obsidian知识沉淀（每天21:30自动） |
| scripts/obsidian_daily.py | Obsidian日记生成 |
| scripts/obsidian_audit.py | 知识库审计+可信度评估（每周日20:00） |
| scripts/obsidian_link.py | 知识关联+索引（每周一11:00） |
| scripts/obsidian_save.py | 快速保存内容到Obsidian |
| scripts/obsidian_correct.py | 勘误标记 |
| scripts/auto_backup_clean.py | 每周备份清理（周日20:00） |
| scripts/system_maintenance.py | 系统维护（每30min） |
| scripts/methodology_health_check.py | 方法论检查（每周一10:05） |

## 多工作空间

| 工作空间 | 路径 | 用途 |
|---------|------|------|
| 主系统 | workspace/ | 核心配置+调度 |
| 小说系统 | workspace-novel/ | 创作引擎+知识库 |
| 投资系统 | workspace-investment/ | 行情+策略+ML |
| 自媒体系统 | workspace-social/ | 热点采集+发布 |
| 数学动画 | workspace-math/ | Manim渲染+配音 |
| 微信小程序 | workspace-weixin/ | 前端+后端 |
| 地图热点 | workspace-maphot/ | 流水线+地图绘制 |
| 百都系统 | workspace-baiduagent/ | 销售辅助+CRM |
| 光伏获客 | workspace-pv/ | 内容生成+视频合成 |

## HyperFrames

- **CLI**: v0.7.63（2026-09-25 验证）
- **渲染流程**: `lint` → `check` → `render --quality draft --output xxx.mp4`
- **低内存模式**: 自动启用，draft质量足够预览

## ForkProbe

- **路径**: `~/.agents/skills/forkprobe/`
- **功能**: 对比多个 Skill 在同一任务上的表现
- **用法**: `python scripts/recommend.py --text "<任务>" --domain <domain>`

## Obsidian知识库

- **路径**: `F:\Obsidian\Jarvis`
- **分类**: 00-日记 / 01-小说 / 02-自媒体 / 03-投资 / 04-数学动画 / 05-微信小程序 / 06-项目 / Z-归档
- **全量初始化**: `python scripts/obsidian_init.py`
- **快速保存**: `python scripts/obsidian_save.py "标题" "内容" [分类]`

---
_由可悦🌸 维护，2026-09-05_

- obsidian_audit cron的timeoutSeconds应设为300，120秒不够审计整个知识库
