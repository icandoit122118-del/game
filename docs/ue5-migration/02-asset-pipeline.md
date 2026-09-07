# 02. 자산 추출과 변환 파이프라인

UE2.5 패키지는 UE5가 읽을 수 없으므로 **패키지 → 중간 포맷(FBX/PNG/WAV) → UE5
임포트** 3단계를 거칩니다. 이 단계는 이식 작업 중 유일하게 대규모 자동화가
가능한 구간이므로, 배치 스크립트에 투자할 가치가 충분합니다.

## 2.1 추출 도구

| 도구 | 용도 | 비고 |
|---|---|---|
| **UE Viewer (umodel)** | 메시·텍스처·애니메이션 추출 | UE1~UE5 지원. 스켈레탈은 `.psk`/`.psa`, 스태틱은 `.pskx`, 텍스처는 `.tga`/`.dds`로 내보냄. 사실상 표준 도구 |
| **UTPT (UT Package Tool)** | UE1/UE2 패키지 브라우징, 텍스처·사운드 추출 | `.uax` 사운드 추출과 패키지 내부 구조 확인에 유용 |
| **UnrealEd 3.0** (UT2004 동봉) | 원본 에디터에서 직접 Export | 텍스처(`.bmp`), 사운드(`.wav`), 메시, 맵(`.t3d`) 내보내기. **원본이 어떻게 조립돼 있는지 확인하는 용도로도 필수** |
| **Blender + PSK/PSA 애드온** | `.psk`/`.psa` → 정리 → `.fbx` | `io_scene_psk_psa` 애드온 사용 |
| **ActorX Importer** | 3ds Max용 psk/psa 임포터 | Max 파이프라인일 때 |

> 원본 게임 실행 파일이 남아 있다면 **UnrealEd를 반드시 한 번은 띄워 보십시오.**
> 머티리얼이 `Combiner`/`TexPanner` 조합으로 만들어진 방식, 라이트 배치, 무버
> 세팅 등은 스크린샷이나 문서보다 에디터에서 직접 보는 편이 정확합니다.

## 2.2 자산 종류별 변환 경로

| UE2.5 | 중간 포맷 | UE5 결과물 | 주의점 |
|---|---|---|---|
| `.utx` 텍스처 | TGA / PNG | Texture2D | 팔레트 텍스처(P8)는 RGBA로 변환됨. sRGB 플래그·노멀맵 압축 설정을 임포트 후 재지정 |
| `.usx` 스태틱 메시 | FBX | StaticMesh | 스케일 2배 보정 필요(2.5절). 라이트맵 UV는 UE5에서 재생성 |
| `.ukx` 스켈레탈 + 애님 | PSK/PSA → FBX | SkeletalMesh + AnimSequence | 본 이름 규칙이 UE5 표준과 달라 리타게팅 필요 |
| `.uax` 사운드 | WAV | SoundWave | UE2는 22kHz/16bit가 많음. 리샘플링 또는 재녹음 검토 |
| `.umx` 음악 (트래커) | OGG/WAV로 렌더 | SoundWave / MetaSound | OpenMPT 등으로 렌더링 |
| `.u` 스크립트 | `.uc` 텍스트 | C++ / Blueprint | 03 문서 참조. 자동 변환 불가 |
| `.ut2` 맵 | `.t3d` 텍스트 | 재구축 | 05 문서 참조. 배치 좌표만 부분 이관 가능 |
| `.int` 로컬라이징 | CSV | String Table | 키 구조가 달라 매핑표 필요 |
| `.ini` 설정 | — | `Config/Default*.ini` | 문법은 비슷하나 키가 전부 다름. 수동 이관 |

## 2.3 텍스처 배치 변환 예시

추출된 TGA를 UE5 임포트에 적합하게 정리하는 스크립트 예시입니다.

```bash
# TGA → PNG 일괄 변환 + 이름 정규화 (T_ 접두사, 공백 제거)
mkdir -p out
for f in extracted/**/*.tga; do
  base=$(basename "${f%.tga}" | tr ' ' '_')
  magick "$f" "out/T_${base}.png"
done
```

노멀맵으로 쓰이던 텍스처는 UE2.5에 노멀맵 개념이 없었으므로 대부분 존재하지
않습니다. **디퓨즈만 있는 텍스처 세트를 UE5의 PBR(Base Color / Normal /
Roughness / Metallic)로 승격하는 작업이 별도로 필요**하며, 이는 자동화되지
않는 아트 작업입니다. 옵션은 세 가지입니다.

1. 디퓨즈만 사용하고 Roughness는 상수로 고정 (가장 저렴, 룩은 평평함)
2. 디퓨즈에서 노멀·러프니스를 추정 생성 (Materialize, ArmorPaint 등)
3. 텍스처 전면 재제작 (Substance 등) — 리마스터 범위라면 결국 여기로 수렴

## 2.4 임포트 시 설정 체크리스트

UE5 임포트 직후 반드시 확인할 항목입니다.

- **텍스처**: sRGB 체크(컬러=on, 마스크/노멀=off), Compression Settings, Virtual Texture 여부
- **스태틱 메시**: `Generate Lightmap UVs`(Lumen 사용 시 불필요할 수 있음), Nanite 활성화 여부, Collision Complexity
- **스켈레탈 메시**: Skeleton 재사용 여부, `Import Morph Targets`, Physics Asset 자동 생성 후 수동 정리
- **애니메이션**: 대상 Skeleton 지정, Root Motion 설정, 프레임레이트(UE2 애님은 30fps 기준이 많음)
- **사운드**: Compression Quality, Looping, Attenuation 에셋 연결

## 2.5 스케일 보정 — 반드시 짚고 넘어갈 것

UE2.5와 UE5는 **언리얼 유닛(uu)의 실제 크기 정의가 다릅니다.**

| | UE2.5 | UE5 |
|---|---|---|
| 1 uu | 약 2 cm | 정확히 1 cm |
| 표준 인간 캐릭터 높이 | 약 88 uu (CollisionHeight 44 × 2) | 176 uu (캡슐 half height 88) |
| 표준 걷기 속도 | 약 440 uu/s | 약 600 uu/s |

즉 **UE2.5 지오메트리를 그대로 임포트하면 UE5에서 절반 크기로 보입니다.**
대응 방법은 두 가지입니다.

- **권장**: 임포트 시 Uniform Scale `2.0` 을 적용해 실제 물리 크기를 맞춘다.
  UE5의 캐릭터 무브먼트·물리·라이팅 유닛이 모두 1uu=1cm를 가정하므로 장기적으로 안전.
- **비권장**: 원본 스케일 유지 후 캐릭터를 축소. 초반엔 편하지만 Lumen 감쇠 거리,
  물리 질량, 카메라 근접 평면 등에서 계속 문제가 생깁니다.

회전값도 표현이 다릅니다. UE2.5의 로테이터는 **정수 0~65535(한 바퀴 = 65536)**,
UE5의 `FRotator`는 **실수 도(degree)** 입니다.

```
degrees = unreal_rotator_units * 360.0 / 65536.0
```

맵의 액터 배치 데이터를 스크립트로 이관할 때 이 변환을 빠뜨리면 모든 오브젝트가
엉뚱한 방향을 봅니다. 좌표계 자체(Z-up, X-forward)는 동일하므로 축 교환은
필요 없습니다.
