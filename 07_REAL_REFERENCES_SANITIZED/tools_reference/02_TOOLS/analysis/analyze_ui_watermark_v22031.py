from __future__ import annotations

import io
import json
import struct
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM, CS_OP_IMM, CS_OP_MEM, CS_OP_REG

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patch_kimiki_identity_v22031 as base


TARGET_SELECTORS = [
    "drawAtPoint:withAttributes:",
    "imageWithActions:",
    "initWithSize:format:",
    "setTransform:",
    "systemRedColor",
    "drawInRect:withAttributes:",
]


@dataclass
class Slice:
    name: str
    offset: int
    size: int


@dataclass
class Section:
    seg: str
    sect: str
    addr: int
    size: int
    offset: int


def parse_fat(path: Path) -> list[Slice]:
    data = path.read_bytes()
    magic = data[:4]
    if magic == b"\xca\xfe\xba\xbe":
        n = struct.unpack_from(">I", data, 4)[0]
        out = []
        for i in range(n):
            cputype, _sub, off, size, _align = struct.unpack_from(">IIIII", data, 8 + i * 20)
            out.append(Slice("arm64e" if cputype == 0x100000C and i == 1 else "arm64", off, size))
        return out
    return [Slice("thin", 0, len(data))]


def parse_sections(full: bytes, sl: Slice) -> list[Section]:
    base_off = sl.offset
    if struct.unpack_from("<I", full, base_off)[0] != 0xFEEDFACF:
        raise ValueError(f"not mach-o64 at {base_off:#x}")
    _magic, _cpu, _sub, _filetype, ncmds, _sizeofcmds, _flags, _reserved = struct.unpack_from(
        "<IiiIIIII", full, base_off
    )
    pos = base_off + 32
    sections: list[Section] = []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", full, pos)
        if cmd == 0x19:  # LC_SEGMENT_64
            segname = full[pos + 8 : pos + 24].split(b"\x00", 1)[0].decode("ascii", "replace")
            nsects = struct.unpack_from("<I", full, pos + 64)[0]
            secpos = pos + 72
            for _j in range(nsects):
                sectname = full[secpos : secpos + 16].split(b"\x00", 1)[0].decode("ascii", "replace")
                secseg = full[secpos + 16 : secpos + 32].split(b"\x00", 1)[0].decode("ascii", "replace")
                addr, size = struct.unpack_from("<QQ", full, secpos + 32)
                offset = struct.unpack_from("<I", full, secpos + 48)[0]
                sections.append(Section(secseg or segname, sectname, addr, size, sl.offset + offset))
                secpos += 80
        pos += cmdsize
    return sections


def section_bytes(full: bytes, sec: Section) -> bytes:
    return full[sec.offset : sec.offset + sec.size]


def fileoff_to_va(sections: list[Section], off: int) -> int | None:
    for s in sections:
        if s.offset <= off < s.offset + s.size:
            return s.addr + (off - s.offset)
    return None


def va_to_fileoff(sections: list[Section], va: int) -> int | None:
    for s in sections:
        if s.addr <= va < s.addr + s.size:
            return s.offset + (va - s.addr)
    return None


def find_cstring(full: bytes, sec: Section, text: str) -> tuple[int, int] | None:
    needle = text.encode() + b"\x00"
    idx = section_bytes(full, sec).find(needle)
    if idx < 0:
        return None
    return sec.offset + idx, sec.addr + idx


def find_selrefs(full: bytes, sec: Section, selector_va: int) -> list[tuple[int, int]]:
    hits = []
    data = section_bytes(full, sec)
    needle = struct.pack("<Q", selector_va)
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx < 0:
            break
        hits.append((sec.offset + idx, sec.addr + idx))
        start = idx + 1
    return hits


