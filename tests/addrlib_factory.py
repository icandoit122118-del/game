"""테스트용 Address Library .bin 인코더 (여러 인코딩 분기를 골고루 사용)."""

from __future__ import annotations

import struct


def _id_options(id_, prev):
    diff = id_ - prev
    opts = [(0, struct.pack("<Q", id_))]
    if diff == 1:
        opts.append((1, b""))
    if 0 <= diff <= 0xFF:
        opts.append((2, struct.pack("<B", diff)))
    if 0 <= -diff <= 0xFF:
        opts.append((3, struct.pack("<B", -diff)))
    if 0 <= diff <= 0xFFFF:
        opts.append((4, struct.pack("<H", diff)))
    if 0 <= -diff <= 0xFFFF:
        opts.append((5, struct.pack("<H", -diff)))
    if id_ <= 0xFFFF:
        opts.append((6, struct.pack("<H", id_)))
    if id_ <= 0xFFFFFFFF:
        opts.append((7, struct.pack("<I", id_)))
    return opts


def _offset_options(offset, prev, ptr_size):
    opts = []
    for scaled in (False, True):
        if scaled and offset % ptr_size:
            continue
        value = offset // ptr_size if scaled else offset
        base = prev // ptr_size if scaled else prev
        flag = 8 if scaled else 0
        diff = value - base
        opts.append((flag | 0, struct.pack("<Q", value)))
        if diff == 1:
            opts.append((flag | 1, b""))
        if 0 <= diff <= 0xFF:
            opts.append((flag | 2, struct.pack("<B", diff)))
        if 0 <= -diff <= 0xFF:
            opts.append((flag | 3, struct.pack("<B", -diff)))
        if 0 <= diff <= 0xFFFF:
            opts.append((flag | 4, struct.pack("<H", diff)))
        if 0 <= -diff <= 0xFFFF:
            opts.append((flag | 5, struct.pack("<H", -diff)))
        if value <= 0xFFFF:
            opts.append((flag | 6, struct.pack("<H", value)))
        if value <= 0xFFFFFFFF:
            opts.append((flag | 7, struct.pack("<I", value)))
    return opts


def _pick(opts, preferred):
    """가능하면 preferred 타입을, 아니면 첫 번째(항상 가능한 절대값) 인코딩을 고른다."""
    for opt in opts:
        if opt[0] == preferred:
            return opt
    return opts[0]


def encode(pairs, version=(1, 7, 104, 0), fmt=2, module="SkyrimSE.exe", ptr_size=8) -> bytes:
    out = bytearray(struct.pack("<i4i", fmt, *version))
    name = module.encode()
    out += struct.pack("<i", len(name)) + name
    out += struct.pack("<ii", ptr_size, len(pairs))
    prev_id = prev_off = 0
    for i, (id_, offset) in enumerate(pairs):
        id_opts = _id_options(id_, prev_id)
        off_opts = _offset_options(offset, prev_off, ptr_size)
        low, id_bytes = _pick(id_opts, i % 8)
        high, off_bytes = _pick(off_opts, (i * 3) % 16)
        out += struct.pack("<B", (high << 4) | low) + id_bytes + off_bytes
        prev_id, prev_off = id_, offset
    return bytes(out)


def sample_pairs(n: int = 400) -> list[tuple[int, int]]:
    pairs, id_, off = [], 1000, 0x1000
    for i in range(n):
        id_ += (1, 3, 300, 70000, 2)[i % 5]
        if i % 11 == 0:
            id_ -= 150
        if i % 17 == 6:
            id_ = 500 + i  # 작은 ID (16비트 절대값 인코딩)
        off += (8, 16, 0x40, 0x12345, 1)[i % 5]
        if i % 13 == 0:
            off -= 0x100
        pairs.append((id_, off))
    return pairs
