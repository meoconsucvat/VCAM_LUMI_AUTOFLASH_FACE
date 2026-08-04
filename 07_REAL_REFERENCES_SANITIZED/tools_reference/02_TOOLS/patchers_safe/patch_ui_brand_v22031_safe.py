from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import patch_kimiki_identity_v22031 as base
import patch_kimiki_identity_v22031_safe as safe


OLD_UI_MARKER = b"tele: @lumierephan"


UI_BRAND_FIELDS = {
    # Decoded from VcamLumiereUI.dylib, helper-based obfuscated string builder.
    # These are the visible menu/contact marker fields, and the same marker is
    # used by the login request signature code marker.
    "arm64_ui_marker": base.EncodedField(
        fat_base=0x4000,
        table=0x181E8,
        seed=0x185EB,
        nonce=0x18B6E,
        indices=0x18B76,
        length=18,
    ),
    "arm64e_ui_marker": base.EncodedField(
        fat_base=0x34000,
        table=0x19728,
        seed=0x19B2B,
        nonce=0x1A0AE,
        indices=0x1A0B6,
        length=18,
    ),
}


def read_data_members(deb_path: Path) -> tuple[bytes, bytes]:
    data_member = None
    for name, data in base.read_ar(deb_path):
        if name.startswith("data.tar"):
            data_member = (name, data)
            break
    if data_member is None:
        raise SystemExit(f"data.tar.* not found in {deb_path}")

    data_tar, _compression = base.decompress_tar(*data_member)
    with tarfile.open(fileobj=io.BytesIO(data_tar), mode="r:") as tf:
        ui_f = tf.extractfile(base.UI_MEMBER)
        daemon_f = tf.extractfile(base.DAEMON_MEMBER)
        if ui_f is None:
            raise SystemExit(f"{base.UI_MEMBER} not found")
        if daemon_f is None:
            raise SystemExit(f"{base.DAEMON_MEMBER} not found")
        return ui_f.read(), daemon_f.read()


def marker_targets(new_marker: bytes) -> dict[str, bytes]:
    return {name: new_marker for name in UI_BRAND_FIELDS}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Safely patch VcamLumiereUI visible contact marker only."
    )
    ap.add_argument("--deb", required=True, type=Path, help="Input DEB")
    ap.add_argument("--out-dir", required=True, type=Path, help="Output folder")
    ap.add_argument(
        "--marker",
        default="tele: @vcamplus",
        help="New marker. It will be space-padded to 18 bytes.",
    )
    ap.add_argument("--allow-unknown", action="store_true")
    args = ap.parse_args()

    marker_raw = args.marker.encode("utf-8")
    if len(marker_raw) > len(OLD_UI_MARKER):
        raise SystemExit(
            f"marker too long: {len(marker_raw)} bytes; max={len(OLD_UI_MARKER)}"
        )
    new_marker = marker_raw.ljust(len(OLD_UI_MARKER), b" ")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ui, daemon = read_data_members(args.deb)
    ui_before = bytearray(ui)
    ui_after = bytearray(ui)

    decoded_before = {
        name: base.decode_field(ui_after, field).decode("utf-8", "replace")
        for name, field in UI_BRAND_FIELDS.items()
    }
    for name, decoded in decoded_before.items():
        if decoded.encode("utf-8") != OLD_UI_MARKER:
            raise SystemExit(f"unexpected decoded marker for {name}: {decoded!r}")

    tmp_ui_for_scan = args.out_dir / "_tmp_ui_for_reserved_scan.dylib"
    tmp_ui_for_scan.write_bytes(bytes(ui_after))
    reserved = safe.collect_reserved_indices(ui_after, tmp_ui_for_scan)
    table_diffs = safe.patch_fields_safe(
        ui_after,
        UI_BRAND_FIELDS,
        marker_targets(new_marker),
        reserved,
    )
    decoded_after = {
        name: base.decode_field(ui_after, field).decode("utf-8", "replace")
        for name, field in UI_BRAND_FIELDS.items()
    }

    deb_out = args.out_dir / (
        args.deb.stem.replace(".deb", "")
        + "_ui_marker_vcamplus.deb"
    )
    base.patch_deb(
        args.deb,
        deb_out,
        bytes(ui_after),
        daemon,
        allow_unknown=args.allow_unknown,
    )

    manifest = {
        "format": "vcam-ui-marker-safe-v1",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": {
            "ui_dylib_marker_only": True,
            "daemon_unchanged": True,
            "control_metadata_unchanged_from_input": True,
            "relay_unchanged": True,
            "watermark_unchanged": True,
        },
        "input_deb": str(args.deb),
        "output_deb": str(deb_out),
        "sha256_before_deb": base.sha256(args.deb.read_bytes()),
        "sha256_after_deb": base.sha256(deb_out.read_bytes()),
        "ui": {
            "sha256_before": base.sha256(ui_before),
            "sha256_after": base.sha256(ui_after),
            "decoded_before": decoded_before,
            "decoded_after": decoded_after,
            "changed_ranges": base.changed_ranges(ui_before, ui_after),
            "table_diffs": table_diffs,
            "fields": {
                name: field.__dict__
                for name, field in UI_BRAND_FIELDS.items()
            },
        },
        "backend": {
            "old_marker": OLD_UI_MARKER.decode("ascii"),
            "new_marker_exact": new_marker.decode("ascii"),
            "required_policy": "Backend must accept the new marker for login signatures. Prefer accepting both old and new markers during migration.",
        },
        "notes": [
            "New marker is padded to 18 bytes to preserve UI binary layout.",
            "Do not change com.lumiere.* notification/channel strings in this stage.",
            "If backend accepts only the old marker, this DEB will login with bad_signature.",
        ],
    }
    manifest_path = args.out_dir / "ui_marker_vcamplus_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "deb": str(deb_out),
        "manifest": str(manifest_path),
        "sha256": manifest["sha256_after_deb"],
        "new_marker_exact": manifest["backend"]["new_marker_exact"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
