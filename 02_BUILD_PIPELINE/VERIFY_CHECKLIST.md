# Verify Checklist

## Static verify

- [ ] DEB output có SHA256.
- [ ] Relay output có SHA256.
- [ ] Manifest ghi input/output.
- [ ] Patch đúng slice arm64.
- [ ] Patch đúng slice arm64e nếu universal.
- [ ] Không đổi ngoài vùng dự kiến.
- [ ] Metadata Sileo đúng.
- [ ] Brand/contact đúng.
- [ ] Watermark policy đúng theo yêu cầu khách.

## Backend verify

- [ ] DNS trỏ đúng VPS.
- [ ] HTTPS certificate OK.
- [ ] `/health` OK.
- [ ] Backend service active.
- [ ] Bot service active.
- [ ] Tạo user test được.
- [ ] Login iPhone không `bad_signature`.
- [ ] Sai pass trả lỗi đúng.
- [ ] User hết hạn trả lỗi đúng nếu project yêu cầu.

## Relay verify

- [ ] Relay mở được trên Windows.
- [ ] Relay login OK.
- [ ] TCP `:1935` LISTEN.
- [ ] Firewall rule cho `1935` OK.
- [ ] Relay path cố định.

## OBS verify

- [ ] OBS URL đúng `rtmp://<windows-ip>/live`.
- [ ] Stream Key trống nếu URL đã có `/live`.
- [ ] OBS Start Streaming không báo lỗi.

## iPhone verify

- [ ] Menu mở không respring.
- [ ] Login OK.
- [ ] Menu hiện RTMP URL.
- [ ] Bật LIVE OK.
- [ ] Camera nhận luồng.
- [ ] Flash OK nếu cần.
- [ ] Treo vài phút không văng.



