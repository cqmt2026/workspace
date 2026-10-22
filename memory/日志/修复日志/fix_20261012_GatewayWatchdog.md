# 修复日志：Gateway Watchdog部署

## 执行时间
2026-10-12 22:05

## 问题分析

### 原方案：双Gateway实例
- Primary: 端口18789
- Standby: 端口18790

### 发现的问题
OpenClaw Gateway不支持同配置目录多实例运行：
1. SQLite数据库锁冲突
2. 会话状态混乱
3. 配置覆盖风险

---

## 解决方案

### 采用进程守护方案
创建`gateway_watchdog.cmd`脚本：
- 每5分钟检查Gateway进程
- 检测到崩溃时自动重启
- 日志记录到`logs/gateway_watchdog.log`

---

## 已创建文件

| 文件 | 用途 |
|------|------|
| `scripts/gateway_watchdog.cmd` | 进程守护脚本 |
| `gateway_watchdog_config.json` | 配置文件 |
| `memory/日志/Gateway高可用部署指南.md` | 部署文档 |

---

## 下一步操作

### 立即可做
```powershell
# 1. 创建Windows任务计划
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\Users\Administrator\.openclaw\scripts\gateway_watchdog.cmd"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" -Action $action -Trigger $trigger -Force

# 2. 启动任务
Start-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog"

# 3. 验证
Get-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" | Get-ScheduledTaskInfo
```

### 验证方法
```powershell
# 查看日志
Get-Content C:\Users\Administrator\.openclaw\logs\gateway_watchdog.log -Tail 20

# 测试故障切换
# 1. 停止Gateway: taskkill /F /PID 9108
# 2. 等待5分钟
# 3. 检查是否自动重启
```

---

## 局限性说明

进程守护方案 limitations：
1. **切换延迟**：最多5分钟（检查间隔）
2. **状态丢失**：重启期间请求失败
3. **无数据同步**：简单重启，无需复杂同步

对于当前使用规模（单用户）足够满足需求。

---

执行人：可悦（主Agent）
