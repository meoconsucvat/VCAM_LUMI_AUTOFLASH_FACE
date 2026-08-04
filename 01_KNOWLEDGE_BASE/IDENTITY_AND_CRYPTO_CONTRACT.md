# Identity and Crypto Contract

Contract đã confirmed từ binary 2.2.031 + backend sample. Không đoán field.

## Base URL

Binary encoded URL fields có **length cố định 27** UTF-8 bytes.

Format:

```text
https://<host>/vcam
```

Độ dài:

```text
len(url) = 8 + len(host) + 5 = len(host) + 13
=> len(host) = 14
```

Ví dụ host 14 bytes:

```text
vc.kimiki.bond
api.leixi.bond
hai.leixi.bond
cam.corev.bond
api1.demo.bond
```

Sai length → safe patcher raise / binary corrupt / login fail. **Không pad/cắt mù.**

## Identity JSON (public)

Mẫu: `07_REAL_REFERENCES_SANITIZED/backend_reference/identity_kimiki_public.json`

```text
base_url                 # 27 bytes
ed25519_public_key_b64
ed25519_public_key_hex
spki_pin
backup_spki_pin
```

Private Ed25519 **không** nằm trong identity public. Backend:

```text
VCAM_ED25519_KEY  (default: server_ed25519.key cạnh app)
```

## UI / code marker

- Old: `tele: @lumierephan` (18 bytes)
- New phải pad space tới **18** bytes
- Dùng trong request signature:

```text
code_hash = sha256(code_marker.encode()).hexdigest()
```

Backend accept multi-marker:

```text
VCAM_CODE_MARKER
VCAM_CODE_MARKERS   # split "||"
```

Đổi marker DEB mà backend không list marker mới → `bad_signature`.

## Request signature

```text
payload = v3:{METHOD}:{path}:{timestamp}:{nonce}:{fingerprint}:{code_hash}:{body}
X-Signature = HMAC-SHA256(bootstrap_secret, payload).hexdigest()
```

Headers:

```text
X-Timestamp
X-Nonce      # length 32
X-Signature
```

Path trong HMAC:

```text
request.url.path.removeprefix("/vcam")
# client POST /vcam/login  => path signed = /login
```

Body: **raw request bytes** decode UTF-8, không re-dump JSON.

Bootstrap secret: default legacy trong `recovery_kit/vcam_crypto.py` (`LEGACY_BOOTSTRAP_SECRET`). Không đổi secret nếu chưa rekey full client+backend. **Không in secret ra report.**

## Response signing

```text
server_sig   = HMAC over fields joined by "|"
ed25519_sig  = Ed25519 sign same message, base64
```

Login field order (backend sample):

```text
login_ok | nonce | server_ts | device_id | token | expires
```

Verify field order:

```text
valid|invalid | nonce_echo | server_ts | device_id | expires_at | reason
```

Verify OK còn trả `key_seed`, `epoch_hour`.

## Relay crypto path

```text
POST /vcam/relay_login  {username, password} -> relay_key
POST /vcam/stream_key   {relay_key}          -> key_seed, epoch_hour
```

Stream key:

```text
SHA256( seed64 + b"vcam-stream-v1" + LE64(epoch_hour) )
```

## SPKI / TLS pin

- iOS UI/daemon: patch 3 pin slots trong identity patch.
- Relay Kimiki safe: **stub** TLS pin callback (`0x296d60`, `31c031dbc3`).
- Khách mới: replicate stub (như Kimiki) hoặc reverse pin đúng — không bịa pin.

## Env vars backend thật (app.py)

```text
VCAM_DB
VCAM_ED25519_KEY
VCAM_BOOTSTRAP_SECRET
VCAM_CODE_MARKER
VCAM_CODE_MARKERS
VCAM_SESSION_HOURS
VCAM_ALLOWED_SKEW
VCAM_PUBLIC_BASE_URL
VCAM_PAIRING_TTL
VCAM_LEGACY_RELAY_AUTO_PAIR
VCAM_BAD_LOGIN_LIMIT
VCAM_BAD_LOGIN_LOCK_ENABLED
VCAM_CONTACT_HANDLE
VCAM_TELEGRAM_BOT_TOKEN
VCAM_TELEGRAM_CHAT_ID
VCAM_VERIFY_ALLOW_DEVICE_MISMATCH
VCAM_VERIFY_IGNORE_REVOKED
VCAM_LOG_LEVEL
VCAM_DISABLE_INITIAL_SEED
VCAM_INITIAL_USER
VCAM_INITIAL_PASSWORD
VCAM_RELAY_USER
VCAM_RELAY_PASSWORD
```

Không dùng tên env “đoán” từ template cũ nếu lệch list này.

## Bằng chứng

```text
backend_reference/app.py
backend_reference/recovery_kit/vcam_crypto.py
backend_reference/identity_kimiki_public.json
tools_reference/02_TOOLS/patchers_safe/
manifests_reference/manifests/kimiki_safe_patch_manifest.json
baseline_reference/
```
