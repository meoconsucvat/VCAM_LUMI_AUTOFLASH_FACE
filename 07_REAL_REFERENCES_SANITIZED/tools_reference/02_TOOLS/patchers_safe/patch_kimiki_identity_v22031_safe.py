from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import tarfile
import time
from pathlib import Path

import patch_kimiki_identity_v22031 as base
import scan_identity_fields_v22031 as scan


def collect_reserved_indices(full: bytes, path_for_fat: Path) -> dict[tuple[int, int], set[int]]:
    reserved: dict[tuple[int, int], set[int]] = {}
    for sl in scan.parse_fat(path_for_fat):
        thin = full[sl.offset : sl.offset + sl.size]
        for _call, helper, _nonce, indices, length in scan.collect_calls(thin):
            params = scan.helper_params(thin, helper)
            if not params:
                continue
            table, _seed = params
            key = (sl.offset, table)
            # Conservative upper bound for these recovered obfuscated literals.
            # Known identity lengths are 27, 32, and 44; for unknown calls reserve 44.
            literal_len = length if length in (27, 32, 44) else 44
            for i in range(literal_len):
                off = sl.offset + indices + 2 * i
                if off + 2 > len(full):
                    continue
                idx = struct.unpack_from("<H", full, off)[0]
                if idx < 0x1000:
                    reserved.setdefault(key, set()).add(idx)
    return reserved


def patch_fields_safe(
    blob: bytearray,
    fields: dict[str, base.EncodedField],
    targets: dict[str, bytes],
    reserved: dict[tuple[int, int], set[int]],
) -> dict[str, list[dict[str, object]]]:
    grouped: dict[tuple[int, int], list[tuple[str, base.EncodedField]]] = {}
    for name, field in fields.items():
        grouped.setdefault((field.fat_base, field.table), []).append((name, field))

    table_diffs: dict[str, list[dict[str, object]]] = {}
    for key, members in grouped.items():
        fat_base, table_offset = key
        table_start = fat_base + table_offset
        table = bytearray(blob[table_start : table_start + 0x403])
        before_table = bytes(table)

        referenced_by_any_call = set(reserved.get(key, set()))
        referenced_by_identity_old = set()
        for _name, field in members:
            for i in range(field.length):
                referenced_by_identity_old.add(
                    struct.unpack_from("<H", blob, fat_base + field.indices + 2 * i)[0]
                )

        # A slot can only be overwritten if it is not used by non-identity decode calls.
        protected = referenced_by_any_call - referenced_by_identity_old
        free = [
            i
            for i in range(len(table))
            if i not in protected and i not in referenced_by_identity_old
        ]
        assigned: dict[int, int] = {}

        for name, field in members:
            target = targets[name]
            if len(target) != field.length:
                raise ValueError(f"{name}: requires {field.length} bytes, got {len(target)}")
            stream = base.keystream(blob, field)
            for i, (plain, mask) in enumerate(zip(target, stream)):
                wanted = plain ^ mask
                idx = table.find(bytes([wanted]))
                if idx < 0:
                    if wanted in assigned:
                        idx = assigned[wanted]
                    else:
                        if not free:
                            raise RuntimeError(f"{name}: no safe free table slot for 0x{wanted:02x}")
                        idx = free.pop(0)
                        table[idx] = wanted
                        assigned[wanted] = idx
                struct.pack_into("<H", blob, fat_base + field.indices + 2 * i, idx)

        blob[table_start : table_start + len(table)] = table
        diffs = []
        for i, (old, new) in enumerate(zip(before_table, table)):
            if old != new:
                diffs.append(
                    {
                        "table_index": f"0x{i:x}",
                        "old": f"0x{old:02x}",
                        "new": f"0x{new:02x}",
                        "protected": i in protected,
                        "identity_old_index": i in referenced_by_identity_old,
                    }
                )
        table_diffs[f"0x{table_start:x}"] = diffs

    for name, field in fields.items():
        got = base.decode_field(blob, field)
        expected = targets[name]
        if got != expected:
            raise AssertionError(f"{name}: decode verify failed got={got.hex()} expected={expected.hex()}")
    return table_diffs


def extract_dylibs_from_deb(deb_path: Path) -> tuple[bytes, bytes]:
    for name, body in base.read_ar(deb_path):
        if name.startswith("data.tar"):
            raw, _comp = base.decompress_tar(name, body)
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tin:
                found = {}
                for member in tin.getmembers():
                    norm = member.name if member.name.startswith("./") else "./" + member.name
                    if norm in (base.UI_MEMBER, base.DAEMON_MEMBER):
                        f = tin.extractfile(member)
                        found[norm] = f.read() if f else b""
                return found[base.UI_MEMBER], found[base.DAEMON_MEMBER]
    raise SystemExit("DEB has no data.tar member")


