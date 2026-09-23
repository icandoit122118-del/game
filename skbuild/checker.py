"""SKSE 플러그인 DLL 의 런타임 / Address Library 호환성 검사."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

from skbuild.pe import PluginDll, parse_dll
from skbuild.runtimes import Runtime, unpack_version

OK, WARN, ERROR = "ok", "warn", "error"
_ICONS = {OK: "[OK]", WARN: "[주의]", ERROR: "[오류]"}


@dataclass
class Finding:
    level: str
    message: str

    def __str__(self) -> str:
        return f"{_ICONS[self.level]} {self.message}"


@dataclass
class RuntimeReport:
    runtime: Runtime
    findings: list[Finding] = field(default_factory=list)
    needs_address_library: bool = False

    @property
    def compatible(self) -> bool:
        return not any(f.level == ERROR for f in self.findings)

    def add(self, level: str, message: str) -> None:
        self.findings.append(Finding(level, message))


def check_runtime(dll: PluginDll, rt: Runtime) -> RuntimeReport:
    rep = RuntimeReport(rt)
    if not dll.is_x64:
        rep.add(ERROR, f"x64 DLL 이 아닙니다 (machine={dll.machine:#x}); 스카이림 SE/AE 는 64비트입니다")
    if not dll.has_load:
        rep.add(ERROR, "SKSEPlugin_Load export 가 없습니다 (SKSE 플러그인이 아님)")

    if rt.is_ae:
        _check_ae(dll, rt, rep)
    else:
        _check_se(dll, rt, rep)
    return rep


def _check_ae(dll: PluginDll, rt: Runtime, rep: RuntimeReport) -> None:
    vd = dll.version_data
    if vd is None:
        rep.add(ERROR, f"SKSEPlugin_Version export 가 없습니다 → SE(1.5.97) 전용 플러그인이라 {rt.version} 에서 로드되지 않습니다")
        return
    if vd.data_version < 1:
        rep.add(ERROR, f"SKSEPluginVersionData.dataVersion={vd.data_version} 이 잘못되었습니다")

    if rt.packed in vd.compatible_versions:
        rep.add(OK, f"{rt.version} 이(가) compatibleVersions 에 명시되어 있습니다 (버전 고정 빌드)")
    elif vd.uses_address_library or vd.uses_signatures:
        how = "Address Library" if vd.uses_address_library else "시그니처 스캔"
        rep.add(OK, f"버전 독립 플러그인 ({how})")
        if rt.post_629 and not (vd.structs_post_629 or vd.no_struct_use):
            rep.add(ERROR, "1.6.629+ 구조체 레이아웃 플래그(StructsPost629 / NoStructUse)가 없어 로드가 거부됩니다")
        elif not rt.post_629 and vd.structs_post_629 and not vd.no_struct_use:
            rep.add(ERROR, "1.6.629+ 구조체 전용으로 빌드되어 이전 런타임에서는 로드되지 않습니다")
    else:
        listed = ", ".join(unpack_version(v) for v in vd.compatible_versions) or "없음"
        rep.add(ERROR, f"버전 독립 플래그가 없고 {rt.version} 이(가) 호환 목록에 없습니다 (목록: {listed})")

    if vd.uses_address_library:
        rep.needs_address_library = True
        rep.add(WARN, f"Address Library 필요: Data/SKSE/Plugins/{rt.address_library}")
    if vd.se_version_required:
        rep.add(WARN, f"최소 SKSE 버전 요구: {unpack_version(vd.se_version_required)}")


def _check_se(dll: PluginDll, rt: Runtime, rep: RuntimeReport) -> None:
    if not dll.has_query:
        rep.add(ERROR, f"SKSEPlugin_Query export 가 없습니다 → {rt.version}(SE) SKSE 가 로드하지 않습니다")
        return
    rep.add(OK, "SKSEPlugin_Query 존재 (SE 로더 호환)")
    rep.needs_address_library = True
    rep.add(WARN, f"Address Library 를 사용하는 경우 필요: Data/SKSE/Plugins/{rt.address_library}")


def check_dll(path: Path, runtimes: list[Runtime]) -> tuple[PluginDll, list[RuntimeReport]]:
    dll = parse_dll(path)
    return dll, [check_runtime(dll, rt) for rt in runtimes]


# ---- 게임 설치 폴더 검사 ----

def read_file_version(exe: Path) -> str | None:
    """VS_FIXEDFILEINFO 시그니처를 찾아 파일 버전을 읽는다 (예: SkyrimSE.exe)."""
    data = exe.read_bytes()
    idx = data.find(struct.pack("<I", 0xFEEF04BD))
    if idx < 0 or idx + 16 > len(data):
        return None
    ms, ls = struct.unpack_from("<II", data, idx + 8)
    return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"


def check_game_dir(game_dir: Path, rt: Runtime, needs_address_library: bool = True) -> list[Finding]:
    findings = []
    exe = game_dir / "SkyrimSE.exe"
    if exe.is_file():
        ver = read_file_version(exe)
        if ver:
            installed = ".".join(ver.split(".")[:3])
            if installed == ".".join(rt.version.split(".")[:3]):
                findings.append(Finding(OK, f"SkyrimSE.exe 버전 {ver}"))
            else:
                findings.append(Finding(WARN, f"설치된 SkyrimSE.exe 버전 {ver} ≠ 대상 런타임 {rt.version}"))
    else:
        findings.append(Finding(ERROR, f"SkyrimSE.exe 가 없습니다: {game_dir}"))

    if (game_dir / "skse64_loader.exe").is_file():
        findings.append(Finding(OK, "skse64_loader.exe 설치됨"))
    else:
        findings.append(Finding(ERROR, "skse64_loader.exe 가 없습니다 (SKSE 미설치)"))

    if needs_address_library:
        bin_path = game_dir / "Data" / "SKSE" / "Plugins" / rt.address_library
        if bin_path.is_file():
            findings.append(Finding(OK, f"Address Library 설치됨 ({rt.address_library})"))
        else:
            findings.append(Finding(ERROR, f"Address Library 가 없습니다: {bin_path}"))
    return findings
