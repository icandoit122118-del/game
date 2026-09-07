# 07. 네트워크와 리플리케이션

UE5의 네트워크 모델(서버 권위, 액터 채널, 프로퍼티 리플리케이션, RPC, 클라이언트
예측)은 UE2.5에서 이어진 **동일 계보**입니다. 개념을 새로 배울 필요는 없고,
문법만 옮기면 됩니다. 이 영역은 이식에서 가장 "번역"에 가까운 작업입니다.

## 7.1 프로퍼티 리플리케이션

```unrealscript
// UE2.5
var int Health;
var Weapon CurrentWeapon;

replication
{
    reliable if (Role == ROLE_Authority)
        Health, CurrentWeapon;
}
```

```cpp
// UE5 : 헤더
UPROPERTY(Replicated)
int32 Health;

UPROPERTY(ReplicatedUsing = OnRep_CurrentWeapon)
TObjectPtr<AWeapon> CurrentWeapon;

UFUNCTION()
void OnRep_CurrentWeapon();

virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
```

```cpp
// UE5 : 소스
#include "Net/UnrealNetwork.h"

void AMyPawn::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(AMyPawn, Health);
    DOREPLIFETIME(AMyPawn, CurrentWeapon);

    // 소유 클라이언트에게만 복제 (UE2.5의 `if (bNetOwner)` 조건에 대응)
    DOREPLIFETIME_CONDITION(AMyPawn, Ammo, COND_OwnerOnly);
}
```

`GetLifetimeReplicatedProps` 호출을 빠뜨리면 **컴파일은 되지만 값이 복제되지
않습니다.** 이식 중 가장 흔한 조용한 버그이므로, `Replicated` 프로퍼티를 추가할
때마다 즉시 짝을 맞추는 습관을 들이십시오.

## 7.2 RPC

| UE2.5 | UE5 |
|---|---|
| `reliable if (Role < ROLE_Authority) ClientFoo();` | `UFUNCTION(Client, Reliable) void ClientFoo();` |
| `reliable if (Role == ROLE_Authority) ServerFoo();` | `UFUNCTION(Server, Reliable, WithValidation) void ServerFoo();` |
| `unreliable if (...)` | `UFUNCTION(..., Unreliable)` |
| 전체 브로드캐스트 (수동 루프) | `UFUNCTION(NetMulticast, Reliable)` |
| `simulated function` | 개념 소멸 |

UE5의 서버 RPC는 구현 함수 이름에 `_Implementation` 접미사를 붙입니다.

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void ServerFire(FVector_NetQuantize Origin);

// .cpp
bool AMyWeapon::ServerFire_Validate(FVector_NetQuantize Origin) { return true; }
void AMyWeapon::ServerFire_Implementation(FVector_NetQuantize Origin) { /* 실제 로직 */ }
```

`WithValidation`은 UE2.5에 없던 개념으로, **클라이언트가 보낸 값을 서버가 검증**하는
훅입니다. `_Validate`가 `false`를 반환하면 해당 클라이언트가 연결 해제됩니다.
치트 방지 측면에서 이식 시 실제 검증 로직을 채워 넣을 가치가 있습니다.

## 7.3 역할(Role)과 권한 체크

| UE2.5 | UE5 |
|---|---|
| `Role == ROLE_Authority` | `HasAuthority()` |
| `Role < ROLE_Authority` | `!HasAuthority()` |
| `RemoteRole` | `GetRemoteRole()` |
| `Level.NetMode == NM_DedicatedServer` | `GetNetMode() == NM_DedicatedServer` |
| `Level.NetMode == NM_Client` | `GetNetMode() == NM_Client` |
| `Level.NetMode == NM_Standalone` | `GetNetMode() == NM_Standalone` |
| `bNetOwner` | `COND_OwnerOnly` 리플리케이션 조건 |
| `IsLocallyControlled()` (Pawn) | `IsLocallyControlled()` (동일) |

**`simulated function`의 소멸**이 이식 시 가장 큰 사고 지점입니다. UE2.5에서는
`simulated`가 붙지 않은 함수는 클라이언트에서 아예 실행되지 않았습니다. UE5에는
그런 안전장치가 없으므로, **원본에서 `simulated`가 아니었던 함수는 이식 시
반드시 `if (!HasAuthority()) return;` 가드를 넣어야** 클라이언트에서 서버 전용
로직이 잘못 실행되는 것을 막을 수 있습니다.

## 7.4 액터 리플리케이션 설정

| UE2.5 | UE5 |
|---|---|
| `bAlwaysRelevant` | `bAlwaysRelevant` (동일) |
| `bNetTemporary` | `bNetTemporary` (동일) |
| `bReplicateMovement` | `SetReplicateMovement(true)` |
| `NetPriority` | `NetPriority` (동일) |
| `NetUpdateFrequency` | `NetUpdateFrequency` (동일) |
| `bNoDelete` | 레벨 배치 액터는 자동 처리 |
| `RemoteRole = ROLE_SimulatedProxy` | `SetReplicates(true)` + 이동 복제 설정 |

액터를 복제하려면 생성자에서 `bReplicates = true;`를 설정합니다. UnrealScript의
`defaultproperties`에 `bNetInitial`, `RemoteRole` 등을 지정하던 부분이 여기에
대응합니다.

## 7.5 이동 예측

UE2.5도 클라이언트 사이드 예측(`SavedMove`)을 사용했고 UE5도 동일한 구조를
유지합니다. **커스텀 이동(닷지, 대시, 부스트)이 있다면** 다음을 확장해야 합니다.

- `UCharacterMovementComponent` 파생 클래스
- `FSavedMove_Character` 파생 (`CanCombineWith`, `Clear`, `SetMoveFor`, `PrepMoveFor`)
- `FNetworkPredictionData_Client_Character` 파생
- `FCharacterNetworkMoveData` / 압축 플래그(`FSavedMove_Character::GetCompressedFlags`)

이 부분은 단순 번역이 아니라 재설계에 가깝습니다. **수직 슬라이스 단계(로드맵 3단계)에서
반드시 한 번 관통**해 두십시오. 후반에 손대면 이동 감각 전체를 다시 튜닝해야 합니다.

## 7.6 테스트 방법

UE5 에디터의 **Play In Editor → Net Mode: Play As Client, 플레이어 수 2~4**로
대부분의 리플리케이션 버그를 잡을 수 있습니다. 추가로:

- `Net PktLag=100`, `Net PktLoss=5` 콘솔 명령으로 지연/손실 환경 재현
- `showdebug net`, `stat net` 으로 대역폭 확인
- **데디케이티드 서버 빌드로도 반드시 테스트** — PIE 리슨 서버에서는
  드러나지 않는 `HasAuthority()` 오류가 있습니다
