# 编码铁律（2026-07-14 新增）

## 架构基准铁律（2026-08-17 新增）

**光伏/获客子系统所有任务执行与优化升级，必须严格基于《多行业获客系统架构设计文档》**：

- **基准文档**: `workspace-pv/docs/ARCHITECTURE.md`（六层架构 + 行业插件层 + 统一接口 + S1-S5建设路径）
- **执行前必读**: 任何涉及光伏获客系统的开发/优化/迭代，先读此文档确认与架构一致，禁止凭直觉直接写代码
- **行业插件原则**: 通用引擎 + 行业插件（industry_config/<行业>/），换行业不改引擎
- **当前阶段**: S1完成+插件化改造（2026-08-18）：hot_topic_collector/policy_monitor/content_generator 均已接入 industry_config/solar/ 插件层；pv_analyzer bug已修复；pipeline正常运行
- **归属**: 这是system级规则，所有子系统/子Agent执行光伏获客任务时同样强制

## 架构文档同步铁律（2026-08-17 新增）

**任何经过验证的优化升级，都必须同步回更新《多行业获客系统架构设计文档》**：

- **验证才更新**: 只有经过验证的优化（已跑通/已测试通过）才写入文档，不留"规划中但未实现"的过时内容
- **先迁移后更新**: 新的/改进的模块代码落地后，同步更新 ARCHITECTURE.md（模块清单/接口/数据表/建设路径）
- **版本递增**: 每次重大变更后递增文档版本号（v0.1 → v0.2...），并在"关键决策记录"表追加记录
- **检查时机**: 每次光伏获客系统任务完成后，检查是否需要同步更新架构文档
- **落地位置**: 与架构更新对应的修复日志，存至 memory/日志/修复日志/ 并标注"架构同步"

---

# 编码铁律（2026-07-14 新增）

## 强制工作流（每次写代码必须执行）

### 开始前
1. `read` 目标文件 → 确认当前逻辑
2. `exec grep` 搜索调用点 → 确认影响范围
3. 确认 Python 版本、路径编码、依赖可用性

### 编写中
1. 遵循命名约定（snake_case/PascalCase/UPPER_SNAKE_CASE）
2. 边界情况同步处理（空输入/None/null/0/负数/极大值）
3. 遇到重复代码 → 立即提取函数
4. 错误处理用具体异常类型，不要裸 except

### 完成后
1. 运行验证测试（assert + print）
2. grep 确认没有遗漏的调用点
3. 错误信息完整可读

## 12 项短板对照表

| # | 短板 | 解决方式 | 优先级 |
|---|------|---------|--------|
| 1 | 语法/基础边界漏 | 每项检查空/None/0/负/超大 | P0 |
| 2 | 项目结构缺全局 | 改前先读+grep 调用点 | P0 |
| 3 | 调试能力低效 | 先看错误栈→二分法定位→日志验证 | P0 |
| 4 | 重构嗅觉弱 | 出现坏味道立即修（重复代码/长函数/深嵌套） | P1 |
| 5 | 测试意识缺失 | 核心逻辑必须有 assert 验证 | P0 |
| 6 | 性能意识不足 | O(n²) 操作检查 + 大文件逐行读 | P1 |
| 7 | 安全意识空白 | 用户输入不可信 + 参数化查询 | P1 |
| 8 | 错误处理简单 | 分层异常 + fallback | P0 |
| 9 | 代码可读性差 | 见名知意 + 注释解释为什么 | P1 |
| 10 | 版本管理弱 | git diff 确认变更 | P2 |
| 11 | 依赖管理随意 | 标准库优先 + 锁定版本 | P1 |
| 12 | 环境不一致 | 版本检查 + 路径处理 + utf-8 | P0 |

完整规范: `coding-standards.md`

---

### 2026-07-30 方法论铁律优化 (v1.2)

