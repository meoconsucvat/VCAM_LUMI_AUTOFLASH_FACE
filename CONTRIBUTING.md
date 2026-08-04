# Contributing (internal)

Repo private. Chỉ collaborator được mời mới được push.

## Trước khi commit

1. Không commit secret: token, `.pem`, `.env` thật, `.db`, `relaykey.bin`, private key.
2. Không patch baseline **trong** repo handoff — copy ra project khách.
3. Nếu thêm binary/reference: cập nhật `07_REAL_REFERENCES_SANITIZED/SHA256SUMS.txt`.
4. Nếu đổi contract (URL length, marker, crypto): cập nhật  
   `01_KNOWLEDGE_BASE/IDENTITY_AND_CRYPTO_CONTRACT.md` + checklist.
5. Nếu đổi readiness: cập nhật `00_START_HERE/HANDOFF_STATUS.md`.

## Commit message

```text
<area>: <short summary>

Optional body: why / evidence / hash if baseline changed.
```

Ví dụ:

```text
docs: clarify host length 14 for base URL constraint
baseline: add verified relay.exe hash note
```

## PR / review checklist

- [ ] README / START_HERE vẫn đúng entry path
- [ ] Không lộ secret trong diff
- [ ] Baseline hash vẫn documented
- [ ] Safe tools only; không promote legacy_dangerous
- [ ] Customer package rules unchanged unless intentional

## Branch

- `main` — kit ổn định để AI/engineer mới clone
- Feature: `docs/...`, `tools/...`, `baseline/...` — merge sau review ngắn
