# Troubleshooting: Firewall Port 1935

## Triệu chứng

- relay chạy nhưng iPhone không thấy RTMP.
- OBS publish được nhưng iPhone không nhận.
- Khách đổi thư mục relay thì lỗi lại.

## Fix chuẩn

Đặt relay ở:

```text
C:\VcamPlusRelay
```

PowerShell Run as Administrator:

```powershell
New-NetFirewallRule -DisplayName "VCAM RTMP 1935 TCP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 1935 -Profile Any
New-NetFirewallRule -DisplayName "VCAM Relay Program" -Direction Inbound -Action Allow -Program "C:\VcamPlusRelay\relay.exe" -Profile Any
```

## Kiểm tra profile mạng

```powershell
Get-NetConnectionProfile
```

Nếu đang Public, rule Profile Any vẫn giúp tránh lỗi.