- **AGENTS.md** 方法论铁律版本化：v1.2
- **新增第四步：事后复盘（30秒）**：任务完成后的快速复盘，确保学习闭环
- **新增验证钩子**：执行前查 shared-knowledge/系统知识图谱与常见陷阱手册.md 匹配陷阱
- **新增执行中确认**：每步完成后验证结果，防止重复操作/凭感觉判断
- **触发时机补充**：新增地图热点子系统
- **新增方法论健康检查 cron**：每周一10:05扫描核心规则文件完整性/版本/一致性（scripts/methodology_health_check.py）
- **R1 文档自动同步**：system_maintenance.py 追加 sync_core_docs()，每30分钟检测5个核心文件日期一致性
- **R2 LLM 熔断**：run_with_log.py 追加熔断器，连续3次失败告警、5次熔断暂停24h，成功一次即重置
- **R3 记忆层降级**：memory_tools.py 已重构，DB 从 F:\\supermemory 迁移至本地 memory\\supermemory_db，所有域统一使用 LIKE 搜索（不依赖外部服务），365 条记录保留可读


- **陷阱手册更新**：新增 4 条陷阱记录（auto_stagger stale引用、edit换行符bug、Supermemory路径迁移、熔断器降级规则），更新至 698 行

- **R4 修复日志模板**\uff1a新增 TEMPLATE.md\uff08YAML frontmatter + 结构化字段\uff09\uff0c以后修复日志自动标签化

## 系统变更记录

### 2026-07-18 PPT模板批量生产系统 (v2.3)

- **Skill创建**: `ppt-template-producer` — 配置驱动→python-pptx生成→自检→修复→打包全流程
- **核心文件**: `scripts/gen_ppt_batch.py` + `scripts/ppt_templates_config.json`
- **产出**: 10套可售模板，23-25页/套，27种版式，81%标准符合度
- **调用方式**: 下次说"继续PPT模板"或"调ppt-template-producer"即接续
- **同步**: TOOLS.md已更新，skill提案已创建

### 2026-08-07 ForkProbe 安装与配置

- **安装**: `git clone` 到 `~/.agents/skills/forkprobe/`
- **依赖**: jinja2 ✅
- **验证**: 推荐功能正常（recommend.py 跑通），66个smoke测试中核心文本对比模块通过
- **Windows 限制**: artifact 管道（web/video/图）依赖 unix 命令，Windows 下部分失败；文本对比模式可用
- **调用方式**: 自然语言触发（"比较几个skill"）或 `/forkprobe`
- **同步**: TOOLS.md 已更新

### 2026-07-18 编程子Agent创建 (coding-agent)

- **Skill创建**: `coding-agent` — 专家级编程子Agent，主系统派发→编码→验收→交付
- **10条编码铁律**: 改前先读/影响面检查/边界全覆盖/标准库优先/错误处理分层/重复代码提取/命名规范/改完必验/报错先看栈/环境感知
- **工作流**: 子系统发现问题→报告给主系统→主系统派发→编程子Agent执行→主系统验收→交付子系统
- **适用**: 主系统/小说/自媒体/投资/数学动画/微信小程序/PPT模板，所有编程任务
- **禁止**: 不删文件/不改系统配置/不联网/不跨域回答
- **调用方式**: 主系统通过 sessions_send 或 sessions_spawn 派发任务
- **同步**: TOOLS.md已更新, skill提案已创建, AGENTS.md已更新

### 2026-07-18 巡检脚本修复

- **daily_inspection.py** 修复3个bug: 月份硬编码(06→动态)、Supermemory地址(已迁移)、Server酱残留检测排除
- **Server酱清理**: `holding_alert.py` 移除废弃server酱推送代码
- **磁盘清理**: Whisper缓存释放2.5GB (large-v3-turbo/medium/base/tiny→只保留small)

### 2026-07-22 系统检查修复与瘦身

