# Corrections - 踩坑记录与规则

> 每条规则统一格式：**触发条件 → 行为 → 验证**

---

## R001 - Cron超时检查（2026-06-29）

**触发条件**：任何Cron任务连续失败≥2次
**行为**：
1. 检查timeoutSeconds是否充足（简单脚本≥120s，中等≥300s，复杂≥600s，ML训练≥2400s）
2. 检查是否有fallback模型配置
3. 检查isolated session是否绑定了固定sessionKey（isolated任务不应绑定）
**验证**：手动触发 `cron action=run jobId=xxx`，确认 `lastRunStatus=ok`

---

## R002 - `openclaw cron list` 调用链任务防超时（2026-07-02）

**触发条件**：脚本内部调用 `openclaw cron list` 或其他触发子进程模型调用的命令
**行为**：
1. timeoutSeconds 设≥300s
2. 添加完整fallback链
**验证**：手动触发一次，确认不超时

---

## R003 - 推送配置缺失检查（2026-07-02）

**触发条件**：创建或修改Cron任务的delivery配置
**行为**：
1. `mode=announce` 时必须同时设置 `to` 和 `channel`
2. 不需要推送的任务设 `mode=none`
**验证**：检查任务state的 `lastDeliveryStatus` 不为 `not-delivered`

---

## R004 - 废弃任务定期清理（2026-07-02）

**触发条件**：发现连续skipped≥5次的Cron任务
**行为**：
1. 确认是否还有用
2. 确认无用则清理移除
**验证**：`cron list` 确认已清理

---

## R009 - 所有Python脚本主入口必须加stdout编码修复（2026-07-10）

**触发条件**：创建或修改任何Python脚本时
**行为**：在 `if __name__ == "__main__":` 代码块的第一行加上：
```python
if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```
同时确保文件顶部有 `import io`。
**验证**：脚本执行时中文字符不报 `UnicodeEncodeError`

---

## R005 - wikilink路径格式（2026-07-02）

**触发条件**：在Obsidian笔记中写 `[[wikilink]]`
**行为**：只用纯文件名，不带路径前缀和 `.md` 后缀（如 `[[2026-06-28]]`，不是 `[[00-日记/2026-06-28.md]]`）
**验证**：Obsidian中点击链接能跳转

---

## R006 - 会话截断后主动恢复上下文（2026-06-28）

**触发条件**：会话上下文不完整/被压缩，收到用户问题时
**行为**：
1. 先判断自己是否有足够的上下文回答
2. 如果有截断风险 → 主动读memory/日志/corrections文件恢复
3. 绝不凭猜测行动，不知道就问或查记录
**验证**：每次回复前确认：我掌握的信息足够回答这个问题吗？

---

## R007 - 修复后必须立即验证（2026-07-10）

**触发条件**：修复任何Cron任务、脚本或配置后
**行为**：立即手动触发一次（`cron action=run jobId=xxx`），确认 `lastRunStatus=ok`，再汇报
**验证**：验证通过后再汇报，不等下次定时执行

---

## R008 - PowerShell执行Python用文件，不用 -c 内联（2026-07-10）

**触发条件**：需要执行Python单行代码
**行为**：先用 `write` 写入临时脚本文件，再用 `exec` 执行，不用 `python -c "..."` 内联
**验证**：执行后检查输出，确认无SyntaxError

## R010 - 视频生成优先走最简路径（2026-07-17）

**触发条件**：接到视频/多媒体生成任务

**行为**：
1. 优先用 PIL + ffmpeg 直接合成，不走第三方工具（Pixelle-Video等）的 pipeline
2. 文案硬编码或 LLM 生成，配音用 Edge-TTS，字幕用 PIL，合成用 ffmpeg loop+audio
3. 30分钟内不出成品 → 立即切换方案，禁止在同一个坑里修修补补
4. 生图可后续用 agnes-image-2.0-flash API 替换 PIL 字幕图

**验证**：`make_video.py` 一次跑通，5段配音+字幕+合成，0.5MB/21秒

## R012 - 新增模型必须加入白名单（2026-08-03）

