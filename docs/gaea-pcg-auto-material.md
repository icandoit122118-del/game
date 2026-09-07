# Gaea 지형 위 에셋 배치 & 오토 머티리얼 (UE5 PCG + Auto Landscape Material)

Gaea에서 구운 대형 지형을 UE5로 가져온 뒤,

1. **경사도/고도/침식 마스크에 따라 자동으로 텍스처를 칠하고** (Auto Landscape Material)
2. **그 마스크를 그대로 재사용해 나무·바위·풀을 절차적으로 배치**하는 (PCG)

전체 파이프라인 정리 문서입니다. 별도 유료 에셋 없이 UE5 순정 기능만으로 구성하는 것을 기본으로 하고,
마켓플레이스 에셋을 쓸 때의 판단 기준은 마지막 절에 따로 정리했습니다.

---

## 0. 전체 흐름 한눈에 보기

```
Gaea
 ├─ Height     (16-bit PNG / R16)  ──► Landscape 하이트맵
 └─ Masks      (8-bit PNG, 흑백)   ──► Landscape Layer Weightmap
      ├─ Flow / Wear   (침식)            │
      ├─ Deposits      (퇴적)            ├─► Auto Material 의 "수동 보정용" 레이어
      ├─ Slope         (경사)            │
      └─ Texture/Soil  (합성)            └─► PCG 의 배치 밀도/종류 결정 마스크
                                          
UE5
 Landscape ──► Landscape Material (Slope/Height/Curvature 자동 블렌딩 + 수동 페인트 오버라이드)
     │
     └──► PCG Volume ──► PCG Graph
                          ├─ Get Landscape Data (position / normal / layer weight)
                          ├─ Density Filter (경사·고도·마스크 값으로 컷)
                          ├─ Transform (랜덤 회전/스케일, 지면 노멀 정렬)
                          └─ Static Mesh Spawner (Nanite + ISM/HISM)
```

핵심 원칙: **Gaea에서 만든 마스크 한 벌을 머티리얼과 PCG가 공유한다.**
그래야 "바위 텍스처가 칠해진 곳에 바위가 놓이고, 퇴적된 평지에 풀이 자라는" 시각적 일관성이 생깁니다.

---

## 1. Gaea 쪽 준비

### 1-1. 내보낼 것

| 출력 | Gaea 노드 | 포맷 | 용도 |
|---|---|---|---|
| Height | Export (Height) | **16-bit PNG** 또는 R16 | Landscape 하이트맵 |
| Flow / Wear | Erosion 계열 출력 | 8-bit PNG | 침식 골짜기 → 자갈/젖은 바위, 배치 금지 영역 |
| Deposits | Erosion 계열 출력 | 8-bit PNG | 퇴적 평지 → 흙/잔디, 풀·덤불 밀집 |
| Slope | Slope 노드 | 8-bit PNG | 절벽 판정 (머티리얼에서 실시간 계산도 가능, 아래 참고) |
| Texture / Soil | Texture 노드 | 8-bit PNG | 종합 마스크. 바이옴 분할용 |
| Curvature | Curvature 노드 | 8-bit PNG | 능선(볼록)/골(오목) 구분. 나무 라인 만들 때 유용 |

### 1-2. 해상도 규칙

Landscape 해상도는 `(2^n) * ComponentQuads + 1` 형태여야 이어붙임이 깔끔합니다.
Gaea Build 해상도를 아래 값에 맞춰 두면 UE 임포트 시 리샘플링 없이 들어갑니다.

| Gaea Build 해상도 | UE Landscape 크기 | 대략 실제 크기(1uu=1cm, 스케일 100) |
|---|---|---|
| 1009 | 1009 x 1009 | 약 1 x 1 km |
| 2017 | 2017 x 2017 | 약 2 x 2 km |
| 4033 | 4033 x 4033 | 약 4 x 4 km |
| 8129 | 8129 x 8129 | 약 8 x 8 km (World Partition 필수) |

> Gaea는 1024/2048/4096으로 굽는 경우가 많은데, 그대로 넣으면 UE가 늘려서 계단 현상이 생깁니다.
> Gaea Build 설정에서 해상도를 위 값으로 직접 지정하거나, 굽고 나서 정확히 +1 픽셀 패딩하세요.

### 1-3. 마스크 굽기 팁

- 마스크는 **반드시 8-bit 그레이스케일**로. 컬러/알파가 섞이면 UE 임포트가 거부합니다.
- Gaea에서 `Clamp`, `Curve` 노드로 미리 대비를 정리해 두면 UE에서 파라미터 튜닝이 훨씬 편합니다.
- 파일명을 `<맵이름>_<레이어이름>.png` 로 통일하세요.
  UE 임포트 창에서 레이어 이름 매칭이 자동으로 잡히진 않지만, 수동 지정할 때 헷갈리지 않습니다.

