# Skills 索引表

> 自动生成: 2026-04-19 10:27
> 共 96 个有效 Skill | 0 个无效

---

## ✍️ 小说创作 (4个)

### ⚡ novel-generator
> 根据用户提供的内容方向自动生成提示词并创作爽文小说。适用场景：(1) 用户提供小说方向/题材/关键词，(2) 需要生成章节连贯的长篇爽文，(3) 需要维护角色、地点、情节的连续性，(4) 需要为关键情节生成图解，(5) 需要记录生成失败场景
**功能**: generator: description: "根据用户提供的内容方向自动生成提示词并创作爽文小说。适用场景：(1) 用户提供小说方向/题材/关键词，(2) 需要生成章节连贯的长篇 | writing: tags: "novel, fiction, creative-writing, chinese, 爽文, 小说生成" | # 爽文小说生成器: 根据用户提供的内容方向，自动完善提示词并生成章节制爽文小说。通过 `.learnings/` 记忆系统维护故事连续性，确保角色、地点、情节前后一致。 | ## 第一步：提示词生成与完善: 用户只需提供一个方向，代理自动补全为完整的创作提示词。
**触发**: user asks to write a novel, generate fiction, create stories, or mentions 爽文/小说/写作。" | ：(1) 用户提供小说方向/题材/关键词，(2) 需要生成章节连贯的长篇爽文，(3) 需要维护角色、地点、情节的连续性，(4) 需要为关键情节生成图解，(5) 需要记录生成失败场景以优化后续创作。支持都市、修仙、玄幻、重生、系统流等多种题材

### ⚡ novel-writing-assistant
> **技能类型**：创作指导、结构化写作辅助
**功能**: 小说创作助手: ## 🎯 技能概述 | "写小说"、"长篇小说"、"小说创作": "小说大纲"、"人物设定"、"世界观构建" | "写作指导"、"小说写作助手": "我需要写一本小说"、"帮我写小说" | "创作灵感"、"小说构思"、"写作规划": "玄幻小说"、"都市小说"、"仙侠小说"（各类题材）

### 📖 story-cog
> AI creative writing and storytelling powered by CellCog. Write novels, short stories, screenplays, fan fiction, poetry. 
**功能**: Flash Fiction: "Write a 500-word horror story that ends with a twist" | Short Stories: "Create a 3,000-word sci-fi story about first contact" | Micro Fiction: "Write a complete story in exactly 100 words" | Anthology Pieces: "Create a short story for a cyberpunk anthology"

### ⚡ webnovel-writer
> 长篇网文辅助创作系统，基于 Claude，支持 200 万字连载，解决 AI 遗忘和幻觉问题
**功能**: memory_limit: 记忆限制（默认：200 万字） | style_learning: 风格学习（默认：启用） | auto_review: 自动审核（默认：启用） | consistency_check: 一致性检查（默认：启用）


## 🎬 视频创作 (17个)

### ⚡ acedatacloud-seedance-video
> Generate AI dance and motion videos with Seedance (ByteDance) via AceDataCloud API. Use when creating videos from text p
**功能**: video: description: Generate AI dance and motion videos with Seedance (ByteDance) via A | seedance for: tool-use. | # Seedance Video Generation: Generate AI dance and motion videos through AceDataCloud's Seedance (ByteDance) | token: here"
**触发**: creating videos from text prompts or animating images into motion videos. Supports multiple models with configurable res

### ⚡ ai-video-script
> AI视频脚本生成器。根据用户输入的主题/关键词，生成完整的视频脚本，包含分镜描述、画面提示词、配音文案。适用于短视频创作者、AI视频制作者、内容营销人员。触发词：视频脚本、分镜、AI视频、短视频文案、视频策划。
**功能**: video: script | # AI 视频脚本生成器: 快速生成 AI 视频脚本的工具，包含分镜、提示词、配音文案。 | 风格定位: 目标受众 | 画面描述: 镜头运动
**触发**: ：视频脚本、分镜、AI视频、短视频文案、视频策划。

### ⚡ bilibili-transcript
> Transcribe Bilibili videos to text with high accuracy using Whisper medium model. Use when the user provides a Bilibili 
**功能**: GPU: NVIDIA RTX 4070 Super (12GB VRAM) - ✅ Perfect for medium model | WSL Memory: 16GB (configured) | WSL CPU: 6 cores (configured) | WSL Chromium: (recommended) - Log in to Bilibili in WSL
**触发**: the user provides a Bilibili video URL (BVxxxxx) and wants to: (1) Extract the complete audio content as text with high 

### ⚡ content-writer-pro
> 专业内容写作 Agent，支持文章、文案、脚本创作
**功能**: # 专业内容写作 Agent: ## 功能模块 | 文章创作: 2. **copy** - 文案写作 | 脚本创作: 4. **edit** - 编辑优化 | writer: pro --article "科技文章标题"

### 📹 douyin-video
> 抖音视频下载工具 - 解析抖音链接，下载视频并发送
**功能**: 自动清理: 下载新视频时，会自动删除上一个视频 | 只保留一个视频: 始终使用固定文件名 `douyin_last.mp4` | 节省空间: 不会累积多个视频文件 | video: description: 抖音视频下载工具 - 解析抖音链接，下载视频并发送

### ⚡ douyin-video-publish
> 抖音视频发布。使用浏览器自动化在抖音创作者平台发布视频。当用户说"发布视频到抖音"、"发抖音"时使用此技能。
**功能**: video: publish | # 抖音视频发布: ## 使用场景 | 浏览器：OpenClaw Chrome扩展 (profile=chrome): 账号：需要登录抖音创作者账号 | 点击「上传视频」按钮: 选择本地视频文件（MP4格式最佳）

### ⚡ ffmpeg-video-editor
> Generate FFmpeg commands from natural language video editing requests - cut, trim, convert, compress, change aspect rati
**功能**: # FFmpeg Video Editor: You are a video editing assistant that translates natural language requests into | y` (overwrite) and `: hide_banner` for cleaner output | ## Command Reference: ### Cut/Trim Video | hide_banner: i "INPUT" -ss START_TIME -to END_TIME -c copy "OUTPUT"

