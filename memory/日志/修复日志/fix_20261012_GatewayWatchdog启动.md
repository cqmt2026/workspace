# 修复日志：Gateway Watchdog启动

## 执行时间
2026-10-12 22:04

## 执行命令

### 1. 创建Scheduled Task
```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\Users\Administrator\.openclaw\scripts\gateway_watchdog.cmd"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
```

### 2. 启动任务
```powershell
Start-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog"
```

---

## 验证结果

| 检查项 | 状态 |
|--------|------|
| 任务创建 | ✅ 成功 |
| 任务启动 | ✅ 成功 |
| Gateway健康 | ✅ 正常 |

---

## 功能说明

Gateway Watchdog每5分钟检查一次：
1. 检查18789端口是否监听
2. 如未监听，自动重启Gateway
3. 记录日志到`logs/gateway_watchdog.log`

---

## 管理命令

```powershell
# 查看任务状态
Get-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" | Get-ScheduledTaskInfo

# 手动运行
Start-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog"

# 查看日志
Get-Content C:\Users\Administrator\.openclaw\logs\gateway_watchdog.log -Tail 20

# 禁用任务
Disable-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog"

# 启用任务
Enable-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog"

# 删除任务
Unregister-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" -Confirm:$false
```

---

执行人：可悦（主Agent）
