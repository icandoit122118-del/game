# 03. UnrealScript → C++ / Blueprint 변환

UnrealScript는 UE4(2014)에서 완전히 제거되었습니다. 대체재는 **C++ + Blueprint**
조합이며, 다행히 UnrealScript의 상당수 개념(UClass 리플렉션, `UPROPERTY` 메타데이터,
리플리케이션, 액터 라이프사이클)은 이름만 바뀐 채 그대로 살아 있습니다.
**문법은 전부 다시 쓰되, 설계는 대부분 그대로 옮길 수 있습니다.**

## 3.1 무엇을 C++로, 무엇을 Blueprint로 옮길 것인가

| 원본 UnrealScript | 권장 이식 대상 |
|---|---|
| 게임 규칙, 데미지 계산, 상태 머신, 리플리케이션 | **C++** |
| `defaultproperties` 수치 (체력, 속도, 쿨다운) | **Data Asset / Data Table** 또는 BP 기본값 |
| 무기·아이템 개별 변형 클래스 | C++ 베이스 1개 + **Blueprint 파생** |
| UI (`Canvas`, GUI 클래스) | **UMG** (전면 재제작) |
| 이펙트 스폰, 사운드 재생 타이밍 | **애님 노티파이 / Niagara / Blueprint** |

**핵심 원칙**: UnrealScript에서 "클래스 하나 = 파일 하나"였던 구조를 그대로
C++ 클래스 1:1로 옮기지 마십시오. UT2004류 프로젝트는 무기 변형만으로 수십 개
클래스를 만드는 관례가 있었는데, UE5에서는 **C++ 베이스 클래스 하나 + 데이터
에셋 N개**가 유지보수·이터레이션 양쪽에서 압도적으로 유리합니다.

## 3.2 클래스 선언

```unrealscript
// UE2.5 : MyWeapon.uc
class MyWeapon extends Weapon;

var() float FireRate;
var   int   Ammo;

function Fire()
{
    Ammo--;
}

defaultproperties
{
    FireRate=0.5
    Ammo=30
}
```

```cpp
// UE5 : MyWeapon.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MyWeapon.generated.h"

UCLASS()
class MYGAME_API AMyWeapon : public AActor
{
    GENERATED_BODY()

public:
    AMyWeapon();

    UFUNCTION(BlueprintCallable, Category = "Weapon")
    void Fire();

protected:
    /** var() float FireRate; → 에디터 노출 프로퍼티 */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Weapon")
    float FireRate = 0.5f;

    /** var int Ammo; → 에디터 비노출, 코드 전용 */
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Weapon")
    int32 Ammo = 30;
};
```

```cpp
// UE5 : MyWeapon.cpp
#include "MyWeapon.h"

AMyWeapon::AMyWeapon()
{
    PrimaryActorTick.bCanEverTick = false;
}

void AMyWeapon::Fire()
{
    --Ammo;
}
```

대응 규칙 요약:

| UnrealScript | UE5 |
|---|---|
| `class X extends Y;` | `UCLASS() class AX : public AY { GENERATED_BODY() }` |
| `var Type Name;` | `UPROPERTY() Type Name;` |
| `var() Type Name;` (에디터 노출) | `UPROPERTY(EditAnywhere, Category="...")` |
| `var config Type Name;` | `UPROPERTY(Config)` + `UCLASS(Config=Game)` |
| `var transient` | `UPROPERTY(Transient)` |
| `defaultproperties { ... }` | 생성자에서 대입 또는 멤버 초기화자 |
| `const X = 5;` | `static constexpr int32 X = 5;` |
| `enum EFoo { FOO_A, FOO_B };` | `UENUM(BlueprintType) enum class EFoo : uint8 { A, B };` |
| `struct FVec { ... };` | `USTRUCT(BlueprintType) struct FVec { GENERATED_BODY() ... };` |
| `native` | 전부 C++이므로 개념 자체가 소멸 |
| `abstract` | `UCLASS(Abstract)` |
| `placeable` / `notplaceable` | `UCLASS(NotPlaceable)` (기본은 배치 가능) |

## 3.3 타입 대응

| UnrealScript | UE5 |
|---|---|
| `int` | `int32` |
| `byte` | `uint8` |
| `bool` | `bool` (`uint8 bFlag : 1` 비트필드도 가능) |
| `float` | `float` (좌표 관련은 `double`로 승격됨, 3.7절) |
| `string` | `FString` (표시용은 `FText`, 식별자는 `FName`) |
| `name` | `FName` |
| `vector` | `FVector` |
| `rotator` | `FRotator` (단위가 도로 바뀜 — 02 문서 2.5절) |
| `Actor A` (참조) | `AActor* A` (`UPROPERTY()`로 GC 보호 필수) |
| `class<Weapon> WeaponClass` | `TSubclassOf<AWeapon> WeaponClass` |
| `array<int> Foo` | `TArray<int32> Foo` |
| `Object.StaticSaveConfig()` | `SaveConfig()` |

