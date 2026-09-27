# GitHub营销工具调研报告

> 调研日期：2026-09-06  
> 调研目标：为百都科技"小度"销售搭档系统寻找可提升效率的开源营销/获客/CRM工具  
> 核心场景：挖掘企业客户名单（目标池）、补企业电话、行业数据分析、话术方案生成、客户管理（CRM）

---

## 一、企业/商户名单抓取 & 数据挖掘类

这类工具直接服务于"找企业名单+补电话"的核心需求，是本调研重点。

### 1. google-maps-scraper（Google地图爬虫）
| 项目 | 信息 |
|------|------|
| **Stars** | 3,439 |
| **功能定位** | Google Maps企业数据抓取，提取50+数据点（名称、地址、电话、邮箱、评分、评论等），支持API调用 |
| **开发语言** | 原生应用（Python/Node.js集成API） |
| **最近提交** | 2026-07-27（仍在维护） |
| **许可证** | MIT |
| **GitHub** | https://github.com/omkarcloud/google-maps-scraper |

**适用性评估：🟢 高**  
> 直接匹配我们"地图POI抓取企业名单+补电话"的场景；免费额度每月200次搜索，每次100-1000+结果，可免费获取2万+线索/月；有Python/Node.js API，可集成到我们的补抓脚本中；中国场景可用百度地图/高德地图替代方案。

---

### 2. AIHawk（AI浏览器自动化代理）
| 项目 | 信息 |
|------|------|
| **Stars** | 30,314 |
| **功能定位** | 开源AI浏览器代理，自然语言控制浏览器完成网页自动化任务（市场调研、数据抓取、简历投递等） |
| **开发语言** | Python |
| **最近提交** | 2026-09-06（非常活跃） |
| **许可证** | MIT |
| **GitHub** | https://github.com/feder-cr/AIHawk |

**适用性评估：🟢 高**  
> 可用于自动化访问百度地图/高德地图/企业信息网站抓取客户数据；支持在China部署，绕过登录验证；可作为我们POI抓取脚本的AI增强层——用自然语言指令替代硬编码。

---

### 3. Scout（社交媒体线索抓取）
| 项目 | 信息 |
|------|------|
| **Stars** | 593 |
| **功能定位** | 抓取Instagram/Twitch/TikTok/LinkedIn个人资料，从bio提取邮箱并用SMTP验证，导出CSV |
| **开发语言** | Python |
| **最近提交** | 2026-09-05（活跃） |
| **许可证** | MIT |
| **GitHub** | https://github.com/kiryano/Scout |

**适用性评估：🟡 中**  
> 适合从LinkedIn等B2B平台获取决策人联系方式；但LinkedIn反爬严格，需要配合AIHawk等浏览器自动化工具使用；对我们"找企业主/老板电话"有一定帮助。

---

### 4. OpenOutreach（AI B2B线索发现）
| 项目 | 信息 |
|------|------|
| **Stars** | 2,913 |
| **功能定位** | 开源AI B2B线索发现代理：描述你的产品→自动找到匹配客户→解释原因→从你的邮箱发送邮件；无需自带名单 |
| **开发语言** | Python |
| **最近提交** | 2026-09-05（活跃） |
| **许可证** | GPLv3 |
| **GitHub** | https://github.com/eracle/OpenOutreach |

**适用性评估：🟡 中**  
> 理念先进（描述产品→自动找线索→发邮件），但目前依赖BetterContact数据源（英文B2B为主）；对国内中小企业名单覆盖有限；可作为外线英文客户的工具参考。

---

### 5. business-leads-ai-automation（AI自动化获客）
| 项目 | 信息 |
|------|------|
| **Stars** | 180 |
| **功能定位** | Google Maps爬虫 + AI生成邮件/WhatsApp模板，面向中小企业和代理商 |
| **开发语言** | HTML/JS |
| **最近提交** | 2026-08-18 |
| **许可证** | MIT |
| **GitHub** | https://github.com/asiifdev/business-leads-ai-automation |

**适用性评估：🟢 高**  
> 与我们的场景高度契合：地图爬虫→AI生成话术模板→多渠道触达；虽然是英文模板但架构可直接参考复用。

---

### 6. email-sleuth（企业邮箱发现）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 用姓名+域名发现和验证专业邮箱 |
| **开发语言** | Rust |
| **最近提交** | 2025-12-20 |
| **许可证** | 未知 |
| **GitHub** | https://github.com/buyukakyuz/email-sleuth |

**适用性评估：🟡 中**  
> Rust编写性能优秀，适合批量验证已有邮箱格式；但对国内企业电邮覆盖率有限（企业多用QQ邮箱/企业微信）。

---

## 二、CRM客户管理类（轻量、本地部署）

