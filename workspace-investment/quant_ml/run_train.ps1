# ML训练启动脚本 - 无超时后台运行
$ErrorActionPreference = 'Stop'
$workspace = "C:\Users\Administrator\.openclaw\workspace\workspace-investment"
$logFile = "$workspace\quant_ml\logs\quant_ml_v1\train_bg.log"

$python = python
$trainer = "$workspace\quant_ml\src\training\trainer.py"

# 启动训练进程（-u = unbuffered输出，-b = batchmode）
$proc = Start-Process -FilePath $python -ArgumentList "-u", $trainer -WorkingDirectory $workspace -PassThru -NoNewWindow -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err"

$msg = "$(Get-Date -Format 'HH:mm:ss') 训练已启动 PID=$($proc.Id)"
Write-Output $msg

# 等待进程结束（最多90分钟）
$exited = $proc.WaitForExit(5400000)
if ($exited) {
    $msg = "$(Get-Date -Format 'HH:mm:ss') 训练完成退出码=$($proc.ExitCode)"
} else {
    $proc.Kill()
    $msg = "$(Get-Date -Format 'HH:mm:ss') 训练超时50分钟已终止"
}
Write-Output $msg

# 读取结果
$resultsFile = "$workspace\quant_ml\logs\quant_ml_v1\results.json"
if (Test-Path $resultsFile) {
    $content = Get-Content $resultsFile -Raw
    Write-Output "RESULTS:$content"
} else {
    Write-Output "RESULTS:null"
}