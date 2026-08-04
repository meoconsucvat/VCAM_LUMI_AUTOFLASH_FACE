# Real References Sanitized

File thật (hoặc bản copy đã rà) dùng làm mẫu cho AI/kỹ sư mới — không chỉ Markdown lý thuyết.

## Nội dung

```text
baseline_reference/              # DEB + relay GỐC để patch (bắt buộc cho build khách)
backend_reference/               # backend + bot + crypto sample
tools_reference/                 # patcher/reverse tools
manifests_reference/             # manifest/hash/build summary
docs_reference/                  # docs project nguồn
official_artifacts_reference/    # DEB/relay Kimiki FINAL — reference only
customer_package_layout_reference/
SHA256SUMS.txt
SOURCE_MAP.md
DO_NOT_COPY_TO_CUSTOMER.md
```

## Vai trò từng nhóm

| Thư mục | Dùng để | Gửi khách? |
|---|---|---|
| `baseline_reference/` | Input patch (hash cố định) | Không (trừ khi cố ý giao baseline) |
| `backend_reference/` | Học/copy backend cho project khách | Không nguyên xi; deploy bản đã đổi env/identity |
| `tools_reference/` | Chạy patch an toàn | Không |
| `manifests_reference/` | Đối chiếu format manifest/hash | Không |
| `official_artifacts_reference/` | Biết artifact final trông thế nào | **Không** gửi nguyên (domain/brand Kimiki) |
| `customer_package_layout_reference/` | Layout package | Không; chỉ học layout |

## Baseline hash (verify trước patch)

```text
DEB   5a641447cdb2b3030f8e531695e647d53e9beeef5e592dbe7f5c84929b0a9efb
      com.lumiere.vcamlumiere_universal-Update.deb

Relay 83230cc05a0544faedbae33ab72abda0c0bafd0d52668e803e5212d5d762384b
      relay.exe
```

Kimiki final (reference-only):

```text
DEB   a94a8464a5370bdbb318ff6b4be672639c26ade4d86424838dccaa0e29c624e1
Relay zip af0644c3a85441b485514d26c7ffc15618802a124a71bb407d598039e8c5ef50
```

## Quy tắc sử dụng

1. Học format, cấu trúc, patch flow, manifest.
2. Build khách: **project riêng**, copy baseline → patch → package.
3. Không deploy nguyên backend Kimiki nếu chưa đổi domain/identity/bot/env.
4. Không gửi nguyên thư mục `07_` cho khách cuối.
5. Verify `SHA256SUMS.txt` sau khi copy kit sang máy khác.

## Những gì đã tránh copy

- `05_PRIVATE/`
- SSH `.pem`
- DB production / env production
- Extracted relay runtime có `relaykey.bin` / log cá nhân

## Cách AI mới nên dùng

1. `baseline_reference/README.md` — chốt input patch.
2. `backend_reference/app.py` + `recovery_kit/vcam_crypto.py` — endpoint + signature.
3. `tools_reference/02_TOOLS/patchers_safe/` — patch flow an toàn.
4. `manifests_reference/manifests/kimiki_safe_patch_manifest.json` — manifest identity đầy đủ.
5. `official_artifacts_reference/` — hình dạng final (không reuse identity Kimiki).
6. `01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md` — contract URL/marker/HMAC.
