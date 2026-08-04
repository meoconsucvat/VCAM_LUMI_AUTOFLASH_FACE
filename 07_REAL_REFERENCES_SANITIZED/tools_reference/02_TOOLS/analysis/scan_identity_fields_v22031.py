from __future__ import annotations

import hashlib
import json
import string
import struct
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM, CS_OP_IMM, CS_OP_MEM, CS_OP_REG


TARGET_URL = b"https://lumierevip.net/vcam"
TARGET_PUB_HEX = "d15ea3d1a9ac3afb8824951ba233190bf3c2d940bde4619f13341b8b0f44940d"
PRINTABLE = set(bytes(string.printable, "ascii"))


@dataclass(frozen=True)
class Slice:
    name: str
    offset: int
    size: int
    cpusubtype: int


@dataclass(frozen=True)
class Field:
    arch: str
    fat_base: int
    table: int
    seed: int
    nonce: int
    indices: int
    length: int
    helper: int
    call_site: int
    decoded_hex: str
    decoded_ascii: str
    kind: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_fat(path: Path) -> list[Slice]:
    b = path.read_bytes()
    if b[:4] not in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        return [Slice("thin", 0, len(b), 0)]
    nfat = struct.unpack_from(">I", b, 4)[0]
    out: list[Slice] = []
    off = 8
    for i in range(nfat):
        cputype, subtype, offset, size, align = struct.unpack_from(">IIIII", b, off)
        off += 20
        if cputype != 0x0100000C:
            continue
        name = "arm64e" if (subtype & 0x80000000) else "arm64"
        out.append(Slice(name, offset, size, subtype))
    return out


def disasm(blob: bytes, rel: int, size: int):
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    md.skipdata = True
    return list(md.disasm(blob[rel : rel + size], rel))


def target_from_adrp_next(insns, idx: int, reg: str) -> int | None:
    ins = insns[idx]
    try:
        if ins.mnemonic != "adrp" or ins.reg_name(ins.operands[0].reg) != reg:
            return None
        if idx + 1 >= len(insns):
            return None
        nxt = insns[idx + 1]
        if not nxt.operands or nxt.operands[0].type != CS_OP_REG:
            return None
        if nxt.reg_name(nxt.operands[0].reg) != reg:
            return None
        page = ins.operands[1].imm
        if nxt.mnemonic == "add" and len(nxt.operands) >= 3 and nxt.operands[2].type == CS_OP_IMM:
            return page + nxt.operands[2].imm
        if nxt.mnemonic == "ldr" and len(nxt.operands) >= 2 and nxt.operands[1].type == CS_OP_MEM:
            return page + nxt.operands[1].mem.disp
        return None
    except Exception:
        return None


def helper_params(thin: bytes, helper: int) -> tuple[int, int] | None:
    if helper < 0 or helper >= len(thin):
        return None
    insns = disasm(thin, helper, min(0x380, len(thin) - helper))
    table = None
    seeds: list[int] = []
    reg_targets: dict[str, int] = {}
    derived_table_regs: dict[str, int] = {}
    for i, ins in enumerate(insns[:-1]):
        try:
            if ins.mnemonic == "adrp" and ins.operands and ins.operands[0].type == CS_OP_REG:
                reg = ins.reg_name(ins.operands[0].reg)
                tgt = target_from_adrp_next(insns, i, reg)
                if tgt is not None:
                    reg_targets[reg] = tgt
                    if reg == "x1" and 0x1000 <= tgt < len(thin):
                        seeds.append(tgt)
            if ins.mnemonic == "add" and len(ins.operands) >= 3:
                if ins.operands[0].type == CS_OP_REG and ins.operands[1].type == CS_OP_REG:
                    dst = ins.reg_name(ins.operands[0].reg)
                    src = ins.reg_name(ins.operands[1].reg)
                    if src in reg_targets:
                        derived_table_regs[dst] = reg_targets[src]
                    elif src in derived_table_regs:
                        derived_table_regs[dst] = derived_table_regs[src]
            if ins.mnemonic == "ldrb" and len(ins.operands) >= 2 and ins.operands[1].type == CS_OP_MEM:
                base_reg = ins.reg_name(ins.operands[1].mem.base)
                cand = reg_targets.get(base_reg) or derived_table_regs.get(base_reg)
                if table is None and cand is not None and 0x1000 <= cand < len(thin):
                    table = cand
        except Exception:
            continue
    seed = None
    for i in range(len(seeds) - 2):
        if seeds[i + 1] == seeds[i] + 0x10 and seeds[i + 2] == seeds[i] + 0x20:
            seed = seeds[i]
            break
    if table is None or seed is None:
        return None
    return table, seed


