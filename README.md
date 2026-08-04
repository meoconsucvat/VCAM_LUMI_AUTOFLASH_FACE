# VcamAutoFlashFace Handoff Kit

Bộ handoff để AI/kỹ sư **trên máy khác** build project VcamLumiere/VcamPlus riêng cho khách từ: domain, VPS, bot Telegram, brand, account mặc định, thiết bị test.

## Mục tiêu

- Làm việc có kỷ luật, **không đoán mò**.
- Đủ baseline + tools + backend sample để **không bắt buộc** có project `Vcam_LumierePhan` trên máy mới.
- Chuẩn hoá: profile khách → backend → patch DEB/relay → package → test.
- Ghi lỗi thực chiến: `bad_signature`, `invalid_credentials`, không dò RTMP, firewall `1935`, OBS sai URL, respring/safemode.

## Bắt đầu ở đâu?

1. Copy prompt trong `00_START_HERE/PROMPT_FOR_NEW_AI.md` gửi AI mới (block ```text```).
2. AI mới đọc theo thứ tự trong prompt, verify baseline hash, tự chấm checklist 20 dòng.
3. Chưa có profile khách → chỉ báo onboarding, không patch/deploy.
4. Có profile → plan theo `02_BUILD_PIPELINE/PATCH_ORDER.md`, chờ duyệt rồi làm.

File nền (AI phải đọc, không chỉ đọc prompt):

- `00_START_HERE/AI_RULES_OF_WORK.md`
- `00_START_HERE/HANDOFF_STATUS.md`
- `00_START_HERE/AI_ONBOARDING_CHECKLIST.md`
- `01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md`
- `07_REAL_REFERENCES_SANITIZED/baseline_reference/README.md`

## Cấu trúc

```text
VcamAutoFlashFace_Handoff/
├── 00_START_HERE/
├── 01_KNOWLEDGE_BASE/
├── 02_BUILD_PIPELINE/
├── 03_SERVER_TEMPLATES/
├── 04_CUSTOMER_PACKAGE_TEMPLATE/
├── 05_TROUBLESHOOTING/
├── 06_OUTPUT_EXPECTED/
├── 07_REAL_REFERENCES_SANITIZED/
│   ├── baseline_reference/          # DEB + relay GỐC để patch
│   ├── backend_reference/
│   ├── tools_reference/
│   ├── manifests_reference/
│   ├── official_artifacts_reference/ # Kimiki final — reference only
│   └── customer_package_layout_reference/
├── 08_AUTOMATION/
└── 09_SAMPLE_CONFIGS/
```

## Nguyên tắc lớn nhất

Không kết luận bằng cảm giác. Debug đúng tầng:

```text
Backend/DNS/TLS -> Login/Verify -> Relay :1935 -> OBS -> iPhone RTMP -> Injection -> Codec/Crypto
```

- Không patch DEB khi lỗi là firewall/OBS/relay.
- Không sửa backend account khi lỗi là signature.
- Không nói "thiết bị lỗi" nếu chưa có log/process/network evidence.
- Không gửi artifact Kimiki final cho khách mới nếu chưa patch identity/domain/brand riêng.

## Constraints cứng (nhớ trước khi patch)

| Constraint | Giá trị |
|---|---|
| Base URL length | **27** UTF-8 bytes (`len(host)=14`) |
| UI marker length | **18** bytes, pad space |
| Signed path | strip prefix `/vcam` |
| RTMP | Windows LAN `:1935`, không VPS |
| Patch scripts | chỉ `patchers_safe/` |

Chi tiết: `01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md`

## Source of truth

- **Chỉ mang handoff** sang máy khác: handoff đủ để build khách (baseline + tools + backend sample).
- **Nếu còn** `C:\Users\Admin\Desktop\Vcam_LumierePhan`: project chính thắng khi handoff lệch.
- Production VPS systemd/nginx exact: **verify trên VPS**, không đoán từ template.

## Không có trong kit (cố ý)

Private key, bot token production, DB, `.pem`, `relaykey.bin` runtime, log cá nhân.

## Automation

Xem `08_AUTOMATION/README.md` — script là template, sửa path/service theo khách trước khi chạy production.
