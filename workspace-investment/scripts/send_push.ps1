$body = Get-Content 'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\push_msg.json' -Raw
$result = Invoke-RestMethod -Uri 'http://127.0.0.1:18789/api/message/send' -Method POST -ContentType 'application/json' -Headers @{'Authorization'='Bearer c321e1637183245af253b8bc817822170c1c65454627558c'} -Body $body
Write-Host $result