def keystream(full: bytes, fat_base: int, seed: int, nonce: int, length: int) -> bytes:
    base = fat_base
    s = hashlib.sha256(
        full[base + seed : base + seed + 16]
        + full[base + seed + 16 : base + seed + 32]
        + full[base + seed + 32 : base + seed + 48]
    ).digest()
    out = bytearray()
    for block in range((length + 31) // 32):
        out.extend(hashlib.sha256(s + full[base + nonce : base + nonce + 8] + bytes([block])).digest())
    return bytes(out[:length])


def decode(full: bytes, fat_base: int, table: int, seed: int, nonce: int, indices: int, length: int) -> bytes | None:
    try:
        stream = keystream(full, fat_base, seed, nonce, length)
        enc = bytearray()
        for i in range(length):
            idx = struct.unpack_from("<H", full, fat_base + indices + 2 * i)[0]
            if idx >= 0x1000:
                return None
            pos = fat_base + table + idx
            if pos >= len(full):
                return None
            enc.append(full[pos])
        return bytes(a ^ b for a, b in zip(enc, stream))
    except Exception:
        return None


def classify(raw: bytes) -> str:
    if raw == TARGET_URL:
        return "url"
    if raw.hex() == TARGET_PUB_HEX:
        return "legacy_pub"
    if len(raw) == 32:
        return "pub32_candidate"
    if len(raw) == 44 and all(c in PRINTABLE for c in raw) and raw.endswith(b"="):
        return "spki_pin_candidate"
    if all(c in PRINTABLE for c in raw) and (b"http" in raw or b"lumiere" in raw or b"vcam" in raw):
        return "ascii_candidate"
    return ""


def collect_calls(thin: bytes) -> list[tuple[int, int, int, int, int | None]]:
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    md.skipdata = True
    regs: dict[str, int] = {}
    movs: dict[str, int] = {}
    out = []
    for ins in md.disasm(thin, 0):
        if ins.mnemonic == "ret":
            regs.clear()
            movs.clear()
            continue
        if ins.mnemonic == "adrp" and ins.operands and ins.operands[0].type == CS_OP_REG:
            regs[ins.reg_name(ins.operands[0].reg)] = ins.operands[1].imm
            continue
        if ins.mnemonic == "add" and len(ins.operands) >= 3:
            if ins.operands[0].type == CS_OP_REG and ins.operands[1].type == CS_OP_REG and ins.operands[2].type == CS_OP_IMM:
                dst = ins.reg_name(ins.operands[0].reg)
                src = ins.reg_name(ins.operands[1].reg)
                if src in regs:
                    regs[dst] = regs[src] + ins.operands[2].imm
            continue
        if ins.mnemonic == "mov" and len(ins.operands) >= 2:
            if ins.operands[0].type == CS_OP_REG and ins.operands[1].type == CS_OP_IMM:
                movs[ins.reg_name(ins.operands[0].reg)] = ins.operands[1].imm
                continue
            if ins.operands[0].type == CS_OP_REG and ins.operands[1].type == CS_OP_REG:
                dst = ins.reg_name(ins.operands[0].reg)
                src = ins.reg_name(ins.operands[1].reg)
                if src in regs:
                    regs[dst] = regs[src]
                if src in movs:
                    movs[dst] = movs[src]
            continue
        if ins.mnemonic == "bl" and ins.operands and ins.operands[0].type == CS_OP_IMM:
            length = movs.get("w2")
            if "x0" in regs and "x1" in regs:
                out.append((ins.address, ins.operands[0].imm, regs["x0"], regs["x1"], int(length) if length in (27, 32, 44) else None))
            regs.clear()
            movs.clear()
    return out


def scan_file(path: Path) -> dict:
    full = path.read_bytes()
    result = {
        "path": str(path),
        "size": len(full),
        "sha256": sha256(full),
        "slices": [asdict(s) for s in parse_fat(path)],
        "fields": [],
    }
    for sl in parse_fat(path):
        thin = full[sl.offset : sl.offset + sl.size]
        calls = collect_calls(thin)
        helper_cache: dict[int, tuple[int, int] | None] = {}
        for call_site, helper, nonce, indices, length_hint in calls:
            if helper not in helper_cache:
                helper_cache[helper] = helper_params(thin, helper)
            params = helper_cache[helper]
            if not params:
                continue
            table, seed = params
            lengths = [length_hint] if length_hint in (27, 32, 44) else [27, 32, 44]
            for length in lengths:
                raw = decode(full, sl.offset, table, seed, nonce, indices, int(length))
                if raw is None:
                    continue
                kind = classify(raw)
                if not kind:
                    continue
                result["fields"].append(asdict(Field(
                    arch=sl.name,
                    fat_base=sl.offset,
                    table=table,
                    seed=seed,
                    nonce=nonce,
                    indices=indices,
                    length=int(length),
                    helper=helper,
                    call_site=call_site,
                    decoded_hex=raw.hex(),
                    decoded_ascii=raw.decode("ascii", "replace"),
                    kind=kind,
                )))
    return result


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: scan_identity_fields_v22031.py <dylib> [<dylib>...]", file=sys.stderr)
        return 2
    print(json.dumps([scan_file(Path(x)) for x in argv[1:]], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
