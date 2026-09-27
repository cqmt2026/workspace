$procs = Get-Process python -ErrorAction SilentlyContinue
$procs | Select Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,0)}} | Format-Table -AutoSize