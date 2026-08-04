# Troubleshooting: Camera Black Screen

## Triệu chứng

- Menu có RTMP URL.
- LIVE bật.
- Camera mở nhưng không có hình.

## Debug thứ tự

1. OBS đã Start Streaming chưa.
2. OBS URL đúng chưa.
3. Relay log có publisher connected không.
4. Windows có connection từ iPhone tới `:1935` không.
5. iPhone daemon có inject vào `mediaserverd` không.
6. Sau cùng mới kiểm tra codec/crypto.

## Windows check

```powershell
netstat -ano | findstr :1935
```

Tìm connection từ IP iPhone.

## OBS

URL:

```text
rtmp://<windows-ip>/live
```

Stream Key: trống.

## Không làm

Không patch AES/decoder khi iPhone chưa connect.



