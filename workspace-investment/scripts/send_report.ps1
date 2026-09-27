$ErrorActionPreference = "Stop"
$MsgFile = "C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\daily_decision_latest.txt"
$Openclaw = "C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"
$Target = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"

$msg = Get-Content $MsgFile -Raw -Encoding UTF8
Write-Host "Message length: $($msg.Length)"
Write-Host "OpenClaw path: $Openclaw"
Write-Host "Exists: $(Test-Path $Openclaw)"

$success = $false
for ($i = 0; $i -lt 3; $i++) {
    try {
        $proc = Start-Process -FilePath $Openclaw -ArgumentList "message", "send", "--target", $Target, "--message", $msg -Wait -PassThru
        Write-Host "Exit code: $($proc.ExitCode)"
        if ($proc.ExitCode -eq 0) {
            Write-Host "SUCCESS"
            $success = $true
            break
        }
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "Error: $_"
        Start-Sleep -Seconds 2
    }
}

if (-not $success) {
    Write-Host "FAILED after 3 attempts"
    exit 1
}
