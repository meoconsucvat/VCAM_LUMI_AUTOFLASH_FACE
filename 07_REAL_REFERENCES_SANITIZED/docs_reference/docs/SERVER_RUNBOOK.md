# Server Runbook

Tài liệu vận hành backend Kimiki.

## Thành phần

Local source:

```text
01_SERVER/backend/
```

Backend domain:

```text
https://vc.kimiki.bond/vcam
```

Health endpoint:

```text
https://vc.kimiki.bond/health
```

## File chính

```text
app.py
vcam_telegram_admin_bot.py
schema.sql
requirements.txt
recovery_kit/vcam_crypto.py
```

## Kiểm tra nhanh backend

Trên máy local:

```powershell
curl.exe https://vc.kimiki.bond/health
```

Kỳ vọng: health OK hoặc JSON OK tuỳ backend hiện tại.

## Vận hành trên VPS

Tên service thực tế cần kiểm tra trực tiếp trên VPS trước khi sửa. Theo trạng thái gần nhất project dùng backend/bot Kimiki, service thường theo dạng:

```text
vcam-kimiki-backend.service
vcam-kimiki-bot.service
```

Các lệnh kiểm tra mẫu:

```bash
sudo systemctl status vcam-kimiki-backend.service
sudo systemctl status vcam-kimiki-bot.service
sudo journalctl -u vcam-kimiki-backend.service -n 100 --no-pager
sudo journalctl -u vcam-kimiki-bot.service -n 100 --no-pager
```

Nếu tên service khác, phải dùng tên thực tế trên VPS, không đoán.

## Khi login bị bad_signature

Kiểm tra theo thứ tự:

1. DEB có đúng bản official không.
2. Domain trong DEB có trỏ đúng backend không.
3. Backend đang dùng đúng crypto/signature format không.
4. Backend có nhận marker/secret đúng không.
5. Log backend có `request_signature_rejected` không.

Không sửa account trước khi xác nhận signature layer.

## Khi invalid_credentials

Khả năng thường gặp:

- Sai user/pass.
- User chưa tồn tại.
- Account đã bị xoá/expire/lock.
- User đang login bằng identity/device khác nếu rule giới hạn máy còn bật.

Kiểm tra bằng bot admin hoặc DB trên VPS.

## Backup trước khi deploy

Trước khi thay backend/bot:

```bash
sudo cp -a /opt/vcam_kimiki /opt/vcam_kimiki.backup_$(date +%Y%m%d-%H%M%S)
```

Nếu có DB SQLite production, backup riêng DB trước khi migrate.


