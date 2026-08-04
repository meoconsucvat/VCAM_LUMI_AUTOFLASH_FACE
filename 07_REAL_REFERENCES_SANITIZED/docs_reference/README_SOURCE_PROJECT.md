# VcamLumierePhan / Kimiki

Đây là project khôi phục và đóng gói VcamLumiere cho backend `kimiki.bond`, gồm 4 phần chính:

- DEB iOS đã patch identity/server/metadata/UI/no-red watermark.
- Windows relay package dùng cho OBS RTMP LAN.
- Backend + Telegram admin bot.
- Bộ tool patch/reverse để build lại khi đổi domain, VPS, brand hoặc khách hàng mới.

## Bản đang dùng chính thức

Nguồn sự thật hiện tại nằm trong:

```text
00_ACTIVE/
```

DEB chính thức:

```text
00_ACTIVE/deb/com.lumiere.vcamlumiere_2.2.031_kimiki_universal_safe_vcamplus_metadata_ui_marker_vcamplus_nored_test.deb
```

Relay chính thức:

```text
00_ACTIVE/relay/VCam_Kimiki_Windows_Relay_safe_vcamplus_contact_clean.zip
```

Chi tiết hash, manifest và trạng thái test nằm ở:

```text
docs/CURRENT_ARTIFACTS.md
```

## Không dùng nhầm

Các thư mục/file cũ ở root đã được dọn khỏi root và đưa vào archive cleanup. Không dùng artifact trong archive để gửi khách nếu chưa đối chiếu lại manifest/hash.

Archive cleanup gần nhất:

```text
04_ARCHIVE/root_cleanup_20260804-173057/
```

Các stage build cũ cũng đã có bản copy trong:

```text
04_ARCHIVE/build_stages/
```

Script legacy cần tránh dùng trực tiếp:

```text
02_TOOLS/legacy_dangerous/patch_kimiki_identity_v22031.py
```

Khi build bản mới, ưu tiên các script trong:

```text
02_TOOLS/patchers_safe/
```

Backend source đang dùng nằm ở:

```text
01_SERVER/backend/
```

## Tài liệu nên đọc

- `docs/CURRENT_ARTIFACTS.md`: bản nào đang là official.
- `docs/PROJECT_STRUCTURE.md`: cấu trúc thư mục.
- `docs/BUILD_AND_PATCH_GUIDE.md`: quy trình build/patch an toàn.
- `docs/SERVER_RUNBOOK.md`: vận hành backend/VPS/bot.
- `docs/CUSTOMER_SETUP.md`: hướng dẫn gửi khách dùng relay + DEB.
- `docs/CLEANUP_LOG.md`: lịch sử dọn root và nơi lưu bản cũ.

