# VCamLumiere Kimiki backend

Backend/bot riêng cho project `Vcam_LumierePhan`.

Base URL dự kiến:

```text
https://vc.kimiki.bond/vcam
```

Lý do chọn `vc.kimiki.bond`: URL đầy đủ dài đúng 27 UTF-8 bytes, phù hợp patch binary fixed-length.

RTMP không chạy trên VPS. RTMP vẫn do Windows `relay.exe` listen LAN port `1935`.

VPS chỉ cần:

```text
22/tcp  SSH
80/tcp  HTTP/certbot
443/tcp HTTPS backend
```

Ghi chú triển khai:

- Service backend: `vcam-kimiki-backend.service`
- Service bot: `vcam-kimiki-bot.service`
- Working directory VPS: `/opt/vcam_kimiki`
- Env file VPS: `/etc/vcam_kimiki.env`
- Database VPS: `/opt/vcam_kimiki/vcam.db`


