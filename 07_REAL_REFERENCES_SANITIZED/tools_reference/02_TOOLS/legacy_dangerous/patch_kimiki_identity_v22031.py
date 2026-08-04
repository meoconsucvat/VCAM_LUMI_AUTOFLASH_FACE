from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
import lzma
import shutil
import struct
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path


OLD_URL = b"https://lumierevip.net/vcam"
OLD_PUB_HEX = "d15ea3d1a9ac3afb8824951ba233190bf3c2d940bde4619f13341b8b0f44940d"
OLD_PINS = {
    b"YBkV/sM6Xp8FfeYKtMuF31Gw1a7h2kBvAoXpViMAdLM=",
    b"5dDQcI9kEmYkQ7O/GAcGqRXHMXs4OiUgK8LqXiTgGrY=",
    b"C5+lpZ7tcVwmwQIMcRtPbsQtWLABXhQzejna0wHFr8M=",
}

EXPECTED = {
    "deb": {
        "sha256": "5a641447cdb2b3030f8e531695e647d53e9beeef5e592dbe7f5c84929b0a9efb",
        "size": 361048,
    },
    "daemon": {
        "sha256": "f2563217ffdae1fdeff2c284126215d7fcbcc3c78638c03aada61c5d803126a3",
        "size": 1691776,
    },
    "ui": {
        "sha256": "460e7bace6354586fac2bcf6ee19c6a8dc670974193f824e54260fd43f59ca43",
        "size": 395184,
    },
    "relay": {
        "sha256": "83230cc05a0544faedbae33ab72abda0c0bafd0d52668e803e5212d5d762384b",
        "size": 6962176,
    },
}

DAEMON_MEMBER = "./var/jb/Library/MobileSubstrate/DynamicLibraries/VcamLumiereDaemon.dylib"
UI_MEMBER = "./var/jb/Library/MobileSubstrate/DynamicLibraries/VcamLumiereUI.dylib"

RELAY_URL_OFFSET = 0x3A5808
RELAY_URL_LENGTH = 27
RELAY_VERIFY_PINNED_OFFSET = 0x296D60
RELAY_VERIFY_PINNED_FIRST16 = bytes.fromhex("493b66100f86bd000000554889e54883")
RELAY_VERIFY_PINNED_STUB = bytes.fromhex("31c031dbc3")


@dataclass(frozen=True)
class EncodedField:
    fat_base: int
    table: int
    seed: int
    nonce: int
    indices: int
    length: int


UI_FIELDS = {
    "arm64_url": EncodedField(0x4000, 0x181E8, 0x185EB, 0x1865C, 0x18664, 27),
    "arm64_pub": EncodedField(0x4000, 0x181E8, 0x185EB, 0x18AB0, 0x18AB8, 32),
    "arm64_pin1": EncodedField(0x4000, 0x18DF6, 0x191F9, 0x18D96, 0x18D9E, 44),
    "arm64_pin2": EncodedField(0x4000, 0x18DF6, 0x191F9, 0x19229, 0x19232, 44),
    "arm64_pin3": EncodedField(0x4000, 0x18DF6, 0x191F9, 0x1928A, 0x19292, 44),
    "arm64e_url": EncodedField(0x34000, 0x19728, 0x19B2B, 0x19B9C, 0x19BA4, 27),
    "arm64e_pub": EncodedField(0x34000, 0x19728, 0x19B2B, 0x19FF0, 0x19FF8, 32),
    "arm64e_pin1": EncodedField(0x34000, 0x1A336, 0x1A739, 0x1A2D6, 0x1A2DE, 44),
    "arm64e_pin2": EncodedField(0x34000, 0x1A336, 0x1A739, 0x1A769, 0x1A772, 44),
    "arm64e_pin3": EncodedField(0x34000, 0x1A336, 0x1A739, 0x1A7CA, 0x1A7D2, 44),
}

