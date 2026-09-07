# 05. 레벨·머티리얼·라이팅 재구축

이식 작업 중 **가장 자동화가 안 되고, 가장 비용이 큰 구간**입니다. UE2.5 레벨은
BSP(CSG) 기반으로 만들어졌지만 UE5의 렌더링 파이프라인(Nanite, Lumen, 가상 그림자
맵)은 전부 **스태틱 메시**를 전제로 최적화되어 있습니다.

## 5.1 BSP를 어떻게 할 것인가

| 방식 | 설명 | 권장도 |
|---|---|---|
| **UE5 브러시로 그대로 재현** | UE5에도 지오메트리 브러시가 남아 있음 | ✗ 비권장. Nanite·Lumen 지원이 빈약하고 사실상 레거시 기능 |
| **블록아웃 → 모듈러 메시 교체** | BSP는 프로토타입 용도로만 쓰고 최종 지오메트리는 스태틱 메시 | ✓ **표준 워크플로우** |
| **Modeling Mode로 직접 제작** | UE5 내장 모델링 툴로 레벨 지오메트리 생성 | ✓ DCC 왕복 없이 빠름 |
| **원본 맵을 통째로 메시로 추출** | umodel/에디터로 레벨 지오메트리를 OBJ로 뽑아 임포트 | △ 참조·정렬용으로만. 최종 자산으로는 부적합 (UV·머티리얼·라이트맵 엉망) |

**현실적인 절차**:

1. 원본 맵을 UnrealEd에서 열고 **탑뷰/사이드뷰 스크린샷과 주요 치수를 기록**합니다.
2. 원본 지오메트리를 OBJ/FBX로 추출해 UE5에 **참조 레이어로만** 임포트합니다
   (스케일 2배 보정, 콜리전 없음, 반투명 머티리얼).
3. 그 위에 UE5 Modeling Mode 또는 모듈러 메시 킷으로 **정식 지오메트리를 새로 만듭니다.**
4. 참조 레이어를 삭제합니다.

이 방식은 "원본과 똑같은 레이아웃"을 보장하면서도 UE5에 맞는 자산 구조를 얻습니다.

## 5.2 액터 배치 데이터는 부분 이관이 가능하다

지오메트리와 달리 **액터 배치(위치·회전·클래스)** 는 스크립트로 옮길 수 있습니다.
UnrealEd에서 맵을 `.t3d` 텍스트로 내보내면 다음과 같은 형태입니다.

```
Begin Actor Class=Light Name=Light42
    Location=(X=1024.000000,Y=-512.000000,Z=256.000000)
    Rotation=(Pitch=0,Yaw=16384,Roll=0)
    LightBrightness=200
End Actor
```

이를 파싱해 UE5의 액터 배치로 변환하는 컨버터를 작성할 수 있습니다. 변환 시
반드시 적용할 것:

- **위치 × 2.0** (uu 정의 변경, 02 문서 2.5절)
- **회전 × 360 / 65536** (정수 로테이터 → 도)
- **클래스 이름 매핑표** (`Light` → `APointLight`, `PlayerStart` → `APlayerStart` 등)

산출물은 UE5 레벨 에디터에 **붙여넣기 가능한 T3D 텍스트** 또는 에디터 유틸리티
Blueprint/Python(`unreal.EditorLevelLibrary.spawn_actor_from_class`)로 실행하는
스폰 스크립트로 만드는 것이 편합니다.

이 방식이 특히 효과적인 대상: **PlayerStart, 아이템/무기 스폰 포인트, 사운드
액터, 트리거, 라이트의 대략적 위치.** 멀티플레이 맵이라면 아이템 배치 좌표를
정확히 유지하는 것이 밸런스 재현에 결정적입니다.

## 5.3 머티리얼 변환

UE2.5는 셰이더 그래프 대신 **머티리얼 클래스 조합**을 사용했습니다.

| UE2.5 머티리얼 클래스 | UE5 대응 |
|---|---|
| `Texture` | Texture Sample 노드 |
| `Combiner` (Modulate/Add/AlphaBlend) | Multiply / Add / Lerp 노드 |
| `Shader` (Diffuse+Opacity+Specular) | Material의 각 출력 핀에 직접 연결 |
| `FinalBlend` (블렌드 모드 지정) | Material Blend Mode (Opaque/Masked/Translucent/Additive) |
| `TexPanner` | Panner 노드 |
| `TexRotator` | Rotator 노드 |
| `TexOscillator` | `Sine(Time)` × Scale → UV 조작 |
| `TexScaler` | UV × Scale |
| `Cubemap` | Reflection/Cubemap 샘플 (대부분 Lumen 반사로 대체) |
| `VertexColor` | Vertex Color 노드 |
| `TexEnvMap` | Reflection Vector 기반 UV (대부분 불필요) |

