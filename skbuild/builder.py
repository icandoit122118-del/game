"""CMake 프리셋 기반 빌드 래퍼 (Windows + MSVC + vcpkg)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

from skbuild.config import ProjectConfig
from skbuild.scaffold import BASELINE_PLACEHOLDER


class BuildError(RuntimeError):
    pass


def build_commands(cfg: ProjectConfig, preset: str | None = None) -> list[list[str]]:
    preset = preset or cfg.preset
    return [
        ["cmake", "--preset", preset],
        ["cmake", "--build", "--preset", preset],
    ]


def preflight(cfg: ProjectConfig) -> list[str]:
    """빌드 전에 환경 문제를 모아 반환 (빈 리스트면 통과)."""
    problems = []
    if platform.system() != "Windows":
        problems.append("SKSE 플러그인은 Windows(MSVC)에서만 빌드할 수 있습니다")
    if shutil.which("cmake") is None:
        problems.append("cmake 를 PATH 에서 찾을 수 없습니다")
    uses_vcpkg = (cfg.root / "vcpkg.json").is_file()
    if uses_vcpkg and not os.environ.get("VCPKG_ROOT"):
        problems.append("VCPKG_ROOT 환경 변수가 설정되지 않았습니다")
    vcfg = cfg.root / "vcpkg-configuration.json"
    if vcfg.is_file() and BASELINE_PLACEHOLDER in vcfg.read_text(encoding="utf-8"):
        problems.append(f"{vcfg.name} 의 baseline 을 실제 커밋 SHA 로 채워야 합니다")
    return problems


def run_build(cfg: ProjectConfig, preset: str | None = None, dry_run: bool = False) -> list[list[str]]:
    cmds = build_commands(cfg, preset)
    if dry_run:
        return cmds
    problems = preflight(cfg)
    if problems:
        raise BuildError("빌드 환경 문제:\n  - " + "\n  - ".join(problems))
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=cfg.root)
        if result.returncode != 0:
            raise BuildError(f"명령 실패 (exit {result.returncode}): {' '.join(cmd)}")
    return cmds


def find_output(cfg: ProjectConfig, suffix: str = ".dll") -> Path | None:
    """빌드 폴더에서 가장 최근 산출물(<name>.dll / .pdb)을 찾는다."""
    build_dir = cfg.root / cfg.build_dir
    if not build_dir.is_dir():
        return None
    target = cfg.name + suffix
    candidates = [p for p in build_dir.rglob(target) if p.is_file()]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None
