# RTMP Relay OBS Guide

## Luồng đúng

```text
OBS -> Windows relay.exe :1935 -> iPhone menu/daemon -> Camera
```

RTMP chạy trong LAN Windows, không chạy trên VPS trong mô hình này.

## Windows relay

Khuyến nghị đặt relay ở:

```text
C:\VcamPlusRelay
```

Chạy:

```text
relay.exe
```

Nếu relay đã login trước đó, nó có thể tự dùng credential/token đã lưu.

## OBS

Nếu Windows LAN IP là:

```text
192.168.2.144
```

OBS Server/URL:

```text
rtmp://192.168.2.144/live
```

Stream Key:

```text

```

Để trống nếu URL đã có `/live`.

## Kiểm tra port

PowerShell:

```powershell
netstat -ano | findstr :1935
```

Kỳ vọng:

```text
0.0.0.0:1935 LISTENING <PID>
```

## Firewall

PowerShell Admin:

```powershell
New-NetFirewallRule -DisplayName "VCAM RTMP 1935 TCP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 1935 -Profile Any
New-NetFirewallRule -DisplayName "VCAM Relay Program" -Direction Inbound -Action Allow -Program "C:\VcamPlusRelay\relay.exe" -Profile Any
```

## Test end-to-end

1. Mở relay.
2. Mở OBS Start Streaming.
3. Mở menu iPhone.
4. Chờ RTMP URL.
5. Bật LIVE.
6. Mở Camera.



