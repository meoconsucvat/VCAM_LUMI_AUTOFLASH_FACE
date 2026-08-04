# VCAM LUMI AutoFlash Face — Handoff Kit

**Private engineering kit** để AI / kỹ sư build một project **VcamLumiere / VcamPlus** riêng cho từng khách  
(domain · VPS · Telegram bot · brand · account · thiết bị test).

> Standalone: clone kit này là đủ để build khách.  
> Không bắt buộc có project gốc `Vcam_LumierePhan` trên máy mới.

---

## Mục tiêu

| Mục tiêu | Chi tiết |
|---|---|
| Kỷ luật | Làm theo **bằng chứng**, không đoán mò |
| Đủ nguyên liệu | Baseline DEB/relay + safe patch tools + backend sample + manifests |
| Pipeline chuẩn | Profile → backend → patch → package → test → bàn giao |
| Debug đúng tầng | Backend → login → relay `:1935` → OBS → iPhone → inject → codec |
| An toàn bàn giao | Customer package không chứa secret / runtime key / log |

---

## Bắt đầu trong 60 giây

```text
1. Clone repo (private) về máy làm việc
2. Mở 00_START_HERE/PROMPT_FOR_NEW_AI.md
3. Copy toàn bộ block prompt gửi AI mới / engineer mới
4. AI verify baseline SHA256 + tự chấm AI_ONBOARDING_CHECKLIST.md
5. Chưa có CUSTOMER_PROFILE → chỉ onboarding, không patch/deploy
6. Có profile → plan theo 02_BUILD_PIPELINE/PATCH_ORDER.md → chờ duyệt
```

### Đọc theo thứ tự

| # | File | Việc |
|---|---|---|
| 1 | [`00_START_HERE/PROMPT_FOR_NEW_AI.md`](00_START_HERE/PROMPT_FOR_NEW_AI.md) | Prompt onboarding đầy đủ |
| 2 | [`00_START_HERE/AI_RULES_OF_WORK.md`](00_START_HERE/AI_RULES_OF_WORK.md) | Luật làm việc / báo cáo |
| 3 | [`00_START_HERE/HANDOFF_STATUS.md`](00_START_HERE/HANDOFF_STATUS.md) | Kit OK / MISSING / UNKNOWN |
| 4 | [`00_START_HERE/AI_ONBOARDING_CHECKLIST.md`](00_START_HERE/AI_ONBOARDING_CHECKLIST.md) | 20 dòng tự chấm |
| 5 | [`01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md`](01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md) | URL · marker · HMAC · env |
| 6 | [`02_BUILD_PIPELINE/PATCH_ORDER.md`](02_BUILD_PIPELINE/PATCH_ORDER.md) | Thứ tự patch |
| 7 | [`07_REAL_REFERENCES_SANITIZED/baseline_reference/README.md`](07_REAL_REFERENCES_SANITIZED/baseline_reference/README.md) | Input patch + hash |

---

## Kiến trúc hệ thống

```text
┌─────────────────┐     HTTPS /vcam/*      ┌──────────────────────┐
│  iPhone DEB     │ ─────────────────────► │  VPS Backend         │
│  UI + Daemon    │ ◄── token/key_seed ─── │  + Telegram admin bot│
└────────┬────────┘                        └──────────────────────┘
         │ RTMP player
         ▼
┌─────────────────┐     RTMP publish       ┌──────────────────────┐
│ Windows relay   │ ◄───────────────────── │ OBS                  │
│ TCP :1935 LAN   │                        │ rtmp://PC-IP/live    │
└─────────────────┘                        └──────────────────────┘
```

**RTMP không chạy trên VPS.** VPS chỉ `22/80/443`. Stream LAN qua Windows `relay.exe`.

### Debug layers (bắt buộc)

```text
Backend / DNS / TLS
  → Login / Verify
  → Relay process + :1935 LISTEN + firewall
  → OBS publish
  → iPhone thấy RTMP
  → iPhone connect Windows
  → Camera frame
  → Stability / respring
```

---

## Cấu trúc repo

```text
.
├── 00_START_HERE/                 # Prompt, rules, checklist, profile template
├── 01_KNOWLEDGE_BASE/             # Field manual, crypto contract, failures
├── 02_BUILD_PIPELINE/             # Patch order, verify, release
├── 03_SERVER_TEMPLATES/           # env / nginx / systemd / deploy runbook
├── 04_CUSTOMER_PACKAGE_TEMPLATE/  # README + install guides cho khách
├── 05_TROUBLESHOOTING/            # bad_signature, RTMP, firewall, black screen
├── 06_OUTPUT_EXPECTED/            # Artifact tree + final report template
├── 07_REAL_REFERENCES_SANITIZED/  # File thật (baseline, tools, backend, manifests)
│   ├── baseline_reference/        # ★ DEB + relay GỐC để patch
│   ├── backend_reference/
│   ├── tools_reference/
│   ├── manifests_reference/
│   ├── official_artifacts_reference/   # Kimiki final — REFERENCE ONLY
│   └── customer_package_layout_reference/
├── 08_AUTOMATION/                 # Windows / Linux / packaging scripts
└── 09_SAMPLE_CONFIGS/             # Ví dụ CUSTOMER_PROFILE
```

