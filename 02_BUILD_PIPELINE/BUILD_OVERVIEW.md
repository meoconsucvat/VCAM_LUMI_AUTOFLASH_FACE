# Build Overview

Một build khách chuẩn gồm 5 nhóm output:

```text
01_CLIENT_DEB/
02_WINDOWS_RELAY/
03_BACKEND_SERVER/
04_MANIFESTS/
05_CUSTOMER_PACKAGE/
```

## Input cần có

- DEB baseline từ `07_REAL_REFERENCES_SANITIZED/baseline_reference/` (hash `5a641447...`).
- Relay baseline cùng thư mục (hash `83230cc0...`).
- Backend source/template (`backend_reference/` hoặc copy vào project khách).
- Safe patch tools (`tools_reference/02_TOOLS/patchers_safe/`).
- Customer profile (URL 27 bytes, brand 18-byte marker, VPS, bot, device).
- Domain DNS đã trỏ VPS.
- VPS SSH.
- Bot token/admin ID.

Không dùng `official_artifacts_reference/` làm input patch cho khách mới.

## Output tối thiểu

- DEB final.
- Relay zip final.
- Backend deployed trên VPS.
- Bot Telegram chạy.
- Manifest SHA256.
- Customer README.
- Final report.

## Gate trước khi chốt

Không được gọi là done nếu thiếu một trong các test:

1. `/health` OK.
2. Bot `/status` hoặc nút status OK.
3. Login iPhone OK.
4. Relay login OK.
5. iPhone dò được RTMP.
6. OBS publish OK.
7. Camera nhận luồng.
8. Treo vài phút không respring/safemode.



