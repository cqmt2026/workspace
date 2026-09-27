# Session State

Last updated: 2026-08-14 21:56:52 (Asia/Shanghai)

## Status: ACTIVE

### 当前运行信息
- **Gateway uptime**: 正常
- **System uptime**: 正常
- **Model**: minimax-portal/MiniMax-M2.7
- **Context**: 0/1.0m (0%)
- **Session**: cron Token-Monitor refresh
- **Route**: WeChat (openclaw-weixin)

### 告警记录 (2026-08-14 21:56:52)
- **[SESSION CRITICAL]** session-state.md 超过9小时未刷新
- **根因**: Session-State-Backup cron任务不存在
- **修复**: 需要创建 Session-State-Backup cron任务

### Cron 任务状态
| 任务 | 状态 | 说明 |
|------|------|------|
| Token-Monitor | ⚠️ 超时 | 最后运行超时94s |
| Session-State-Backup | ❌ 不存在 | 需创建 |

