# Known Failures and Fixes

## bad_signature

Triệu chứng:

```text
Popup: bad_signature
Backend log: request_signature_rejected
HTTP 401
```

Nguyên nhân thường gặp:

- Backend signature format không khớp client.
- Path sai: signed path phải là `/login` (strip `/vcam`), không dùng `/vcam/login` trong HMAC.
- Body bị serialize lại thay vì dùng raw bytes.
- Secret/client marker sai — đổi UI marker 18-byte mà `VCAM_CODE_MARKERS` chưa accept.
- DEB/relay chưa patch cùng identity với backend.
- Base URL client không đúng 27 bytes / patch identity lệch.

Cách xử lý:

1. Capture request thật.
2. Lấy `X-Timestamp`, `X-Nonce`, `X-Signature`, raw body.
3. So sánh với `vcam_crypto.py`.
4. Không sửa account/user trước khi signature pass.

## invalid_credentials

Triệu chứng:

```text
Popup: invalid_credentials
```

Nguyên nhân:

- Sai user/pass.
- User chưa tồn tại.
- User expired/disabled/locked.
- Device limit policy đang chặn.

Cách xử lý:

1. Kiểm tra user bằng bot/DB.
2. Kiểm tra password hash.
3. Kiểm tra hạn.
4. Kiểm tra device binding.

## Không dò được RTMP

Triệu chứng:

```text
Menu hiển thị: Không tìm thấy, nhập RTMP tay
```

Nguyên nhân:

- relay.exe chưa chạy.
- port `1935` không listen.
- Windows firewall.
- Windows network profile Public.
- iPhone/Windows khác LAN.
- relay chạy từ path khác.
- menu chưa refresh.

Cách xử lý: xem `05_TROUBLESHOOTING/RTMP_NOT_FOUND.md`.

## Camera đen

Triệu chứng:

```text
Menu có RTMP, bật LIVE nhưng Camera không lên frame.
```

Nguyên nhân:

- OBS chưa Start Streaming.
- OBS URL/key sai.
- iPhone chưa connect tới relay.
- daemon chưa inject vào mediaserverd.
- codec/packet không khớp.

Không debug codec trước khi có bằng chứng iPhone đã connect.

## Respring / Safe Mode

Triệu chứng:

```text
Mở menu hoặc bật LIVE thì respring/safemode.
```

Nguyên nhân có thể:

- Patch UI sai offset/string length.
- Dylib không tương thích thiết bị/jailbreak.
- Hook trong SpringBoard/mediaserverd crash.
- Frida/hook debug gây quá tải.
- Runtime verify/revoke path gọi stop/kill.

Cách xử lý:

1. Gỡ bản patch lỗi, cài baseline known-good.
2. Test menu trước.
3. Test login.
4. Test relay.
5. Test LIVE.
6. Patch lại theo stage nhỏ, mỗi stage test riêng.