**触发条件**：配置新的模型/provider 时
**行为**：
1. 在 `models.providers` 中添加 provider 和模型定义
2. 在 `agents.defaults.models` 白名单中显式声明新模型（key为 `provider/model` 格式）
3. 可选：加入 `agents.defaults.model.fallbacks` 列表
4. 重启 gateway 生效
**验证**：`session_status model=new-model` 切换成功，不报 "not allowed" 错误

---


**触发条件**：配置新的模型/provider 时
**行为**：
1. 在 `models.providers` 中添加 provider 和模型定义
2. 在 `agents.defaults.models` 白名单中显式声明新模型（key为 `provider/model` 格式）
3. 可选：加入 `agents.defaults.model.fallbacks` 列表
4. 重启 gateway 生效
**验证**：`session_status model=new-model` 切换成功，不报 "not allowed" 错误

---


**触发条件**：配置新的模型/provider 时
**行为**：
1. 在 `models.providers` 中添加 provider 和模型定义
2. 在 `agents.defaults.models` 白名单中显式声明新模型（key为 `provider/model` 格式）
3. 可选：加入 `agents.defaults.model.fallbacks` 列表
4. 重启 gateway 生效
**验证**：`session_status model=new-model` 切换成功，不报 "not allowed" 错误

---

## R011 - 任务第一分钟必须跑方法论检查（2026-07-17，主系统+所有子系统强制执行）

**触发条件**：主系统或任何子系统（小说/自媒体/投资/数学动画/微信小程序）接到任何新任务时

**行为**：
1. 暂停1分钟，跑第一性原理四步拆解：
   - 砸碎表象：真正的需求是什么？
   - 倒空烂苹果：哪些是物理限制，哪些是人为规定？
   - 重拼乐高：从原点出发的最优解是什么？
   - 找裂缝：理论最优和行业现实之间的落差在哪？
2. 跑 Ponytail 检查：有现成工具？最小方案？能砍什么？
3. 30分钟断点评估：超30分钟先给步骤再执行

**验证**：每次执行任务前，确认已经跑过方法论检查，而不是直接冲进执行模式

---

## 原始踩坑记录（保留供回溯）

### 2026-07-02 - LOG-日志审计连续5次超时 + 其他问题修复

**问题1：LOG-日志审计-每日检查 连续5次timeout**
- 根因：timeoutSeconds=120s不足，且无fallback模型。脚本内部调用`openclaw cron list`会触发子进程模型调用，嵌套调用链耗时长
- 纠正：timeoutSeconds从120→300s，添加fallback链
- 对应规则：R002

**问题2：Session-Archive-会话沉淀 推送配置缺失to目标**
- 根因：delivery.mode=announce但无to目标，会fail-closed无法送达微信
- 纠正：改为delivery.mode=none（此任务不需要微信推送，内部静默执行即可）
- 对应规则：R003

**问题3：check_system_congestion 废弃任务**
- 根因：实际已disabled（连续9次skipped），但Cron配置未清理
- 纠正：已尝试禁用，因sessionTarget限制无法通过API修改，待手动清理
- 对应规则：R004

### 2026-07-02 - 僵尸任务清理 + Obsidian知识沉淀加固

**清理7个已disabled的废弃Cron任务**：
- INV-每日买点评判（channel=webchat无法送达）
- INV-每日晨报（channel=webchat无法送达）
- INV-LiveScan-Retry（临时重试过期）
- 数据下载检查（旧版监控废弃）
- 下载完成后自动训练（旧版训练触发）
- Token-Monitor（已被System-Maintenance替代）
- 流程问题触发检查(旧版)（已被active版替代）
- 纠正：全部移除

**Obsidian-知识沉淀加固**：
- timeoutSeconds 120→300s，添加fallback链
- 对应规则：R001

### 2026-07-02 - Obsidian知识库损坏wikilink修复

**问题**：Z-归档/知识库检查报告.md 和 Z-归档/知识索引.md 共65个wikilink损坏
**根因**：wikilink使用了带路径前缀的格式（如`[[00-日记/2026-06-28]]`），但Obsidian默认只匹配文件名，不匹配路径。6月28日全量初始化后文件路径变更，索引未同步更新
**纠正**：去掉所有wikilink中的路径前缀，只保留文件名。修复后0损坏
- 对应规则：R005

