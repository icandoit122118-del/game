# skse-buildkit (`skbuild`)

스카이림 **SKSE + Address Library** 기반 모드를 한 번에 **생성 → 빌드 → 호환성 검사 → 패키징** 하는 Python CLI 입니다.
기본 대상 런타임은 **Steam 최신 1.7.104** 이며, 런타임 목록은 `skbuild/data/runtimes.json` 에서 관리합니다.

## 설치

```bash
pip install -e .          # Python 3.11+
pip install -e .[test] && pytest
```

## 명령

| 명령 | 설명 |
| --- | --- |
| `skbuild runtimes` | 알려진 런타임과 Address Library 파일명 목록 |
| `skbuild init MyPlugin --author me [--template commonlib\|minimal] [--runtime 1.7.104 ...]` | C++ 플러그인 프로젝트 생성 |
| `skbuild build [--preset release] [--dry-run]` | CMake 프리셋으로 빌드 (Windows + MSVC + vcpkg) |
| `skbuild check Plugin.dll [--runtime ...] [--game-dir "C:/.../Skyrim Special Edition"]` | DLL 호환성 검사 + 게임 폴더 설치 상태 확인 |
| `skbuild package [--fomod] [-o dist] [--force]` | 호환성 검사 통과 시 배포 zip 생성 |

### `init` — 프로젝트 생성

템플릿을 `--template` 으로 고릅니다.

| 템플릿 | 의존성 | 용도 |
| --- | --- | --- |
| `commonlib` (기본) | CommonLibSSE-NG, spdlog, vcpkg | 게임 구조체/함수를 폭넓게 다루는 플러그인 |
| `minimal` | 없음 (CMake + MSVC 만) | 로그, 이벤트, 메모리 패치 등 가벼운 플러그인 |

#### `commonlib` 템플릿

생성 파일: `CMakeLists.txt`, `CMakePresets.json`, `vcpkg.json`, `vcpkg-configuration.json`,
`src/PCH.h`, `src/main.cpp`, `skbuild.toml`.

- `add_commonlibsse_plugin()` 이 `SKSEPlugin_Version` / `SKSEPlugin_Query` export 를 생성하므로 SE·AE 겸용 DLL 이 나옵니다.
- 주소는 `REL::RelocationID(SE_ID, AE_ID)` 로 Address Library ID 를 사용합니다 (`main.cpp` 예시 참고).
- vcpkg / colorglass 레지스트리 baseline 은 `git ls-remote` 로 자동 채웁니다. 오프라인이면(`--offline`)
  `REPLACE_WITH_COMMIT_SHA` 가 남고, `build` 가 이를 감지해 알려 줍니다.

#### `minimal` 템플릿

생성 파일: `CMakeLists.txt`, `CMakePresets.json`, `src/SKSE.h`, `src/AddressLibrary.h`, `src/main.cpp`, `skbuild.toml`.

- `src/SKSE.h`: SKSE64 플러그인 ABI(`SKSEPluginVersionData`, `SKSEInterface`, 메시징 인터페이스)를 직접 정의.
  구조체 크기/오프셋은 `static_assert` 로 고정되어 있습니다.
- `src/AddressLibrary.h`: Address Library `.bin` (SE format 1 / AE format 2) 로더. 표준 라이브러리만 사용합니다.
- `src/main.cpp`: `SKSEPlugin_Version`·`SKSEPlugin_Query`·`SKSEPlugin_Load` 를 export 하고, 런타임 버전에 맞는
  Address Library 를 읽어 `Resolve(id)` 로 실제 주소를 얻습니다. 로그는
  `문서/My Games/Skyrim Special Edition/SKSE/<이름>.log`.
- 버전 플래그는 `AddressLibraryPostAE` + `NoStructUse` 입니다. 게임 구조체를 직접 다루기 시작하면
  `NoStructUse` 대신 `StructsPost629` 를 쓰세요 (`skbuild check` 가 이 조합을 검사합니다).