> **`UPROPERTY()` 없는 raw 포인터는 GC가 수거해 댕글링 포인터가 됩니다.**
> UnrealScript에서는 모든 오브젝트 참조가 자동 추적되었기 때문에 이식 과정에서
> 가장 흔하게 발생하는 크래시 원인입니다. 액터/오브젝트 포인터 멤버에는 예외 없이
> `UPROPERTY()`를 붙이거나 `TObjectPtr<T>`를 사용하십시오.

## 3.4 함수와 라이프사이클

| UnrealScript | UE5 |
|---|---|
| `PreBeginPlay()` | `PostInitializeComponents()` |
| `PostBeginPlay()` | `BeginPlay()` |
| `PostNetBeginPlay()` | `BeginPlay()` + `OnRep_` 콜백 |
| `Destroyed()` | `EndPlay(EEndPlayReason)` / `Destroyed()` |
| `Tick(float Delta)` | `Tick(float DeltaSeconds)` (`PrimaryActorTick.bCanEverTick = true` 필요) |
| `Timer()` + `SetTimer(T, bLoop)` | `GetWorldTimerManager().SetTimer(Handle, this, &AX::Fn, T, bLoop)` |
| `Spawn(class'X', ...)` | `GetWorld()->SpawnActor<AX>(Class, Loc, Rot, Params)` |
| `Destroy()` | `Destroy()` |
| `Log("msg")` | `UE_LOG(LogTemp, Log, TEXT("msg"))` |
| `Warn("msg")` | `UE_LOG(LogTemp, Warning, TEXT("msg"))` |
| `Touch(Actor Other)` | `NotifyActorBeginOverlap` / `OnComponentBeginOverlap` 델리게이트 |
| `UnTouch(Actor Other)` | `NotifyActorEndOverlap` |
| `Bump(Actor Other)` | `NotifyHit` / `OnComponentHit` |
| `HitWall(vector N, Actor W)` | `ACharacter::MoveBlockedBy` 또는 `NotifyHit` |
| `Landed(vector HitNormal)` | `ACharacter::Landed(const FHitResult&)` |
| `TakeDamage(...)` | `AActor::TakeDamage(...)` / `UGameplayStatics::ApplyDamage` |
| `simulated function` | 개념 소멸 — `HasAuthority()` / `GetLocalRole()`로 분기 |
| `exec function Foo()` | `UFUNCTION(Exec) void Foo();` |
| `event Foo()` | `UFUNCTION(BlueprintNativeEvent)` 또는 가상 함수 |
| `foreach AllActors(class'X', A)` | `for (TActorIterator<AX> It(GetWorld()); It; ++It)` |
| `foreach DynamicActors(...)` | 동일하게 `TActorIterator` |
| `foreach TouchingActors(...)` | `GetOverlappingActors(OutActors, AX::StaticClass())` |
| `Trace(...)` | `GetWorld()->LineTraceSingleByChannel(Hit, Start, End, Channel, Params)` |
| `VSize(V)` | `V.Size()` |
| `Normal(V)` | `V.GetSafeNormal()` |
| `Rand(N)` | `FMath::RandRange(0, N - 1)` |
| `FRand()` | `FMath::FRand()` |
| `FClamp(V, A, B)` | `FMath::Clamp(V, A, B)` |
| `Level` | `GetWorld()` |
| `Level.TimeSeconds` | `GetWorld()->GetTimeSeconds()` |
| `Level.Game` | `GetWorld()->GetAuthGameMode()` |
| `Level.NetMode` | `GetNetMode()` |

## 3.5 상태(State) — 가장 까다로운 부분

UnrealScript의 `state`는 **함수 오버라이드를 런타임에 바꾸는** 언어 차원의 기능이며,
UE5에는 직접적인 대응물이 없습니다.

```unrealscript
// UE2.5
auto state Idle
{
    function Touch(Actor Other) { GotoState('Active'); }
}

state Active
{
    Begin:
        PlayAnim('Open');
        Sleep(2.0);
        GotoState('Idle');
}
```

UE5에서의 대체 수단은 세 가지이며, 규모에 따라 고릅니다.

1. **열거형 + `switch` FSM** (소규모, 상태 3~5개)
   ```cpp
   UENUM(BlueprintType)
   enum class EDoorState : uint8 { Idle, Opening, Active, Closing };

   UPROPERTY(ReplicatedUsing = OnRep_State)
   EDoorState State = EDoorState::Idle;

   void ADoor::SetState(EDoorState NewState); // 진입/퇴출 처리를 여기 한 곳에 모을 것
   ```
