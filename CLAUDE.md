# skbuild — Claude 작업 안내

스카이림 SKSE / Address Library 모드용 빌드업 툴(Python CLI `skbuild`). 사용자에게는 **한국어**로 답한다.

## 구조
- `skbuild/cli.py` — argparse 서브커맨드 `init / build / check / package / runtimes`
- `skbuild/scaffold.py` — 템플릿 렌더링. `TEMPLATES` 에 템플릿별 파일 목록, `COMMON_FILES` 는 공통
- `skbuild/templates/{common,commonlib,minimal}/` — 프로젝트 템플릿. 치환자는 `@@NAME@@`, `@@VERSION@@`,
  `@@AUTHOR@@`, `@@DESCRIPTION@@`, `@@RUNTIMES@@`, `@@SLUG@@` (CMake 의 `${}` 와 겹치지 않게 `@@` 사용)
- `skbuild/builder.py` — `cmake --preset` 래퍼 + 환경 사전 점검
- `skbuild/pe.py` — 표준 라이브러리 PE 파서, `SKSEPluginVersionData`(848바이트) 판독
- `skbuild/checker.py` — 런타임별 호환성 판정, 게임 폴더 검사
- `skbuild/packager.py` — Data 레이아웃 zip / FOMOD
- `skbuild/runtimes.py` + `skbuild/data/runtimes.json` — 런타임 목록 (기본 1.7.104)

## 규칙
- 런타임 추가/변경은 `skbuild/data/runtimes.json` 만 수정한다. 코드에 버전을 하드코딩하지 않는다.
- 새 템플릿 파일은 템플릿 폴더에 추가하고 `scaffold.py` 의 `TEMPLATES` 에 등록한다.
  폴더 깊이가 바뀌면 `pyproject.toml` 의 `package-data` 도 확인한다.
- 런타임 의존성은 추가하지 않는다 (표준 라이브러리만, Python 3.11+).
- 메시지·주석은 한국어, 기존 코드 스타일을 따른다.

## 검증
- `pytest` — 전체 테스트. `tests/pe_factory.py` 가 합성 DLL 을, `tests/addrlib_factory.py` 가 Address Library `.bin` 을 만든다.
  minimal 템플릿의 C++ 로더 테스트는 g++ 로 실제 컴파일한다. MinGW(`apt-get install mingw-w64`)가 있으면
  minimal 템플릿을 실제 Windows x64 DLL 로 교차 빌드해 `skbuild check` 판정까지 확인한다 (없으면 skip).
  템플릿의 Windows 헤더 include 는 소문자로 쓴다 (MinGW 는 대소문자 구분).
- 실제 SKSE 플러그인 빌드는 Windows + MSVC 에서만 가능하다. 이 환경에서는 `skbuild build --dry-run` 과
  생성 파일 검증까지만 하고, 그 사실을 사용자에게 알린다.
