# Obsidian 对接方案

> L5 层 — 人类知识层 — 永久 + 人工审核

---

## 🎯 对接目标

把 Obsidian 打造成贾维斯系统的 **L5 知识沉淀层**，实现：
- AI 自动写入知识到 Obsidian
- 主人人工审核后正式沉淀
- 双向链接知识网络
- 创作素材库

---

## 📁 Vault 结构规划

```
主人ObsidianVault/
│
├── 00-日记/              ← 每日记录
│   └── YYYY-MM-DD.md
│
├── 01-创作库/            ← 创作素材
│   ├── 选题库/
│   ├── 标题库/
│   ├── 框架库/
│   └── 金句库/
│
├── 02-知识库/            ← 沉淀知识
│   ├── 科技趋势/
│   ├── 互联网观察/
│   └── 行业洞察/
│
├── 03-项目/              ← 项目文档
│   └── 贾维斯系统/
│
└── Z-归档/               ← 临时存放

```

---

## 🔄 数据流转设计

```
OpenClaw                    Obsidian
   │                           │
   ├── bank/ (整理好的)  ──→  02-知识库/ (自动写入)
   │                           │
   ├── review/ (待审核)   ──→  等待主人审核
   │                           │
   │                      ←── 主人审核后正式归档
   │                           │
   └── insights/ (洞察)    ──→ 03-项目/贾维斯系统/
```

---

## ⚙️ 技术方案

### 方案A：直接文件写入（推荐）
- Obsidian vault 指向 `C:\Users\Administrator\Obsidian\Jarvis`
- 可悦直接读写 markdown 文件
- 无需插件，纯文件操作

### 方案B：Obsidian Shell Commands
- 安装 Obsidian Shell Commands 插件
- 可悦调用 shell 命令触发 Obsidian 自动化

### 方案C：Dataview + Templater
- 用 Dataview 查询、 Templater 模板
- 可悦生成结构化笔记

---

## 📝 写作流程整合

```
主人发起写作任务
      │
      ▼
可悦生成初稿 → review/
      │
      ▼
主人审核修改
      │
      ├── 满意 → 发布
      │
      └── 不满意 → 修改 → 再次审核

最终版本 → bank/ + Obsidian 创作库
```

---

## ✅ 待实施清单

- [x] 创建 Obsidian Vault
- [x] 初始化目录结构
- [ ] 配置 Templater 模板（可选，提升体验）
- [ ] 配置 Dataview 索引（可选）
- [ ] 测试 AI 写入流程
- [ ] 配置每日自动同步