### ⚡ image-generate
> 使用内置 image_generate.py 脚本生成图片, 准备清晰具体的 `prompt`。
**功能**: generate: description: 使用内置 image_generate.py 脚本生成图片, 准备清晰具体的 `prompt`。 | # Image Generate: ## 适用场景 | 输出生成的图片 URL。: 若调用失败，将打印错误信息。
**触发**: 当需要根据文本描述生成图片时，使用该技能调用 `image_generate` 函数。

### ⚡ jianying-editor-skill
> 剪映 (JianYing) AI自动化剪辑的高级封装 API (JyWrapper)。提供开箱即用的 Python 接口，支持录屏、素材导入、字幕生成、Web 动效合成及项目导出。
**功能**: Mandatory: initialization code for all scripts. | Advanced: Adding Keyframe animations. | New: Screen Recording & Smart Zoom automation. | Asset Search: Find filters, transitions, and animations by Chinese/English name:
**触发**: skill when the user wants to automate video editing, generate drafts, or manipulate media assets in JianYing Pro.

### ⚡ novel-to-script
> 将小说/网文内容转换为可拍、可剪、可分镜、可配音的短剧剧本格式。适用场景：小说改编短剧、故事可视化、角色分镜对白全套生成。
**功能**: script: description: "将小说/网文内容转换为可拍、可剪、可分镜、可配音的短剧剧本格式。适用场景：小说改编短剧、故事可视化、角色分镜对白全套生成。" | conversion: tags: [novel, script, short-drama, story-conversion] | # 小说转短剧剧本: ## 适用场景 | 已有小说章节，需要改编为短视频/短剧脚本: 网文片段需要可视化
**触发**: ：小说改编短剧、故事可视化、角色分镜对白全套生成。" | - 已有小说章节，需要改编为短视频/短剧脚本

### ⚡ short-video-script-generator-intl
> AI Short Video Script Generator, support TikTok/YouTube Shorts/Instagram Reels, auto generate hook, shots, voiceover, su
**功能**: video: script-generator-pro | # AI Short Video Script Generator Pro: ## Features | platform: support**: TikTok, YouTube Shorts, Instagram Reels, Facebook Reels, Snapchat | seconds hook to grab attention: Shot list with time codes and scene descriptions

### ⚡ video-frames
> Extract frames or short clips from videos using ffmpeg.
**功能**: frames: description: Extract frames or short clips from videos using ffmpeg. | # Video Frames (ffmpeg): Extract a single frame from a video, or create quick thumbnails for inspection. | time 00: 00:10 --out /tmp/frame-10s.jpg | Prefer `: time` for “what is happening around here?”.

### ⚡ video-producer
> 短视频一键生成技能 v2.2。调用video-director进行画面规划，然后生成AI素材、TTS配音、视频渲染，输出完整MP4。
**功能**: producer: description: 短视频一键生成技能 v2.2。调用video-director进行画面规划，然后生成AI素材、TTS配音、视频渲染，输出完整MP4。 | generation, automation, storyboard]: # Video Producer - 短视频一键生成技能 v2.2 | 调用video: director生成分镜表（含素材路径） | 根据文案关键词智能匹配素材: 3. **TTS配音** - 每场景独立配音

### ⚡ video-script-generator
> 镜头描述：特写/中景/全景，动作，表情
**功能**: script: generator | 解决、反转剧情、before: after。触发词：视频脚本、短视频文案、分镜、storyboard、video script。 | # 短视频脚本+分镜生成: ## 工作流程 | | 模板：pain: solution / before-after / plot-twist |
**触发**: ：视频脚本、短视频文案、分镜、storyboard、video script。

### ⚡ video-transcript-downloader
> Download videos, audio, subtitles, and clean paragraph-style transcripts from YouTube and any other yt-dlp supported sit
**功能**: transcript: downloader | dlp/ffmpeg and formats/playlists.: # Video Transcript Downloader | Print a transcript as a clean paragraph: (timestamps optional). | Download video/audio/subtitles.: Transcript behavior:
**触发**: asked to “download this video”, “save this clip”, “rip audio”, “get subtitles”, “get transcript”, or to troubleshoot yt-

### ⚡ youtube-transcript
> Fetch and summarize YouTube video transcripts. Use when asked to summarize, transcribe, or extract content from YouTube
**功能**: transcript: description: Fetch and summarize YouTube video transcripts. Use when asked to su | # YouTube Transcript: Fetch transcripts from YouTube videos and optionally summarize them. | Python dependencies installation: WireGuard VPN configuration (required for cloud VPS) | Troubleshooting common errors: Alternative proxy options
**触发**: asked to summarize, transcribe, or extract content from YouTube videos. Handles transcript fetching via residential IP p

### ⚡ ytdlp-transcript
> Fetch and summarize transcripts from any YouTube video. Paste a URL and your agent reads the video for you — summarize,
**功能**: transcript: description: Fetch and summarize transcripts from any YouTube video. Paste a URL | # youtube: transcript | "Get the transcript of [YouTube URL]": "Summarize this video: [YouTube URL]" | dlp` to download auto: generated or manual captions from YouTube.


## 💹 投资分析 (2个)

### ⚡ investment-portfolio
> Track investments with buy/sell records, allocation charts, and P/L analysis. Use when managing a stock or crypto portfo
**功能**: version: "4.0.0" | portfolio: description: "Track investments with buy/sell records, allocation charts, and P/ | skills: # investment-portfolio | in ticker: to-sector mapping.
**触发**: managing a stock or crypto portfolio, rebalancing, or comparing assets."

### ⚡ j-investment-checklist
> 投资决策清单，每次买入/卖出前必须走一遍，确保决策质量
**功能**: # Investment Checklist | 投资决策清单: **每次买入、卖出前，必须走一遍这个清单。** | ## 🟢 买入前清单: ### A. 能力圈确认 | ## 🟠 持有期间检查: ### 每季度 | [ ] 基本面有变化吗？: [ ] 当初买入的理由还成立吗？


