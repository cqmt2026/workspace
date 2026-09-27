# 修复日志：光伏获客S2完整建设

## 基本信息
- **日期**: 2026-08-18
- **子系统**: 光伏获客(workspace-pv)
- **类型**: S2渠道+素材+线索完整建设
- **严重度**: P1

## 完成内容

### 新模块
1. `scripts/core/channel/base.py` — ChannelAdapter抽象接口 + ContentPack/PublishResult/PerformanceData
2. `scripts/core/channel/douyin.py` — 抖音导出适配器（Markdown格式）
3. `scripts/core/material_lib.py` — 素材整合模块（整合L2各数据源）
4. `scripts/core/lead_manager.py` — 线索管理模块（录入+打分+分级）
5. `scripts/core/template_engine.py` — 模板渲染引擎（读插件templates/prompts）

### Bug修复
1. `pv_analyzer.py` — `self.execute()` → `self.db.conn.cursor()`（4处）
2. `content_generator.py` — `{kw}` 占位符缺失 → 移除
3. `material_lib.py` — `get_all_region_data` → `get_region_data`
4. `template_engine.py` — `fname` 未定义 → 在render_template开头添加
5. `database.py` — `save_content_item` 错误插入类外 → 正确插入到PVDatabase类
6. `content_generator.py` v0.1→v0.2 重构：使用TemplateEngine后端渲染

### DB扩展
- 新增4张业务表：leads, content_items, campaigns, attribution
- `init_business_tables()` 函数
- `PVDatabase.save_content_item()` 方法

### Cron修复
- PV-HotTopic-采集：补充delivery(channel/to/accountId)，timeout 180→600s
- PV-Daily-Content-生成：同上
- 微信推送验证成功

## 验证结果
6/6 OK: content_gen, pipeline, material_lib, lead_manager, template_engine, douyin_channel
DB: 244 hot_topics, 16 policies, 4 leads, 6 content_items

## 影响范围
- scripts/core/ 新增3个文件，修改5个文件
- scripts/core/channel/ 新增2个文件
- data/pv.db 新增4张表
- docs/PROGRESS.md 更新
- 系统知识手册追加6条陷阱记录
