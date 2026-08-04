# Customer Profile Template

Tạo một file `CUSTOMER_PROFILE.md` từ template này cho mỗi khách.

## Thông tin khách

```text
CLIENT_NAME=
CLIENT_BRAND=
CLIENT_CONTACT_TEXT=
```

Ví dụ:

```text
CLIENT_BRAND=@vcamplus
CLIENT_CONTACT_TEXT=tele: @vcamplus
```

`CLIENT_CONTACT_TEXT` / UI marker sẽ được **pad space tới 18 bytes** khi patch  
(ví dụ `tele: @vcamplus` + 3 spaces). Backend `VCAM_CODE_MARKERS` phải khớp.

## Domain / VPS

```text
CLIENT_DOMAIN=
CLIENT_API_SUBDOMAIN=
CLIENT_BACKEND_BASE_URL=
CLIENT_VPS_IP=
CLIENT_SSH_USER=ubuntu
CLIENT_SSH_KEY_PATH=
CLIENT_SSH_COMMAND=
```

**Ràng buộc:** `CLIENT_BACKEND_BASE_URL` phải đúng **27** UTF-8 bytes  
(`https://` + host **14** bytes + `/vcam`). Đếm byte trước khi patch.

Ví dụ host 14 bytes:

```text
CLIENT_DOMAIN=example.co
CLIENT_API_SUBDOMAIN=api.example.co
CLIENT_BACKEND_BASE_URL=https://api.example.co/vcam
CLIENT_VPS_IP=1.2.3.4
CLIENT_SSH_COMMAND=ssh -i "path\\to\\key.pem" ubuntu@host
```

## Telegram bot

```text
CLIENT_TELEGRAM_BOT_TOKEN=
CLIENT_TELEGRAM_ADMIN_ID=
```

Không in token trong log/báo cáo public.

## Account mặc định

```text
DEFAULT_USERNAME=
DEFAULT_PASSWORD=
DEFAULT_MAX_DEVICES=1
DEFAULT_EXPIRE_DAYS=
DEFAULT_EXPIRE_HOURS=
```

## Thiết bị test

```text
TEST_IPHONE_MODEL=
TEST_IOS_VERSION=
TEST_JAILBREAK=
TEST_PACKAGE_MANAGER=
TEST_IPHONE_LAN_IP=
TEST_IPHONE_SSH_PORT=22
```

Ví dụ:

```text
TEST_IPHONE_MODEL=iPhone Xs
TEST_IOS_VERSION=16.6.1
TEST_JAILBREAK=RootHide Bootstrap
```

## Windows relay / OBS

```text
WINDOWS_LAN_IP=
RELAY_INSTALL_DIR=C:\\VcamPlusRelay
OBS_RTMP_URL=rtmp://<WINDOWS_LAN_IP>/live
OBS_STREAM_KEY=
```

Nếu URL đã có `/live`, stream key để trống.

## Build policy

```text
CHANGE_DOMAIN=yes/no
CHANGE_BRAND=yes/no
CHANGE_METADATA=yes/no
DISABLE_RED_WATERMARK=yes/no
KEEP_BASELINE_BACKUP=yes
```

## Ghi chú khách

```text
NOTES=
```