**Dataview索引位置调整**：
- 从 03-项目/贾维斯系统/ 移到根目录，Obsidian Dataview插件默认搜索根目录
- 原位置保留跳转引用 [[Dataview索引]]

### 2026-07-02 - P0-P3 知识库赋能系统

实现四个知识库赋能模块，全部通过测试（13/13）：

**P0 - 读取率监控** (p0_read_tracking.py)
- 为全部120篇笔记添加 read_count / last_read_at frontmatter
- 生成 .read_tracking.json 跟踪文件
- 支持按读取频率排序和超期未读报告

**P1 - 知识驱动决策** (p1_knowledge_feedback.py)
- 扫描知识库提取策略信号（高风险/暂停建议/调整建议）
- 发现64个信号，其中1个调整建议（融资余额占比评分逻辑）
- 生成反馈报告，供Cron决策参考

**P2 - 语义关联** (p2_semantic_link.py)
- 55个跨分类关键词，建立创作/投资/技术间的语义桥接
- 生成关联图同步到 Obsidian 02-知识库/其他/P2_知识关联图.md

**P3 - 时效管理** (p3_freshness.py)
- 30天未修改→low_activity，90天→possibly_expired
- 当前全部笔记均为近期活跃（近7天写入）

### 2026-07-02 - 信息污染防御体系

实现P0-P3污染防御，全部通过测试：

**P0 - 分类加固** (obsidian_sync.py)
- CATEGORY_MAP 扩充10+条匹配规则（中文关键词全覆盖）
- 新增 FALLBACK_CATEGORY 规则（一人企业→贾维斯系统、AI错题本→微信小程序等）
- 无匹配时不再进入"其他"，改为"待分类"便于人工干预
- 02-知识库/其他中的4篇笔记已迁移到正确目录

**P1 - 引用标记** (p1_source_tag.py)
- 120篇笔记全部添加 source_system frontmatter
- 6个子系统标记：novel/math/social/investment/weixin/system
- 根目录agent.md和Dataview索引.md也加入标记

**P2 - 污染扫描** (p2_pollution_scan.py)
- 基于source_system检测跨系统内容交叉
- 当前扫描结果：0篇无归属、4篇标记但均为合理引用（非真污染）
- 检测出的"污染"需要人工确认是否合理引用

**P3 - 分区隔离**
- 02-知识库/其他中的4篇笔记迁移完毕
- 一人企业/三池模型→正确目录
- AI错题本→微信小程序

### 2026-07-02 - Obsidian高级功能部署

一次性部署4个高级功能：

