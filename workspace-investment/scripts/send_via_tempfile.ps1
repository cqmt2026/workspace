param($MsgFile, $Target, $Openclaw)

$ErrorActionPreference = "Continue"
$msg = Get-Content $MsgFile -Raw -Encoding UTF8
Write-Host "Msg length: $($msg.Length)"

for ($i = 0; $i -lt 3; $i++) {
    try {
        $tmpPs1 = [System.IO.Path]::GetTempFileName() + ".ps1"
        $script = @"
`$msg = [System.IO.File]::ReadAllText($('$MsgFile'.Replace('\','\\').Replace("'",'\'')), [System.Text.Encoding]::UTF8)
`$target = $'$Target'
`$oc = $'$Openclaw'
`$proc = Start-Process -FilePath `$oc -ArgumentList "message", "send", "--target", `$target, "--message", `$msg -Wait -PassThru
Write-Host "Exit: $($proc.ExitCode)"
if (`$proc.ExitCode -eq 0) { exit 0 }
"@
        $script | Set-Content -Path $tmpPs1 -Encoding UTF8
        $result = powershell -ExecutionPolicy Bypass -File $tmpPs1 2>&1
        Write-Host "Result: $result"
        Remove-Item $tmpPs1 -Force -ErrorAction SilentlyContinue
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS"
            exit 0
        }
    } catch {
        Write-Host "Error: $_"
    }
    Start-Sleep -Seconds 2
}
Write-Host "FAILED"
exit 1
