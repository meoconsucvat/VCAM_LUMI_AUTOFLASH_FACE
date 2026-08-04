# Automation Scripts

Thư mục này chứa script mẫu để AI/kỹ sư mới thao tác nhanh.

## Windows

```text
windows/check_relay_port.ps1
windows/add_vcam_firewall_rules.ps1
windows/package_customer_relay.ps1
```

Mục đích:

- Kiểm tra relay process.
- Kiểm tra port `1935`.
- Thêm firewall rule.
- Đóng gói relay và loại runtime log/key.

## Linux

```text
linux/check_backend.sh
linux/deploy_backend_template.sh
```

Mục đích:

- Kiểm tra health/backend/bot service.
- Deploy backend template lên VPS.

## Packaging

```text
packaging/make_sha256sums.ps1
packaging/make_customer_package.ps1
```

Mục đích:

- Tạo hash manifest.
- Đóng gói customer package gồm DEB, relay zip, README.

## Lưu ý

Các script này là template. Trước khi chạy production, phải sửa đúng path/service/domain của khách.


