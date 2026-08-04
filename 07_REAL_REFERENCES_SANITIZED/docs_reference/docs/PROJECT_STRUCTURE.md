# Project Structure

Cấu trúc mới được tạo theo hướng không phá dữ liệu cũ: các file quan trọng đã được copy vào cây chuẩn. Sau Phase cleanup, các thư mục/file duplicate ở root đã được move vào archive cleanup, không xoá vĩnh viễn.

## Cây chuẩn

```text
Vcam_LumierePhan/
├── 00_ACTIVE/
│   ├── deb/
│   ├── relay/
│   ├── customer_package/
│   └── manifests/
│
├── 01_SERVER/
│   ├── backend/
│   └── deploy/
│
├── 02_TOOLS/
│   ├── patchers_safe/
│   ├── analysis/
│   └── legacy_dangerous/
│
├── 03_BASELINE/
│   ├── original_deb/
│   └── device_baseline/
│
├── 04_ARCHIVE/
│   ├── build_stages/
│   ├── captures/
│   ├── root_cleanup_20260804-173057/
│   └── temp_extracts/
│
├── 05_PRIVATE/
│   ├── ssh_keys/
│   └── deploy_backups/
│
└── docs/
```

## 00_ACTIVE

Chỉ chứa bản đang dùng chính thức:

- DEB official.
- Relay zip official.
- Customer package official.
- Manifest/hash/summary official.

Khi gửi khách, ưu tiên lấy từ `00_ACTIVE/customer_package/`.

## 01_SERVER

Chứa source backend và Telegram bot:

- `app.py`
- `vcam_telegram_admin_bot.py`
- `schema.sql`
- `requirements.txt`
- `recovery_kit/vcam_crypto.py`

Không nên để DB production, token bot, private key hoặc log nhạy cảm trong thư mục này nếu định đưa lên Git.

## 02_TOOLS

Chia thành 3 nhóm:

### patchers_safe

Các script được ưu tiên dùng để build bản mới:

- `patch_kimiki_identity_v22031_safe.py`
- `brand_metadata_relay_only.py`
- `patch_ui_brand_v22031_safe.py`
- `patch_nored_watermark_v22031.py`

### analysis

Script phân tích/capture:

- `scan_identity_fields_v22031.py`
- `analyze_ui_watermark_v22031.py`
- `springboard_hmac_capture.py`
- `springboard_login_capture.py`

### legacy_dangerous

Script lịch sử, không dùng nếu chưa hiểu rõ:

- `patch_kimiki_identity_v22031.py`

Lý do: hướng official hiện tại dùng safe patcher. Dùng nhầm script legacy có thể tạo artifact sai bảng/offset và gây lỗi runtime.

## 03_BASELINE

Chứa bản gốc và bằng chứng thiết bị:

- DEB gốc.
- Device baseline từ iPhone lab.

Không sửa trực tiếp baseline. Mọi patch phải đi từ bản copy.

## 04_ARCHIVE

Chứa lịch sử build, capture, temp extract.

Các stage cũ được giữ để đối chiếu, không nên gửi khách và không nên coi là bản official.

`root_cleanup_20260804-173057/` chứa các thư mục/file cũ từng nằm ở root trước khi dọn, ví dụ:

- `artifacts_kimiki_*`
- `build_kimiki_*`
- `server_kimiki`
- `tools`
- `relay`
- `captures`
- `tmp_ui_brand_scan`
- `keyminhhaivip.pem`
- `server_kimiki_deploy_*.tar.gz`

Nếu cần khôi phục nhầm lẫn, lấy lại từ thư mục này.

## 05_PRIVATE

Chứa private material:

- SSH key VPS.
- Deploy archive.
- Sau này có thể thêm `.env`, backup DB, token bot.

Không đưa thư mục này lên Git public hoặc gửi khách.