### 7. Twenty（AI原生CRM）⭐ 推荐
| 项目 | 信息 |
|------|------|
| **Stars** | 56,309 |
| **功能定位** | 开源Salesforce替代品，专为AI设计，支持自定义实体、自动化工作流 |
| **开发语言** | TypeScript (NestJS + React) |
| **最近提交** | 2026-09-05（非常活跃） |
| **许可证** | 自定义开源协议 |
| **GitHub** | https://github.com/twentyhq/twenty |

**适用性评估：🟢 高**  
> 现代架构，REST/GraphQL API丰富，可本地部署；AI原生设计便于接入我们的LLM话术生成能力；但部署复杂度较高，需要Docker环境。

---

### 8. EspoCRM（轻量PHP CRM）
| 项目 | 信息 |
|------|------|
| **Stars** | 3,327 |
| **功能定位** | 轻量级开源CRM，支持leads/contacts/opportunities/营销活动/知识库，SPA架构 |
| **开发语言** | PHP (Laravel风格) |
| **最近提交** | 2026-09-04（活跃） |
| **许可证** | AGPLv3 |
| **GitHub** | https://github.com/espocrm/espocrm |

**适用性评估：🟢 高**  
> 部署极简单（PHP+MySQL），REST API完善，有中文界面；非常适合我们当前SQLite CRM的升级替代；支持自定义字段和流程。

---

### 9. SuiteCRM（企业级CRM）
| 项目 | 信息 |
|------|------|
| **Stars** | 5,725 |
| **功能定位** | 源自SugarCRM，功能完整的企业级CRM，支持销售漏斗、营销自动化、客服工单 |
| **开发语言** | PHP |
| **最近提交** | 2026-09-03（活跃） |
| **许可证** | AGPLv3 |
| **GitHub** | https://github.com/SuiteCRM/SuiteCRM |

**适用性评估：🟡 中**  
> 功能全面但偏重，对于小团队可能过重；适合百都科技销售团队规模化后的升级选项。

---

### 10. Frappe CRM（极简CRM）
| 项目 | 信息 |
|------|------|
| **Stars** | 3,473 |
| **功能定位** | 功能完整的开源CRM，轻量简洁，与Frappe生态无缝集成 |
| **开发语言** | Vue + Python (Frappe框架) |
| **最近提交** | 2026-09-05（活跃） |
| **许可证** | AGPLv3 |
| **GitHub** | https://github.com/frappe/crm |

**适用性评估：🟢 高**  
> 部署简单（bench工具一键安装），UI现代，支持移动端；可与Frappe ERPNext无缝对接，适合销售团队快速上手。

---

### 11. Krayin CRM（Laravel多租户CRM）
| 项目 | 信息 |
|------|------|
| **Stars** | 23,842 |
| **功能定位** | 基于Laravel的多租户CRM，支持SaaS模式，多角色权限管理 |
| **开发语言** | PHP (Laravel + Vue) |
| **最近提交** | 2026-09-01（活跃） |
| **许可证** | MIT |
| **GitHub** | https://github.com/krayin/laravel-crm |

**适用性评估：🟢 高**  
> 23K+ stars说明社区认可度高；多租户架构适合百都科技未来SaaS化需求；MIT许可可商业使用无风险。

---

### 12. Dolibarr ERP/CRM
| 项目 | 信息 |
|------|------|
| **Stars** | 7,576 |
| **功能定位** | 法国老牌ERP/CRM套件，支持发票/订单/库存/会计/联系人/销售漏斗 |
| **开发语言** | PHP |
| **最近提交** | 2026-09-05（活跃） |
| **许可证** | GPLv3 |
| **GitHub** | https://github.com/Dolibarr/dolibarr |

**适用性评估：🟡 中**  
> 功能非常全面但界面偏传统；适合已有意向做完整ERP管理的企业；作为纯CRM替代偏重。

---

### 13. Monica（个人关系管理PRM）
| 项目 | 信息 |
|------|------|
| **Stars** | 25,233 |
| **功能定位** | 个人关系管理工具，类似CRM但面向亲友而非商业客户 |
| **开发语言** | PHP (Laravel) |
| **最近提交** | 2026-04-24（维护中但放缓） |
| **许可证** | AGPLv3 |
| **GitHub** | https://github.com/monicahq/monica |

**适用性评估：🔴 低**  
> 定位是个人社交关系管理，不是商业CRM；不适用于企业销售场景。

---

### 14. Odoo（开源ERP套件）
| 项目 | 信息 |
|------|------|
| **Stars** | 54,182 |
| **功能定位** | 模块化ERP套件，含CRM、销售、库存、会计、HR等50+应用 |
| **开发语言** | Python |
| **最近提交** | 2026-09-06（非常活跃） |
| **许可证** | LGPLv3（社区版免费） |
| **GitHub** | https://github.com/odoo/odoo |