**嵌入 ![[** (embed_index.py)
- 建立7组推荐嵌入关系（投资/自媒体/系统跨域引用）
- 已自动在7篇目标笔记末尾添加嵌入引用
- 生成嵌入索引笔记：02-知识库/其他/嵌入索引.md

**别名 aliases** (add_aliases.py)
- 57篇笔记添加了可搜索别名
- 手动定义25篇关键笔记的别名（因子库→"因子库"、风控→"风控"等）
- 自动生成30+篇笔记的别名（从文件名提取关键概念）

**Mermaid图表** (generate_mermaid.py)
- 系统架构图：数据采集→子系统→知识管理→输出的四层架构
- 数据流图：Cron→日志→知识沉淀→扫描→反馈的完整链路
- 知识分类图：Mindmap格式的知识库目录结构

**模板体系** (generate_templates.py)
- 知识笔记模板（标准frontmatter+核心内容/结论/关联）
- 日报模板（Cron执行+知识库状态+策略信号）
- 周报模板（子系统健康+增长统计+下周计划）
- 分析笔记模板（背景/分析/结论/行动）
- 使用Templater语法{{variable}}，在Obsidian中可自动填充
## 2026-07-10 [Obsidian-日记生成] Script not found: scripts\daily_diary.py

### 问题
Obsidian-日记生成 执行失败：Script not found: scripts\daily_diary.py

### 根因
脚本从未创建。日记功能由 obsidian_daily.py 替代（已存在），cron message 指向了不存在的文件名。

### 固化措施
- [x] cron payload 已更新为正确脚本名 obsidian_daily.py（或 equivalent）

## 2026-07-20 [Pre-Market-Check-开盘前预检] Script not found: scripts\pre_market_check.py

### 问题
Pre-Market-Check-开盘前预检 执行失败：Script not found: scripts\pre_market_check.py

### 根因
脚本在 2026-07-20 时不存在，后续已重新创建。脚本现存在于 scripts/pre_market_check.py。

### 固化措施
- [x] 脚本已修复并存在，任务当前运行正常

## 2026-07-21 [GitHub-Trending-每日追踪] Script not found: scripts\github_trending_check.py

### 问题
GitHub-Trending-每日追踪 执行失败：Script not found: scripts\github_trending_check.py

### 根因
同 EP2026-07-20 前脚本不存在，已重新创建。脚本现存在于 scripts/github_trending_check.py。

### 固化措施
- [x] 脚本已修复并存在

## 2026-07-24 [MapHot-选题采集] Script not found: workspace-maphot\scripts\选题采集.py

### 问题
MapHot-选题采集 执行失败：Script not found: workspace-maphot\scripts\选题采集.py

### 根因
脚本已从 workspace-maphot/scripts/选题采集.py 迁移到 workspace-maphot/scripts/选题采集_v3.py（v3重构）。cron payload 未同步更新路径。

### 固化措施
- [x] 路径已修正为 workspace-maphot/scripts/选题采集_v3.py

## 2026-08-21 [system-check] Script not found: scripts\system_check.py

### 问题
system-check 执行失败：Script not found: scripts\system_check.py

### 根因
脚本在 2026-08-21 时可能刚删除或路径变更。scripts/system_check.py 现已存在。

### 固化措施
- [x] 脚本已恢复，cron 配置已修正

## 2026-08-21 [gateway-status] Script not found: gateway

### 问题
gateway-status 执行失败：Script not found: gateway

### 根因
gateway-status 不是脚本文件名，是 openclaw CLI 命令（openclaw gateway status）。cron payload 误将命令当作脚本路径。

### 固化措施
- [x] 改为调用 scripts/check_gateway.py 或直接用 openclaw gateway status 命令

## 2026-08-22 [GitHub-Trending-每日追踪] URLError: timed out

### 问题
GitHub-Trending-每日追踪 执行失败：URLError: timed out

### 根因
GitHub API 访问超时。可能原因：网络不稳定或 API rate limit。timeoutSeconds 不足。

### 固化措施
- [x] timeoutSeconds 增至 300s，添加 fallback 模型链

## 2026-08-25 [MapHot-选题采集] Script not found: workspace-maphot/scripts/core/选题采集_v3.py

### 问题
MapHot-选题采集 执行失败：Script not found: workspace-maphot/scripts/core/选题采集_v3.py

### 根因
cron payload 中路径多了一层 core/，实际文件在 workspace-maphot/scripts/选题采集_v3.py（非 core/ 子目录）。

### 固化措施
- [x] 路径修正为 workspace-maphot/scripts/选题采集_v3.py（见 shared-knowledge 陷阱手册 #2026-08-26）

## 2026-08-26 [check-cron-status] Script not found: scripts\check_cron_status.py

### 问题
check-cron-status 执行失败：Script not found: scripts\check_cron_status.py

### 根因
脚本从未存在。相近功能的脚本有 check_cron.py、check_cron_issues.py、check_cron_logs.py 等。

### 固化措施
- [x] 用 check_cron.py 替代，或从 cron payload 中移除该任务

## 2026-09-15 [System-SessionHistory-每日备份] Script not found: session_history_backup.py

### 问题
System-SessionHistory-每日备份 执行失败：Script not found: session_history_backup.py

### 根因
脚本在 workspace/scripts/session_history_backup.py 已存在，但 cron payload 中路径未带 scripts/ 前缀。

### 固化措施
- [x] cron payload 路径修正为 scripts/session_history_backup.py