---

## 2. UE5 임포트

1. `Landscape Mode → Manage → Import from File`
2. Heightmap File 에 16-bit PNG 지정
3. Section Size / Sections Per Component 는 기본값(63x63, 1x1)에서 시작
4. **Material** 슬롯에 뒤에서 만들 Auto Landscape Material 을 먼저 지정
   (이걸 지정해야 Layers 목록에 Layer Info 슬롯이 나타납니다)
5. 각 Layer 옆 `+` 로 **Layer Info Object** 생성
   - 웨이트 블렌딩(일반 레이어): **Weight-Blended Layer** 선택
   - 하나만 칠해지는 배타 레이어: Non Weight-Blended
6. 각 Layer 에 Gaea 마스크 PNG 지정 → Import

### Z 스케일 맞추기

Gaea에서 지형의 실제 높이가 예를 들어 1200m 라면:

```
Landscape Actor 의 Scale Z = (실제높이_cm / 512) / 100 * 100
                            = 실제높이_m * 100 / 512
예) 1200m → 1200 * 100 / 512 ≈ 234.375
```

UE 랜드스케이프는 16-bit 하이트맵의 전체 범위를 `-256 ~ +256 uu * ScaleZ` 로 매핑합니다.
Gaea에서 지형 높이 범위를 메모해 두고 위 식으로 계산하면 축척이 정확히 맞습니다.

### 대형 맵일 때

- 4k 이상이면 **World Partition** 을 켜고 `Landscape → Build → Build Landscape Grid` 로 스트리밍 분할
- 임포트 후 `Build → Build All Landscape` 로 그림자/노멀 캐시 생성
- Nanite Landscape (`Landscape 액터 → Enable Nanite`) 를 켜면 원거리 실루엣이 크게 좋아집니다

---

## 3. 오토 머티리얼 (Auto Landscape Material)

### 3-1. 목표

- **경사(Slope)** 가 급하면 → 바위
- **완만 + 고도 낮음** → 잔디/흙
- **고도 높음** → 눈/자갈
- 그 위에 Gaea 침식/퇴적 마스크로 보정
- 필요하면 손으로 덧칠 (수동 페인트가 자동 규칙을 이긴다)

### 3-2. 경사도 계산 (핵심 노드)

머티리얼 그래프에서 지면 기울기는 **월드 노멀의 Z 성분**으로 구합니다.

```
PixelNormalWS ──► Mask (B only) ──► Slope01
    Slope01 = 1.0  → 완전 평지
    Slope01 = 0.0  → 완전 수직 절벽
```

이걸 `SmoothStep` 으로 부드러운 블렌드 알파로 바꿉니다.

```
RockAlpha = 1 - SmoothStep( SlopeMin, SlopeMax, PixelNormalWS.B )

  SlopeMin = 0.55  (약 56도 이상은 완전히 바위)
  SlopeMax = 0.80  (약 37도 이하는 완전히 지면)
```

두 값은 **Scalar Parameter** 로 빼서 Material Instance에서 슬라이더로 조절되게 하세요.
지형마다 최적값이 다르므로, 하드코딩하면 반드시 다시 고치게 됩니다.

### 3-3. 고도 블렌딩

```
AbsoluteWorldPosition ──► Mask(B) ──► SnowAlpha
SnowAlpha = SmoothStep( SnowStart, SnowFull, WorldZ )
```

`SnowStart`/`SnowFull` 도 파라미터로. 여기에 노이즈 텍스처를 더해주면
칼로 자른 듯한 눈 경계선이 자연스러워집니다.

```
SnowAlpha = SmoothStep( SnowStart, SnowFull, WorldZ + (Noise - 0.5) * NoiseAmount )
```

### 3-4. 절벽 텍스처는 World Aligned 로

수직 절벽에 일반 UV 텍스처를 깔면 **세로로 길게 늘어납니다**. 반드시 트라이플래너를 쓰세요.

- 엔진 내장 `World Aligned Texture` 머티리얼 함수 사용
- 또는 `World Aligned Blend` 로 위/옆 텍스처를 나눠 적용
- 비용이 크므로 **절벽 레이어에만** 적용하고 평지는 일반 UV 유지

### 3-5. 레이어 구조 예시

`Landscape Layer Blend` 노드에 아래 순서로 쌓습니다. (뒤에 오는 것이 위에 칠해짐)

