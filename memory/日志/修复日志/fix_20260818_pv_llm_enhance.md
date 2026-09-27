# 修复日志：光伏获客LLM内容增强

## 基本信息
- **日期**: 2026-08-18
- **子系统**: 光伏获客(workspace-pv)
- **类型**: 内容质量升级（LLM增强）
- **严重度**: P2

## 问题描述
content_generator生成的正文是模板占位符（"今天聊一个光伏人基本都遇到过的问题…"），缺乏真实信息，内容空洞无法直接使用。

## 修复方案
1. 新建 `scripts/core/llm_enhancer.py`:
   - SolarLLMClient类：从openclaw.json读取sensenova provider配置，调用deepseek-v4-flash
   - generate_hook(): 生成30字内爆款钩子
   - generate_body(): 生成150字内真实正文
   - 429限流重试（3次，2s退避递增）
   - enhance_content(): 增强单条内容
2. content_generator升级v0.3:
   - 模板引擎生成基础 → LLM增强hook和body
   - use_llm参数控制是否启用
   - enhanced标记

## 验证结果
- LLM API连通: ✅ (deepseek-v4-flash, URL https://token.sensenova.cn/v1)
- 正文生成功示例: "镇江发布光伏倍增计划，到2030年分布式光伏规模要翻一番，达到5.6GW。→ 屋顶资源多的工厂、园区赶紧自查…"
- 原模板正文对比: "今天聊一个光伏人基本都遇到过的问题…"
- 12/13模块import成功（pipeline因stdout环境问题单独验证正常）

## 陷阱记录
- base_url可能已含`/v1`（sensenova的url是token.sensenova.cn/v1），需判断避免拼成/v1/v1
- sensenova API有429限流，需重试退避
- Windows下sys.stdout被关闭会导致content_generator内print报错，脚本末尾不要print

## 影响范围
- 新增 scripts/core/llm_enhancer.py
- 修改 scripts/core/content_generator.py (v0.2→v0.3)
- 同步 docs/PROGRESS.md