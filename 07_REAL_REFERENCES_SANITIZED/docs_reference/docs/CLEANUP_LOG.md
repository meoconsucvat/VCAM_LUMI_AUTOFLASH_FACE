# Cleanup Log

## 2026-08-04 Phase cleanup

Mục tiêu: làm root project gọn hơn, nhưng không xoá vĩnh viễn dữ liệu cũ.

## Kết quả

Các thư mục/file duplicate ở root đã được move vào:

```text
04_ARCHIVE/root_cleanup_20260804-173057/
```

## Các mục đã move khỏi root

```text
artifacts_kimiki_20260804
artifacts_kimiki_safe_20260804
artifacts_kimiki_safe_brand12_20260804
artifacts_kimiki_safe_brand123_20260804
artifacts_kimiki_safe_brand123_nored_20260804
build_kimiki_20260804-144658
captures
device_baseline_192.168.2.120_20260804
relay
server_kimiki
tmp_ui_brand_scan
tools
com.lumiere.vcamlumiere_universal-Update.deb
keyminhhaivip.pem
server_kimiki_deploy_20260804-143858.tar.gz
LATEST_KIMIKI_BUILD_DIR.txt
```

## Nguồn chính sau cleanup

- Official artifact: `00_ACTIVE/`
- Backend source: `01_SERVER/backend/`
- Safe patch tools: `02_TOOLS/patchers_safe/`
- Baseline/original: `03_BASELINE/`
- Private key/deploy backup: `05_PRIVATE/`

## Ghi chú

Không dùng trực tiếp các bản trong `04_ARCHIVE/root_cleanup_20260804-173057/` để gửi khách. Nếu cần dùng lại, phải kiểm tra hash và manifest trước.

