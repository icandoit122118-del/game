# 04. 게임플레이 프레임워크 매핑

UE2.5(정확히는 UT2003에서 도입된 Controller 분리 구조)는 UE5 게임플레이
프레임워크의 직계 조상입니다. **클래스 이름과 역할 분담이 거의 그대로 살아 있어,
이식 대상 중 가장 손이 덜 가는 영역**입니다.

## 4.1 핵심 클래스 대응표

| UE2.5 | UE5 | 비고 |
|---|---|---|
| `Actor` | `AActor` | 컴포넌트 기반으로 재구성됨 (4.2절) |
| `Info` | `AInfo` | 그대로 존재 |
| `GameInfo` | `AGameModeBase` / `AGameMode` | **서버에만 존재**(UE2.5도 동일). 매치 상태 머신은 `AGameMode` |
| `GameReplicationInfo` (GRI) | `AGameStateBase` / `AGameState` | 전원에게 복제되는 게임 상태 |
| `PlayerReplicationInfo` (PRI) | `APlayerState` | 점수·이름·팀 |
| `TeamInfo` | `APlayerState::GetTeamId` 등 자체 구현 | UE5에 팀 클래스 기본 제공 없음. `IGenericTeamAgentInterface` 활용 |
| `Controller` | `AController` | |
| `PlayerController` | `APlayerController` | |
| `Bot` / `AIController` | `AAIController` | Behavior Tree 기반으로 재설계 권장 |
| `Pawn` | `APawn` | |
| `xPawn` / `UnrealPawn` (걷는 캐릭터) | `ACharacter` | `UCharacterMovementComponent` 포함 |
| `Weapon` / `Inventory` | `AActor` 파생 + `UActorComponent` | UE5엔 인벤토리 기본 클래스 없음. 직접 설계 |
| `HUD` | `AHUD` + **UMG** | Canvas 드로잉 코드는 UMG로 재제작 |
| `PlayerInput` | **Enhanced Input** (IMC + IA 에셋) | 완전 재구성 |
| `Mutator` | 대응물 없음 | 4.4절 |
| `Trigger` | 트리거 볼륨 + 오버랩 델리게이트 | `ATriggerBox`/`ATriggerVolume` |
| `Mover` / `InterpActor` | 무버블 액터 + Level Sequence / Timeline | |
| `ZoneInfo` | `APostProcessVolume`, `APhysicsVolume` | 존 개념 자체는 사라짐 |
| `PhysicsVolume` | `APhysicsVolume` | 이름 동일 |
| `PathNode` / `NavigationPoint` | **NavMesh** (`ANavMeshBoundsVolume`) | 수동 패스노드 배치 → 자동 내비메시 생성 |
| `Projectile` | `AActor` + `UProjectileMovementComponent` | |
| `Emitter` / `xEmitter` | **Niagara** | Cascade는 UE5에서 비권장. 전면 재제작 |
| `ScriptedSequence` / `AIScript` | Level Sequence + Behavior Tree | |
| `SavedMove` (네트워크 예측) | `FSavedMove_Character` | 커스텀 이동이 있다면 여기 재구현 |

## 4.2 상속에서 컴포넌트로 — 설계 전환

UE2.5 코드베이스의 전형적인 패턴은 **깊은 상속 트리**입니다.

```
Actor → Pawn → UnrealPawn → xPawn → MyCustomPawn → MyBossPawn
```

UE5도 상속을 쓰지만, **기능 단위는 컴포넌트로 분리하는 것이 표준**입니다.
이식하면서 다음과 같이 재구성하면 이후 확장 비용이 크게 줄어듭니다.

```cpp
// AMyCharacter (ACharacter 파생)
//  ├─ UCharacterMovementComponent   (엔진 제공)
//  ├─ UHealthComponent              (원본의 Health/Armor/TakeDamage 로직)
//  ├─ UInventoryComponent           (원본의 Inventory 링크드 리스트 대체)
//  └─ UAbilitySystemComponent       (GAS 사용 시)
```

