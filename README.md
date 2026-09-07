# game

Unreal Engine 2.5 기반 프로젝트를 **Unreal Engine 5**로 이식하기 위한 작업 저장소입니다.

## 시작하기

이식 계획 전체는 [`docs/ue5-migration/`](docs/ue5-migration/README.md) 에 정리되어 있습니다.

> **핵심 전제**: UE2.5 프로젝트를 UE5에서 자동 변환하거나 열 수 있는 방법은
> 존재하지 않습니다. UnrealScript 제거, 패키지 포맷 변경, BSP 중심에서 스태틱
> 메시 중심으로의 렌더링 전환 때문에 이 작업은 *업그레이드*가 아니라
> **자산을 구출해 UE5에서 다시 만드는 포팅 프로젝트**입니다.

| 문서 | 내용 |
|---|---|
| [개요와 로드맵](docs/ue5-migration/README.md) | 전체 단계와 일정 개요 |
| [01. 현황 조사](docs/ue5-migration/01-assessment.md) | 자산 인벤토리, 공수 산정, 범위 확정 |
| [02. 자산 파이프라인](docs/ue5-migration/02-asset-pipeline.md) | 패키지 추출, 변환, **스케일 2배 보정** |
| [03. UnrealScript → C++](docs/ue5-migration/03-unrealscript-to-cpp.md) | 문법·API 대응표, state 대체 전략 |
| [04. 게임플레이 프레임워크](docs/ue5-migration/04-gameplay-framework.md) | GameInfo/Pawn/Controller/Mutator 매핑 |
| [05. 레벨과 렌더링](docs/ue5-migration/05-level-and-rendering.md) | BSP, 머티리얼, 라이팅, 지형 |
| [06. 물리·애니메이션·오디오](docs/ue5-migration/06-physics-animation-audio.md) | Karma → Chaos, 리타게팅, 사운드 |
| [07. 네트워크](docs/ue5-migration/07-networking.md) | 리플리케이션과 RPC 변환 |
| [08. 프로젝트 셋업](docs/ue5-migration/08-project-setup.md) | 폴더 구조, 네이밍, Git LFS, 빌드 |
| [09. 체크리스트](docs/ue5-migration/09-checklist.md) | 단계별 체크리스트와 리스크 |

## 저장소 설정

UE5 프로젝트 파일이 추가되면 바이너리 자산 관리를 위해 Git LFS가 필요합니다.

```bash
git lfs install
```

`.gitattributes`에 `.uasset` / `.umap` 및 주요 소스 자산의 LFS 추적 규칙이,
`.gitignore`에 엔진 생성 산출물(`Binaries/`, `Intermediate/`, `Saved/`,
`DerivedDataCache/`) 제외 규칙이 이미 설정되어 있습니다.
