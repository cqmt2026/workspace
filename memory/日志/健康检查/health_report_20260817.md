# 子系统健康检查报告 2026-08-17 15:21

**Overall: ⚠️ WARN | 1 DOWN + 4 WARN + 1 ERR**

---

## 🚨 问题清单

| # | 级别 | 子系统 | 问题 | 详情 |
|---|------|--------|------|------|
| 1 | 🔴 DOWN | Main | Supermemory 离线 | 端口 8642 拒绝连接 |
| 2 | 🟡 WARN | Main | C盘空间不足 | 13.6GB (18.6%) |
| 3 | 🟡 WARN | Main | Session状态过期 | 最后更新 65.5小时前 |
| 4 | 🟡 WARN | Investment | ML模型缺失 | ml_output_v6 目录不存在 |
| 5 | 🟡 WARN | Social | 近7天零产出 | 0条草稿 |
| 6 | 🟡 WARN | Math | 无 ep_build 脚本 | workspace-math/scripts 无构建脚本 |

---

## ✅ 正常项

| 子系统 | 状态 | 详情 |
|--------|------|------|
| Cron失败 | OK | 今日 0 次 |
| 市场数据 | OK | 最新 2026-08-14（3天前，临界） |
| 小说 | OK | 3章，最新第二章_重生.md |
| 地图热点 | OK | pipeline.py 就绪，13个核心脚本完整 |
| 知识库 | OK | 44KB，669行 |
| Obsidian同步 | OK | 461个文件近2天有修改 |
| 备份执行 | OK | sessions: 2026-08-16 23:00, weekly: 2026-08-16 20:00 |
| 持仓 | OK | 0 holdings（空仓） |

---

## 🔧 分析与建议

### 1. Supermemory 离线（DOWN）🔴
**根因**: 端口 8642 无服务监听
**影响**: 向量检索不可用，依赖Supermemory的子系统全部降级
**建议**:
- 确认服务是否已启动：`netstat -an | findstr 8642`
- 如未启动，检查服务配置并启动
- 如长期不需要，考虑从检查中移除

### 2. C盘空间不足（WARN）
**根因**: 剩余13.6GB（18.6%），低于20%警戒线
**影响**: 系统运行可能受影响，文件写入可能失败
**建议**:
- 清理临时文件和日志
- 检查大文件：`Get-ChildItem C:\ -Recurse -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 20`
- 迁移不常用数据到其他盘

### 3. Session状态过期（WARN）
**根因**: session-state.md 最后写入 65.5小时前（2026-08-14 21:56）
**影响**: 状态同步延迟，但不影响核心功能
**建议**: 检查 session-state 更新机制是否正常

### 4. ML模型缺失（WARN）
**根因**: `ml_output_v6` 目录不存在，ML训练未执行
**影响**: 投资系统缺少ML预测能力
**建议**:
- 检查 quant_ml 目录下的训练脚本（pipeline.py 存在）
- 确认是否需要重新训练模型
- 考虑将检查路径从 ml_output_v6 改为 quant_ml

### 5. 自媒体零产出（WARN）
**根因**: 近7天无草稿活动
**影响**: 内容运营停滞
**建议**: 确认是否有意为之（休息/暂停），或需重新启动

### 6. 数学动画无构建脚本（WARN）
**根因**: workspace-math/scripts 无 ep_build.py 文件
**影响**: 数学动画无法生成
**建议**: 检查 ep_build 脚本是否在其他位置，或是否需要重建

---

## 📊 仪表盘缺失项（建议补充）

当前 dashboard 未检查：
- 地图热点子系统（pipeline.py 存在但未检查）
- 备份执行状态（已确认正常，但未纳入检查）
- Obsidian 同步状态（已确认正常，但未纳入检查）
- 市场数据新鲜度（3天临界，但未计入问题）

建议更新 dashboard v4 覆盖这些项。

---

## 📁 备份状态

| 备份类型 | 最后执行 | 状态 |
|----------|----------|------|
| sessions | 2026-08-16 23:00 | ✅ 正常 |
| weekly | 2026-08-16 20:00 | ✅ 正常 |
| workspace-git | 2026-05-14 17:13 | ⚠️ 过时3个月 |

---

_报告生成时间: 2026-08-17 15:21_
_报告路径: memory/日志/健康检查/health_report_20260817.md_