def main() -> None:
    ap = argparse.ArgumentParser(description="Safe-table patch VcamLumiere 2.2.031 universal DEB and relay.")
    ap.add_argument("--identity", type=Path, required=True)
    ap.add_argument("--deb", type=Path, required=True)
    ap.add_argument("--relay", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--stub-relay-tls-pin", action="store_true")
    ap.add_argument("--allow-unknown-input", action="store_true")
    args = ap.parse_args()

    url, pub, pin1, pin2 = base.parse_identity(args.identity)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    ui_before, daemon_before = extract_dylibs_from_deb(args.deb)
    base.require_expected("ui", ui_before, base.UI_MEMBER, args.allow_unknown_input)
    base.require_expected("daemon", daemon_before, base.DAEMON_MEMBER, args.allow_unknown_input)

    ui_tmp = args.output_dir / "_source_ui_for_scan.dylib"
    daemon_tmp = args.output_dir / "_source_daemon_for_scan.dylib"
    ui_tmp.write_bytes(ui_before)
    daemon_tmp.write_bytes(daemon_before)

    ui = bytearray(ui_before)
    daemon = bytearray(daemon_before)
    ui_old_decoded = base.decoded_map(ui, base.UI_FIELDS)
    daemon_old_decoded = base.decoded_map(daemon, base.DAEMON_FIELDS)

    ui_table_diffs = patch_fields_safe(
        ui,
        base.UI_FIELDS,
        base.target_map(base.UI_FIELDS, url, pub, pin1, pin2),
        collect_reserved_indices(ui_before, ui_tmp),
    )
    daemon_table_diffs = patch_fields_safe(
        daemon,
        base.DAEMON_FIELDS,
        base.target_map(base.DAEMON_FIELDS, url, pub, pin1, pin2),
        collect_reserved_indices(daemon_before, daemon_tmp),
    )

    deb_out = args.output_dir / "com.lumiere.vcamlumiere_2.2.031_kimiki_universal_safe.deb"
    relay_out = args.output_dir / "relay" / "relay.exe"
    deb_info = base.patch_deb(args.deb, deb_out, bytes(ui), bytes(daemon), args.allow_unknown_input)
    relay_info = base.patch_relay(args.relay, relay_out, url, args.stub_relay_tls_pin, args.allow_unknown_input)

    manifest = {
        "format": "vcam-lumiere-2.2.031-kimiki-safe-table-manifest-v1",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity": {
            "base_url": url.decode("ascii"),
            "ed25519_public_key_hex": pub.hex(),
            "spki_pin": pin1.decode("ascii"),
            "backup_spki_pin": pin2.decode("ascii"),
            "brand_changed": False,
        },
        "ui": {
            "sha256_before": hashlib.sha256(ui_before).hexdigest(),
            "sha256_after": hashlib.sha256(ui).hexdigest(),
            "changed_ranges": base.changed_ranges(ui_before, ui),
            "decoded_before": ui_old_decoded,
            "decoded_after": base.decoded_map(ui, base.UI_FIELDS),
            "table_diffs": ui_table_diffs,
            "fields": {k: vars(v) for k, v in base.UI_FIELDS.items()},
        },
        "daemon": {
            "sha256_before": hashlib.sha256(daemon_before).hexdigest(),
            "sha256_after": hashlib.sha256(daemon).hexdigest(),
            "changed_ranges": base.changed_ranges(daemon_before, daemon),
            "decoded_before": daemon_old_decoded,
            "decoded_after": base.decoded_map(daemon, base.DAEMON_FIELDS),
            "table_diffs": daemon_table_diffs,
            "fields": {k: vars(v) for k, v in base.DAEMON_FIELDS.items()},
        },
        "deb": deb_info,
        "relay": relay_info,
        "runtime_evidence": {
            "stage1_ui_url_only": "opened menu OK",
            "stage2_old_unsafe": "opened menu caused SpringBoard Safe Mode",
            "stage2a_ui_url_pub_safe": "opened menu OK",
            "stage2b_ui_full_safe": "opened menu OK and login succeeded after server code_marker fix",
            "stage3_daemon_full_safe": "OBS publisher and iPhone player both connected; verify_succeeded repeated",
        },
        "notes": [
            "This build uses safe-table reservation. Do not reuse the older non-safe kimiki DEB.",
            "Brand/contact strings are intentionally unchanged.",
            "All three SPKI pin slots found in UI and daemon are patched.",
            "For RootHide devices, convert/rootless-compat exactly like the original working DEB before install.",
        ],
    }
    manifest_path = args.output_dir / "kimiki_safe_patch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    try:
        ui_tmp.unlink()
        daemon_tmp.unlink()
    except OSError:
        pass

    print(
        json.dumps(
            {
                "deb": str(deb_out),
                "relay": str(relay_out),
                "manifest": str(manifest_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
