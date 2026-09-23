"""SKSE 플러그인 DLL 분석용 최소 PE 파서 (표준 라이브러리만 사용)."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

MACHINE_AMD64 = 0x8664
MACHINE_I386 = 0x14C

# SKSE64 PluginAPI.h 의 SKSEPluginVersionData
VERSION_DATA_SIZE = 848
ADDRESS_LIBRARY_POST_AE = 1 << 0   # kVersionIndependent_AddressLibraryPostAE
SIGNATURES = 1 << 1                # kVersionIndependent_Signatures
STRUCTS_POST_629 = 1 << 2          # kVersionIndependent_StructsPost629
EX_NO_STRUCT_USE = 1 << 0          # kVersionIndependentEx_NoStructUse


class PEError(ValueError):
    pass


@dataclass
class Section:
    name: str
    virtual_address: int
    virtual_size: int
    raw_offset: int
    raw_size: int


@dataclass
class VersionData:
    data_version: int
    plugin_version: int
    name: str
    author: str
    support_email: str
    version_independence_ex: int
    version_independence: int
    compatible_versions: list[int]
    se_version_required: int

    @property
    def uses_address_library(self) -> bool:
        return bool(self.version_independence & ADDRESS_LIBRARY_POST_AE)

    @property
    def uses_signatures(self) -> bool:
        return bool(self.version_independence & SIGNATURES)

    @property
    def structs_post_629(self) -> bool:
        return bool(self.version_independence & STRUCTS_POST_629)

    @property
    def no_struct_use(self) -> bool:
        return bool(self.version_independence_ex & EX_NO_STRUCT_USE)

    @classmethod
    def parse(cls, raw: bytes) -> "VersionData":
        if len(raw) < VERSION_DATA_SIZE:
            raise PEError("SKSEPlugin_Version 데이터가 잘렸습니다")

        def cstr(b: bytes) -> str:
            return b.split(b"\0", 1)[0].decode("utf-8", errors="replace")

        data_version, plugin_version = struct.unpack_from("<II", raw, 0)
        name = cstr(raw[8:264])
        author = cstr(raw[264:520])
        email = cstr(raw[520:772])
        ex, indep = struct.unpack_from("<II", raw, 772)
        compat = list(struct.unpack_from("<16I", raw, 780))
        (se_required,) = struct.unpack_from("<I", raw, 844)
        compat = compat[: compat.index(0)] if 0 in compat else compat
        return cls(data_version, plugin_version, name, author, email, ex, indep, compat, se_required)


@dataclass
class PluginDll:
    path: Path
    machine: int
    exports: dict[str, int] = field(default_factory=dict)
    version_data: VersionData | None = None

    @property
    def is_x64(self) -> bool:
        return self.machine == MACHINE_AMD64

    @property
    def has_query(self) -> bool:
        return "SKSEPlugin_Query" in self.exports

    @property
    def has_load(self) -> bool:
        return "SKSEPlugin_Load" in self.exports

    @property
    def has_version(self) -> bool:
        return "SKSEPlugin_Version" in self.exports


class _Image:
    def __init__(self, data: bytes):
        self.data = data
        if data[:2] != b"MZ":
            raise PEError("MZ 헤더가 없습니다 (DLL 이 아님)")
        (pe_off,) = struct.unpack_from("<I", data, 0x3C)
        if data[pe_off : pe_off + 4] != b"PE\0\0":
            raise PEError("PE 시그니처가 없습니다")
        coff = pe_off + 4
        self.machine, nsections = struct.unpack_from("<HH", data, coff)
        (opt_size,) = struct.unpack_from("<H", data, coff + 16)
        opt = coff + 20
        (magic,) = struct.unpack_from("<H", data, opt)
        if magic == 0x20B:
            dd_off = opt + 112
        elif magic == 0x10B:
            dd_off = opt + 96
        else:
            raise PEError(f"알 수 없는 Optional Header magic: {magic:#x}")
        self.export_rva, self.export_size = struct.unpack_from("<II", data, dd_off)
        self.sections = []
        sec = opt + opt_size
        for i in range(nsections):
            off = sec + i * 40
            name = data[off : off + 8].rstrip(b"\0").decode("ascii", errors="replace")
            vsize, va, rsize, roff = struct.unpack_from("<IIII", data, off + 8)
            self.sections.append(Section(name, va, vsize, roff, rsize))

    def rva_to_offset(self, rva: int) -> int:
        for s in self.sections:
            if s.virtual_address <= rva < s.virtual_address + max(s.virtual_size, s.raw_size):
                return s.raw_offset + (rva - s.virtual_address)
        raise PEError(f"RVA {rva:#x} 가 어느 섹션에도 속하지 않습니다")

    def read(self, rva: int, size: int) -> bytes:
        off = self.rva_to_offset(rva)
        return self.data[off : off + size]

    def cstr(self, rva: int) -> str:
        off = self.rva_to_offset(rva)
        end = self.data.index(b"\0", off)
        return self.data[off:end].decode("ascii", errors="replace")

    def exports(self) -> dict[str, int]:
        if not self.export_rva:
            return {}
        d = self.read(self.export_rva, 40)
        nfuncs, nnames, funcs, names, ords = struct.unpack_from("<IIIII", d, 20)
        result = {}
        for i in range(nnames):
            (name_rva,) = struct.unpack("<I", self.read(names + 4 * i, 4))
            (ordinal,) = struct.unpack("<H", self.read(ords + 2 * i, 2))
            if ordinal >= nfuncs:
                continue
            (func_rva,) = struct.unpack("<I", self.read(funcs + 4 * ordinal, 4))
            result[self.cstr(name_rva)] = func_rva
        return result


def parse_bytes(data: bytes, path: Path | None = None) -> PluginDll:
    try:
        img = _Image(data)
        exports = img.exports()
        dll = PluginDll(path or Path("<memory>"), img.machine, exports)
        if "SKSEPlugin_Version" in exports:
            dll.version_data = VersionData.parse(img.read(exports["SKSEPlugin_Version"], VERSION_DATA_SIZE))
    except (struct.error, IndexError, ValueError) as e:
        if isinstance(e, PEError):
            raise
        raise PEError(f"PE 파싱 실패: {e}") from e
    return dll


def parse_dll(path: Path) -> PluginDll:
    return parse_bytes(Path(path).read_bytes(), Path(path))
