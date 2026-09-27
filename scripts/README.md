# scripts/

自动化脚本目录

## sync-to-obsidian.ps1

bank/ → Obsidian Vault 自动同步脚本

**同步映射：**
- `bank/` → `02-知识库/`
- `insights/` → `02-知识库/`
- `decisions/` → `03-项目/贾维斯系统/`

**使用方式：**
```powershell
# 干跑（不实际复制）
.\sync-to-obsidian.ps1 -DryRun

# 正式同步
.\sync-to-obsidian.ps1
```

**每日自动：**
配合 Windows 任务计划程序，设置为每日 22:00 执行。
