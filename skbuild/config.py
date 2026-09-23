"""프로젝트 설정 파일 skbuild.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "skbuild.toml"


@dataclass
class ProjectConfig:
    root: Path
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    runtimes: list[str] = field(default_factory=list)
    preset: str = "release"
    build_dir: str = "build"
    # 패키지에 포함할 추가 파일: {"소스 경로": "Data 기준 대상 경로"}
    extra_files: dict[str, str] = field(default_factory=dict)
    include_pdb: bool = False

    @property
    def dll_name(self) -> str:
        return f"{self.name}.dll"


def find_config(start: Path) -> Path:
    start = start.resolve()
    for d in [start, *start.parents]:
        candidate = d / CONFIG_NAME
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{CONFIG_NAME} 을(를) 찾을 수 없습니다: {start} (먼저 `skbuild init` 실행)")


def load_config(start: Path | None = None) -> ProjectConfig:
    path = find_config(start or Path.cwd())
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    build = data.get("build", {})
    package = data.get("package", {})
    if "name" not in project:
        raise ValueError(f"{path}: [project] name 이 필요합니다")
    return ProjectConfig(
        root=path.parent,
        name=project["name"],
        version=project.get("version", "1.0.0"),
        author=project.get("author", ""),
        description=project.get("description", ""),
        runtimes=list(project.get("runtimes", [])),
        preset=build.get("preset", "release"),
        build_dir=build.get("dir", "build"),
        extra_files=dict(package.get("files", {})),
        include_pdb=bool(package.get("include_pdb", False)),
    )