**适用性评估：🟡 中**  
> 功能极其丰富，但企业版部分模块收费；部署复杂，学习曲线陡峭；适合作为中长期ERP选型参考。

---

### 15. Frappe ERPNext
| 项目 | 信息 |
|------|------|
| **Stars** | 38,923 |
| **功能定位** | 功能完整的开源ERP，含CRM模块，印度市场主导 |
| **开发语言** | Python (Frappe框架) |
| **最近提交** | 2026-09-05（活跃） |
| **许可证** | GPLv3 |
| **GitHub** | https://github.com/frappe/erpnext |

**适用性评估：🟡 中**  
> 成熟稳定，社区活跃；但同样偏重，且对中文/中国企业适配不足；CRM模块可单独使用。

---

### 16. CordysCRM（国产AI CRM）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 国产开源AI CRM，深度融合AI能力，支持私有化部署 |
| **开发语言** | Java |
| **最近提交** | 2026-09-04（活跃） |
| **许可证** | 未知 |
| **GitHub** | https://github.com/1Panel-dev/CordysCRM |

**适用性评估：🟢 高**  
> 国产项目，天然适配中文环境；AI CRM定位与我们的需求高度一致；但需进一步评估功能完整性和社区活跃度。

---

## 三、话术/文案生成 & 内容营销类

### 17. AI SDR Agent Template（B2B销售AI代理模板）⭐ 强烈推荐
| 项目 | 信息 |
|------|------|
| **Stars** | 173 |
| **功能定位** | 基于OpenClaw的10阶段销售管道AI SDR模板，支持WhatsApp/Telegram/Email多渠道，4层记忆防遗忘架构 |
| **开发语言** | Shell (OpenClaw Skill模板) |
| **最近提交** | 2026-08-20 |
| **许可证** | MIT |
| **GitHub** | https://github.com/iPythoning/b2b-sdr-agent-template |

**适用性评估：🟢 高（与生态最强匹配）**  
> 这是专门为OpenClaw生态设计的B2B销售AI代理模板，与我们当前的技术栈完全一致！支持：多渠道外呼(WhatsApp/Telegram/Email)、10阶段销售管道、BANT资格判定、自动报价、话术生成、记忆持久化。可直接作为"小度"系统的参照蓝图或升级方向。

---

### 18. sales-outreach-automation-langgraph（AI销售外联自动化）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 用LangGraph构建AI销售代理，自动研究线索、资质审核、个性化消息生成，集成HubSpot/Airtable |
| **开发语言** | Python |
| **最近提交** | 2025-01-15 |
| **许可证** | 未知 |
| **GitHub** | https://github.com/kaymen99/sales-outreach-automation-langgraph |

**适用性评估：🟡 中**  
> LangGraph架构值得参考，但依赖LangChain生态；与我们的OpenClaw体系不兼容，可作为设计思路借鉴。

---

### 19. YALC - The GTM Operating System（开源Clay替代）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 开源Clay替代，CLI优先，自我托管，在Claude Code中运行GTM代理 |
| **开发语言** | TypeScript |
| **最近提交** | 2026-08-20 |
| **许可证** | MIT |
| **GitHub** | https://github.com/Othmane-Khadri/YALC-the-GTM-operating-system |

**适用性评估：🟡 中**  
> 理念先进（GTM操作系统），但偏英文SaaS场景；架构设计值得参考。

---

### 20. AI-powered Email/WhatsApp Templates（AI外联模板）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 基于AI生成个性化冷启邮件/WhatsApp消息模板 |
| **开发语言** | 未知 |
| **GitHub** | 分散在多个项目中 |

**适用性评估：🟡 中**  
> AI文案生成是通用能力，OpenAI/Anthropic API已足够强大；无需专门工具。

---

## 四、行业数据分析类

### 21. API Mega List（API聚合目录）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 收录大量可用API，包含工商数据、企业信息、搜索引擎等接口 |
| **开发语言** | Markdown |
| **最近提交** | 2026-07-23 |
| **GitHub** | https://github.com/cporter202/API-mega-list |

**适用性评估：🟡 中**  
> 可作为数据源参考目录，帮助我们了解有哪些可用的工商数据API。

---

### 22. Industry Completion Tracker（行业完成度追踪）
> 注意：这是我们已经自研的工具（`scripts/core/industry_completion.py`），非外部工具，但值得在此列出作为参考基准。

---

## 五、电话拨打/外呼辅助类

### 23. CoreClaw API Directory（118个Worker API目录）
| 项目 | 信息 |
|------|------|
| **Stars** | 信息不足 |
| **功能定位** | 118个分类API目录，涵盖网页抓取、自动化、电商、社交数据、Lead Gen等 |
| **开发语言** | Python |
| **最近提交** | 2026-09-05（活跃） |
| **GitHub** | https://github.com/cporter202/coreclaw-api-directory |