## 📄 办公文档 (15个)

### 🔍 baidu-hot-monitor
> 百度热榜监控 | Baidu Hot Topics Monitor. 获取百度热搜榜、搜索趋势、关键词热度 | Get Baidu trending searches, trends, keyword popularity. 触发词：百度、
**功能**: 实时热搜 / Real-time Hot: 获取当前百度热搜榜 Top 30 | Get current Baidu hot search Top 30 | 搜索指数 / Search Index: 显示每条热搜的搜索量 | Show search volume for each hot topic | 分类标签 / Category Tags: 娱乐、科技、社会、体育等 | Entertainment, Tech, Society, Sports, etc. | 上升最快 / Rising Fastest: 搜索量上升最快的关键词 | Keywords with fastest rising search volume
**触发**: ：百度、热搜、baidu."

### 📄 docx-cn
> Word 文档处理 | Word Document Processing. 创建、读取、编辑 Word 文档 | Create, read, edit Word documents. 支持 .docx 格式、格式化、表格、图片 | Supp
**功能**: Always use `WidthType.DXA`: — never `WidthType.PERCENTAGE` (incompatible with Google Docs) | Set page size explicitly: docx-js defaults to A4; use US Letter (12240 x 15840 DXA) for US documents | Landscape: pass portrait dimensions: docx-js swaps width/height internally; pass short edge as `width`, long edge as | Never use `\n`: use separate Paragraph elements
**触发**: ：Word、文档、docx."

### ⚡ docx-to-md
> 将Word文档(.docx)转换为Markdown格式并提取图片。使用此技能当用户需要:(1)将Word文档转换为Markdown格式,(2)从Word文档中提取图片,(3)同时完成文档格式转换和图片提取任务。
**功能**: # docx: to-md | `input_file`: Word文档路径(.docx) | `output_dir`: 输出目录(可选,默认创建同名_output文件夹) | 内容 |: | 有序列表 | 1. 内容 |

### ⚡ excel-xlsx
> Create, inspect, and edit Microsoft Excel workbooks and XLSX files with reliable formulas, dates, types, formatting, rec
**功能**: ## When to Use: Use when the main artifact is a Microsoft Excel workbook or spreadsheet file, es | platform behavior matter.: ## Core Rules | For model: style work, document non-obvious hardcodes, assumptions, or source inputs in com | Mixed text: number columns need explicit handling on read and on write.
**触发**: (1) the task is about Excel, `.xlsx`, `.xlsm`, `.xls`, `.csv`, or `.tsv`; (2) formulas, formatting, workbook structure,  | the main artifact is a Microsoft Excel workbook or spreadsheet file, especially when formulas, dates, formatting, merged

### ⚡ jianying
> 注册“剪映”技能；用于创作工具公开页面、模板能力、功能说明与帮助文档整理。
**功能**: 面向公开官网、模板页、功能页、帮助中心与定价页的信息整理: 不提供账号代操作、素材版权绕过、付费资源下载或接口调用能力 | 主页：https: //www.capcut.cn/ | 功能与模板：官网中的模板中心、创作能力、素材或编辑器说明入口: 帮助与定价：帮助中心、版权说明、套餐页与更新说明入口 | 模板类型、编辑能力、导出规格与协作能力整理: 素材、版权、商用说明与帮助信息汇总

