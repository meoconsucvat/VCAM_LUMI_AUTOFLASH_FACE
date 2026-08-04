from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone


TOKEN = os.environ["VCAM_TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = str(os.environ["VCAM_TELEGRAM_CHAT_ID"])
DB_PATH = os.environ.get("VCAM_DB", "/var/lib/vcam/vcam.db")
BASE_URL = os.environ.get("VCAM_PUBLIC_BASE_URL", "")
API = f"https://api.telegram.org/bot{TOKEN}"

STATE: dict[str, str] = {}

BTN_USERS = "\ud83d\udccb Users"
BTN_STATUS = "\ud83d\udcca Status"
BTN_ADD = "\u2795 Add user"
BTN_FIND = "\ud83d\udd0e T\u00ecm user"
BTN_CLEAR = "\ud83e\uddf9 Clear m\u00e1y"
BTN_DELETE = "\ud83d\uddd1 X\u00f3a user"
BTN_EXPIRED = "\u231b X\u00f3a h\u1ebft h\u1ea1n"
BTN_HELP = "❓ Help"


def db() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    ensure_tables(c)
    return c


def ensure_tables(c: sqlite3.Connection) -> None:
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
          updated_at INTEGER NOT NULL,
          display_password TEXT
        );
        """
    )
    cols = {row[1] for row in c.execute("PRAGMA table_info(user_limits)")}
    if "display_password" not in cols:
        c.execute("ALTER TABLE user_limits ADD COLUMN display_password TEXT")


def remaining_text(expires_at: str | None) -> str:
    if not expires_at:
        return "N/A"
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = exp - now
        if delta.total_seconds() <= 0:
            return "\u274c Da het han"
        days = delta.days
        hours = delta.seconds // 3600
        return f"{days} ngay {hours} gio"
    except Exception:
        return "N/A"


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = secrets.token_bytes(16) if salt is None else salt
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 250_000)
    return f"pbkdf2-sha256$250000${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def tg(method: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=35) as r:
        return json.loads(r.read())


def send(chat_id: str, text: str, keyboard: bool = True) -> None:
    payload: dict = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if keyboard:
        payload["reply_markup"] = {
            "keyboard": [
                [{"text": BTN_USERS}, {"text": BTN_STATUS}],
                [{"text": BTN_ADD}, {"text": BTN_FIND}],
                [{"text": BTN_CLEAR}, {"text": BTN_DELETE}],
                [{"text": BTN_EXPIRED}, {"text": BTN_HELP}],
            ],
            "resize_keyboard": True,
        }
    try:
        tg("sendMessage", payload)
    except Exception as exc:
        print(f"telegram_send_failed: {type(exc).__name__}: {exc}", flush=True)


def is_admin(msg: dict) -> bool:
    chat_id = str(msg.get("chat", {}).get("id", ""))
    from_id = str(msg.get("from", {}).get("id", ""))
    return chat_id == ADMIN_CHAT_ID or from_id == ADMIN_CHAT_ID


def fmt_time(ts: int | None) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def cmd_users() -> str:
    with db() as c:
        rows = c.execute(
            """
            SELECT u.id,u.username,u.enabled,u.expires_at,
                   COUNT(DISTINCT s.token) AS sessions,
                   COUNT(DISTINCT d.device_fingerprint) AS devices,
                   COALESCE(l.max_devices, 1) AS max_devices,
                   COALESCE(l.timeout_seconds, 300) AS timeout_seconds,
                   COALESCE(l.display_password, '') AS display_password
            FROM users u LEFT JOIN sessions s ON s.user_id=u.id AND s.revoked=0
            LEFT JOIN device_security d ON d.username=u.username
            LEFT JOIN user_limits l ON l.username=u.username
            GROUP BY u.id ORDER BY u.id ASC LIMIT 50
            """
        ).fetchall()
        total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if not rows:
        return "Chua co user."
    lines = [f"\U0001f465 Danh sach Users ({total})"]
    for r in rows:
        remain = remaining_text(r["expires_at"])
        if not r["enabled"]:
            remain = "\u274c Da het han"
        password = r["display_password"] or "-"
        lines.append("")
        lines.append(f"\U0001f464 {r['id']} | {r['username']} | {remain}")
        lines.append(f"   \U0001f511 {password} | \U0001f4f1 {r['devices']}/{r['max_devices']} | \u23f1 {r['timeout_seconds']}s")
    return "\n".join(lines)

def cmd_status() -> str:
    with db() as c:
        users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        online = c.execute("SELECT COUNT(DISTINCT user_id) FROM sessions WHERE revoked=0").fetchone()[0]
        devices = c.execute("SELECT COUNT(*) FROM device_security").fetchone()[0]
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
    return (
        "\U0001f4ca Trang thai VCAM\n"
        f"\U0001f465 Users: {users}\n"
        f"\U0001f4f1 User online: {online}\n"
        f"\U0001f510 Thiet bi ghi nhan: {devices}\n"
        f"\U0001f550 {now}"
    )

def parse_add_args(text: str) -> tuple[str, str, int, int, int]:
    parts = text.split()
    if len(parts) not in {3, 5}:
        raise ValueError("Cú pháp: /add user pass ngày [số_máy timeout]")
    username, password = parts[0], parts[1]
    days = int(parts[2])
    max_devices = int(parts[3]) if len(parts) == 5 else 1
    timeout_seconds = int(parts[4]) if len(parts) == 5 else 300
    if days <= 0 or max_devices <= 0 or timeout_seconds <= 0:
        raise ValueError("ngày, số_máy, timeout phải lớn hơn 0")
    return username, password, days, max_devices, timeout_seconds


def add_user(username: str, password: str, days: int, max_devices: int = 1, timeout_seconds: int = 300) -> str:
    now = int(time.time())
    expires_iso = datetime.fromtimestamp(now + days * 86400, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with db() as c:
        row = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        ph = password_hash(password)
        if row:
            user_id = row["id"]
            c.execute("UPDATE users SET password_hash=?,enabled=1,expires_at=? WHERE id=?", (ph, expires_iso, user_id))
            action = "cập nhật"
        else:
            c.execute(
                "INSERT INTO users(username,password_hash,enabled,expires_at,created_at) VALUES(?,?,1,?,?)",
                (username, ph, expires_iso, now),
            )
            user_id = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()["id"]
            action = "tạo mới"
        relay = c.execute("SELECT id FROM relay_credentials WHERE username=?", (username,)).fetchone()
        rph = password_hash(password)
        if relay:
            c.execute(
                "UPDATE relay_credentials SET password_hash=?,user_id=?,enabled=1 WHERE id=?",
                (rph, user_id, relay["id"]),
            )
        else:
            c.execute(
                "INSERT INTO relay_credentials(username,password_hash,user_id,enabled) VALUES(?,?,?,1)",
                (username, rph, user_id),
            )
        c.execute(
            "INSERT INTO user_limits(username,max_devices,timeout_seconds,updated_at,display_password) VALUES(?,?,?,?,?) "
            "ON CONFLICT(username) DO UPDATE SET max_devices=excluded.max_devices,"
            "timeout_seconds=excluded.timeout_seconds,updated_at=excluded.updated_at,"
            "display_password=excluded.display_password",
            (username, max_devices, timeout_seconds, now, password),
        )
        c.commit()
    return (
        f"✅ Đã {action} thành công\n"
        f"👤 User: {username}\n"
        f"🔑 Pass: {password}\n"
        f"⏳ Hạn: {days} ngày\n"
        f"📅 Ngày hết hạn: {expires_iso}\n"
        f"🔒 Khóa tối đa: {max_devices} thiết bị\n"
        f"⏱ Timeout: {timeout_seconds}s"
    )

def find_user(term: str) -> str:
    like = f"%{term}%"
    with db() as c:
        users = c.execute(
            "SELECT * FROM users WHERE username LIKE ? OR id LIKE ? ORDER BY id DESC LIMIT 10",
            (like, like),
        ).fetchall()
        devices = c.execute(
            """
            SELECT * FROM device_security
            WHERE username LIKE ? OR device_id LIKE ? OR device_fingerprint LIKE ? OR last_ip LIKE ?
            ORDER BY last_seen_at DESC LIMIT 10
            """,
            (like, like, like, like),
        ).fetchall()
    lines = [f"🔎 Tìm: {term}"]
    for u in users:
        lines.append(f"User #{u['id']}: {u['username']} enabled={u['enabled']} exp={u['expires_at'] or '-'}")
    for d in devices:
        lines.append(
            "Device: "
            f"user={d['username']} locked={d['locked']} fail={d['failed_count']} "
            f"ip={d['last_ip'] or '-'} id={d['device_id'] or '-'} fp={d['device_fingerprint'][:16]}..."
        )
    return "\n".join(lines) if len(lines) > 1 else "Không tìm thấy."


def clear_device(term: str) -> str:
    like = f"%{term}%"
    with db() as c:
        cur = c.execute(
            """
            UPDATE device_security SET failed_count=0,locked=0,locked_at=NULL,note=NULL
            WHERE username LIKE ? OR device_id LIKE ? OR device_fingerprint LIKE ? OR last_ip LIKE ?
            """,
            (like, like, like, like),
        )
        c.commit()
        count = cur.rowcount
    return f"🧹 Đã clear {count} thiết bị khớp: {term}"


def placeholders(values: list[object]) -> str:
    return ",".join("?" for _ in values)


def hard_delete_user_rows(c: sqlite3.Connection, user_rows: list[sqlite3.Row]) -> dict[str, int]:
    if not user_rows:
        return {
            "users": 0,
            "sessions": 0,
            "relay_credentials": 0,
            "relay_tokens": 0,
            "relay_pairings": 0,
            "pairing_codes": 0,
            "device_security": 0,
            "request_nonces": 0,
            "login_events": 0,
            "user_limits": 0,
        }

    user_ids = [row["id"] for row in user_rows]
    usernames = [row["username"] for row in user_rows]

    session_rows = c.execute(
        f"SELECT token,device_fingerprint FROM sessions WHERE user_id IN ({placeholders(user_ids)})",
        user_ids,
    ).fetchall()
    session_tokens = [row["token"] for row in session_rows]

    device_rows = c.execute(
        f"SELECT device_fingerprint FROM device_security WHERE username IN ({placeholders(usernames)})",
        usernames,
    ).fetchall()
    fingerprints = list(
        {
            row["device_fingerprint"]
            for row in list(session_rows) + list(device_rows)
            if row["device_fingerprint"]
        }
    )

    relay_cred_rows = c.execute(
        f"""
        SELECT id FROM relay_credentials
        WHERE user_id IN ({placeholders(user_ids)})
           OR username IN ({placeholders(usernames)})
        """,
        user_ids + usernames,
    ).fetchall()
    relay_cred_ids = [row["id"] for row in relay_cred_rows]

    relay_keys: list[str] = []
    if relay_cred_ids:
        relay_key_rows = c.execute(
            f"SELECT relay_key FROM relay_tokens WHERE credential_id IN ({placeholders(relay_cred_ids)})",
            relay_cred_ids,
        ).fetchall()
        relay_keys = [row["relay_key"] for row in relay_key_rows]

    counts: dict[str, int] = {}

    if relay_keys:
        cur = c.execute(
            f"DELETE FROM relay_pairings WHERE relay_key IN ({placeholders(relay_keys)})",
            relay_keys,
        )
        counts["relay_pairings"] = cur.rowcount
    else:
        counts["relay_pairings"] = 0

    if session_tokens:
        cur = c.execute(
            f"DELETE FROM relay_pairings WHERE session_token IN ({placeholders(session_tokens)})",
            session_tokens,
        )
        counts["relay_pairings"] += cur.rowcount
        cur = c.execute(
            f"DELETE FROM pairing_codes WHERE session_token IN ({placeholders(session_tokens)})",
            session_tokens,
        )
        counts["pairing_codes"] = cur.rowcount
    else:
        counts["pairing_codes"] = 0

    if relay_cred_ids:
        cur = c.execute(
            f"DELETE FROM relay_tokens WHERE credential_id IN ({placeholders(relay_cred_ids)})",
            relay_cred_ids,
        )
        counts["relay_tokens"] = cur.rowcount
    else:
        counts["relay_tokens"] = 0

    if relay_cred_ids:
        cur = c.execute(
            f"DELETE FROM relay_credentials WHERE id IN ({placeholders(relay_cred_ids)})",
            relay_cred_ids,
        )
        counts["relay_credentials"] = cur.rowcount
    else:
        counts["relay_credentials"] = 0

    if session_tokens:
        cur = c.execute(
            f"DELETE FROM sessions WHERE token IN ({placeholders(session_tokens)})",
            session_tokens,
        )
        counts["sessions"] = cur.rowcount
    else:
        counts["sessions"] = 0

    if fingerprints:
        cur = c.execute(
            f"DELETE FROM request_nonces WHERE fingerprint IN ({placeholders(fingerprints)})",
            fingerprints,
        )
        counts["request_nonces"] = cur.rowcount
    else:
        counts["request_nonces"] = 0

    cur = c.execute(
        f"DELETE FROM device_security WHERE username IN ({placeholders(usernames)})",
        usernames,
    )
    counts["device_security"] = cur.rowcount

    cur = c.execute(
        f"DELETE FROM login_events WHERE username IN ({placeholders(usernames)})",
        usernames,
    )
    counts["login_events"] = cur.rowcount

    cur = c.execute(
        f"DELETE FROM user_limits WHERE username IN ({placeholders(usernames)})",
        usernames,
    )
    counts["user_limits"] = cur.rowcount

    cur = c.execute(
        f"DELETE FROM users WHERE id IN ({placeholders(user_ids)})",
        user_ids,
    )
    counts["users"] = cur.rowcount

    return counts


def format_delete_counts(counts: dict[str, int]) -> str:
    return (
        f"users={counts.get('users', 0)}, "
        f"sessions={counts.get('sessions', 0)}, "
        f"relay_credentials={counts.get('relay_credentials', 0)}, "
        f"relay_tokens={counts.get('relay_tokens', 0)}, "
        f"pairings={counts.get('relay_pairings', 0)}, "
        f"devices={counts.get('device_security', 0)}"
    )


def delete_user(username: str) -> str:
    username = username.strip()
    with db() as c:
        row = c.execute("SELECT id,username FROM users WHERE username=?", (username,)).fetchone()
        if not row:
            return f"Không có user: {username}"
        counts = hard_delete_user_rows(c, [row])
        c.commit()
    return f"🗑 Đã xóa vĩnh viễn user: {username}\n{format_delete_counts(counts)}"


def clear_expired() -> str:
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with db() as c:
        expired_users = c.execute(
            "SELECT id,username FROM users WHERE expires_at IS NOT NULL AND expires_at<?",
            (now_iso,),
        ).fetchall()
        counts = hard_delete_user_rows(c, expired_users)
        cur2 = c.execute("DELETE FROM sessions WHERE expires_at<?", (now_iso,))
        counts["sessions"] = counts.get("sessions", 0) + cur2.rowcount
        c.commit()
    return f"⌛ Đã xóa vĩnh viễn dữ liệu hết hạn\n{format_delete_counts(counts)}"


def help_text() -> str:
    return (
        "❓ Help — VCAM Admin Bot\n\n"
        "Lệnh:\n"
        "/users — danh sách user\n"
        "/status — thống kê\n"
        "/add user pass ngày — thêm/gia hạn (mặc định 1 máy, 300s)\n"
        "/add user pass ngày số_máy timeout — nâng cao\n"
        "/find text — tìm user/thiết bị/IP\n"
        "/clear text — clear fail/lock theo user/device/fingerprint/IP\n"
        "/del username — XÓA VĨNH VIỄN user + relay + session\n"
        "/expired hoặc /purge_expired — xóa vĩnh viễn user/session hết hạn\n\n"
        "Nút bàn phím map đúng các lệnh trên.\n"
        "Lưu ý: backend mặc định KHÔNG tự khóa máy sau N lần sai "
        "(VCAM_BAD_LOGIN_LOCK_ENABLED=0). /del là hard-delete."
    )

def handle_text(chat_id: str, text: str) -> None:
    text = text.strip()
    state = STATE.pop(chat_id, "")
    try:
        if state == "add":
            send(chat_id, add_user(*parse_add_args(text)))
            return
        if state == "find":
            send(chat_id, find_user(text))
            return
        if state == "clear":
            send(chat_id, clear_device(text))
            return
        if state == "delete":
            send(chat_id, delete_user(text))
            return

        normalized = text.lower()
        if text in {"/start", "/help", BTN_HELP} or normalized.endswith("help"):
            send(chat_id, help_text())
        elif text == BTN_USERS or text == "/users" or normalized.endswith("users"):
            send(chat_id, cmd_users())
        elif text == BTN_STATUS or text == "/status" or normalized.endswith("status"):
            send(chat_id, cmd_status())
        elif text == BTN_ADD or "add user" in normalized:
            STATE[chat_id] = "add"
            send(
                chat_id,
                "\u2795 Th\u00eam/gia h\u1ea1n user\n\n"
                "G\u00f5:\n/add loki 1 30\n\n"
                "N\u00e2ng cao:\n/add loki 1 30 1 300\n"
                "(/add user pass ng\u00e0y s\u1ed1_m\u00e1y timeout)\n"
                "M\u1eb7c \u0111\u1ecbnh: 1 thi\u1ebft b\u1ecb, timeout 300s.",
            )
        elif text.startswith("/add "):
            send(chat_id, add_user(*parse_add_args(text.split(maxsplit=1)[1])))
        elif text == BTN_FIND or "t\u00ecm user" in normalized or "tim user" in normalized:
            STATE[chat_id] = "find"
            send(chat_id, "\ud83d\udd0e T\u00ecm user\n\nG\u00f5:\n/find loki")
        elif text.startswith("/find "):
            send(chat_id, find_user(text.split(maxsplit=1)[1]))
        elif text == BTN_CLEAR or "clear" in normalized:
            STATE[chat_id] = "clear"
            send(chat_id, "\ud83e\uddf9 Clear m\u00e1y / reset fail-lock\n\nG\u00f5:\n/clear loki")
        elif text.startswith("/clear "):
            send(chat_id, clear_device(text.split(maxsplit=1)[1]))
        elif text == BTN_DELETE or "x\u00f3a user" in normalized or "xoa user" in normalized:
            STATE[chat_id] = "delete"
            send(chat_id, "\ud83d\uddd1 X\u00f3a v\u0129nh vi\u1ec5n user\n\nG\u00f5:\n/del loki")
        elif text.startswith("/del "):
            send(chat_id, delete_user(text.split(maxsplit=1)[1]))
        elif (
            text == BTN_EXPIRED
            or text in {"/expired", "/delexpired", "/purge_expired"}
            or "h\u1ebft h\u1ea1n" in normalized
            or "het han" in normalized
        ):
            send(chat_id, clear_expired())
        else:
            send(chat_id, "Kh\u00f4ng hi\u1ec3u l\u1ec7nh.\n\n" + help_text())
    except Exception as exc:
        send(chat_id, f"Loi: {exc}")

def main() -> None:
    offset = 0
    send(ADMIN_CHAT_ID, "✅ VCAM admin bot started")
    while True:
        try:
            params = urllib.parse.urlencode({"timeout": 30, "offset": offset}).encode()
            req = urllib.request.Request(f"{API}/getUpdates", data=params, method="POST")
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read())
            for update in data.get("result", []):
                offset = max(offset, int(update["update_id"]) + 1)
                msg = update.get("message") or update.get("edited_message")
                if not msg or "text" not in msg:
                    continue
                chat_id = str(msg["chat"]["id"])
                if not is_admin(msg):
                    send(chat_id, "Unauthorized", keyboard=False)
                    continue
                handle_text(chat_id, msg["text"])
        except Exception:
            time.sleep(5)


if __name__ == "__main__":
    main()
