#!/usr/bin/env python3
"""Apply the accepted automatic book skip to the development ROM."""

from hashlib import sha256
from pathlib import Path
import shutil
import struct
import sys


BASE_SHA256 = "58ba15896e9decf7575fd70c70a14279a349884a5d4542ffd2a27ffc79db5025"
PATCHED_SHA256 = "10b66522c3ba89f1830b437c3e8ef5b8bedae12fbe50623ed6a0d773caa2e8e3"
ROM_NAME = "Shining Soul II - Monster Hunter Mod Dev.gba"
BACKUP_NAME = "Shining Soul II - Monster Hunter Mod Dev.before-book-ready-skip.gba"
HOOK_OFFSET = 0x77C
CAVE_OFFSET = 0x3F9040


def thumb_bl(source: int, target: int) -> bytes:
    displacement = target - (source + 4)
    if displacement % 2 or not -(1 << 22) <= displacement < (1 << 22):
        raise ValueError("Thumb BL target is out of range")
    high = 0xF000 | ((displacement >> 12) & 0x7FF)
    low = 0xF800 | ((displacement >> 1) & 0x7FF)
    return struct.pack("<HH", high, low)


def main() -> None:
    rom = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / ROM_NAME
    backup = rom.with_name(BACKUP_NAME)
    data = bytearray(rom.read_bytes())
    current_sha = sha256(data).hexdigest()
    if current_sha == PATCHED_SHA256:
        print(f"Already patched: {rom}")
        return
    if current_sha != BASE_SHA256:
        raise SystemExit(f"Unexpected ROM SHA-256: {current_sha}")
    if data[HOOK_OFFSET : HOOK_OFFSET + 4] != bytes.fromhex("0580f020"):
        raise SystemExit("Unexpected input hook bytes")

    # 0300296C identifies the opening coroutine. 030029B8 distinguishes the
    # initialized book from the earlier character-confirmation transition.
    cave = bytes.fromhex(
        "0eb4"      # push {r1-r3}
        "0849"      # ldr r1, =0300296C
        "0a68"      # ldr r2, [r1]
        "084b"      # ldr r3, =08002CF9
        "9a42"      # cmp r2, r3
        "06d1"      # bne finish
        "0749"      # ldr r1, =030029B8
        "0a68"      # ldr r2, [r1]
        "074b"      # ldr r3, =030065A0
        "9a42"      # cmp r2, r3
        "01d1"      # bne finish
        "0821"      # movs r1, #8 (Start)
        "0d43"      # orrs r5, r1
        "0ebc"      # finish: pop {r1-r3}
        "0580"      # original strh r5, [r0]
        "f020"      # original movs r0, #0xF0
        "7047"      # bx lr
        "c046"      # alignment
        "6c290003"  # 0300296C
        "f92c0008"  # 08002CF9
        "b8290003"  # 030029B8
        "a0650003"  # 030065A0
    )
    if any(data[CAVE_OFFSET : CAVE_OFFSET + len(cave)]):
        raise SystemExit("Selected code cave is not empty")

    if backup.exists() and sha256(backup.read_bytes()).hexdigest() != BASE_SHA256:
        raise SystemExit(f"Existing backup does not match the base ROM: {backup}")
    if not backup.exists():
        shutil.copy2(rom, backup)

    data[CAVE_OFFSET : CAVE_OFFSET + len(cave)] = cave
    data[HOOK_OFFSET : HOOK_OFFSET + 4] = thumb_bl(
        0x08000000 + HOOK_OFFSET, 0x08000000 + CAVE_OFFSET
    )
    patched_sha = sha256(data).hexdigest()
    if patched_sha != PATCHED_SHA256:
        raise SystemExit(f"Patch result differs from the tested ROM: {patched_sha}")
    rom.write_bytes(data)
    print(f"Patched: {rom}")
    print(f"Backup:  {backup}")
    print(f"SHA-256: {patched_sha}")


if __name__ == "__main__":
    main()
