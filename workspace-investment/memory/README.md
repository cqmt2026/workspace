# workspace-investment 记忆结构说明

**更新时间**: 2026-04-07 12:55  
**结构版本**: V1.0

---

## 📁 目录结构

```
workspace-investment/
├── memory/                 ← 记忆系统 (新增)
│   ├── L1-日志/           ← 每日投资日志
│   ├── L2-核心/           ← 核心配置 (AGENTS.md/MEMORY.md 等)
│   ├── L3-数据/           ← 股票池/配置文件
│   └── L4-文档/           ← 使用说明/规则
│
├── src/                    ← 源代码
│   ├── data_fetchers/     ← 数据获取脚本
│   ├── factors/           ← 因子库
│   ├── strategies/        ← 策略库
│   ├── risk/              ← 风控模块
│   └── signals/           ← 信号生成
│
├── data/                   ← 数据文件
│   ├── raw/               ← 原始数据
│   └── processed/         ← 处理后的数据
│
├── outputs/                ← 输出目录 (统一)
│   ├── reports/           ← 日报/周报/月报
│   ├── charts/            ← 图表
│   └── logs/              ← 运行日志
│
├── config/                 ← 配置文件
│   ├── eastmoney_cookie.json
│   ├── stock_pool.json
│   └── ...
│
└── docs/                   ← 文档归档 (新增)
    ├── H 盘整合报告/
    ├── 系统配置文档/
    ├── 使用指南/
    └── API 文档/
```

---

## 📊 memory/ 层级说明

### 【L1-日志】每日记录

**用途**: 记录每日市场数据、系统状态、投资笔记

**文件**: `YYYY-MM-DD.md`

**内容**:
- 大盘指数
- 热点板块
- 资金流向
- 个股监控
- 系统状态
- 投资笔记

**示例**: `2026-04-07.md`

---

### 【L2-核心】核心配置

**用途**: 系统核心配置文件

**文件**:
- `AGENTS.md` - Agent 配置
- `SOUL.md` - 系统定位
- `USER.md` - 用户偏好
- `MEMORY.md` - 长期记忆

---

### 【L3-数据】数据文件

**用途**: 股票池、配置数据

**文件**:
- `stock_pool.json` - 股票池配置
- `eastmoney_cookie.json` - 东财 Cookie
- `strategies/` - 策略配置

---

### 【L4-文档】使用说明

**用途**: 使用指南、规则说明

**文件**:
- `usage_guide.md` - 使用说明
- `rules.md` - 投资规则
- `api_docs.md` - API 文档

---

## 📁 docs/ 归档说明

### 【H 盘整合报告】
- H_DRIVE_INVENTORY.md
- H_DRIVE_RESOURCES.md
- INTEGRATION_COMPLETE.md
- ...

### 【系统配置文档】
- SYSTEM_FINALIZATION.md
- SKILL_INTEGRATION.md
- ...

### 【使用指南】
- README.md
- USAGE_GUIDE.md

### 【API 文档】
- DATA_CAPABILITIES_REPORT.md
- ...

---

## 🎯 优化成果

### 【优化前】
```
workspace-investment/
├── MEMORY.md              ← 单个文件
├── AGENTS.md              ← 根目录
├── SOUL.md                ← 根目录
├── 20+ 个文档             ← 根目录混乱
├── outputs/               ← 输出
└── src/
    └── outputs/           ← 重复输出
```

### 【优化后】
```
workspace-investment/
├── memory/                ← 统一记忆系统
│   ├── L1-日志/
│   ├── L2-核心/
│   ├── L3-数据/
│   └── L4-文档/
├── docs/                  ← 文档归档
├── outputs/               ← 统一输出
└── src/                   ← 源代码
```

---

## 📋 文件移动汇总

| 文件 | 原位置 | 新位置 |
|------|--------|--------|
| MEMORY.md | 根目录 | memory/L2-核心/ |
| AGENTS.md | 根目录 | memory/L2-核心/ |
| SOUL.md | 根目录 | memory/L2-核心/ |
| USER.md | 根目录 | memory/L2-核心/ |
| DATA_CAPABILITIES_REPORT.md | 根目录 | docs/H 盘整合报告/ |
| H_DRIVE_INVENTORY.md | 根目录 | docs/H 盘整合报告/ |
| README.md | 根目录 | docs/使用指南/ |
| USAGE_GUIDE.md | 根目录 | docs/使用指南/ |

---

## ✅ 清理项目

| 项目 | 操作 | 说明 |
|------|------|------|
| `data/ml_configs/` | 删除 | 空目录 |
| `data/raw/` | 删除 | 空目录 |
| `notebooks/` | 删除 | 空目录 |
| `src/outputs/logs/` | 删除 | 空目录 |

---

## 🎯 后续优化

### 【已完成】
- ✅ memory/ 目录结构创建
- ✅ docs/ 文档归档创建
- ✅ 核心文件移动
- ✅ 空目录清理
- ✅ L1 日志模板创建

### 【待办】
- ⏳ data/knowledge_cards/ 整理 (67 个文件)
- ⏳ 根目录剩余文档归档
- ⏳ Git 提交结构变更

---

_结构优化完成时间：2026-04-07 12:55_
