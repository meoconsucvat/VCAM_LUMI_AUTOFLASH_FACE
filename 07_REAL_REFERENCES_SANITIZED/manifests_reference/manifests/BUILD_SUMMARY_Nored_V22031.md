# Build summary — Kimiki safe + VcamPlus + no-red watermark test

Thời điểm build: 2026-08-04

Mục tiêu:

- Kế thừa bản Kimiki safe đã test login/stream ổn.
- Kế thừa Sileo metadata `VcamPlus`.
- Kế thừa relay contact `@vcamplus`.
- Kế thừa UI marker `tele: @vcamplus`.
- Thử tắt dòng chữ đỏ chạy quanh mép màn hình bằng patch block vẽ watermark.

## Artifact chính

| Loại | File | SHA256 |
|---|---|---|
| DEB | `com.lumiere.vcamlumiere_2.2.031_kimiki_universal_safe_vcamplus_metadata_ui_marker_vcamplus_nored_test.deb` | `a94a8464a5370bdbb318ff6b4be672639c26ade4d86424838dccaa0e29c624e1` |

## Bằng chứng patch

Patch cũ của bản 2.1.08 không dùng lại nguyên offset vì bản 2.2.031 đã dịch code.

Patch 2.2.031 đã remap:

| Slice | Thin addr | File offset | Old bytes | New bytes | Ý nghĩa |
|---|---:|---:|---|---|---|
| arm64 | `0xa068` | `0xe068` | `eb2bbb6d` | `c0035fd6` | return khỏi block `imageWithActions/drawAtPoint` |
| arm64e | `0xa548` | `0x42548` | `7f2303d5` | `c0035fd6` | return khỏi block `imageWithActions/drawAtPoint` |

Changed ranges sau build:

```text
0xe068  - 0xe06c   length 4
0x42548 - 0x4254c  length 4
```

## Những gì vẫn giữ

- `Package: com.lumiere.vcamlumiere`
- `Name: VcamPlus`
- UI marker: `tele: @vcamplus   `
- Relay contact: `@vcamplus`
- Domain: `https://vc.kimiki.bond/vcam`
- `VcamLumiereSensor.plist` vẫn còn.

## Trạng thái

Đây là bản test vật lý. Chỉ coi là official sau khi iPhone xác nhận:

1. Mở menu không respring.
2. Login OK.
3. Dòng chữ đỏ chạy quanh mép màn hình biến mất.
4. Relay + OBS + LIVE vẫn lên hình.
5. Treo vài phút không respring/safemode.


