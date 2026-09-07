# 06. 물리 · 애니메이션 · 오디오

## 6.1 물리: Karma → Chaos

UE2.5는 MathEngine의 **Karma** 물리 엔진을 사용했고, UE5는 자체 **Chaos** 엔진을
사용합니다(UE4의 PhysX도 UE5에서 제거됨). 두 엔진 사이에 데이터 호환성은 전혀
없으며, **물리 세팅은 전부 다시 만들고 다시 튜닝해야 합니다.**

| UE2.5 | UE5 |
|---|---|
| `Physics = PHYS_Walking` | `UCharacterMovementComponent` (`MOVE_Walking`) |
| `Physics = PHYS_Falling` | `MOVE_Falling` |
| `Physics = PHYS_Flying` | `MOVE_Flying` |
| `Physics = PHYS_Swimming` | `MOVE_Swimming` + `APhysicsVolume(bWaterVolume)` |
| `Physics = PHYS_Projectile` | `UProjectileMovementComponent` |
| `Physics = PHYS_Karma` | `PrimitiveComponent->SetSimulatePhysics(true)` |
| `KarmaParams` (KMass, KFriction, KRestitution) | Physical Material + Body Instance 설정 |
| `KarmaParamsRBFull` (래그돌) | **Physics Asset** (본별 바디·컨스트레인트) |
| `CollisionRadius` / `CollisionHeight` (실린더) | **Capsule Component** (`SetCapsuleSize`) |
| `bCollideActors` / `bBlockActors` | Collision Preset + Channel/Response 매트릭스 |
| `bProjTarget` | 커스텀 트레이스 채널 |
| `Velocity`, `Acceleration` | 동일 이름 유지 (`GetVelocity()`) |
| `SetPhysics()` | `SetMovementMode()` |

**콜리전 모델의 차이**를 반드시 인지하십시오. UE2.5의 액터 충돌은 **원기둥
(radius + height)** 고정이었고, UE5는 캡슐/박스/스피어/컨벡스/복합 형태를
지원합니다. 원기둥 → 캡슐 전환만으로도 좁은 통로 통과, 계단 오르기, 모서리
걸림 거동이 미묘하게 달라지므로 **레벨 디자인 수치(문 너비, 계단 높이)를
재검증**해야 합니다.

캐릭터 이동 파라미터는 다음 순서로 튜닝하는 것이 빠릅니다.

1. 캡슐 크기를 원본 × 2 로 설정 (예: 44/25 → half height 88, radius 50 → 실측 후 조정)
2. `MaxWalkSpeed`, `JumpZVelocity`, `GravityScale`을 원본 값 × 2 로 시작
3. **점프 최고 높이와 도달 거리를 실측**해 원본 스크린샷/영상과 비교하며 보정
4. `MaxStepHeight`, `WalkableFloorAngle`, `GroundFriction`, `AirControl` 순으로 미세 조정

UT류 게임 특유의 감각(닷지, 부스트 점프, 벽 튕김)은 `UCharacterMovementComponent`를
상속해 커스텀 이동 모드로 구현하고, 멀티플레이라면 `FSavedMove_Character`를
확장해 클라이언트 예측에 반영해야 합니다(07 문서 참조).

## 6.2 애니메이션

| UE2.5 | UE5 |
|---|---|
| `.ukx` 스켈레탈 패키지 | SkeletalMesh + Skeleton + AnimSequence 에셋 |
| `MeshAnimation` / AnimSet | Animation Sequence 모음 |
| 정점 애니메이션 메시 (`.3d`, UE1 레거시) | 대응물 없음 — 스켈레탈로 재제작 |
| `PlayAnim('Name')` / `LoopAnim()` | **Animation Blueprint** 상태 머신 / `PlayAnimMontage()` |
| `AnimBlendParams` (본별 블렌딩) | Layered Blend Per Bone 노드 |
| `SetAnimFrame()` | 몽타주 포지션 제어 |
| `AnimEnd()` 이벤트 | `OnMontageEnded` 델리게이트 |
| `NotifyAnim` | **Anim Notify** (사운드·이펙트·히트박스 활성화) |
| `AttachToBone()` | `AttachToComponent(Mesh, Rules, SocketName)` + **소켓** |
| 래그돌 (Karma) | Physics Asset + `SetSimulatePhysics` |
| IK 없음 (또는 수동 구현) | Control Rig / IK Rig / Full Body IK |

**본 이름과 스켈레톤 구조**가 최대 난관입니다. UE2.5 캐릭터의 본 계층은
UE5 표준(`root` / `pelvis` / `spine_01`...)과 다르므로 다음 중 하나를 택합니다.

- **원본 스켈레톤 유지**: 추출한 psk의 본 구조를 그대로 UE5 Skeleton으로 사용.
  원본 애니메이션이 그대로 재생되는 장점. 대신 UE5 마켓플레이스/Mixamo 애니메이션을
  쓰려면 매번 리타게팅 필요.
- **UE5 표준 스켈레톤으로 리타게팅**: **IK Retargeter**로 원본 애님을 UE5 매네퀸
  스켈레톤에 옮김. 초기 비용은 크지만 이후 에셋 생태계 전체를 쓸 수 있음. 장기
  프로젝트라면 이쪽 권장.

또한 UE2.5 애니메이션은 대부분 **루트 모션이 없고(제자리 애님 + 코드 이동)**,
프레임레이트가 30fps 기준입니다. UE5에서도 in-place 방식을 유지하는 것이
이식 비용상 유리하며, 루트 모션 전환은 별도 프로젝트로 다루십시오.

## 6.3 오디오

| UE2.5 | UE5 |
|---|---|
| `.uax` 사운드 패키지 | SoundWave 에셋 |
| `PlaySound(Sound, Slot, Volume, ...)` | `UGameplayStatics::PlaySoundAtLocation` / `SpawnSoundAttached` |
| 사운드 슬롯 (`SLOT_Talk`, `SLOT_Interact` 등) | **Sound Class / Sound Mix** 로 재구성 |
| `SoundRadius` / `SoundVolume` | **Attenuation 에셋** (거리 감쇠 커브, 공간화) |
| `AmbientSound` 액터 | `AAmbientSound` |
| `.umx` 트래커 음악 | OGG로 렌더 후 SoundWave, 또는 **MetaSound**로 동적 구성 |
| EAX / 리버브 존 | **Audio Volume** + Reverb Effect |
| 없음 | MetaSound (절차적 오디오), Quartz (동기화) |

원본 사운드는 22kHz/16bit 모노가 흔합니다. 그대로 써도 동작하지만 현대 기준으로는
음질이 눈에 띄게 낮으므로, **중요한 사운드(무기, 피격, 음성)부터 재녹음/교체**하는
우선순위 목록을 만드는 편이 좋습니다.

사운드 슬롯 개념은 UE5에 없습니다. 원본이 `SLOT_None`~`SLOT_Misc`로 채널을
관리했다면, UE5에서는 Sound Class 계층(Master → SFX/Music/Voice → 세부)과
Concurrency 설정(동시 재생 수 제한)으로 대체하십시오.