def referenced_call_contexts(full: bytes, text_sec: Section, target_vas: set[int]) -> list[dict]:
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    regs: dict[str, int] = {}
    pending: list[dict] = []
    contexts: list[dict] = []
    text = section_bytes(full, text_sec)
    for ins in md.disasm(text, text_sec.addr):
        if ins.mnemonic in {"ret", "b"}:
            regs.clear()
            pending.clear()
        if ins.mnemonic == "adrp" and len(ins.operands) >= 2:
            if ins.operands[0].type == CS_OP_REG and ins.operands[1].type == CS_OP_IMM:
                regs[ins.reg_name(ins.operands[0].reg)] = ins.operands[1].imm
            continue
        if ins.mnemonic == "add" and len(ins.operands) >= 3:
            if (
                ins.operands[0].type == CS_OP_REG
                and ins.operands[1].type == CS_OP_REG
                and ins.operands[2].type == CS_OP_IMM
            ):
                dst = ins.reg_name(ins.operands[0].reg)
                src = ins.reg_name(ins.operands[1].reg)
                if src in regs:
                    regs[dst] = regs[src] + ins.operands[2].imm
            continue
        if ins.mnemonic == "ldr" and len(ins.operands) >= 2:
            op0, op1 = ins.operands[0], ins.operands[1]
            if op0.type == CS_OP_REG and op1.type == CS_OP_MEM:
                base_reg = ins.reg_name(op1.mem.base)
                if base_reg in regs:
                    addr = regs[base_reg] + op1.mem.disp
                    if addr in target_vas:
                        pending.append({
                            "selector_load_va": f"0x{ins.address:x}",
                            "selector_ref_va": f"0x{addr:x}",
                            "register": ins.reg_name(op0.reg),
                        })
            continue
        if ins.mnemonic == "bl" and pending:
            contexts.append({
                "call_va": f"0x{ins.address:x}",
                "target_va": f"0x{ins.operands[0].imm:x}" if ins.operands and ins.operands[0].type == CS_OP_IMM else ins.op_str,
                "pending": pending[-5:],
            })
            pending = []
    return contexts


def extract_ui_from_deb(deb: Path, out: Path) -> Path:
    members = base.read_ar(deb)
    data_member = next((m for m in members if m[0].startswith("data.tar")), None)
    if data_member is None:
        raise SystemExit("data.tar.* not found")
    raw, _ = base.decompress_tar(*data_member)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tf:
        f = tf.extractfile(base.UI_MEMBER)
        if f is None:
            raise SystemExit("UI dylib not found")
        ui = f.read()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(ui)
    return out


def analyze(path: Path) -> dict:
    full = path.read_bytes()
    result = {"path": str(path), "slices": []}
    for sl in parse_fat(path):
        secs = parse_sections(full, sl)
        meth = next((s for s in secs if s.sect == "__objc_methname"), None)
        selrefs = next((s for s in secs if s.sect == "__objc_selrefs"), None)
        text = next((s for s in secs if s.sect == "__text"), None)
        if not meth or not selrefs or not text:
            continue
        selectors = {}
        target_ref_vas = set()
        ref_to_selector = {}
        for selector in TARGET_SELECTORS:
            found = find_cstring(full, meth, selector)
            if not found:
                continue
            off, va = found
            refs = find_selrefs(full, selrefs, va)
            selectors[selector] = {
                "string_fileoff": f"0x{off:x}",
                "string_va": f"0x{va:x}",
                "selrefs": [{"fileoff": f"0x{o:x}", "va": f"0x{v:x}"} for o, v in refs],
            }
            for _o, v in refs:
                target_ref_vas.add(v)
                ref_to_selector[v] = selector
        contexts = referenced_call_contexts(full, text, target_ref_vas)
        for ctx in contexts:
            for p in ctx["pending"]:
                p["selector"] = ref_to_selector.get(int(p["selector_ref_va"], 16), "?")
        result["slices"].append({
            "arch": sl.name,
            "slice_offset": f"0x{sl.offset:x}",
            "slice_size": sl.size,
            "sections": {
                "__text": {"addr": f"0x{text.addr:x}", "fileoff": f"0x{text.offset:x}", "size": text.size},
                "__objc_methname": {"addr": f"0x{meth.addr:x}", "fileoff": f"0x{meth.offset:x}", "size": meth.size},
                "__objc_selrefs": {"addr": f"0x{selrefs.addr:x}", "fileoff": f"0x{selrefs.offset:x}", "size": selrefs.size},
            },
            "selectors": selectors,
            "contexts": contexts,
        })
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: analyze_ui_watermark_v22031.py <ui.dylib|deb> [out.json]", file=sys.stderr)
        return 2
    inp = Path(sys.argv[1])
    if inp.suffix == ".deb":
        ui = extract_ui_from_deb(inp, inp.with_suffix(".VcamLumiereUI.dylib"))
    else:
        ui = inp
    result = analyze(ui)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
