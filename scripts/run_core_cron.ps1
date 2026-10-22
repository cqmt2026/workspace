# OpenClaw 核心Cron任务执行脚本
$scripts = "C:\Users\Administrator\.openclaw\scripts"

Write-Host "=== OpenClaw Core Cron Execution ===" -ForegroundColor Cyan
Write-Host "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "脚本目录: $scripts" -ForegroundColor Gray

$tasks = @(
    @{Name = "core-fix-check"; Script = "oc_fix.py"; Args = "all"},
    @{Name = "core-experience-learning"; Script = "error_pattern_detector.py"; Args = ""},
    @{Name = "core-tool-validation"; Script = "tool_validator.py"; Args = ""},
    @{Name = "core-task-inference"; Script = "timing_logger.py"; Args = ""}
)

foreach ($task in $tasks) {
    Write-Host "`n[$($task.Name)] 运行..." -ForegroundColor Yellow
    $fullPath = Join-Path $scripts $task.Script
    $command = "python `"$fullPath`""
    if ($task.Args) { $command += " $($task.Args)" }
    
    try {
        $output = Invoke-Expression $command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK" -ForegroundColor Green
        } else {
            Write-Host "  FAILED (code: $LASTEXITCODE)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
