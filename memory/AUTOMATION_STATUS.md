# 自动化配置状态

**配置时间**: 2026-04-06 15:56  
**状态**: ✅ 已完成

---

## 📋 Cron 任务列表（7 个）

| ID | 任务名称 | 频率 | 时间 | 下次运行 | 状态 |
|----|---------|------|------|---------|------|
| 60af4ed8 | 主系统-Token 监控 | 每 30 分钟 | - | 30 分钟后 | ✅ |
| 9b2fa608 | 主系统-L1 日志 | 每天 | 09:00 | 明天 09:00 | ✅ |
| 8cfa3dce | 创作系统 - 自动备份 | 每天 | 23:00 | 今天 23:00 | ✅ |
| 8e8dc542 | 项目一-L1 日志 | 每天 | 09:00 | 明天 09:00 | ✅ |
| 1d4987ba | 项目一 - 自动备份 | 每天 | 23:00 | 今天 23:00 | ✅ |
| 03c08965 | 项目二-L1 日志 | 每天 | 09:00 | 明天 09:00 | ✅ |
| 25345cdb | 项目二 - 自动备份 | 每天 | 23:00 | 今天 23:00 | ✅ |

---

## 📂 自动化脚本

### 主系统 (workspace/)
- `scripts/auto_summary.py` - L1 日志自动创建
- `scripts/auto_backup_main.py` - 配置文件自动备份

### 创作系统
- `L1-日志/scripts/auto_backup.py` - 正文章节自动备份
- `L1-日志/scripts/auto_daily_log.py` - L1 日志自动创建
- `L1-日志/scripts/auto_learning.py` - 自动学习
- `L1-日志/scripts/ml_daily_optimizer.py` - ML 优化

### 项目一：鉴城师
- `scripts/auto_backup.py` - 章节自动备份
- `scripts/auto_daily_log.py` - L1 日志自动创建

### 项目二：旧城改造
- `scripts/auto_backup.py` - 项目文件自动备份
- `scripts/auto_daily_log.py` - L1 日志自动创建

---

## ⚙️ 自动化行为

### 每 30 分钟
- ✅ 检查 Token 使用量
- ✅ 超过 80% 提醒用户
- ✅ 超过 95% 建议立即压缩

### 每天 09:00
- ✅ 创建主系统 L1 日志
- ✅ 创建项目一 L1 日志
- ✅ 创建项目二 L1 日志

### 每天 23:00
- ✅ 备份创作系统正文
- ✅ 备份项目一章节到 L5-archive
- ✅ 备份项目二文件到 L5-archive

---

## 📊 备份策略

| 系统 | 备份目标 | 保留策略 |
|------|---------|---------|
| 主系统 | `backup/workspace/backup_YYYYMMDD_HHMMSS/` | 每次备份新建子目录 |
| 创作系统 | `创作系统/backup/backup_YYYYMMDD_HHMMSS/` | 每次备份新建子目录 |
| 项目一 | `项目一：鉴城师/L5-archive/backup_YYYYMMDD_HHMMSS/` | 每次备份新建子目录 |
| 项目二 | `项目二：旧城改造/L5-archive/backup_YYYYMMDD_HHMMSS/` | 每次备份新建子目录 |

---

## 🔧 管理命令

```bash
# 查看 Cron 任务
openclaw cron list

# 手动触发任务
openclaw cron run <job-id>

# 禁用任务
openclaw cron update <job-id> --enabled=false

# 查看任务历史
openclaw cron runs <job-id>
```

---

## ⚠️ 注意事项

1. **Cron 任务依赖 Gateway 运行** - 确保 Gateway 服务正常
2. **备份不删除旧文件** - 定期手动清理旧备份
3. **Token 监控通过 HEARTBEAT 触发** - 需要会话活跃
4. **L1 日志每天只创建一次** - 已存在则跳过

---

_由 可悦🌸 配置于 2026-04-06_
