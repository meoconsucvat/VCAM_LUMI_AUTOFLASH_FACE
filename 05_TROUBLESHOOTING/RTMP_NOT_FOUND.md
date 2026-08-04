# Troubleshooting: RTMP Not Found

## Triệu chứng

Menu iPhone:

```text
Không tìm thấy, nhập RTMP tay
```

## Nguyên nhân cao nhất

Windows relay hoặc firewall, không phải DEB.

## Checklist

### 1. Relay process

```powershell
Get-Process | Where-Object { $_.ProcessName -like "*relay*" } | Select-Object Id,ProcessName,Path
```

### 2. Port 1935

```powershell
netstat -ano | findstr :1935
```

Phải có `LISTENING`.

### 3. IP Windows

```powershell
ipconfig
```

iPhone phải hiện:

```text
rtmp://<windows-ip>/live
```

### 4. Firewall

PowerShell Admin:

```powershell
New-NetFirewallRule -DisplayName "VCAM RTMP 1935 TCP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 1935 -Profile Any
```

### 5. Refresh menu

Nếu mở menu trước relay, hide menu rồi mở lại.

## Kết luận

Chỉ chuyển sang debug DEB nếu:

- relay chạy;
- port `1935` listen;
- firewall OK;
- iPhone cùng LAN;
- OBS đúng;
- menu vẫn không thấy RTMP.