- **3个Cron timeout优化**: Hot-Topic-Finder(600s→900s)、Math-自动学习(120s→300s)、GitHub-Trending(180s→300s)，均加 sense-6.7 fallback
- **空目录清理**: 245个空目录全部删除（719→0）
- **磁盘瘦身合计**: 释放 ~2.5GB（Pixelle-Video 545MB + MoneyPrinterTurbo 1.58GB + Temp/缓存 253MB + 废弃脚本清理）
- **核心脚本精简**: scripts/ 从208个→73个（精简65%），skills/ 从54个→39个（精简28%）
- **安全修复**: ai_retry.py 硬编码API Key → 改为从 openclaw.json 读取
- **备份目录清理**: 保留 backup/sessions/ 和 backup/weekly/，清理废弃文件
- **PPT模板**: 从2套→10套（v2.3, 81%符合度）

### 2026-07-22 系统维护 Auto-Stagger 修复

- **问题**: system_maintenance.py 调用 auto_stagger.py 但文件不存在 → 退出码1
- **根因**: stale reference 陷阱
- **修复**: 将 run_auto_stagger() 调用改为 SKIP
- **验证**: 手动执行返回 3/3 OK，退出码0

### 2026-07-24 地图热点子系统 HyperFrames 集成 (v13)

- **核心改造**: 引入HyperFrames (HTML+GSAP) 替代原有FFmpeg drawtext视频合成方案
- **新文件**: `scripts/hyperframes_template.py` — JSON配置→自动生成HyperFrames HTML
- **新文件**: `scripts/config/city_shenzhen.json` — 深圳9区数据配置文件
- **新配置**: `config/map_style_config.json` 新增"抖音深色"样式
- **修改文件**: `scripts/pipeline.py` — 新增 `--hyperframes` 参数切换渲染引擎
- **修改文件**: `scripts/modules/map_drawer.py` — 修复全景图重复罗湖区bug（highlight_name=None）
- **修复bug**: 全景图高亮第一个区导致罗湖区重复显示、福田区被跳过
- **修复bug**: 音频时长不匹配（自动检测音频时长，动态分配各区时间）
- **修复bug**: 深色背景效果差（改为蓝灰背景+蓝色主调 #3b82f6）
- **v13产出**: 9.9MB, 52.4s, 动画含放大镜+柱状图闪烁+数据项逐项弹出
- **调用方式**: `python pipeline.py shenzhen --hyperframes`
- **模板生成**: `python hyperframes_template.py shenzhen --render`
- **同步**: TOOLS.md已更新, HEARTBEAT.md已更新

### 2026-07-24 方法论铁律执行检查

- **教训**: 今天多次卡在循环执行失败命令，没有及时意识到卡住
- **改进**: 执行任务前先跑方法论检查，超过30分钟不出成品立即切换方案
- **验证**: 已完成

- **AGENTS.md**：工作规则新增「🧩 第一性原理铁律」，四步拆解法（砸碎表象→倒空烂苹果→重拼乐高→找裂缝）+ 5个触发时机
- **SOUL.md**：核心原则「第一性原理」从一句话展开为可执行的四步拆解法 + 底线原则

## Promoted From Short-Term Memory (2026-07-17)

