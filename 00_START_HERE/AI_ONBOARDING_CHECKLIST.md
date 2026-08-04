# AI Onboarding Checklist (minimum viable understanding)

AI mới **tự chấm** trước khi build khách. Chưa pass đủ thì chưa patch/deploy.

## Baseline & artifacts

- [ ] 1. Biết DEB baseline path + SHA256 `5a641447...`
- [ ] 2. Biết relay baseline path + SHA256 `83230cc0...`
- [ ] 3. Biết DEB/relay Kimiki final chỉ **reference-only**, không gửi khách nguyên
- [ ] 4. Biết copy baseline sang project khách, không patch trong handoff

## Identity

- [ ] 5. Base URL phải đúng **27** UTF-8 bytes: `https://` + host(14) + `/vcam`
- [ ] 6. Công thức: `len(host) == 14`
- [ ] 7. UI marker **18** bytes, pad space; tham gia HMAC qua `code_hash`
- [ ] 8. Backend `VCAM_CODE_MARKERS` phải accept marker của DEB
- [ ] 9. Ed25519 private chỉ trên VPS; public + SPKI pin trong identity JSON

## Crypto / API

- [ ] 10. Payload: `v3:{METHOD}:{path}:{ts}:{nonce}:{fp}:{code_hash}:{raw_body}`
- [ ] 11. Path signed = `request.url.path` sau `removeprefix("/vcam")` → `/login` không phải `/vcam/login`
- [ ] 12. Verify HMAC trên **raw body**, không re-serialize JSON
- [ ] 13. Endpoints: `/health`, `/vcam/login|verify|logout|relay_login|stream_key` (+ pair)
- [ ] 14. `bad_signature` → capture + offline offline trước; không tạo/xoá user

## Patch

- [ ] 15. Chỉ dùng `patchers_safe/*`
- [ ] 16. Cấm `legacy_dangerous/patch_kimiki_identity_v22031.py` (Safe Mode evidence)
- [ ] 17. No-red offsets chỉ cho **2.2.031**; old bytes mismatch → stop
- [ ] 18. Mỗi bước: input hash, output hash, manifest

## Runtime / package

- [ ] 19. RTMP = Windows `relay.exe` LAN `:1935`, không VPS; OBS `rtmp://IP/live` + stream key trống
- [ ] 20. Customer package chỉ: DEB + relay zip + README + SHA256SUMS (không secret)

## Gate

Nếu thiếu bất kỳ mục identity/crypto/baseline → **hỏi / đọc reference**, không đoán.

Nếu thiếu domain/VPS/bot/device của khách → **hỏi profile**, không bịa.
