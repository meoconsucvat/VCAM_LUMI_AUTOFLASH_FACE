# Build and Patch Guide

Tài liệu này dành cho lần sau khi cần đổi domain, VPS, brand hoặc build cho khách mới.

## Nguyên tắc

1. Không patch trực tiếp file gốc.
2. Luôn lưu SHA256 input/output.
3. Luôn verify manifest sau patch.
4. Không trộn identity cũ và backend mới.
5. Không dùng script legacy nếu đã có safe script.

## Input nên dùng

Baseline gốc:

```text
03_BASELINE/original_deb/com.lumiere.vcamlumiere_universal-Update.deb
```

Backend source hiện tại:

```text
01_SERVER/backend/
```

Tool patch an toàn:

```text
02_TOOLS/patchers_safe/
```

## Thứ tự patch khuyến nghị

1. Patch identity/server bằng safe patcher.
2. Patch metadata Sileo nếu cần đổi tên hiển thị.
3. Patch relay contact/server tương ứng.
4. Patch UI marker nếu đổi brand trong menu.
5. Patch no-red watermark.
6. Rebuild DEB.
7. Tạo customer package.
8. Hash toàn bộ artifact.
9. Test trên thiết bị thật.

## Script an toàn

```text
02_TOOLS/patchers_safe/patch_kimiki_identity_v22031_safe.py
02_TOOLS/patchers_safe/brand_metadata_relay_only.py
02_TOOLS/patchers_safe/patch_ui_brand_v22031_safe.py
02_TOOLS/patchers_safe/patch_nored_watermark_v22031.py
```

## Script legacy cần tránh

```text
02_TOOLS/legacy_dangerous/patch_kimiki_identity_v22031.py
```

Không dùng script này cho build mới nếu chưa kiểm chứng lại toàn bộ offset/table.

## Patch no-red watermark đã dùng

Manifest:

```text
00_ACTIVE/manifests/nored_watermark_v22031_manifest.json
```

Các patch quan trọng:

```text
arm64  offset 0xe068   old eb2bbb6d   new c0035fd6
arm64e offset 0x42548  old 7f2303d5   new c0035fd6
```

Ý nghĩa: trả về sớm khỏi block vẽ chữ chạy quanh mép màn hình.

## Điều kiện test trước khi chốt artifact

- Cài DEB bằng Sileo.
- Mở menu không respring/safemode.
- Login thành công.
- Relay login thành công.
- Menu dò được RTMP URL.
- OBS publish vào `rtmp://<windows-lan-ip>/live`.
- Bật LIVE, Camera nhận luồng.
- Treo vài phút không văng.
- Flash hoạt động nếu cần.
- Không xuất hiện watermark đỏ chạy quanh mép màn hình.