### ⚡ keyword-research
> Find high-value SEO keywords: search volume, difficulty, intent classification, topic clusters. 关键词研究/内容选题
**功能**: Reads: user goals, target market inputs, available tool data, and prior strategy from [ | Writes: a user-facing research deliverable plus a reusable summary that can be stored un | Promotes: durable keyword priorities, competitor facts, entity candidates, and strategic d | Next handoff: use the `Next Best Skill` below when the findings are ready to drive action.
**触发**: when the conversation involves any of these situations — even if the user does not use SEO terminology: | whenever the task needs reusable market intelligence that should influence strategy, not just an ad hoc answer.

### ⚡ minimax-docx
> Enterprise-grade Word document generation. Creates validated .docx files with professional formatting, visual hierarchy,
**功能**: <role>: You are a document composition specialist. Your deliverables are complete, valid | Python 3, .NET 9.0 SDK (required): LibreOffice, Pandoc, matplotlib, Playwright, Pillow (optional) | workflow.md` |: | **Template-Apply** | User provides .docx/.doc file | `guides/template-apply-wo | [ ] `python3 <skill: path>/docx_engine.py audit <output.docx>` passes

### ⚡ office-document-specialist-suite
> Advanced suite for creating, editing, and analyzing Microsoft Office documents (Word, Excel, PowerPoint). Provides speci
**功能**: Word (.docx): Create and edit professional reports, manage styles, and insert tables/images. | Excel (.xlsx): Data analysis, automated spreadsheet generation, and complex formatting. | PowerPoint (.pptx): Automated slide deck creation from structured data. | document: specialist-suite

### 📄 pdf-smart-tool-cn
> PDF智能处理工具 v2.1 | PDF Smart Tool. 支持PDF转换、OCR识别、合并拆分、数字签名、批量处理、水印添加、加密解密。触发词：PDF、转换、识别。
**功能**: 多语言识别: 支持中英日韩等50+语言 | 表格识别: 自动识别表格结构 | 手写识别: 识别手写文字 | 版式还原: 保持原文档排版
**触发**: ：PDF、转换、识别。"

### ⚡ pdf-toolkit-pro
> PDF批量处理技能包 - 一键合并、分割、压缩、转换PDF。适合办公人员、文档处理、自动化工作流。
**功能**: 一键合并、分割、压缩、转换PDF。适合办公人员、文档处理、自动化工作流。: version: 1.0.0 | Company: tags: [pdf, merge, split, compress, convert, automation, 文档处理, 批量操作] | # PDF Toolkit Pro: PDF批量处理技能包 | 合并PDF：多个PDF要逐个打开？→ 一键合并成1个: 分割PDF：只要某几页？→ 快速提取指定页面

### ⚡ powerpoint-pptx
> Create, inspect, and edit Microsoft PowerPoint presentations and PPTX decks with reliable layouts, templates, placeholde
**功能**: ## When to Use: Use when the main artifact is a Microsoft PowerPoint presentation or `.pptx` dec | Text extraction plus thumbnail: style visual inspection is safer than editing from shape assumptions alone. | For template: driven work, inventory the deck before replacing content. | Do not force two ideas into a three: column slide or cram dense text under a chart.
**触发**: (1) the task is about PowerPoint or `.pptx`; (2) layouts, placeholders, notes, charts, comments, or template fidelity ma | the main artifact is a Microsoft PowerPoint presentation or `.pptx` deck, especially when layouts, templates, placeholde

### ⚡ pptx-generator
> 专业PPT生成器。Use when user wants to create editable PowerPoint presentations with professional layouts, multiple styles, and
**功能**: generator: description: 专业PPT生成器。Use when user wants to create editable PowerPoint presenta | pptx pillow": # PPT Generator | ## Python代码实现: ```python | ## Notes: 生成标准.pptx格式，可编辑
**触发**: user wants to create editable PowerPoint presentations with professional layouts, multiple styles, and beautiful designs

### ⚡ read-word
> Read Microsoft Word documents (.docx and .doc) with Chinese support. Extract text, search keywords, and save as UTF-8 te
**功能**: Read .docx files: Word 2007 and later format | Read .doc files: Word 97-2003 format via OLE parsing | Auto format detection: Automatically identifies file type | Full Chinese support: Handles Chinese encoding correctly

### ⚡ summarize-pro
> When user asks to summarize text, articles, documents, meetings, emails, YouTube transcripts, books, PDFs, reports, conv
**功能**: "summarize": or **"summary"** — summarize any text | "tldr": or **"tl;dr"** — quick summary | "eli5": — explain like I'm 5 | "key takeaways": — extract main points

### ⚡ xcrawl-search
> Use this skill for XCrawl search tasks, including keyword search request design, location and language controls, result
**功能**: search: description: Use this skill for XCrawl search tasks, including keyword search re | up crawl or scrape planning.: allowed-tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep | search","homepage": "https://www.xcrawl.com/","requires":{"localFiles":["~/.xcrawl/config.json"],"an | # XCrawl Search: ## Overview
**触发**: skill for XCrawl search tasks, including keyword search request design, location and language controls, result analysis,


## 📦 其他工具 (10个)

### ⚡ data-analysis-litiao
> Turn raw data into decisions with statistical rigor, proper methodology, and awareness of analytical pitfalls.
**功能**: analysis: litiao | ## When to Load: User asks about: analyzing data, finding patterns, understanding metrics, testin | [ ] Multiple comparisons? (20 tests = 1: "significant" by chance) | [ ] Uncertainty quantified? ("12: 18% lift" not just "15% lift")

### ⚡ fast-browser-use
> name: fast-browser-use
**功能**: vision_map: Returns a screenshot overlay with numbered bounding boxes for all interactive el | snapshot: Capture the raw HTML snapshot (YAML/Markdown optimized for AI). | screenshot: Capture a visual image of the page. | extract: Get structured data from the DOM.
**触发**: to understand site architecture before scraping, map navigation flows, or audit SEO structure.

### ⚡ minimax-xlsx
> MiniMax spreadsheet production system. Engage for any task that involves tabular data, numeric analysis, or spreadsheet 
**功能**: When to run: ALWAYS after `wb.save()` and BEFORE `recalc`, whenever the file has formulas | When to skip: Only if the file has zero formulas (pure static data) | Banned workflow patterns:: Building all sheets first, then running checks once at the end | <brief>: You are a rigorous quantitative analyst who converts raw data into publication-r

### ⚡ obsidian-notesmd-cli
> Work with Obsidian vaults (plain Markdown notes) and automate via notesmd-cli.
**功能**: Note:: Works directly on disk (headless supported); Obsidian does *not* need to be runn | cli"]},"install": [{"id":"brew","kind":"brew","formula":"yakitrak/yakitrak/notesmd-cli","bins":["n | cli"],"label": "Install notesmd-cli (brew)"}]}} | # Obsidian: Obsidian vault = a normal folder on disk.

### ⚡ personal-productivity
> 个人效率与时间管理顾问。帮助用户更好地管理时间、任务和能量，提升工作效率。当用户询问如何提高效率、时间管理、任务规划、专注力、拖延症等问题时触发。
**功能**: productivity: description: 个人效率与时间管理顾问。帮助用户更好地管理时间、任务和能量，提升工作效率。当用户询问如何提高效率、时间管理、任务规划、专注力、拖延症等 | # Personal Productivity: 个人效率与时间管理顾问 | 🔍 诊断效率问题: 📋 建立任务管理系统 | ⏰ 设计时间块计划: ⚡ 优化能量使用
**触发**: | 场景 | 说明 | | ：** 多角色兼顾（全职工作+副业+家庭）、日程碎片化、总是被动响应

### ⚡ planning-with-files
> Implements Manus-style file-based planning to organize and track progress on complex tasks. Creates task_plan.md, findin
**功能**: Templates: are in `${CLAUDE_PLUGIN_ROOT}/templates/` | Your planning files: go in **your project directory** | Manus Principles:: See [reference.md](reference.md) | Real Examples:: See [examples.md](examples.md)
**触发**: asked to plan out, break down, or organize a multi-step project, research task, or any work requiring >5 tool calls. Sup

### ⚡ receiving-code-review
> Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or techni
**功能**: Trusted: implement after understanding | Still ask: if scope unclear | No performative agreement: **Skip to action** or technical acknowledgment | review: description: Use when receiving code review feedback, before implementing sugges
**触发**: receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically que

### ⚡ todo-tracker
> Persistent TODO scratch pad for tracking tasks across sessions. Use when user says "add to TODO", "what's on the TODO",
**功能**: tracker: description: Persistent TODO scratch pad for tracking tasks across sessions. Use | # TODO Tracker: Maintain a persistent TODO.md scratch pad in the workspace. | bot/TODO.md`): ## Commands | tracker/scripts/todo.sh done "<item: pattern>"
**触发**: user says "add to TODO", "what's on the TODO", "mark X done", "show TODO list", "remove from TODO", or asks about pendin

### ⚡ ui-ux-pro-max
> UI/UX design intelligence and implementation guidance for building polished interfaces. Use when the user asks for UI de
**功能**: UI concept + layout: Provide a clear visual direction, grid, typography, color system, key screens/se | UX flow: Map the user journey, critical paths, error/empty/loading states, edge cases. | Design system: Tokens (color/typography/spacing/radius/shadow), component rules, accessibility | Implementation plan: Exact file-level edits, component breakdown, and acceptance criteria.
**触发**: the user asks for UI design, UX flows, information architecture, visual style direction, design systems/tokens, componen

### ⚡ vercel-deployment
> Deploy and manage Vercel projects, including linking repositories, env vars, and domains.
**功能**: deployment: version: 1.0.0 | # Vercel — Deploy and Manage Projects: ## Set Up a New Project | vercel: project && npx vercel domains ls | NEVER use `echo`: — it adds a trailing `\n`:


## 📱 社媒运营 (9个)

### ⚡ hot-topic-finder
> 发现并追踪热点话题，自动去重，支持多平台热榜监控。Use when: (1) 寻找创作灵感或热点话题，(2) 检查话题是否已使用过，(3) 监控微博/知乎/抖音等平台热榜，(4) 需要话题推荐时。NOT for: 实时新闻追踪、舆情危机处理
**功能**: topic: finder | # Hot Topic Finder: 自动发现热点话题，智能去重，追踪使用历史。 | "帮我找个热点话题写文章": "今天有什么热门事件" | "这个话题我之前写过吗": "推荐几个新鲜话题"
**触发**: (1) 寻找创作灵感或热点话题，(2) 检查话题是否已使用过，(3) 监控微博/知乎/抖音等平台热榜，(4) 需要话题推荐时。NOT for: 实时新闻追踪、舆情危机处理。"

### ⚡ opencli-tool
> 使用 OpenCLI 工具从各种网站和桌面应用获取数据、下载媒体内容、控制外部 CLI 工具。支持 Bilibili、知乎、小红书、Twitter/X、Reddit、YouTube、Boss直聘、即刻、微博等 30+ 平台，以及 Curso
**功能**: 社交媒体: Twitter/X, Reddit, 微博, 即刻 | 视频平台: Bilibili, YouTube, 小红书 | 问答社区: 知乎, V2EX, StackOverflow, Linux-Do | 新闻资讯: BBC, Bloomberg, Reuters, HackerNews, Dev.to
**触发**: ：bilibili、知乎、小红书、twitter、reddit、youtube、热门、下载视频、平台数据、opencli、网站数据、社交媒体。

### ⚡ social-media-agent
> 自媒体内容创作 Agent，支持多平台内容生成和发布
**功能**: media: agent | media, content, writing, auto: publish] | # 自媒体 Agent: ## 功能模块 | 内容创作: 2. **schedule** - 发布调度

