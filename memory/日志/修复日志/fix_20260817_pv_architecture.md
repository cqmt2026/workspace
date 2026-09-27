# 修复日志 - 2026-08-17 光伏获客系统架构设计与插件化

## 目标
从单一光伏系统升级为"多行业通用获客引擎"，按模块化框架完整设计架构

## 完成内容

### ① 架构文档定稿
- 文件：`docs/ARCHITECTURE.md`（8199字节）
- 六层架构：L1渠道/L2数据/L3内容/L4线索/L5反馈/L6战略 + 行业插件层
- 统一接口：ChannelAdapter / ContentPack / IndustryPlugin
- 数据库双轨：本地SQLite（采集素材）+ 业务表（leads/customers/content_items/attribution）
- 建设路径：S1（数据+内容）→ S2（抖音打穿）→ S3（归因闭环）→ S4（插件化验证）→ S5（多渠扩张）

### ② 光伏行业插件落地
- `industry_config/solar/keywords.json` — 41个关键词、31个省份
- `industry_config/solar/templates/` — 5个方向模板（policy/benefit/avoid/news/tech）
- `industry_config/solar/prompts/` — 3个AI提示词（hook/body/cta）
- `industry_config/solar/value_prop.md` — 价值主张文案
- `industry_config/template/` — 新行业插件模板参考

### ③ 行业插件加载器
- `scripts/core/industry_plugin_loader.py` — 通用插件加载器
- 支持多插件注册、关键词评分、方向分类
- 换行业 = 复制template → 改名 → 改配置，引擎零修改

### ④ AGENTS.md更新
- 目录结构重编（新增industry_config/docs）
- 数据库表新增leads/customers/content_items/attribution
- 数据流改为闭环结构
- 版本状态更新为S1完成

## 架构关键决策
| 决策 | 选择 | 理由 |
|------|------|------|
| 数据库选型（前期） | SQLite单机 | 零成本验证，未来可迁移 |
| 归因颗粒度 | 内容级 | 每条内容唯一追踪ID |
| 渠道接口 | ChannelAdapter抽象 | 换渠道不改引擎 |
| 行业扩展 | 插件目录+注册表 | 引擎完全通用 |

## 下一步行动
1. 完善leads/customer/content_items表schema（database.py新增）
2. S2：实现content_generator读取industry_config插件，而非硬编码