<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:10:13 -->
- 最终产出: | 项目 | 值 | |------|-----| | 文件 | L4-共享/videos/EP143_周期问题_final.mp4 | | 总时长 | 50.97s（含CTA结尾4.7s） | [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:10-13]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:14:17 -->
- 最终产出: | 净时长 | 46.27s（偏差-3.7s ✅） | | 文件大小 | 1.6MB | | atempo | 1.145x ✅ | | TTS | 198字，44.52s | [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:14-17]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:20:22 -->
- Method场景修复过程（5轮，效率极低）: v1: self.wait(14.0)空转14秒 → 重写为3步widget展示; v2: 循环动画+wait过多，28s → 简化为3步widget不加循环; v3-v5: wait缩放震荡（11s→28s→18s） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:20-22]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:25:27 -->
- 核心教训: **ep_duration_checker --fix 不可盲信**：它只统计静态代码中的wait，无法预测Manim渲染时的实际run_time; **复杂场景wait必须手动算**：非wait动画时长≈12s，目标20s，直接加8s wait。不要每次只调0.5s试; **改完脚本先跑预检再看差距**：差距>3s就一次性调够，不要反复微调 [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:25-27]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:30:31 -->
- 自动化系统bug: `auto_learn_trigger.py` Supermemory写入失败：`name 'error_counts' is not defined`; **已修复**：`error_counts` → `error_counter`（L485） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:30-31]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:38:41 -->
- 新增3个通用widget组件: | 组件 | 功能 | |------|------| | widget_pie_chart | 通用饼图（分数/概率/百分数可视化） | | widget_calendar_grid | 通用日历网格（星期计算可视化） | [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:38-41]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:42:42 -->
- 新增3个通用widget组件: | widget_number_blocks | 通用数字方块阵（数列/周期/页码可视化） | [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:42-42]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:45:48 -->
- 改造14个图形化combo（18/18 = 100%）: 饼图组：combo_fraction_ops, combo_probability, combo_percentage 条形图组：combo_discount_calc, combo_ratio 分组图组：combo_pigeonhole, combo_cow_grass 日历组：combo_calendar_weekday [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:45-48]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:49:51 -->
- 改造14个图形化combo（18/18 = 100%）: 方块组：combo_period_problem, combo_page_digit_count, combo_arithmetic_sequence 线段图组：combo_speed_time_dist, combo_midterm_method 表格组：combo_logic_reasoning [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:49-51]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:6:7 -->
- 题目: 今天是星期二，100天后是星期几？ 方法：余数法（周期7天，100÷7=14余2 → 周四） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:6-7]

## Promoted From Short-Term Memory (2026-07-22)

<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:15:15 -->
- Pixelle-Video 部署与排错（15:14~20:06）: **教训：没有先跑方法论检查，直接冲进执行模式** [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:15-15]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:16:19 -->
- Pixelle-Video 部署与排错（15:14~20:06）: 尝试部署 Pixelle-Video（开源视频生成工具）; Streamlit Web UI 被杀软 SIGKILL → 尝试修config/源码/路径/env 共5次才放弃; ComfyUI 需要本地显卡（940MX 2GB不够）; RunningHub 云端需要 API Key [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:16-19]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:20:20 -->
- Pixelle-Video 部署与排错（15:14~20:06）: 最终方案：PIL+ffmpeg 直接合成（不需要 Pixelle-Video） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:20-20]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:22:22 -->
- Pixelle-Video 部署与排错（15:14~20:06）: **成品**：`workspace/Pixelle-Video/output/final_video/final_video.mp4` [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:22-22]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:23:24 -->
- Pixelle-Video 部署与排错（15:14~20:06）: 5段配音+字幕，21秒，1080x1920竖屏; 零LLM依赖（文案硬编码），零生图依赖（PIL字幕），零filter依赖（ffmpeg loop+audio） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:23-24]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:27:30 -->
- 方法论固化（21:05~21:31）: 新增 R011：所有系统（主系统+全部子系统）执行任务前必须先跑方法论检查; AGENTS.md 新增「方法论铁律」章节，放在「主动推动」前面; 所有子系统的 AGENTS.md 同步更新引用; 教训已写入 corrections.md [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:27-30]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:4:6 -->
- 系统巡检（14:11）: Gateway 运行 1h16m，Context 3%，无积压; Web-Hot 全网热点连续6次timeout（已修复：timeout 180→300s）; INV-持仓监控脚本名错误（holding_monitor.py→holding_alert.py，已修复） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:4-6]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:9:12 -->
- 微信视频号内容分析（14:41~15:12）: 视频1: 富迪电能「1兆瓦光伏成本及收益一次性讲透」（7月2日）; 视频2: 中泽能源「绿电强制消费令来了！」（7月16日）; 微信视频号无法直接获取视频流（纯前端渲染，无公开API）; 通过搜索结果推测逐字稿，两份均完成 [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:9-12]
<!-- openclaw-memory-promotion:memory:memory/2026-07-18.md:11:14 -->
- Pixelle-Video 修复 ✅: **问题**: 测试失败（7月17日），`frame_html.py` 依赖 Playwright Chromium 渲染 HTML 模板，但 Chromium 引擎未安装; **根因**: `Executable doesn't exist at ...\ms-playwright\chromium_headless_shell-1208\...`; **修复**: 编程子Agent执行 `playwright install chromium`，下载 Chrome 145.0.7632.6 (chromium v1208, 281MB); **验证**: 完整跑通 LLM→Edge TTS→Playwright HTML渲染→FFmpeg合成，10.6s 视频成功输出 [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-18.md:11-14]
<!-- openclaw-memory-promotion:memory:memory/2026-07-18.md:15:18 -->

