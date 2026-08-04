# Patch Order

Thứ tự patch khuyến nghị cho project khách mới.

## 0. Chuẩn bị project + baseline

```text
Tạo project khách riêng (không patch trong handoff).
Copy baseline:
  07_REAL_REFERENCES_SANITIZED/baseline_reference/com.lumiere.vcamlumiere_universal-Update.deb
  07_REAL_REFERENCES_SANITIZED/baseline_reference/relay.exe
Verify SHA256:
  DEB   5a641447cdb2b3030f8e531695e647d53e9beeef5e592dbe7f5c84929b0a9efb
  Relay 83230cc05a0544faedbae33ab72abda0c0bafd0d52668e803e5212d5d762384b
Copy tools safe + backend sample vào project khách.
```

## 1. Chốt identity

Từ `CUSTOMER_PROFILE.md`, xác định:

```text
Backend base URL   # đúng 27 UTF-8 bytes
Brand/contact text # UI marker 18 bytes pad space
Telegram bot
Account mặc định
```

Công thức URL:

```text
https://<host>/vcam  =>  len(host) == 14
```

Nếu URL không đúng 27 bytes, **đổi subdomain trước** — không patch.

## 2. Dựng backend trước

Backend phải có:

- `/health`
- `/vcam/login`
- `/vcam/verify`
- `/vcam/logout`
- `/vcam/relay_login`
- `/vcam/stream_key`
- Telegram bot quản lý user.

## 3. Patch DEB + relay identity (safe)

Script:

```text
tools_reference/02_TOOLS/patchers_safe/patch_kimiki_identity_v22031_safe.py
```

Input: identity JSON + baseline DEB + baseline relay.

Patch đồng bộ:

- UI + Daemon, arm64 + arm64e.
- Base URL (27), Ed25519 pub (32), SPKI pins (44).
- Relay URL (+ stub TLS pin nếu dùng `--stub-relay-tls-pin` như Kimiki).

Cấm:

```text
tools_reference/02_TOOLS/legacy_dangerous/patch_kimiki_identity_v22031.py
```

(Evidence: mở menu → SpringBoard Safe Mode.)

## 4. Patch brand / metadata / relay contact

```text
brand_metadata_relay_only.py
```

- Sileo Name/Description/Maintainer/Author.
- Relay contact string (pad length).
- Không copy `relaykey.bin` / log runtime.

## 5. Patch UI marker + watermark (tuỳ policy)

```text
patch_ui_brand_v22031_safe.py   # marker 18 bytes; sync VCAM_CODE_MARKERS
patch_nored_watermark_v22031.py # chỉ 2.2.031; old bytes mismatch → stop
```

## 6. Verify

Mỗi patch phải có:

```text
input hash
output hash
offset
old bytes
new bytes
decode check
```

## 7. Đóng customer package

Package khách nên có:

- DEB.
- Relay zip.
- Customer README.
- SHA256SUMS.

Không có:

- `.pem`
- bot token
- DB production
- relaykey.bin của người khác
- log cá nhân



