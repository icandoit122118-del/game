"""테스트용 최소 SKSE 플러그인 DLL(PE32+) 생성기."""

from __future__ import annotations

import struct

from skbuild.pe import MACHINE_AMD64, VERSION_DATA_SIZE

SECTION_RVA = 0x1000
SECTION_RAW = 0x200


def version_data(
    name: str = "TestPlugin",
    author: str = "tester",
    plugin_version: int = 0x01000000,
    independence: int = 0,
    independence_ex: int = 0,
    compatible: list[int] | None = None,
    se_required: int = 0,
) -> bytes:
    buf = bytearray(VERSION_DATA_SIZE)
    struct.pack_into("<II", buf, 0, 1, plugin_version)
    buf[8 : 8 + len(name)] = name.encode()
    buf[264 : 264 + len(author)] = author.encode()
    struct.pack_into("<II", buf, 772, independence_ex, independence)
    compat = (compatible or [])[:16]
    struct.pack_into(f"<{len(compat)}I", buf, 780, *compat)
    struct.pack_into("<I", buf, 844, se_required)
    return bytes(buf)


def make_dll(exports: list[str], vdata: bytes | None = None, machine: int = MACHINE_AMD64) -> bytes:
    """exports 에 SKSEPlugin_Version 이 있으면 vdata 를 그 심볼로 export 한다."""
    names = sorted(exports)
    sec = bytearray(0x40)  # export directory 자리
    code_off = len(sec)
    sec += b"\xc3" * 16  # 함수 본문(ret)
    vd_off = len(sec)
    sec += vdata or b""

    func_rvas = [SECTION_RVA + (vd_off if n == "SKSEPlugin_Version" else code_off) for n in names]
    funcs_off = len(sec)
    sec += struct.pack(f"<{len(names)}I", *func_rvas)
    name_ptrs_off = len(sec)
    sec += b"\0" * (4 * len(names))
    ords_off = len(sec)
    sec += struct.pack(f"<{len(names)}H", *range(len(names)))
    name_rvas = []
    for n in names:
        name_rvas.append(SECTION_RVA + len(sec))
        sec += n.encode() + b"\0"
    dll_name_rva = SECTION_RVA + len(sec)
    sec += b"TestPlugin.dll\0"
    struct.pack_into(f"<{len(names)}I", sec, name_ptrs_off, *name_rvas)
    struct.pack_into(
        "<IIHHIIIIIII", sec, 0,
        0, 0, 0, 0, dll_name_rva, 1, len(names), len(names),
        SECTION_RVA + funcs_off, SECTION_RVA + name_ptrs_off, SECTION_RVA + ords_off,
    )
    while len(sec) % 0x200:
        sec += b"\0"

    img = bytearray(SECTION_RAW)
    img[0:2] = b"MZ"
    struct.pack_into("<I", img, 0x3C, 0x40)
    img[0x40:0x44] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", img, 0x44, machine, 1, 0, 0, 0, 240, 0x2022)
    opt = 0x58
    struct.pack_into("<H", img, opt, 0x20B)
    struct.pack_into("<II", img, opt + 112, SECTION_RVA, 0x40)  # export data directory
    sh = opt + 240
    img[sh : sh + 8] = b".rdata\0\0"
    struct.pack_into("<IIII", img, sh + 8, len(sec), SECTION_RVA, len(sec), SECTION_RAW)
    return bytes(img + sec)
