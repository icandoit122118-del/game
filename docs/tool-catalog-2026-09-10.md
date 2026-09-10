# 오늘 만든 도구 카탈로그 — 2026-09-10

한 줄만 보면 된다. **용도** = 이게 뭐고, **언제** = 이 순간에 부른다.

경로 기준: `D:\MO2-Skyrim\_tools\` · 프로필은 **Plan만** · Default 금지.

---

## 지금 뭐부터?

| 상황 | 부를 것 |
|---|---|
| 파이프가 살아 있나 | `pipeline_doctor` |
| 툴체인(게임·SKSE·AL·MSVC) 재기 | `latest_build_doctor` |
| 모드 폴더 새로 풀었음 | `plan_detect` → `mcm_harvest` |
| 버전 안 맞다 / DLL 의심 | `plan_runtime_gate` → `latest_build_rebuild_check` |
| 어디에 넣을지 | `plan_mod_classify` → `plan_mod_place` |
| 겹침·누가 이기나 | `plan_mod_conflicts` / `plan_record_audit` / `plan_abc_form` |
| 한글패치 | `plan_kr_gate` |
| 튕김 | `plan_crash_pack` 또는 `plan_feedback_loop` |
| 이 모드가 뭐더라 | `plan_mod_purpose` + 스킬 `skyrim-applied-mods` |
| 장부 쓰기 | 스킬 `skyrim-jeongbon` |

---

## 1. 에이전트 스킬 (Cursor)

에이전트가 **언제 그 규칙을 켜는지** 정한 카드다. CLI가 아니다.

### `skyrim-latest-build`
- **용도:** SE 1.7.104용 SKSE/Papyrus/ESP 빌드 파이프라인 안내
- **언제:** 재빌드, CommonLib, papyrus-compiler, 「최신빌드」 말할 때
- **한 방:** `latest_build.py doctor` → `catalog` → `rebuild-check`

### `skyrim-ai-pipeline`
- **용도:** SkyLink · MCM Recorder · houseCARL · Forge 를 한 줄로 묶는 순서표
- **언제:** 파이프라인, 런타임 MCP, MCM, SkyLink 말할 때
- **한 방:** `pipeline.py doctor` 후 `plan_feedback_loop`

### `skyrim-runtime-compat`
- **용도:** 버전 안 맞는다고 **버리지 말고** 재빌드 가능부터 판정
- **언제:** 1.6.1170 / format 5 / DLL / 「버전 안맞」 나올 때
- **한 방:** `plan_runtime.py` → `rebuild-check` → 정본에 가능/불가만 적기

### `skyrim-mod-arrange`
- **용도:** 왼쪽(파일·위 승) / 오른쪽(레코드·아래 승) 배열 규칙
- **언제:** 모드배열, 로드오더, 칸, separator, LOOT 유혹 올 때
- **한 방:** 줄 **한 줄만** 끼우기. 전체 재작성·LOOT Apply 금지

### `skyrim-jeongbon`
- **용도:** 정본 빌드 장부 (추가·뺀·적용 + 버전 자리)
- **언제:** Plan에 뭐든 바꾸거나 「정본」「완성됐다」 말할 때
- **한 방:** 답만 하고 장부 안 고치면 실패

### `skyrim-applied-mods`
- **용도:** 적용 모드마다 용도·언제·사용법·헷갈림 카드
- **언제:** 켜기·끄기·재빌드·「어떤모드」「용도」 말할 때
- **한 방:** `applied.md` 칸을 **전부** 채운다

### 규칙 `explain-found-mods`
- **용도:** 찾은/나열한 모드를 이름만 찍지 말고 설명
- **언제:** Nexus 검색·추천·비교·켜기끄기마다 (항상)
- **한 방:** 용도 / 언제 / 사용법 / 헷갈림 / 이 스택

---

## 2. MCP · CLI — 진단

### `pipeline_doctor`
- **용도:** SkyLink DLL · MCM Recorder · houseCARL · Forge 트리 생존 확인
- **언제:** 세션 시작, 「파이프 안 됨」 직전
- **CLI:** `python -X utf8 D:\MO2-Skyrim\_tools\ai-pipeline\pipeline.py doctor`

### `latest_build_doctor`
- **용도:** 게임 1.7.104 · SKSE · AL · CommonLib · MSVC · Papyrus 컴파일러를 디스크에서 측정
- **언제:** 빌드/재빌드 들어가기 전
- **CLI:** `python -X utf8 D:\MO2-Skyrim\_tools\latest-build\latest_build.py doctor`

### `latest_build_catalog`
- **용도:** 오픈소스 판정표 USE / TEMPLATE / STALE / SKIP / GUI
- **언제:** 「이 레포 써도 돼?」 물을 때 (`--refresh` = GitHub만)
- **CLI:** `... latest_build.py catalog`

### `latest_build_rebuild_check`
- **용도:** Plan `+` SKSE DLL을 AL 지문(NEW/OLD/…) + 공개 소스로 분류
- **언제:** 버전 안 맞는 DLL, 재빌드 후보 고를 때 — **삭제·재빌드 안 함**
- **CLI:** `... latest_build.py rebuild-check [--mod NAME]`

### `skylink_status`
- **용도:** SkyrimMCP named pipe 있는지 확인
- **언제:** 게임 SKSE로 띄운 뒤 런타임 MCP 붙이기 전 — 치트 명령 안 보냄

---

## 3. MCP · CLI — 모드 넣기 / MCM

### `plan_detect`
- **용도:** `mods\` 폴더 vs Plan 목록 대조. 빠진 줄만 후보
- **언제:** zip 풀고 폴더가 생겼을 때
- **주의:** `apply=true` 는 MO2 종료 + Plan만. 전체 재작성·LOOT 없음

### `mcm_harvest`
- **용도:** 디스크 INI 슬라이더/토글을 MCM Recorder JSON으로. 인게임 MCM Config는 `_ingame_removed`로 이동
- **언제:** 모드를 Plan에 **넣을 때** (`detect --apply` 직후)
- **주의:** 숫자 날조 금지. autorun 끔. SkyUI/MCM Helper/Plan 00 안 건드림

### `mcm_list`
- **용도:** 수확된 Recorder JSON 목록
- **언제:** 「뭐가 harvest 됐지?」

### `mcm_rewrite`
- **용도:** 인게임 Recorder 적용은 **거부**한다고 알려 줌
- **언제:** rewrite/재생 유혹이 올 때 — 값은 디스크 harvest만

---

## 4. MCP · CLI — 버전 게이트 / 한글 / 조합

### `plan_runtime_gate`
- **용도:** 이 PC Skyrim↔SKSE↔AL 짝 + 그 모드 DLL 지문 → 배열 가능/보류
- **언제:** 설치 **확정** 직후 (`confirmed_by` 필요). 폴더 삭제·재빌드·줄 이동 없음
- **CLI:** `python -X utf8 D:\MO2-Skyrim\_tools\plan-compat\plan_runtime.py "모드" --confirmed-by 고래`

### `plan_kr_gate`
- **용도:** Nexus 한글패치 검색·다운로드. 없으면 Tullius XML+Gemini → `SST KR - 본체`
- **언제:** 조합 산출물 **직전**. `combo_final`은 이거 끝나야 나옴
- **CLI:** `python -X utf8 D:\MO2-Skyrim\_tools\plan-compat\plan_kr.py "모드"`

### `plan_combo`
- **용도:** Nexus 제작자 요구·버그 확인 → 한글 게이트 → Plan `+` 조합안
- **언제:** 여러 모드를 같이 넣을지 짜는 단계 — 줄 이동·ESP 안 함

### `plan_abc_form`
- **용도:** 겹치는 모드 A/B/C 질문표 (제작자 페이지 1순위)
- **언제:** 승자를 사용자에게 물을 때 — 확정·ESP 안 함

### `plan_evidence` / `plan_evidence_sources`
- **용도:** 근거 수집 / 붙인 사이트 카탈로그
- **언제:** 「왜 이렇게 배열?」 증거 필요할 때. 빈 소스 = 확인 불가. LOOT hit ≠ apply

---

## 5. MCP · CLI — 배열 (왼쪽 파일 / 오른쪽 레코드)

### `plan_mod_slots`
- **용도:** 왼쪽 `_separator` 칸 목록 + `+` 개수
- **언제:** 「어느 칸에 넣지?」 지도 볼 때

### `plan_mod_find`
- **용도:** 모드 이름 → 왼쪽 줄 + 오른쪽 플러그인 줄
- **언제:** 「지금 목록에 있나?」

### `plan_mod_classify`
- **용도:** 왼쪽 칸 + 오른쪽 kb 층 제안
- **언제:** 새 모드 자리 고를 때 — 줄은 안 옮김

### `plan_mod_purpose`
- **용도:** 한 모드 용도 카드 (이기면 / 아닌 것)
- **언제:** 이름만 보고 헷갈릴 때

### `plan_mod_conflicts`
- **용도:** 왼쪽 루즈파일 겹침 (위가 이김). BSA 내부는 안 Sweep
- **언제:** 메시/텍스처가 누가 이기는지

### `plan_mod_place`
- **용도:** 왼쪽 **한 줄** 끼우기/이동 (`above`/`below`/`slot`)
- **언제:** 자리 확정 후. 기본 dry-run. `apply` = MO2 끔 + Plan

### `plan_plugin_place`
- **용도:** 오른쪽 **한 줄** 이동 (아래가 레코드 승)
- **언제:** 패치를 대상 아래로 둘 때. 마스터 역순 거부

### `plan_lo_audit` / `plan_lo_apply`
- **용도:** Missing Master + 오른쪽 제안 / 제안을 라이브에 복사
- **언제:** 감사는 자주, apply는 `confirm_apply` + MO2 끔일 때만

### `plan_record_audit`
- **용도:** FormID 충돌 분류. NPC 얼굴 vs AI → A/B/C 후보
- **언제:** ESP 겹침 의심. ESP는 안 씀

### `plan_synthesis_propose`
- **용도:** 확정 forwards → Synthesis 스텁 + houseCARL 레시피
- **언제:** `confirmed_by` 있는 decisions만. CELL/WRLD/LAND/NAVM/REFR 거부

---

## 6. MCP · CLI — 감시 / 크래시

### `plan_watch`
- **용도:** modlist/plugins 해시·켜짐 스냅샷 델타
- **언제:** 모드 토글한 **뒤** 다시 부름 (데몬 아님)

### `plan_crash_pack`
- **용도:** 최신 Crash Logger 로그 → Plan 플러그인/SKSE에 매핑
- **언제:** CTD 직후. 자동 재배열·삭제·LOOT 없음

### `plan_feedback_loop`
- **용도:** watch + detect + 최신 CTD 매핑을 **한 번에**
- **언제:** 설치 후, 튕긴 후, 「지금 상태 한 장」 원할 때

### `plan_mod_classify` (루프 옵션)
- `plan_feedback_loop(classify_mod=...)` 로 감지가 끝난 모드에 칸 제안까지

---

## 7. houseCARL (데이터 층 · Nexus)

원본 ESP 안 건드림. 쓰기는 **새 플러그인**. Nexus는 API 키 없음.

| 도구 | 용도 | 언제 |
|---|---|---|
| `housecarl_nexus_search` | 이름으로 Nexus 검색 | 모드 찾을 때 (브라우저 대신) |
| `housecarl_nexus_mod` | id/URL → 설명·요구·파일목록·changelog | 한 모드 자세히 |
| `housecarl_update_status` | MO2 로컬 캐시로 업데이트 후보 + `id#fileid` | 네트워크 없이 먼저 좁힐 때 |
| `housecarl_nexus_check_updates` | 파일 단위 최신 여부 | `id#fileid` 토큰으로 확정 |
| `housecarl_nexus_identify` | MD5 → 어느 모드/파일 | 출처 모를 파일 |
| `housecarl_load_order_status` | 켜진/꺼진 모드·플러그인 요약 | 「지금 로드오더 뭐 보임?」 |
| `housecarl_asset_status` | Data 경로 승자 파일 | 「이 nif 누가 이김?」 |
| `housecarl_read_record` / `diff` / `forward` | 레코드 읽기·차이·포워드 | 패치 ESP 설계 |
| `housecarl_compile_script` / `decompile_script` | Papyrus | PEX↔PSC |

