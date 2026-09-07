# 08. UE5 프로젝트 셋업과 폴더 구조

## 8.1 프로젝트 생성

1. Epic Games Launcher에서 **UE 5.x** 설치 (LTS 성격의 안정 버전 권장. 프로젝트
   시작 시점의 최신 마이너 버전 중 하나를 골라 **고정**하고, 팀 전원이 동일
   버전을 사용하십시오. 엔진 버전 혼용은 `.uasset` 손상의 주원인입니다).
2. **Games → Blank → C++** 템플릿으로 생성. 스타터 콘텐츠는 제외.
3. 프로젝트 이름은 향후 C++ 모듈 이름·API 매크로(`MYGAME_API`)로 굳어지므로
   신중히 정하십시오. **나중에 바꾸기 매우 번거롭습니다.**

## 8.2 저장소 폴더 구조

```
game/
  docs/
    ue5-migration/          이 문서들
  legacy/                   원본 UE2.5 참조 자료 (커밋하지 않거나 별도 저장소)
    scripts/                *.uc 원본 (읽기 전용 참조)
    reference/              원본 스크린샷, 맵 t3d, 치수 메모
  tools/
    extract/                패키지 추출 스크립트
    convert/                t3d 파서, 텍스처 배치 변환 스크립트
  MyGame/                   UE5 프로젝트 루트
    MyGame.uproject
    Source/
      MyGame/               런타임 주 모듈
        Core/               GameMode, GameState, PlayerState
        Characters/         Pawn, Character, Movement
        Weapons/            무기 베이스와 컴포넌트
        AI/                 AIController, BT 태스크
        UI/                 UMG 백엔드 C++
        MyGame.Build.cs
      MyGameEditor/         에디터 전용 모듈 (컨버터 툴 등)
    Config/
      DefaultEngine.ini
      DefaultGame.ini
      DefaultInput.ini
    Content/
      Characters/
      Weapons/
      Maps/
      Materials/
      Audio/
      UI/
      Legacy/               원본에서 추출한 미정리 자산의 임시 격리 구역
    Plugins/
```

`Content/Legacy/`를 **격리 구역**으로 두는 것이 중요합니다. 추출한 자산을
곧바로 최종 폴더에 넣으면 "정리된 자산"과 "임포트만 해 둔 자산"이 섞여
품질 관리가 불가능해집니다. 정리·검수를 마친 것만 정식 폴더로 승격하십시오.

## 8.3 네이밍 규칙

UE 커뮤니티 표준(Allar 스타일 가이드)을 따르는 것을 권장합니다. 원본 UE2.5의
패키지 기반 이름(`MyPkg.MyTexture`)은 UE5의 경로 기반 이름과 맞지 않으므로
**임포트 시점에 일괄 리네임**하는 것이 가장 저렴합니다.

| 자산 | 접두사 | 예 |
|---|---|---|
| Blueprint | `BP_` | `BP_PlayerCharacter` |
| Static Mesh | `SM_` | `SM_Crate_01` |
| Skeletal Mesh | `SK_` | `SK_Soldier` |
| Texture | `T_` | `T_Crate_D`, `T_Crate_N` |
| Material | `M_` | `M_Metal_Master` |
| Material Instance | `MI_` | `MI_Metal_Rusted` |
| Animation Sequence | `A_` | `A_Soldier_Run` |
| Animation Blueprint | `ABP_` | `ABP_Soldier` |
| Sound Wave | `S_` | `S_Rifle_Fire` |
| Niagara System | `NS_` | `NS_MuzzleFlash` |
| Widget Blueprint | `WBP_` | `WBP_MainMenu` |
| Data Asset | `DA_` | `DA_RifleStats` |
| Level | `L_` / 접두사 없음 | `L_Arena_01` |

C++ 클래스는 엔진 규칙을 그대로 따릅니다: `A`=Actor, `U`=UObject, `F`=구조체,
`E`=열거형, `I`=인터페이스, `T`=템플릿, `b`=bool 변수.

## 8.4 Git과 LFS 설정

UE5 프로젝트는 바이너리 자산이 대부분이므로 **Git LFS가 사실상 필수**입니다.
이 저장소에 함께 커밋된 `.gitattributes`와 `.gitignore`를 프로젝트 루트에
적용하십시오.

```bash
git lfs install
git lfs track "*.uasset"
git lfs track "*.umap"
```

주의할 점:

- **`.uasset`은 병합할 수 없습니다.** LFS는 파일 잠금(`git lfs lock`)을 지원하므로,
  여러 명이 같은 자산을 만지는 팀이라면 잠금 워크플로우를 도입하십시오.
- `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`는 **절대 커밋하지
  마십시오.** 용량이 수십 GB로 불어납니다.
- `Config/`는 반드시 커밋합니다.
- 원본 UE2.5 자산은 용량이 크고 재배포 권한 문제도 있으므로 **별도 저장소나
  아티팩트 스토리지**에 두고, 이 저장소에는 추출·변환 스크립트만 두는 것이
  깔끔합니다.

## 8.5 빌드와 CI

```bash
# 프로젝트 파일 생성 (Linux/Mac)
"$UE_ROOT/Engine/Build/BatchFiles/Linux/GenerateProjectFiles.sh" -project="$PWD/MyGame/MyGame.uproject" -game -engine

# 에디터 타깃 빌드
"$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" MyGameEditor Linux Development -project="$PWD/MyGame/MyGame.uproject"

# 패키징
"$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  -project="$PWD/MyGame/MyGame.uproject" \
  -noP4 -platform=Linux -clientconfig=Development \
  -cook -build -stage -pak -archive -archivedirectory="$PWD/Build"
```

CI는 엔진 설치 용량(수십 GB) 때문에 셀프 호스티드 러너나 전용 도커 이미지가
필요합니다. 초기에는 **컴파일 성공 여부만 검증하는 파이프라인**부터 세우고,
쿠킹·자동 테스트는 프로젝트가 안정된 뒤에 추가하십시오.
