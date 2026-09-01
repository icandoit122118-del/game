# VFX Testbed

VFX를 판단하기 위한 중립 무대를 씬에 생성합니다. 외부 에셋을 받지 않으며,
바닥 텍스처·머티리얼·블룸 프로파일까지 전부 에디터에서 생성합니다.

## 사용법

1. Unity 메뉴 → **`Tools > VFX Testbed > Build Test Stage`**
2. 만들 효과(VFX Graph 또는 Particle System)를 `VFX Testbed/Effect Anchor` 아래에 넣습니다
3. 플레이 모드 진입

## 단축키

| 키 | 동작 |
|---|---|
| `1` | 배경값 순환 — 중간 회색 → 검정 → 흰색 → 황혼 |
| `2` | 라이팅 순환 — 스튜디오 → 암실 → 야간+안개 → 주광 |
| `B` | 블룸(포스트 프로세싱) on/off |
| `T` | 타임스케일 순환 — 1x → 0.5x → 0.25x → 0.1x |
| `Space` | 일시정지 |
| `R` | 효과 재생 (리스타트) |
| `G` | 격자 바닥 on/off |
| `C` | 스케일 기준물 on/off |
| `H` | HUD on/off |
| `P` | 스크린샷 저장 |
| 우클릭 드래그 | 궤도 회전 |
| 휠 클릭 드래그 | 팬 |
| 휠 | 줌 |
| `F` | 카메라 피벗 초기화 |

## 구성

| 오브젝트 | 역할 |
|---|---|
| `Grid Floor` | 1m 격자. 텍스처 1타일 = 1m, 세부선 = 0.25m |
| `Scale References` | 1m 큐브 / 1.8m 인체 / 0.5m 구 |
| `Key Light` | 라이팅 프리셋이 색·강도·각도를 덮어씁니다 |
| `Stage Camera` | HDR 활성 턴테이블 카메라 |
| `Post Processing Volume` | 블룸 볼륨 (SRP 프로젝트에서만 생성) |
| `Effect Anchor` | 여기에 효과를 넣으면 `R`로 재시작됩니다 |

## 파이프라인 호환

| 파이프라인 | 상태 |
|---|---|
| **URP** | 전 기능 동작 (권장) |
| **HDRP** | 전 기능 동작 |
| **Built-in** | 무대·카메라·라이팅은 동작. 블룸 볼륨은 생성되지 않으므로 직접 포스트 스택을 넣고 컨트롤러의 `Post Processing Volume` 필드에 연결하세요 |

런타임 스크립트는 코어 엔진 타입만 사용하므로 세 파이프라인 모두에서 컴파일됩니다.

## 요구 사항

- **Color Space = Linear** (`Project Settings > Player > Other Settings`).
  Gamma면 HDR·블룸이 어긋나며, 스테이지 빌드 시 경고가 뜹니다.
- 입력은 레거시 Input Manager를 사용합니다. 새 Input System 전용 프로젝트라면
  `Project Settings > Player > Active Input Handling` 을 **Both** 로 두세요.
  (`Input System (New)` 단독일 경우 단축키만 비활성화되고 씬은 정상 동작합니다.)

## 라이선스 안내

이 폴더의 스크립트와 생성물에는 서드파티 에셋이 포함되어 있지 않으므로 저장소에 커밋해도 안전합니다.
Unity Asset Store · Synty · Fab 등에서 구매한 에셋은 재배포가 금지되어 있으니
`Assets/ThirdParty/` 아래에 두고 커밋하지 마세요 (`.gitignore`에 반영되어 있습니다).
