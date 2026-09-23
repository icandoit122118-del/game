"""스카이림 런타임 정의 (data/runtimes.json)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources

# SKSE 가 런타임 버전을 u32 로 패킹하는 방식 (MAKE_EXE_VERSION_EX)
def pack_version(major: int, minor: int, build: int, sub: int = 0) -> int:
    return ((major & 0xFF) << 24) | ((minor & 0xFF) << 16) | ((build & 0xFFF) << 4) | (sub & 0xF)


def unpack_version(value: int) -> str:
    major = (value >> 24) & 0xFF
    minor = (value >> 16) & 0xFF
    build = (value >> 4) & 0xFFF
    sub = value & 0xF
    return f"{major}.{minor}.{build}" + (f".{sub}" if sub else "")


def parse_version(text: str) -> tuple[int, int, int, int]:
    parts = [int(p) for p in text.strip().split(".")]
    if not 3 <= len(parts) <= 4:
        raise ValueError(f"잘못된 런타임 버전: {text!r} (예: 1.7.104)")
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


# 1.6.629 부터 게임 구조체 레이아웃이 바뀌어 SKSE 가 별도 플래그를 요구한다.
STRUCTS_629 = (1, 6, 629, 0)


@dataclass(frozen=True)
class Runtime:
    version: str
    edition: str
    label: str
    address_library: str

    @property
    def parts(self) -> tuple[int, int, int, int]:
        return parse_version(self.version)

    @property
    def packed(self) -> int:
        return pack_version(*self.parts)

    @property
    def is_ae(self) -> bool:
        return self.parts >= (1, 6, 0, 0)

    @property
    def post_629(self) -> bool:
        return self.parts >= STRUCTS_629


def _load() -> dict:
    text = resources.files("skbuild").joinpath("data/runtimes.json").read_text(encoding="utf-8")
    return json.loads(text)


def all_runtimes() -> list[Runtime]:
    return [Runtime(**r) for r in _load()["runtimes"]]


def default_version() -> str:
    return _load()["default"]


def get_runtime(version: str | None = None) -> Runtime:
    version = version or default_version()
    for rt in all_runtimes():
        if rt.version == version:
            return rt
    # 목록에 없는 버전도 규칙대로 추정해서 사용할 수 있게 한다.
    parts = parse_version(version)
    dashed = "-".join(str(p) for p in parts)
    if parts >= (1, 6, 0, 0):
        return Runtime(version, "AE", "사용자 지정", f"versionlib-{dashed}.bin")
    return Runtime(version, "SE", "사용자 지정", f"version-{dashed}.bin")
