# Troubleshooting: bad_signature

## Triệu chứng

iPhone popup:

```text
bad_signature
```

Backend log:

```text
request_signature_rejected
HTTP 401
```

## Không làm vội

- Không tạo/xoá user.
- Không đổi password.
- Không patch relay.
- Không kết luận account sai.

## Cần thu thập

```text
Request path
X-Timestamp
X-Nonce
X-Signature
Content-Type
raw_body exact bytes
backend log quanh thời điểm login
DEB SHA256 đang cài
backend commit/source đang chạy
```

## Kiểm tra

1. Client đang gọi đúng domain chưa.
2. Path đúng `/vcam/login` hay path khác.
3. Backend verify HMAC đúng raw body chưa.
4. Bootstrap secret/client marker đúng chưa.
5. DEB và backend có cùng identity không.

## Kết luận

Chỉ kết luận fix xong khi cùng request capture tạo được signature khớp `X-Signature`.



