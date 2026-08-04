# Troubleshooting: Respring or Safe Mode

## Triệu chứng

- Mở menu respring.
- Login respring.
- Bật LIVE respring.
- Treo vài phút rồi respring.
- Vào Safe Mode.

## Phân tầng

### Respring khi mở menu

Khả năng cao ở UI/SpringBoard dylib:

- Patch string sai length.
- Patch metadata/UI sai offset.
- Hook UI crash.

### Respring khi bật LIVE

Khả năng ở daemon/mediaserverd:

- RTMP/packet/codec.
- Verify/revoke.
- Hook camera pipeline.

### Respring khi attach Frida

Có thể do Frida/hook làm thiết bị quá tải hoặc đụng process nhạy.

## Cách xử lý

1. Dừng Frida.
2. Gỡ bản lỗi.
3. Cài baseline known-good.
4. Test từng stage.
5. Chỉ patch thêm một thay đổi mỗi lần.

## Cần log

```sh
log stream --predicate 'process == "SpringBoard" OR process == "mediaserverd"'
```

Nếu thiết bị không đủ quyền log do RootHide/Bootstrap, dùng syslog/crash reporter có sẵn.