특히 UE2.5의 인벤토리는 `Inventory` 액터가 `Inventory` 포인터로 이어지는
**연결 리스트**였습니다. UE5에서는 `TArray<TObjectPtr<AWeapon>>`를 보유한
컴포넌트로 옮기는 것이 리플리케이션·정렬·검색 모두에서 단순합니다.

## 4.3 GameMode 매치 흐름

| UE2.5 `GameInfo` | UE5 `AGameMode` |
|---|---|
| `InitGame(Options, Error)` | `InitGame(MapName, Options, ErrorMessage)` |
| `Login()` / `PreLogin()` | `PreLogin()` / `Login()` / `PostLogin()` |
| `Logout(Controller)` | `Logout(AController*)` |
| `RestartPlayer(Controller)` | `RestartPlayer(AController*)` |
| `FindPlayerStart()` | `ChoosePlayerStart_Implementation()` |
| `SpawnDefaultPawnFor()` | `SpawnDefaultPawnFor_Implementation()` |
| `ScoreKill(Killer, Other)` | 직접 구현 (엔진 기본 제공 없음) |
| `CheckEndGame()` | 직접 구현 + `AGameMode::EndMatch()` |
| `bGameEnded` | `AGameMode` 매치 상태(`MatchState::WaitingPostMatch`) |
| `Broadcast()` / `BroadcastLocalized()` | 직접 구현 (`APlayerController` 클라이언트 RPC) |

`AGameMode`(`AGameModeBase`가 아님)는 `MatchState` 상태 머신을 제공하므로
UT류의 워밍업 → 진행 → 종료 흐름을 여기에 얹으십시오.

## 4.4 Mutator를 어떻게 옮길 것인가

UT2004의 `Mutator` 체인(`CheckReplacement`, `ModifyPlayer`, `MutatorHook`)은
UE5에 대응물이 없습니다. 세 가지 대안이 있습니다.

1. **GameMode 파생 클래스** — 변형이 소수이고 조합할 필요가 없다면 가장 단순.
2. **Modular Gameplay 플러그인 (`UGameFrameworkComponentManager`)** — 액터에
   런타임으로 컴포넌트를 주입하는 방식. 원본 Mutator의 `ModifyPlayer`에 가장 가깝습니다.
3. **Game Feature Plugin** — 기능 세트를 플러그인 단위로 켜고 끄는 UE5 정식 기능.
   원본이 "뮤테이터 여러 개를 동시에 켜는" 구조였다면 이쪽이 정답에 가깝습니다.

`CheckReplacement`(스폰되는 액터를 가로채 교체)는 UE5에서 직접 대응하는 훅이
없으므로, **스폰 지점을 팩토리 함수 하나로 모으고** 거기서 클래스 치환을 하는
방식으로 재설계하십시오.

## 4.5 설정(.ini) 이관

UE2.5의 `System/*.ini`와 UE5의 `Config/Default*.ini`는 문법은 비슷하지만
키가 전부 다릅니다. 자동 변환은 불가능하고 수동 매핑이 필요합니다.

| UE2.5 | UE5 |
|---|---|
| `[Engine.GameInfo]` | `Config/DefaultGame.ini` 의 `[/Script/Engine.GameMode]` 등 |
| `[Engine.PlayerInput]` `Bindings=` | Enhanced Input 에셋 (ini 아님) |
| `[Engine.GameEngine]` `ServerPackages=` | 개념 소멸 (쿠킹/패키징으로 대체) |
| `[URL]` `Map=` | `Config/DefaultEngine.ini` 의 `[/Script/EngineSettings.GameMapsSettings]` |

`var config` 프로퍼티는 UE5에서도 `UPROPERTY(Config)` + `UCLASS(Config=Game)`로
동일하게 동작하므로, **설정 가능 변수 목록 자체는 그대로 옮길 수 있습니다.**
