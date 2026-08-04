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


PATCHES = [
    {
        "arch": "arm64",
        "thin_addr": 0x00A068,
        "file_offset": 0x0000E068,
        "old_bytes": bytes.fromhex("eb2bbb6d"),
        "new_bytes": bytes.fromhex("c0035fd6"),
        "reason": "Return immediately from shifted imageWithActions/drawAtPoint watermark block in VcamLumiereUI 2.2.031 arm64.",
    },
    {
        "arch": "arm64e",
        "thin_addr": 0x00A548,
        "file_offset": 0x00042548,
        "old_bytes": bytes.fromhex("7f2303d5"),
        "new_bytes": bytes.fromhex("c0035fd6"),
        "reason": "Return immediately from shifted imageWithActions/drawAtPoint watermark block in VcamLumiereUI 2.2.031 arm64e.",
    },
]


def extract_ui_daemon_and_sensor(deb: Path) -> tuple[bytes, bytes, bool]:
    members = base.read_ar(deb)
    data_member = next((m for m in members if m[0].startswith("data.tar")), None)
    if data_member is None:
        raise SystemExit("data.tar.* not found")
    raw, _comp = base.decompress_tar(*data_member)
    sensor_present = False
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tf:
        ui_f = tf.extractfile(base.UI_MEMBER)
        daemon_f = tf.extractfile(base.DAEMON_MEMBER)
        if ui_f is None:
            raise SystemExit(f"{base.UI_MEMBER} not found")
        if daemon_f is None:
            raise SystemExit(f"{base.DAEMON_MEMBER} not found")
        for member in tf.getmembers():
            if member.name.endswith("VcamLumiereSensor.plist"):
                sensor_present = True
                break
        return ui_f.read(), daemon_f.read(), sensor_present


def main() -> int:
    ap = argparse.ArgumentParser(description="Patch VcamLumiereUI 2.2.031 red edge watermark draw block.")
    ap.add_argument("--deb", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--allow-unknown", action="store_true")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ui, daemon, sensor_present = extract_ui_daemon_and_sensor(args.deb)
    ui_before = bytearray(ui)
    ui_after = bytearray(ui)

    applied = []
    for patch in PATCHES:
        off = patch["file_offset"]
        old = patch["old_bytes"]
        new = patch["new_bytes"]
        actual = bytes(ui_after[off : off + len(old)])
        if actual != old:
            raise SystemExit(
                f"{patch['arch']} old bytes mismatch at 0x{off:x}: expected {old.hex()}, got {actual.hex()}"
            )
        ui_after[off : off + len(old)] = new
        applied.append({
            "arch": patch["arch"],
            "thin_addr": f"0x{patch['thin_addr']:x}",
            "file_offset": f"0x{off:x}",
            "old_bytes": old.hex(),
            "new_bytes": new.hex(),
            "reason": patch["reason"],
        })

    out_deb = args.out_dir / (
        args.deb.stem.replace(".deb", "") + "_nored_test.deb"
    )
    base.patch_deb(args.deb, out_deb, bytes(ui_after), daemon, allow_unknown=args.allow_unknown)

    manifest = {
        "format": "vcam-kimiki-v22031-nored-test-v1",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_deb": str(args.deb),
        "output_deb": str(out_deb),
        "input_sha256": base.sha256(args.deb.read_bytes()),
        "output_sha256": base.sha256(out_deb.read_bytes()),
        "patched_file": base.UI_MEMBER,
        "ui_sha256_before": base.sha256(ui_before),
        "ui_sha256_after": base.sha256(ui_after),
        "sensor_plist_present": sensor_present,
        "patches": applied,
        "changed_ranges": base.changed_ranges(ui_before, ui_after),
        "notes": [
            "Built on top of Kimiki safe brand123 DEB: metadata + relay contact + UI marker already applied.",
            "Offsets are not copied from 2.1.08 directly; they were remapped on VcamLumiereUI 2.2.031 by matching the shifted imageWithActions/drawAtPoint block.",
            "This is a test artifact until physical iPhone confirms menu/login/stream/no-red behavior.",
            "VcamLumiereSensor.plist is intentionally preserved.",
        ],
    }
    manifest_path = args.out_dir / "nored_watermark_v22031_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "deb": str(out_deb),
        "manifest": str(manifest_path),
        "sha256": manifest["output_sha256"],
        "patches": applied,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
