"""Local smoke tests for Phase 1 login error strings + bot parsers. No secrets needed."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_module(name: str, path: Path, extra_env: dict[str, str] | None = None):
    env_backup = dict(os.environ)
    try:
        if extra_env:
            os.environ.update(extra_env)
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_ui_errors():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        key = td_path / "server_ed25519.key"
        # app.py creates key if missing via cryptography
        env = {
            "VCAM_DB": str(td_path / "vcam.db"),
            "VCAM_ED25519_KEY": str(key),
            "VCAM_DISABLE_INITIAL_SEED": "1",
            "VCAM_BAD_LOGIN_LOCK_ENABLED": "0",
            "VCAM_CONTACT_HANDLE": "@khachABC",
            "VCAM_TELEGRAM_BOT_TOKEN": "",
            "VCAM_TELEGRAM_CHAT_ID": "",
            "VCAM_PUBLIC_BASE_URL": "https://hai.leixi.bond/vcam",
        }
        # Ensure recovery_kit importable
        sys.path.insert(0, str(ROOT))
        app = load_module("vcam_app_phase1", ROOT / "app.py", env)
        assert app.CONTACT_HANDLE == "@khachABC"
        assert app.BAD_LOGIN_LOCK_ENABLED is False
        assert app.ui_error_user_not_found() == "Tài khoản chưa đăng kí vui lòng liên hệ tele @khachABC"
        assert app.ui_error_wrong_password() == "Sai mật khẩu vui lòng liên hệ tele @khachABC"
        assert app.ui_error_expired() == "Tài khoản của bạn đã hết hạn vui lòng liên hệ tele @khachABC"
        assert app.ui_error_disabled() == "Tài khoản đã bị khóa vui lòng liên hệ tele @khachABC"
        assert app.ui_error_device_limit() == "Tài khoản đã đạt giới hạn thiết bị vui lòng liên hệ tele @khachABC"
        print("ui_errors_ok contact=@khachABC")


def test_bot_add_parse_and_format():
    # Load bot module without executing main loop: only functions, env required at import
    env = {
        "VCAM_TELEGRAM_BOT_TOKEN": "000:test",
        "VCAM_TELEGRAM_CHAT_ID": "1",
        "VCAM_DB": str(ROOT / "_smoke_bot.db"),
    }
    # bot imports TOKEN at module level — set env before load
    for k, v in env.items():
        os.environ[k] = v
    # Import by reading and exec only needed? simpler: importlib after env set
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    # Avoid starting main: load as module
    import importlib.util

    spec = importlib.util.spec_from_file_location("vcam_bot_phase1", ROOT / "vcam_telegram_admin_bot.py")
    assert spec and spec.loader
    bot = importlib.util.module_from_spec(spec)
    # Prevent main from running — file only runs main under __main__
    spec.loader.exec_module(bot)
    u, p, d, m, t = bot.parse_add_args("loki secret 30")
    assert (u, p, d, m, t) == ("loki", "secret", 30, 1, 300)
    u, p, d, m, t = bot.parse_add_args("loki secret 7 2 600")
    assert (u, p, d, m, t) == ("loki", "secret", 7, 2, 600)
    # add_user against temp db (bot assumes app schema already exists in production)
    db_path = ROOT / "_smoke_bot.db"
    if db_path.exists():
        db_path.unlink()
    os.environ["VCAM_DB"] = str(db_path)
    import sqlite3

    with sqlite3.connect(db_path) as c:
        c.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        c.commit()
    msg = bot.add_user("smokeuser", "smokepass", 10, 1, 300)
    assert "Đã" in msg and "thành công" in msg
    assert "👤 User: smokeuser" in msg
    assert "🔑 Pass: smokepass" in msg
    assert "🔒 Khóa tối đa: 1 thiết bị" in msg
    # hard delete
    del_msg = bot.delete_user("smokeuser")
    assert "xóa vĩnh viễn" in del_msg.lower() or "Xóa vĩnh viễn" in del_msg
    users = bot.cmd_users()
    assert "smokeuser" not in users
    print("bot_add_del_ok")
    help_t = bot.help_text()
    assert "VCAM_BAD_LOGIN_LOCK_ENABLED=0" in help_t or "KHÔNG tự khóa" in help_t
    print("bot_help_ok")


if __name__ == "__main__":
    test_ui_errors()
    test_bot_add_parse_and_format()
    print("SMOKE_OK")