- vcpkg 가 필요 없으므로 `VCPKG_ROOT` 없이 `skbuild build` 가 가능합니다.

### `build` — 빌드

필요 환경: Windows, Visual Studio 2022(C++) 또는 Build Tools, CMake 3.24+, Ninja. `commonlib` 템플릿은 `VCPKG_ROOT` 환경 변수도 필요합니다.
Developer PowerShell 에서 실행하세요. `--dry-run` 으로 실행될 명령만 확인할 수 있습니다.

### `check` — 호환성 검사

순수 Python PE 파서로 DLL 의 export 와 `SKSEPluginVersionData` 를 읽어 런타임별로 판정합니다.

- 64비트 DLL 인지, `SKSEPlugin_Load` 가 있는지
- AE(1.6+/1.7) 런타임: `SKSEPlugin_Version` 필수. `compatibleVersions` 에 명시되었거나
  Address Library / 시그니처 버전 독립 플래그가 있어야 함
- 1.6.629 이후 런타임: `StructsPost629` 또는 `NoStructUse` 플래그 필요 (없으면 SKSE 가 로드 거부)
- SE(1.5.97) 런타임: `SKSEPlugin_Query` 필수
- `--game-dir`: `SkyrimSE.exe` 버전, `skse64_loader.exe`, `Data/SKSE/Plugins/<Address Library bin>` 존재 확인

비호환이면 종료 코드 1 을 반환하므로 CI 에서 그대로 사용할 수 있습니다.

### `package` — 패키징

빌드 폴더에서 `<이름>.dll` 을 찾아 `check` 를 거친 뒤 `dist/<이름>-<버전>.zip` 을 만듭니다.

- 일반 zip: 루트가 Data 폴더 (`SKSE/Plugins/<이름>.dll`)
- `--fomod`: `Data/...` + `fomod/info.xml`, `fomod/ModuleConfig.xml`
- `skbuild.toml` 의 `[package.files]` 로 ESP, INI, 스크립트 등을 추가하고 `include_pdb = true` 로 PDB 포함

## skbuild.toml

```toml
[project]
name = "MyPlugin"
version = "1.0.0"
author = "me"
runtimes = ["1.7.104"]

[build]
preset = "release"
dir = "build"

[package]
include_pdb = false

[package.files]
"data/MyPlugin.esp" = "MyPlugin.esp"
"config/MyPlugin.ini" = "SKSE/Plugins/MyPlugin.ini"
```

## Claude Code 로 작업하기

저장소의 `CLAUDE.md` 에 구조와 규칙이 정리되어 있고, 웹 세션 시작 훅(`.claude/hooks/session-start.sh`)이
`pip install -e .[test]` 를 자동 실행하므로 바로 요청하면 됩니다. 예:

- "런타임 1.7.120 추가해줘" → `runtimes.json` 수정 + 테스트
- "`skbuild check` 에 SKSE 최소 버전 검사 옵션 추가해줘"
- "minimal 템플릿에 Papyrus 네이티브 함수 등록 예시 넣어줘"
- "이 DLL 호환성 검사해줘" (DLL 파일을 저장소에 올린 뒤)

Claude 는 변경 후 `pytest` 로 검증하고 PR 로 올립니다. 실제 C++ 빌드는 Windows PC 에서 `skbuild build` 로 확인하세요.

## 런타임 추가 / 갱신

새 게임 패치가 나오면 `skbuild/data/runtimes.json` 에 항목을 추가하고 `default` 를 바꾸면 됩니다.
목록에 없는 버전도 `--runtime 1.7.200` 처럼 지정하면 Address Library 파일명을 규칙대로
(`versionlib-1-7-200-0.bin`, SE 는 `version-…bin`) 추정합니다.

> 참고: 1.7.104 용 Address Library 파일명은 AE 규칙(`versionlib-1-7-104-0.bin`)을 가정했습니다.
> 또한 1.7.x 대응은 사용하는 CommonLibSSE-NG 버전이 해당 런타임을 지원해야 합니다.