### ⚡ social-media-content
> Generate social media posts for LevelUpLove and PayLessTax brands
**功能**: media: content | # Social Media Content Generator Skill: ## Overview | carousel: 4-panel Instagram carousel | infographic: Single detailed infographic

### ⚡ social-media-content-calendar
> Generate structured social media content calendars with platform-specific posts, hashtags, and scheduling. Use when crea
**功能**: Brand voice: Professional, casual, witty, inspirational, educational | Target audience: Demographics, interests, pain points | Content pillars: (3-5 themes that all content maps to): | Competitor reference: What type of content works in this niche?
**触发**: creating social media plans, content calendars, or social media management deliverables for clients.

### 📱 social-media-publish
> 社交媒体浏览器自动化发布。支持微信公众号、百家号、小红书等平台。当用户说"发公众号"、"发百家号"、"发布到..."时使用此技能。
**功能**: media: publish | # 社交媒体浏览器自动化发布: ## 使用场景 | 发布图文消息到草稿箱: 支持标题、正文、封面图 | 自动格式化排版: ### 2. 百度百家号

### ⚡ social-media-scheduler
> Plan, draft, and organize social media content across platforms. Create content calendars, write platform-optimized post
**功能**: Twitter/X: Punchy, <280 chars, thread-friendly, hook-first | LinkedIn: Professional, storytelling, paragraph breaks, 1300 char sweet spot | Instagram: Visual-first caption, line breaks, 20-30 hashtags in comment | TikTok: Hook in first 2 seconds, trending format awareness

### ⚡ web-hot
> 获取微博、知乎、百度、抖音、今日头条、B站等主流中文平台的实时热搜榜单和热门话题。Use when users want to know trending topics, hot searches, or popular content o
**功能**: Solution: API might be updating, retry after a few seconds | topics: description: 获取微博、知乎、百度、抖音、今日头条、B站等主流中文平台的实时热搜榜单和热门话题。Use when users want to kno | trending: social-media | search: china
**触发**: users want to know trending topics, hot searches, or popular content on Chinese social media platforms. | skill when users:

### ⚡ weibo-hot-trend
> 获取微博热搜榜数据，返回热搜标题、热度值和跳转链接。当用户需要查看微博热搜、微博热点、微博热榜时使用此技能。支持自定义获取条数（默认50条）。
**功能**: trend: description: 获取微博热搜榜数据，返回热搜标题、热度值和跳转链接。当用户需要查看微博热搜、微博热点、微博热榜时使用此技能。支持自定义获取条数（默认5 | # 微博热搜榜: ## 获取热搜 | 访问频繁可能触发风控，建议间隔 ≥30 分钟: 热度单位为万，label_name 为标签（沸、新、热等）


