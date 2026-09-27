# Git 提交指南

**更新时间**: 2026-04-07  
**状态**: 待提交

---

## 📊 当前变更汇总

### 【新增文件】

| 目录 | 文件数 | 说明 |
|------|--------|------|
| `memory/` | 4 个目录 + 3 文件 | 记忆系统 (L1-L4) |
| `docs/` | 7 个目录 + 15 文件 | 文档归档 |
| `src/data_fetchers/` | 10+ 文件 | 数据获取脚本 |

### 【移动文件】

| 原位置 | 新位置 | 文件数 |
|--------|--------|--------|
| 根目录 | memory/L2-核心/ | 4 个 (MEMORY/AGENTS 等) |
| 根目录 | docs/H 盘整合报告/ | 5 个报告 |
| 根目录 | docs/系统配置文档/ | 3 个文档 |
| 根目录 | docs/使用指南/ | 2 个指南 |
| data/knowledge_cards/ | docs/分类目录/ | 67 个文件 |

### 【删除文件】

| 目录 | 说明 |
|------|------|
| `data/ml_configs/` | 空目录 |
| `data/raw/` | 空目录 |
| `notebooks/` | 空目录 |
| `src/outputs/logs/` | 空目录 |

---

## 📝 Git 提交命令

### 【步骤 1: 查看状态】
```bash
cd C:\Users\Administrator\.openclaw\workspace
git status
```

### 【步骤 2: 添加变更】
```bash
# 添加 workspace-investment 所有变更
git add workspace-investment/
```

### 【步骤 3: 提交】
```bash
git commit -m "优化 workspace-investment 结构

- 新增 memory/ 记忆系统 (L1-L4 四层架构)
- 新增 docs/ 文档归档目录
- 整理 data/knowledge_cards/ (67 个文件分类)
- 移动核心配置到 memory/L2-核心/
- 移动报告文档到 docs/
- 删除空目录 (4 个)
- 统一 outputs/ 输出目录
- 创建 L1 投资日志模板
- 创建投资规则文档
- 创建 API 使用指南

投资分析系统结构优化完成。"
```

### 【步骤 4: 推送】
```bash
git push
```

---

## 🎯 提交检查清单

- [ ] 确认所有文件已正确移动
- [ ] 确认 memory/ 结构完整
- [ ] 确认 docs/ 归档完整
- [ ] 确认空目录已删除
- [ ] 确认配置文件在正确位置
- [ ] 运行测试脚本验证功能

---

## 📋 提交后验证

### 【1. 检查文件结构】
```bash
tree workspace-investment -L 2
```

### 【2. 验证关键文件】
- [ ] `memory/L2-核心/MEMORY.md` 存在
- [ ] `memory/L1-日志/2026-04-07.md` 存在
- [ ] `config/eastmoney_cookie.json` 存在
- [ ] `config/stock_pool.json` 存在

### 【3. 测试数据获取】
```bash
python workspace-investment/src/data_fetchers/tencent_realtime.py
```

---

## ⚠️ 注意事项

1. **大文件**: knowledge_cards/ 有 67 个文件，提交可能较慢
2. **编码**: 确保所有文件 UTF-8 编码
3. **路径**: Windows 路径使用反斜杠

---

_提交指南创建时间：2026-04-07 12:58_
