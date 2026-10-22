# OpenClaw 启动时自动修复 Cron 路径
$scripts = "C:\Users\Administrator\.openclaw\scripts"
$workspace = "C:\Users\Administrator\.openclaw\workspace"

Write-Host "=== OpenClaw Cron 路径修复 ===" -ForegroundColor Cyan
Write-Host "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

$fixes = @(
    @{Id = "5a5b3b49-f2ad-4880-bacc-ca3cabca1e36"; Cmd = "python $scripts\oc_fix.py all"},
    @{Id = "fdbfaa15-e02b-4d4a-8cc6-1d2cf08aafc0"; Cmd = "python $scripts\error_pattern_detector.py"},
    @{Id = "cb33b826-3588-4d4a-8e15-5218e38d2065"; Cmd = "python $scripts\tool_validator.py"},
    @{Id = "853976c6-126c-4cef-aa5d-e6ba5929cbda"; Cmd = "python $scripts\timing_logger.py"}
)

foreach ($fix in $fixes) {
    Write-Host "`n修复: $($fix.Id.Substring(0,8))..." -ForegroundColor Yellow
    try {
        $result = openclaw cron edit $fix.Id --command $fix.Cmd --command-cwd $workspace 2>&1
        if ($result -match "ok|updated|success|id:") {
            Write-Host "  OK" -ForegroundColor Green
        } else {
            Write-Host "  Need check: $($result -join ' ')" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  FAILED: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
