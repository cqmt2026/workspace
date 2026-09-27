# 修复日志：光伏获客系统插件化集成

## 基本信息
- **日期**: 2026-08-18
- **子系统**: 光伏获客（workspace-pv）
- **类型**: 架构改造 + Bug修复
- **严重度**: P1

## 问题描述
1. pv_analyzer.py 使用了不存在的 self.execute() 方法，导致 analyze_hot_trends() 报错
2. hot_topic_collector.py 和 policy_monitor.py 硬编码从 config.py 读取 PV_KEYWORDS/PROVINCES
3. content_generator.py 的 _classify() 方法硬编码分类逻辑，未接入行业插件层
4. 这些导致系统虽能跑但违反了 ARCHITECTURE.md 定义的插件化原则

## 修复方案
1. pv_analyzer.py L48,L54: self.execute() → cur = self.db.conn.cursor()
2. hot_topic_collector.py: from core.config import PV_KEYWORDS,PROVINCES → from core.industry_plugin_loader import get_plugin，在 __init__ 中读取 plugin.keywords/plugin.provinces
3. policy_monitor.py: 同上
4. content_generator.py: _classify() 改为调用 self.plugin.classify_direction(title)

## 验证结果
- 14项检查全部通过
- pipeline 运行正常，采集到22条PV相关话题
- content_generator 生成6条脚本
- DB: 32条PV话题, 16条政策

## 影响范围
- scripts/core/pv_analyzer.py
- scripts/core/hot_topic_collector.py
- scripts/core/policy_monitor.py
- scripts/core/content_generator.py
- 不涉及数据库结构变更