| # | Layer Name | Blend Type | Preview Weight | 소스 |
|---|---|---|---|---|
| 1 | `Auto` | Weight-Blended | 1.0 | 자동 규칙 결과 (경사/고도) |
| 2 | `Deposits` | Weight-Blended | 0.0 | Gaea 퇴적 마스크 |
| 3 | `Flow` | Weight-Blended | 0.0 | Gaea 침식 마스크 |
| 4 | `Rock_Paint` | Weight-Blended | 0.0 | 수동 페인트 |
| 5 | `Grass_Paint` | Weight-Blended | 0.0 | 수동 페인트 |

`Auto` 레이어의 컬러/노멀/러프니스 입력에 3-2 ~ 3-4 에서 만든 자동 블렌딩 결과를 넣습니다.
이렇게 하면 **아무것도 칠하지 않아도 지형이 완성 상태로 보이고**, 필요한 곳만 손으로 덧칠하면 됩니다.

### 3-6. 근거리 디테일 & 원거리 타일링

- **Distance Blend**: `Distance Blend` 노드로 가까울 때만 디테일 노멀/디테일 텍스처를 섞기
- **Macro Variation**: 아주 큰 스케일(수천 uu)의 노이즈를 컬러에 곱해서 타일링 반복감 깨기
  ```
  FinalColor = BaseColor * lerp( 1 - MacroAmount, 1 + MacroAmount, MacroNoise )
  ```
- **Runtime Virtual Texture (RVT)**: 대형 맵이면 거의 필수.
  랜드스케이프 머티리얼 결과를 RVT에 굽고, 바위/도로 메시가 그걸 읽어 지형과 자연스럽게 섞이게 합니다.

### 3-7. 성능 체크리스트

- 샘플러 개수: 랜드스케이프 머티리얼은 텍스처 샘플러 16개 제한에 잘 걸립니다.
  → **Shared: Wrap** 샘플러 소스 사용, 또는 Texture Array / 채널 패킹(ORM: AO-Rough-Metal을 RGB에)
- 레이어는 실제로 쓰는 것만. 안 쓰는 레이어도 웨이트맵 텍스처를 잡아먹습니다.
- `Landscape Material` 과 별도로 `Landscape Hole Material` 은 동굴 뚫을 때만
- Material Instance 로만 작업하고, 마스터 머티리얼 재컴파일은 최소화

---

## 4. PCG 로 에셋 배치

### 4-1. 준비

`Edit → Plugins` 에서 활성화:
- **Procedural Content Generation Framework** (필수)
- **PCG Geometry Script Interop** (메시 샘플링 쓸 경우)

### 4-2. 기본 그래프

레벨에 `PCG Volume` 을 배치하고, 새 `PCG Graph` 애셋을 할당합니다.

```
[Input]
   │
   ▼
[Get Landscape Data]              ← 볼륨 범위의 랜드스케이프를 포인트로
   │
   ▼
[Surface Sampler]                 ← Points Per Squared Meter 로 밀도 결정
   │                                (넓은 맵은 0.001 ~ 0.01 부터 시작)
   ▼
[Density Filter / Attribute Filter]  ← 경사·고도·마스크로 컷
   │
   ▼
[Transform Points]                ← 랜덤 회전(Yaw만), 랜덤 스케일, 지면에 정렬
   │
   ▼
[Static Mesh Spawner]             ← 메시 목록 + 가중치
```

### 4-3. Gaea 마스크를 필터로 쓰기

이 파이프라인의 핵심입니다. 두 가지 방법이 있습니다.

**방법 A — 랜드스케이프 레이어 웨이트 읽기 (권장)**

`Get Landscape Data` 노드의 **Get Layer Weights** 를 켜면, 각 포인트에 랜드스케이프
레이어 이름 그대로 어트리뷰트가 붙습니다. 즉 3장에서 임포트한 Gaea 마스크가
그대로 PCG 필터 조건이 됩니다.

```
Attribute Filter:  $Deposits > 0.4      → 퇴적 평지에만 덤불
Attribute Filter:  $Flow     < 0.2      → 물길에는 나무 배치 금지
```

**방법 B — 텍스처 직접 샘플링**

`Get Texture Data` 로 Gaea 마스크 텍스처를 직접 물려 월드 좌표로 샘플링.
랜드스케이프 레이어로 임포트하지 않은 보조 마스크(바이옴 구분 등)에 씁니다.
텍스처는 임포트 시 **sRGB 끄기 + 압축 설정 `Masks (no sRGB)`** 로 두어야 값이 왜곡되지 않습니다.

### 4-4. 경사도로 거르기

