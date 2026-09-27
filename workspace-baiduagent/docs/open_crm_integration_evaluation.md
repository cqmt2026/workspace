# OpenCRM融合评估报告

> 评估日期：2026-09-06  
> 评估目标：判断是否将OpenCRM融合进百都工作系统

---

## 一、OpenCRM简介

### 核心特性
- **定位**：OpenClaw原生轻量CRM，HubSpot开源替代
- **技术栈**：React 19 + Hono + Cloudflare D1 (SQLite)
- **数据模型**：companies（公司）||--o{ contacts（联系人）||--o{ deals（商机）
- **特色功能**：
  - Agent Mode（`?agent=true`）— AI代理优化UI
  - CSV/XLSX导入 — 列映射自动匹配
  - 活动时间线 — 每次交互自动记录
  - 原生集成Gmail/Google Calendar/Slack

### GitHub
- **链接**：github.com/clawnify/OpenCRM
- **Stars**：20 ⭐
- **许可证**：MIT
- **最后更新**：2026-08-22

---

## 二、当前系统CRM分析

### 现有结构
```
data/baidu_crm.db
├── customers（客户表）
│   ├── id, name, industry, phone, address, district
│   ├── lat, lng, source, status, tier
│   └── created_at, updated_at
├── call_logs（通话记录表）
│   ├── id, customer_id, duration, result, notes
│   └── created_at
└── industry_cards（行业数据卡）
    ├── id, industry, data, stats
    └── created_at
```

### 当前数据量
- **customers**：~12,000+条（创新型中小企业+专精特新等）
- **call_logs**：待确认
- **industry_cards**：待确认

### 当前能力
- ✅ 客户信息管理（基础CRUD）
- ✅ 通话记录追踪
- ✅ 行业数据卡
- ❌ 商机管理（deals）
- ❌ 活动时间线
- ❌ AI代理优化UI
- ❌ 第三方集成（Gmail/Calendar/Slack）

---

## 三、融合可行性评估

### 优势（Pros）

| 维度 | OpenCRM优势 | 对系统价值 |
|------|------------|-----------|
| **Agent Mode** | `?agent=true`优化UI，大点击目标 | ✅ 高 — 便于AI自动化操作 |
| **活动时间线** | 每次交互自动记录 | ✅ 高 — 增强客户追踪 |
| **原生集成** | Gmail/Calendar/Slack | ⚠️ 中 — 国内场景适配需定制 |
| **数据模型** | companies→contacts→deals三层 | ✅ 中 — 更清晰的销售漏斗 |
| **CSV导入** | 列映射自动匹配 | ✅ 高 — 批量导入现有数据 |
| **技术栈** | React+Hono+D1 | ⚠️ 中 — 需额外部署Node环境 |

### 劣势（Cons）

| 维度 | OpenCRM劣势 | 对系统影响 |
|------|------------|-----------|
| **数据库** | Cloudflare D1（边缘计算） | ⚠️ 中 — 需迁移到本地SQLite |
| **依赖** | Node.js 20+ + pnpm | ⚠️ 中 — 需安装额外环境 |
| **规模** | 20 Stars，较新项目 | ⚠️ 低 — 社区支持待观察 |
| **中文适配** | 英文版，无中文界面 | ⚠️ 中 — 需本地化 |
| **国内集成** | Gmail/Calendar/Slack | ❌ 高 — 需替换为微信/企微 |
| **迁移成本** | 需迁移12,000+条数据 | ⚠️ 中 — 工作量大 |

### 核心冲突

1. **数据库架构差异**
   - 当前：单表customers（扁平结构）
   - OpenCRM：三表关联（companies→contacts→deals）
   - **影响**：需重构数据模型

2. **集成生态差异**
   - 当前：微信/电话为主
   - OpenCRM：Gmail/Calendar/Slack
   - **影响**：需大量定制开发

3. **部署环境差异**
   - 当前：Python+SQLite，轻量级
   - OpenCRM：Node.js+D1，需额外环境
   - **影响**：增加运维复杂度

---

## 四、融合方案对比

### 方案A：完全替换（不推荐）
- **做法**：迁移所有数据到OpenCRM，弃用当前CRM
- **优点**：获得完整功能
- **缺点**：
  - 迁移工作量巨大（12,000+条数据）
  - 需重新适配所有脚本（补抓/话术/盘点）
  - 需安装Node.js环境
  - 国内集成需大量定制
- **风险评估**：🔴 高风险

### 方案B：并行运行（谨慎尝试）
- **做法**：保留当前CRM，同时部署OpenCRM作为辅助
- **优点**：
  - 可测试Agent Mode功能
  - 不影响现有工作流
- **缺点**：
  - 数据 duplication
  - 双系统维护成本高
  - 需解决数据同步问题
- **风险评估**：🟡 中等风险

### 方案C：借鉴理念（推荐）
- **做法**：不直接集成OpenCRM，而是借鉴其设计理念
- **可借鉴点**：
  1. **活动时间线** — 在call_logs表增加时间线字段
  2. **Agent Mode UI** — 在web界面增加AI优化模式
  3. **CSV导入** — 增强现有导入脚本
  4. **商机管理** — 在CRM增加deals表
- **优点**：
  - 低风险，不影响现有系统
  - 按需增强，逐步迭代
  - 保持Python+SQLite轻量架构
- **风险评估**：🟢 低风险

---

## 五、具体融合建议

### 短期（本周）
1. **增强call_logs表**
   ```sql
   ALTER TABLE call_logs ADD COLUMN activity_type TEXT;
   ALTER TABLE call_logs ADD COLUMN next_followup DATETIME;
   ALTER TABLE call_logs ADD COLUMN ai_score REAL;
   ```

2. **增加leads表**（商机管理）
   ```sql
   CREATE TABLE leads (
       id INTEGER PRIMARY KEY,
       customer_id INTEGER,
       stage TEXT, -- prospect/qualified/proposal/negotiation/won/lost
       value REAL,
       close_date DATETIME,
       notes TEXT,
       created_at DATETIME,
       updated_at DATETIME
   );
   ```

3. **增强CSV导入**
   - 借鉴OpenCRM的列映射逻辑
   - 支持自动识别行业/区域/层级

### 中期（本月）
1. **增加活动时间线**
   - 在customers表增加activity_log字段
   - 每次通话/跟进自动记录

2. **开发Agent Mode界面**
   - 基于当前web界面
   - 增加大点击目标、显式操作按钮

3. **集成微信/企微**
   - 替换OpenCRM的Gmail/Slack集成
   - 使用企业微信API

### 长期（本季度）
1. **评估OpenCRM完整部署**
   - 如需求增长，可考虑完整部署
   - 作为高级功能模块，非核心替换

---

## 六、结论与建议

### 评估结论
**不建议完全替换，建议借鉴理念增强现有系统**

### 理由
1. **成本效益比低**
   - 迁移12,000+条数据成本高
   - 需重新适配所有脚本
   - 需安装额外环境（Node.js）

2. **适配成本高**
   - 国内集成（微信/企微）需大量定制
   - OpenCRM主要面向海外SaaS场景

3. **风险高**
   - 完全替换可能导致系统不稳定
   - 影响当前销售工作流程

### 建议行动
**采用方案C：借鉴理念，增强现有系统**

具体步骤：
1. ✅ 本周：增强call_logs表（增加activity_type/next_followup/ai_score）
2. ✅ 本周：增加leads表（商机管理）
3. ✅ 本周：增强CSV导入脚本（列映射逻辑）
4. ⏳ 本月：开发活动时间线功能
5. ⏳ 本月：开发Agent Mode界面
6. ⏳ 本季度：评估是否需要完整部署OpenCRM

---

## 七、下一步

主人现在要：
- **A** 立即执行方案C（增强现有CRM）
- **B** 先部署OpenCRM测试版，评估效果
- **C** 暂不融合，继续调研其他工具
- **D** 总结今天成果，结束调研

选一个？