## 🔊 音频处理 (1个)

### ⚡ openai-whisper
> Local speech-to-text with the Whisper CLI (no API key).
**功能**: whisper: description: Local speech-to-text with the Whisper CLI (no API key). | whisper","bins": ["whisper"],"label":"Install OpenAI Whisper (brew)"}]}} | # Whisper (CLI): Use `whisper` to transcribe audio locally. | `whisper /path/audio.mp3: model medium --output_format txt --output_dir .`


## 🔍 搜索热点 (21个)

### ⚡ admapix
> Ad intelligence & app analytics assistant. Search ad creatives, analyze apps, view rankings, track downloads/revenue, an
**功能**: NEVER fall back to manual analysis.: The framework WILL complete — just wait for it. | NEVER write your own polling loop.: Use the exact script above. | MUST: set `generate_page: true` in the API request — this generates an H5 page where u | # AdMapix Intelligence Assistant: **Get started:** Sign up and get your API key at https://www.admapix.com
**触发**: exact script, do NOT modify):**

### ⚡ agent-browser-clawdbot
> Headless browser automation CLI optimized for AI agents with accessibility tree snapshots and ref-based element selectio
**功能**: browser: description: Headless browser automation CLI optimized for AI agents with access | based element selection: metadata: {"clawdbot":{"emoji":"🌐","requires":{"commands":["agent-browser"]},"ho | labs/agent: browser"}} | # Agent Browser Skill: Fast browser automation using accessibility tree snapshots with refs for determi

### ⚡ amazon-competitor-analyzer
> Scrapes Amazon product data from ASINs using browseract.com automation API and performs surgical competitive analysis. C
**功能**: CSV: Structured data table | Markdown: Comprehensive report | JSON: Raw data with analysis | Invalid API Key: Check BROWSERACT_API_KEY environment variable

### ⚡ baidu-search
> Search the web using Baidu AI Search Engine (BDSE). Use for live information, documentation, or research topics.
**功能**: search: description: Search the web using Baidu AI Search Engine (BDSE). Use for live in | # Baidu Search: Search the web via Baidu AI Search API. | fetch.md](references/apikey: fetch.md) | search/scripts/search.py: '<JSON>'

