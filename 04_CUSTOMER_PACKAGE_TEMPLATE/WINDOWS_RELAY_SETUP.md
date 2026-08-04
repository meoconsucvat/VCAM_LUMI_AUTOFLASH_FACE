# Windows Relay Setup

## Thư mục khuyến nghị

```text
C:\VcamPlusRelay
```

Không nên chạy relay từ Telegram Desktop/Downloads vì firewall rule có thể lệch path.

## Mở firewall

PowerShell Run as Administrator:

```powershell
New-NetFirewallRule -DisplayName "VCAM RTMP 1935 TCP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 1935 -Profile Any
New-NetFirewallRule -DisplayName "VCAM Relay Program" -Direction Inbound -Action Allow -Program "C:\VcamPlusRelay\relay.exe" -Profile Any
```

## Kiểm tra relay

```powershell
Get-Process | Where-Object { $_.ProcessName -like "*relay*" }
netstat -ano | findstr :1935
```

## Nếu port bị chiếm

```powershell
netstat -ano | findstr :1935
tasklist /FI "PID eq <PID>"
```

Không kill process nếu chưa biết nó là gì.



