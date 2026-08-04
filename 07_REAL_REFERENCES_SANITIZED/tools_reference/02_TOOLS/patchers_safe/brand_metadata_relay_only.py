from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
import time
from pathlib import Path

import patch_kimiki_identity_v22031 as debutil


OLD_CONTACT = b"@lumierephan"
NEW_CONTACT = b"@vcamplus"
NEW_CONTACT_PADDED = NEW_CONTACT.ljust(len(OLD_CONTACT), b" ")


CONTROL_REPLACEMENTS = {
    "Name": "VcamPlus",
    "Description": "Professional Virtual Camera & RTMP Streaming Engine for iOS By VcamPlus",
    "Maintainer": "VcamPlus",
    "Author": "VcamPlus",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite_control_text(text: str) -> tuple[str, dict[str, dict[str, str]]]:
    changes: dict[str, dict[str, str]] = {}
    lines = []
    for line in text.splitlines():
        if ":" not in line:
            lines.append(line)
            continue
        key, value = line.split(":", 1)
        if key in CONTROL_REPLACEMENTS:
            old = value.strip()
            new = CONTROL_REPLACEMENTS[key]
            lines.append(f"{key}: {new}")
            changes[key] = {"old": old, "new": new}
        else:
            lines.append(line)
    return "\n".join(lines) + "\n", changes


def patch_control_in_deb(source_deb: Path, output_deb: Path) -> dict[str, object]:
    members = debutil.read_ar(source_deb)
    new_members: list[tuple[str, bytes]] = []
    control_changes = None
    control_member_name = None

    for name, body in members:
        if name.startswith("control.tar"):
            control_member_name = name
            raw, comp = debutil.decompress_tar(name, body)
            inp = io.BytesIO(raw)
            outp = io.BytesIO()
            with tarfile.open(fileobj=inp, mode="r:") as tin, tarfile.open(fileobj=outp, mode="w:") as tout:
                for member in tin.getmembers():
                    payload = None
                    if member.isfile():
                        f = tin.extractfile(member)
                        payload = f.read() if f else b""
                    norm = member.name if member.name.startswith("./") else "./" + member.name
                    if norm == "./control":
                        old_text = payload.decode("utf-8")
                        new_text, control_changes = rewrite_control_text(old_text)
                        payload = new_text.encode("utf-8")
                        member.size = len(payload)
                    tout.addfile(member, io.BytesIO(payload) if payload is not None else None)
            body = debutil.compress_tar(outp.getvalue(), comp)
        new_members.append((name, body))

    if control_member_name is None:
        raise SystemExit("DEB has no control.tar member")
    if control_changes is None:
        raise SystemExit("control file was not found in DEB")

    output_deb.parent.mkdir(parents=True, exist_ok=True)
    debutil.write_ar(output_deb, new_members)
    return {
        "source": str(source_deb.resolve()),
        "output": str(output_deb.resolve()),
        "sha256_before": sha256_file(source_deb),
        "sha256_after": sha256_file(output_deb),
        "control_member": control_member_name,
        "control_changes": control_changes,
    }


def patch_relay_contact(source_relay: Path, output_relay: Path) -> dict[str, object]:
    before = source_relay.read_bytes()
    patched = bytearray(before)
    offsets = []
    start = 0
    while True:
        idx = before.find(OLD_CONTACT, start)
        if idx < 0:
            break
        offsets.append(idx)
        patched[idx : idx + len(OLD_CONTACT)] = NEW_CONTACT_PADDED
        start = idx + 1
    if not offsets:
        raise SystemExit(f"no relay contact occurrences found: {OLD_CONTACT!r}")
    output_relay.parent.mkdir(parents=True, exist_ok=True)
    output_relay.write_bytes(patched)
    return {
        "source": str(source_relay.resolve()),
        "output": str(output_relay.resolve()),
        "sha256_before": hashlib.sha256(before).hexdigest(),
        "sha256_after": hashlib.sha256(patched).hexdigest(),
        "old_contact": OLD_CONTACT.decode("ascii"),
        "new_contact_padded": NEW_CONTACT_PADDED.decode("ascii"),
        "offsets": [f"0x{x:x}" for x in offsets],
        "occurrences": len(offsets),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Patch Sileo metadata and relay console contact only.")
    ap.add_argument("--deb", type=Path, required=True)
    ap.add_argument("--relay", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    deb_info = patch_control_in_deb(
        args.deb, args.output_dir / "com.lumiere.vcamlumiere_2.2.031_kimiki_universal_safe_vcamplus_metadata.deb"
    )
    relay_info = patch_relay_contact(args.relay, args.output_dir / "relay" / "relay.exe")
    manifest = {
        "format": "vcam-kimiki-brand-metadata-relay-only-v1",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": {
            "deb_control_metadata_only": True,
            "relay_contact_only": True,
            "ui_dylib_brand_unchanged": True,
            "watermark_unchanged": True,
            "backend_code_marker_unchanged": "tele: @lumierephan",
        },
        "deb": deb_info,
        "relay": relay_info,
        "notes": [
            "Package id is intentionally unchanged: com.lumiere.vcamlumiere.",
            "UI dylib brand strings are intentionally not patched in this step.",
            "Because UI brand is unchanged, backend VCAM_CODE_MARKER must remain tele: @lumierephan.",
            "Relay contact is padded to preserve binary layout.",
        ],
    }
    manifest_path = args.output_dir / "brand_metadata_relay_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"deb": deb_info["output"], "relay": relay_info["output"], "manifest": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
