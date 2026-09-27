# L1自检监控脚本修复

**日期**: 2026-09-06
**问题**: `self_heal_l1.py` 存在死代码，`check_orphan_runs()` 后多出一段无法执行的代码
**修复**: 创建 `l1_check_v2.py` 替代版本，修复路径问题并完善逻辑
**验证**: 运行正常，PASS

## 原脚本问题

1. `check_orphan_runs()` 函数末尾有 `return 1`，导致函数后代码（task_name = sys.argv[1]...）永远无法执行
2. `subprocess.run(['openclaw', ...])` 在Windows Python中找不到openclaw命令
3. KNOWN_ISSUES集合为空，无法过滤已知问题

## 修复方案

- 重写为 `l1_check_v2.py`，使用 `cmd /c "openclaw.cmd cron list --json"` 调用
- 修复死代码问题
- 补充KNOWN_ISSUES配置
- 增加熔断器状态检查

## 状态

- 原脚本仍可用（通过run_with_log包装），但监控效果受限
- 建议后续替换cron payload中的脚本路径
