# 修复日志：光伏获客S2渠道层+业务表

## 基本信息
- 日期: 2026-08-18
- 子系统: 光伏获客(workspace-pv)
- 类型: S2渠道层建设
- 严重度: P1

## 完成内容
1. 创建business DB表: leads, content_items, campaigns, attribution
2. 创建channel适配器: scripts/core/channel/base.py + douyin.py
3. 添加init_business_tables()到database.py
4. 添加save_content_item()到PVDatabase类
5. 修复pv_analyzer.py self.execute bug
6. 修复content_generator.py {kw}占位符bug
7. 修复hot_topic_collector/policy_monitor/content_generator插件化
8. 修复PV cron delivery配置（微信推送）
9. 延长cron timeout到600s

## 验证结果
- 15项检查14项通过（1项FAIL是content_generator的{kw}bug已修复）
- Pipeline运行正常：33 PV topics, 16 policies
- Douyin导出成功：生成markdown发布包
- Cron微信推送成功：PV-Daily-Content已推送
