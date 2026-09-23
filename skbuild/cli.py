"""skbuild 명령줄 인터페이스."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skbuild import __version__
from skbuild.builder import BuildError, find_output, run_build
from skbuild.checker import ERROR, RuntimeReport, check_dll, check_game_dir
from skbuild.config import load_config
from skbuild.packager import create_package
from skbuild.pe import PEError
from skbuild.runtimes import all_runtimes, default_version, get_runtime, unpack_version
from skbuild.scaffold import BASELINE_PLACEHOLDER, DEFAULT_TEMPLATE, TEMPLATES, create_project


def _runtimes(values: list[str] | None, fallback: list[str] | None = None):
    versions = values or fallback or [default_version()]
    return [get_runtime(v) for v in versions]


def cmd_runtimes(args) -> int:
    default = default_version()
    for rt in all_runtimes():
        mark = "*" if rt.version == default else " "
        print(f"{mark} {rt.version:<10} {rt.edition}  {rt.address_library:<28} {rt.label}")
    print("\n* = 기본 대상 런타임")
    return 0


def cmd_init(args) -> int:
    dest = Path(args.path or args.name)
    written = create_project(
        dest,
        args.name,
        author=args.author,
        version=args.version,
        description=args.description,
        runtimes=args.runtime,
        template=args.template,
        resolve_baselines=not args.offline,
        force=args.force,
    )
    print(f"프로젝트 생성 ({args.template} 템플릿): {dest.resolve()}")
    for p in written:
        print(f"  + {p.relative_to(dest.resolve())}")
    vcfg = dest / "vcpkg-configuration.json"
    if vcfg.is_file() and BASELINE_PLACEHOLDER in vcfg.read_text(encoding="utf-8"):
        print(f"\n[주의] {vcfg.name} 의 baseline 을 채우지 못했습니다. 각 레지스트리의 최신 커밋 SHA 로 바꾸세요:")
        print("  git ls-remote https://github.com/microsoft/vcpkg HEAD")
        print("  git ls-remote https://gitlab.com/colorglass/vcpkg-colorglass HEAD")
    print("\n다음 단계: cd", dest, "&& skbuild build")
    return 0


def cmd_build(args) -> int:
    cfg = load_config(Path(args.project))
    cmds = run_build(cfg, args.preset, dry_run=args.dry_run)
    if args.dry_run:
        for c in cmds:
            print(" ".join(c))
        return 0
    dll = find_output(cfg)
    print(f"빌드 완료: {dll}" if dll else "빌드 완료 (DLL 위치를 찾지 못했습니다)")
    return 0


def _print_reports(dll, reports: list[RuntimeReport]) -> None:
    print(f"DLL: {dll.path}")
    vd = dll.version_data
    if vd:
        print(f"  이름: {vd.name}  작성자: {vd.author}  플러그인 버전: {vd.plugin_version:#x}")
        if vd.compatible_versions:
            print("  compatibleVersions:", ", ".join(unpack_version(v) for v in vd.compatible_versions))
    exports = [e for e in ("SKSEPlugin_Version", "SKSEPlugin_Query", "SKSEPlugin_Load") if e in dll.exports]
    print("  exports:", ", ".join(exports) or "(없음)")
    for rep in reports:
        status = "호환" if rep.compatible else "비호환"
        print(f"\n== 런타임 {rep.runtime.version} ({rep.runtime.edition}): {status}")
        for f in rep.findings:
            print("  ", f)


def _game_dir_findings(game_dir: Path, reports: list[RuntimeReport]) -> bool:
    ok = True
    for rep in reports:
        print(f"\n== 게임 폴더 검사 ({rep.runtime.version}): {game_dir}")
        for f in check_game_dir(game_dir, rep.runtime, rep.needs_address_library):
            print("  ", f)
            ok = ok and f.level != ERROR
    return ok


def cmd_check(args) -> int:
    dll, reports = check_dll(Path(args.dll), _runtimes(args.runtime))
    _print_reports(dll, reports)
    ok = all(r.compatible for r in reports)
    if args.game_dir:
        ok = _game_dir_findings(Path(args.game_dir), reports) and ok
    return 0 if ok else 1


def cmd_package(args) -> int:
    cfg = load_config(Path(args.project))
    runtimes = _runtimes(args.runtime, cfg.runtimes)
    dll = Path(args.dll) if args.dll else find_output(cfg)
    if dll is None or not dll.is_file():
        print("[오류] 패키징할 DLL 을 찾지 못했습니다. 먼저 `skbuild build` 를 실행하거나 --dll 을 지정하세요.")
        return 1
    parsed, reports = check_dll(dll, runtimes)
    _print_reports(parsed, reports)
    if not all(r.compatible for r in reports) and not args.force:
        print("\n[오류] 호환성 검사 실패 → 패키징 중단 (--force 로 무시)")
        return 1
    pdb = dll.with_suffix(".pdb")
    out = create_package(cfg, dll, Path(args.output), runtimes, pdb=pdb, fomod=args.fomod)
    print(f"\n패키지 생성: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="skbuild", description="SKSE / Address Library 모드 빌드업 툴")
    p.add_argument("--version", action="version", version=f"skbuild {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    rt_help = "대상 런타임 버전 (여러 번 지정 가능, 기본: runtimes.json 의 default)"

    s = sub.add_parser("runtimes", help="알려진 런타임 / Address Library 파일명 목록")
    s.set_defaults(func=cmd_runtimes)

    s = sub.add_parser("init", help="CommonLibSSE-NG 플러그인 프로젝트 생성")
    s.add_argument("name", help="플러그인 이름 (DLL 이름)")
    s.add_argument("--path", help="생성 위치 (기본: ./<name>)")
    s.add_argument("--author", default="")
    s.add_argument("--version", default="1.0.0")
    s.add_argument("--description", default="")
    s.add_argument("--runtime", action="append", help=rt_help)
    s.add_argument("--template", choices=list(TEMPLATES), default=DEFAULT_TEMPLATE,
                   help="commonlib: CommonLibSSE-NG+vcpkg (기본), minimal: 외부 라이브러리 없음")
    s.add_argument("--offline", action="store_true", help="vcpkg baseline 자동 조회 생략")
    s.add_argument("--force", action="store_true", help="비어 있지 않은 폴더에 덮어쓰기")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("build", help="CMake 프리셋으로 빌드")
    s.add_argument("--project", default=".", help="프로젝트 폴더")
    s.add_argument("--preset", help="CMake 프리셋 (기본: skbuild.toml 의 build.preset)")
    s.add_argument("--dry-run", action="store_true", help="실행할 명령만 출력")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("check", help="DLL 의 SKSE / Address Library 호환성 검사")
    s.add_argument("dll")
    s.add_argument("--runtime", action="append", help=rt_help)
    s.add_argument("--game-dir", help="스카이림 설치 폴더 (SKSE / Address Library 설치 확인)")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("package", help="호환성 검사 후 배포 zip 생성")
    s.add_argument("--project", default=".", help="프로젝트 폴더")
    s.add_argument("--dll", help="패키징할 DLL (기본: 빌드 폴더에서 자동 탐색)")
    s.add_argument("--runtime", action="append", help=rt_help)
    s.add_argument("-o", "--output", default="dist", help="출력 폴더")
    s.add_argument("--fomod", action="store_true", help="FOMOD 설치기 포함")
    s.add_argument("--force", action="store_true", help="호환성 검사 실패해도 패키징")
    s.set_defaults(func=cmd_package)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (BuildError, PEError, FileNotFoundError, FileExistsError, ValueError) as e:
        print(f"[오류] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
