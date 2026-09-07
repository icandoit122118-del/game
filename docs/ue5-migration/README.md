# Unreal Engine 2.5 → Unreal Engine 5 이식 가이드

이 문서 묶음은 Unreal Engine 2.5(UT2003/UT2004, Unreal II, Postal 2 세대) 기반
프로젝트를 Unreal Engine 5로 이식하기 위한 실무 계획서입니다.

## 가장 먼저 알아야 할 것

**UE2.5 프로젝트를 UE5로 "열거나 자동 변환하는 방법은 존재하지 않습니다."**

UE4 이후 마이그레이션 도구(`Convert Project`, 애셋 재저장 등)는 UE4/UE5 사이에서만
동작합니다. UE2 → UE3 → UE4 → UE5 로 이어지는 자동 업그레이드 경로는 엔진 역사상
한 번도 제공된 적이 없고, 다음 세 가지가 결정적인 단절 지점입니다.

| 단절 지점 | UE2.5 | UE5 | 결과 |
|---|---|---|---|
| 스크립트 언어 | UnrealScript (`.uc` → `.u`) | C++ / Blueprint | 전량 재작성 |
| 패키지 포맷 | `.utx`, `.usx`, `.ukx`, `.uax`, `.u`, `.ut2` | `.uasset`, `.umap` | 추출 후 재임포트 |
| 레벨 구성 | BSP(CSG) 중심 + 라이트맵 베이크 | 스태틱 메시 + Nanite/Lumen | 레벨 재구축 |

따라서 이 작업의 정확한 성격은 *업그레이드*가 아니라 **"자산을 구출해서 UE5에서
게임을 다시 만드는 포팅 프로젝트"** 입니다. 아래 문서들은 그 재구축 비용을 최대한
줄이는 순서와 방법을 다룹니다.

## 문서 목차

| 문서 | 내용 |
|---|---|
| [01-assessment.md](01-assessment.md) | 현황 조사, 자산 인벤토리, 범위와 일정 산정 |
| [02-asset-pipeline.md](02-asset-pipeline.md) | 패키지 추출 도구와 자산 종류별 변환 파이프라인 |
| [03-unrealscript-to-cpp.md](03-unrealscript-to-cpp.md) | UnrealScript → C++/Blueprint 문법·API 대응표 |
| [04-gameplay-framework.md](04-gameplay-framework.md) | GameInfo/Pawn/Controller/Mutator 등 프레임워크 매핑 |
| [05-level-and-rendering.md](05-level-and-rendering.md) | 레벨·BSP·머티리얼·라이팅 재구축 |
| [06-physics-animation-audio.md](06-physics-animation-audio.md) | Karma→Chaos, 스켈레탈 애니메이션, 사운드 |
| [07-networking.md](07-networking.md) | 리플리케이션과 RPC 변환 |
| [08-project-setup.md](08-project-setup.md) | UE5 프로젝트 구조, 폴더 규칙, Git/LFS 설정 |
| [09-checklist.md](09-checklist.md) | 단계별 체크리스트와 리스크 목록 |

## 전체 로드맵

```
0단계  현황 조사        자산 인벤토리 작성, 이식 범위 확정            (1~2주)
1단계  프로젝트 셋업     UE5 빈 프로젝트 + 폴더 규칙 + Git LFS         (2~3일)
2단계  자산 추출        umodel/UTPT로 텍스처·메시·사운드 뽑아내기      (1~3주)
3단계  코어 게임플레이   GameMode/Pawn/Controller/무기 1종 수직 슬라이스 (3~6주)
4단계  스크립트 이식     UnrealScript 클래스별 C++/BP 재작성            (지속)
5단계  레벨 재구축      맵 1개 기준 블록아웃 → 라이팅 → 폴리싱          (맵당 2~4주)
6단계  멀티플레이       리플리케이션 재구성 및 네트워크 테스트           (2~4주)
7단계  최적화/출시      Nanite/Lumen 튜닝, 패키징, 플랫폼 대응          (지속)
```

3단계의 **수직 슬라이스**(플레이어 1명이 이동해서 무기 1종을 쏘고 적 1종을 죽이는
플레이 루프)를 최우선으로 완성하십시오. 여기서 검증된 패턴이 이후 수백 개 클래스
이식의 템플릿이 됩니다.

## 법적 주의

UE2.5 프로젝트에 포함된 에픽게임즈 기본 콘텐츠(UT2004 기본 텍스처·메시·사운드,
`Engine.u` 등 엔진 패키지 파생물)는 재배포 권한이 없습니다. **직접 제작했거나
권리를 보유한 자산만** UE5 프로젝트로 옮기고, 엔진 기본 자산에 의존하던 부분은
UE5 기본 콘텐츠나 신규 제작물로 대체하십시오. UnrealScript 코드도 엔진 소스에서
복사된 부분과 자체 작성 부분을 구분해 기록해 두는 편이 안전합니다.