머티리얼과 동일한 규칙을 PCG에서도 적용해야 룩이 맞습니다.

```
[Get Landscape Data] (Output Normal 켜기)
   │
   ▼
[Attribute Maths / Create Attribute]
   Slope = $Normal.Z
   │
   ▼
[Attribute Filter]  Slope > 0.85     → 나무는 완만한 곳만
[Attribute Filter]  Slope in 0.5~0.8 → 바위는 중간 경사에
```

경사 임계값은 머티리얼의 `SlopeMin/SlopeMax` 와 **같은 값을 쓰세요.**
바위 텍스처가 칠해진 경사에 나무가 서 있으면 바로 티가 납니다.

### 4-5. 밀도와 자연스러움

- `Surface Sampler` 의 **Points Per Squared Meter** 로 대략의 밀도
- `Density Noise` 노드로 뭉치고 흩어지는 클러스터 만들기 (일정 간격은 인공적으로 보임)
- `Self Pruning` / `Distance` 노드로 최소 간격 확보 → 메시 겹침 방지
- 큰 것부터 배치하고, 작은 것은 큰 것 주변을 **제외**하도록 순서 구성
  (나무 → 나무 반경 내 제외 → 덤불 → 풀)

### 4-6. Transform Points 설정 (자연스러움의 8할)

| 항목 | 값 | 이유 |
|---|---|---|
| Rotation Min/Max | Yaw `0~360`, Pitch/Roll `0` | Yaw만 랜덤. Pitch/Roll 랜덤은 나무가 넘어짐 |
| Scale Min/Max | `0.8 ~ 1.3` (균등) | 축별로 다르게 주면 찌그러져 보임 |
| Absolute Rotation | 나무=Off, 바위=On | 바위만 지면 노멀에 눕히기 |
| Offset Min/Max Z | `-20 ~ -5` | 살짝 파묻어 접지 틈 제거 |

### 4-7. Static Mesh Spawner

- **Mesh Entries** 에 여러 메시 + Weight 로 종 다양성 확보
- Quixel/Fab 나무는 Nanite 지원 여부 확인. Nanite면 LOD 걱정이 거의 사라짐
- **잎사귀(2-sided foliage)는 Nanite와 궁합이 나쁠 수 있음** → 잎은 기존 LOD, 줄기만 Nanite 등 혼용 검토
- `Static Mesh Spawner` 의 **ISM Descriptor** 에서:
  - `Cull Distance` 반드시 설정 (풀 3000~8000, 나무 30000~100000)
  - `Cast Shadow`: 작은 풀은 끄기. 그림자가 성능의 대부분을 먹습니다
  - `World Position Offset Disable Distance`: 바람 애니메이션 원거리 차단

### 4-8. 런타임 생성 vs 에디터 타임

| | 에디터 타임 (기본) | 런타임 (Runtime Generation) |
|---|---|---|
| 생성 시점 | `Generate` 버튼 / 저장 시 | 플레이 중 플레이어 주변 |
| 메모리 | 전체를 레벨에 보존 | 주변만 유지 |
| 적합 | 중소 맵, 아트 통제 필요 | 대형 오픈월드 |
| 설정 | 기본값 | PCG Component → `Generation Trigger = Generate At Runtime` + Runtime Generation Scheduler 설정 |

**대형 Gaea 맵이면 런타임 생성 + World Partition 조합을 권장합니다.**
런타임 모드에서는 `Grid Size` 를 계층으로 나눠(예: 나무 = 25600, 풀 = 3200)
멀리 있는 큰 것만 먼저 뜨게 하세요.

### 4-9. 배치 금지 영역 (도로/건물/스폰 지점)

```
[Get Actor Data] (태그로 필터, 예: "PCG_Exclude")
   │
   ▼
[Difference]  ←  Surface Sampler 결과
   │
   ▼
[Static Mesh Spawner]
```

`Difference` 노드에 Actor Bounds 나 Spline 을 물리면 그 안쪽은 배치에서 제외됩니다.
길·건물·컷씬 카메라 경로를 여기에 등록해 두면 이후 레벨 작업이 훨씬 자유로워집니다.

---

## 5. 성능 예산 잡기

Gaea 대형 맵 + 대량 폴리지 조합에서 실제로 문제가 되는 순서:

1. **그림자** — 폴리지 그림자가 가장 비쌉니다. 작은 것은 끄고, 중간 것은 `Cull Distance`를 짧게
2. **드로우콜 / 인스턴스 수** — `stat rhi`, `stat foliage` 로 확인. ISM 병합 단위 조정
3. **오버드로우** — 반투명 잎이 겹칠 때. `Shader Complexity` 뷰모드로 빨간 영역 확인
4. **랜드스케이프 머티리얼 명령 수** — 레이어 수 × 샘플러 수. 500 이하 목표
5. **WPO(바람)** — `World Position Offset Disable Distance` 로 원거리 차단

