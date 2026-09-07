# 폴아웃 4 애니메이션을 언리얼 엔진 5에서 인식시키는 방법

> 조사 정리 문서. 2026-09 기준으로 확인 가능한 툴체인을 정리했습니다.

## 0. 결론부터

**언리얼 5는 폴아웃 4의 애니메이션 파일(`.hkx`)이나 메시(`.nif`)를 절대 직접 읽지 못합니다.**
UE5 애니메이션 임포터가 받는 것은 사실상 **FBX**(그리고 glTF, USD)뿐입니다. 따라서 문제는
"UE5가 hkx를 인식하게 만드는 법"이 아니라 **"hkx를 FBX로 바꾸는 법"** 입니다.

```
Fallout4 - Animations.ba2   (베데스다 아카이브)
        │  ① 아카이브 추출 (B.A.E. / BSA Browser / Archive2)
        ▼
   skeleton.hkx + *.hkx      (Havok 2014.1.0-r1, amd64/64비트)
        │  ② hkx → FBX 변환  ← 여기가 유일한 관문
        ▼
       *.fbx
        │  ③ UE5 임포트 (Skeleton 지정 / Import Animations)
        ▼
   UE5 AnimSequence
        │  ④ IK Rig + IK Retargeter 로 마네킹(Manny/Quinn)이나 자체 캐릭터에 리타겟
        ▼
        완성
```

핵심 포인트 3가지:

1. 폴아웃 4의 hkx는 **Havok 2014.1.0-r1 / 64비트(amd64) 패킹**입니다. 스카이림(오리지널)의
   Havok 2010 32비트용 구형 툴(`hkxcmd` 단독 등)은 그대로는 먹지 않습니다.
2. 변환 도구 대부분(특히 `havok2fbx`)은 **32비트(win32) hkx만** 받습니다. 그래서 실무 파이프라인에
   거의 항상 **64비트 → 32비트 재패킹 단계**가 끼어 있습니다.
3. `Meshes/Actors/Character/Behaviors/*.hkx` 는 **애니메이션이 아니라 비헤이비어 그래프**입니다.
   이건 변환 대상이 아니고, UE5에서는 Animation Blueprint / State Machine으로 직접 다시 만들어야 합니다.

---

## 1. 어떤 파일을 어디서 꺼내는가

| 대상 | 경로 (Data 폴더 기준) | 들어있는 아카이브 |
|---|---|---|
| 인체 Havok 스켈레톤 | `Meshes/Actors/Character/CharacterAssets/skeleton.hkx` | `Fallout4 - Meshes.ba2` |
| 인체 메시 스켈레톤(NIF) | `Meshes/Actors/Character/CharacterAssets/skeleton.nif` | `Fallout4 - Meshes.ba2` |
| 애니메이션 | `Meshes/Actors/Character/Animations/**/*.hkx` | `Fallout4 - Animations.ba2` |
| 비헤이비어 그래프(변환 X) | `Meshes/Actors/Character/Behaviors/*.hkx` | `Fallout4 - Animations.ba2` |

다른 종족/액터(슈퍼뮤턴트, 파워아머, 데스클로 등)는 `Meshes/Actors/<ActorName>/` 아래에 같은 구조로 있습니다.

**추출 도구**