DAEMON_FIELDS = {
    "arm64_url_a": EncodedField(0x8000, 0x55BDE, 0x55FE1, 0x55BA0, 0x55BA8, 27),
    "arm64_pub_a": EncodedField(0x8000, 0x55BDE, 0x55FE1, 0x56011, 0x5601A, 32),
    "arm64_url_extra": EncodedField(0x8000, 0x56E1E, 0x57221, 0x56DE0, 0x56DE8, 27),
    "arm64_pub_extra": EncodedField(0x8000, 0x56E1E, 0x57221, 0x57251, 0x5725A, 32),
    "arm64_url_b": EncodedField(0x8000, 0x572D8, 0x576DB, 0x5729A, 0x572A2, 27),
    "arm64_pub_b": EncodedField(0x8000, 0x572D8, 0x576DB, 0x5770B, 0x57714, 32),
    "arm64_pin1": EncodedField(0x8000, 0x577FE, 0x57C01, 0x5779E, 0x577A6, 44),
    "arm64_pin2": EncodedField(0x8000, 0x577FE, 0x57C01, 0x57C31, 0x57C3A, 44),
    "arm64_pin3": EncodedField(0x8000, 0x577FE, 0x57C01, 0x57C92, 0x57C9A, 44),
    "arm64e_url_a": EncodedField(0xD0000, 0x87B8E, 0x87F91, 0x87B50, 0x87B58, 27),
    "arm64e_pub_a": EncodedField(0xD0000, 0x87B8E, 0x87F91, 0x87FC1, 0x87FCA, 32),
    "arm64e_url_extra": EncodedField(0xD0000, 0x88DCE, 0x891D1, 0x88D90, 0x88D98, 27),
    "arm64e_pub_extra": EncodedField(0xD0000, 0x88DCE, 0x891D1, 0x89201, 0x8920A, 32),
    "arm64e_url_b": EncodedField(0xD0000, 0x89288, 0x8968B, 0x8924A, 0x89252, 27),
    "arm64e_pub_b": EncodedField(0xD0000, 0x89288, 0x8968B, 0x896BB, 0x896C4, 32),
    "arm64e_pin1": EncodedField(0xD0000, 0x897AE, 0x89BB1, 0x8974E, 0x89756, 44),
    "arm64e_pin2": EncodedField(0xD0000, 0x897AE, 0x89BB1, 0x89BE1, 0x89BEA, 44),
    "arm64e_pin3": EncodedField(0xD0000, 0x897AE, 0x89BB1, 0x89C42, 0x89C4A, 44),
}


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def require_expected(kind: str, data: bytes | bytearray, source: str, allow_unknown: bool) -> None:
    expected = EXPECTED[kind]
    actual = {"size": len(data), "sha256": sha256(data)}
    if actual == expected:
        return
    msg = f"unsupported {kind} {source}: actual={actual}; expected={expected}"
    if allow_unknown:
        print("WARNING:", msg)
        return
    raise SystemExit(msg)


