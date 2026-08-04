# Field Manual

Đây là kinh nghiệm thực chiến khi khôi phục VcamLumiere/VcamPlus.

## Sơ đồ hệ thống

```text
iPhone DEB UI
  -> HTTPS backend /vcam/login, /vcam/verify
  -> ghi prefs RTMP
  -> bật LIVE

Windows relay.exe
  -> login backend /vcam/relay_login
  -> nhận OBS RTMP tại TCP :1935
  -> cung cấp/biến đổi stream cho iPhone

OBS
  -> publish RTMP vào Windows relay

iPhone daemon
  -> mediaserverd inject
  -> đọc RTMP URL
  -> nhận stream
  -> đưa frame vào camera ảo
```

## Debug đúng tầng

Luôn đi theo thứ tự:

1. Backend/DNS/TLS.
2. Login/verify.
3. Relay process + port `1935`.
4. OBS publish.
5. iPhone thấy RTMP URL.
6. iPhone kết nối tới Windows.
7. Camera nhận frame.
8. Runtime ổn định/respring.

## Bẫy hay gặp

### Bẫy 1: tưởng lỗi DEB nhưng thật ra firewall

Nếu menu không hiện `rtmp://.../live`, nguyên nhân thường là Windows firewall hoặc relay chưa listen `1935`.

### Bẫy 2: tưởng lỗi crypto khi iPhone chưa connect

Không phân tích AES/codec khi chưa chứng minh iPhone đã kết nối tới Windows `:1935`.

### Bẫy 3: OBS nhập sai

Nếu OBS dùng URL:

```text
rtmp://192.168.2.144/live
```

thì Stream Key nên để trống.

### Bẫy 4: relay chạy từ thư mục khác

Windows firewall có thể allow theo path. Nếu khách chạy relay từ `Downloads` hôm nay, ngày mai copy sang thư mục khác, firewall rule cũ có thể không khớp.

Khuyến nghị:

```text
C:\VcamPlusRelay
```

### Bẫy 5: menu mở trước relay

Nếu mở menu trước khi relay sẵn sàng, menu có thể chưa thấy RTMP. Cách xử lý: hide menu, mở lại, hoặc restart relay.

## Kết luận đúng

- UI không login: backend/signature/account.
- UI login nhưng không thấy RTMP: relay/firewall/LAN.
- Có RTMP nhưng không frame: OBS/iPhone connection/injection.
- Có frame rồi văng: runtime verify, mediaserverd, tweak compatibility, CPU/codec.



