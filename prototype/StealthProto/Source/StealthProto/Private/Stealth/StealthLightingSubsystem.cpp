#include "Stealth/StealthLightingSubsystem.h"

#include "Components/LightComponent.h"
#include "Components/LocalLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"

void UStealthLightingSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	RefreshLights();
}

void UStealthLightingSubsystem::RefreshLights()
{
	Lights.Reset();

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		TArray<ULightComponent*> FoundLights;
		It->GetComponents<ULightComponent>(FoundLights);

		for (ULightComponent* Light : FoundLights)
		{
			RegisterLight(Light);
		}
	}

	UE_LOG(LogTemp, Log, TEXT("[Stealth] 광원 %d개 등록됨"), Lights.Num());
}

void UStealthLightingSubsystem::RegisterLight(ULightComponent* Light)
{
	if (!Light)
	{
		return;
	}

	Lights.AddUnique(Light);
}

void UStealthLightingSubsystem::UnregisterLight(ULightComponent* Light)
{
	if (!Light)
	{
		return;
	}

	Lights.RemoveAll([Light](const TWeakObjectPtr<ULightComponent>& Entry)
	{
		return !Entry.IsValid() || Entry.Get() == Light;
	});
}

float UStealthLightingSubsystem::ComputeBrightnessAtLocation(const FVector& Location, const AActor* IgnoredActor, float DebugDrawDuration) const
{
	float Total = 0.f;

	for (const TWeakObjectPtr<ULightComponent>& Entry : Lights)
	{
		const ULightComponent* Light = Entry.Get();
		if (!Light || !Light->IsVisible() || Light->Intensity <= 0.f)
		{
			continue;
		}

		Total += ComputeLightContribution(Light, Location, IgnoredActor, DebugDrawDuration);
	}

	return Total;
}

float UStealthLightingSubsystem::ComputeLightContribution(const ULightComponent* Light, const FVector& Location, const AActor* IgnoredActor, float DebugDrawDuration) const
{
	// 디렉셔널 라이트는 감쇠가 없다. 방향만 보고 차폐만 검사한다.
	if (const UDirectionalLightComponent* Directional = Cast<UDirectionalLightComponent>(Light))
	{
		const FVector ToLight = -Directional->GetForwardVector();
		const FVector TraceStart = Location + ToLight * DirectionalTraceDistance;

		if (IsOccluded(TraceStart, Location, IgnoredActor))
		{
			return 0.f;
		}

		if (DebugDrawDuration > 0.f)
		{
			DrawDebugLine(GetWorld(), Location, Location + ToLight * 200.f, FColor::Cyan, false, DebugDrawDuration, 0, 1.f);
		}

		return Directional->Intensity * DirectionalBrightnessScale;
	}

	// 포인트/스포트 라이트는 감쇠 반경 안에서만 기여한다.
	const ULocalLightComponent* Local = Cast<ULocalLightComponent>(Light);
	if (!Local)
	{
		return 0.f;
	}

	const FVector LightLocation = Local->GetComponentLocation();
	const float Distance = FVector::Dist(LightLocation, Location);
	const float Radius = Local->AttenuationRadius;

	if (Radius <= KINDA_SMALL_NUMBER || Distance >= Radius)
	{
		return 0.f;
	}

	// 물리적으로는 역제곱이지만, 게임플레이 값으로는 반경 기준의 제곱 감쇠가
	// 튜닝하기 쉽다. 반경 경계에서 정확히 0이 되어 "빛의 끝"이 명확해진다.
	float Attenuation = 1.f - (Distance / Radius);
	Attenuation = Attenuation * Attenuation;

	// 스포트라이트는 콘 밖이면 기여하지 않고, 내부/외부 콘 사이에서 부드럽게 감쇠한다.
	if (const USpotLightComponent* Spot = Cast<USpotLightComponent>(Local))
	{
		const FVector ToPoint = (Location - LightLocation).GetSafeNormal();
		if (ToPoint.IsNearlyZero())
		{
			return 0.f;
		}

		const float CosAngle = FVector::DotProduct(Spot->GetForwardVector(), ToPoint);
		const float CosOuter = FMath::Cos(FMath::DegreesToRadians(Spot->OuterConeAngle));
		const float CosInner = FMath::Cos(FMath::DegreesToRadians(Spot->InnerConeAngle));

		if (CosAngle <= CosOuter)
		{
			return 0.f;
		}

		// CosInner > CosOuter 이므로 콘 경계에서 0, 중심에서 1이 된다.
		const float ConeFalloff = FMath::IsNearlyEqual(CosInner, CosOuter)
			? 1.f
			: FMath::Clamp((CosAngle - CosOuter) / (CosInner - CosOuter), 0.f, 1.f);

		Attenuation *= ConeFalloff;
	}

	if (Attenuation <= KINDA_SMALL_NUMBER)
	{
		return 0.f;
	}

	// 차폐 검사는 가장 비싼 단계이므로 감쇠 계산을 통과한 뒤에만 수행한다.
	if (IsOccluded(LightLocation, Location, IgnoredActor))
	{
		return 0.f;
	}

	if (DebugDrawDuration > 0.f)
	{
		DrawDebugLine(GetWorld(), LightLocation, Location, FColor::Yellow, false, DebugDrawDuration, 0, 1.f);
	}

	return Local->Intensity * Attenuation;
}

bool UStealthLightingSubsystem::IsOccluded(const FVector& LightLocation, const FVector& Location, const AActor* IgnoredActor) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return true;
	}

	FCollisionQueryParams Params(SCENE_QUERY_STAT(StealthLightOcclusion), /*bTraceComplex=*/false);
	if (IgnoredActor)
	{
		Params.AddIgnoredActor(IgnoredActor);
	}

	return World->LineTraceTestByChannel(LightLocation, Location, OcclusionChannel, Params);
}
