# Release Checklist

Trước khi bàn giao khách:

## Artifact

- [ ] DEB final nằm trong customer package.
- [ ] Relay zip final nằm trong customer package.
- [ ] `SHA256SUMS.txt` có đủ hash.
- [ ] README khách có hướng dẫn cài.
- [ ] Không có secret/token/private key.

## Test

- [ ] Test trên ít nhất một iPhone thật.
- [ ] Test login.
- [ ] Test relay.
- [ ] Test OBS.
- [ ] Test Camera.
- [ ] Test restart relay.
- [ ] Test reboot/respring nếu cần.

## Báo cáo

- [ ] Ghi domain.
- [ ] Ghi VPS service name.
- [ ] Ghi bot admin.
- [ ] Ghi user/pass test.
- [ ] Ghi lỗi còn tồn tại nếu có.

## Rollback

- [ ] Giữ DEB baseline.
- [ ] Giữ relay baseline.
- [ ] Giữ backend backup.
- [ ] Có hướng dẫn rollback.



