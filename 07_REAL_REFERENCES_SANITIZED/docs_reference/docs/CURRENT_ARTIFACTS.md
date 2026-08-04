# Current Artifacts

File này là nguồn sự thật hiện tại của project Kimiki.

## Trạng thái

- Trạng thái: official hiện tại.
- Backend domain: `https://vc.kimiki.bond/vcam`
- Health endpoint: `https://vc.kimiki.bond/health`
- Brand UI hiện tại: `tele: @vcamplus`
- Watermark đỏ chạy quanh mép màn hình: đã patch tắt ở bản official.
- Thiết bị đã test gần nhất: iPhone lab đã login, relay đã nhận RTMP, OBS stream lên camera, không văng trong test cuối.

## DEB official

Path:

```text
00_ACTIVE/deb/com.lumiere.vcamlumiere_2.2.031_kimiki_universal_safe_vcamplus_metadata_ui_marker_vcamplus_nored_test.deb
```

SHA256:

```text
a94a8464a5370bdbb318ff6b4be672639c26ade4d86424838dccaa0e29c624e1
```

Size:

```text
360612 bytes
```

Ghi chú:

- Đây là bản universal.
- Đã patch metadata Sileo sang VcamPlus.
- Đã patch UI marker sang `tele: @vcamplus`.
- Đã tắt watermark đỏ chạy quanh mép màn hình.
- Tên file còn có chữ `_test` vì xuất phát từ giai đoạn test; theo trạng thái hiện tại, đây là bản đã được chốt dùng chính thức.

## Relay official

Path:

```text
00_ACTIVE/relay/VCam_Kimiki_Windows_Relay_safe_vcamplus_contact_clean.zip
```

SHA256:

```text
af0644c3a85441b485514d26c7ffc15618802a124a71bb407d598039e8c5ef50
```

Size:

```text
2936503 bytes
```

Ghi chú:

- Dùng cùng tài khoản với DEB.
- Relay chạy RTMP LAN ở máy Windows, OBS publish vào `rtmp://<windows-lan-ip>/live`.
- Khi gửi khách, nên giải nén vào thư mục ổn định như `C:\VcamPlusRelay`.

## Baseline gốc

Path:

```text
03_BASELINE/original_deb/com.lumiere.vcamlumiere_universal-Update.deb
```

SHA256:

```text
5a641447cdb2b3030f8e531695e647d53e9beeef5e592dbe7f5c84929b0a9efb
```

Size:

```text
361048 bytes
```

## Manifest liên quan

Các manifest của bản official nằm ở:

```text
00_ACTIVE/manifests/
```

Các file quan trọng:

- `nored_watermark_v22031_manifest.json`
- `ui_marker_vcamplus_manifest.json`
- `brand_metadata_relay_manifest.json`
- `SHA256SUMS.txt`
- `BUILD_SUMMARY_Nored_V22031.md`


