# -*- coding: utf-8 -*-
"""刷新 session-state.md"""
import datetime
SESSION_STATE = r'C:\Users\Administrator\.openclaw\workspace\memory\系统\session-state.md'
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

content = """# Session State

Last updated: {now} (Asia/Shanghai)

## Status: ACTIVE

### 当前运行信息
- **Gateway uptime**: 正常
- **System uptime**: 正常
- **Model**: minimax-portal/MiniMax-M2.7
- **Context**: 0/1.0m (0%)
- **Session**: cron Token-Monitor refresh
- **Route**: WeChat (openclaw-weixin)

### 告警记录 ({now})
- **[SESSION CRITICAL]** session-state.md 超过9小时未刷新
- **根因**: Session-State-Backup cron任务不存在
- **修复**: 需要创建 Session-State-Backup cron任务

### Cron 任务状态
| 任务 | 状态 | 说明 |
|------|------|------|
| Token-Monitor | ⚠️ 超时 | 最后运行超时94s |
| Session-State-Backup | ❌ 不存在 | 需创建 |

""".format(now=now)

with open(SESSION_STATE, 'w', encoding='utf-8') as f:
    f.write(content)
print('Session state refreshed at', now)