측정 명령:
```
stat unit          프레임 분해 (Game / Draw / GPU)
stat foliage       폴리지 인스턴스/트라이앵글
stat rhi           드로우콜
r.Nanite.Visualize 1
```

---

## 6. 마켓플레이스 에셋을 살 것인가

순정 PCG + 직접 만든 오토 머티리얼로 대부분 해결되지만, 아래 경우엔 구매가 시간을 아껴줍니다.

| 상황 | 권장 |
|---|---|
| 머티리얼 그래프를 직접 다루기 싫다 / 빨리 룩을 뽑아야 한다 | **Landscape Auto Material** 계열 구매 |
| 텍스처 세트까지 통째로 필요하다 | 텍스처 포함 팩 (Megascans Surface + 오토 머티리얼) |
| 파이프라인을 팀에서 오래 유지·확장해야 한다 | **직접 제작.** 남의 머티리얼은 디버깅이 지옥입니다 |
| 배치 로직이 프로젝트 고유 규칙에 크게 의존 | **PCG 직접 제작.** 대체 불가 |

구매하더라도 **경사/고도 판정 로직은 위 3-2, 3-3 과 동일**합니다.
원리를 알고 있으면 남의 에셋도 파라미터를 바로 찾아 고칠 수 있습니다.

참고: <https://www.pixelsdesign.it/blog/procedural-landscape-unreal-engine-5.html>

---

## 7. 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| 임포트한 지형이 계단처럼 각짐 | 8-bit 하이트맵을 썼음. **16-bit** 로 다시 내보내기 |
| 지형 높이가 너무 납작/과장됨 | Landscape Scale Z 미조정. 2장 공식으로 계산 |
| 마스크를 넣었는데 아무 변화 없음 | Layer Info Object 미생성, 또는 머티리얼의 Layer 이름 불일치 |
| 절벽 텍스처가 세로로 늘어남 | 트라이플래너(World Aligned Texture) 미적용 |
| 눈/바위 경계가 칼로 자른 듯함 | SmoothStep 범위가 너무 좁거나 노이즈 없음 |
| PCG Generate 해도 아무것도 안 나옴 | PCG Volume 이 랜드스케이프와 실제로 겹치는지, Density Filter가 전부 걸러내는지 확인 |
| 나무가 공중에 뜨거나 파묻힘 | Transform Points 의 Offset Z, 그리고 메시 피벗 위치 확인 |
| 나무가 절벽에 수평으로 붙어 있음 | Absolute Rotation 이 켜져 있음. 나무는 Off |
| 에디터가 PCG Generate 중 멈춤 | Points Per Squared Meter 가 과다. 1/10 로 낮추고 다시 |
| 플레이 중 폴리지가 뚝뚝 나타남 | Cull Distance 가 짧음. 또는 런타임 Grid Size 계층 재조정 |

---

## 8. 작업 순서 체크리스트

- [ ] Gaea Build 해상도를 UE 규격(1009/2017/4033/8129)으로 설정
- [ ] Height는 16-bit, 마스크는 8-bit 그레이스케일로 내보내기
- [ ] 지형 실제 높이(m) 메모 → Landscape Scale Z 계산
- [ ] 마스터 랜드스케이프 머티리얼 제작 (Slope/Height 자동 + 수동 페인트 레이어)
- [ ] Slope/Height 임계값을 Scalar Parameter 로 노출
- [ ] 절벽 레이어에만 World Aligned Texture 적용
- [ ] 머티리얼 지정 상태로 Landscape Import → Layer Info 생성 → 마스크 할당
- [ ] Build All Landscape
- [ ] PCG 플러그인 활성화, PCG Volume + Graph 생성
- [ ] Get Landscape Data 에서 **Layer Weights + Normal** 출력 켜기
- [ ] 머티리얼과 **동일한 경사 임계값**으로 PCG 필터 구성
- [ ] 큰 에셋 → 작은 에셋 순서로 배치, Self Pruning 으로 겹침 제거
- [ ] 배치 금지 영역(도로/건물)을 Difference 로 제외
- [ ] ISM Descriptor 에서 Cull Distance / Cast Shadow 정리
- [ ] 대형 맵이면 Runtime Generation + Grid Size 계층화
- [ ] `stat unit` / `stat foliage` 로 예산 확인
