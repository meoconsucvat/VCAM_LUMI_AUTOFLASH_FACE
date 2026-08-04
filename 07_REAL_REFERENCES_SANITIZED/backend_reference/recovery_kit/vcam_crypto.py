"""Reference implementation recovered from VcamLumiere 2.1.08 binaries."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
from dataclasses import dataclass
from typing import Iterable

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


LEGACY_BOOTSTRAP_SECRET = "01b13940d4d3565e2d0af2a3ad519f5d198494690676e437975a73ad7038afca"
LEGACY_ED25519_PUBLIC_KEY = bytes.fromhex(
    "d15ea3d1a9ac3afb8824951ba233190bf3c2d940bde4619f13341b8b0f44940d"
)
LEGACY_MASTER64 = bytes.fromhex(
    "91a1c0ef1486b3556db2e4206e992cd49df2fb25baf3ee9d63fe2d8d74b306d6"
    "58734ce5eb27b7a967287939b586aaa3cf5851a0af3503f22f3250b88d93a5f1"
)
LEGACY_CODE_MARKER = "tele: @lumierephan"
LEGACY_UI_SPKI_PINS = (
    "YBkV/sM6Xp8FfeYKtMuF31Gw1a7h2kBvAoXpViMAdLM=",
    "5dDQcI9kEmYkQ7O/GAcGqRXHMXs4OiUgK8LqXiTgGrY=",
)
LEGACY_RELAY_SPKI_PIN = "h1:ShrD1U9pZB12TX0cVy0DtePoCH97K8EtX+mg7ZARUtM="


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hmac_hex(secret: str | bytes, payload: str | bytes) -> str:
    key = secret.encode() if isinstance(secret, str) else secret
    msg = payload.encode() if isinstance(payload, str) else payload
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def request_payload(
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    fingerprint: str,
    body: str,
    code_marker: str = LEGACY_CODE_MARKER,
) -> str:
    code_hash = sha256_hex(code_marker.encode())
    return f"v3:{method.upper()}:{path}:{timestamp}:{nonce}:{fingerprint}:{code_hash}:{body}"


def request_signature(
    secret: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    fingerprint: str,
    body: str,
    code_marker: str = LEGACY_CODE_MARKER,
) -> str:
    return hmac_hex(secret, request_payload(method, path, timestamp, nonce, fingerprint, body, code_marker))


def response_message(fields: Iterable[object]) -> str:
    return "|".join(str(x) for x in fields)


def sign_response_hmac(secret: str, fields: Iterable[object]) -> str:
    return hmac_hex(secret, response_message(fields))


def sign_response_ed25519(private_key: Ed25519PrivateKey, fields: Iterable[object]) -> str:
    msg = response_message(fields).encode()
    return base64.b64encode(private_key.sign(msg)).decode()


def verify_response_ed25519(public_key: bytes, signature_b64: str, fields: Iterable[object]) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            base64.b64decode(signature_b64, validate=True), response_message(fields).encode()
        )
        return True
    except Exception:
        return False


def derive_stream_key(key_seed_b64: str, epoch_hour: int) -> bytes:
    seed = base64.b64decode(key_seed_b64, validate=True)
    if len(seed) != 64:
        raise ValueError("key_seed must decode to exactly 64 bytes")
    return hashlib.sha256(seed + b"vcam-stream-v1" + struct.pack("<q", epoch_hour)).digest()


def frame_code_binding(base_url: str, ed25519_public_key: bytes) -> str:
    if len(ed25519_public_key) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    return sha256_hex(base_url.encode() + b"|" + ed25519_public_key)


def frame_key_message(
    device_id: str,
    fingerprint: str,
    epoch_hour: int,
    base_url: str,
    ed25519_public_key: bytes,
    code_checksum: str | None = None,
) -> str:
    core = (
        f"framekey:{device_id}:{fingerprint}:{epoch_hour}:"
        f"{frame_code_binding(base_url, ed25519_public_key)}"
    )
    return core if code_checksum is None else f"{core}:{code_checksum}"


def make_key_seed(
    private_key: Ed25519PrivateKey,
    device_id: str,
    fingerprint: str,
    epoch_hour: int,
    base_url: str,
    code_checksum: str | None = None,
) -> str:
    public = private_key.public_key().public_bytes_raw()
    message = frame_key_message(
        device_id, fingerprint, epoch_hour, base_url, public, code_checksum
    )
    return base64.b64encode(private_key.sign(message.encode())).decode()


def aes_ctr(data: bytes, key: bytes, iv: bytes) -> bytes:
    if len(key) != 32 or len(iv) != 16:
        raise ValueError("AES-256-CTR requires a 32-byte key and 16-byte IV")
    c = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
    return c.update(data) + c.finalize()


def encrypt_avc_nalu_packet(packet: bytes, key: bytes, iv: bytes | None = None) -> bytes:
    if len(packet) < 6:
        raise ValueError("FLV AVC packet is too short")
    if (packet[0] & 0x0F) != 7 or packet[1] != 1:
        return packet
    iv = os.urandom(16) if iv is None else iv
    return packet[:5] + iv + aes_ctr(packet[5:], key, iv)


def decrypt_avc_nalu_packet(packet: bytes, key: bytes) -> bytes:
    if len(packet) < 22 or (packet[0] & 0x0F) != 7 or packet[1] != 1:
        raise ValueError("not an encrypted AVC NALU packet")
    iv = packet[5:21]
    return packet[:5] + aes_ctr(packet[21:], key, iv)


def derive_plist_key(purpose: str, fingerprint: str, master64: bytes = LEGACY_MASTER64) -> bytes:
    if len(master64) != 64:
        raise ValueError("master key must be 64 bytes")
    return hashlib.sha256(master64 + b":" + purpose.encode() + b":" + fingerprint.encode()).digest()


def plist_integrity_key(fingerprint: str, master64: bytes = LEGACY_MASTER64) -> str:
    return hmac.new(master64, f"plist-integrity:{fingerprint}".encode(), hashlib.sha256).hexdigest()


def plist_integrity(token: str, signing_key: str, device_id: str, fingerprint: str) -> str:
    return hmac_hex(plist_integrity_key(fingerprint), f"{token}|{signing_key}|{device_id}")


def encrypt_plist_string(value: str, fingerprint: str, iv: bytes | None = None) -> str:
    iv = os.urandom(16) if iv is None else iv
    enc_key = derive_plist_key("enc", fingerprint)
    mac_key = derive_plist_key("mac", fingerprint)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(value.encode()) + padder.finalize()
    enc = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).encryptor()
    ciphertext = enc.update(padded) + enc.finalize()
    tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
    return base64.b64encode(iv + ciphertext + tag).decode()


def decrypt_plist_string(blob_b64: str, fingerprint: str) -> str:
    blob = base64.b64decode(blob_b64, validate=True)
    if len(blob) < 49:
        raise ValueError("encrypted plist string is too short")
    iv, ciphertext, tag = blob[:16], blob[16:-32], blob[-32:]
    mac_key = derive_plist_key("mac", fingerprint)
    expected = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("plist string MAC mismatch")
    dec_key = derive_plist_key("enc", fingerprint)
    dec = Cipher(algorithms.AES(dec_key), modes.CBC(iv)).decryptor()
    padded = dec.update(ciphertext) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode()


@dataclass(frozen=True)
class RequestHeaders:
    timestamp: str
    nonce: str
    signature: str

    def as_http(self) -> dict[str, str]:
        return {
            "X-Timestamp": self.timestamp,
            "X-Nonce": self.nonce,
            "X-Signature": self.signature,
        }