---

## 8. 폴더 지도

| 폴더 | 한 줄 |
|---|---|
| `_tools\latest-build\` | 1.7.104 빌드·카탈로그·재빌드 분류 |
| `_tools\plan-compat\` | 배열·충돌·런타임·한글·크래시·조합 MCP |
| `_tools\ai-pipeline\` | doctor · detect · MCM harvest · SkyLink 상태 |
| `_tools\houseCARL\` | Mutagen 데이터 층 + Nexus |
| `_tools\loadorder\` | `sortmods.py` / `sortlo.py` (드라이런 기본) |

산출물(빌드 DLL/PEX): `바탕화면\스카이림_빌드산출물` — `mods\`에 자동 복사 없음.

---

## 절대 안 하는 것 (공통)

- Default 프로필 쓰기
- LOOT로 목록 **전체** 덮기
- 버전 안 맞는다고 DLL 폴더 삭제
- 지시 없이 `--apply` / ESP / CELL·WRLD·LAND·NAVM·REFR 스매시
- 인게임 MCM Recorder 재생·SkyLink 치트 중계
- SST KR 폴더 삭제

---

## 빠른 CLI 복붙

```
python -X utf8 D:\MO2-Skyrim\_tools\ai-pipeline\pipeline.py doctor
python -X utf8 D:\MO2-Skyrim\_tools\latest-build\latest_build.py doctor
python -X utf8 D:\MO2-Skyrim\_tools\latest-build\latest_build.py catalog
python -X utf8 D:\MO2-Skyrim\_tools\latest-build\latest_build.py rebuild-check
python -X utf8 D:\MO2-Skyrim\_tools\plan-compat\plan_loop.py
python -X utf8 D:\MO2-Skyrim\_tools\plan-compat\plan_runtime.py "모드이름" --confirmed-by 고래
python -X utf8 D:\MO2-Skyrim\_tools\plan-compat\plan_kr.py "모드이름"
```
