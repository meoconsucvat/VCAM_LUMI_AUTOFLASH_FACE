# VPS Deploy Runbook

## Trước khi deploy

Xác nhận:

- Domain đã trỏ đúng VPS IP.
- Port VPS mở: `22`, `80`, `443`.
- SSH key dùng được.
- Có bot token/admin ID.
- Backend source đã sẵn sàng.

## Cài package cơ bản

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx sqlite3
```

## Tạo thư mục app

```bash
sudo mkdir -p /opt/<PROJECT_NAME>
sudo chown -R ubuntu:ubuntu /opt/<PROJECT_NAME>
```

Copy backend vào `/opt/<PROJECT_NAME>`.

## Python venv

```bash
cd /opt/<PROJECT_NAME>
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Env

Tạo:

```text
/opt/<PROJECT_NAME>/.env
```

Dựa theo:

```text
03_SERVER_TEMPLATES/ENV_TEMPLATE.env
```

## Systemd

Copy service:

```bash
sudo cp vcam-backend.service /etc/systemd/system/
sudo cp vcam-telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vcam-backend.service
sudo systemctl enable --now vcam-telegram-bot.service
```

## Nginx + TLS

```bash
sudo cp nginx.conf /etc/nginx/sites-available/<PROJECT_NAME>.conf
sudo ln -s /etc/nginx/sites-available/<PROJECT_NAME>.conf /etc/nginx/sites-enabled/<PROJECT_NAME>.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d <CLIENT_API_SUBDOMAIN>
```

## Check

```bash
curl -i https://<CLIENT_API_SUBDOMAIN>/health
sudo systemctl status vcam-backend.service
sudo systemctl status vcam-telegram-bot.service
sudo journalctl -u vcam-backend.service -n 100 --no-pager
sudo journalctl -u vcam-telegram-bot.service -n 100 --no-pager
```



