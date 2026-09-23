# wingui — Claude Code / Codex가 Windows GUI를 "눈 없이" 다루게 하는 도구

스크린샷을 보고 좌표를 클릭하는 방식도 아니고, 미리 짜 둔 매크로(오토메이션 스크립트)도 아닙니다.
Windows **UI Automation(UIA)** — 스크린리더가 쓰는 접근성 트리 — 를 **MCP 서버**와 CLI로 열어서,
에이전트가 창 구조를 텍스트로 읽고 버튼·입력칸·메뉴를 **의미 단위로 직접 조작**하게 합니다.

```
에이전트                          wingui (MCP)                     Windows 앱
 snapshot("메모장")   ──────▶  UIA 트리 순회            ──────▶  COM / UIA Provider
                     ◀──────  - Edit "텍스트 편집기" [e5] value="" {value}
                              - MenuItem "파일" [e3] {expand}
 set_value("e5","안녕") ─────▶  ValuePattern.SetValue    (마우스·키보드 이벤트 없음)
 menu("w1","파일 > 저장") ───▶  ExpandCollapse → Invoke
```

| 방식 | 입력 | 단점 |
| --- | --- | --- |
| 화면 보고 클릭 (computer use) | 스크린샷 + 좌표 | 느림, 해상도/DPI/테마에 깨짐, 토큰 많이 씀 |
| 매크로/오토메이션 스크립트 | 사람이 미리 작성 | 매번 새로 짜야 함, 에이전트가 판단 못 함 |
| **wingui (UIA 트리)** | 요소 이름·ID·패턴 | 접근성 정보를 안 내는 앱(게임, 캔버스)은 한계 |

## 설치 (Windows)

Windows 쪽 Python 3.10+ 이 필요합니다.

```powershell
git clone <this repo> game; cd game/wingui
pip install -e .
wingui windows        # 창 목록이 나오면 OK
```

## 에이전트에 연결

**Claude Code**

```powershell
claude mcp add wingui -- wingui-mcp
# 또는 wingui/.mcp.json 을 사용할 프로젝트 루트에 복사
```

**Codex CLI** — `%USERPROFILE%\.codex\config.toml` 에 추가 ([examples/codex-config.toml](examples/codex-config.toml)):

```toml
[mcp_servers.wingui]
command = "wingui-mcp"
args = []
tool_timeout_sec = 120
```

**WSL에서 에이전트를 돌리는 경우**: UIA는 Windows 프로세스에서만 동작하므로 서버는 Windows Python으로 띄웁니다.
stdio는 WSL interop으로 그대로 연결됩니다.

```bash
claude mcp add wingui -- cmd.exe /c py -m wingui
```

MCP를 못 쓰는 환경이면 셸에서 `wingui` CLI를 직접 호출해도 됩니다 ([AGENTS.md](AGENTS.md) 참고).
`AGENTS.md`(Codex)와 `CLAUDE.md`(Claude Code)에 에이전트용 사용 규칙이 들어 있습니다. 에이전트가 이 규칙을 따르게 하려면 작업할 프로젝트에 복사해 두세요.

## MCP 도구

| 도구 | 하는 일 | 사용하는 UIA 패턴 |
| --- | --- | --- |
| `list_windows` | 최상위 창 목록 (ref, 제목, pid, hwnd) | — |
| `launch` | 프로그램 실행 후 새 창 ref 반환 | — |
| `snapshot` | 창/요소의 접근성 트리를 텍스트로 | 전부 (상태 표시) |
| `find` | 이름·AutomationId·타입으로 검색 | — |
| `invoke` | 버튼 누르기 / 체크 / 선택 / 펼치기 | Invoke → Toggle → SelectionItem → ExpandCollapse → LegacyIAccessible |
| `set_value` | 입력칸 텍스트, 슬라이더 값 설정 | Value, RangeValue |
| `select` | 콤보박스·리스트·탭에서 항목 선택 | ExpandCollapse + SelectionItem |
| `toggle`, `expand` | 체크 상태 지정, 트리/콤보 펼치기 | Toggle, ExpandCollapse |
| `menu` | `"파일 > 다른 이름으로 저장"` 경로 실행 | ExpandCollapse, Invoke |
| `get_text` | 문서/입력칸/라벨 텍스트 읽기 | Text, Value, LegacyIAccessible |
| `wait_for` | 창·요소가 나타나거나 사라질 때까지 대기 | — |
| `focus`, `close_window` | 창 활성화, 닫기 요청 | Window |
| `type_text`, `send_keys` | Value 패턴이 없을 때의 키보드 폴백 | (유니코드 키 입력) |

`snapshot` 한 줄 형식: `Type "Name" [ref] #AutomationId 상태 {가능한 동작}`

```
- Window "제목 없음 - 메모장" [w1]
  - MenuBar "애플리케이션" [e2]
    - MenuItem "파일" [e3] collapsed {expand}
  - Document "텍스트 편집기" [e5] #15 value="" {value,text}
  - Button "닫기" [e9] {invoke}
```

- 이름 없고 동작도 없는 레이아웃용 컨테이너는 기본으로 숨깁니다 (`compact=false`로 전부 표시).
- ref는 요소가 살아 있는 동안 유지됩니다(RuntimeId 기준). 사라진 요소를 쓰면 "새 snapshot을 찍으라"는 오류가 납니다.
- 마우스 이동·좌표 클릭 기능은 의도적으로 넣지 않았습니다.

## 한계

- 접근성 정보를 노출하지 않는 UI(DirectX/OpenGL 게임 화면, 캔버스, 일부 Java/Qt/Electron 앱)는 트리가 거의 비어 있습니다.
  이 경우 `send_keys`(단축키) 정도만 가능합니다. Electron/Chromium 앱은 `--force-renderer-accessibility`로 실행하면 트리가 채워집니다.
- 관리자 권한으로 실행된 앱은 wingui도 관리자 권한으로 띄워야 조작할 수 있습니다(UIPI).
- 잠긴 화면/로그오프 세션에서는 동작하지 않습니다.

## 개발

```bash
pip install -e .[dev]
pytest   # 가짜 UIA 트리로 테스트 → Linux/macOS에서도 실행됨
```

구조: `src/wingui/core.py`(UIA 로직, `Session`), `server.py`(MCP), `cli.py`(CLI).
UIA COM 객체는 스레드(아파트먼트)에 묶이므로 서버는 모든 호출을 단일 워커 스레드에서 실행합니다.
