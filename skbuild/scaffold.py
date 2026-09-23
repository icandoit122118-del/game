"""CommonLibSSE-NG 기반 SKSE 플러그인 프로젝트 생성."""

from __future__ import annotations

import re
import subprocess
from importlib import resources
from pathlib import Path

from skbuild.runtimes import get_runtime

BASELINE_PLACEHOLDER = "REPLACE_WITH_COMMIT_SHA"
VCPKG_REPO = "https://github.com/microsoft/vcpkg"
COLORGLASS_REPO = "https://gitlab.com/colorglass/vcpkg-colorglass"

# 템플릿 폴더 안의 파일 -> 생성 경로. common/ 은 모든 템플릿에 공통.
COMMON_FILES = {
    "skbuild.toml": "skbuild.toml",
    "gitignore": ".gitignore",
}
TEMPLATES = {
    # CommonLibSSE-NG + vcpkg: 게임 구조체/함수를 폭넓게 다루는 플러그인용
    "commonlib": {
        "CMakeLists.txt": "CMakeLists.txt",
        "CMakePresets.json": "CMakePresets.json",
        "vcpkg.json": "vcpkg.json",
        "vcpkg-configuration.json": "vcpkg-configuration.json",
        "src/PCH.h": "src/PCH.h",
        "src/main.cpp": "src/main.cpp",
    },
    # 외부 라이브러리 없음: SKSE ABI + Address Library 로더를 직접 포함
    "minimal": {
        "CMakeLists.txt": "CMakeLists.txt",
        "CMakePresets.json": "CMakePresets.json",
        "src/SKSE.h": "src/SKSE.h",
        "src/AddressLibrary.h": "src/AddressLibrary.h",
        "src/main.cpp": "src/main.cpp",
    },
}
DEFAULT_TEMPLATE = "commonlib"

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}$")


def resolve_head(repo: str, timeout: float = 15.0) -> str | None:
    """git ls-remote 로 레지스트리 HEAD 커밋을 조회 (실패 시 None)."""
    try:
        out = subprocess.run(
            ["git", "ls-remote", repo, "HEAD"],
            capture_output=True, text=True, timeout=timeout, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    sha = out.split()[0] if out.split() else ""
    return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None


def slugify(name: str) -> str:
    """vcpkg 매니페스트 이름 규칙(소문자, 숫자, '-')."""
    slug = re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "skse-plugin"


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"@@{key}@@", value)
    return text


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def create_project(
    dest: Path,
    name: str,
    *,
    author: str = "",
    version: str = "1.0.0",
    description: str = "",
    runtimes: list[str] | None = None,
    template: str = DEFAULT_TEMPLATE,
    resolve_baselines: bool = True,
    force: bool = False,
) -> list[Path]:
    if template not in TEMPLATES:
        raise ValueError(f"알 수 없는 템플릿: {template!r} (가능: {', '.join(TEMPLATES)})")
    if not _NAME_RE.match(name):
        raise ValueError(f"플러그인 이름은 영문/숫자/_ 만 사용하고 숫자로 시작할 수 없습니다: {name!r}")
    if not _VERSION_RE.match(version):
        raise ValueError(f"버전 형식이 잘못되었습니다: {version!r} (예: 1.0.0)")
    runtimes = runtimes or [get_runtime().version]
    for rt in runtimes:
        get_runtime(rt)  # 형식 검증

    dest = dest.resolve()
    if dest.exists() and any(dest.iterdir()) and not force:
        raise FileExistsError(f"대상 폴더가 비어 있지 않습니다: {dest} (--force 로 덮어쓰기)")

    vcpkg_sha = colorglass_sha = None
    if resolve_baselines and "vcpkg-configuration.json" in TEMPLATES[template]:
        vcpkg_sha = resolve_head(VCPKG_REPO)
        colorglass_sha = resolve_head(COLORGLASS_REPO)

    values = {
        "NAME": name,
        "SLUG": slugify(name),
        "VERSION": version,
        "AUTHOR": _escape(author),
        "DESCRIPTION": _escape(description),
        "RUNTIMES": ", ".join(f'"{r}"' for r in runtimes),
        "VCPKG_BASELINE": vcpkg_sha or BASELINE_PLACEHOLDER,
        "COLORGLASS_BASELINE": colorglass_sha or BASELINE_PLACEHOLDER,
    }

    root = resources.files("skbuild").joinpath("templates")
    sources = [(root / "common" / src, rel) for src, rel in COMMON_FILES.items()]
    sources += [(root / template / src, rel) for src, rel in TEMPLATES[template].items()]
    written = []
    for src, rel in sources:
        text = src.read_text(encoding="utf-8")
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(text, values), encoding="utf-8", newline="\n")
        written.append(out)
    return written