---

## Constraints cứng (không được bẻ)

| Constraint | Giá trị | Ghi chú |
|---|---|---|
| Base URL | **27** UTF-8 bytes | `https://` + **host 14** + `/vcam` |
| UI / code marker | **18** bytes | pad space; tham gia HMAC `code_hash` |
| Signed path | strip `/vcam` | client `/vcam/login` → HMAC path `/login` |
| Request body | raw bytes | không re-serialize JSON |
| Patch tools | `patchers_safe/` only | cấm `legacy_dangerous/` |
| RTMP | Windows LAN `:1935` | không VPS |
| Kimiki final artifacts | reference-only | không gửi khách nguyên |

Chi tiết: [`IDENTITY_AND_CRYPTO_CONTRACT.md`](01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md)

### Baseline hashes (verify trước patch)

```text
DEB   5a641447cdb2b3030f8e531695e647d53e9beeef5e592dbe7f5c84929b0a9efb
      07_REAL_REFERENCES_SANITIZED/baseline_reference/com.lumiere.vcamlumiere_universal-Update.deb

Relay 83230cc05a0544faedbae33ab72abda0c0bafd0d52668e803e5212d5d762384b
      07_REAL_REFERENCES_SANITIZED/baseline_reference/relay.exe
```

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath `
  "07_REAL_REFERENCES_SANITIZED\baseline_reference\com.lumiere.vcamlumiere_universal-Update.deb"
Get-FileHash -Algorithm SHA256 -LiteralPath `
  "07_REAL_REFERENCES_SANITIZED\baseline_reference\relay.exe"
```

Hash lệch → **STOP**, không patch.

---

## Pipeline build khách

```text
Phase 0  CUSTOMER_PROFILE + URL 27 bytes
Phase 1  DNS / VPS / TLS / backend / bot  →  /health OK
Phase 2  identity JSON + Ed25519 (private chỉ trên VPS)
Phase 3  Safe patch:
           1. identity (DEB + relay)
           2. brand / metadata / relay contact
           3. UI marker  (sync VCAM_CODE_MARKERS)
           4. no-red watermark  (chỉ 2.2.031)
Phase 4  Customer package + SHA256SUMS
Phase 5  Test: login · relay · :1935 · OBS · RTMP menu · LIVE · camera · soak
Phase 6  Bàn giao + final report
```

Xem: [`PATCH_ORDER.md`](02_BUILD_PIPELINE/PATCH_ORDER.md) · [`VERIFY_CHECKLIST.md`](02_BUILD_PIPELINE/VERIFY_CHECKLIST.md)

### Customer package chỉ gồm

```text
✓  <client>_vcam_universal.deb
✓  <client>_windows_relay.zip
✓  README.md
✓  SHA256SUMS.txt

✗  .pem  .env  .db  bot token  private key  relaykey.bin  logs  tools  baseline thô
```

---

## Troubleshooting nhanh

| Triệu chứng | Không làm vội | Làm trước |
|---|---|---|
| Menu không dò RTMP | Patch DEB | `relay.exe`, `:1935`, firewall, OBS URL, cùng LAN |
| `bad_signature` | Tạo/xoá user | Capture headers + raw body + `vcam_crypto.py` + marker |
| `invalid_credentials` | Đổi crypto | User/pass, expire, lock, device limit |
| Camera đen | AES/codec ngay | Chứng minh iPhone đã connect `:1935` + OBS publish |
| Safe Mode / respring | Tiếp tục patch | Rollback stage; nghi unsafe / length sai |

Chi tiết: [`05_TROUBLESHOOTING/`](05_TROUBLESHOOTING/)

---

## Bảo mật & phạm vi repo

**Repo này là private / nội bộ.**

Có chứa:

- Baseline binary, patch tools, backend crypto sample, reverse notes

**Không** được commit:

- Production bot token, `.pem`, private Ed25519, DB, `.env` thật, `relaykey.bin`, log khách

Xem [`.gitignore`](.gitignore) và [`07_REAL_REFERENCES_SANITIZED/DO_NOT_COPY_TO_CUSTOMER.md`](07_REAL_REFERENCES_SANITIZED/DO_NOT_COPY_TO_CUSTOMER.md).

### Source of truth

```text
Chỉ có handoff          → handoff đủ build khách
Còn Vcam_LumierePhan    → project chính thắng nếu lệch
VPS production exact    → SSH verify (systemd/nginx), không đoán template
```

Gap còn lại: [`HANDOFF_STATUS.md`](00_START_HERE/HANDOFF_STATUS.md)

---

## Clone & làm việc

```bash
git clone https://github.com/meoconsucvat/VCAM_LUMI_AUTOFLASH_FACE.git
cd VCAM_LUMI_AUTOFLASH_FACE

# Windows: bật long paths nếu cần (tên DEB dài)
git config core.longpaths true
```

**Không** patch file trong repo handoff tại chỗ.  
Copy baseline + tools sang **project khách riêng**, rồi patch / deploy ở đó.

---

## License / ownership

Private proprietary kit. Không phân phối public, không gửi nguyên tree cho khách cuối.  
Dùng nội bộ cho build & bàn giao project khách theo quy trình trong kit.
