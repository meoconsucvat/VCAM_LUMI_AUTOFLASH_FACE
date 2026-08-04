# Baseline Reference (patch inputs)

Đây là **input gốc được phép patch** cho build khách mới. Không nhầm với `official_artifacts_reference/` (artifact Kimiki final — chỉ reference-only).

## Files

| File | Role | SHA256 |
|---|---|---|
| `com.lumiere.vcamlumiere_universal-Update.deb` | DEB baseline 2.2.031 universal | `5a641447cdb2b3030f8e531695e647d53e9beeef5e592dbe7f5c84929b0a9efb` |
| `relay.exe` | Relay baseline Windows | `83230cc05a0544faedbae33ab72abda0c0bafd0d52668e803e5212d5d762384b` |

## Quy tắc

1. **Copy** sang project khách rồi patch. Không patch trực tiếp file trong handoff.
2. Trước patch: hash input; sau patch: hash output + manifest.
3. Safe patcher expect đúng baseline hash trên (trừ khi bạn hiểu rõ và dùng `--allow-unknown-input` có chủ đích).
4. Không gửi baseline thô cho khách cuối nếu chưa patch identity/brand.

## Nguồn copy

Từ project chính (khi còn tồn tại):

```text
Vcam_LumierePhan\03_BASELINE\original_deb\com.lumiere.vcamlumiere_universal-Update.deb
Vcam_LumierePhan\04_ARCHIVE\build_stages\relay\relay.exe
```

Nếu handoff đã có thư mục này, AI mới **không bắt buộc** phải có project Kimiki trên máy.