def keystream(blob: bytearray, field: EncodedField) -> bytes:
    base = field.fat_base
    seed = hashlib.sha256(
        blob[base + field.seed : base + field.seed + 16]
        + blob[base + field.seed + 16 : base + field.seed + 32]
        + blob[base + field.seed + 32 : base + field.seed + 48]
    ).digest()
    out = bytearray()
    for block in range((field.length + 31) // 32):
        out.extend(hashlib.sha256(seed + blob[base + field.nonce : base + field.nonce + 8] + bytes([block])).digest())
    return bytes(out[: field.length])


def decode_field(blob: bytearray, field: EncodedField) -> bytes:
    base = field.fat_base
    stream = keystream(blob, field)
    enc = bytearray()
    for i in range(field.length):
        idx = struct.unpack_from("<H", blob, base + field.indices + 2 * i)[0]
        enc.append(blob[base + field.table + idx])
    return bytes(a ^ b for a, b in zip(enc, stream))


def changed_ranges(before: bytes | bytearray, after: bytes | bytearray) -> list[dict[str, object]]:
    if len(before) != len(after):
        raise ValueError("patch changed file size")
    ranges: list[dict[str, object]] = []
    start = None
    for i, (a, b) in enumerate(zip(before, after)):
        if a != b and start is None:
            start = i
        elif a == b and start is not None:
            ranges.append({"offset_start": f"0x{start:x}", "offset_end_exclusive": f"0x{i:x}", "length": i - start})
            start = None
    if start is not None:
        ranges.append({"offset_start": f"0x{start:x}", "offset_end_exclusive": f"0x{len(before):x}", "length": len(before) - start})
    return ranges


def patch_fields(blob: bytearray, fields: dict[str, EncodedField], targets: dict[str, bytes]) -> None:
    grouped: dict[tuple[int, int], list[tuple[str, EncodedField]]] = {}
    for name, field in fields.items():
        grouped.setdefault((field.fat_base, field.table), []).append((name, field))

    for (base, table_offset), members in grouped.items():
        table_start = base + table_offset
        table = bytearray(blob[table_start : table_start + 0x403])
        reserved: set[int] = set()
        for _, field in members:
            for i in range(field.length):
                reserved.add(struct.unpack_from("<H", blob, base + field.indices + 2 * i)[0])
        free = [i for i in range(len(table)) if i not in reserved]
        assigned: dict[int, int] = {}

        for name, field in members:
            target = targets[name]
            if len(target) != field.length:
                raise ValueError(f"{name}: requires {field.length} bytes, got {len(target)}")
            stream = keystream(blob, field)
            for i, (plain, mask) in enumerate(zip(target, stream)):
                wanted = plain ^ mask
                idx = table.find(bytes([wanted]))
                if idx < 0:
                    if wanted in assigned:
                        idx = assigned[wanted]
                    elif free:
                        idx = free.pop(0)
                        table[idx] = wanted
                        assigned[wanted] = idx
                    else:
                        raise ValueError(f"{name}: no table byte/free slot for 0x{wanted:02x}")
                struct.pack_into("<H", blob, base + field.indices + 2 * i, idx)
        blob[table_start : table_start + len(table)] = table

    for name, field in fields.items():
        got = decode_field(blob, field)
        if got != targets[name]:
            raise AssertionError(f"{name}: verify failed; got={got.hex()} expected={targets[name].hex()}")


def parse_pin(value: str, field_name: str) -> bytes:
    val = value.removeprefix("h1:")
    raw = base64.b64decode(val, validate=True)
    if len(raw) != 32:
        raise SystemExit(f"{field_name} must decode to 32 bytes")
    return base64.b64encode(raw)


def parse_identity(path: Path) -> tuple[bytes, bytes, bytes, bytes]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    url = obj["base_url"].encode("utf-8")
    if len(url) != 27:
        raise SystemExit(f"base_url must be exactly 27 UTF-8 bytes, got {len(url)}: {obj['base_url']!r}")
    pub_hex = obj.get("ed25519_public_key_hex")
    pub_b64 = obj.get("ed25519_public_key_b64")
    pub = bytes.fromhex(pub_hex) if pub_hex else base64.b64decode(pub_b64, validate=True)
    if len(pub) != 32:
        raise SystemExit("Ed25519 public key must be 32 bytes")
    pin1 = parse_pin(obj["spki_pin"], "spki_pin")
    pin2 = parse_pin(obj.get("backup_spki_pin") or obj["spki_pin"], "backup_spki_pin")
    return url, pub, pin1, pin2


def target_map(fields: dict[str, EncodedField], url: bytes, pub: bytes, pin1: bytes, pin2: bytes) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for name in fields:
        if "url" in name:
            out[name] = url
        elif "pub" in name:
            out[name] = pub
        elif "pin1" in name:
            out[name] = pin1
        elif "pin2" in name or "pin3" in name:
            out[name] = pin2
        else:
            raise AssertionError(name)
    return out


def decoded_map(blob: bytearray, fields: dict[str, EncodedField]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, field in fields.items():
        raw = decode_field(blob, field)
        out[name] = raw.hex() if "pub" in name else raw.decode("ascii")
    return out


def read_ar(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if not data.startswith(b"!<arch>\n"):
        raise SystemExit(f"{path} is not an ar/deb archive")
    members: list[tuple[str, bytes]] = []
    pos = 8
    while pos + 60 <= len(data):
        header = data[pos : pos + 60]
        pos += 60
        name = header[:16].decode("ascii").strip()
        size = int(header[48:58].decode("ascii").strip())
        body = data[pos : pos + size]
        pos += size
        if pos % 2:
            pos += 1
        members.append((name.rstrip("/"), body))
    return members


def write_ar(path: Path, members: list[tuple[str, bytes]]) -> None:
    out = bytearray(b"!<arch>\n")
    now = int(time.time())
    for name, body in members:
        ar_name = (name + "/").encode("ascii")
        if len(ar_name) > 16:
            raise ValueError(f"ar member name too long: {name}")
        header = (
            ar_name.ljust(16, b" ")
            + str(now).encode("ascii").ljust(12, b" ")
            + b"0     "
            + b"0     "
            + b"100644  "
            + str(len(body)).encode("ascii").ljust(10, b" ")
            + b"`\n"
        )
        out.extend(header)
        out.extend(body)
        if len(out) % 2:
            out.extend(b"\n")
    path.write_bytes(out)


def decompress_tar(name: str, data: bytes) -> tuple[bytes, str]:
    if name.endswith(".xz"):
        return lzma.decompress(data), "xz"
    if name.endswith(".gz"):
        return gzip.decompress(data), "gz"
    return data, "plain"


def compress_tar(data: bytes, kind: str) -> bytes:
    if kind == "xz":
        return lzma.compress(data, preset=6)
    if kind == "gz":
        return gzip.compress(data, compresslevel=9)
    return data


def patch_data_tar(data_tar: bytes, compression: str, replacements: dict[str, bytes]) -> bytes:
    raw_tar, _ = decompress_tar("data.tar." + compression, data_tar)
    inp = io.BytesIO(raw_tar)
    outp = io.BytesIO()
    found: set[str] = set()
    with tarfile.open(fileobj=inp, mode="r:") as tin, tarfile.open(fileobj=outp, mode="w:") as tout:
        for member in tin.getmembers():
            norm = member.name if member.name.startswith("./") else "./" + member.name
            src = tin.extractfile(member) if member.isfile() else None
            payload = src.read() if src is not None else None
            if norm in replacements:
                payload = replacements[norm]
                member.size = len(payload)
                found.add(norm)
            tout.addfile(member, io.BytesIO(payload) if payload is not None else None)
    missing = set(replacements) - found
    if missing:
        raise SystemExit(f"missing tar members: {sorted(missing)}")
    return compress_tar(outp.getvalue(), compression)


def patch_deb(deb_path: Path, output_deb: Path, patched_ui: bytes, patched_daemon: bytes, allow_unknown: bool) -> dict[str, object]:
    before = deb_path.read_bytes()
    require_expected("deb", before, str(deb_path), allow_unknown)
    members = read_ar(deb_path)
    new_members: list[tuple[str, bytes]] = []
    data_member_name = None
    for name, body in members:
        if name.startswith("data.tar"):
            data_member_name = name
            raw_tar, comp = decompress_tar(name, body)
            # Validate original members before replacement.
            with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:") as t:
                bodies = {}
                for m in t.getmembers():
                    norm = m.name if m.name.startswith("./") else "./" + m.name
                    if norm in (UI_MEMBER, DAEMON_MEMBER):
                        f = t.extractfile(m)
                        bodies[norm] = f.read() if f else b""
                require_expected("ui", bodies.get(UI_MEMBER, b""), UI_MEMBER, allow_unknown)
                require_expected("daemon", bodies.get(DAEMON_MEMBER, b""), DAEMON_MEMBER, allow_unknown)
            body = patch_data_tar(body, comp, {UI_MEMBER: patched_ui, DAEMON_MEMBER: patched_daemon})
        new_members.append((name, body))
    if data_member_name is None:
        raise SystemExit("DEB has no data.tar member")
    output_deb.parent.mkdir(parents=True, exist_ok=True)
    write_ar(output_deb, new_members)
    after = output_deb.read_bytes()
    return {
        "source": str(deb_path.resolve()),
        "output": str(output_deb.resolve()),
        "sha256_before": sha256(before),
        "sha256_after": sha256(after),
        "size_before": len(before),
        "size_after": len(after),
        "data_member": data_member_name,
    }


def patch_relay(relay_path: Path, output_path: Path, url: bytes, stub_tls_pin: bool, allow_unknown: bool) -> dict[str, object]:
    before = relay_path.read_bytes()
    require_expected("relay", before, str(relay_path), allow_unknown)
    relay = bytearray(before)
    old_url = bytes(relay[RELAY_URL_OFFSET : RELAY_URL_OFFSET + RELAY_URL_LENGTH])
    if old_url != OLD_URL:
        raise SystemExit(f"unexpected relay URL bytes at 0x{RELAY_URL_OFFSET:x}: {old_url!r}")
    relay[RELAY_URL_OFFSET : RELAY_URL_OFFSET + RELAY_URL_LENGTH] = url
    patches: dict[str, object] = {
        "url": {"offset": f"0x{RELAY_URL_OFFSET:x}", "old": old_url.decode("ascii"), "new": url.decode("ascii")},
    }
    if stub_tls_pin:
        first16 = bytes(relay[RELAY_VERIFY_PINNED_OFFSET : RELAY_VERIFY_PINNED_OFFSET + 16])
        if first16 != RELAY_VERIFY_PINNED_FIRST16:
            raise SystemExit(f"unexpected relay TLS pin callback bytes at 0x{RELAY_VERIFY_PINNED_OFFSET:x}: {first16.hex()}")
        relay[RELAY_VERIFY_PINNED_OFFSET : RELAY_VERIFY_PINNED_OFFSET + len(RELAY_VERIFY_PINNED_STUB)] = RELAY_VERIFY_PINNED_STUB
        patches["tls_pin_callback_stub"] = {
            "offset": f"0x{RELAY_VERIFY_PINNED_OFFSET:x}",
            "old_first16": first16.hex(),
            "new_bytes": RELAY_VERIFY_PINNED_STUB.hex(),
        }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(relay)
    return {
        "source": str(relay_path.resolve()),
        "output": str(output_path.resolve()),
        "sha256_before": sha256(before),
        "sha256_after": sha256(relay),
        "size": len(relay),
        "changed_ranges": changed_ranges(before, relay),
        "patches": patches,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Patch VcamLumiere 2.2.031 universal DEB + original relay to a new backend identity.")
    ap.add_argument("--identity", type=Path, required=True)
    ap.add_argument("--deb", type=Path, required=True)
    ap.add_argument("--relay", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--stub-relay-tls-pin", action="store_true", help="Patch Go relay main.verifyPinned to accept the new TLS cert.")
    ap.add_argument("--allow-unknown-input", action="store_true")
    args = ap.parse_args()

    url, pub, pin1, pin2 = parse_identity(args.identity)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    members = read_ar(args.deb)
    data_member = next((body for name, body in members if name.startswith("data.tar")), None)
    data_name = next((name for name, _ in members if name.startswith("data.tar")), None)
    if data_member is None or data_name is None:
        raise SystemExit("DEB has no data.tar member")
    raw_tar, _ = decompress_tar(data_name, data_member)
    with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:") as t:
        blobs = {}
        for m in t.getmembers():
            norm = m.name if m.name.startswith("./") else "./" + m.name
            if norm in (UI_MEMBER, DAEMON_MEMBER):
                f = t.extractfile(m)
                blobs[norm] = f.read() if f else b""
    ui_before = blobs[UI_MEMBER]
    daemon_before = blobs[DAEMON_MEMBER]
    require_expected("ui", ui_before, UI_MEMBER, args.allow_unknown_input)
    require_expected("daemon", daemon_before, DAEMON_MEMBER, args.allow_unknown_input)

    ui = bytearray(ui_before)
    daemon = bytearray(daemon_before)
    old_ui_decoded = decoded_map(ui, UI_FIELDS)
    old_daemon_decoded = decoded_map(daemon, DAEMON_FIELDS)
    patch_fields(ui, UI_FIELDS, target_map(UI_FIELDS, url, pub, pin1, pin2))
    patch_fields(daemon, DAEMON_FIELDS, target_map(DAEMON_FIELDS, url, pub, pin1, pin2))

    deb_out = args.output_dir / "com.lumiere.vcamlumiere_2.2.031_kimiki_universal.deb"
    relay_out = args.output_dir / "relay" / "relay.exe"
    deb_info = patch_deb(args.deb, deb_out, bytes(ui), bytes(daemon), args.allow_unknown_input)
    relay_info = patch_relay(args.relay, relay_out, url, args.stub_relay_tls_pin, args.allow_unknown_input)

    manifest = {
        "format": "vcam-lumiere-2.2.031-kimiki-patch-manifest-v1",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity": {
            "base_url": url.decode("ascii"),
            "ed25519_public_key_hex": pub.hex(),
            "spki_pin": pin1.decode("ascii"),
            "backup_spki_pin": pin2.decode("ascii"),
            "brand_changed": False,
        },
        "ui": {
            "sha256_before": sha256(ui_before),
            "sha256_after": sha256(ui),
            "changed_ranges": changed_ranges(ui_before, ui),
            "decoded_before": old_ui_decoded,
            "decoded_after": decoded_map(ui, UI_FIELDS),
            "fields": {k: vars(v) for k, v in UI_FIELDS.items()},
        },
        "daemon": {
            "sha256_before": sha256(daemon_before),
            "sha256_after": sha256(daemon),
            "changed_ranges": changed_ranges(daemon_before, daemon),
            "decoded_before": old_daemon_decoded,
            "decoded_after": decoded_map(daemon, DAEMON_FIELDS),
            "fields": {k: vars(v) for k, v in DAEMON_FIELDS.items()},
        },
        "deb": deb_info,
        "relay": relay_info,
        "notes": [
            "Patch source is VcamLumiere 2.2.031 universal lineage.",
            "Brand/contact strings are intentionally unchanged in this build.",
            "All three SPKI pin slots found in UI and daemon were patched to the new identity pins.",
            "If the package fails to inject after RootHide conversion, re-sign patched Mach-O files with ldid in the target jailbreak environment.",
        ],
    }
    manifest_path = args.output_dir / "kimiki_patch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"deb": str(deb_out), "relay": str(relay_out), "manifest": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
