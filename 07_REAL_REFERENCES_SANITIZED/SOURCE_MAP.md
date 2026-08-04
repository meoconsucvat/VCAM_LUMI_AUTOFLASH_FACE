# Source Map

Nguồn copy từ project chính (khi còn tồn tại):

```text
C:\Users\Admin\Desktop\Vcam_LumierePhan
```

Handoff **độc lập**: sau khi có `baseline_reference/`, AI trên máy khác không bắt buộc phải mount project chính.

## Mapping

| Trong handoff | Nguồn project chính | Mục đích |
|---|---|---|
| `baseline_reference/*.deb` | `03_BASELINE/original_deb/` | DEB gốc patch |
| `baseline_reference/relay.exe` | `04_ARCHIVE/build_stages/relay/relay.exe` | Relay gốc patch |
| `backend_reference/` | `01_SERVER/backend/` | Backend + bot + crypto |
| `tools_reference/` | `02_TOOLS/` | Tool patch/reverse |
| `manifests_reference/` | `00_ACTIVE/manifests/` + archive safe manifest | Manifest/hash |
| `manifests_reference/.../kimiki_safe_patch_manifest.json` | `04_ARCHIVE/build_stages/artifacts_kimiki_safe_20260804/` | Manifest identity full |
| `docs_reference/` | `docs/` + README | Tài liệu vận hành |
| `official_artifacts_reference/` | `00_ACTIVE/deb`, `00_ACTIVE/relay` | Artifact final mẫu |
| `customer_package_layout_reference/` | `00_ACTIVE/customer_package/` | Layout package khách |

## Conflict rule

```text
Project chính còn tồn tại  →  project chính là source of truth nếu lệch
Chỉ có handoff             →  handoff đủ build khách; unknown ghi trong HANDOFF_STATUS.md
```

## Ghi chú

`official_artifacts_reference/` là Kimiki — **không** output cho khách mới. Khách mới: domain/backend/bot/brand riêng + patch từ `baseline_reference/`.
