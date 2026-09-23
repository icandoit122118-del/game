"""Data 폴더 레이아웃의 배포 zip (옵션: FOMOD) 생성."""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath
from xml.sax.saxutils import escape

from skbuild.config import ProjectConfig
from skbuild.runtimes import Runtime

PLUGIN_DIR = "SKSE/Plugins"


def collect_files(cfg: ProjectConfig, dll: Path, pdb: Path | None = None) -> dict[str, Path]:
    """zip 내부 경로(Data 기준) -> 원본 파일."""
    files = {f"{PLUGIN_DIR}/{dll.name}": dll}
    if cfg.include_pdb and pdb and pdb.is_file():
        files[f"{PLUGIN_DIR}/{pdb.name}"] = pdb
    for src, dst in cfg.extra_files.items():
        path = (cfg.root / src).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"[package.files] 파일이 없습니다: {src}")
        dst_path = PurePosixPath(dst.replace("\\", "/"))
        if dst_path.is_absolute() or ".." in dst_path.parts:
            raise ValueError(f"[package.files] 대상 경로는 Data 기준 상대 경로여야 합니다: {dst}")
        files[str(dst_path)] = path
    return files


def fomod_info(cfg: ProjectConfig) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<fomod>\n"
        f"  <Name>{escape(cfg.name)}</Name>\n"
        f"  <Author>{escape(cfg.author)}</Author>\n"
        f"  <Version>{escape(cfg.version)}</Version>\n"
        f"  <Description>{escape(cfg.description)}</Description>\n"
        "</fomod>\n"
    )


def fomod_module_config(cfg: ProjectConfig, runtimes: list[Runtime]) -> str:
    requirements = ", ".join(rt.version for rt in runtimes)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">\n'
        f"  <moduleName>{escape(cfg.name)}</moduleName>\n"
        "  <requiredInstallFiles>\n"
        '    <folder source="Data" destination=""/>\n'
        "  </requiredInstallFiles>\n"
        f"  <!-- 요구 사항: SKSE64, Address Library (런타임 {escape(requirements)}) -->\n"
        "</config>\n"
    )


def create_package(
    cfg: ProjectConfig,
    dll: Path,
    out_dir: Path,
    runtimes: list[Runtime],
    *,
    pdb: Path | None = None,
    fomod: bool = False,
) -> Path:
    files = collect_files(cfg, dll, pdb)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{cfg.name}-{cfg.version}.zip"
    # FOMOD 설치기는 Data 폴더를 통째로 복사, 일반 zip 은 루트가 곧 Data 폴더.
    prefix = "Data/" if fomod else ""
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, src in sorted(files.items()):
            zf.write(src, prefix + arc)
        if fomod:
            zf.writestr("fomod/info.xml", fomod_info(cfg))
            zf.writestr("fomod/ModuleConfig.xml", fomod_module_config(cfg, runtimes))
    return archive
