#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "StealthLightingSubsystem.generated.h"

class ULightComponent;

/**
 * 레벨의 광원 목록을 관리하고, 임의 지점의 "게임플레이 밝기"를 계산한다.
 *
 * 렌더링 결과를 읽는 대신 광원을 직접 순회해 계산하는 방식이다. 결정적이고,
 * 데디케이티드 서버(렌더링 없음)에서도 동작하며, 조명을 끄거나 파괴했을 때
 * 즉시 반영된다. 대신 Lumen 간접광은 계산에 잡히지 않는다.
 * (자세한 선택 근거는 docs/ue5-migration/10-splinter-cell-chaos-theory.md 10.5절)
 */
UCLASS()
class STEALTHPROTO_API UStealthLightingSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	/** 런타임에 스폰된 광원을 등록한다. 이미 등록된 광원은 무시된다. */
	UFUNCTION(BlueprintCallable, Category = "Stealth|Lighting")
	void RegisterLight(ULightComponent* Light);

	/** 파괴되거나 더 이상 감지에 관여하지 않을 광원을 제거한다. */
	UFUNCTION(BlueprintCallable, Category = "Stealth|Lighting")
	void UnregisterLight(ULightComponent* Light);

	/** 레벨의 모든 광원을 다시 수집한다. 레벨 스트리밍 이후 호출. */
	UFUNCTION(BlueprintCallable, Category = "Stealth|Lighting")
	void RefreshLights();

	/**
	 * 한 지점의 밝기를 계산한다.
	 *
	 * 반환값은 정규화되지 않은 누적 기여도다. 0이면 완전한 어둠이고 상한은
	 * 레벨의 조명 세팅에 따라 달라지므로, 게임플레이 값으로 쓰려면
	 * UExposureComponent 쪽에서 ReferenceBrightness로 나눠 정규화한다.
	 *
	 * @param Location            측정할 월드 좌표
	 * @param IgnoredActor        차폐 트레이스에서 제외할 액터 (보통 측정 대상 본인)
	 * @param DebugDrawDuration   0보다 크면 기여한 광원까지 선을 그리고 그 시간만큼 유지한다
	 */
	float ComputeBrightnessAtLocation(const FVector& Location, const AActor* IgnoredActor = nullptr, float DebugDrawDuration = 0.f) const;

	/** 현재 등록된 광원 수. 디버그 표시용. */
	UFUNCTION(BlueprintPure, Category = "Stealth|Lighting")
	int32 GetRegisteredLightCount() const { return Lights.Num(); }

	/** 광원 → 측정 지점 사이 차폐 검사에 사용할 채널. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Lighting")
	TEnumAsByte<ECollisionChannel> OcclusionChannel = ECC_Visibility;

	/**
	 * 감쇠 반경이 없는 디렉셔널 라이트의 차폐를 검사할 때, 측정 지점에서
	 * 광원 방향으로 얼마나 멀리 트레이스할지. (cm)
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Lighting")
	float DirectionalTraceDistance = 100000.f;

	/**
	 * 디렉셔널 라이트의 세기에 곱할 값.
	 *
	 * UE5는 광원 종류마다 광량 단위가 다르다. 디렉셔널은 럭스(기본 10 안팎),
	 * 포인트/스포트는 칸델라 또는 루멘이라 원시값을 그냥 더하면 실외광이
	 * 실내 조명에 묻힌다. 두 값을 같은 눈금으로 맞추기 위한 보정 계수다.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Lighting", meta = (ClampMin = "0.0"))
	float DirectionalBrightnessScale = 1.f;

private:
	/** 한 광원이 해당 지점에 기여하는 밝기. 기여가 없으면 0. */
	float ComputeLightContribution(const ULightComponent* Light, const FVector& Location, const AActor* IgnoredActor, float DebugDrawDuration) const;

	/** 광원과 지점 사이가 지오메트리로 막혀 있는가. */
	bool IsOccluded(const FVector& LightLocation, const FVector& Location, const AActor* IgnoredActor) const;

	UPROPERTY(Transient)
	TArray<TWeakObjectPtr<ULightComponent>> Lights;
};
