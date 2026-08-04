#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-}"
BACKEND_SERVICE="${2:-vcam-backend.service}"
BOT_SERVICE="${3:-vcam-telegram-bot.service}"

if [[ -z "$BASE_URL" ]]; then
  echo "Usage: ./check_backend.sh https://your.domain/health [backend.service] [bot.service]"
  exit 1
fi

echo "== HTTP health =="
curl -i "$BASE_URL"

echo
echo "== systemd backend =="
sudo systemctl status "$BACKEND_SERVICE" --no-pager || true

echo
echo "== systemd bot =="
sudo systemctl status "$BOT_SERVICE" --no-pager || true

echo
echo "== backend logs =="
sudo journalctl -u "$BACKEND_SERVICE" -n 80 --no-pager || true

echo
echo "== bot logs =="
sudo journalctl -u "$BOT_SERVICE" -n 80 --no-pager || true