**适用性评估：🟢 高**  
> 可作为数据源和工具集的外部补充参考，包含多个与我们场景相关的API端点。

---

## 六、OpenClaw/Claude Skill生态延伸

### 24. b2b-sdr-agent（PulseAgent技能）
- **来源**：ClawHub市场
- **定位**：AI SDR技能包，与上面的模板对应
- **适用性：🟢 高** — 可直接安装到OpenClaw生态使用

### 25. 其他发现
- **coreclaw-api-directory** — 118个营销相关API，可作为数据源目录
- **agentic-ai-starters** — AI应用启动模板集合，含lead gen系统蓝图
- **tinder-to-crm** — 将Tinder匹配转为CRM联系人（有趣但非直接相关）

---

## 七、综合评估与推荐排序

### 🏆 第一梯队：强烈推荐（高度匹配我们的场景）

| 排名 | 工具 | Stars | 理由 |
|------|------|-------|------|
| 1 | **AI SDR Agent Template** | 173 | 与OpenClaw完全兼容，10阶段销售管道+多渠道外呼+记忆持久化，可直接借鉴或升级 |
| 2 | **google-maps-scraper** | 3,439 | 直接匹配"地图POI抓取企业名单+补电话"场景，免费额度大，API易集成 |
| 3 | **EspoCRM** | 3,327 | 轻量PHP CRM，部署简单，适合当前SQLite CRM升级，REST API完善 |
| 4 | **AIHawk** | 30,314 | 浏览器自动化能力强，可增强POI抓取，绕过登录限制 |
| 5 | **Krayin CRM** | 23,842 | 多租户架构，MIT许可，适合未来SaaS化扩展 |

### ⭐ 第二梯队：值得关注（中等匹配度）

| 排名 | 工具 | Stars | 理由 |
|------|------|-------|------|
| 6 | **Twenty CRM** | 56,309 | AI原生架构最先进，但部署复杂 |
| 7 | **business-leads-ai-automation** | 180 | "地图爬虫+AI话术"一体化方案，架构可借鉴 |
| 8 | **CordysCRM** | — | 国产AI CRM，中文适配天然优势 |
| 9 | **OpenOutreach** | 2,913 | B2B线索发现理念先进，但数据源偏英文 |
| 10 | **Frappe CRM** | 3,473 | 轻量现代，与ERPNext无缝集成 |

### 🔵 第三梯队：参考了解（场景不直接匹配但有用）

| 排名 | 工具 | Stars | 理由 |
|------|------|-------|------|
| 11 | **SuiteCRM** | 5,725 | 企业级但偏重 |
| 12 | **Dolibarr** | 7,576 | 老牌但界面传统 |
| 13 | **Odoo** | 54,182 | 功能最全但复杂 |
| 14 | **Scout** | 593 | 社交媒体线索抓取，适用B2B社交平台 |
| 15 | **CoreClaw API Directory** | — | 数据源参考目录 |

### ❌ 不推荐（明显不匹配）

| 工具 | 理由 |
|------|------|
| Monica | 个人关系管理，非商业CRM |
| Open Food Facts | 食品数据库，完全无关 |

---

## 八、针对百都科技"小度"系统的 actionable 建议

### 立即可以尝试的
1. **试用 EspoCRM** — 替换当前SQLite CRM，部署10分钟搞定，REST API可直接对接现有脚本
2. **集成 google-maps-scraper** — 增强我们的地图POI补抓能力，替代百度POI配额不足的问题
3. **研究 AIHawk** — 作为浏览器自动化层，增强我们现有爬虫脚本的稳健性

### 中期规划
4. **评估 AI SDR Agent Template** — 与我们现有b2b-sdr-agent技能做对比，看哪些能力可以吸收进小度系统
5. **探索 Twenty CRM** — 如果EspoCRM不够用，Twenty的AI原生架构更适合长期演进
6. **关注 Krayin CRM** — 作为多租户SaaS化的候选底座

### 长期方向
7. **借鉴 OpenOutreach 理念** — "描述产品→自动找线索→发邮件"的零名单外联模式
8. **参考 AI-powered lead gen 一体化** — 将爬虫+AI话术+CRM+外呼串联成端到端pipeline

---

## 九、备注

- 所有Star数和数据截至2026-09-06
- web_search工具不可用，数据来自GitHub API和HTML页面直接抓取
- GitHub API存在速率限制，部分项目未获取完整信息
- 本报告不做任何外部数据抓取动作，仅做信息检索和文档整理

---

*报告由小度自动生成 | 2026-09-06*
