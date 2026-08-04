# Do Not Copy Directly To Customer

Không gửi trực tiếp các nhóm sau cho khách nếu chưa rà soát:

```text
baseline_reference/
backend_reference/
tools_reference/
docs_reference/
manifests_reference/
official_artifacts_reference/
```

Lý do:

- Đây là tài liệu/code/baseline cho AI/kỹ sư, không phải package người dùng cuối.
- `official_artifacts_reference` mang identity Kimiki — không phải bản khách.
- Có thể khiến khách cài nhầm DEB/domain hoặc chạy backend reference.

Package khách cuối nên dựa theo:

```text
04_CUSTOMER_PACKAGE_TEMPLATE/
06_OUTPUT_EXPECTED/EXPECTED_ARTIFACT_TREE.md
```

Customer package cuối chỉ nên có:

- DEB đã build **cho khách đó**.
- Relay zip đã build **cho khách đó**.
- README hướng dẫn.
- SHA256SUMS.

Tuyệt đối không có:

```text
*.pem  *.env  *.db  bot token  private key  relaykey.bin  runtime logs
```