- [B.A.E. – Bethesda Archive Extractor](https://www.nexusmods.com/fallout4/mods/78) — 가장 무난
- [BSA Browser (.BA2 지원)](https://www.nexusmods.com/fallout4/mods/17061) — 미리보기/부분 추출 편함
- `Archive2.exe` — 폴아웃 4 Creation Kit에 동봉된 공식 툴

> ⚠️ 애니메이션은 **반드시 그 애니메이션이 만들어진 스켈레톤과 짝**으로 다뤄야 합니다.
> hkx 애니메이션 파일 안에는 본 이름이 들어있지 않고 **트랙 인덱스만** 있습니다. 스켈레톤이 없으면
> 어느 트랙이 어느 본인지 알 수 없어서 변환기가 아예 동작하지 않거나 뼈가 뒤섞입니다.

---

## 2. 경로 A — Blender + PyNifly (권장, 전부 무료)

2026년 기준 가장 접근성이 좋은 경로입니다. 유료 3ds Max도, 구하기 어려운 Havok Content Tools도 필요 없습니다.

**PyNifly**: 블렌더용 NIF/HKX 임포트·익스포트 애드온.
공식 설명에 *"Handles animations. Direct import/export to hkx files for FO4, SE, and LE, and exports hkx skeletons for Skyrim and FO4"* 라고 명시되어 있습니다.

- GitHub: <https://github.com/BadDogSkyrim/PyNifly>
- Nexus: <https://www.nexusmods.com/fallout4/mods/52319>
- **애니메이션 임포트/익스포트 기능은 Blender 4.4 이상 필요** (애드온 자체는 4.0+)

### 순서

1. Blender 4.4+ 설치 → PyNifly 릴리스 zip을 `Edit > Preferences > Add-ons > Install`로 설치
2. **스켈레톤 먼저 임포트**: `skeleton.hkx` 를 임포트 (⚠️ `skeleton.nif`가 아님 — 둘은 다른 파일이고
   애니메이션은 hkx 스켈레톤 기준으로 만들어져 있음)
3. 필요하면 그 위에 바디 메시(`.nif`)를 임포트해서 스키닝 상태로 붙임
4. **애니메이션 hkx 임포트**: 기존 아마추어를 선택한 상태에서 임포트하면 그 위에 액션으로 올라옴
   - `Rotate bones pretty` 옵션을 쓰면 본 방향이 보기 좋게 회전되지만, 임포트/익스포트가 이를 보정하므로
     재생 자체는 정상. 문제가 생기면 이 옵션을 끄고 다시 시도
   - 본 이름 리네임 옵션도 문제가 되면 끄기 (원본 이름 유지)
5. `File > Export > FBX` 로 내보내기 (아래 3장 설정 참고)

### 여러 개 일괄 처리

`bpy` 스크립트로 폴더 순회하며 임포트 → 액션 이름 지정 → FBX 익스포트를 돌리면
수백 개짜리 배치 변환이 됩니다. 액션 하나당 FBX 하나로 뽑는 편이 UE5 임포트가 깔끔합니다.

---

## 3. 경로 B — havok2fbx 직행 (CLI, 배치에 강함)

3D 툴을 거치지 않고 커맨드라인으로 hkx를 바로 FBX로 굽는 경로입니다.

**핵심 도구: `havok2fbx`** — Havok SDK 2014-1-0 + FBX SDK 2014.2.1로 빌드된 변환기.

```
havok2fbx.exe -hk_skeleton <skeleton.hkx> -hk_anim <animation.hkx> -fbx <output.fbx>
```

- 원본: <https://github.com/Highflex/havok2fbx>
- 포크: <https://github.com/nta/havok2fbx>, <https://github.com/razar51/havok2fbx>
  (razar51 포크는 **스켈레톤 본 수와 애니메이션 트랙 수가 다를 때** 트랙-본 매칭을 고쳐서 붙여줌 — 폴아웃 4에서 자주 필요)
- GUI 래퍼: **`F4AK_HKXPackUI`** (ShadeAnimator의 Fallout 4 Animation Kit에 포함).
  스켈레톤 지정 후 hkx들을 드래그&드롭 → `Convert HKX to FBX` 버튼.
  <https://github.com/ShadeAnimator/ShadeAnimator_Fallout4_AnimationKit>

### ⚠️ 반드시 걸리는 제약: 32비트

README에 *"Files to be converted must be on Version 2014-1-0 x32!"* 라고 못박혀 있습니다.
폴아웃 4의 hkx는 **amd64(64비트)** 이므로 먼저 **win32(32비트)로 재패킹**해야 합니다.

**64비트 → 32비트 변환 방법 (택 1)**

| 도구 | 설명 | 링크 |
|---|---|---|
| **serde-hkx (`hkxc`)** | Rust로 작성된 최신 Havok 직렬화 CLI. `xml ↔ 32bit hkx ↔ 64bit hkx` 무손실 변환 지원. 현재 가장 추천 | <https://github.com/SARDONYX-sard/serde-hkx> |
| **HkxTools (gs-oar)** | 위 `hkxc.exe` + `hkxconv`를 감싼 GUI. amd64 → win32 배치 변환 | <https://github.com/gs-oar/hkxtools> |
| **Composite HKX Conversion GUI** | `serde-hkx` + `hkxcmd` + `hkxconv`를 한 번에 묶은 GUI | Nexus SSE mods/154237 |
| **hkxconv** | amd64 hkx → XML. 중간 포맷 확인/디버깅용으로 유용 | — |
| **HKXPack** | "폴아웃 4에 최적화된" hkx ↔ XML 변환기 (Java) | <https://dexesttp.github.io/hkxpack/> |
| **Havok Content Tools 2014** | 공식 툴. `ConvertAnimation_X32` 필터 설정으로 변환. 정확하지만 구하기 어려움 | — |

### ⚠️ havok2fbx의 축 문제

`havok2fbx`는 **애니메이션을 +X축 기준으로 돌려서** 내보냅니다.
FBX를 받은 뒤 Blender/Max에서 **Root 본을 선택해 방향을 바로잡거나**, UE5 임포트 시
`Force Front X Axis` / `Convert Scene` 옵션으로 보정해야 합니다. 캐릭터가 옆이나 뒤를 보고 있으면 이게 원인입니다.

---

## 4. 경로 C — 3ds Max + Havok Content Tools (전통 방식, 가장 정확)

모딩 커뮤니티의 원조 파이프라인입니다. 정확도는 최고지만 진입 장벽이 높습니다.

**필요한 것**

- **3ds Max 2013 / 2014 / 2015 중 하나** (그 이후 버전은 HCT 플러그인 미지원)
- **Havok Content Tools 2014.1** (`HavokContentTools_2014-1-0_20140830_64Bit_PcXs.exe`).
  Microsoft가 Havok을 인수한 뒤 공식 배포가 중단되어 현재는 구하기 까다로움
- [HavokMax (PredatorCZ)](https://github.com/PredatorCZ/HavokMax) — Max용 Havok 임포트 플러그인
  (2022-07-07 아카이브됨, 읽기 전용이지만 릴리스 바이너리는 계속 사용 가능. Max 2010~2023용 빌드 존재)
- [hkxImport (SebboHN)](https://github.com/SebboHN/hkxImport) — 바닐라 폴아웃 4 애니메이션을 Max로 끌어오는
  MaxScript. `HKXImport.ms` + `hkxreano.exe` + `hkxpack-cli.jar` 를 같은 폴더에 두고 실행. Java JRE는 어노테이션용으로 선택
- [F4AK – Fallout 4 Animation Kit (ShadeAnimator)](https://www.nexusmods.com/fallout4/mods/16694) — 인체/파워아머/슈퍼뮤턴트 리그와 HCT 프리셋 포함
- NIF 임포터/익스포터 플러그인 (메시용)

**순서**: 리그가 들어있는 max 씬 열기 → `HKXImport.ms` 실행 → 종족 선택 → hkx 선택 →
(`Invert Top` 체크 해제 확인) → 임포트 → 다른 이름으로 저장 → `File > Export > FBX`.

---

## 5. FBX 익스포트 설정 (Blender / 3ds Max → UE5)

Blender FBX 익스포트 기준 권장값:

| 항목 | 값 |
|---|---|
| Path Mode | Copy (+ Embed Textures, 메시 내보낼 때) |
| Apply Scalings | `FBX All` |
| Forward / Up | `-Y Forward` / `Z Up` (UE5 기본 궁합) |
| Apply Unit | 켜기 |
| Object Types | Armature (+ Mesh, 메시가 필요할 때) |
| **Add Leaf Bones** | **끄기** (이거 켜져 있으면 UE에서 쓸데없는 `_end` 본이 생김) |
| Bake Animation | 켜기, `NLA Strips` 끄고 `All Actions` 상황에 맞게 |
| Simplify | `0` (키 간소화로 미묘한 모션이 뭉개지는 것 방지) |

**프레임레이트**: 베데스다 애니메이션은 **30 fps** 기준입니다. 씬 FPS를 30으로 맞추고 베이크하세요.
(블렌더용 HKX 애드온 문서에서도 정확한 결과를 위해 30fps 샘플링을 요구합니다.)

**스케일**: Havok 스켈레톤은 미터 단위, NIF는 베데스다 유닛(1 unit ≈ 1.43 cm) 기준이라
경로에 따라 결과 스케일이 100배 또는 1/100배로 어긋나기 쉽습니다.
UE5에서 캐릭터가 개미만 하거나 거인이면 임포트 옵션의 **Import Uniform Scale**을 `100` 또는 `0.01`로 조정하세요.
(3ds Max 경유일 때는 보통 `1.0`이 맞습니다.) 절대값보다 **마네킹과 나란히 세워서 눈으로 확인**하는 게 빠릅니다.

---

## 6. UE5 임포트

### 6-1. 스켈레톤 애셋 먼저 만들기

1. **스킨이 입혀진 캐릭터 FBX 하나**를 먼저 임포트합니다.
2. FBX Import Options 창에서 **Skeleton 칸을 비워두면** 그 메시를 기준으로 Skeleton 애셋이 자동 생성됩니다.
3. 이게 앞으로 모든 폴아웃 4 애니메이션이 붙을 **기준 스켈레톤**이 됩니다.

### 6-2. 애니메이션 임포트

- Import Options에서 **방금 만든 Skeleton을 반드시 지정**합니다.
- `Import Animations` 체크, `Import Mesh` 해제 (애니메이션 전용 FBX일 때).
- `Animation Length`: `Exported Time`
- `Use Default Sample Rate` 해제 → **30** 입력
- `Import Bone Tracks` 켜기
- 축이 틀어졌다면 `Convert Scene` / `Force Front X Axis` 조합을 바꿔가며 시도

> 본 이름이 하나라도 다르면 UE5는 "Skeleton과 맞지 않는다"며 임포트를 거부합니다.
> **FBX 안의 본 이름 = Skeleton 애셋의 본 이름** 이 되도록 맞추는 게 임포트 성공의 90%입니다.
> 이름이 조금 다를 뿐이라면, 스켈레톤 애셋의 `Retarget Manager`에서 매핑하거나 Blender 단계에서 리네임하세요.

### 6-3. UE5 마네킹으로 리타게팅

폴아웃 4 스켈레톤은 UE5 마네킹과 본 이름·계층·비율이 전부 다릅니다.
그대로는 마네킹에서 재생되지 않으므로 **IK Rig + IK Retargeter**를 씁니다.

1. **IK Rig 2개 생성** — 하나는 폴아웃 4 스켈레톤용, 하나는 `SK_Mannequin`용
2. 각 IK Rig에서 **Retarget Root 지정** — 휴머노이드는 거의 항상 **골반(Pelvis)**
3. **Retarget Chain 정의** — `Spine`, `LeftArm`, `RightArm`, `LeftLeg`, `RightLeg`, `Head` 등
   같은 이름의 체인끼리 자동으로 짝지어집니다.
   폴아웃 4 인체 스켈레톤은 대체로 `Root` → `COM` → `Pelvis` → `Spine…` → `Neck`/`Head`,
   팔다리는 `LArm_*` / `RArm_*` / `LLeg_*` / `RLeg_*` 형태의 접두사를 씁니다.
   (정확한 이름은 NifSkope나 Blender에서 직접 확인하세요 — 종족·모드마다 다릅니다.)
4. **IK Retargeter 생성** → Source = 폴아웃 4 IK Rig, Target = 마네킹 IK Rig
5. 미리보기에서 발 미끄러짐/포즈 확인 후 **Export Selected Animations** 로 새 AnimSequence 굽기

UE 5.5 이후의 **Auto Retargeting**을 쓰면 체인 자동 생성으로 초기 세팅이 훨씬 빨라집니다.
→ <https://dev.epicgames.com/documentation/unreal-engine/auto-retargeting-in-unreal-engine>
→ <https://dev.epicgames.com/documentation/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine>

---

## 7. 자주 터지는 문제 정리

| 증상 | 원인 | 해결 |
|---|---|---|
| 변환기가 hkx를 아예 못 읽음 | 64비트(amd64) 파일을 32비트 툴에 넣음 | `serde-hkx`/`hkxtools`로 win32 재패킹 후 재시도 |
| 뼈가 스파게티처럼 뒤엉킴 | 애니메이션과 스켈레톤이 안 맞음 (트랙 인덱스 불일치) | 해당 액터 전용 `skeleton.hkx` 사용, `razar51/havok2fbx` 포크 시도 |
| 캐릭터가 옆/뒤를 봄 | `havok2fbx`가 +X축 기준으로 회전시킴 | Root 본 회전 보정, 또는 UE 임포트 시 `Force Front X Axis` 토글 |
| UE5가 "스켈레톤이 맞지 않음" 거부 | 본 이름/계층 불일치, Leaf Bone 추가됨 | FBX 익스포트에서 `Add Leaf Bones` 끄기, 본 이름 통일 |
| 캐릭터가 개미/거인 | 미터 vs 베데스다 유닛 스케일 차이 | `Import Uniform Scale` 100 또는 0.01 |
| 동작이 미묘하게 빠르거나 느림 | 30fps 원본을 24/60fps로 샘플링 | 씬 FPS 30, `Use Default Sample Rate` 해제 후 30 입력 |
| 제자리걸음(루트 모션 없음) | Havok의 extracted motion(reference frame)이 FBX로 안 넘어감 | AnimSequence의 `Enable Root Motion` + `Root Motion Root Lock` 설정, 필요하면 루트 커브를 수동 제작 |
| 발이 미끄러짐 | 비율 차이 | IK Retargeter에서 IK Goal 설정 후 재굽기 |
| 공격 타이밍/사운드 이벤트가 없음 | hkx 어노테이션이 FBX에 없음 | `hkanno`/`hkxreano`로 어노테이션 덤프 → UE5에서 AnimNotify 수동 배치 |
| 스테이트 전환이 재현 안 됨 | `Behaviors/*.hkx`는 비헤이비어 그래프 | UE5 Animation Blueprint로 새로 구성 (자동 변환 불가) |

---

## 8. 역방향 (참고)

UE5/블렌더에서 만든 애니메이션을 **폴아웃 4로 되돌리는** 경우:

- **`hkxanim` (Dexesttp)** — HKXPack 기반. FBX → 폴아웃 4용 hkx 생성.
  `java -jar hkxanim.jar <filename>.fbx` — <https://github.com/Dexesttp/hkxanim>
- **`FBXImporter` (andrelo1)** — Havok SDK 2014.1.0-r1로 빌드된 FBX → Havok 씬 변환기.
  <https://www.nexusmods.com/fallout4/mods/59849>
- **PyNifly** — 블렌더에서 FO4/SE/LE용 hkx 직접 익스포트 지원

---

## 9. 라이선스 관련 주의

폴아웃 4의 애니메이션·메시·스켈레톤은 **Bethesda / ZeniMax의 저작물**입니다.
베데스다 EULA는 이 애셋들을 **해당 게임의 모드 제작** 용도로 쓰는 것을 전제로 합니다.
추출한 애셋을 언리얼 프로젝트에 넣어 **배포하거나 상업적으로 이용하는 것은 허용 범위 밖**입니다.
개인 학습·기술 검증·파이프라인 연구 목적으로만 사용하고, 공개 배포물에는 자체 제작 애셋으로 교체하세요.
(스켈레톤 구조나 리타게팅 세팅 같은 *기법*은 자유롭게 재사용해도 무방합니다.)

---

## 10. 참고 링크

**변환 도구**
- havok2fbx — <https://github.com/Highflex/havok2fbx> · <https://github.com/nta/havok2fbx> · <https://github.com/razar51/havok2fbx>
- serde-hkx — <https://github.com/SARDONYX-sard/serde-hkx>
- hkxtools (GUI) — <https://github.com/gs-oar/hkxtools>
- HKXPack — <https://dexesttp.github.io/hkxpack/>
- hkxanim (FBX→HKX) — <https://github.com/Dexesttp/hkxanim>
- hkxcmd — <https://github.com/figment/hkxcmd>
- HKX2Library — <https://github.com/ret2end/HKX2Library>

**DCC 툴 연동**
- PyNifly (Blender) — <https://github.com/BadDogSkyrim/PyNifly>
- HavokMax (3ds Max) — <https://github.com/PredatorCZ/HavokMax>
- hkxImport (3ds Max) — <https://github.com/SebboHN/hkxImport>
- F4AK — <https://github.com/ShadeAnimator/ShadeAnimator_Fallout4_AnimationKit>
- blender-hkx (스카이림 전용, Havok SDK 자가 빌드 필요) — <https://github.com/jgernandt/blender-hkx>

**문서**
- Animation In Fallout 4 (Nexus Wiki) — <https://wiki.nexusmods.com/index.php/Animation_In_Fallout_4>
- sfmnauts 폴아웃 4 애니메이션 파이프라인 — <https://www.sfmnauts.com/fallout-4/animations.html>
- HKX File (Fallout Wiki) — <https://fallout.wiki/wiki/HKX_File>
- UE5 IK Rig 리타게팅 — <https://dev.epicgames.com/documentation/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine>
- UE5 Auto Retargeting — <https://dev.epicgames.com/documentation/unreal-engine/auto-retargeting-in-unreal-engine>
- UE5 Skeletons — <https://dev.epicgames.com/documentation/unreal-engine/skeletons-in-unreal-engine>
