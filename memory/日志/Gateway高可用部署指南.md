# Gateway高可用部署指南

## 当前状态
- Primary Gateway: 127.0.0.1:18789 ✅ 运行中
- Standby Gateway: 127.0.0.1:18790 ❌ 不支持（同配置目录冲突）

## 推荐方案：进程守护

由于OpenClaw Gateway不支持原生多实例HA，采用**进程守护+自动重启**方案：

### 1. 创建Watchdog脚本
文件：`scripts/gateway_watchdog.cmd`
功能：每5分钟检查Gateway进程，崩溃时自动重启

### 2. 配置Windows任务计划
```powershell
# 创建定时任务
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\Users\Administrator\.openclaw\scripts\gateway_watchdog.cmd"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Gateway进程守护，崩溃自动重启"
```

### 3. 启动任务
```powershell
Start-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog"
```

### 4. 验证
```powershell
Get-ScheduledTask -TaskName "OpenClaw-Gateway-Watchdog" | Get-ScheduledTaskInfo
Get-Content C:\Users\Administrator\.openclaw\logs\gateway_watchdog.log -Tail 10
```

---

## 高级方案：真正的HA（需要额外投资）

如需真正的多Gateway HA，需要：

### 架构改造
```
外部请求 → Load Balancer (nginx/HAProxy) → Gateway-Primary:18789
                                              ↓ 故障切换
                                        Gateway-Standby:18790
```

### 所需改动
1. **配置分离**：每个Gateway实例使用独立配置目录
2. **共享存储**：SQLite数据库移至网络共享或主从复制
3. **会话同步**：实现Session复制机制
4. **Load Balancer**：配置nginx/HAProxy健康检查

### 预估工作量
- 开发：3-5天
- 测试：2天
- 运维成本：中等

---

## 建议

**当前阶段**：使用进程守护方案（已创建脚本）
**未来升级**：当系统规模扩大后，考虑真正的HA架构

---

更新时间：2026-10-12 22:05
