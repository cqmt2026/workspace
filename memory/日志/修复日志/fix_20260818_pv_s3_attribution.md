# 修复日志：光伏获客S3归因闭环

## 基本信息
- **日期**: 2026-08-18
- **子系统**: 光伏获客(workspace-pv)
- **类型**: S3归因闭环建设
- **严重度**: P1

## 完成内容
1. 新建 `scripts/core/tracker.py` — 追踪ID生成器
   - generate_id(): PV_YYYYMMDD_HHMMSSfff格式
   - extract_info(): 从ID提取channel和created_at
   - inject_url(): 在URL中注入utm追踪参数
2. 新建 `scripts/core/attribution.py` — 归因引擎
   - record_publish(): 记录内容发布
   - update_performance(): 回填播放/互动/线索数据
   - record_lead(): 记录线索来源（写入leads+attribution）
   - mark_converted(): 标记成交
   - get_content_roi(): 单条内容ROI
   - get_channel_roi(): 渠道ROI
   - get_template_performance(): 模板方向表现对比
   - adjust_template_weights(): 根据表现调整模板权重
   - get_content_summary(): 内容效果总览
3. content_generator升级v0.4
   - 自动注入tracking_id到每条内容
   - auto_record参数控制是否自动record_publish
   - 输出文件新增"追踪ID"字段
4. database.py改造
   - content_items表加tracking_id列
   - init_business_tables()建表语句更新
   - save_content_item()支持tracking_id参数
5. douyin.py更新
   - 调用save_content_item时传入tracking_id

## 验证结果
11/11 OK: tracking_id列存在、所有模块import、content_generator v0.4生成6条带追踪ID、attribution全链路测试通过、DB数据正确

## 影响范围
- 新增: tracker.py, attribution.py
- 修改: content_generator.py (v0.3→v0.4), database.py, douyin.py
- 不涉及: DB结构变更（仅新增列）
