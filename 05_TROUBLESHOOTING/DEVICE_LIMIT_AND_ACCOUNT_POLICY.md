# Troubleshooting: Device Limit and Account Policy

## Chính sách phổ biến

- Một user giới hạn tối đa 1 thiết bị.
- User hết hạn thì không login/verify.
- Xoá user phải xoá triệt để hoặc hard delete nếu admin yêu cầu.

## Khi khách muốn không giới hạn máy

Phải sửa policy backend, không patch DEB.

Các điểm cần kiểm tra:

- User table.
- Device/session table.
- Verify endpoint.
- Relay login endpoint.
- Bot command add/del/clear.

## Khi `/del user` vẫn hiện trong list

Có thể bot đang soft-delete/expire thay vì hard-delete.

Nếu yêu cầu xoá triệt để:

- Xoá user row.
- Xoá device bindings.
- Xoá sessions.
- Xoá relay sessions.

Sau đó `/users` không còn thấy user.



