# Expected Artifact Tree

Sau khi build cho một khách, output nên có dạng:

```text
<CLIENT_PROJECT>/
├── 00_ACTIVE/
│   ├── deb/
│   │   └── <client>_vcam_universal.deb
│   ├── relay/
│   │   └── <client>_windows_relay.zip
│   ├── customer_package/
│   │   ├── <client>_vcam_universal.deb
│   │   ├── <client>_windows_relay.zip
│   │   ├── README.md
│   │   └── SHA256SUMS.txt
│   └── manifests/
│       ├── deb_patch_manifest.json
│       ├── relay_patch_manifest.json
│       └── build_summary.md
│
├── 01_SERVER/
│   ├── backend/
│   └── deploy/
│
├── 02_TOOLS/
├── 03_BASELINE/
├── 04_ARCHIVE/
├── 05_PRIVATE/
└── docs/
```

## Không để trong customer package

```text
*.pem
*.env
*.db
relaykey.bin
runtime.log
bot token
private key
```