---

## 重庆主城区范围（2026-08-28 主人明确定义）

**重庆主城区 = 9个区域：**
1. 渝中区
2. 两江新区（含江北、渝北）
3. 南岸区
4. 九龙坡区
5. 沙坪坝区
6. 北碚区
7. 大渡口区
8. 巴南区
9. 重庆高新区

⚠️ **璧山区不属于主城区**，后续所有区域相关任务必须严格按此范围执行。
⚠️ 所有区域相关任务都以这个定义为准。

### 高德地图adcode（2026-08-28 新增）
- 渝中区500103、大渡口区500104、江北区500105
- 沙坪坝区500106、九龙坡区500107、南岸区500108
- 北碚区500109、渝北区500112、巴南区500113
- 高新区：无独立adcode，需周边搜索

_最后更新：2026-09-06_
- Pixelle-Video 修复 ✅: **Pixelle-Video 当前能力**:; LLM (DeepSeek) ✅; Edge TTS ✅; Playwright HTML 渲染 ✅（刚修复） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-18.md:15-18]

### agency-agents 完整安装（2026-09-06 新增）

**仓库**: `workspace/agency-agents/`（GitHub: msitarzewski/agency-agents）
**已安装**: 273 个 agent，格式 OpenClaw (SOUL.md + AGENTS.md + IDENTITY.md)
**安装位置**: `workspace/agents/<agent-slug>/`

**按部门统计**:
| 部门 | 数量 |
|------|------|
| engineering | 59 |
| specialized | 58 |
| marketing | 36 |
| game-development | 21 |
| gis | 13 |
| security | 12 |
| design | 10 |
| sales | 9 |
| testing | 9 |
| paid-media | 7 |
| project-management | 7 |
| academic | 6 |
| spatial-computing | 6 |
| support | 6 |
| finance | 5 |
| product | 5 |
| healthcare | 3 |
| research | 1 |

**百都搭档适配 agent** (双源验证通过，详见 `shared-knowledge/百都搭档-agency-agents适配报告.md`):
P0核心(11): outbound-strategist, deal-strategist, sales-engineer, pipeline-analyst, ppc-campaign-strategist, search-query-analyst, baidu-seo-specialist, government-digital-presales-consultant, proposal-strategist, finance-tracker, wechat-mini-program-developer
P1推荐(8): sales-account-strategist, sales-coach, sales-discovery-coach, sales-offer-lead-gen-strategist, paid-media-auditor, ad-creative-strategist, paid-media-tracking-specialist, analytics-reporter
P2可选: douyin-strategist, tiktok-strategist, growth-hacker, xiaohongshu-specialist, content-creator 等

**自媒体相关 agent**:
douyin-strategist, tiktok-strategist, content-creator, growth-hacker, xiaohongshu-specialist, bilibili-content-strategist, weibo-strategist, zhihu-strategist, kuaishou-strategist

**小说相关 agent**:
narrative-designer, book-co-author, visual-storyteller

**调用方式**: 通过 sessions_spawn 或 sessions_send 指定 agentId 即可激活对应 agent