**전략**: 원본 머티리얼을 1:1로 복제하지 마십시오. UE5에서는
**Material 하나 + Material Instance N개** 구조가 표준입니다. 원본에서
`Combiner` 조합이 20종 있었다면, 마스터 머티리얼 2~3개로 수렴시키고 나머지는
파라미터 차이로 표현하는 것이 렌더링 성능과 관리 양쪽에서 유리합니다.

또한 UE2.5는 **PBR이 아닙니다.** 디퓨즈 텍스처를 그대로 Base Color에 넣으면
조명이 이중으로 적용된 것처럼 보입니다(원본 텍스처에 명암이 그려져 있기 때문).
리마스터 범위라면 텍스처에서 베이크된 음영을 제거(de-lighting)하는 작업이 필요합니다.

## 5.4 라이팅

| UE2.5 | UE5 |
|---|---|
| 라이트맵 베이크 (에디터 `Build Lighting`) | **Lumen**(동적 GI, 기본) 또는 Lightmass(베이크) |
| `Light` 액터, `LightBrightness` 0~255 | `APointLight` 등, **Intensity(칸델라/루멘 물리 단위)** |
| `LightHue`/`LightSaturation` (HSV 바이트) | `LightColor` (RGB) |
| `LightRadius` (uu, 비물리적 감쇠) | `AttenuationRadius` (cm) + 물리 기반 역제곱 감쇠 |
| 정점 라이팅 (Vertex Lighting) | 개념 소멸 |
| `Corona`, `LensFlare` | Bloom / 커스텀 포스트프로세스 |
| `Fog` (ZoneInfo) | Exponential Height Fog / Volumetric Fog |
| `Skybox` (별도 존을 카메라로 촬영) | Sky Sphere / Sky Atmosphere + Sky Light |

**밝기 값은 그대로 옮길 수 없습니다.** UE2.5의 `LightBrightness=64`는
아무 물리적 의미가 없는 반면 UE5는 실제 광량 단위를 씁니다. 원본 스크린샷을
옆에 띄워 두고 눈으로 맞추는 수밖에 없으며, 이때 **하나의 기준 씬을 정해
노출(Exposure)을 고정**한 뒤 작업해야 합니다. Auto Exposure를 켠 채로 라이팅을
맞추면 씬마다 결과가 달라집니다.

UE2.5의 스카이박스는 "멀리 떨어진 별도 존을 SkyZoneInfo 카메라로 렌더링해
BSP 표면에 투사"하는 독특한 방식이었습니다. UE5에는 이 개념이 없으므로
Sky Atmosphere + Sky Light 또는 큐브맵 기반 스카이 스피어로 재제작합니다.

## 5.5 지형(Terrain)

UE2.5의 `TerrainInfo`는 하이트맵과 레이어 텍스처, 데코레이션 레이어로 구성됩니다.
UE5의 Landscape로 다음과 같이 옮깁니다.

1. 원본 하이트맵을 8bit/16bit 그레이스케일 이미지로 추출.
2. UE5 Landscape 생성 시 **Import from File**로 하이트맵 지정.
3. **Z 스케일에 스케일 보정 2배를 반영**하고, 하이트맵 비트 심도 차이(UE2는
   8bit인 경우가 많음)로 인한 계단 현상은 스무딩으로 완화.
4. 레이어 텍스처는 Landscape Material의 Layer Blend로 재구성.
5. 데코레이션(풀·나무)은 **Foliage 툴** 또는 PCG로 재배치. 원본 배치 데이터는
   보통 절차적으로 생성된 것이라 그대로 옮길 수 없습니다.

## 5.6 Nanite / Lumen 적용 판단

| 자산 | Nanite | 비고 |
|---|---|---|
| 추출한 저폴리 원본 메시 (수백~수천 폴리) | 켜도 무방하나 이득 적음 | Nanite는 고밀도 메시에서 이득이 큼 |
| 신규 제작 고밀도 메시 | ✓ 권장 | |
| 반투명/마스크드 머티리얼 메시 | 제약 있음 | 마스크드는 지원되나 비용 존재 |
| 스켈레탈 메시 | UE5.5+ 실험적 | 안정성 확인 후 결정 |

Lumen은 기본으로 켜 두되, 원작 재현(1:1 포팅) 범위라면 **베이크 라이팅 +
Lumen 끄기**가 원본 룩에 더 가깝고 성능도 예측 가능합니다. 리마스터 범위라면
Lumen을 전제로 라이팅을 다시 설계하십시오.
