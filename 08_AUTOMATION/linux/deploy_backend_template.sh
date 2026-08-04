#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-vcam-client}"
APP_DIR="/opt/${PROJECT_NAME}"
SERVICE_BACKEND="${SERVICE_BACKEND:-vcam-backend.service}"
SERVICE_BOT="${SERVICE_BOT:-vcam-telegram-bot.service}"

echo "Deploying to $APP_DIR"

sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx sqlite3

sudo mkdir -p "$APP_DIR"
sudo chown -R "$USER:$USER" "$APP_DIR"

echo "Copy backend files to $APP_DIR before continuing if they are not present."
if [[ ! -f "$APP_DIR/requirements.txt" ]]; then
  echo "Missing $APP_DIR/requirements.txt"
  exit 1
fi

cd "$APP_DIR"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Missing $APP_DIR/.env"
  echo "Create it from ENV_TEMPLATE.env first."
  exit 1
fi

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_BACKEND"
sudo systemctl enable --now "$SERVICE_BOT"
sudo systemctl status "$SERVICE_BACKEND" --no-pager || true
sudo systemctl status "$SERVICE_BOT" --no-pager || true

