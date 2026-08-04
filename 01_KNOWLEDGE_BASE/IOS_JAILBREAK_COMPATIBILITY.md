# iOS Jailbreak Compatibility

## Các môi trường thường gặp

- iPhone 8/8 Plus: arm64.
- iPhone Xs trở lên: arm64e.
- RootHide Dopamine.
- RootHide Bootstrap.
- Sileo package manager.

## Điều cần kiểm tra

Trên iPhone:

```sh
dpkg -l | grep -i -E 'vcam|lumi|ellekit|roothide|bootstrap|dopamine'
```

Kiểm tra file tweak:

```sh
ls -la /var/jb/usr/lib/TweakInject/
```

Kiểm tra prefs:

```sh
plutil -p /var/jb/var/mobile/vc.plist
```

Không in token/auth secret nếu có.

## Khi respring/safemode

Không attach Frida bừa nếu thiết bị đã unstable. Làm theo stage:

1. Cài baseline known-good.
2. Mở menu.
3. Login.
4. Relay/RTMP.
5. LIVE.
6. Camera.

Nếu chỉ stage mới gây respring, rollback stage đó.

## Ghi chú arm64e

Thiết bị arm64e nhạy với patch sai offset/slice. Nếu build universal, phải verify cả arm64 và arm64e slice. Không chỉ test iPhone 8 rồi kết luận chạy tốt trên iPhone Xs/11/12.



