# Grid Inventory × CC Adventurer Backpack — 소지 칸만 보이게

날짜: 2026-09-10 · Plan 빌드 0.47.0

## 한 줄

메인 격자는 `!pocket`만큼만 보이고, CC 배낭(`ccfsvsse001-backpacks.esl`)이 티어별 가방 칸을 준다. HDT-SMP Creation Backpacks(Nexus 154157)는 메시만.

## 동작

| 상태 | 메인 보드 | 수납 |
|---|---|---|
| 배낭 없음 | `!pocket = 2` → 10×2 = 20칸 | 짐 거의 못 듦 |
| T1 가죽/고급/검정/털 (±침낭) | 동일 + CW 보너스 칸 | 가방 5×6 (침낭 5×7) |
| T2 모험가/마법/사냥/도둑 (±침낭) | 동일 + CW 보너스 칸 | 가방 6×9 (침낭 6×10) |

배낭은 착용해도 타일이 남고(Grid Inventory worn-bag), 우클릭으로 연다.

## Plan 모드

- `Plan Grid Backpack Capacity` (Grid Inventory **위**)
  - `SKSE/Plugins/GridInventory.dll` — `!pocket` + `GridInventory_items_*.ini` 오버레이 로드
  - `SKSE/Plugins/GridInventory_items_cc_backpacks.ini` — CC 16종 `bag:1`
- `Plan 00 Settings` `GridInventory_ui.ini` — `!pocket = 2`

## 아직 디스크에 없는 것

- `ccfsvsse001-backpacks.esl` (AE / Creation Club Adventurer's Backpack)
- HDT-SMP Creation Backpacks v1.0a (Nexus 154157, 매니저 전용) — FSMP 필요

없으면 INI 줄은 스킵되고, 포켓 축소만 적용된다.

## 소스

`D:\MO2-Skyrim\_unpack\build\grid-inventory\`

- `Grid.cpp` / `Grid.h` — `g_pocketRows`, 소유·표시·용량
- `WinManager.cpp` — `!pocket`
- `main.cpp` — `GridInventory_items_*.ini` 병합
