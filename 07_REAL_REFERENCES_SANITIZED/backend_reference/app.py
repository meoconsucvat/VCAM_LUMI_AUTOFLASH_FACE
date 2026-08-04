from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from recovery_kit.vcam_crypto import (
    LEGACY_BOOTSTRAP_SECRET,
    make_key_seed,
    request_signature,
    response_message,
    sign_response_ed25519,
    sign_response_hmac,
)

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("VCAM_DB", ROOT / "vcam.db"))
KEY_PATH = Path(os.getenv("VCAM_ED25519_KEY", ROOT / "server_ed25519.key"))
BOOTSTRAP_SECRET = os.getenv("VCAM_BOOTSTRAP_SECRET", LEGACY_BOOTSTRAP_SECRET)
CODE_MARKER = os.getenv("VCAM_CODE_MARKER", "tele: @lumierephan")
CODE_MARKERS = [
    marker
    for marker in os.getenv(
        "VCAM_CODE_MARKERS",
        CODE_MARKER + "||" + "tele: @vcamplus   ",
    ).split("||")
    if marker
]
SESSION_HOURS = int(os.getenv("VCAM_SESSION_HOURS", "720"))
ALLOWED_SKEW = int(os.getenv("VCAM_ALLOWED_SKEW", "60"))
PUBLIC_BASE_URL = os.getenv("VCAM_PUBLIC_BASE_URL", "https://lumierevip.net/vcam")
PAIRING_TTL = int(os.getenv("VCAM_PAIRING_TTL", "300"))
LEGACY_RELAY_AUTO_PAIR = os.getenv("VCAM_LEGACY_RELAY_AUTO_PAIR", "0").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
PAIRING_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
BAD_LOGIN_LIMIT = int(os.getenv("VCAM_BAD_LOGIN_LIMIT", "5"))
# Default OFF: do not auto-lock devices after N bad passwords.
BAD_LOGIN_LOCK_ENABLED = os.getenv("VCAM_BAD_LOGIN_LOCK_ENABLED", "0").lower() not in {
    "0",
    "false",
    "no",
    "off",
    "",
}
CONTACT_HANDLE = os.getenv("VCAM_CONTACT_HANDLE", "@vcamplus").strip() or "@vcamplus"
TELEGRAM_BOT_TOKEN = os.getenv("VCAM_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("VCAM_TELEGRAM_CHAT_ID", "")
VERIFY_ALLOW_DEVICE_MISMATCH = os.getenv(
    "VCAM_VERIFY_ALLOW_DEVICE_MISMATCH", "1"
).lower() not in {"0", "false", "no", "off"}
VERIFY_IGNORE_REVOKED = os.getenv(
    "VCAM_VERIFY_IGNORE_REVOKED", "0"
).lower() not in {"0", "false", "no", "off"}

app = FastAPI(title="VcamLumiere compatibility backend", version="1.0")
logger = logging.getLogger("vcam.backend")
if not logger.handlers:
    logging.basicConfig(level=os.getenv("VCAM_LOG_LEVEL", "INFO").upper())


def audit(event: str, **fields: object) -> None:
    safe = {"event": event, "ts": int(time.time()), **fields}
    logger.info(json.dumps(safe, separators=(",", ":"), sort_keys=True))


def telegram_notify(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        urllib.request.urlopen(url, data=data, timeout=5).read()
    except Exception as exc:
        audit("telegram_notify_failed", error=str(exc)[:160])


def contact_suffix() -> str:
    return f"vui lòng liên hệ tele {CONTACT_HANDLE}"


def ui_error_user_not_found() -> str:
    return f"Tài khoản chưa đăng kí {contact_suffix()}"


def ui_error_wrong_password() -> str:
    return f"Sai mật khẩu {contact_suffix()}"


def ui_error_expired() -> str:
    return f"Tài khoản của bạn đã hết hạn {contact_suffix()}"


def ui_error_disabled() -> str:
    return f"Tài khoản đã bị khóa {contact_suffix()}"


def ui_error_device_limit() -> str:
    return f"Tài khoản đã đạt giới hạn thiết bị {contact_suffix()}"


def login_event_notify(
    event: str,
    *,
    username: str = "",
    device_id: str = "",
    fingerprint: str = "",
    model: str = "",
    ios_version: str = "",
    ip: str = "",
    reason: str = "",
    extra: str = "",
) -> None:
    """Admin Telegram alert for important login events. Never includes password."""
    host = PUBLIC_BASE_URL.replace("https://", "").replace("http://", "").replace("/vcam", "")
    lines = [
        f"{'✅' if event == 'login_ok' else '⚠️'} [{host}] {event}",
        f"User: {username or '-'}",
        f"Device ID: {device_id or '-'}",
        f"Fingerprint: {(fingerprint[:24] + '...') if fingerprint else '-'}",
        f"Model: {model or '-'}",
        f"iOS: {ios_version or '-'}",
        f"IP: {ip or '-'}",
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]
    if reason:
        lines.append(f"Reason: {reason}")
    if extra:
        lines.append(extra)
    telegram_notify("\n".join(lines))


def request_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else ""


def ensure_admin_tables(c: sqlite3.Connection) -> None:
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS device_security (
          device_fingerprint TEXT PRIMARY KEY,
          device_id TEXT,
          username TEXT,
          first_ip TEXT,
          last_ip TEXT,
          failed_count INTEGER NOT NULL DEFAULT 0,
          locked INTEGER NOT NULL DEFAULT 0,
          locked_at INTEGER,
          last_seen_at INTEGER,
          note TEXT
        );
        CREATE TABLE IF NOT EXISTS login_events (
          id INTEGER PRIMARY KEY,
          username TEXT,
          device_id TEXT,
          device_fingerprint TEXT,
          ip TEXT,
          ok INTEGER NOT NULL,
          reason TEXT,
          created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_limits (
          username TEXT PRIMARY KEY,
          max_devices INTEGER NOT NULL DEFAULT 1,
          timeout_seconds INTEGER NOT NULL DEFAULT 300,
          updated_at INTEGER NOT NULL
        );
        """
    )


def device_row(c: sqlite3.Connection, fingerprint: str) -> sqlite3.Row | None:
    ensure_admin_tables(c)
    return c.execute(
        "SELECT * FROM device_security WHERE device_fingerprint=?", (fingerprint,)
    ).fetchone()


def record_login_failure(
    c: sqlite3.Connection,
    body: dict,
    ip: str,
    reason: str,
    remember_device: bool = True,
) -> None:
    ensure_admin_tables(c)
    now = int(time.time())
    username = str(body.get("username", ""))
    device_id = str(body.get("device_id", ""))
    fingerprint = str(body.get("device_fingerprint", ""))
    if not fingerprint:
        return
    row = device_row(c, fingerprint)
    failed = (int(row["failed_count"]) if row else 0) + 1
    prev_locked = int(row["locked"]) if row else 0
    if BAD_LOGIN_LOCK_ENABLED:
        locked = 1 if failed >= BAD_LOGIN_LIMIT else prev_locked
        locked_at = (
            now
            if locked and not prev_locked
            else (row["locked_at"] if row else None)
        )
    else:
        # Policy: never auto-lock on bad password. Keep any historical lock bit unchanged
        # only if already set; new rows stay unlocked. failed_count is still recorded.
        locked = 0
        locked_at = None
    if remember_device:
        if row:
            c.execute(
                "UPDATE device_security SET device_id=?,username=?,last_ip=?,failed_count=?,"
                "locked=?,locked_at=?,last_seen_at=? WHERE device_fingerprint=?",
                (device_id, username, ip, failed, locked, locked_at, now, fingerprint),
            )
        else:
            c.execute(
                "INSERT INTO device_security(device_fingerprint,device_id,username,first_ip,last_ip,"
                "failed_count,locked,locked_at,last_seen_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (fingerprint, device_id, username, ip, ip, failed, locked, locked_at, now),
            )
    c.execute(
        "INSERT INTO login_events(username,device_id,device_fingerprint,ip,ok,reason,created_at)"
        " VALUES(?,?,?,?,0,?,?)",
        (username, device_id, fingerprint, ip, reason, now),
    )
    audit(
        "login_failed",
        user=username,
        device_id=device_id,
        fingerprint_prefix=fingerprint[:12],
        ip=ip,
        failed_count=failed,
        locked=bool(locked),
        lock_enabled=BAD_LOGIN_LOCK_ENABLED,
        reason=reason,
    )
    if BAD_LOGIN_LOCK_ENABLED and locked and failed == BAD_LOGIN_LIMIT and not prev_locked:
        telegram_notify(
            "🔒 Khóa thiết bị sau nhiều lần đăng nhập sai\n"
            f"User: {username}\nIP: {ip}\nThiết bị: {device_id}\nFingerprint: {fingerprint}\n"
            f"Limit: {BAD_LOGIN_LIMIT}"
        )


def record_login_success(c: sqlite3.Connection, body: dict, ip: str) -> None:
    ensure_admin_tables(c)
    now = int(time.time())
    username = str(body.get("username", ""))
    device_id = str(body.get("device_id", ""))
    fingerprint = str(body.get("device_fingerprint", ""))
    model = str(body.get("model", ""))
    ios_version = str(body.get("ios_version", ""))
    row = device_row(c, fingerprint)
    old_ip = row["last_ip"] if row else None
    first_ip = row["first_ip"] if row and row["first_ip"] else ip
    c.execute(
        "INSERT INTO device_security(device_fingerprint,device_id,username,first_ip,last_ip,"
        "failed_count,locked,locked_at,last_seen_at) VALUES(?,?,?,?,?,0,0,NULL,?) "
        "ON CONFLICT(device_fingerprint) DO UPDATE SET device_id=excluded.device_id,"
        "username=excluded.username,last_ip=excluded.last_ip,failed_count=0,last_seen_at=excluded.last_seen_at",
        (fingerprint, device_id, username, first_ip, ip, now),
    )
    c.execute(
        "INSERT INTO login_events(username,device_id,device_fingerprint,ip,ok,reason,created_at)"
        " VALUES(?,?,?,?,1,'login_ok',?)",
        (username, device_id, fingerprint, ip, now),
    )
    if old_ip and old_ip != ip:
        telegram_notify(
            "⚠️ Cảnh báo IP Lạ\n"
            f"User: {username}\nIP gốc: {old_ip}\nIP mới: {ip}\nThiết bị: {device_id}"
        )
    user_row = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    user_id = user_row["id"] if user_row else "-"
    login_event_notify(
        "login_ok",
        username=username,
        device_id=device_id,
        fingerprint=fingerprint,
        model=model,
        ios_version=ios_version,
        ip=ip,
        reason="login_ok",
        extra=f"User ID: {user_id}",
    )

@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(DB_PATH)
    try:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = secrets.token_bytes(16) if salt is None else salt
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 250_000)
    return f"pbkdf2-sha256$250000${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def password_ok(password: str, encoded: str) -> bool:
    try:
        alg, rounds, salt, expected = encoded.split("$")
        if alg != "pbkdf2-sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt), int(rounds)
        )
        return hmac.compare_digest(actual, base64.b64decode(expected))
    except Exception:
        return False


def load_or_create_signing_key() -> Ed25519PrivateKey:
    if KEY_PATH.exists():
        return Ed25519PrivateKey.from_private_bytes(KEY_PATH.read_bytes())
    key = Ed25519PrivateKey.generate()
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_PATH.write_bytes(
        key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
    )
    return key


SIGNING_KEY = load_or_create_signing_key()


def initialize() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as c:
        c.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        now = int(time.time())
        if os.getenv("VCAM_DISABLE_INITIAL_SEED", "0") not in {"1", "true", "TRUE", "yes", "YES"}:
            user = os.getenv("VCAM_INITIAL_USER", "admin")
            password = os.getenv("VCAM_INITIAL_PASSWORD", "change-me-now")
            c.execute(
                "INSERT OR IGNORE INTO users(username,password_hash,created_at) VALUES(?,?,?)",
                (user, password_hash(password), now),
            )
            relay_user = os.getenv("VCAM_RELAY_USER", user)
            relay_password = os.getenv("VCAM_RELAY_PASSWORD", password)
            owner = c.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()
            c.execute(
                "INSERT OR IGNORE INTO relay_credentials(username,password_hash,user_id) VALUES(?,?,?)",
                (relay_user, password_hash(relay_password), owner[0]),
            )


initialize()


def utc_expiry() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)).isoformat().replace("+00:00", "Z")


def current_epoch() -> int:
    return int(time.time()) // 3600


def session_key_seed(session: sqlite3.Row, epoch: int) -> str:
    return make_key_seed(
        SIGNING_KEY,
        session["device_id"],
        session["device_fingerprint"],
        epoch,
        PUBLIC_BASE_URL,
    )


async def raw_json(request: Request) -> tuple[bytes, dict]:
    raw = await request.body()
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError
        return raw, obj
    except Exception:
        raise ValueError("invalid JSON object")


def signed_response(fields: list[object], secret: str, extra: dict) -> dict:
    out = dict(extra)
    out["server_sig"] = sign_response_hmac(secret, fields)
    out["ed25519_sig"] = sign_response_ed25519(SIGNING_KEY, fields)
    return out


def request_auth_ok(request: Request, raw: bytes, secret: str, fingerprint: str) -> bool:
    ts = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    supplied = request.headers.get("X-Signature", "")
    try:
        if abs(int(time.time()) - int(ts)) > ALLOWED_SKEW:
            return False
    except ValueError:
        return False
    if len(nonce) != 32:
        return False
    body_text = raw.decode("utf-8")
    for marker in CODE_MARKERS:
        expected = request_signature(
            secret,
            request.method,
            request.url.path.removeprefix("/vcam"),
            ts,
            nonce,
            fingerprint,
            body_text,
            marker,
        )
        if hmac.compare_digest(supplied.lower(), expected):
            return True
    return False


def consume_nonce(fingerprint: str, path: str, timestamp: str, nonce: str) -> bool:
    now = int(time.time())
    try:
        with db() as c:
            c.execute("DELETE FROM request_nonces WHERE created_at<?", (now - ALLOWED_SKEW * 2,))
            c.execute(
                "INSERT INTO request_nonces(fingerprint,path,nonce,timestamp,created_at) VALUES(?,?,?,?,?)",
                (fingerprint, path, nonce, int(timestamp), now),
            )
        return True
    except (sqlite3.IntegrityError, ValueError):
        audit("request_replay_rejected", path=path, fingerprint_prefix=fingerprint[:12])
        return False


def authenticated_request(request: Request, raw: bytes, secret: str, fingerprint: str) -> bool:
    if not request_auth_ok(request, raw, secret, fingerprint):
        audit("request_signature_rejected", path=request.url.path,
              fingerprint_prefix=fingerprint[:12])
        return False
    return consume_nonce(
        fingerprint,
        request.url.path,
        request.headers.get("X-Timestamp", ""),
        request.headers.get("X-Nonce", ""),
    )


def pairing_hash(code: str) -> str:
    return hmac.new(
        BOOTSTRAP_SECRET.encode(), ("vcam-pair-v1:" + code.upper()).encode(), hashlib.sha256
    ).hexdigest()


def new_pairing_code() -> str:
    return "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(8))


@app.get("/health")
def health() -> dict:
    pub = SIGNING_KEY.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return {
        "ok": True,
        "version": app.version,
        "public_base_url": PUBLIC_BASE_URL,
        "ed25519_public_key_b64": base64.b64encode(pub).decode(),
    }


@app.post("/vcam/login")
async def login(request: Request):
    try:
        raw, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    required = ("username", "password", "device_id", "device_fingerprint", "ios_version", "model")
    if any(not isinstance(body.get(k), str) or not body[k] for k in required):
        return JSONResponse({"error": "bad_request"}, 400)
    ip = request_ip(request)
    username = body["username"]
    device_id = body["device_id"]
    fingerprint = body["device_fingerprint"]
    model = body.get("model", "")
    ios_version = body.get("ios_version", "")
    if not authenticated_request(request, raw, BOOTSTRAP_SECRET, fingerprint):
        login_event_notify(
            "bad_signature",
            username=username,
            device_id=device_id,
            fingerprint=fingerprint,
            model=model,
            ios_version=ios_version,
            ip=ip,
            reason="request_signature_rejected",
        )
        return JSONResponse({"error": "bad_signature"}, 401)
    with db() as c:
        ensure_admin_tables(c)
        locked = device_row(c, fingerprint)
        user = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not user:
            record_login_failure(c, body, ip, "user_not_found")
            login_event_notify(
                "user_not_found",
                username=username,
                device_id=device_id,
                fingerprint=fingerprint,
                model=model,
                ios_version=ios_version,
                ip=ip,
                reason="user_not_found",
            )
            return JSONResponse({"error": ui_error_user_not_found()}, 200)
        if not user["enabled"]:
            record_login_failure(c, body, ip, "user_disabled")
            login_event_notify(
                "user_disabled",
                username=username,
                device_id=device_id,
                fingerprint=fingerprint,
                model=model,
                ios_version=ios_version,
                ip=ip,
                reason="user_disabled",
            )
            return JSONResponse({"error": ui_error_disabled()}, 200)
        if not password_ok(body["password"], user["password_hash"]):
            record_login_failure(c, body, ip, "wrong_password")
            login_event_notify(
                "wrong_password",
                username=username,
                device_id=device_id,
                fingerprint=fingerprint,
                model=model,
                ios_version=ios_version,
                ip=ip,
                reason="wrong_password",
            )
            return JSONResponse({"error": ui_error_wrong_password()}, 200)
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if user["expires_at"] and user["expires_at"] < now_iso:
            record_login_failure(c, body, ip, "user_expired")
            login_event_notify(
                "user_expired",
                username=username,
                device_id=device_id,
                fingerprint=fingerprint,
                model=model,
                ios_version=ios_version,
                ip=ip,
                reason="user_expired",
                extra=f"Expires: {user['expires_at']}",
            )
            return JSONResponse({"error": ui_error_expired()}, 200)
        # Historical device locks (when VCAM_BAD_LOGIN_LOCK_ENABLED was on): unlock on good login.
        if locked and locked["locked"]:
            c.execute(
                """
                UPDATE device_security
                SET failed_count=0,locked=0,locked_at=NULL,note=NULL,
                    username=?,device_id=?,last_ip=?,last_seen_at=?
                WHERE device_fingerprint=?
                """,
                (
                    username,
                    device_id,
                    ip,
                    int(time.time()),
                    fingerprint,
                ),
            )
            telegram_notify(
                "✅ Thiết bị bị khóa đã được mở lại bằng thông tin đăng nhập đúng\n"
                f"User: {username}\nIP: {ip}\nThiết bị: {device_id}"
            )
        limits = c.execute(
            "SELECT max_devices,timeout_seconds FROM user_limits WHERE username=?",
            (username,),
        ).fetchone()
        max_devices = int(limits["max_devices"]) if limits else 1
        known_device = c.execute(
            "SELECT 1 FROM device_security WHERE username=? AND device_fingerprint=?",
            (username, fingerprint),
        ).fetchone()
        used_devices = c.execute(
            "SELECT COUNT(DISTINCT device_fingerprint) FROM device_security WHERE username=?",
            (username,),
        ).fetchone()[0]
        if not known_device and used_devices >= max_devices:
            record_login_failure(c, body, ip, "device_limit", remember_device=False)
            login_event_notify(
                "device_limit",
                username=username,
                device_id=device_id,
                fingerprint=fingerprint,
                model=model,
                ios_version=ios_version,
                ip=ip,
                reason="device_limit",
                extra=f"Đã dùng: {used_devices}/{max_devices}",
            )
            return JSONResponse({"error": ui_error_device_limit()}, 200)
        token = secrets.token_hex(32)
        session_secret = secrets.token_hex(32)
        expires = utc_expiry()
        if user["expires_at"] and user["expires_at"] < expires:
            expires = user["expires_at"]
        c.execute(
            "INSERT INTO sessions(token,user_id,device_id,device_fingerprint,signing_key,expires_at,created_at) VALUES(?,?,?,?,?,?,?)",
            (token, user["id"], device_id, fingerprint, session_secret, expires, int(time.time())),
        )
        record_login_success(c, body, ip)
    server_ts = int(time.time())
    nonce = request.headers["X-Nonce"]
    fields = ["login_ok", nonce, str(server_ts), device_id, token, expires]
    audit("login_succeeded", user=username, device_id=device_id,
          fingerprint_prefix=fingerprint[:12])
    return signed_response(fields, BOOTSTRAP_SECRET, {
        "token": token,
        "signing_key": session_secret,
        "nonce_echo": nonce,
        "server_ts": server_ts,
        "expires_at": expires,
    })


@app.post("/vcam/verify")
async def verify(request: Request):
    try:
        raw, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    token = body.get("token")
    device_id = body.get("device_id")
    with db() as c:
        session = c.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
        if not session:
            return JSONResponse({"error": "missing_auth"}, 200)
        if not authenticated_request(request, raw, session["signing_key"], session["device_fingerprint"]):
            return JSONResponse({"error": "bad_signature"}, 401)
        revoked = bool(session["revoked"])
        device_matches = device_id == session["device_id"]
        if revoked and not VERIFY_IGNORE_REVOKED:
            valid = False
            reason = "revoked"
        elif not device_matches and not VERIFY_ALLOW_DEVICE_MISMATCH:
            valid = False
            reason = "device_mismatch"
        else:
            valid = True
            reason = ""
        server_ts = int(time.time())
        nonce = request.headers["X-Nonce"]
        expires = session["expires_at"]
        # Both the UI and daemon verify this exact six-field order:
        # status|nonce_echo|server_ts|device_id|expires_at|reason
        fields = [
            "valid" if valid else "invalid",
            nonce,
            str(server_ts),
            session["device_id"],
            expires,
            reason,
        ]
        extra = {
            "valid": valid,
            "nonce_echo": nonce,
            "server_ts": server_ts,
            "expires_at": expires,
            "reason": reason,
        }
        if valid:
            epoch = current_epoch()
            extra.update({"key_seed": session_key_seed(session, epoch), "epoch_hour": epoch})
            c.execute("UPDATE sessions SET last_verify_at=? WHERE token=?", (server_ts, token))
            audit(
                "verify_succeeded",
                device_id=session["device_id"],
                request_device_id=device_id,
                device_mismatch=not device_matches,
                revoked_bypassed=revoked and VERIFY_IGNORE_REVOKED,
                epoch_hour=epoch,
            )
        else:
            audit(
                "verify_rejected",
                device_id=session["device_id"],
                request_device_id=device_id,
                reason=reason,
                revoked=revoked,
                device_mismatch=not device_matches,
            )
        return signed_response(fields, session["signing_key"], extra)


@app.post("/vcam/logout")
async def logout(request: Request):
    try:
        raw, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    with db() as c:
        session = c.execute("SELECT * FROM sessions WHERE token=?", (body.get("token"),)).fetchone()
        if not session or not authenticated_request(
            request, raw, session["signing_key"], session["device_fingerprint"]
        ):
            return JSONResponse({"error": "bad_signature"}, 401)
        c.execute("UPDATE sessions SET revoked=1 WHERE token=?", (session["token"],))
        c.execute("DELETE FROM relay_pairings WHERE session_token=?", (session["token"],))
        c.execute(
            "UPDATE pairing_codes SET claimed_at=COALESCE(claimed_at,?) WHERE session_token=?",
            (int(time.time()), session["token"]),
        )
    audit("logout_succeeded", device_id=session["device_id"])
    return {"ok": True}


@app.post("/vcam/relay_login")
async def relay_login(request: Request):
    try:
        _, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    with db() as c:
        row = c.execute("SELECT * FROM relay_credentials WHERE username=?", (body.get("username"),)).fetchone()
        if not row or not row["enabled"] or not password_ok(str(body.get("password", "")), row["password_hash"]):
            return JSONResponse({"error": "invalid_credentials"}, 401)
        existing = c.execute(
            "SELECT relay_key FROM relay_tokens WHERE credential_id=? AND revoked=0 "
            "ORDER BY created_at DESC LIMIT 1",
            (row["id"],),
        ).fetchone()
        if existing:
            relay_key = existing["relay_key"]
        else:
            relay_key = secrets.token_hex(32)
            c.execute(
                "INSERT INTO relay_tokens(relay_key,credential_id,created_at) VALUES(?,?,?)",
                (relay_key, row["id"], int(time.time())),
            )
    audit("relay_login_succeeded", user=body.get("username"), reused=bool(existing))
    return {"relay_key": relay_key}


@app.post("/vcam/pair/create")
async def pair_create(request: Request):
    try:
        raw, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    token = body.get("token")
    device_id = body.get("device_id")
    with db() as c:
        session = c.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
        if not session or session["revoked"] or device_id != session["device_id"]:
            return JSONResponse({"error": "missing_auth"}, 401)
        if not authenticated_request(
            request, raw, session["signing_key"], session["device_fingerprint"]
        ):
            return JSONResponse({"error": "bad_signature"}, 401)
        now = int(time.time())
        c.execute(
            "UPDATE pairing_codes SET claimed_at=? WHERE session_token=? AND claimed_at IS NULL",
            (now, token),
        )
        for _ in range(10):
            code = new_pairing_code()
            try:
                c.execute(
                    "INSERT INTO pairing_codes(code_hash,session_token,expires_at,created_at) VALUES(?,?,?,?)",
                    (pairing_hash(code), token, now + PAIRING_TTL, now),
                )
                break
            except sqlite3.IntegrityError:
                continue
        else:
            return JSONResponse({"error": "pairing_code_generation_failed"}, 500)
    audit("pairing_created", device_id=device_id, expires_in=PAIRING_TTL)
    return {"pairing_code": code, "expires_in": PAIRING_TTL}


@app.post("/vcam/pair/claim")
async def pair_claim(request: Request):
    try:
        _, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    relay_key = body.get("relay_key")
    code = str(body.get("pairing_code", "")).upper()
    now = int(time.time())
    with db() as c:
        relay = c.execute(
            "SELECT t.*,r.user_id FROM relay_tokens t "
            "JOIN relay_credentials r ON r.id=t.credential_id WHERE t.relay_key=?",
            (relay_key,),
        ).fetchone()
        if not relay or relay["revoked"]:
            return JSONResponse({"error": "invalid_relay_key"}, 401)
        pairing = c.execute(
            "SELECT p.*,s.user_id,s.revoked,s.device_id FROM pairing_codes p "
            "JOIN sessions s ON s.token=p.session_token WHERE p.code_hash=?",
            (pairing_hash(code),),
        ).fetchone()
        if (
            not pairing or pairing["claimed_at"] is not None or pairing["expires_at"] < now
            or pairing["revoked"] or pairing["user_id"] != relay["user_id"]
        ):
            audit("pairing_claim_rejected", reason="invalid_or_expired")
            return JSONResponse({"error": "invalid_pairing_code"}, 409)
        updated = c.execute(
            "UPDATE pairing_codes SET claimed_at=? WHERE id=? AND claimed_at IS NULL",
            (now, pairing["id"]),
        )
        if updated.rowcount != 1:
            return JSONResponse({"error": "pairing_already_claimed"}, 409)
        c.execute(
            "INSERT INTO relay_pairings(relay_key,session_token,paired_at) VALUES(?,?,?) "
            "ON CONFLICT(relay_key) DO UPDATE SET session_token=excluded.session_token,"
            "paired_at=excluded.paired_at",
            (relay_key, pairing["session_token"], now),
        )
    audit("pairing_claimed", device_id=pairing["device_id"])
    return {"ok": True}


@app.post("/vcam/stream_key")
async def stream_key(request: Request):
    try:
        _, body = await raw_json(request)
    except ValueError:
        return JSONResponse({"error": "bad_json"}, 400)
    with db() as c:
        row = c.execute(
            "SELECT t.*,r.user_id,p.session_token FROM relay_tokens t "
            "JOIN relay_credentials r ON r.id=t.credential_id "
            "LEFT JOIN relay_pairings p ON p.relay_key=t.relay_key WHERE t.relay_key=?",
            (body.get("relay_key"),),
        ).fetchone()
        if not row or row["revoked"]:
            return JSONResponse({"error": "invalid_relay_key"}, 401)
        if row["session_token"]:
            session = c.execute(
                "SELECT * FROM sessions WHERE token=? AND user_id=? AND revoked=0",
                (row["session_token"], row["user_id"]),
            ).fetchone()
        elif LEGACY_RELAY_AUTO_PAIR:
            # Compatibility mode for the original Windows relay.exe.
            #
            # Frida evidence from the original relay shows it only sends
            # {"relay_key": "..."} to /vcam/stream_key and does not know the
            # newer /pair/create + /pair/claim flow.  In legacy mode we bind
            # it implicitly to the newest active session for the same owner.
            session = c.execute(
                "SELECT * FROM sessions WHERE user_id=? AND revoked=0 "
                "ORDER BY COALESCE(last_verify_at, created_at) DESC, created_at DESC LIMIT 1",
                (row["user_id"],),
            ).fetchone()
            if session:
                c.execute(
                    "INSERT INTO relay_pairings(relay_key,session_token,paired_at) VALUES(?,?,?) "
                    "ON CONFLICT(relay_key) DO UPDATE SET session_token=excluded.session_token,"
                    "paired_at=excluded.paired_at",
                    (row["relay_key"], session["token"], int(time.time())),
                )
                audit("legacy_relay_auto_paired", device_id=session["device_id"])
        else:
            return JSONResponse({"error": "relay_not_paired"}, 409)
        if not session:
            return JSONResponse({"error": "No active device"}, 409)
        epoch = current_epoch()
        seed = session_key_seed(session, epoch)
        c.execute("UPDATE relay_tokens SET last_refresh_at=? WHERE relay_key=?", (int(time.time()), row["relay_key"]))
    audit("stream_key_issued", device_id=session["device_id"], epoch_hour=epoch)
    return {"key_seed": seed, "epoch_hour": epoch}
