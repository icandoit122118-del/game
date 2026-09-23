# 스카이림 모딩 툴을 만들며 배우는 프로그래밍 기초

프로그래밍을 처음 배우는 사람이 **파이썬으로 스카이림 로드 오더 검사기**를 직접 만들면서
변수부터 바이너리 파일 읽기까지 배우는 강의입니다.

완성품(`../skyrim_tool/load_order_checker.py`)은 이런 문제를 찾아 줍니다:

- 필요한 **마스터 파일이 없는** 모드 → 게임 시작하자마자 튕기는(CTD) 가장 흔한 원인
- **마스터보다 먼저 로드되는** 모드 (패치가 원본보다 위에 있는 경우 등)
- plugins.txt 에서 켜져 있지만 **Data 폴더에 없는** 파일
- 일반 플러그인 **254개 제한** 초과

```
=== 로드 오더 ===
  [    00] Skyrim.esm
  ...
  [FE:000] TinyTweaks.esl
  [    06] CoolArmor_Patch.esp
  [    07] CoolArmor.esp

[오류] CoolArmor_Patch.esp: 마스터 'CoolArmor.esp' 보다 먼저 로드됩니다 (순서를 뒤로 옮기세요)
[오류] OldBrokenMod.esp: 필요한 마스터 'Missing.esm' 가 없거나 비활성화돼 있습니다
```

## 준비하기

1. [python.org](https://www.python.org/downloads/)에서 Python 3 설치 (Windows 설치 시 "Add python.exe to PATH" 체크)
2. 터미널에서 확인: `python3 --version` (Windows는 `python --version`)
3. 이 저장소 폴더에서 명령을 실행합니다. 연습용 가짜 모드 파일은 `sample_data/` 에 이미 들어 있어요.
   (다시 만들려면 `python3 tools/make_sample_data.py`)

## 강의 순서

| 강 | 파일 | 배우는 내용 | 툴에서 쓰이는 곳 |
|---|---|---|---|
| 0 | `00_basics.md` | **처음이라면 여기부터!** 프로그래밍 용어와 기초 이론 | 모든 강의 |
| 1 | `01_mod_info.py` | 변수, print, f-string, 계산 | 결과 출력, 16진수 로드 번호 |
| 2 | `02_input_and_strings.py` | input, 문자열 메서드, 슬라이싱 | 확장자 판별, `*` 활성화 표시 |
| 3 | `03_conditions.py` | if / elif / else, and / or / not | .esm/.esp/.esl 판별, 개수 제한 |
| 4 | `04_lists_and_loops.py` | 리스트, for, enumerate, while | 로드 오더 목록 |
| 5 | `05_functions.py` | def, 매개변수, return | 기능을 함수로 나누기 |
| 6 | `06_read_plugins_txt.py` | 파일 읽기/쓰기, pathlib | plugins.txt 읽기 |
| 7 | `07_dict_masters.py` | 딕셔너리, 중첩 반복 | 마스터 누락/순서 검사 |
| 8 | `08_read_esp_header.py` | 바이너리 파일, struct, 비트 플래그 | .esp 헤더에서 마스터 목록 읽기 |
| 🏁 | `../skyrim_tool/load_order_checker.py` | 전부 합치기 | 완성된 검사기 |

실행 예: `python3 lessons/01_mod_info.py`

각 파일은 주석을 읽으며 따라가고, 숫자·이름을 바꿔 실험해 본 뒤, 맨 아래 **✏️ 연습문제**를 풀어 보세요.

## 내 게임에 사용하기

```
python3 skyrim_tool/load_order_checker.py "<plugins.txt 경로>" "<Data 폴더 경로>"
```

- plugins.txt: `C:\Users\<사용자>\AppData\Local\Skyrim Special Edition\plugins.txt`
  (MO2 사용 시 `MO2\profiles\<프로필>\plugins.txt`)
- Data 폴더: `...\steamapps\common\Skyrim Special Edition\Data`
  (MO2 사용 시 모드 파일이 `mods\` 폴더에 흩어져 있으므로 MO2 안에서 실행하는 것이 정확합니다)

이 도구는 파일을 **읽기만** 하고 게임 파일은 절대 수정하지 않습니다.

> 💡 참고: 게임 안에서 동작하는 모드 스크립트는 Papyrus 언어로 만들지만,
> xEdit, 모드 매니저, LOOT 같은 **모딩 툴**은 이 강의처럼 일반 프로그래밍 언어로 만듭니다.
