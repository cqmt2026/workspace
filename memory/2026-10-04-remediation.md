# 补救方案：2026-10-04 文件完整性修复

## 时间
2026-10-04 10:18 (GMT+8)

## 问题确认

1. **workspace-math/ 脚本缺失**
   - 现状：只有1个Python脚本
   - 期望：应有几十到几百个（Manim、TTS、合成等）
   - 风险：数学动画无法重新生成

2. **Markdown文件异常**
   - workspace-novel/: 3414个（可能包含日记、日志）
   - workspace-weixin/: 318个
   - 需要确认是否正常

3. **备份过时**
   - 最新备份：2026-06-11（4个月前）
   - 不包含最近4个月的工作成果

## 补救步骤

### 步骤1：检查workspace-math/应有哪些脚本

执行：
```bash
python scripts/check_math_scripts.py
```

目标：
- 列出当前workspace-math/的所有文件
- 检查是否有scripts/子目录（之前报告说有）
- 对比其他子系统（如workspace-maphot有252个py）的规模

### 步骤2：从备份恢复（如有必要）

如果确认脚本缺失：
```bash
# 从6月11日备份恢复（可能不含最新脚本）
python scripts/restore_missing.py
```

### 步骤3：验证Markdown文件

检查异常多的MD文件是否是系统生成的：
```bash
python scripts/check_md_files.py
```

检查：
- 文件内容（是否日记、日志、审计记录）
- 文件命名规则（是否有规律）
- 是否为系统自动生成

### 步骤4：建立文件清单

为每个子系统生成完整文件清单：
```bash
python scripts/generate_inventory.py
```

输出：
- 每个子系统的文件清单（CSV格式）
- 按类型分组统计
- 按日期分组统计

### 步骤5：建立定期备份

创建每日备份任务：
```bash
# 添加到cron
openclaw cron add --name "Daily-Backup" --schedule "0 2 * * *" --command "python scripts/daily_backup.py"
```

## 执行计划

1. **立即执行**：步骤1（检查math脚本）
2. **确认后执行**：步骤2（恢复，如需）
3. **并行执行**：步骤3+4（验证MD+生成清单）
4. **明天执行**：步骤5（建立定期备份）

## 责任归属

- 执行者：可悦
- 监督：主人
- 完成时间：今天内

---

_记录者: 可悦 | 2026-10-04 10:18_
