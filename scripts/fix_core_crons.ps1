#!/usr/bin/env pwsh
# Gateway启动后自动修复核心Cron路径配置
# 解决Windows路径被sh -lc错误解析的问题

Write-Host "=== Core Cron Path Fix ===" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$base = "C:\Users\Administrator\.openclaw\scripts"

$fixes = @(
    @{ Id = "5a5b3b49-f2ad-4880-bacc-ca3cabca1e36"; Name = "core-fix-check"; Cmd = "python `"$base\oc_fix.py`" all" },
    @{ Id = "fdbfaa15-e02b-4d4a-8cc6-1d2cf08aafc0"; Name = "core-experience-learning"; Cmd = "python `"$base\error_pattern_detector.py`"" },
    @{ Id = "cb33b826-3588-4d4a-8e15-5218e38d2065"; Name = "core-tool-validation"; Cmd = "python `"$base\tool_validator.py`"" },
    @{ Id = "853976c6-126c-4cef-aa5d-e6ba5929cbda"; Name = "core-task-inference"; Cmd = "python `"$base\timing_logger.py`"" }
)

foreach ($fix in $fixes) {
    Write-Host "Fixing $($fix.Name)... " -NoNewline
    $result = openclaw cron edit $($_.Id) --command $($_.Cmd) 2>&1
    if ($LASTEXITCODE -eq 0 -or $result -match '"ok":true') {
        Write-Host "OK" -ForegroundColor Green
    } else {
        Write-Host "FAILED" -ForegroundColor Red
        Write-Host "  $result" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
