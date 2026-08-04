param(
    [int]$Port = 1935
)

Write-Host "== VCAM Relay/Port Check =="

Write-Host "`n[1] Relay-like processes:"
Get-Process | Where-Object { $_.ProcessName -match 'relay|vcam|rtmp|mona|media' } |
    Select-Object Id, ProcessName, Path |
    Format-Table -AutoSize

Write-Host "`n[2] TCP connections on port $Port:"
Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess |
    Format-Table -AutoSize

Write-Host "`n[3] netstat fallback:"
netstat -ano | findstr ":$Port"

Write-Host "`n[4] Network profile:"
Get-NetConnectionProfile | Select-Object Name, InterfaceAlias, InterfaceIndex, NetworkCategory |
    Format-Table -AutoSize

Write-Host "`nDone."

