# Handoff Status

Cập nhật: 2026-08-04

## Mục tiêu kit

Cho phép AI/kỹ sư **trên máy khác**, **không cần** project `Vcam_LumierePhan`, vẫn:

1. Hiểu hệ thống và quy tắc làm việc.
2. Có baseline DEB/relay + tools + backend sample + manifests.
3. Build project khách theo pipeline an toàn.
4. Debug đúng tầng bằng evidence.

## Mức sẵn sàng (standalone)

| Nhóm | Status | Ghi chú |
|---|---|---|
| Quy tắc / prompt / debug tầng | **OK** | `00_START_HERE`, `05_TROUBLESHOOTING` |
| Knowledge crypto/auth/RTMP | **OK** | `01_KNOWLEDGE_BASE` + notes identity |
| Baseline DEB + relay + hash | **OK** | `07_.../baseline_reference/` |
| Safe patch tools | **OK** | `tools_reference/02_TOOLS/patchers_safe/` |
| Backend + crypto sample | **OK** | `backend_reference/` |
| Safe identity manifest đầy đủ | **OK** | `manifests_reference/.../kimiki_safe_patch_manifest.json` |
| Kimiki final reference artifacts | **OK** | reference-only, không gửi khách nguyên |
| ENV template khớp `app.py` | **OK** | `03_SERVER_TEMPLATES/ENV_TEMPLATE.env` |
| Automation scripts | **OK template** | Phải sửa path/service theo khách |
| Production VPS systemd/nginx redacted | **MISSING** | Phải SSH VPS khách / copy redacted sau deploy |
| RootHide/rootless convert exact command | **UNKNOWN** | Chỉ có note; phải lấy từ quy trình cài thật |
| `relaykey.bin` format | **UNKNOWN** | Binary; không copy sang package khách |
| Device matrix đầy đủ | **PARTIAL** | Mỗi khách test lại |

## Source of truth

```text
Nếu project chính còn: Vcam_LumierePhan  >  handoff
Nếu chỉ mang handoff sang máy khác: handoff là đủ để build khách
  (trừ unknown production VPS exact / rootless convert / device test)
```

## Không có trong handoff (cố ý)

- Private key, `.pem`, bot token production, DB production, `.env` thật.
- `05_PRIVATE/`.
- Runtime `relaykey.bin` / log cá nhân.

## AI mới bắt đầu ở đâu

1. `00_START_HERE/PROMPT_FOR_NEW_AI.md`
2. `00_START_HERE/AI_RULES_OF_WORK.md`
3. `00_START_HERE/HANDOFF_STATUS.md` (file này)
4. `00_START_HERE/AI_ONBOARDING_CHECKLIST.md`
5. `01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md`
6. `07_REAL_REFERENCES_SANITIZED/README.md` + `baseline_reference/README.md`
7. Chỉ sau đó mới thu thập `CUSTOMER_PROFILE` và plan theo `02_BUILD_PIPELINE/PATCH_ORDER.md`
