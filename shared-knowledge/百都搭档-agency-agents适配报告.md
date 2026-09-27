# 百都搭档 - agency-agents 适配报告
> 生成时间: 2026-09-06 | 来源: msitarzewski/agency-agents (273 agents)
> 双源验证: 主系统筛选 + 百都搭档子Agent独立分析，结论一致

## 筛选逻辑
百都搭档 = 百度代理商销售辅助，服务低空经济/新能源板块客户
核心场景：客户开发 + 话术生成 + 数据分析 + 方案撰写 + ROI测算

---

## P0 核心必用（11个）

| Agent | 英文名 | 核心能力 | 百都适用场景 |
|-------|--------|---------|------------|
| 🎯 outbound-strategist | Outbound Strategist | 信号驱动客户开发、ICP定义、多触点序列 | 低空经济/新能源客户开发策略、每日拨打清单排序 |
| ♟️ deal-strategist | Deal Strategist | MEDDPICC商机评估、竞争定位、赢单规划 | 评估Top20意向客户质量、判断跟进优先级 |
| 🛠️ sales-engineer | Sales Engineer | 技术演示、POC设计、竞品Battlecard | 向客户演示百度广告投放方案 |
| 📊 pipeline-analyst | Pipeline Analyst | 销售漏斗分析、预测准确率、商机健康度 | 周报数据诊断、转化率异常预警 |
| 💰 ppc-campaign-strategist | PPC Campaign Strategist | 搜索广告架构、预算分配、出价策略 | 百度推广账户结构与优化 |
| 🔍 search-query-analyst | Search Query Analyst | 搜索词分析、否定关键词、意图分类 | 挖掘各行业高价值搜索词 |
| 🇨🇳 baidu-seo-specialist | Baidu SEO Specialist | 百度搜索优化、ICP合规、中文关键词 | SEO+SEM协同方案、百度推广差异话术 |
| 🏛️ government-digital-presales-consultant | Gov Digital Presales Consultant | 中国ToG售前、政策理解、标书制作 | 政府/国企客户开发 |
| 🏹 proposal-strategist | Proposal Strategist | RFP响应、方案撰写、叙事结构 | 大客户提案、投标方案结构 |
| 💰 finance-tracker | Finance Tracker | 财务分析、预算管控、ROI计算 | 帮口腔/医美客户算投放ROI账 |
| 💬 wechat-mini-program-developer | WeChat Mini Program Dev | 微信小程序开发 | 本地商家小程序落地页方案 |

## P1 推荐增强（8个）

| Agent | 英文名 | 核心能力 | 百都适用场景 |
|-------|--------|---------|------------|
| 🗺️ sales-account-strategist | Account Strategist | 客户深耕、stakeholder映射、扩单 | 老客户转介绍/复购策略 |
| 🏋️ sales-coach | Sales Coach | 销售培训、通话辅导、pipeline review | 销售团队赋能 |
| 🔍 sales-discovery-coach | Discovery Coach | 需求挖掘话术、SPIN提问法 | 客户沟通话术优化 |
| 🧲 sales-offer-lead-gen-strategist | Offer & Lead Gen | 线索生成策略、诱饵设计 | 获客策略 |
| 📋 paid-media-auditor | Paid Media Auditor | 200+项账户审计 | 大客户账户诊断 |
| ✍️ ad-creative-strategist | Ad Creative Strategist | 广告文案、RSA优化 | 百度创意文案框架生成 |
| 📡 paid-media-tracking-specialist | Tracking Specialist | 转化追踪、GTM/GA4 | 客户转化数据追踪 |
| 📊 analytics-reporter | Analytics Reporter | 数据看板、KPI追踪 | 客户数据报表 |

## P2 可选增强

### 内容+增长
- douyin-strategist → 本地生活客户抖音代运营参考
- tiktok-strategist → 海外抖音策略
- growth-hacker → 低成本获客渠道发现
- content-creator → 百家号/短视频内容规划
- short-video-editing-coach → 视频剪辑指导
- multi-platform-publisher → 多平台一键发布

### 垂直场景
- government-digital-presales-consultant → ToG项目售前
- wechat-mini-program-developer → 本地商家小程序
- finance-tracker → 客户ROI测算
- xiaohongshu-specialist → 小红书种草策略

---

## 双源对比结论

| 维度 | 主系统筛选 | 百都搭档子Agent | 一致性 |
|------|-----------|----------------|-------|
| P0核心agent | 11个 | 11个 | ✅ 完全一致 |
| P1推荐agent | 8个 | 5个(部分合并) | ✅ 一致 |
| P2可选 | 20+个 | 6个 | ✅ 主系统更全 |
| 排除项 | 技术/游戏/海外/垂直 | 技术/游戏/海外/垂直 | ✅ 一致 |

### 子Agent补充视角
- account-strategist 定位为"老客户转介绍/复购策略"更贴合实际
- brand-guardian 可适配为"百度品牌保护服务销售话术"
- 强调立即接入建议（每日拨打清单排序、Top20意向客户分析）

---

## 立即行动清单

**本周接入（P0）**：
1. `outbound-strategist` → 优化每日拨打清单排序
2. `deal-strategist` → 分析Top20意向客户，判断跟进优先级
3. `baidu-seo-specialist` → 生成百度推广产品差异话术
4. `finance-tracker` → 帮口腔/医美客户算ROI账

**下周接入（P1）**：
5. `pipeline-analyst` → 诊断销售漏斗健康度
6. `ppc-campaign-strategist` → 设计百度搜索推广方案框架
7. `content-creator` → 百家号内容规划模板
8. `search-query-analyst` → 挖掘低空经济/新能源行业搜索词

**按需接入（P2）**：
- 短视频/内容营销类 agent
- 垂直行业定制化 agent

---

## 使用方式

```python
# 主系统派发
sessions_spawn(task="优化今日拨打清单", agentId="outbound-strategist")
sessions_spawn(task="分析Top20口腔诊所客户跟进优先级", agentId="deal-strategist")
sessions_spawn(task="生成百度推广SEO+SEM协同方案", agentId="baidu-seo-specialist")
sessions_spawn(task="帮客户算投放ROI账", agentId="finance-tracker")

# 自然语言触发（写入记忆后）
# "调outbound-strategist优化今日拨打清单"
# "用deal-strategist分析客户跟进优先级"
```

## 文件位置
- 源仓库: `workspace/agency-agents/`
- OpenClaw格式: `workspace/agents/<slug>/SOUL.md + AGENTS.md + IDENTITY.md`
- 共273个agent（含README占位共274目录）

---
_双源验证完成，结论一致。_