2. **Gameplay Ability System (GAS)** (무기·스킬·버프처럼 상태가 능력에 붙는 경우)
   — UnrealScript의 무기 상태 머신(`Idle`/`Firing`/`Reloading`)은 GAS의
   `GameplayAbility` + `GameplayTag` 조합으로 옮기는 것이 가장 자연스럽습니다.
3. **Behavior Tree / State Tree** (AI 로직)
   — UE2.5의 `Controller` 상태 머신(`Roaming`, `Attacking`)은 Behavior Tree로
   재설계하는 편이 UE5 툴링(디버거, 시각화)의 이점을 그대로 받습니다.

**`state` 안의 latent 코드 블록(`Begin:` 레이블, `Sleep()`, `FinishAnim()`)** 은
UE5에서 다음으로 대체합니다.

| UnrealScript latent | UE5 |
|---|---|
| `Sleep(2.0)` | 타이머, 또는 Blueprint의 `Delay`, 또는 C++ 코루틴/`FTimerHandle` 체인 |
| `FinishAnim()` | 애님 몽타주 `OnMontageEnded` 델리게이트 |
| `WaitForLanding()` | `ACharacter::Landed` 오버라이드 |
| `MoveTo()` / `MoveToward()` | `AAIController::MoveTo` + `OnMoveCompleted` |

## 3.6 연산자·문법 함정

| UnrealScript | UE5 (C++) | 함정 |
|---|---|---|
| `A ~= B` (문자열 대소문자 무시 비교) | `A.Equals(B, ESearchCase::IgnoreCase)` | 연산자 없음 |
| `A dot B` | `FVector::DotProduct(A, B)` | |
| `A cross B` | `FVector::CrossProduct(A, B)` | |
| `V << R` / `V >> R` | `R.UnrotateVector(V)` / `R.RotateVector(V)` | 방향 헷갈리기 쉬움 |
| `$` (문자열 연결) | `+` 또는 `FString::Printf` | |
| `@` (공백 포함 연결) | `A + TEXT(" ") + B` | |
| `class'MyPkg.MyClass'` | `AMyClass::StaticClass()` 또는 `TSoftClassPtr` | 문자열 경로 하드코딩 금지 |
| `None` | `nullptr` | |
| `Self` | `this` | |
| `Super.Foo()` | `Super::Foo()` | UE5는 `Super`가 typedef로 존재 |
| `local int i;` (함수 어디서나 선언 필요) | 사용 시점 선언 | UnrealScript는 지역 변수를 함수 최상단에만 선언 가능했음 |

**참조 전달**: UnrealScript는 `out` 키워드를, C++는 `&` 참조를 사용합니다.

```unrealscript
function GetInfo(out int Health, out int Armor);
```
```cpp
void GetInfo(int32& Health, int32& Armor);
```

## 3.7 UE5 고유 주의사항 (UE4 지식만 있어도 걸리는 부분)

- **Large World Coordinates (LWC)**: UE5부터 `FVector`의 성분이 `double`입니다.
  `float`로 좌표를 받는 코드는 경고 또는 정밀도 손실을 유발하므로, 이식 시
  좌표 계산은 `double`을 그대로 쓰거나 `FVector3f`를 명시하십시오.
- **`TObjectPtr<T>`**: UE5 권장 표기. 에디터 빌드에서 접근 추적 기능이 붙습니다.
  신규 코드는 `AActor* Foo` 대신 `TObjectPtr<AActor> Foo`를 사용하십시오.
- **모듈 구조**: UnrealScript의 패키지(`.u`)는 UE5의 **모듈**(`Source/<Module>/`)과
  대응합니다. 원본 패키지 경계가 합리적이었다면 모듈 경계로 그대로 옮기고,
  단일 거대 패키지였다면 이 기회에 분할하십시오.
- **Enhanced Input**: UE2.5의 `.ini` 기반 키 바인딩(`Aliases`, `Bindings`)은 UE5의
  **Input Mapping Context + Input Action** 에셋으로 재구성됩니다. 레거시
  `PlayerInput` 축 바인딩은 UE5에서 비권장입니다.

## 3.8 이식 순서 권장안

클래스 의존성의 아래쪽부터 올라가는 것이 재작업을 줄입니다.

```
1. 유틸리티 / 데이터 구조체 / 열거형        의존성 없음, 빠른 승리
2. GameMode / GameState / PlayerState        게임 골격
3. Pawn / Character / Controller             이동과 입력
4. Weapon / Item 베이스 클래스               수직 슬라이스의 핵심
5. AI Controller + Behavior Tree             적 1종
6. HUD / UMG                                 마지막. 원본 Canvas 코드는 참고만
7. 나머지 변형 클래스 → 대부분 데이터 에셋으로 흡수
```
