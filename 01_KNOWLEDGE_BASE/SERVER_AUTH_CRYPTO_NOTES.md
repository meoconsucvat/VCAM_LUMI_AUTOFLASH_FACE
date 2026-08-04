# Server Auth Crypto Notes

Contract đầy đủ: `IDENTITY_AND_CRYPTO_CONTRACT.md`.

## Mục tiêu

Backend phải khớp chính xác với client đã patch. Sai một field trong signature có thể gây:

```text
bad_signature
HTTP 401
```

## Nguyên tắc

1. Dùng **raw request body** khi verify HMAC (client ký raw bytes).
2. Không tự serialize JSON lại.
3. Path trong HMAC: sau `removeprefix("/vcam")` — client gọi `/vcam/login` thì signed path là `/login`.
4. Timestamp / nonce lấy nguyên string header; nonce length 32.
5. `code_hash = sha256(code_marker)`; backend thử từng marker trong `VCAM_CODE_MARKERS`.
6. Bootstrap secret khớp client (legacy default trong `vcam_crypto.py` trừ khi rekey full stack).
7. Base URL client 27 bytes; public key + SPKI pin khớp identity đã patch.

## Khi gặp bad_signature

Cần capture:

```text
X-Timestamp
X-Nonce
X-Signature
Content-Type
raw_body exact bytes
path request thật
```

Sau đó tạo test vector:

```text
secret + timestamp + nonce + path + raw_body + fingerprint -> expected X-Signature
```

Nếu không tạo được signature khớp capture, chưa được deploy.

## Response signature

Sau login/verify, nếu server trả response có `ed25519_sig` hoặc `server_sig`, phải giữ đúng field order client mong đợi. Nếu login đã pass nhưng verify fail, kiểm tra response signing tiếp.



