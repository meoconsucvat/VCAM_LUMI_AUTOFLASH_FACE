from pathlib import Path

app = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
bot = Path(__file__).with_name("vcam_telegram_admin_bot.py").read_text(encoding="utf-8")
checks = {
    "BAD_LOGIN_LOCK_ENABLED": "BAD_LOGIN_LOCK_ENABLED" in app,
    "CONTACT_HANDLE": "CONTACT_HANDLE" in app,
    "ui_error_user_not_found": "ui_error_user_not_found" in app,
    "login_event_notify": "login_event_notify" in app,
    "user_not_found branch": '"user_not_found"' in app,
    "wrong_password branch": '"wrong_password"' in app,
    "login_ok notify": '"login_ok"' in app and "login_event_notify" in app,
    "add success format": "thành công" in bot,
    "purge_expired": "purge_expired" in bot,
    "hard delete help": "VĨNH VIỄN" in bot or "vĩnh viễn" in bot,
}
for k, v in checks.items():
    print(f"{k}: {v}")
assert all(checks.values()), checks
print("ALL_MARKERS_OK")
