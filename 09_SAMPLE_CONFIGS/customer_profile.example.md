# Customer Profile Example

Đây là ví dụ minh hoạ. Không dùng nguyên xi cho production.

## Thông tin khách

```text
CLIENT_NAME=demo_customer
CLIENT_BRAND=@demo
CLIENT_CONTACT_TEXT=tele: @demo
```

## Domain / VPS

```text
CLIENT_DOMAIN=example.com
# Host phải đúng 14 UTF-8 bytes nếu URL = https://HOST/vcam (tổng 27).
# Ví dụ host 14: vc.example.com = 14? đếm kỹ — "vc.example.com" = 13, SAI.
# Hợp lệ ví dụ: api.example.co (14) -> https://api.example.co/vcam (27)
CLIENT_API_SUBDOMAIN=api.example.co
CLIENT_BACKEND_BASE_URL=https://api.example.co/vcam
CLIENT_VPS_IP=1.2.3.4
CLIENT_SSH_USER=ubuntu
CLIENT_SSH_KEY_PATH=C:\path\to\client.pem
CLIENT_SSH_COMMAND=ssh -i "C:\path\to\client.pem" ubuntu@1.2.3.4
```

Kiểm length:

```powershell
[System.Text.Encoding]::UTF8.GetByteCount('https://api.example.co/vcam')  # must be 27
```

## Telegram bot

```text
CLIENT_TELEGRAM_BOT_TOKEN=<BOT_TOKEN_FROM_BOTFATHER>
CLIENT_TELEGRAM_ADMIN_ID=<ADMIN_ID>
```

## Account mặc định

```text
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=1234
DEFAULT_MAX_DEVICES=1
DEFAULT_EXPIRE_DAYS=30
```


