# 光伏获客系统 — 子系统设计文档

## 概述
帮光伏公司更高效获取客户线索的SaaS系统。五层架构，Python实现。

## 目录结构
```
workspace-pv/
├── AGENTS.md           # 子系统说明
├── docs/
│   └── ARCHITECTURE.md # 系统架构设计基准文档（必读）
├── industry_config/    # 行业插件层（可插拔配置包）
│   ├── solar/          # 光伏行业插件（当前测试）
│   │   ├── keywords.json     # 行业关键词词库
│   │   ├── value_prop.md     # 价值主张文案
│   │   ├── templates/        # 内容模板（5方向）
│   │   └── prompts/          # AI提示词
│   └── template/       # 新行业插件模板参考
├── config.py           # 全局配置（已迁移至industry_config）
├── data/
│   ├── raw/            # 原始采集数据
│   ├── processed/      # 处理后数据
│   ├── output/         # 输出报告
│   ├── content/        # 已生成内容脚本
│   └── pv.db           # SQLite数据库（本地工作库）
├── scripts/
│   ├── run.py          # 运行入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── industry_plugin_loader.py  # 行业插件加载器（新增）
│   │   ├── main.py     # 主入口
│   │   ├── database.py # 数据仓库（7+张表）
│   │   ├── pipeline.py # 流水线编排器
│   │   ├── hot_topic_collector.py  # 热点采集
│   │   ├── policy_monitor.py      # 政策监控
│   │   ├── pv_analyzer.py         # 数据分析
│   │   ├── content_generator.py   # 内容生成
│   │   ├── content_analyzer.py    # 竞品内容分析
│   │   ├── competitor_monitor.py  # 竞品监控
│   │   └── report.py
│   └── utils/          # 工具函数
└── web/                # Web管理后台（后期）
```

## 数据库表结构
1. **hot_topics** — 热点话题（标题、来源、热度、光伏相关度）
2. **policies** — 政策信息（标题、省份、级别、类型、补贴金额）
3. **competitors** — 竞品账号（平台、名称、粉丝数）
4. **competitor_contents** — 竞品内容（标题、播放量、点赞数）
5. **pv_companies** — 光伏公司信息（名称、地区、类型）
6. **region_data** — 区域数据（日照时数、电价、补贴、装机容量）
7. **system_logs** — 系统日志
8. **leads** — 线索池（新增，内容级归因）
9. **customers** — 成交客户（新增）
10. **content_items** — 内容追踪（新增，唯一追踪ID）

## 数据流
```
行业插件(solar/) → L2数据采集 → L3内容生成 → L1渠道发布 → L4线索收集 → L5归因反馈 → L3优化
```

## 当前状态
✅ S1 数据+内容引擎（通用骨架+光伏插件）
✅ 行业插件层落地（industry_config/solar/）
✅ 架构文档定稿（docs/ARCHITECTURE.md）
⏳ S2 抖音渠道打穿 + 线索手动录入
⏳ S3 归因闭环（内容级追踪ID）
⏳ S4 行业插件化验证（新建edu插件）
⏳ S5 多渠扩张

## 数据源核实结论（2026-08-16 逐一实测）

### ✅ 稳定可用
| 数据源 | 采集方式 | 实测结果 | 说明 |
|--------|---------|---------|------|
| **百度热搜** | s-data JSONP (`top.baidu.com/board?tab=realtime`) | 51条/次，HTTP 200 | 全网热点，光伏相关少（社会热点为主），用于横向参考 |
| **索比光伏网** | urllib直抓 (`news.solarbe.com`) | 15条，6条光伏相关 | 光伏垂直媒体，政策解读精准（浙江/江苏/山东分布式细则等） |
| **国家能源局** | urllib直抓 (`nea.gov.cn/sjzz/xny/index.htm`) | 15条，6条光伏相关 | 官方权威，494链接/151光伏相关，唯一权威政策源 |

### ❌ 不可用（已废弃）
| 数据源 | 原因 | 替代方案 |
|--------|------|---------|
| **北极星光伏网** | JS渲染，urllib拿到0个`<a>`标签 | 需BrowserAct/换接口 |
| **CPIA中国光伏协会** | HTTP 500 | 需换域名/接口 |
| **百度搜索** | 安全验证拦截（1438字符验证码页） | 改用其他搜索/直抓 |
| **Google搜索** | ascii编码错误 + 国内超时 | 弃用 |

## 运行方式
```bash
python scripts/run.py
```