### ⚡ clawdhub
> Use the ClawdHub CLI to search, install, update, and publish agent skills from clawdhub.com. Use when you need to fetch
**功能**: installed clawdhub CLI.: metadata: {"clawdbot":{"requires":{"bins":["clawdhub"]},"install":[{"id":"node", | # ClawdHub CLI: Install | skill: clawdhub install my-skill --version 1.2.3 | based match + upgrade): ```bash
**触发**: you need to fetch new skills on the fly, sync installed skills to latest or a specific version, or publish new/updated s

### ⚡ clawflows
> Search, install, and run multi-skill automations from clawflows.com. Combine multiple skills into powerful workflows wit
**功能**: Registry: https://clawflows.com | CLI on npm: https://www.npmjs.com/package/clawflows | GitHub: https://github.com/Cluka-399/clawflows-registry | # ClawFlows: Discover and run multi-skill automations that combine capabilities like database

### ⚡ crawlee-web-scraper
> Resilient web scraper with bot-detection evasion using the Crawlee library. Use when web_fetch is blocked by rate limits
**功能**: `crawlee_fetch.py`: — main scraper; accepts a single URL or a file of URLs; returns JSON | `crawlee_http.py`: — library helper; tries `requests` first, falls back to Crawlee on 403/429/503 | scraper: description: Resilient web scraper with bot-detection evasion using the Crawlee | # crawlee: web-scraper
**触发**: web_fetch is blocked by rate limits or bot detection. Supports single URLs, bulk file input, and automatic fallback from

### ⚡ desearch-web-search
> Search the web and get real-time SERP-style results with titles, URLs, and snippets. Use this for general web queries wh
**功能**: search: description: Search the web and get real-time SERP-style results with titles, UR | # Web Search By Desearch: Real-time web search returning structured SERP-style results with titles, links, | here'`: ## Usage | start` | Pagination offset (default: 0). Use to get the next page of results. |
**触发**: for general web queries when you need current links and information from across the internet.

### ⚡ find-skills-skill
> Search and discover OpenClaw skills from various sources. Use when: user wants to find available skills, search for spec
**功能**: skills: description: "Search and discover OpenClaw skills from various sources. Use when | # Find Skills Skill: Search and discover OpenClaw skills from various sources. | "Find skills for [task]": "Search for OpenClaw skills" | "What skills are available?": "Discover new skills"
**触发**: user wants to find available skills, search for specific functionality, or discover new skills to install." | skill when:**

### ⚡ frontend-design-3
> Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when building web comp
**功能**: Purpose: What problem does this interface solve? Who uses it? | Tone: Pick an extreme — brutally minimal, maximalist chaos, retro-futuristic, organic/ | Constraints: Technical requirements (framework, performance, accessibility) | Differentiation: What makes this UNFORGETTABLE? What's the one thing someone will remember?
**触发**: skill when building web components, pages, or applications. Generates creative, polished code that avoids generic AI aes

### ⚡ github-trending-daily
> 每天定时获取 GitHub Trending 热门项目并推送到钉钉群。
**功能**: 安全关键词: `AI 推送` | 推送时间: 默认每天早上 9 点（可自定义） | 消息格式: Markdown | trending: daily - 每日 GitHub Trending 推送

### ⚡ memos-search
> Use MemOS API for memory operations. Use when: (1) user asks to save/store/remember something to memory, (2) user asks t
**功能**: # MemOS: External Memory Service | 23.md'): print(r.json()['content']) | File path format: `{agent}/{filename}.md` | Add memory:: ```python
**触发**: (1) user asks to save/store/remember something to memory, (2) user asks to read/retrieve memory, (3) user wants to list/

### ⚡ multi-search-engine
> Multi search engine integration with 17 engines (8 CN + 9 Global). Supports advanced search operators, time filters, sit
**功能**: Baidu: `https://www.baidu.com/s?wd={keyword}` | Bing CN: `https://cn.bing.com/search?q={keyword}&ensearch=0` | Bing INT: `https://cn.bing.com/search?q={keyword}&ensearch=1` | 360: `https://www.so.com/s?q={keyword}`

### ⚡ openclaw-supermemory
> Long-term agent memory with atomic fact extraction, relational versioning, semantic search, and entity profiles. Extract
**功能**: Storage:: SQLite with WAL mode (concurrent reads, single writer) | Embeddings:: Local sentence-transformers (free, on-device) or API (OpenAI/Cohere/Voyage via l | Extraction:: LLM-based atomic fact extraction with relation detection (default: Haiku) | Entity system:: Join tables, aliases, auto-merged profiles across sources

### ⚡ pls-audit-website
> Perform full health check on websites, identifying technical friction points and user experience issues. Use when: (1) A
**功能**: website: description: Perform full health check on websites, identifying technical fricti | # Website Audit: Comprehensive website health check for performance, accessibility, security, and | command overview: curl -I https://example.com && \ | w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTo
**触发**: (1) Auditing website performance, (2) Checking for broken links, (3) Analyzing page structure, (4) Testing accessibility

### ⚡ pls-seo-audit
> Scan content and websites for SEO gaps, identify opportunities to outrank competitors. Use when: (1) Analyzing page SEO,
**功能**: Score:: X/100 | audit: description: Scan content and websites for SEO gaps, identify opportunities to o | # SEO Audit: Comprehensive SEO analysis for content and websites. | Page SEO: ```markdown
**触发**: (1) Analyzing page SEO, (2) Checking meta tags and structured data, (3) Reviewing content for keyword optimization, (4) 

### 🕷️ scrapling-official
> Scrape web pages using Scrapling with anti-bot bypass (like Cloudflare Turnstile), stealth headless browsing, spiders fr
**功能**: official: description: Scrape web pages using Scrapling with anti-bot bypass (like Cloudfl | bot protections; write Python code to: scrape/crawl; or write spiders. | python3: anyBins: | pip3: # Scrapling
**触发**: asked to scrape, crawl, or extract data from websites; web_fetch fails; the site has anti-bot protections; write Python 

### ⚡ security-scanner
> Automated security scanning and vulnerability detection for web applications, APIs, and infrastructure. Use when you nee
**功能**: scanner: description: Automated security scanning and vulnerability detection for web app | # Security Scanner: Automated security scanning toolkit for penetration testing and vulnerability as | oN scan.txt: TARGET | u TARGET: o results.txt
**触发**: you need to scan targets for vulnerabilities, check SSL certificates, find open ports, detect misconfigurations, or perf

### ⚡ smart-web-scraper
> Extract structured data from any web page. Supports CSS selectors, auto-detection of tables and lists, JSON/CSV output f
**功能**: scraper: description: Extract structured data from any web page. Supports CSS selectors, | # Smart Web Scraper: Extract structured data from web pages into clean JSON or CSV. | with beautifulsoup4: with lxml python scripts/scraper.py extract "https://example.com" | card": # Auto-detect and extract tables
**触发**: asked to scrape a website, extract data from a page, pull product info, gather contact details, or collect listings from

### 🎨 timeflow-web-design-guidelines
> Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit
**功能**: design: guidelines | pattern>: domain: design | skills/tree/main/teams/skills/web: design-guidelines | # Web Interface Guidelines: Review files for compliance with Web Interface Guidelines.
**触发**: asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices". 

### ⚡ xcrawl-crawl
> Use this skill for XCrawl crawl tasks, including bulk site crawling, crawler rule design, async status polling, and deli
**功能**: crawl: description: Use this skill for XCrawl crawl tasks, including bulk site crawling | tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep | crawl","homepage": "https://www.xcrawl.com/","requires":{"localFiles":["~/.xcrawl/config.json"],"an | # XCrawl Crawl: ## Overview
**触发**: skill for XCrawl crawl tasks, including bulk site crawling, crawler rule design, async status polling, and delivery of c


## 🖼️ 图像处理 (1个)

### ⚡ diagram-generator
> Generate and edit various types of diagrams (including draw.io, Mermaid, and Excalidraw). This tool supports common diag
**功能**: Global config: (`~/.claude.json`) for all projects, or | Project config: (`.claude.json`) for specific project | Solution: MCP server not configured. Follow installation steps above. | Diagram type: flowchart, sequence diagram, class diagram, ER diagram, mindmap, architecture di


## 🤖 系统工具 (16个)

### ⚡ agency-agents
> AI Agent 团队 - 61 个专业 Agent，8 大部门，完整的 AI 代理机构。支持单 Agent 使用和多 Agent 协作编排。
**功能**: 明确任务类型: → 选择对应专业 Agent | 复杂项目: → 使用编排器 | 需要多领域: → 使用部门协作 | agents: description: AI Agent 团队 - 61 个专业 Agent，8 大部门，完整的 AI 代理机构。支持单 Agent 使用和多 Agent 协

### ⚡ agency-coordinator
> Agent 协调器，协调多个 Agent 协同工作
**功能**: coordinator: description: Agent 协调器，协调多个 Agent 协同工作 | agent, workflow]: # Agent 协调器 | 多 Agent 协调: 2. **workflow** - 工作流管理 | 流程优化: 4. **monitor** - 执行监控

### ⚡ agent-memory-setup
> name: agent-memory-setup
**功能**: Backing up or exporting memory: — this skill sets up memory, it doesn't handle backup/migration | Memory is already set up: — run the verification checklist in Step 4 instead of re-running setup | Debugging a specific memory issue: — check the Troubleshooting section directly | Changing memory tier content: — that's the agent's job during normal operation, not a setup task
**触发**: onboarding a new agent, setting up memory for a fresh OpenClaw instance, or when asked to install the memory system on a

### ⚡ agentic-workflow-automation
> Generate reusable multi-step agent workflow blueprints. Use for trigger/action orchestration, deterministic workflow def
**功能**: workflow: automation | step agent workflow blueprints. Use for: trigger/action orchestration, deterministic workflow definitions, and automation | # Agentic Workflow Automation: ## Overview | Read `references/workflow: blueprint-guide.md` for step design guidance.

### ⚡ auto-updater
> Automatically update Clawdbot and all installed skills once daily. Runs via cron, checks for updates, applies them, and 
**功能**: Permission errors: Ensure the Gateway user can write to skill directories | Network errors: Check internet connectivity | Package conflicts: Run `clawdbot doctor` to diagnose | updater: description: "Automatically update Clawdbot and all installed skills once daily.

### ⚡ automation-workflows
> Design and implement automation workflows to save time and scale operations as a solopreneur. Use when identifying repet
**功能**: Automating before optimizing.: Don't automate a bad process. Fix the process first, then automate it. | Over-automating.: Not everything needs to be automated. If a task is rare or requires judgment, do | No error handling.: If an automation breaks and you don't know, it causes silent failures. Always se | Not testing thoroughly.: A broken automation is worse than no automation — it creates incorrect data or m
**触发**: identifying repetitive tasks to automate, building workflows across tools, setting up triggers and actions, or optimizin

### ⚡ cli-anything
> Generate or refine agent-usable CLIs for existing software/codebases using the CLI-Anything methodology. Use when the us
**功能**: Methodology request: user wants to understand or apply CLI-Anything generally | Existing harness request: user wants to use/demo one of the included examples like GIMP or LibreOffice | Packaging request: user wants an OpenClaw skill or ClawHub package derived from CLI-Anything | Method skill: teaches OpenClaw how to use CLI-Anything on local repos
**触发**: the user wants to turn a GUI app, desktop tool, repository, SDK, or web/API surface into a structured CLI for agents; wh | skill to work with the local `CLI-Anything/` repository in the workspace and turn its methodology into something usable 

### ⚡ ontology
> Typed knowledge graph for structured agent memory and composable skills. Use when creating/querying entities (Person, Pr
**功能**: skill data access.: # Ontology | Only Rule: When working with existing ontology data or schema, **append/merge** changes ins | type Person: props '{"name":"Alice","email":"alice@example.com"}' | type Task: where '{"status":"open"}'
**触发**: creating/querying entities (Person, Project, Task, Event, Document), linking related objects, enforcing constraints, pla

### ⚡ productivity-bot
> Automation bot for productivity tasks including data processing, scheduled notifications, and workflow optimization.
**功能**: # Productivity Bot: Automation bot for everyday productivity tasks. | Auto: process CSV/Excel files | Data transformation pipelines: Report generation | Daily reminders: Periodic data syncs

### ⚡ react-best-practices-2
> React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, r
**功能**: react: best-practices | # Vercel React Best Practices: Comprehensive performance optimization guide for React and Next.js applications, | Reviewing code for performance issues: Refactoring existing React/Next.js code | Optimizing bundle size or load times: ## Rule Categories by Priority

### ⚡ self-improving-proactive-agent
> A unified OpenClaw skill that merges self-improvement and proactivity: learn from corrections, maintain active state, re
**功能**: Self-improving: learn from corrections, reflection, and repeated wins | Proactive: maintain momentum, recover context, and push the next useful move | Improving Proactive Agent: slug: self-improving-proactive-agent | improving: proactive-agent
**触发**: when you want an agent that does not just remember better, but also operates better. | skill when:

### ⚡ skill-creator
> Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an exist
**功能**: Frontmatter: (YAML): Contains `name` and `description` fields. These are the only fields that | Body: (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the | When to include: When the same code is being rewritten repeatedly or deterministic reliability is | Example: `scripts/rotate_pdf.py` for PDF rotation tasks
**触发**: multiple approaches are valid, decisions depend on context, or heuristics guide the approach. | a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

### 🔍 skill-finder-cn
> Skill 查找器 | Skill Finder. 帮助发现和安装 ClawHub Skills | Discover and install ClawHub Skills. 回答
**功能**: # Skill 查找器 v1.0.1: 帮助用户发现和安装 ClawHub 上的 Skills。 | "有什么 skill 可以帮我...？": "找一个能做 X 的 skill" | "有没有 skill 可以...": "我需要一个能...的 skill" | name>" | jq: '.skill.stats'
**触发**: ：找 skill、find skill、搜索 skill."

### ⚡ skill-vetter
> Security-first skill vetting for AI agents. Use before installing any skill from ClawdHub, GitHub, or other sources. Che
**功能**: vetter: version: 1.0.0 | # Skill Vetter 🔒: Security-first vetting protocol for AI agent skills. **Never install a skill wit | [ ] Where did this skill come from?: [ ] Is the author known/reputable? | [ ] Are there reviews from other: agents?

### ⚡ superpowers-mode
> Enable or disable a strict engineering workflow inspired by obra/superpowers when the user explicitly asks (e.g., "включ
**功能**: # Superpowers Mode (On: demand) | mode.md`: Format: | Enable phrases: `включи superpowers`, `enable superpowers`, `superpowers on` | Write `enabled: true` to the state file.
**触发**: skill only for coding workflows, not general chat. | only when the user explicitly asks to enable/disable this mode, or when mode is already enabled for coding tasks.

### ⚡ travel-manager
> Comprehensive travel planning, booking, and management skill. Use when needing to plan international trips, manage multi
**功能**: manager: description: Comprehensive travel planning, booking, and management skill. Use w | # Travel Manager Skill: ## Core Capabilities | International trip planning: Multi-destination itinerary creation | Family travel logistics: Cost optimization
**触发**: needing to plan international trips, manage multi-destination itineraries, handle family travel logistics, optimize trav


---
*由 可悦🌸 自动生成 | 2026-04-19*